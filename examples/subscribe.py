from simconnect import SimConnect

"""Simple example of subscribing to a set of metrics"""

with SimConnect(name='MonitorMetrics') as sc:
    simvars = [
        # Simulation variable names are not case-sensitive
        "Kohlsman setting hg",
        # Provide a dictionary to specify optional attributes:
        # 'units' (per SDK), 'epsilon' (default 1e-4) and 'type' (default DATATYPE_FLOAT64)
        dict(name="Indicated Altitude", units="m", epsilon=0.1),
        dict(name="Plane Latitude", units='degrees'),
        dict(name="Plane Longitude", units='degrees'),
    ]
    ds = sc.subscribeSimObjects(simvars)
    print(ds.get_units())

    latest = 0
    while True:
        # fetch next RECV object within timeout_seconds, or None
        recv = sc.receiveNext(timeout_seconds=1)
        # subscription will validate recv matches subscription
        metrics = ds.update(recv)
        n = len(metrics.changedsince(latest))
        print(f"Updated {n} simvars")
        if n:
            print(metrics)
        latest = metrics.latest()
