Various examples of how to use the `simconnect` package.

- `demo.py`: pythonic README example showing get, set, subscribe and send_event

- `send_event.py`: simple send_event example

- `set_data.py`: simple set_datum example

- `subscribe.py`: pythonic version of the low-level `monitor_metrics.py` example

Low level examples calling raw SDK functions:

- `show_version.py`: trivial low-level example showing how to retrieve the result of the SDK `Open()` call.

- `call_dispatch.py`: example of how to poll for results with a callback function,
which is only called when a message is available

- `monitor_metrics.py`: example of several low-level SDK calls to retrieve a group of simulation variables




