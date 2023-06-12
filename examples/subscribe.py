from simconnect import SimConnect

"""Simple example of subscribing to a set of metrics"""

with SimConnect(name='MonitorMetrics') as sc:
    simvars = [
        # We can monitor simvars with string values
        "ATC ID",
        # boolean, flag, and mask vars are retured as int, most others as float
        "ATC cleared landing",
        # Simulation variable names are not case-sensitive
        "Kohlsman setting hg:1",
        # Provide a dictionary to specify optional attributes:
        # 'units' (per SDK), 'epsilon' (default 1e-4) and 'type' (default DATATYPE_FLOAT64)
        dict(name="Indicated Altitude", units="m", epsilon=0.1),
        dict(name="Plane Latitude", units='degrees'),
        dict(name="Plane Longitude", units='degrees'),
    ]

    print(f"One-off snaphsot of {sc.get_simdata(simvars[0])}")

    # but subscribe is more efficient if we're repeating...
    dd = sc.subscribe_simdata(simvars)
    print(f"Subscribed to simvars with units {dd.get_units()}")

    latest = 0
    while True:
        while sc.receive(timeout_seconds=0.1):
            # clear queue of pending results, processed by receiver handlers
            print('received result')
            pass
        n = len(dd.simdata.changedsince(latest))
        if n:
            print(f"Updated {n} simvars")
            print(dd.simdata)
            latest = dd.simdata.latest()
