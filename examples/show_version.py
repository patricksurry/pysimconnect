from SimConnect import SimConnect, RECV_P
from ctypes import byref
from ctypes.wintypes import DWORD
from time import sleep


# Use SimConnect object as context manager
# and simply retrieve the response to the implicit SimConnect.Open()
# which is a RECV_OPEN struct containing various version numbers
with SimConnect(name='ShowVersion') as sc:
    sleep(0.1)
    pRecv = RECV_P()
    nSize = DWORD()
    sc.GetNextDispatch(byref(pRecv), byref(nSize))
    ro = sc._get_recv(pRecv)
    appVer = f"v{ro.dwApplicationVersionMajor}.{ro.dwApplicationVersionMinor}"
    appBuild = f"build {ro.dwApplicationBuildMajor}.{ro.dwApplicationBuildMinor}"
    scVer = f"v{ro.dwSimConnectVersionMajor}.{ro.dwSimConnectVersionMinor}"
    scBuild = f"build {ro.dwSimConnectBuildMajor}.{ro.dwSimConnectBuildMinor}"
    print(f"{ro.__name__} App: {ro.szApplicationName} {appVer} {appBuild} SimConnect: {scVer} {scBuild}")
