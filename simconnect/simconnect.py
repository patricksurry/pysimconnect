from typing import Dict, List, Union, Any, Optional
from ctypes import cast, byref, sizeof, windll, POINTER, c_float, c_double, c_longlong
from ctypes.wintypes import HANDLE, DWORD
import itertools
import logging
import os
from time import time, sleep
from scdefs import (
    _decls, Struct1, RECV, RECV_EXCEPTION, RECV_SIMOBJECT_DATA,
    DATATYPE_INT32, DATATYPE_INT64, DATATYPE_FLOAT32, DATATYPE_FLOAT64,
    DATA_REQUEST_FLAG_CHANGED, DATA_REQUEST_FLAG_TAGGED,
    OBJECT_ID_USER, PERIOD_SECOND,
)
from scdefs import *   # just for ease of downstream import
from changedict import ChangeDict


RECV_P = POINTER(RECV)

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


class SimConnect:
    def __init__(self, name='pySimConnect', dll_path='SimConnect.dll'):
        try:
            dll = windll.LoadLibrary(dll_path)
        except Exception:
            logging.error(f"Failed to load SimConnect DLL from {dll_path}")
            raise
        self._decls = _decls(dll)
        self.hsc = HANDLE()
        # All methods other than open pass the sc HANDLE as the first arg
        try:
            self._decls['Open'](byref(self.hsc), name.encode('utf-8'), None, 0, 0, 0)
        except OSError:
            logging.error("Failed to open SimConnect, is Flight Simulator running?")
            raise
        self._reqid_iter = itertools.count()
        self._defid_iter = itertools.count()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.Close()

    def _dispatch(self, f):
        """Dispatch to a registered method, using our open handle"""
        def _callable(*args):
            args = [arg.encode('utf-8') if isinstance(arg, str) else arg for arg in args]
            return f(self.hsc, *args)
        return _callable

    def _cast_recv(self, pRecv) -> RECV:   #TODO type annotation : pointer[RECV] per https://github.com/python/mypy/issues/7540
        recv_id = pRecv.contents.dwID
        if recv_id in _recv_map:
            pRecv = cast(pRecv, POINTER(_recv_map[recv_id]))
        return pRecv.contents

    def _get_simdata(
            self,
            recv: RECV_SIMOBJECT_DATA,
            dtyp=DATATYPE_FLOAT64,
            ) -> Union[List[Any], Dict[int, Any]]:

        ctyp = _dtyps[dtyp]
        # dwData is a placeholder for where the data values start
        # so get a void* to that location and cast appropriately
        p = byref(recv, RECV_SIMOBJECT_DATA.dwData.offset)
        items = recv.dwDefineCount
        if recv.dwFlags & DATA_REQUEST_FLAG_TAGGED:
            class Datum(Struct1):
                _fields_ = [("idx", DWORD), ("value", ctyp)]
            ds = cast(p, POINTER(Datum))
            return {ds[i].idx: ds[i].value for i in range(items)}
        else:
            ds = cast(p, POINTER(ctyp))
            return [ds[i] for i in range(items)]

    def __getattr__(self, k):
        if k in self._decls:
            return self._dispatch(self._decls[k])
        # Default behaviour
        raise AttributeError

    def receiveNext(self, timeout_seconds=None) -> Optional[RECV]:
        pRecv = RECV_P()
        nSize = DWORD()
        t0 = time()
        recv = None
        while True:
            logging.debug('sc.receiveNext: GetNextDispatch()')
            try:
                self.GetNextDispatch(byref(pRecv), byref(nSize))
            except OSError:
                logging.debug('sc.receiveNext: OSError')
                if timeout_seconds and time() - t0 < timeout_seconds:
                    sleep(0.1)
                    continue
                else:
                    break

            recv = self._cast_recv(pRecv)
            logging.debug(f"sc.receiveNext: received {recv.__class__.__name__}")
            if isinstance(recv, RECV_EXCEPTION):
                logging.warning(
                    f"sc.receiveNext: exception {recv.dwException}, sendID {recv.dwSendID}, index {recv.dwIndex}"
                )
            break
        return recv

    def subscribeSimObjects(
            self, simvars: List[Dict], def_id=None,
            req_id=None, period=PERIOD_SECOND, interval=1) -> 'DataSubscription':
        ds = DataSubscription(self, simvars, def_id, req_id)
        self.RequestDataOnSimObject(
            ds.req_id,  # request identifier for response packets
            ds.def_id,  # the data definition group
            OBJECT_ID_USER,
            PERIOD_SECOND,
            DATA_REQUEST_FLAG_CHANGED | DATA_REQUEST_FLAG_TAGGED,
            0,  # number of periods before starting events
            period,  # number of periods between events, e.g. with PERIOD_SIM_FRAME
            0,  # number of repeats, 0 is forever
        )
        return ds


class DataSubscription:
    def __init__(self, sc: SimConnect, simvars: List[Dict], def_id=None, req_id=None):
        self.def_id = def_id or next(sc._defid_iter)
        self.req_id = req_id or next(sc._reqid_iter)
        self.defs = {}
        self.metrics = ChangeDict()
        for i, d in enumerate(simvars):
            name = d['name']
            unit = d.get('unit', None)      #TODO or lookup
            dtyp = d.get('type', DATATYPE_FLOAT64)
            epsilon = d.get('epsilon', 1e-6)
            self.defs[i] = dict(name=name, unit=unit, dtyp=dtyp)
            sc.AddToDataDefinition(self.def_id, name, unit, dtyp, epsilon, i)

    def get_units(self) -> Dict[str, str]:
        return {d['name']: d['unit'] for d in self.defs.values()}

    def update(self, recv: Optional[RECV]):
        if not isinstance(recv, RECV_SIMOBJECT_DATA) or recv.dwRequestID != self.req_id:
            return self.metrics

        assert recv.dwFlags & DATA_REQUEST_FLAG_TAGGED, 'Expected tagged SIMOBJECT_DATA'

        # dwData is a placeholder for where the data values start
        # so get a void* to that location and cast appropriately
        offset = RECV_SIMOBJECT_DATA.dwData.offset

        items = recv.dwDefineCount
        while items > 0:
            idx = cast(byref(recv, offset), POINTER(DWORD))[0].value
            offset += sizeof(DWORD)
            d = self.defs[idx]
            ctyp = _dtyps[d['dtyp']]
            val = cast(byref(recv, offset), POINTER(ctyp))[0]
            offset += sizeof(ctyp)
            self.metrics[d['name']] = val
            items -= 1

        return self.metrics


def all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)])


# SDK calls trigger responses which are subclasses of RECV
# indicated by a corresponding RECV_ID_* constant
# for example a response with recv.dwID = RECV_ID_OPEN
# indicates the full response is a RECV_OPEN structure
_recv_map: Dict[str, type] = {
    getattr(scdefs, kls.__name__.replace('RECV_', 'RECV_ID_'), None):
    kls
    for kls in all_subclasses(RECV)
}

_dtyps = {
    DATATYPE_INT32: DWORD,   # 32-bit integer number
    DATATYPE_INT64: c_longlong,   # 64-bit integer number
    DATATYPE_FLOAT32: c_float,   # 32-bit floating-point number (float)
    DATATYPE_FLOAT64: c_double,   # 64-bit floating-point number (double)
}
