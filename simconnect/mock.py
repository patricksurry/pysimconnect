"""Generic MSFS 2020/2024 MockSimConnect for offline development, demos, and testing."""

import logging
import math
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from .changedict import ChangeDict
from .datadef import DataDefinition, SimData, SimDataHandler, SimVarsSpec, _norm_simvars
from .scdefs import DATATYPE_FLOAT64, DATATYPE_INT32, DATATYPE_STRING256
from .scvars import validate_event, validate_simvar

logger = logging.getLogger(__name__)

# Simple unit scale factors relative to default MSFS SimVar units
_UNIT_CONVERSIONS: dict[tuple[str, str], Callable[[float], float]] = {
    ("feet", "meters"): lambda ft: ft * 0.3048,
    ("meters", "feet"): lambda m: m / 0.3048,
    ("inhg", "hectopascal"): lambda hg: hg * 33.863886666667,
    ("inhg", "millibars"): lambda hg: hg * 33.863886666667,
    ("millibars", "inhg"): lambda mb: mb / 33.863886666667,
    ("hectopascal", "inhg"): lambda hpa: hpa / 33.863886666667,
    ("knots", "meters per second"): lambda kt: kt * 0.514444,
    ("radians", "degrees"): lambda rad: math.degrees(rad),
    ("degrees", "radians"): lambda deg: math.radians(deg),
}


def _convert_unit(val: Any, from_unit: Optional[str], to_unit: Optional[str]) -> Any:
    if not isinstance(val, (int, float)) or not from_unit or not to_unit:
        return val
    f_u, t_u = from_unit.lower(), to_unit.lower()
    if f_u == t_u:
        return val
    fn = _UNIT_CONVERSIONS.get((f_u, t_u))
    return fn(float(val)) if fn else val


