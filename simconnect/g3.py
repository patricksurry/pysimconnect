"""Lightweight, zero-dependency HTTP + SSE server bridging SimConnect to G3 instrument panels."""
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import math
import threading
import time
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from .changedict import ChangeDict
from .sc import SimConnect
from .scdefs import PERIOD_VISUAL_FRAME

logger = logging.getLogger(__name__)

# Mapping from G3 supported units (convert-units) to equivalent MSFS units
G3_TO_MSFS_UNITS: Dict[str, List[str]] = {
    "ft": ["feet", "foot"],
    "deg": ["degrees", "degree"],
    "rad": ["radians", "radian"],
    "knot": ["knots", "knot"],
    "R": ["rankine"],
    "C": ["celsius"],
    "F": ["fahrenheit"],
    "rpm": ["rpm", "r.p.m."],
    "inHg": ["inhg", "inches of mercury", "inch of mercury"],
    "rad/s": ["radians per second", "radian per second"],
    "ft/min": ["feet/minute", "feet per minute"],
    "ft/s": ["feet/second", "feet per second"],
    "hPa": ["millibars", "millibar", "hectopascals", "hectopascal"],
    "gal": ["gallons", "gallon"],
    "psi": ["psi", "pounds per square inch"],
}

MSFS_TO_G3_UNIT: Dict[str, str] = {
    msfs_u.lower(): g3_u
    for g3_u, msfs_list in G3_TO_MSFS_UNITS.items()
    for msfs_u in msfs_list
}

