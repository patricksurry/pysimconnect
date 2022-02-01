This is a wrapper for FlightSimulator 2020's
[SimConnect SDK](https://docs.flightsimulator.com/html/index.htm?#t=Programming_Tools%2FSimConnect%2FSimConnect_SDK.htm),
inspired by [Python-SimConnect](https://github.com/odwdinc/Python-SimConnect).

It aims to provide more comprehensive stubs to access the raw SDK methods,
as well as some pythonic wrappers to simplify some use cases,
in particular watching a fixed set of metrics and generating SDK
events to sync external controls with FS2020.


The files `SimConnect.dll` is a recent copy of the DLL provided with FS2020,
and `SimConnect.h` is a copy of the C header file that ships with the SDK
(which can be installed via the Options > General > Developer tools help menu).

The `genscdefs.py` script creates `scdefs.py` which contains
a python translation of all the SDK function declarations, data structures
and enumerated constants.  This translation is quite fragile,
assuming the header is formatted in a specific way, and is
based on first generating `SimConnect_cpp.h` from the raw header
using the C pre-processor along with an empty `float.h` include.
This approach makes it easy to tweak the rules for mapping from C++
to Python, as long as header format doesn't change significantly.

The main interface is defined in `SimConnect.py` which wraps the raw
definitions from `scdefs.py`, providing access to both the low-level
SDK functions as well as some pythonic sugar.
