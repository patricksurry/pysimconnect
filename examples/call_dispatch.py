from simconnect import SimConnect, DispatchProc, ReceiverInstance
from time import sleep


"""
Illlustrate low-level use of DispatchProc via CallDispatch
In this case the call to CallDispatch will always succeed,
but will only trigger the dispatcher when a message is ready.

Compare GetNextDispatch which will raises an error when no message is waiting,
but can still be used for polling until it succeeds
"""


def dispatcher(pRecv, nSize, pContext):
    """eventually called once when the result of the implicit Open() call is ready"""
    recv = ReceiverInstance.cast_recv(pRecv)
    print(f"dispatcher: received {recv.__class__.__name__} with size {nSize} and context {pContext}")


# disable the default receivers so we can see the RECV_OPEN response
with SimConnect(name='CallDispatch', default_receivers=[]) as sc:
    for _ in range(10):
        print('CallDispatch')
        sc.CallDispatch(DispatchProc(dispatcher), None)
        sleep(0.1)
