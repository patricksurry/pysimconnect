"""Lightweight HTTP + SSE hub bridging SimConnect to G3 instrument panels.

Implements the G3 hub protocol (https://github.com/patricksurry/g3/blob/master/doc/API.md#hubs):
panels read metrics by polling /metrics.json or streaming /stream, filtered by `keys`,
and POST batches of set/adjust/trigger actions to /inputs, which the bridge maps
to SimConnect simvar writes and events. The effect of an action reaches the panel
as an ordinary metric change once it's reflected in the simulator.
"""

import json
import logging
import os
import threading
import time
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from ..changedict import ChangeDict
from ..sc import SimConnect
from ..scdefs import PERIOD_VISUAL_FRAME

logger = logging.getLogger(__name__)

DEFAULT_EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))

# Map canonical MSFS unit names to G3 convert-units symbols
MSFS_TO_G3_UNIT: dict[str, str] = {
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


def load_config(config_path: str | None = None) -> dict[str, Any]:
    path = config_path or os.path.join(DEFAULT_EXAMPLE_DIR, "config.json")
    with open(path) as f:
        if path.endswith((".yml", ".yaml")):
            import yaml  # type: ignore

            return yaml.safe_load(f)
        return json.load(f)


def matches_keys(metric: str, keys: list[str] | None) -> bool:
    """A metric matches the requested keys if it equals one of them or is a dot-separated prefix of one."""
    return not keys or any(k == metric or k.startswith(metric + ".") for k in keys)


def _resolve(name: str, known: dict[str, Any]) -> str | None:
    """Resolve a G3 metric key to the longest dot-separated prefix of itself in known."""
    ks = name.split(".")
    while ks:
        k = ".".join(ks)
        if k in known:
            return k
        ks.pop()
    return None


def _limit(x: float, action: dict[str, Any]) -> float:
    """Apply an adjust action's optional min/max/wrap hints."""
    lo, hi = action.get("min"), action.get("max")
    if action.get("wrap") and lo is not None and hi is not None:
        span = hi - lo
        return (x - lo) % span + lo
    if lo is not None:
        x = max(lo, x)
    if hi is not None:
        x = min(hi, x)
    return x


class SimConnectG3Bridge:
    """Hub state for G3 panels: polls a SimConnect (or MockSimConnect) instance and applies G3 actions to it."""

    def __init__(self, sc: Any | None = None, config: dict[str, Any] | None = None):
        self.sc = sc if sc is not None else SimConnect(name="g3_bridge")
        self.cfg = config or load_config()
        self.mapping: list[dict[str, Any]] = [dict(m) for m in self.cfg.get("metrics", [])]
        self.actions: list[dict[str, Any]] = list(self.cfg.get("actions", []))
        self.state = ChangeDict()
        self._lock = threading.Lock()
        self._dd_latest = 0

        self.dd = self.sc.subscribe_simdata(
            [dict(name=m["simvar"], units=m.get("unit")) for m in self.mapping],
            period=PERIOD_VISUAL_FRAME,
            interval=10,
        )
        simvar_units = self.dd.get_units()
        for m in self.mapping:
            u = simvar_units.get(m["simvar"]) or m.get("unit")
            m["unit"] = MSFS_TO_G3_UNIT.get(u.lower(), u) if u else None

    def metric_units(self) -> dict[str, Any]:
        return {
            m["metric"]: m["fxunit"] if "fxunit" in m else m.get("unit")
            for m in self.mapping
            if (m["fxunit"] if "fxunit" in m else m.get("unit")) is not None
        }

    def poll_metrics(self) -> dict[str, Any]:
        """Read any simvar changes into the hub state, returning the changed metrics."""
        with self._lock:
            while self.sc.receive():
                pass
            recent = self.dd.simdata.changedsince(self._dd_latest)
            self._dd_latest = self.dd.simdata.latest()
            data = {}
            for m in self.mapping:
                name, sv = m["metric"], m["simvar"]
                if sv not in recent:
                    continue
                v = recent[sv]
                if "fx" in m:
                    v = eval(m["fx"], {"__builtins__": {}}, {"x": v})
                data[name] = v
            self.state.update(data)
            return data

    def apply_actions(self, actions: list[dict[str, Any]]) -> None:
        """Apply a batch of G3 actions in order, ignoring (and logging) any that aren't supported."""
        with self._lock:
            for action in actions:
                self._apply(action)

    def _apply(self, action: dict[str, Any]) -> None:
        op = action.get("op") if isinstance(action, dict) else None
        if op not in ("set", "adjust", "trigger"):
            logger.warning("ignoring unknown action %r", action)
            return
        field = "event" if op == "trigger" else "metric"
        rules = {r[field]: r for r in self.actions if r.get("op") == op and field in r}
        name = action.get(field)
        key = _resolve(name, rules) if isinstance(name, str) else None
        if key is None:
            logger.warning("ignoring unsupported action %r", action)
            return
        rule = rules[key]

        unit = action.get("unit")
        if unit and op != "trigger":
            expected = self.metric_units().get(rule["metric"])
            if expected and unit != expected:
                logger.warning("ignoring action %r: expected unit %s", action, expected)
                return

        value = action.get("value")
        if op == "adjust":
            by = action.get("by")
            if not isinstance(by, (int, float)):
                logger.warning("ignoring adjust action without numeric 'by' %r", action)
                return
            if "simevent" in rule:
                inc, dec = rule["simevent"]
                for _ in range(int(abs(by))):
                    self.sc.send_event(inc if by > 0 else dec)
                return
            current = self.state.get(rule["metric"])
            if not isinstance(current, (int, float)):
                logger.warning("ignoring action %r: no current value for %s", action, rule["metric"])
                return
            value = _limit(current + by, action)

        if "fx" in rule and value is not None:
            value = eval(rule["fx"], {"__builtins__": {"round": round, "int": int}}, {"x": value})
        if "simvar" in rule:
            self.sc.set_simdatum(rule["simvar"], value)
        elif "simevent" in rule:
            if value is None:
                self.sc.send_event(rule["simevent"])
            else:
                self.sc.send_event(rule["simevent"], int(value))
        else:
            logger.warning("ignoring action %r: rule has no simvar or simevent", action)

    def close(self) -> None:
        self.sc.Close()


class G3HTTPRequestHandler(SimpleHTTPRequestHandler):
    """Serves static panel files plus the G3 hub endpoints /metrics.json, /stream (SSE), and POST /inputs."""

    protocol_version = "HTTP/1.1"

    def __init__(
        self,
        *args: Any,
        bridge: SimConnectG3Bridge,
        stream_interval: float = 0.1,
        directory: str | None = None,
        **kwargs: Any,
    ):
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
        qs = parse_qs(parsed.query)
        keys = [k for k in qs.get("keys", [""])[0].split(",") if k]

        def matching(d: dict[str, Any]) -> dict[str, Any]:
            return {k: v for k, v in d.items() if matches_keys(k, keys)}

        if parsed.path == "/metrics.json":
            latest = int(qs.get("latest", ["0"])[0] or 0)
            want_units = qs.get("units", ["false"])[0].lower() in ("true", "1", "yes")

            self.bridge.poll_metrics()
            result: dict[str, Any] = {
                "latest": self.bridge.state.latest(),
                "metrics": matching(self.bridge.state.changedsince(latest)),
            }
            if want_units:
                result["units"] = matching(self.bridge.metric_units())
            return self._send_json(result)

        if parsed.path == "/stream":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            client_latest = None
            try:
                while True:
                    self.bridge.poll_metrics()
                    if client_latest is None:
                        # start each connection with a full snapshot of the matching metrics, with units
                        payload: dict[str, Any] = {
                            "metrics": matching(dict(self.bridge.state)),
                            "units": matching(self.bridge.metric_units()),
                        }
                    else:
                        payload = {"metrics": matching(self.bridge.state.changedsince(client_latest))}
                    if client_latest is None or payload["metrics"]:
                        client_latest = payload["latest"] = self.bridge.state.latest()
                        self.wfile.write(f"data: {json.dumps(payload)}\n\n".encode())
                        self.wfile.flush()
                    time.sleep(self.stream_interval)
            except (BrokenPipeError, ConnectionResetError, OSError):
                return

        super().do_GET()

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/inputs":
            return self.send_error(HTTPStatus.NOT_FOUND)
        length = int(self.headers.get("Content-Length", "0") or 0)
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") if length else "{}")
        except ValueError:
            payload = None
        actions = payload.get("actions") if isinstance(payload, dict) else None
        if not isinstance(actions, list):
            return self._send_json({"status": "error", "error": 'expected {"actions": [...]}'}, HTTPStatus.BAD_REQUEST)
        self.bridge.apply_actions(actions)
        self._send_json({"status": "ok"})


def create_g3_server(
    bridge: SimConnectG3Bridge,
    host: str = "0.0.0.0",
    port: int = 8000,
    stream_interval: float = 0.1,
    static_dir: str | None = None,
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
