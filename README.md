

This is a wrapper for FlightSimulator 2020's
[SimConnect SDK](https://docs.flightsimulator.com/html/index.htm?#t=Programming_Tools%2FSimConnect%2FSimConnect_SDK.htm),
inspired by [Python-SimConnect](https://github.com/odwdinc/Python-SimConnect).

It provides simple Pythonic methods to get simulator variables,
subscribe to watch changes to one or more variables,
set editable variables, and trigger simulator events.
It also includes a complete mapping to the low-level SDK methods
and all of the constants defined in `SimConnect.h`

Quick start
---

Making sure you're using python 3.6+ and install the package:

    pip install pysimconnect

Start Microsoft flight simulator 2020, and begin a flight, perhaps with the AI pilot flying.
Start python and try something like this:

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

This should show output like:

    TODO

Also take a look at the
[examples from github](https://github.com/patricksurry/pysimconnect/tree/master/examples),
which illustrate both low-level examples interacting directly with the SDK functions,
and simplified python bindings.

Check out g3 and g3py ...

    TODO


What's what?
---

The `simconnect` folder contains the package itself.
The main interface is defined in `SimConnect.py` which wraps the raw
definitions from the auto-generated `scdefs.py`,
providing access to both the low-level
SDK functions as well as some pythonic sugar.
The python interface requires a copy of `SimConnect.dll`
which ships with FS2020.  A recent copy is included here, but
you can point to your own by specifying the `dll_path` argument.
The `scvars.json` file lists all the simulation variables (SimVars),
events and dimensional units, as scraped from the SDK documentation pages

The `examples` folder contains various illustrations of how to use
the package, with both low-level SDK access and the pythonic wrappers.
See the `README.md` there for more details.

The `scripts` folder includes several scripts used to generate
parts of the package.
The `genscdefs.py` script creates `scdefs.py` from a post-processed
version of the `SimConnect.h` C++ header that ships with the SDK
(which can be installed via the Options > General > Developer tools help menu).
This contains a python translation of all the SDK function declarations, data structures
and enumerated constants.  The translation is quite fragile:
it assumes the header is formatted in a particular way, and has been
pre-processed with `cpp` to `SimConnect_cpp.h` from the raw header.
This approach makes it easy to tweak the rules for mapping from C++
to Python, as long as header format doesn't change significantly.

The `scrapevars.py` script is a quick hack to scrape the tables of
simulation variables, events and units from the API documentation.
This results in `scvars.json` which is useful for finding the content
you want to interact with.

Notes
---

Be warned, the SDK documentation appears to have some copy & paste errors
which make understanding the workflow complicated.  The header file comments
make a good secondary source.

Packaging
---

Bump version in `setup.cfg` then following https://packaging.python.org/en/latest/tutorials/packaging-projects/

    python3 -m build

    python3 -m twine upload dist/*  # login with __token__ / pypi...
