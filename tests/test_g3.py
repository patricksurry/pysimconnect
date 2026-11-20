import json
import socket
import threading

from simconnect.g3 import SimConnectG3Bridge, create_g3_server, matches_keys
from simconnect.mock import MockSimConnect


def test_g3_bridge_with_mock_simconnect():
    mock_sc = MockSimConnect()
    bridge = SimConnectG3Bridge(sc=mock_sc)
    units = bridge.metric_units()
    assert units["altitude"] == "ft"
    assert units["airspeed"] == "knot"
    assert units["pressureSetting"] == "hPa"
    assert units["slip"] == "deg"

    metrics = bridge.poll_metrics()
    assert "altitude" in metrics
    assert "airspeed" in metrics
    assert "heading" in metrics
    assert metrics["toFromVOR"] == 1
    bridge.close()


def test_matches_keys_uses_longest_prefix_rule():
    # a metric matches a requested key if it equals the key or is a dot-separated prefix of it
    assert matches_keys("fuel", ["fuel.left"])
    assert matches_keys("fuel.left", ["fuel.left"])
    assert not matches_keys("fuel.left", ["fuel"])
    assert not matches_keys("fuelPressure", ["fuel"])
    assert matches_keys("anything", [])


def test_adjust_action_fires_inc_dec_simevents():
    mock_sc = MockSimConnect()
    bridge = SimConnectG3Bridge(sc=mock_sc)
    initial_baro = mock_sc.get_simdatum("BAROMETER PRESSURE")
    bridge.apply_actions([{"op": "adjust", "metric": "pressureSetting", "by": 2}])
    assert mock_sc.event_history == [("KOHLSMAN_INC", 0), ("KOHLSMAN_INC", 0)]
    assert mock_sc.get_simdatum("BAROMETER PRESSURE") > initial_baro
    bridge.apply_actions([{"op": "adjust", "metric": "pressureSetting", "by": -1}])
    assert mock_sc.event_history[-1] == ("KOHLSMAN_DEC", 0)


def test_trigger_action_fires_simevent():
    mock_sc = MockSimConnect()
    bridge = SimConnectG3Bridge(sc=mock_sc)
    bridge.apply_actions([{"op": "trigger", "event": "attitudeCage"}])
    assert mock_sc.event_history == [("ATTITUDE_CAGE_BUTTON", 0)]


def test_set_action_writes_simvar():
    mock_sc = MockSimConnect()
    bridge = SimConnectG3Bridge(sc=mock_sc)
    bridge.apply_actions([{"op": "set", "metric": "masterBattery", "value": 0}])
    assert mock_sc.get_simdatum("ELECTRICAL MASTER BATTERY") == 0


def test_set_action_can_send_simevent_with_transformed_value():
    mock_sc = MockSimConnect()
    bridge = SimConnectG3Bridge(sc=mock_sc)
    bridge.actions.append({"op": "set", "metric": "headingBug", "simevent": "HEADING_BUG_SET", "fx": "round(x)"})
    bridge.apply_actions([{"op": "set", "metric": "headingBug", "value": 90.4}])
    assert mock_sc.event_history == [("HEADING_BUG_SET", 90)]


def test_adjust_action_on_simvar_applies_limit_hints():
    mock_sc = MockSimConnect()
    bridge = SimConnectG3Bridge(sc=mock_sc)
    bridge.actions.append({"op": "adjust", "metric": "headingBug", "simvar": "AUTOPILOT HEADING LOCK DIR"})
    bridge.state["headingBug"] = 350
    bridge.apply_actions([{"op": "adjust", "metric": "headingBug", "by": 20, "min": 0, "max": 360, "wrap": True}])
    assert mock_sc.get_simdatum("AUTOPILOT HEADING LOCK DIR") == 10


