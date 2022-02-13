from typing import List, Sequence, Union, Dict, Any, Callable, Optional, Type, TYPE_CHECKING
import logging
import json
from hashlib import sha1
from difflib import get_close_matches
from ctypes import cast, byref, sizeof, POINTER, c_float, c_double, c_longlong
from ctypes.wintypes import DWORD

from .scvars import _scvars, _namestd, _unitstd
from .scdefs import (
    Struct1, RECV_SIMOBJECT_DATA, DATA_REQUEST_FLAG_TAGGED,
    DATATYPE_INT32, DATATYPE_INT64, DATATYPE_FLOAT32, DATATYPE_FLOAT64,
)
from .changedict import ChangeDict
if TYPE_CHECKING:
    from .sc import SimConnect

EPSILON_DEFAULT = 1e-4


SimData = Dict[str, Any]
SimDataHandler = Callable[[SimData], None]
SimVarSpec = Union[str, Dict[str, Any]]
SimVarsSpec = Union[SimVarSpec, Sequence[SimVarSpec]]
"""
simvars can be specified as:
- a single simvar as a string like "Indicated Altitude"
- a single simvar as a dict of {name: , [units: ], [type: ], [epsilon: ]}
- a list containing a one or more individual simvars

name: a string matching a SDK variable (case insenstive),
    note that simvar names are typically space-separated words,
    while event names are underscore-separated.
    Indexed variables need a 1-based index, e.g. "ENG MANIFOLD PRESSURE:1"

units: a string from scvars.json::UNITS as defined in the SDK,
    if not present will be inferred using the default from the SDK,
    via scvars.json::VARIABLES

type: one of the scdefs.py::DATATYPE_* constants (currently only numeric types are supported),
    defaulting to DATATYPE_FLOAT64

epsilon: the precision to detect changes (see SDK), defaulting to 0.0001
"""
def _norm_simvars(simvars: SimVarsSpec) -> Sequence[Dict[str, Any]]:
    ds = simvars if isinstance(simvars, (list, tuple)) else [simvars]
    return [dict(name=d) if isinstance(d, str) else d for d in ds]


class DataDefinition:
    _instances: Dict[str, 'DataDefinition'] = {}

    @classmethod
    def create(kls, sc: 'SimConnect', simvars: SimVarsSpec, settable=False) -> 'DataDefinition':
        """create or retrieve a data definition for the specified variables"""
        defs: List[Dict[str, Any]] = []
        svs = _norm_simvars(simvars)
        for d in svs:
            name = d['name']
            base = _namestd(d['name'])
            sv = SIMVARS.get(base, {})
            if not sv:
                logging.warning(f"SimConnect: unrecognized simvar '{base}', {_closemsg(base, SIMVARS)}")
            else:
                if sv['indexed'] and ':' not in name:
                    logging.warning(f"SimConnect: expected indexed simvar, e.g. {name}:3")
                if settable and not sv.get('settable'):
                    logging.warning(f"SimConnect: simvar {name} is not settable")
            # lookup default units if not provided, note units='' is valid
            v = d.get('units')
            if v is None:
                if sv is not None:
                    # If not specified, try inferring units from variable
                    units = sv.get('units_std', '')
                else:
                    units = ''
                if not units:
                    logging.warning(f"SimConnect: no units specified or inferred for {name}")
            else:
                # standardize the units
                units = _unitstd(v)[0]
                if units not in UNITS:
                    logging.warning(f"SimConnect: unrecognized units '{v}' for {name}, {_closemsg(units, UNITS)}")
                else:
                    units = UNITS[units]['name_std']
            dtyp = d.get('type', DATATYPE_FLOAT64)
            epsilon = d.get('epsilon', EPSILON_DEFAULT)
            defs.append(dict(name=name, units=units, dtyp=dtyp, epsilon=epsilon))

        key = sha1(json.dumps(defs, sort_keys=True).encode('utf-8')).hexdigest()
        if key not in kls._instances:
            kls._instances[key] = kls(sc, len(kls._instances), defs)
        return kls._instances[key]

    def __init__(self, sc: 'SimConnect', def_id: int, defs: List[Dict[str, Any]]):
        self.id = def_id
        self.simdata: SimData = ChangeDict()
        self._struct: Optional[Type[Struct1]] = None
        self.defs = defs
        for i, d in enumerate(self.defs):
            sc.AddToDataDefinition(self.id, d['name'], d['units'], d['dtyp'], d['epsilon'], i)

    def get_units(self) -> Dict[str, str]:
        return {d['name']: d['units'] for d in self.defs}

    def add_receiver(self, sc: 'SimConnect', req_id: int, callback: Optional[SimDataHandler] = None):
        """Create a receiver for this DataDefinition, given req_id and optional callback"""
        def _receiver(recv: RECV_SIMOBJECT_DATA) -> bool:
            if recv.dwRequestID != req_id:
                return False

            logging.debug(f"DataDefinition[{self.id}]: Reading RECV_SIMOBJECT_DATA for request {req_id}")
            # dwData is a placeholder for where the data values start
            # so get a void* to that location and cast appropriately
            offset = RECV_SIMOBJECT_DATA.dwData.offset
            tagged = recv.dwFlags & DATA_REQUEST_FLAG_TAGGED > 0

            idx = -1
            for _ in range(recv.dwDefineCount):
                if tagged:
                    idx = cast(byref(recv, offset), POINTER(DWORD))[0]
                    offset += sizeof(DWORD)
                else:
                    idx += 1
                d = self.defs[idx]
                ctyp = _dtyps[d['dtyp']]
                val = cast(byref(recv, offset), POINTER(ctyp))[0]
                offset += sizeof(ctyp)
                self.simdata[d['name']] = val

            if callback:
                callback(self.simdata)
            return True

        sc.add_receiver(RECV_SIMOBJECT_DATA, _receiver)

    def _pack_data(self, simdata: Dict[str, Any]) -> Struct1:
        if self._struct is None:
            class kls(Struct1):
                _fields_ = [(d['name'], _dtyps[d['dtyp']]) for d in self.defs]
            self._struct = kls

        return self._struct(**simdata)


def _map_event_id(sc: 'SimConnect', event: str) -> int:
    s = event.upper()
    if s not in EVENTS:
        logging.warn(f"Unrecognized event {event}")
    client_id = _event_ids.get(s)
    if client_id is None:
        client_id = len(_event_ids)
        _event_ids[s] = client_id
        sc.MapClientEventToSimEvent(client_id, s)
    return client_id


def _closemsg(s, ss):
    xs = get_close_matches(s, ss)
    return f"perhaps one of {', '.join(xs)}?" if xs else "found nothing similar."


# Map scdefs type flags to ctypes
_dtyps = {
    DATATYPE_INT32: DWORD,   # 32-bit integer number
    DATATYPE_INT64: c_longlong,   # 64-bit integer number
    DATATYPE_FLOAT32: c_float,   # 32-bit floating-point number (float)
    DATATYPE_FLOAT64: c_double,   # 64-bit floating-point number (double)
}
# Track client-mapped event ids
_event_ids: Dict[str, int] = {}

SIMVARS = _scvars['VARIABLES']
EVENTS = _scvars['EVENTS']
UNITS = _scvars['UNITS']
