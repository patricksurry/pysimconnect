from SimConnect import SimConnect, RECV_P, RECV_EXCEPTION, RECV_SIMOBJECT_DATA
from ctypes import byref
from ctypes.wintypes import DWORD
from time import sleep


with SimConnect(name='MonitorMetrics') as sc:
    simvars = [
        ("Kohlsman setting hg", "inHg"),
        ("Indicated Altitude", "feet"),
        ("Plane Latitude", "degrees"),
        ("Plane Longitude", "degrees"),
    ]
    ds = sc.subscribeSimObjects(simvars)
    print(ds.get_units())

    pRecv = RECV_P()
    nSize = DWORD()
    latest = 0
    while True:
        try:
            print('Trying...')
            sc.GetNextDispatch(byref(pRecv), byref(nSize))
        except OSError:
            sleep(0.5)
            continue
        recv = sc._get_recv(pRecv)
        print(f"got {recv.__class__.__name__}")
        if isinstance(recv, RECV_EXCEPTION):
            print(f"Got exception {recv.dwException}, sendID {recv.dwSendID}, index {recv.dwIndex}")
        elif isinstance(recv, RECV_SIMOBJECT_DATA):
            metrics = ds.update(recv)
            print(f"Updated {len(metrics.changedsince(latest))} simvars")
            latest = metrics.latest()
            print(metrics)