DEFAULT_CONFIG: Dict[str, Any] = {
    "metrics": [
        # Nav panel
        {"metric": "heading", "simvar": "HEADING INDICATOR"},
        {"metric": "altitude", "simvar": "INDICATED ALTITUDE"},
        {"metric": "pressureSetting", "simvar": "BAROMETER PRESSURE"},
        {"metric": "pitch", "simvar": "ATTITUDE INDICATOR PITCH DEGREES"},
        {"metric": "roll", "simvar": "ATTITUDE INDICATOR BANK DEGREES"},
        {"metric": "turnrate", "simvar": "TURN INDICATOR RATE"},
        {"metric": "slip", "simvar": "TURN COORDINATOR BALL", "fx": "x / 5", "fxunit": "deg"},
        {"metric": "airspeed", "simvar": "AIRSPEED INDICATED"},
        {"metric": "verticalSpeed", "simvar": "VERTICAL SPEED"},
        # ADF gauge
        {"metric": "relativeADF", "simvar": "ADF RADIAL"},
        {"metric": "headingADF", "simvar": "ADF CARD"},
        # VOR gauge
        {"metric": "radialVOR", "simvar": "NAV RADIAL:1"},
        {"metric": "radialDeviation", "simvar": "NAV RADIAL ERROR:1"},
        {"metric": "toFromVOR", "simvar": "NAV TOFROM:1", "fx": "-1 if x == 2 else x", "fxunit": None},
        # Compass
        {"metric": "compass", "simvar": "MAGNETIC COMPASS"},
        # Engine / Center panel (DHC-2 Beaver)
        {"metric": "suctionPressure", "simvar": "SUCTION PRESSURE"},
        {"metric": "fuel.front", "simvar": "FUEL SELECTED QUANTITY:2"},
        {"metric": "fuel.center", "simvar": "FUEL SELECTED QUANTITY:3"},
        {"metric": "fuel.rear", "simvar": "FUEL SELECTED QUANTITY:6"},
        {
            "metric": "fuelSelector",
            "simvar": "FUEL TANK SELECTOR:1",
            "fx": "{1: 'front', 2: 'front', 3: 'center', 6: 'rear'}.get(x, 'front')",
            "fxunit": None,
        },
        {"metric": "fuelPressure", "simvar": "ENG FUEL PRESSURE:1", "unit": "psi"},
        {"metric": "oilPressure", "simvar": "ENG OIL PRESSURE:1", "unit": "psi"},
        {"metric": "oilTemperature", "simvar": "ENG OIL TEMPERATURE:1"},
        {"metric": "manifoldPressure", "simvar": "ENG MANIFOLD PRESSURE:1"},
        {"metric": "engineRPM", "simvar": "GENERAL ENG RPM:1"},
        {"metric": "cylinderHeadTemp", "simvar": "ENG CYLINDER HEAD TEMPERATURE:1"},
        {"metric": "fuelWarning", "simvar": "WARNING FUEL"},
        {"metric": "oilPressureWarning", "simvar": "WARNING OIL PRESSURE"},
    ],
    "actions": [
        {"input": "ALT-ROT", "method": "incdec", "event": ["KOHLSMAN_INC", "KOHLSMAN_DEC"]},
        {"input": "ATT-BTN", "event": "ATTITUDE_CAGE_BUTTON"},
        {"input": "ATT-ROT", "method": "incdec", "event": ["ATTITUDE_BARS_POSITION_UP", "ATTITUDE_BARS_POSITION_DOWN"]},
        {"input": "VOR-ROT", "method": "incdec", "event": ["VOR1_OBI_INC", "VOR1_OBI_DEC"]},
        {"input": "ADF-ROT", "method": "incdec", "event": ["ADF_CARD_INC", "ADF_CARD_DEC"]},
        {"input": "HDG-ROT", "method": "incdec", "event": ["HEADING_BUG_INC", "HEADING_BUG_DEC"]},
        {"input": "MASTER0", "simvar": "GENERAL ENG GENERATOR ACTIVE:1"},
        {"input": "MASTER1", "simvar": "ELECTRICAL MASTER BATTERY"},
        {"input": "PRIMER", "simvar": "ENGINE PRIMER"},
        {"input": "MIXTURE", "simvar": "GENERAL ENG MIXTURE LEVER POSITION:1"},
        {"input": "SW1-1", "method": "set", "event": "PARKING_BRAKE_SET"},
        {"input": "SW1-2", "method": "set", "event": "STROBES_SET"},
        {"input": "SW1-3", "method": "set", "event": "LANDING_LIGHTS_SET"},
        {"input": "SW2-1", "method": "set", "event": "BEACON_LIGHTS_SET"},
        {"input": "SW2-2", "method": "set", "event": "NAV_LIGHTS_SET"},
        {"input": "SW2-5", "method": "set", "event": "PITOT_HEAT_SET"},
        {"input": "SW3-1", "event": "TOGGLE_ELECT_FUEL_PUMP"},
        {"input": "fuelWarning", "output": "RED_WARNING"},
        {"input": "oilPressureWarning", "output": "ORANGE_WARNING"},
    ],
}


