from SimConnect import SimConnect, DispatchProc
from time import sleep


def dispatcher(pRecv, nSize, pContext):
    recv = sc._get_recv(pRecv)
    print(f"dispatcher: received {recv.__class__.__name__} with size {nSize} and context {pContext}")


with SimConnect(name='CallDispatch') as sc:
    for _ in range(5):
        print('CallDispatch')
        sc.CallDispatch(DispatchProc(dispatcher), None)
        sleep(0.1)
