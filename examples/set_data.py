from simconnect import SimConnect
from time import sleep


"""Simple example of setting a simvar"""
with SimConnect(name='GainAltitude') as sc:
    for _ in range(10):
        altitude = sc.get_simdatum('Indicated Altitude')
        print(f"Got altitude {altitude}, adding 100")
        altitude += 100
        sc.set_simdatum('Indicated Altitude', altitude)
        sleep(0.5)
