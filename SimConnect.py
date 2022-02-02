from typing import Dict
from ctypes import cast, byref, windll, POINTER, pointer
from ctypes.wintypes import HANDLE, LPCSTR, DWORD
from scdefs import *
import scdefs
from time import sleep


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
