from SimConnect import (
    SimConnect, GROUP_PRIORITY_STANDARD, OBJECT_ID_USER,
    PERIOD_SECOND, DATA_REQUEST_FLAG_CHANGED, DATA_REQUEST_FLAG_TAGGED,
    DATATYPE_FLOAT64, RECV_SIMOBJECT_DATA, RECV_P
)
from ctypes import byref, cast, POINTER, pointer, c_float
from ctypes.wintypes import DWORD
from time import sleep


with SimConnect(name='MonitorMetrics') as sc:
    request_id = DWORD(0x1234)
    simvars = [
        ("Kohlsman setting hg", "inHg"),
        ("Indicated Altitude", "feet"),
        ("Plane Latitude", "degrees"),
        ("Plane Longitude", "degrees"),
    ]
    for i, (simvar, unit) in enumerate(simvars):
        sc.SimConnect_AddToDataDefinition(request_id, simvar, unit, DATATYPE_FLOAT64, 0, i)

    sc.RequestDataOnSimObject(
        request_id,
        GROUP_PRIORITY_STANDARD,
        OBJECT_ID_USER,
        PERIOD_SECOND,
        DATA_REQUEST_FLAG_CHANGED.value | DATA_REQUEST_FLAG_TAGGED.value,  #TODO fixme
        0,  # number of periods before starting events
        1,  # number of periods between events, e.g. with PERIOD_SIM_FRAME
        0,  # number of repeats, 0 is forever
    )
    while True:
        sleep(0.1)
        pRecv = RECV_P()
        nSize = DWORD()
        sc.GetNextDispatch(byref(pRecv), byref(nSize))
        recv = sc._get_recv(pRecv)
        if isinstance(recv, RECV_SIMOBJECT_DATA) and recv.dwRequestID.value == request_id.value:
            print("Received metrics:")
            data = cast(pointer(recv.dwData), POINTER(c_float))
            for i, (metric, unit) in enumerate(simvars):
                print(f"{metric}: {data[i].value}")
