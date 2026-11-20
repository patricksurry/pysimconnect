# `pysimconnect` API & Architecture Reference

This reference sits alongside the [Quick Start tutorial](../README.md) and the [Interactive SDK Metrics & Events Explorer](index.html).

---

## 1. Architecture Overview

`pysimconnect` is structured in two layers over Microsoft Flight Simulator's `SimConnect.dll`:

1. **Low-level ctypes bindings (`simconnect.scdefs`)** — Auto-generated from `SimConnect.h`. Exposes all SDK constants (`PERIOD_*`, `DATATYPE_*`, `OBJECT_ID_USER`, `EXCEPTION_*`), `ctypes.Structure` packet definitions (`RECV`, `RECV_OPEN`, `RECV_EXCEPTION`, `RECV_SIMOBJECT_DATA`, etc.), and C function signatures (`_decls`).
2. **Pythonic wrapper (`simconnect.sc`, `simconnect.datadef`, `simconnect.scvars`, `simconnect.changedict`)** — Manages handle lifecycle, automatic unit and data-type inference from the scraped SDK catalog (`scvars.json`), message dispatching, and timestamped delta tracking (`ChangeDict`).

---

## 2. `SimConnect` Class (`simconnect.SimConnect`)

```python
from simconnect import SimConnect

with SimConnect(
    name="my_app",
    dll_path=...,               # Defaults to bundled SimConnect.dll
    default_receivers=...,      # Logs RECV_OPEN and RECV_EXCEPTION by default
    poll_interval_seconds=0.05, # Sleep interval when polling with timeout
    verbose=True,               # Set False to suppress connection error logs
) as sc:
    ...
```

### Core Methods

| Method | Signature | Description |
| :--- | :--- | :--- |
| `get_simdatum` | `(name: str, units: Optional[str] = None, timeout_seconds: float = 1) -> Any` | One-off blocking read of a single SimVar. Returns `None` if timed out. |
| `get_simdata` | `(simvars: SimVarsSpec, timeout_seconds: float = 1) -> SimData` | One-off blocking snapshot of one or more SimVars. Returns a `ChangeDict`. |
| `subscribe_simdata` | `(simvars: SimVarsSpec, period=PERIOD_SECOND, skip_periods=0, interval=1, repeat_count=0, flags=DATA_REQUEST_FLAG_CHANGED \| DATA_REQUEST_FLAG_TAGGED, callback: Optional[SimDataHandler] = None) -> DataDefinition` | Creates and subscribes to a recurring `DataDefinition`. Updates `dd.simdata` on each `sc.receive()` call and optionally invokes `callback(dd.simdata)`. |
| `set_simdatum` | `(name: str, value: Any, units: Optional[str] = None) -> None` | Sets a single writable SimVar on `OBJECT_ID_USER`. |
| `set_simdata` | `(simdata: SimVarsSpec) -> None` | Sets multiple writable SimVars in a single struct payload (`[{name, value, [units], [type]}, ...]`). |
| `send_event` | `(event: str, data: int = 0) -> None` | Maps (on first use) and transmits a client event (`KOHLSMAN_INC`, `AXIS_FLAPS_SET`, or custom addon events like `"MobiFlight.AS1000_PFD_JOYSTICK_UP"`). |
| `receive` | `(timeout_seconds: Optional[float] = None) -> bool` | Pumps the SDK dispatch queue via `CallDispatch`. Returns `True` if at least one packet was handled. |
| `add_receiver` | `(rtype: Type[RECV], receiver: Callable[[RECV], bool]) -> None` | Registers a custom packet handler for `RECV` subclasses. |
| `remove_receiver` | `(receiver: Callable[[RECV], bool]) -> bool` | Removes a previously registered packet handler. |
| `Close` | `() -> int` | Idempotently closes the underlying `SimConnect` handle (called automatically on context manager exit). |
| `<SDKMethod>` | `sc.<MethodName>(*args)` | Any `SimConnect_<MethodName>` function declared in `SimConnect.h` can be called directly on `sc` with `self.hsc` passed automatically as the first argument (and `str` arguments UTF-8 encoded). |

