from simconnect import (
    SimConnect, ReceiverInstance, OBJECT_ID_USER,
    PERIOD_SECOND, DATA_REQUEST_FLAG_CHANGED, DATA_REQUEST_FLAG_TAGGED,
    DATATYPE_FLOAT64, RECV_SIMOBJECT_DATA, RECV_EXCEPTION, RECV_P
)
from ctypes import byref, sizeof, cast, POINTER, c_double
from ctypes.wintypes import DWORD
from time import sleep


"""
Low level example showing the flow for watching a group of simulation variables.
Compare subscribe.py for a more pythonic version
"""
with SimConnect(name='MonitorMetrics') as sc:
    def_id = 0x1234
    simvars = [
        ("Kohlsman setting hg", "inHg"),
        ("Indicated Altitude", "feet"),
        ("Plane Latitude", "degrees"),
        ("Plane Longitude", "degrees"),
    ]
    for i, (simvar, unit) in enumerate(simvars):
        sc.AddToDataDefinition(def_id, simvar, unit, DATATYPE_FLOAT64, 0, i)

    req_id = 0xfeed
    sc.RequestDataOnSimObject(
        req_id,  # request identifier for response packets
        def_id,  # the data definition group
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
        recv = ReceiverInstance.cast_recv(pRecv)
        print(f"got {recv.__class__.__name__}")
        if isinstance(recv, RECV_EXCEPTION):
            print(f"Got exception {recv.dwException}, sendID {recv.dwSendID}, index {recv.dwIndex}")
        elif isinstance(recv, RECV_SIMOBJECT_DATA):
            print(f"Received SIMOBJECT_DATA with {recv.dwDefineCount} data elements, flags {recv.dwFlags}")
            if recv.dwRequestID == req_id:
                print(f"Matched request 0x{req_id:X}")
                data = {}
                # see datadef.py add_receiver() for the general case
                # dwData is a placeholder for start of actual data
                offset = RECV_SIMOBJECT_DATA.dwData.offset
                for _ in range(recv.dwDefineCount):
                    idx = cast(byref(recv, offset), POINTER(DWORD))[0]
                    offset += sizeof(DWORD)
                    # DATATYPE_FLOAT64 => c_double
                    val = cast(byref(recv, offset), POINTER(c_double))[0]
                    offset += sizeof(c_double)
                    name = simvars[idx][0]
                    data[name] = val
                print(f"Received simvars {data}")
