from SimConnect import (
    SimConnect, GROUP_PRIORITY_STANDARD, OBJECT_ID_USER,
    PERIOD_SECOND, DATA_REQUEST_FLAG_CHANGED, DATA_REQUEST_FLAG_TAGGED,
    DATATYPE_FLOAT64, RECV_SIMOBJECT_DATA, RECV_EXCEPTION, RECV_P
)
from ctypes import byref, cast, POINTER, pointer, c_float
from ctypes.wintypes import DWORD
from time import sleep


with SimConnect(name='MonitorMetrics') as sc:
    request_id = 0x1234
    simvars = [
        ("Kohlsman setting hg", "inHg"),
        ("Indicated Altitude", "feet"),
        ("Plane Latitude", "degrees"),
        ("Plane Longitude", "degrees"),
    ]
    for i, (simvar, unit) in enumerate(simvars):
        sc.AddToDataDefinition(request_id, simvar.encode('utf-8'), unit.encode('utf-8'), DATATYPE_FLOAT64, 0, i)

    sc.RequestDataOnSimObject(
        request_id,
        GROUP_PRIORITY_STANDARD,
        OBJECT_ID_USER,
        PERIOD_SECOND,
        DATA_REQUEST_FLAG_CHANGED | DATA_REQUEST_FLAG_TAGGED,
        0,  # number of periods before starting events
        1,  # number of periods between events, e.g. with PERIOD_SIM_FRAME
        0,  # number of repeats, 0 is forever
    )
    pRecv = RECV_P()
    nSize = DWORD()
    while True:
        try:
            print('Trying')
            sc.GetNextDispatch(byref(pRecv), byref(nSize))
        except OSError:
            sleep(0.5)
            continue
        recv = sc._get_recv(pRecv)
        print(f"got {recv.__class__.__name__}")
        if isinstance(recv, RECV_EXCEPTION):
            print(f"Got exception {recv.dwException}, sendID {recv.dwSendID}, index {recv.dwIndex}")
        elif isinstance(recv, RECV_SIMOBJECT_DATA):
            print("Received SIMOBJECT_DATA")
            if recv.dwRequestID == request_id:
                print(f"Matched 0x{request_id:X}")
                data = cast(pointer(recv.dwData), POINTER(c_float))
                for i, (metric, unit) in enumerate(simvars):
                    print(f"{metric}: {data[i].value}")
