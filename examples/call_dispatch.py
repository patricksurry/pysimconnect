from simconnect import SimConnect, DispatchProc
from time import sleep


"""
Illlustrate use of DispatchProce via CallDispatch
In this case the call to CallDispatch will always succeed,
but will only trigger the dispatcher when a message is ready.

Compare GetNextDispatch which will raises an error when no message is waiting,
but can still be used for polling until it succeeds
"""


def dispatcher(pRecv, nSize, pContext):
    """eventually called once when the result of the implicit Open() call is ready"""
    recv = sc._cast_recv(pRecv)
    print(f"dispatcher: received {recv.__class__.__name__} with size {nSize} and context {pContext}")


with SimConnect(name='CallDispatch') as sc:
    for _ in range(10):
        print('CallDispatch')
        sc.CallDispatch(DispatchProc(dispatcher), None)
        sleep(0.1)