---

## 3. Specifying SimVars & `DataDefinition` (`simconnect.datadef`)

Functions accepting `simvars: SimVarsSpec` accept a single spec or a list of specs, where each spec is either:
- A **`str`** (e.g. `"Indicated Altitude"` or indexed `"GENERAL ENG RPM:1"`), using the default SDK unit and inferred `DATATYPE_*`, or
- A **`dict`**:
  ```python
  {
      "name": "Indicated Altitude",
      "units": "meters",          # Optional: override default SDK unit
      "type": DATATYPE_FLOAT64,   # Optional: override inferred DATATYPE_*
      "epsilon": 0.1,             # Optional: change threshold (default 1e-4 for float64, 0 for int/string)
  }
  ```

### Inferred Data Types (`type_for_unit`)

| SDK Unit Category | Inferred SimConnect Type | Python Type |
| :--- | :--- | :--- |
| `Bool`, `Boolean`, `Enum`, `Bco16`, `mask`, `flags` | `DATATYPE_INT32` (`c_int32`) | `int` |
| `string` | `DATATYPE_STRING256` (`char[256]`) | `str` |
| All physical & numeric miscellaneous units (`feet`, `knots`, `percent`, `position`, `number`, etc.) | `DATATYPE_FLOAT64` (`c_double`) | `float` |

### `DataDefinition` Attributes & Methods
- `dd.id: int` — SimConnect definition ID scoped to the parent `SimConnect` instance.
- `dd.simdata: ChangeDict` — Live dictionary of `{name: value}` updated as packets arrive.
- `dd.get_units() -> Dict[str, str]` — Returns `{name: resolved_unit}` for all variables in the definition.

---

## 4. `ChangeDict` (`simconnect.changedict.ChangeDict`)

`ChangeDict` subclasses `collections.OrderedDict` to record millisecond timestamps whenever an item changes beyond a configurable tolerance.

- `ChangeDict(default_comparator=equal_or_close(rel_tol=1e-6, abs_tol=1e-6), comparators=None)`
- `d.latest() -> int` — Millisecond timestamp of the most recently modified key (or `0` if empty).
- `d.changedsince(millis: int) -> Dict[str, Any]` — Returns a `dict` of all `{key: value}` pairs modified strictly after `millis`.

---

## 5. SDK Metadata Catalog (`simconnect.scvars`)

Loaded from `simconnect/scvars.json`:
- `SIMVARS: Dict[str, dict]` — `1,291` simulation variables keyed by canonical uppercase name (`"INDICATED ALTITUDE"`).
- `EVENTS: Dict[str, dict]` — `1,624` event IDs keyed by uppercase name (`"KOHLSMAN_INC"`).
- `UNITS: Dict[str, dict]` — `309` unit definitions keyed by canonical unit name.
- `DIMENSIONS: Dict[str, List[str]]` — Units grouped by physical dimension (`"Length"`, `"Speed"`, `"Miscellaneous Units"`, etc.).

Helper functions:
- `validate_simvar(name: str, settable: bool) -> Optional[Dict[str, Any]]`
- `validate_units(name: str, units: Optional[str], simvar: Optional[Dict[str, Any]]) -> str`
- `validate_event(event: str) -> str`
- `type_for_unit(unit: str) -> int`

---

## 6. Command-Line Interface (`simconnect`)

