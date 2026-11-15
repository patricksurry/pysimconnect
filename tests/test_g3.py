import json
import socket
import threading
import time
from unittest.mock import MagicMock
import pytest

from simconnect.g3 import SimConnectG3Bridge, create_g3_server
from simconnect.mock import MockSimConnect


def test_g3_bridge_with_mock_simconnect():
    mock_sc = MockSimConnect()
    bridge = SimConnectG3Bridge(sc=mock_sc)
    units = bridge.metric_units()
    assert units["altitude"] == "ft"
    assert units["airspeed"] == "knot"
    assert units["pressureSetting"] == "hPa"

    metrics = bridge.poll_metrics()
    assert "altitude" in metrics
    assert "airspeed" in metrics
    assert "heading" in metrics

    # Triggering ALT-ROT sends KOHLSMAN_INC to MockSimConnect and bumps barometer pressure
    initial_baro = mock_sc.get_simdatum("BAROMETER PRESSURE")
    bridge.handle_inputs({"ALT-ROT": 2})
    assert ("KOHLSMAN_INC", 0) in mock_sc.event_history
    assert mock_sc.get_simdatum("BAROMETER PRESSURE") > initial_baro

    # Output rule copies input to state
    bridge.actions.append({"input": "testWarning", "output": "RED_WARNING"})
    out = bridge.handle_inputs({"testWarning": 1})
    assert out == {"RED_WARNING": 1}
    assert bridge.state["RED_WARNING"] == 1


def test_g3_bridge_live_simconnect_dispatch():
    mock_sc = MagicMock()
    mock_sc.receive.return_value = False
    mock_dd = MagicMock()
    mock_dd.get_units.return_value = {
        "INDICATED ALTITUDE": "feet",
        "TURN COORDINATOR BALL": "position",
        "NAV TOFROM:1": "Enum",
    }
    from simconnect.changedict import ChangeDict
    sd = ChangeDict()
    sd["INDICATED ALTITUDE"] = 4500.0
    sd["TURN COORDINATOR BALL"] = 25.0
    sd["NAV TOFROM:1"] = 2
    mock_dd.simdata = sd
    mock_sc.subscribe_simdata.return_value = mock_dd

    bridge = SimConnectG3Bridge(sc=mock_sc)
    assert bridge.metric_units()["altitude"] == "ft"
    assert bridge.metric_units()["slip"] == "deg"

    polled = bridge.poll_metrics()
    assert polled["altitude"] == pytest.approx(4500.0)
    assert polled["slip"] == pytest.approx(5.0)  # fx: x / 5
    assert polled["toFromVOR"] == -1  # fx: -1 if x == 2 else x

    # Test incdec event action
    bridge.handle_inputs({"ALT-ROT": -3})
    assert mock_sc.send_event.call_count == 3
    mock_sc.send_event.assert_called_with("KOHLSMAN_DEC")

    # Test simvar set action
    bridge.handle_inputs({"MASTER1": 1})
    mock_sc.set_simdatum.assert_called_once_with("ELECTRICAL MASTER BATTERY", 1)

    bridge.close()
    mock_sc.Close.assert_called_once()


def _raw_http_request(server, raw_req: bytes, read_first_sse: bool = False) -> bytes:
    c_sock, s_sock = socket.socketpair()
    t = threading.Thread(
        target=server.RequestHandlerClass,
        args=(s_sock, ("127.0.0.1", 0), server),
        daemon=True,
    )
    t.start()
    c_sock.sendall(raw_req)
    chunks = []
    try:
        while True:
            chunk = c_sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            joined = b"".join(chunks)
            if read_first_sse and b"\n\n" in joined.split(b"\r\n\r\n", 1)[-1]:
                break
            if not read_first_sse and b"\r\n\r\n" in joined:
                hdr, body = joined.split(b"\r\n\r\n", 1)
                for line in hdr.split(b"\r\n"):
                    if line.lower().startswith(b"content-length:"):
                        clen = int(line.split(b":", 1)[1].strip())
                        if len(body) >= clen:
                            return joined
    finally:
        c_sock.close()
        s_sock.close()
    return b"".join(chunks)


def test_g3_http_server_endpoints():
    bridge = SimConnectG3Bridge(sc=MockSimConnect())
    server = create_g3_server(bridge, host="127.0.0.1", port=0, stream_interval=0.05)
    try:
        # 1. GET / serves panel HTML
        resp1 = _raw_http_request(server, b"GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n")
        assert b"200 OK" in resp1
        assert b"g3-contrib.min.js" in resp1
        assert b"g3.panel()" in resp1

        # 2. GET /metrics.json?units=true
        resp2 = _raw_http_request(
            server,
            b"GET /metrics.json?units=true HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n",
        )
        body2 = resp2.split(b"\r\n\r\n", 1)[1]
        data = json.loads(body2.decode("utf-8"))
        assert "latest" in data
        assert "metrics" in data
        assert "altitude" in data["metrics"]
        assert data["units"]["altitude"] == "ft"

        # 3. POST /inputs
        bridge.actions.append({"input": "fuelWarning", "output": "RED_WARNING"})
        post_body = json.dumps({"HDG-ROT": 5, "fuelWarning": 1}).encode("utf-8")
        req3 = (
            f"POST /inputs HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\n"
            f"Content-Length: {len(post_body)}\r\nConnection: close\r\n\r\n"
        ).encode("utf-8") + post_body
        resp3 = _raw_http_request(server, req3)
        body3 = resp3.split(b"\r\n\r\n", 1)[1]
        res = json.loads(body3.decode("utf-8"))
        assert res["status"] == "ok"
        assert res["outputs"] == {"RED_WARNING": 1}

        # 4. GET /stream (SSE) - read first SSE event
        resp4 = _raw_http_request(
            server,
            b"GET /stream HTTP/1.1\r\nHost: localhost\r\n\r\n",
            read_first_sse=True,
        )
        hdr4, body4 = resp4.split(b"\r\n\r\n", 1)
        assert b"text/event-stream" in hdr4
        sse_line = body4.decode("utf-8").strip().splitlines()[0]
        assert sse_line.startswith("data: ")
        sse_payload = json.loads(sse_line[len("data: "):])
        assert "metrics" in sse_payload
        assert "units" in sse_payload
        assert "altitude" in sse_payload["metrics"]
    finally:
        server.server_close()
