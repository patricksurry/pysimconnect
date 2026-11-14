import pytest
from simconnect import SimConnect, PERIOD_VISUAL_FRAME


@pytest.fixture(scope="module")
def live_sc():
    try:
        sc = SimConnect(name="pytest_live")
    except Exception as exc:
        pytest.skip(f"Live MSFS 2020 SimConnect not available: {exc}")
    yield sc
    sc.Close()


def test_live_get_simdata_various_types(live_sc):
    data = live_sc.get_simdata([
        "TITLE",
        "ATC ID",
        "Indicated Altitude",
        "GENERAL ENG THROTTLE LEVER POSITION:1",
        "YOKE X POSITION",
        "SIM ON GROUND",
        "TRANSPONDER CODE:1",
        dict(name="ENG FUEL FLOW PPH:1", units="pounds per hour"),
    ])
    assert isinstance(data["TITLE"], str) and len(data["TITLE"]) > 0
    assert isinstance(data["ATC ID"], str)
    assert isinstance(data["Indicated Altitude"], float)
    assert isinstance(data["GENERAL ENG THROTTLE LEVER POSITION:1"], float)
    assert isinstance(data["YOKE X POSITION"], float)
    assert data["SIM ON GROUND"] in (0, 1, -1)
    assert isinstance(data["TRANSPONDER CODE:1"], int)
    assert isinstance(data["ENG FUEL FLOW PPH:1"], float)


def test_live_subscribe_and_callback(live_sc):
    received = []
    dd = live_sc.subscribe_simdata(
        ["Indicated Altitude", "Plane Latitude", "Plane Longitude"],
        period=PERIOD_VISUAL_FRAME,
        interval=1,
        callback=lambda sd: received.append(dict(sd)),
    )
    for _ in range(10):
        if live_sc.receive(timeout_seconds=0.2) and received:
            break
    assert len(received) >= 1
    assert "Indicated Altitude" in dd.simdata
    assert dd.simdata.latest() > 0


def test_live_reconnect_separate_instance(live_sc):
    with SimConnect(name="pytest_reconnect") as sc2:
        alt = sc2.get_simdatum("Indicated Altitude")
        assert isinstance(alt, float)