PANEL_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>pysimconnect × G3 — Live Flight Deck</title>
  <style>
    body {
      margin: 0;
      background: #111827;
      color: #f3f4f6;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    header {
      width: 100%;
      background: #0b0f19;
      border-bottom: 1px solid #374151;
      padding: 0.65rem 1.5rem;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
      box-sizing: border-box;
    }
    .title { font-weight: 700; font-size: 1rem; color: #38bdf8; }
    .toolbar { display: flex; flex-wrap: wrap; gap: 0.45rem; align-items: center; }
    button, a.btn {
      background: #1f2937;
      color: #e5e7eb;
      border: 1px solid #374151;
      border-radius: 0.4rem;
      padding: 0.35rem 0.7rem;
      font-size: 0.82rem;
      cursor: pointer;
      text-decoration: none;
    }
    button:hover, a.btn:hover { border-color: #38bdf8; color: #fff; }
    button.active { background: #0284c7; border-color: #38bdf8; color: #fff; }
    #panel-host {
      margin-top: 0.5rem;
      display: flex;
      justify-content: center;
      width: 100%;
    }
    svg.g3-panel { background: #18181b; border-radius: 0.75rem; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
  </style>
  <script src="https://unpkg.com/@patricksurry/g3/dist/g3-contrib.min.js"></script>
</head>
<body>
  <header>
    <div class="title">✈️ pysimconnect × G3 Live Panel</div>
    <div class="toolbar">
      <a class="btn" id="btn-nav" href="/?panel=nav">🧭 DHC-2 Nav Panel</a>
      <a class="btn" id="btn-engine" href="/?panel=engine">⚙️ DHC-2 Engine Panel</a>
      <span style="color:#6b7280;margin:0 0.25rem;">|</span>
      <button onclick="sendInput({'ALT-ROT': -1})">Baro −</button>
      <button onclick="sendInput({'ALT-ROT': 1})">Baro +</button>
      <button onclick="sendInput({'HDG-ROT': -5})">HDG −</button>
      <button onclick="sendInput({'HDG-ROT': 5})">HDG +</button>
      <button onclick="sendInput({'VOR-ROT': -5})">OBS −</button>
      <button onclick="sendInput({'VOR-ROT': 5})">OBS +</button>
      <button onclick="sendInput({'ADF-ROT': -5})">ADF −</button>
      <button onclick="sendInput({'ADF-ROT': 5})">ADF +</button>
      <button onclick="sendInput({'ATT-BTN': 1})">Cage AI</button>
    </div>
  </header>
  <div id="panel-host"></div>
  <script>
    async function sendInput(payload) {
      await fetch('/inputs', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      });
    }

    const params = new URLSearchParams(window.location.search);
    const mode = params.get('panel') || 'nav';
    document.getElementById(mode === 'engine' ? 'btn-engine' : 'btn-nav').classList.add('active');

    if (mode === 'engine') {
      g3.panel()
        .width(1024)
        .height(768)
        .interval(0)
        .url('/stream')
        .append(
          g3.put().x(170).y(190).scale(1.1).append(g3.contrib.engine.suctionPressure.DHC2()),
          g3.put().x(512).y(190).scale(1.1).append(g3.contrib.engine.fuel.DHC2()),
          g3.put().x(854).y(190).scale(1.1).append(g3.contrib.engine.oilFuelStatus.DHC2()),
          g3.put().x(320).y(540).scale(1.55).append(g3.contrib.engine.manifoldPressure.DHC2()),
          g3.put().x(704).y(540).scale(1.55).append(g3.contrib.engine.tachometer.DHC2())
        )('#panel-host');
    } else {
      g3.panel()
        .width(1024)
        .height(640)
        .interval(0)
        .url('/stream')
        .append(
          g3.put().x(128).y(180).scale(0.9).append(g3.contrib.nav.airspeed.DHC2()),
          g3.put().x(384).y(180).scale(0.9).append(g3.contrib.nav.attitude.generic()),
          g3.put().x(640).y(180).scale(0.9).append(g3.contrib.nav.altitude.generic()),
          g3.put().x(896).y(180).scale(0.9).append(g3.contrib.radionav.VOR.generic()),
          g3.put().x(128).y(448).scale(0.9).append(g3.contrib.nav.turnCoordinator.generic()),
          g3.put().x(384).y(448).scale(0.9).append(g3.contrib.nav.heading.generic()),
          g3.put().x(640).y(448).scale(0.9).append(g3.contrib.nav.VSI.generic()),
          g3.put().x(896).y(448).scale(0.9).append(g3.contrib.radionav.ADF.generic())
        )('#panel-host');
    }
  </script>
</body>
</html>
"""


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    if not config_path:
        return json.loads(json.dumps(DEFAULT_CONFIG))
    with open(config_path, "r") as f:
        if config_path.endswith((".yml", ".yaml")):
            try:
                from ruamel.yaml import YAML
                return YAML(typ="safe").load(f)
            except ImportError:
                import yaml  # type: ignore
                return yaml.safe_load(f)
        return json.load(f)


class SimConnectG3Bridge:
    """Polls SimConnect (or synthetic mock telemetry) and serves G3 metrics/actions."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, mock: bool = False):
        self.cfg = config or json.loads(json.dumps(DEFAULT_CONFIG))
        self.mapping: List[Dict[str, Any]] = self.cfg.get("metrics", [])
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
            "pitch_ trim": 0.0,
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
                sv = m["simvar"]
                if sv in simvar_units and simvar_units[sv]:
                    u = simvar_units[sv]
                    m["unit"] = MSFS_TO_G3_UNIT.get(u.lower(), u)
                else:
                    m.setdefault("unit", None)
        else:
            # Populate standard G3 units for mock mode
            default_mock_units = {
                "heading": "deg",
                "altitude": "ft",
                "pressureSetting": "hPa",
                "pitch": "deg",
                "roll": "deg",
                "turnrate": "deg",
                "slip": "deg",
                "airspeed": "knot",
                "verticalSpeed": "ft/min",
                "relativeADF": "deg",
                "headingADF": "deg",
                "radialVOR": "deg",
                "radialDeviation": "deg",
                "compass": "deg",
                "suctionPressure": "inHg",
                "fuel.front": "gal",
                "fuel.center": "gal",
                "fuel.rear": "gal",
                "fuelPressure": "psi",
                "oilPressure": "psi",
                "oilTemperature": "R",
                "manifoldPressure": "inHg",
                "engineRPM": "rpm",
                "cylinderHeadTemp": "R",
            }
            for m in self.mapping:
                m.setdefault("unit", default_mock_units.get(m["metric"]))

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
                    name = m["metric"]
                    sv = m["simvar"]
                    if (metrics and name not in metrics) or sv not in recent:
                        continue
                    v = recent[sv]
                    if "fx" in m:
                        v = eval(m["fx"], {"__builtins__": {}}, {"x": v})
                    data[name] = v

            self._update_with_triggers(data)
            return data

    def _generate_mock_metrics(self, metrics: Optional[List[str]] = None) -> Dict[str, Any]:
        t = time.time() - self._t0
        baro = self._mock_offsets["pressureSetting"]
        alt_offset = (baro - 1013.25) * 27.3
        raw = {
            "heading": (120.0 + 15.0 * math.sin(t * 0.15) + self._mock_offsets["heading"]) % 360.0,
            "altitude": 5500.0 + 250.0 * math.sin(t * 0.2) + alt_offset,
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
            "suctionPressure": 5.2 + 0.1 * math.sin(t * 0.5),
            "fuel.front": 22.5,
            "fuel.center": 24.0,
            "fuel.rear": 16.0,
            "fuelSelector": "front",
            "fuelPressure": 5.4 + 0.2 * math.sin(t * 0.7),
            "oilPressure": 78.0 + 2.0 * math.sin(t * 0.3),
            "oilTemperature": 615.0 + 3.0 * math.sin(t * 0.1),
            "manifoldPressure": 28.5 + 1.5 * math.sin(t * 0.25),
            "engineRPM": 1950.0 + 40.0 * math.sin(t * 0.25),
            "cylinderHeadTemp": 810.0 + 5.0 * math.sin(t * 0.1),
            "fuelWarning": 0,
            "oilPressureWarning": 0,
        }
        if metrics:
            return {k: v for k, v in raw.items() if k in metrics}
        return raw

    def _update_with_triggers(self, d: Dict[str, Any]) -> None:
        latest = self.state.latest()
        self.state.update(d)
        changed = self.state.changedsince(latest)
        if changed:
            out = self.trigger_actions(changed)
            if out:
                self.state.update(out)

    def handle_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            out = self.trigger_actions(inputs)
            if out:
                self.state.update(out)
            return out

    def trigger_actions(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        outputs: Dict[str, Any] = {}
        for k, raw_v in inputs.items():
            # Apply mock interactive adjustments so buttons visibly move mock needles
            if self.mock:
                if k == "ALT-ROT":
                    self._mock_offsets["pressureSetting"] += float(raw_v) * 0.34
                elif k == "HDG-ROT":
                    self._mock_offsets["heading"] += float(raw_v)
                elif k == "VOR-ROT":
                    self._mock_offsets["radialVOR"] += float(raw_v)
                elif k == "ADF-ROT":
                    self._mock_offsets["headingADF"] += float(raw_v)

            rules = [r for r in self.actions if r.get("input") == k]
            for rule in rules:
                v = eval(rule["fx"], {"__builtins__": {}}, {"x": raw_v}) if "fx" in rule else raw_v
                if "output" in rule:
                    outputs[rule["output"]] = v
                elif "simvar" in rule and self.sc is not None:
                    self.sc.set_simdatum(rule["simvar"], v)
                elif "event" in rule and self.sc is not None:
                    name = rule["event"]
                    method = rule.get("method")
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


def create_g3_server(
    bridge: SimConnectG3Bridge,
    host: str = "0.0.0.0",
    port: int = 8000,
    stream_interval: float = 0.1,
) -> ThreadingHTTPServer:
    """Create a ThreadingHTTPServer serving G3 /stream, /metrics.json, /inputs, and the live panel UI."""

    class G3RequestHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt: str, *args: Any) -> None:
            logger.debug(fmt, *args)

        def _send_cors_headers(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "*")

        def do_OPTIONS(self) -> None:
            self.send_response(HTTPStatus.NO_CONTENT)
            self._send_cors_headers()
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            qs = parse_qs(parsed.query)

            if path in ("/", "/index.html", "/panels/dhc2-nav.html", "/panels/dhc2-center.html", "/panels/panel.html"):
                body = PANEL_HTML.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self._send_cors_headers()
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if path == "/metrics.json":
                metrics_arg = qs.get("metrics", [""])[0]
                ms = [m for m in metrics_arg.split(",") if m] if metrics_arg else None
                latest = int(qs.get("latest", ["0"])[0] or 0)
                want_units = qs.get("units", ["false"])[0].lower() in ("true", "1", "yes")

                bridge.poll_metrics(ms)
                changed = {
                    k: v
                    for k, v in bridge.state.changedsince(latest).items()
                    if not ms or k in ms
                }
                result: Dict[str, Any] = {
                    "latest": bridge.state.latest(),
                    "metrics": changed,
                }
                if want_units:
                    result["units"] = {
                        k: v
                        for k, v in bridge.metric_units().items()
                        if not ms or k in ms
                    }
                body = json.dumps(result).encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if path == "/stream":
                self.send_response(HTTPStatus.OK)
                self._send_cors_headers()
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.end_headers()

                client_latest = 0
                sent_units = False
                try:
                    while True:
                        bridge.poll_metrics()
                        deltas = bridge.state.changedsince(client_latest)
                        if deltas or not sent_units:
                            client_latest = bridge.state.latest()
                            payload: Dict[str, Any] = {"metrics": deltas if sent_units else dict(bridge.state)}
                            if not sent_units:
                                payload["units"] = bridge.metric_units()
                                sent_units = True
                            chunk = f"data: {json.dumps(payload)}\n\n".encode("utf-8")
                            self.wfile.write(chunk)
                            self.wfile.flush()
                        time.sleep(stream_interval)
                except (BrokenPipeError, ConnectionResetError, OSError):
                    return

            self.send_error(HTTPStatus.NOT_FOUND, f"Unknown endpoint: {path}")

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != "/inputs":
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            length = int(self.headers.get("Content-Length", "0") or 0)
            raw_body = self.rfile.read(length) if length > 0 else b"{}"
            payload = json.loads(raw_body.decode("utf-8") or "{}")
            outputs = bridge.handle_inputs(payload)
            resp = json.dumps({"status": "ok", "outputs": outputs}).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

    server = ThreadingHTTPServer((host, port), G3RequestHandler)
    server.daemon_threads = True
    return server
