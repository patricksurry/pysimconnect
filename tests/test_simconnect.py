from ctypes import Structure, addressof, byref, c_char, c_double, c_int32, memmove, sizeof
from unittest.mock import MagicMock, patch
import pytest

from simconnect.sc import SimConnect
from simconnect.scdefs import (
    DATA_REQUEST_FLAG_TAGGED,
    DATATYPE_FLOAT64,
    DATATYPE_INT32,
    DATATYPE_STRING256,
    DWORD,
    RECV_ID_SIMOBJECT_DATA,
    RECV_SIMOBJECT_DATA,
)


def make_mock_sc():
    with patch("simconnect.sc.windll.LoadLibrary") as mock_load:
        mock_dll = MagicMock()
        mock_load.return_value = mock_dll
        sc = SimConnect(name="test")
    return sc, mock_dll


def test_remove_receiver():
    sc, _ = make_mock_sc()
    initial_count = len(sc._receivers)

    def custom_recv(recv):
        return True

    sc.add_receiver(RECV_SIMOBJECT_DATA, custom_recv)
    assert len(sc._receivers) == initial_count + 1

    removed = sc.remove_receiver(custom_recv)
    assert removed is True
    assert len(sc._receivers) == initial_count
    assert all(r._receiver is not custom_recv for r in sc._receivers)


def test_multiple_simconnect_instances_isolated():
    """Regression test for Issue #3: re-creating SimConnect should register DataDefinitions and events on the new handle."""
    sc1, _ = make_mock_sc()
    dd1 = sc1.subscribe_simdata(["Indicated Altitude"])
    dd1.simdata["Indicated Altitude"] = 5000.0
    sc1.send_event("KOHLSMAN_INC")

    sc2, _ = make_mock_sc()
    dd2 = sc2.subscribe_simdata(["Indicated Altitude"])
    sc2.send_event("KOHLSMAN_INC")

    assert dd2 is not dd1
    assert dd2.simdata == {}


def test_datadef_receive_tagged_float_int_string():
    sc, _ = make_mock_sc()
    dd = sc.subscribe_simdata([
        "Indicated Altitude",       # FLOAT64
        "ATC ID",                   # STRING256
        "TURB ENG IGNITION SWITCH", # Enum -> INT32 (can be negative or positive)
    ])

    class Payload(Structure):
        _pack_ = 1
        _fields_ = [
            ("header", RECV_SIMOBJECT_DATA),
            # Note RECV_SIMOBJECT_DATA already has dwData (DWORD) at the start of payload!
            # Wait: RECV_SIMOBJECT_DATA.dwData is the first 4 bytes of data.
        ]

    # Build raw packet starting at RECV_SIMOBJECT_DATA.dwData.offset
    class RawPacket(Structure):
        _pack_ = 1
        _fields_ = [
            ("dwSize", DWORD),
            ("dwVersion", DWORD),
            ("dwID", DWORD),
            ("dwRequestID", DWORD),
            ("dwObjectID", DWORD),
            ("dwDefineID", DWORD),
            ("dwFlags", DWORD),
            ("dwentrynumber", DWORD),
            ("dwoutof", DWORD),
            ("dwDefineCount", DWORD),
            # Tagged item 0: Indicated Altitude (float64)
            ("tag0", DWORD),
            ("val0", c_double),
            # Tagged item 1: ATC ID (string256 with NUL and trailing garbage)
            ("tag1", DWORD),
            ("val1", c_char * 256),
            # Tagged item 2: Enum (negative int32)
            ("tag2", DWORD),
            ("val2", c_int32),
        ]

    pkt = RawPacket(
        dwSize=sizeof(RawPacket),
        dwVersion=1,
        dwID=RECV_ID_SIMOBJECT_DATA,
        dwRequestID=0,
        dwObjectID=0,
        dwDefineID=dd.id,
        dwFlags=DATA_REQUEST_FLAG_TAGGED,
        dwentrynumber=1,
        dwoutof=1,
        dwDefineCount=3,
        tag0=0,
        val0=3500.5,
        tag1=1,
        val1=b"C-FBEV",
        tag2=2,
        val2=-1,
    )
    memmove(addressof(pkt) + RawPacket.val1.offset, b"C-FBEV\x00\xffgarbage", 15)

    recv = RECV_SIMOBJECT_DATA.from_address(addressof(pkt))
    for r in sc._receivers:
        r.receive(recv)

    assert dd.simdata["Indicated Altitude"] == pytest.approx(3500.5)
    assert dd.simdata["ATC ID"] == "C-FBEV"
    assert dd.simdata["TURB ENG IGNITION SWITCH"] == -1


def test_set_simdatum_packs_data():
    sc, mock_dll = make_mock_sc()
    sc.set_simdatum("Indicated Altitude", 4500.0)
    assert mock_dll.SimConnect_SetDataOnSimObject.called


def test_receive_dispatches_open(caplog):
    import logging
    from ctypes import pointer
    from simconnect.scdefs import RECV_OPEN, RECV_ID_OPEN

    sc, mock_dll = make_mock_sc()

    def fake_call_dispatch(hsc, proc, ctx):
        msg = RECV_OPEN(
            dwSize=sizeof(RECV_OPEN),
            dwVersion=1,
            dwID=RECV_ID_OPEN,
            szApplicationName=b"TestSim",
            dwApplicationVersionMajor=1,
            dwApplicationVersionMinor=0,
            dwApplicationBuildMajor=100,
            dwApplicationBuildMinor=0,
            dwSimConnectVersionMajor=1,
            dwSimConnectVersionMinor=0,
            dwSimConnectBuildMajor=1,
            dwSimConnectBuildMinor=0,
        )
        proc(pointer(msg), sizeof(msg), ctx)
        return 0

    mock_dll.SimConnect_CallDispatch.side_effect = fake_call_dispatch
    with caplog.at_level(logging.INFO):
        assert sc.receive() is True
    assert any("Open: App" in r.message for r in caplog.records)

