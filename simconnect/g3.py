"""Lightweight HTTP + SSE server bridging SimConnect to G3 instrument panels."""
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import math
import os
import threading
import time
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from .changedict import ChangeDict
from .sc import SimConnect
from .scdefs import PERIOD_VISUAL_FRAME
from .scvars import validate_simvar, validate_units

logger = logging.getLogger(__name__)

DEFAULT_EXAMPLE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "examples", "g3")
)

# Map canonical MSFS unit names to G3 convert-units symbols
MSFS_TO_G3_UNIT: Dict[str, str] = {
    "feet": "ft",
    "foot": "ft",
    "degrees": "deg",
    "degree": "deg",
    "radians": "rad",
    "radian": "rad",
    "knots": "knot",
    "knot": "knot",
    "rankine": "R",
    "celsius": "C",
    "fahrenheit": "F",
    "rpm": "rpm",
    "r.p.m.": "rpm",
    "inhg": "inHg",
    "inches of mercury": "inHg",
    "radians per second": "rad/s",
    "feet/minute": "ft/min",
    "feet per minute": "ft/min",
    "feet/second": "ft/s",
    "feet per second": "ft/s",
    "millibars": "hPa",
    "hectopascals": "hPa",
    "gallons": "gal",
    "psi": "psi",
    "pounds per square inch": "psi",
}


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    path = config_path or os.path.join(DEFAULT_EXAMPLE_DIR, "config.json")
    with open(path, "r") as f:
        if path.endswith((".yml", ".yaml")):
            import yaml  # type: ignore
            return yaml.safe_load(f)
        return json.load(f)


def _infer_g3_unit(simvar: str, explicit_unit: Optional[str] = None) -> Optional[str]:
    sv_meta = validate_simvar(simvar, settable=False)
    msfs_unit = validate_units(simvar, explicit_unit, sv_meta)
    if not msfs_unit:
        return None
    return MSFS_TO_G3_UNIT.get(msfs_unit.lower(), msfs_unit)


