from SimConnect import SimConnect

"""Simple example of subscribing to a set of metrics"""

with SimConnect(name='MonitorMetrics') as sc:
    #TODO infer units from json file
    simvars = [
        ("Kohlsman setting hg", "inHg"),
        ("Indicated Altitude", "feet"),
        ("Plane Latitude", "degrees"),
        ("Plane Longitude", "degrees"),
    ]
    ds = sc.subscribeSimObjects(simvars)
    print(ds.get_units())

    latest = 0
    while True:
        # fetch next RECV object within timeout_seconds, or None
        recv = sc.receiveNext(timeout_seconds=0.5)
        # subscription will validate recv matches subscription
        metrics = ds.update(recv)
        n = len(metrics.changedsince(latest))
        print(f"Updated {n} simvars")
        if n:
            print(metrics)
        latest = metrics.latest()