class MockSimConnect:
    """Drop-in replacement for SimConnect that generates realistic synthetic flight telemetry."""

    def __init__(self, name: str = "MockSimConnect", verbose: bool = True, **kwargs: Any):
        self.name = name
        self.verbose = verbose
        self._closed = False
        self._datadefs: dict[str, DataDefinition] = {}
        self._subscriptions: list[tuple[DataDefinition, Optional[SimDataHandler]]] = []
        self._t0 = time.time()
        self._last_pump_tick = -1
        self._overrides: dict[str, Any] = {
            "BAROMETER PRESSURE": 1013.25,
            "HEADING OFFSET": 0.0,
            "NAV RADIAL:1": 45.0,
            "ADF CARD": 0.0,
            "ELECTRICAL MASTER BATTERY": 1,
            "GENERAL ENG GENERATOR ACTIVE:1": 1,
            "ELECTRICAL BATTERY BUS VOLTAGE": 24.5,
            "TITLE": "Cessna Skyhawk G1000 Asobo",
            "ATC ID": "ASXGS",
            "TRANSPONDER CODE:1": 1200,
            "SIM ON GROUND": 0,
        }
        self.event_history: list[tuple[str, int]] = []

    def __enter__(self) -> "MockSimConnect":
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.Close()

    def Close(self) -> int:
        self._closed = True
        return 0

    def AddToDataDefinition(self, *args: Any, **kwargs: Any) -> None:
        """No-op stub called by DataDefinition.__init__."""

    def _canonical_key(self, name: str) -> str:
        return name.upper().replace("_", " ")

    def _compute_simvar(self, name: str, target_units: Optional[str], dtyp: int) -> Any:
        key = self._canonical_key(name)
        t = time.time() - self._t0
        baro_mb = float(self._overrides.get("BAROMETER PRESSURE", 1013.25))
        alt_ft = float(
            self._overrides.get(
                "PLANE ALTITUDE",
                self._overrides.get(
                    "INDICATED ALTITUDE",
                    5500.0 + 250.0 * math.sin(t * 0.2) + (baro_mb - 1013.25) * 27.3,
                ),
            )
        )
        hdg_deg = (120.0 + 15.0 * math.sin(t * 0.15) + float(self._overrides.get("HEADING OFFSET", 0.0))) % 360.0

        dynamic: dict[str, tuple[Any, str]] = {
            "INDICATED ALTITUDE": (alt_ft, "feet"),
            "PLANE ALTITUDE": (alt_ft, "feet"),
            "PLANE ALT ABOVE GROUND": (max(0.0, alt_ft - 450.0), "feet"),
            "BAROMETER PRESSURE": (baro_mb, "millibars"),
            "KOHLSMAN SETTING MB": (baro_mb, "millibars"),
            "KOHLSMAN SETTING MB:1": (baro_mb, "millibars"),
            "KOHLSMAN SETTING HG": (baro_mb / 33.863886666667, "inHg"),
            "KOHLSMAN SETTING HG:1": (baro_mb / 33.863886666667, "inHg"),
            "HEADING INDICATOR": (hdg_deg, "degrees"),
            "MAGNETIC COMPASS": (hdg_deg, "degrees"),
            "ATTITUDE INDICATOR PITCH DEGREES": (4.0 * math.sin(t * 0.4), "degrees"),
            "PLANE PITCH DEGREES": (4.0 * math.sin(t * 0.4), "degrees"),
            "ATTITUDE INDICATOR BANK DEGREES": (12.0 * math.sin(t * 0.3), "degrees"),
            "PLANE BANK DEGREES": (12.0 * math.sin(t * 0.3), "degrees"),
            "TURN INDICATOR RATE": (1.5 * math.cos(t * 0.3), "degrees"),
            "TURN COORDINATOR BALL": (15.0 * math.sin(t * 0.5), "position"),
            "AIRSPEED INDICATED": (108.0 + 8.0 * math.cos(t * 0.2), "knots"),
            "AIRSPEED TRUE": (116.0 + 8.0 * math.cos(t * 0.2), "knots"),
            "VERTICAL SPEED": (400.0 * math.cos(t * 0.2), "feet/minute"),
            "ADF RADIAL": ((280.0 + 10.0 * math.sin(t * 0.1)) % 360.0, "degrees"),
            "ADF CARD": (float(self._overrides.get("ADF CARD", 0.0)) % 360.0, "degrees"),
            "NAV RADIAL:1": (float(self._overrides.get("NAV RADIAL:1", 45.0)) % 360.0, "degrees"),
            "NAV RADIAL ERROR:1": (4.0 * math.sin(t * 0.25), "degrees"),
            "NAV TOFROM:1": (1, "Enum"),
            "SUCTION PRESSURE": (5.2 + 0.05 * math.sin(t * 0.5), "inHg"),
            "ENG FUEL PRESSURE:1": (5.4 + 0.1 * math.sin(t * 0.7), "psi"),
            "ENG OIL PRESSURE:1": (78.0 + 1.5 * math.sin(t * 0.3), "psi"),
            "ENG OIL TEMPERATURE:1": (615.0 + 2.0 * math.sin(t * 0.1), "rankine"),
            "ENG MANIFOLD PRESSURE:1": (24.5 + 1.0 * math.sin(t * 0.25), "inHg"),
            "GENERAL ENG RPM:1": (2350.0 + 30.0 * math.sin(t * 0.25), "rpm"),
            "ENG CYLINDER HEAD TEMPERATURE:1": (810.0 + 4.0 * math.sin(t * 0.1), "rankine"),
            "PLANE LATITUDE": (47.4502 + 0.001 * math.sin(t * 0.05), "degrees"),
            "PLANE LONGITUDE": (-122.3088 + 0.001 * math.cos(t * 0.05), "degrees"),
            "ZULU TIME": ((time.time() % 86400), "seconds"),
            "ABSOLUTE TIME": (time.time() + 62135596800.0, "seconds"),
        }

        if key in self._overrides and key not in ("BAROMETER PRESSURE", "PLANE ALTITUDE", "INDICATED ALTITUDE"):
            val = self._overrides[key]
            sv = validate_simvar(name, settable=False)
            base_unit = (sv.get("units_std") or sv.get("units")) if sv else target_units
            return _convert_unit(val, base_unit, target_units)

        if key in dynamic:
            val, base_unit = dynamic[key]
            return _convert_unit(val, base_unit, target_units)

        if dtyp == DATATYPE_STRING256:
            return self._overrides.get(key, "MOCK")
        if dtyp == DATATYPE_INT32:
            return int(self._overrides.get(key, 0))
        return float(self._overrides.get(key, 0.0))

    def _populate_datadef(self, dd: DataDefinition) -> bool:
        latest_before = dd.simdata.latest()
        for d in dd.defs:
            dd.simdata[d["name"]] = self._compute_simvar(d["name"], d["units"], d["dtyp"])
        return dd.simdata.latest() > latest_before

    def get_simdatum(self, name: str, units: Optional[str] = None, timeout_seconds: float = 1.0) -> Any:
        return list(self.get_simdata([dict(name=name, units=units)], timeout_seconds=timeout_seconds).values())[0]

    def get_simdata(self, simvars: SimVarsSpec, timeout_seconds: float = 1.0) -> SimData:
        dd = DataDefinition.create(self, simvars)
        self._populate_datadef(dd)
        return dd.simdata

    def subscribe_simdata(
        self,
        simvars: SimVarsSpec,
        period: int = 0,
        skip_periods: int = 0,
        interval: int = 1,
        repeat_count: int = 0,
        flags: int = 0,
        callback: Optional[SimDataHandler] = None,
    ) -> DataDefinition:
        dd = DataDefinition.create(self, simvars)
        self._populate_datadef(dd)
        self._subscriptions.append((dd, callback))
        return dd

    def set_simdatum(self, name: str, value: Any, units: Optional[str] = None) -> None:
        self.set_simdata([dict(name=name, value=value, units=units)])

    def set_simdata(self, simdata: SimVarsSpec) -> None:
        for d in _norm_simvars(simdata):
            key = self._canonical_key(d["name"])
            sv = validate_simvar(d["name"], settable=True)
            base_unit = (sv.get("units_std") or sv.get("units")) if sv else d.get("units")
            val = _convert_unit(d.get("value"), d.get("units"), base_unit)
            self._overrides[key] = val
            if key == "INDICATED ALTITUDE":
                self._overrides["PLANE ALTITUDE"] = val
            elif key == "PLANE ALTITUDE":
                self._overrides["INDICATED ALTITUDE"] = val

    def send_event(self, event: str, data: int = 0) -> None:
        evt = validate_event(event)
        self.event_history.append((evt, data))
        if evt == "KOHLSMAN_INC":
            self._overrides["BAROMETER PRESSURE"] = float(self._overrides.get("BAROMETER PRESSURE", 1013.25)) + 0.34
        elif evt == "KOHLSMAN_DEC":
            self._overrides["BAROMETER PRESSURE"] = float(self._overrides.get("BAROMETER PRESSURE", 1013.25)) - 0.34
        elif evt == "HEADING_BUG_INC":
            self._overrides["AUTOPILOT HEADING LOCK DIR"] = (
                float(self._overrides.get("AUTOPILOT HEADING LOCK DIR", 0.0)) + 1.0
            ) % 360
        elif evt == "HEADING_BUG_DEC":
            self._overrides["AUTOPILOT HEADING LOCK DIR"] = (
                float(self._overrides.get("AUTOPILOT HEADING LOCK DIR", 0.0)) - 1.0
            ) % 360
        elif evt == "VOR1_OBI_INC":
            self._overrides["NAV RADIAL:1"] = float(self._overrides.get("NAV RADIAL:1", 45.0)) + 1.0
        elif evt == "VOR1_OBI_DEC":
            self._overrides["NAV RADIAL:1"] = float(self._overrides.get("NAV RADIAL:1", 45.0)) - 1.0
        elif evt == "ADF_CARD_INC":
            self._overrides["ADF CARD"] = float(self._overrides.get("ADF CARD", 0.0)) + 1.0
        elif evt == "ADF_CARD_DEC":
            self._overrides["ADF CARD"] = float(self._overrides.get("ADF CARD", 0.0)) - 1.0

    def receive(self, timeout_seconds: Optional[float] = None) -> bool:
        """Pump mock subscriptions at most once per 20ms slice so `while sc.receive(): pass` terminates."""
        tick = int(time.time() * 50)
        if tick == self._last_pump_tick:
            return False
        self._last_pump_tick = tick
        any_updated = False
        for dd, callback in self._subscriptions:
            if self._populate_datadef(dd):
                any_updated = True
                if callback:
                    callback(dd.simdata)
        return any_updated