class SimConnectG3Bridge:
    """Polls SimConnect (or synthetic mock telemetry) and serves G3 metrics/actions."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, mock: bool = False):
        self.cfg = config or load_config()
        self.mapping: List[Dict[str, Any]] = [dict(m) for m in self.cfg.get("metrics", [])]
        self.actions: List[Dict[str, Any]] = self.cfg.get("actions", [])
        self.mock = mock
        self.state = ChangeDict()
        self._lock = threading.Lock()
        self.sc: Optional[SimConnect] = None
        self.dd = None
        self._dd_latest = 0
        self._t0 = time.time()
        self._mock_offsets: Dict[str, float] = {
            "pressureSetting": 1013.25,
            "heading": 0.0,
            "radialVOR": 45.0,
            "headingADF": 0.0,
        }

        if not self.mock:
            self.sc = SimConnect(name="g3_bridge")
            self.dd = self.sc.subscribe_simdata(
                [dict(name=m["simvar"], units=m.get("unit")) for m in self.mapping],
                period=PERIOD_VISUAL_FRAME,
                interval=10,
            )
            simvar_units = self.dd.get_units()
            for m in self.mapping:
                u = simvar_units.get(m["simvar"]) or m.get("unit")
                m["unit"] = MSFS_TO_G3_UNIT.get(u.lower(), u) if u else None
        else:
            for m in self.mapping:
                m["unit"] = _infer_g3_unit(m["simvar"], m.get("unit"))

    def metric_units(self) -> Dict[str, Any]:
        return {
            m["metric"]: m["fxunit"] if "fxunit" in m else m.get("unit")
            for m in self.mapping
            if (m["fxunit"] if "fxunit" in m else m.get("unit")) is not None
        }

    def poll_metrics(self, metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        with self._lock:
            if self.mock:
                data = self._generate_mock_metrics(metrics)
            else:
                while self.sc.receive():
                    pass
                recent = self.dd.simdata.changedsince(self._dd_latest)
                self._dd_latest = self.dd.simdata.latest()
                data = {}
                for m in self.mapping:
                    name, sv = m["metric"], m["simvar"]
                    if (metrics and name not in metrics) or sv not in recent:
                        continue
                    v = recent[sv]
                    if "fx" in m:
                        v = eval(m["fx"], {"__builtins__": {}}, {"x": v})
                    data[name] = v

            latest = self.state.latest()
            self.state.update(data)
            changed = self.state.changedsince(latest)
            if changed:
                self.state.update(self.trigger_actions(changed))
            return data

    def _generate_mock_metrics(self, metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        t = time.time() - self._t0
        baro = self._mock_offsets["pressureSetting"]
        raw = {
            "heading": (120.0 + 15.0 * math.sin(t * 0.15) + self._mock_offsets["heading"]) % 360.0,
            "altitude": 5500.0 + 250.0 * math.sin(t * 0.2) + (baro - 1013.25) * 27.3,
            "pressureSetting": baro,
            "pitch": 4.0 * math.sin(t * 0.4),
            "roll": 12.0 * math.sin(t * 0.3),
            "turnrate": 1.5 * math.cos(t * 0.3),
            "slip": 3.0 * math.sin(t * 0.5),
            "airspeed": 108.0 + 8.0 * math.cos(t * 0.2),
            "verticalSpeed": 400.0 * math.cos(t * 0.2),
            "relativeADF": (280.0 + 10.0 * math.sin(t * 0.1)) % 360.0,
            "headingADF": self._mock_offsets["headingADF"] % 360.0,
            "radialVOR": self._mock_offsets["radialVOR"] % 360.0,
            "radialDeviation": 4.0 * math.sin(t * 0.25),
            "toFromVOR": 1,
            "compass": (120.0 + 15.0 * math.sin(t * 0.15)) % 360.0,
            "suctionPressure": 5.2,
            "fuelPressure": 5.4,
            "oilPressure": 78.0,
            "oilTemperature": 615.0,
            "manifoldPressure": 24.5,
            "engineRPM": 2350.0 + 30.0 * math.sin(t * 0.25),
        }
        return {k: v for k, v in raw.items() if not metrics or k in metrics}

    def handle_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            out = self.trigger_actions(inputs)
            if out:
                self.state.update(out)
            return out

    def trigger_actions(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        outputs: Dict[str, Any] = {}
        mock_deltas = {"ALT-ROT": ("pressureSetting", 0.34), "HDG-ROT": ("heading", 1.0), "VOR-ROT": ("radialVOR", 1.0), "ADF-ROT": ("headingADF", 1.0)}
        for k, raw_v in inputs.items():
            if self.mock and k in mock_deltas:
                field, scale = mock_deltas[k]
                self._mock_offsets[field] += float(raw_v) * scale

            for rule in (r for r in self.actions if r.get("input") == k):
                v = eval(rule["fx"], {"__builtins__": {}}, {"x": raw_v}) if "fx" in rule else raw_v
                if "output" in rule:
                    outputs[rule["output"]] = v
                elif "simvar" in rule and self.sc is not None:
                    self.sc.set_simdatum(rule["simvar"], v)
                elif "event" in rule and self.sc is not None:
                    name, method = rule["event"], rule.get("method")
                    if method == "incdec":
                        evt = name[0 if v > 0 else 1]
                        for _ in range(int(abs(v))):
                            self.sc.send_event(evt)
                    elif method == "set":
                        self.sc.send_event(name, int(v))
                    else:
                        self.sc.send_event(name)
        return outputs

    def close(self) -> None:
        if self.sc is not None:
            self.sc.Close()


class G3HTTPRequestHandler(SimpleHTTPRequestHandler):
    """Serves static panel files plus /metrics.json, /stream (SSE), and POST /inputs."""

    protocol_version = "HTTP/1.1"

    def __init__(self, *args: Any, bridge: SimConnectG3Bridge, stream_interval: float = 0.1, directory: Optional[str] = None, **kwargs: Any):
        self.bridge = bridge
        self.stream_interval = stream_interval
        super().__init__(*args, directory=directory or DEFAULT_EXAMPLE_DIR, **kwargs)

    def log_message(self, fmt: str, *args: Any) -> None:
        logger.debug(fmt, *args)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()

    def _send_json(self, payload: Any, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/metrics.json":
            qs = parse_qs(parsed.query)
            ms = [m for m in qs.get("metrics", [""])[0].split(",") if m] or None
            latest = int(qs.get("latest", ["0"])[0] or 0)
            want_units = qs.get("units", ["false"])[0].lower() in ("true", "1", "yes")

            self.bridge.poll_metrics(ms)
            result: Dict[str, Any] = {
                "latest": self.bridge.state.latest(),
                "metrics": {k: v for k, v in self.bridge.state.changedsince(latest).items() if not ms or k in ms},
            }
            if want_units:
                result["units"] = {k: v for k, v in self.bridge.metric_units().items() if not ms or k in ms}
            return self._send_json(result)

        if parsed.path == "/stream":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            client_latest, sent_units = 0, False
            try:
                while True:
                    self.bridge.poll_metrics()
                    deltas = self.bridge.state.changedsince(client_latest)
                    if deltas or not sent_units:
                        client_latest = self.bridge.state.latest()
                        payload: Dict[str, Any] = {"metrics": deltas if sent_units else dict(self.bridge.state)}
                        if not sent_units:
                            payload["units"] = self.bridge.metric_units()
                            sent_units = True
                        self.wfile.write(f"data: {json.dumps(payload)}\n\n".encode("utf-8"))
                        self.wfile.flush()
                    time.sleep(self.stream_interval)
            except (BrokenPipeError, ConnectionResetError, OSError):
                return

        super().do_GET()

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/inputs":
            return self.send_error(HTTPStatus.NOT_FOUND)
        length = int(self.headers.get("Content-Length", "0") or 0)
        payload = json.loads(self.rfile.read(length).decode("utf-8") if length else "{}")
        self._send_json({"status": "ok", "outputs": self.bridge.handle_inputs(payload)})


def create_g3_server(
    bridge: SimConnectG3Bridge,
    host: str = "0.0.0.0",
    port: int = 8000,
    stream_interval: float = 0.1,
    static_dir: Optional[str] = None,
) -> ThreadingHTTPServer:
    handler_cls = partial(
        G3HTTPRequestHandler,
        bridge=bridge,
        stream_interval=stream_interval,
        directory=static_dir or DEFAULT_EXAMPLE_DIR,
    )
    server = ThreadingHTTPServer((host, port), handler_cls)
    server.daemon_threads = True
    return server
