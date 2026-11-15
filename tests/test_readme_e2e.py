from ctypes import Structure, addressof, c_double, pointer, sizeof
from unittest.mock import MagicMock, patch
import pytest
from typer.testing import CliRunner

from simconnect import SimConnect, PERIOD_VISUAL_FRAME
from simconnect.cli import app, scoped_autocomplete
from simconnect.scdefs import (
    DATA_REQUEST_FLAG_TAGGED,
    DWORD,
    RECV_ID_SIMOBJECT_DATA,
    RECV_SIMOBJECT_DATA,
)

runner = CliRunner()


def test_readme_cli_search():
    """Mirror README 'simconnect search altitude' example (opens web SDK explorer)."""
    with patch("simconnect.cli.webbrowser.open") as mock_open:
        res = runner.invoke(app, ["search", "altitude"])
        assert res.exit_code == 0
        assert "https://patricksurry.github.io/pysimconnect/#search=altitude" in res.stdout
        mock_open.assert_called_once_with("https://patricksurry.github.io/pysimconnect/#search=altitude")


def test_readme_cli_tab_completion():
    """Mirror README 'simconnect get PLA<TAB>' auto-completion."""
    complete_vars = scoped_autocomplete("VARIABLES")
    matches = complete_vars("PLA")
    assert "PLANE_ALTITUDE" in matches


def test_readme_cli_get_set_send():
    """Mirror README 'simconnect get PLANE_ALTITUDE', 'set --units meters', and 'send KOHLSMAN_INC'."""
    with patch("simconnect.cli.SimConnect") as mock_sc_cls:
        mock_sc = MagicMock()
        mock_sc.__enter__.return_value = mock_sc
        mock_sc.get_simdatum.return_value = 5280.0
        mock_sc_cls.return_value = mock_sc

        res_get = runner.invoke(app, ["get", "PLANE_ALTITUDE"])
        assert res_get.exit_code == 0
        assert "PLANE ALTITUDE = 5280.0" in res_get.stdout
        mock_sc.get_simdatum.assert_called_once_with("PLANE ALTITUDE", None)

        res_set = runner.invoke(app, ["set", "PLANE_ALTITUDE", "1500", "--units", "meters"])
        assert res_set.exit_code == 0
        assert "Setting PLANE ALTITUDE = 1500.0 (meters)" in res_set.stdout
        mock_sc.set_simdatum.assert_called_once_with("PLANE ALTITUDE", 1500.0, "meters")

        res_send = runner.invoke(app, ["send", "KOHLSMAN_INC"])
        assert res_send.exit_code == 0
        assert "Sending KOHLSMAN_INC" in res_send.stdout
        mock_sc.send_event.assert_called_once_with("KOHLSMAN_INC", 0)


def test_readme_python_demo_e2e():
    """Mirror README / examples/demo.py end-to-end flow and idempotent Close()."""
    with patch("simconnect.sc.windll.LoadLibrary") as mock_load:
        mock_dll = MagicMock()
        mock_load.return_value = mock_dll

        class SingleFloatPacket(Structure):
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
                ("val0", c_double),
            ]

        class TaggedThreeFloatPacket(Structure):
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
                ("tag0", DWORD),
                ("val0", c_double),
                ("tag1", DWORD),
                ("val1", c_double),
                ("tag2", DWORD),
                ("val2", c_double),
            ]

        call_count = {"n": 0}

        def fake_call_dispatch(hsc, proc, ctx):
            call_count["n"] += 1
            if call_count["n"] == 1:
                pkt = SingleFloatPacket(
                    dwSize=sizeof(SingleFloatPacket),
                    dwVersion=1,
                    dwID=RECV_ID_SIMOBJECT_DATA,
                    dwRequestID=0,
                    dwObjectID=0,
                    dwDefineID=0,
                    dwFlags=0,
                    dwentrynumber=1,
                    dwoutof=1,
                    dwDefineCount=1,
                    val0=8500.0,
                )
                recv = RECV_SIMOBJECT_DATA.from_address(addressof(pkt))
                proc(pointer(recv), sizeof(pkt), ctx)
            elif call_count["n"] == 2:
                pkt = TaggedThreeFloatPacket(
                    dwSize=sizeof(TaggedThreeFloatPacket),
                    dwVersion=1,
                    dwID=RECV_ID_SIMOBJECT_DATA,
                    dwRequestID=1,
                    dwObjectID=0,
                    dwDefineID=1,
                    dwFlags=DATA_REQUEST_FLAG_TAGGED,
                    dwentrynumber=1,
                    dwoutof=1,
                    dwDefineCount=3,
                    tag0=0,
                    val0=8600.0,
                    tag1=1,
                    val1=1013.25,
                    tag2=2,
                    val2=24.5,
                )
                recv = RECV_SIMOBJECT_DATA.from_address(addressof(pkt))
                proc(pointer(recv), sizeof(pkt), ctx)
            return 0

        mock_dll.SimConnect_CallDispatch.side_effect = fake_call_dispatch

        with SimConnect() as sc:
            altitude = sc.get_simdatum("Indicated Altitude")
            assert altitude == pytest.approx(8500.0)

            datadef = sc.subscribe_simdata(
                [
                    "Indicated Altitude",
                    dict(name="Kohlsman setting hg", units="hectopascal"),
                    "ELECTRICAL BATTERY BUS VOLTAGE",
                ],
                period=PERIOD_VISUAL_FRAME,
                interval=10,
            )
            assert datadef.get_units() == {
                "Indicated Altitude": "feet",
                "Kohlsman setting hg": "hectopascal",
                "ELECTRICAL BATTERY BUS VOLTAGE": "volts",
            }

            latest = datadef.simdata.latest()
            sc.set_simdatum("Indicated Altitude", altitude + 100)
            sc.send_event("KOHLSMAN_INC")

            assert sc.receive() is True
            updated = datadef.simdata.changedsince(latest)
            assert updated["Indicated Altitude"] == pytest.approx(8600.0)
            assert updated["Kohlsman setting hg"] == pytest.approx(1013.25)
            assert updated["ELECTRICAL BATTERY BUS VOLTAGE"] == pytest.approx(24.5)

            # Explicit Close() inside context manager should be idempotent
            sc.Close()

        assert mock_dll.SimConnect_Close.call_count == 1


def test_readme_with_mock_simconnect():
    """Verify MockSimConnect supports the full README tutorial and CLI workflow."""
    import time
    from simconnect.mock import MockSimConnect

    with MockSimConnect() as sc:
        altitude = sc.get_simdatum("Indicated Altitude")
        assert isinstance(altitude, float)

        datadef = sc.subscribe_simdata(
            [
                "Indicated Altitude",
                dict(name="Kohlsman setting hg", units="hectopascal"),
                "ELECTRICAL BATTERY BUS VOLTAGE",
            ],
            period=PERIOD_VISUAL_FRAME,
            interval=10,
        )
        assert datadef.get_units() == {
            "Indicated Altitude": "feet",
            "Kohlsman setting hg": "hectopascal",
            "ELECTRICAL BATTERY BUS VOLTAGE": "volts",
        }

        latest = datadef.simdata.latest()
        time.sleep(0.025)
        sc.set_simdatum("PLANE ALTITUDE", 1500.0, units="meters")
        sc.send_event("KOHLSMAN_INC")
        while sc.receive():
            pass
        updated = datadef.simdata.changedsince(latest)
        assert updated["Indicated Altitude"] == pytest.approx(1500.0 / 0.3048)
        assert updated["Kohlsman setting hg"] > 1013.25

