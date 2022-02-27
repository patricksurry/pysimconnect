Introductory examples of how to use the `simconnect` package.

- `demo.py`: illustrates all major features

- `test_units.py`: illustrate SDK unit conversion options

- `send_event.py`: simple send_event example

- `set_data.py`: simple set_datum example

- `subscribe.py`: pythonic wrapper for watching one or more variables over time
    (cf. `monitor_metrics.py` for a low-level implementation)

Examples calling SDK functions directly:

- `show_version.py`: trivial low-level example showing how to retrieve the result of the SDK `Open()` call.

- `call_dispatch.py`: example of how to poll for results with a callback function,
which is only called when a message is available

- `monitor_metrics.py`: example of several low-level SDK calls to retrieve a group of simulation variables




