from simconnect import SimConnect, RECV_P, ReceiverInstance
from ctypes import byref
from ctypes.wintypes import DWORD
from time import sleep


"""
Use a SimConnect object as a context manager,
removing the default receiver handlers so we can
manually retrieve the response to the implicit SimConnect.Open()
which is a RECV_OPEN struct containing various version numbers.
Compare receiver.receiveOpen which normally logs this data automatically
"""
with SimConnect(name='ShowVersion', default_receivers=[]) as sc:
    sleep(0.5)  # make sure the response is waiting for us
    pRecv = RECV_P()
    nSize = DWORD()
    sc.GetNextDispatch(byref(pRecv), byref(nSize))
    ro = ReceiverInstance.cast_recv(pRecv)
    appVer = f"v{ro.dwApplicationVersionMajor}.{ro.dwApplicationVersionMinor}"
    appBuild = f"build {ro.dwApplicationBuildMajor}.{ro.dwApplicationBuildMinor}"
    scVer = f"v{ro.dwSimConnectVersionMajor}.{ro.dwSimConnectVersionMinor}"
    scBuild = f"build {ro.dwSimConnectBuildMajor}.{ro.dwSimConnectBuildMinor}"
    print(f"{ro.__class__.__name__} App: {ro.szApplicationName} {appVer} {appBuild} SimConnect: {scVer} {scBuild}")
