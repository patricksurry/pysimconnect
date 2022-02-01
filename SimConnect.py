from ctypes import byref, windll
from ctypes.wintypes import HANDLE, LPCSTR
from scdefs import *
import scdefs


class SimConnect:
    def __init__(self, dll_path='SimConnect.dll'):
        dll = windll.LoadLibrary('SimConnect.dll')
        self._decls = scdefs._decls(dll)
        self.sc = HANDLE()

    def _dispatch(self, f):
        def _callable(*args):
            result = f(byref(self.sc), *args)
            return result.value
        return _callable

    def __getattr__(self, k):
        if k in self._decls:
            return self._dispatch(self._decls[k])
        # Default behaviour
        raise AttributeError


sc = SimConnect()
client_name = 'MetricMonitor'
print(sc.Open(LPCSTR(client_name.encode('utf-8')), None, 0, 0, 0))
