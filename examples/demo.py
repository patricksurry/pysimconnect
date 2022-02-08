from time import sleep
from simconnect import SimConnect, PERIOD_VISUAL_FRAME

# open a connection to the SDK
# or use as a context via `with SimConnect() as sc: ... `
sc = SimConnect()

# one-off blocking fetch of a single simulator variable,
# which will wait up to 1s (default) to receive the value
altitude = sc.get_simdatum("Indicated Altitude")

# subscribing to one or more variables is much more efficient,
# with the SDK sending updated values up to once per simulator frame.
# the variables are tracked in `datadef.simdata`
# which is a dictionary that tracks the last modified time
# of each variable.  changes can also trigger an optional callback function
datadef = sc.subscribe_simdata(
    [
        "Indicated Altitude",
        dict(name="Kohlsman setting hg", units="hectopascal"),
        "ELECTRICAL BATTERY BUS VOLTAGE"
    ],
    # request an update every ten rendered frames
    period=PERIOD_VISUAL_FRAME,
    interval=10,
)
print("Inferred variable units", datadef.get_units())

# track the most recent data update
latest = datadef.simdata.latest()

while True:
    # bump altitude, which is a settable simulator variable
    sc.set_simdatum("Indicated Altitude", altitude + 100)

    # trigger an event that increments the barometer setting
    # some events also take an optional data value
    sc.send_event("KOHLSMAN_INC")

    # wait a bit...
    sleep(0.5)

    # pump the SDK event queue to deal with any recent messages
    while sc.receive():
        pass

    # show data that's been changed since the last update
    print("Updated data {simdata.changedsince(latest)")

    latest = datadef.simdata.latest()

    # fetch the current altitude
    altitude = simdata['Indicated Altitude']

# explicity close the SDK connection
sc.Close()
