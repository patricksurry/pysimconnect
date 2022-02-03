This is a wrapper for FlightSimulator 2020's
[SimConnect SDK](https://docs.flightsimulator.com/html/index.htm?#t=Programming_Tools%2FSimConnect%2FSimConnect_SDK.htm),
inspired by [Python-SimConnect](https://github.com/odwdinc/Python-SimConnect).

It aims to provide more comprehensive stubs to access the raw SDK methods,
as well as some pythonic wrappers to simplify some use cases,
in particular watching a fixed set of metrics and generating SDK
events to sync external controls with FS2020.

Quick start
---

Making sure you're using python 3.6+, install the package:

    pip install pysimconnect

Start Microsoft flight simulator 2020, and begin a flight, perhaps with the AI pilot flying.

Download the `subscribe.py`
[example from github](https://github.com/patricksurry/pysimconnect/tree/master/examples).

Run it to start monitoring a few metrics from your flight:

    python subscribe.py

You should see output like:

    TODO
    ...

Check out g3 and g3py ...


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
