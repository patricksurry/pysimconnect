from simconnect import SimConnect


with SimConnect(name='SendEvent') as sc:
    # click up the altimeter setting a few times
    event = 'KOHLSMAN_INC'
    for _ in range(10):
        print(f"Sending {event} event")
        # some events require an optional `data` field here, see SDK doc
        sc.send_event(event)

    for _ in range(10):
        # pump the event queue a few times to see what comes back...
        result = sc.receive(timeout_seconds=0.2)
        print(f"Received? {result}")