def test_actions_resolve_metric_keys_by_prefix():
    mock_sc = MockSimConnect()
    bridge = SimConnectG3Bridge(sc=mock_sc)
    bridge.apply_actions([{"op": "adjust", "metric": "pressureSetting.copilot", "by": 1}])
    assert mock_sc.event_history == [("KOHLSMAN_INC", 0)]


def test_unsupported_actions_are_ignored(caplog):
    mock_sc = MockSimConnect()
    bridge = SimConnectG3Bridge(sc=mock_sc)
    bridge.apply_actions(
        [
            {"op": "trigger", "event": "noSuchEvent"},
            {"op": "launch", "metric": "pressureSetting"},
            {"op": "adjust", "metric": "pressureSetting", "by": 1, "unit": "inHg"},  # wrong unit
            {"op": "adjust", "metric": "pressureSetting", "by": 1},
        ]
    )
    assert mock_sc.event_history == [("KOHLSMAN_INC", 0)]
    assert len([r for r in caplog.records if "ignoring" in r.getMessage()]) == 3


def test_heading_bug_events_move_the_mock_heading_bug():
    mock_sc = MockSimConnect()
    mock_sc.send_event("HEADING_BUG_DEC")
    assert mock_sc.get_simdatum("AUTOPILOT HEADING LOCK DIR") == 359


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


def _get(server, path: str) -> bytes:
    return _raw_http_request(server, f"GET {path} HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n".encode())


def _post_json(server, path: str, payload) -> bytes:
    body = json.dumps(payload).encode("utf-8")
    req = (
        f"POST {path} HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n"
    ).encode() + body
    return _raw_http_request(server, req)


def _json_body(resp: bytes):
    return json.loads(resp.split(b"\r\n\r\n", 1)[1].decode("utf-8"))


def test_g3_http_server_endpoints():
    mock_sc = MockSimConnect()
    bridge = SimConnectG3Bridge(sc=mock_sc)
    server = create_g3_server(bridge, host="127.0.0.1", port=0, stream_interval=0.05)
    try:
        # GET / serves a panel built on the hub protocol
        resp = _get(server, "/")
        assert b"200 OK" in resp
        assert b"@patricksurry/g3@0.3.0" in resp
        assert b".inputUrl('/inputs')" in resp

        # GET /metrics.json reports only metrics matching the requested keys, with units
        data = _json_body(_get(server, "/metrics.json?units=true&latest=0&keys=altitude,heading.copilot"))
        assert set(data["metrics"]) == {"altitude", "heading"}
        units = bridge.metric_units()
        assert data["units"] == {"altitude": units["altitude"], "heading": units["heading"]}
        assert data["latest"] > 0

        # POST /inputs applies a batch of actions in order
        resp = _post_json(
            server,
            "/inputs",
            {
                "actions": [
                    {"op": "adjust", "metric": "pressureSetting", "by": 1},
                    {"op": "trigger", "event": "attitudeCage"},
                ]
            },
        )
        assert b"200 OK" in resp
        assert _json_body(resp) == {"status": "ok"}
        assert mock_sc.event_history == [("KOHLSMAN_INC", 0), ("ATTITUDE_CAGE_BUTTON", 0)]

        # POST /inputs rejects anything that isn't an action batch
        assert b"400" in _post_json(server, "/inputs", {"HDG-ROT": 5}).split(b"\r\n", 1)[0]

        # GET /stream starts with a full snapshot of matching metrics, with units and latest
        resp = _raw_http_request(
            server,
            b"GET /stream?keys=altitude HTTP/1.1\r\nHost: localhost\r\n\r\n",
            read_first_sse=True,
        )
        hdr, body = resp.split(b"\r\n\r\n", 1)
        assert b"text/event-stream" in hdr
        sse_line = body.decode("utf-8").strip().splitlines()[0]
        assert sse_line.startswith("data: ")
        payload = json.loads(sse_line[len("data: ") :])
        assert set(payload["metrics"]) == {"altitude"}
        assert payload["units"] == {"altitude": "ft"}
        assert payload["latest"] > 0
    finally:
        server.server_close()
