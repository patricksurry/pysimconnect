from SimConnect import SimConnect, DispatchProc
from time import sleep


def dispatcher(self, pRecv, nSize, pContext):
    recv = sc._get_recv(pRecv)
    print(f"dispatcher: received {recv.__name__} with size {nSize.value} and context {pContext}")


with SimConnect(name='CallDispatch') as sc:
    for _ in range(5):
        print('CallDispatch')
        sc.CallDispatch(DispatchProc(dispatcher), None)
        sleep(0.1)
