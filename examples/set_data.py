from simconnect import SimConnect
from time import sleep


"""Simple example of setting a simvar"""
with SimConnect(name='GainAltitude') as sc:
    altitude = sc.get_simdatum('Indicated Altitude')
    for _ in range(10):
        altitude += 100
        sc.set_simdatum('Indicated Altitude', altitude)
