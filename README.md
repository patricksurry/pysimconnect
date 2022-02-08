`pysimconnect` is a lightweight, high-performance wrapper for FlightSimulator 2020's
[SimConnect SDK](https://docs.flightsimulator.com/html/index.htm?#t=Programming_Tools%2FSimConnect%2FSimConnect_SDK.htm),
inspired by [Python-SimConnect](https://github.com/odwdinc/Python-SimConnect).

If you're looking to build external instrument displays or
connect custom controllers to FS2020, `pysimconnect` is for you.
You might also be interested in [G3](https://github.com/patricksurry/g3),
a flexible Javascript framework for building steam gauge instrument panels.

It provides a simple pythonic interface
to read simulator variables,
set editable variables,
subscribe to variable changes,
and trigger simulator events.
It also exposes all of the low-level SDK methods,
constants and enumerations based on an automatic
translation of the SDK API defined by `SimConnect.h`.


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

    for i in range(10):
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
        print(f"Updated data {datadef.simdata.changedsince(latest)}")

        latest = datadef.simdata.latest()

        # fetch the current altitude
        altitude = datadef.simdata['Indicated Altitude']

    # explicity close the SDK connection
    sc.Close()

This should show output like:

    TODO

Also take a look at the
[other examples](https://github.com/patricksurry/pysimconnect/tree/master/examples),
which illustrate both low-level SDK interaction and the simplify python bindings.

To get more detailed information about what's happening, set the `LOGLEVEL` environment variable
before running your code:

    set LOGLEVEL=DEBUG

What's what?
---

Find the full source on github at https://github.com/patricksurry/pysimconnect.
The `simconnect` folder contains the package itself.

The main interface is defined in `SimConnect.py` which wraps the raw
definitions from the auto-generated `scdefs.py`,
providing access to both the low-level
SDK functions as well as some pythonic sugar.
`pysimconnect` requires a copy of `SimConnect.dll`,
which ships with FS2020, but a recent copy is also included here.
You can point to your own version by specifying the `dll_path` argument
when initializing `SimConnect(...)`.
The `scvars.json` file lists all the simulation variables (SimVars),
events and dimensional units, which were scraped from the SDK documentation pages
using `scripts/scrapevars.json`.  This is useful for finding content
you want to interact with, inferring missing units and data-types
when querying simulation variables, and sanity-checking variable names.

The `examples` folder contains various illustrations of how to use
the package, with both low-level SDK access and the pythonic wrappers.
See the `README.md` there for more details.

The `scripts` folder includes several scripts used to generate
parts of the package.
The `genscdefs.py` script creates `scdefs.py` from a post-processed
version of the `SimConnect.h` C++ header that ships with the SDK
(which can be installed via the Options > General > Developer tools help menu).
This generates a python translation of all the SDK function declarations, data structures
and enumerated constants.  The translation is quite fragile:
it assumes the header is formatted in a particular way, and has been
pre-processed with `cpp` to `SimConnect_cpp.h` from the raw header.
This approach makes it easy to tweak the rules for mapping from C++
to Python, as long as header format doesn't change significantly.
The `scrapevars.py` script is a quick hack to scrape the tables of
simulation variables, events and units from the API documentation.
This results in `scvars.json` which is


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
