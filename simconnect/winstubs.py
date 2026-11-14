# hack to avoid simconnect import error on non-windows platform
# allows us to run some supporting tools, but not simconnect SDK connection
from ctypes import c_char, c_uint16, c_int32, c_uint32, c_void_p, c_char_p, CFUNCTYPE as WINFUNCTYPE


HRESULT = c_int32
BYTE = c_char
WORD = c_uint16
DWORD = c_uint32
HANDLE = c_void_p
LPCSTR = c_char_p
HWND = c_void_p


class windll:
    @staticmethod
    def LoadLibrary(*args, **kwargs):
        raise OSError("SimConnect.dll can only be loaded on Windows")

