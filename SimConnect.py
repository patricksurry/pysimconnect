from typing import Dict, List, Union, Any
from ctypes import cast, byref, windll, POINTER, c_float, c_double, c_longlong, Structure
from ctypes.wintypes import HANDLE, DWORD
import scdefs
from scdefs import *   # just for ease of downstream import


RECV_P = POINTER(scdefs.RECV)


class SimConnect:
    def __init__(self, name='pySimConnect', dll_path='SimConnect.dll'):
        dll = windll.LoadLibrary(dll_path)
        self._decls = scdefs._decls(dll)
        self.hsc = HANDLE()
        # All methods other than open pass the sc HANDLE as the first arg
        self._decls['Open'](byref(self.hsc), name.encode('utf-8'), None, 0, 0, 0)

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

    def _get_recv(self, pRecv) -> scdefs.RECV:   #TODO type annotation : pointer[scdefs.RECV] per https://github.com/python/mypy/issues/7540
        recv_id = pRecv.contents.dwID
        if recv_id in _recv_map:
            pRecv = cast(pRecv, POINTER(_recv_map[recv_id]))
        return pRecv.contents

    def _get_simdata(
            self,
            recv: scdefs.RECV_SIMOBJECT_DATA,
            tagged=False,
            dtyp=scdefs.DATATYPE_FLOAT64,
            ) -> Union[List[Any], Dict[int, Any]]:

        ctyp = _dtyps[dtyp]
        # dwData is a placeholder for where the data values start
        # so get a void* to that location and cast appropriately
        p = byref(recv, scdefs.RECV_SIMOBJECT_DATA.dwData.offset)
        items = recv.dwDefineCount
        if tagged:
            class Datum(Structure):
                _fields_ = [("idx", DWORD), ("value", ctyp)]
            ds = cast(p, Datum * items)
            return {d.idx: d.value for d in ds}
        else:
            ds = cast(p, ctyp * items)
            return [v for v in ds]

    def __getattr__(self, k):
        if k in self._decls:
            return self._dispatch(self._decls[k])
        # Default behaviour
        raise AttributeError


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
    for kls in all_subclasses(scdefs.RECV)
}

_dtyps = {
    scdefs.DATATYPE_INT32: DWORD,   # 32-bit integer number
    scdefs.DATATYPE_INT64: c_longlong,   # 64-bit integer number
    scdefs.DATATYPE_FLOAT32: c_float,   # 32-bit floating-point number (float)
    scdefs.DATATYPE_FLOAT64: c_double,   # 64-bit floating-point number (double)
}