```bash
# Open the interactive SimVar Explorer in your browser
simconnect search altitude

# Read one or more SimVars
simconnect get PLANE_ALTITUDE AIRSPEED_INDICATED
simconnect get PLANE_ALTITUDE --units meters

# Watch SimVars continuously (highlighting changes)
simconnect watch PLANE_ALTITUDE AIRSPEED_INDICATED --interval 1

# Set a writable SimVar
simconnect set PLANE_ALTITUDE 1500 --units meters

# Trigger an Event ID (with optional integer value)
simconnect send KOHLSMAN_INC
simconnect send AXIS_FLAPS_SET 8192

# Serve G3-compatible metrics (/stream, /metrics.json, /inputs) and live DHC-2 panel UI
simconnect serve --port 8000
simconnect serve --mock --port 8000
```

---

## 7. G3 Instrument Panel Bridge (`simconnect.g3`) & Mock Simulator (`simconnect.mock`)

`simconnect.g3` provides a zero-dependency HTTP & Server-Sent Events (SSE) bridge compatible with [G3](https://github.com/patricksurry/g3) (`@patricksurry/g3`) instrument panels, and `simconnect.mock` provides a drop-in `MockSimConnect` generator for offline development and testing:

- `MockSimConnect(name="MockSimConnect")` — Implements the `SimConnect` interface (`get_simdatum`, `get_simdata`, `subscribe_simdata`, `set_simdatum`, `set_simdata`, `send_event`, `receive`, `Close`) with realistic synthetic flight telemetry, unit conversion, and event reactions (`KOHLSMAN_INC`/`DEC`, `HEADING_BUG_INC`/`DEC` on `AUTOPILOT HEADING LOCK DIR`, `VOR1_OBI_INC`/`DEC`, `ADF_CARD_INC`/`DEC`).
- `SimConnectG3Bridge(sc=None, config=None)` — A [G3 hub](https://github.com/patricksurry/g3/blob/master/doc/API.md#hubs) for any `SimConnect` (or `MockSimConnect`) instance. It subscribes to the configured SimVars, translates MSFS units to `convert-units` symbols (`ft`, `deg`, `knot`, `inHg`, `hPa`, etc.), evaluates optional `fx` transforms, and applies G3 actions with `apply_actions([...])`.
- `create_g3_server(bridge, host="0.0.0.0", port=8000, stream_interval=0.1, static_dir=None) -> ThreadingHTTPServer`:
  - `GET /` — Serves static panel files from `static_dir` (defaulting to the bundled `simconnect/g3/` panel).
  - `GET /stream?keys=a,b` — SSE stream (`text/event-stream`) emitting `data: {"latest": ..., "metrics": {...}, "units": {...}}\n\n`. It starts with a full snapshot of the matching metrics, then sends only changes.
  - `GET /metrics.json?keys=a,b&latest=0&units=true` — Polling endpoint returning the matching metrics that changed since `latest`.
  - `POST /inputs` — Applies a batch of G3 actions in order, e.g. `{"actions": [{"op": "adjust", "metric": "headingBug", "by": 5}]}`, and returns `{"status": "ok"}`. Anything else gets a 400. Action effects come back as ordinary metric changes.

  A metric matches the requested `keys` if it equals a key or is a dot-separated prefix of one, e.g. `fuel` matches `fuel.left`.

  The config file's `metrics` list maps SimVars to G3 metric names, and its `actions` list maps G3 actions to the sim:
  - `{"op": "set", "metric": "masterBattery", "simvar": "ELECTRICAL MASTER BATTERY"}` writes the value to a SimVar; use `"simevent": "NAME"` instead to send an event with the value.
  - `{"op": "adjust", "metric": "headingBug", "simevent": ["HEADING_BUG_INC", "HEADING_BUG_DEC"]}` sends the inc or dec event `abs(by)` times. With `"simvar"` instead, it writes the metric's current value plus `by`, applying any `min` / `max` / `wrap` hints.
  - `{"op": "trigger", "event": "attitudeCage", "simevent": "ATTITUDE_CAGE_BUTTON"}` sends an event.

  Any rule can add an `fx` expression in `x` to transform the value before it's written. Unsupported actions, or actions in an unexpected unit, are logged and ignored.
