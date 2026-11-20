import time
from unittest.mock import patch

import pytest

from simconnect import PERIOD_VISUAL_FRAME, MockSimConnect, SimConnect


@pytest.fixture(scope="module")
def live_sc():
    """Connect to live MSFS 2020 when running, or fall back to MockSimConnect."""
    try:
        sc = SimConnect(name="pytest_live")
        yield sc
        sc.Close()
    except Exception:
        sc = MockSimConnect(name="pytest_mock")
        with (
            patch("tests.test_live_msfs.SimConnect", MockSimConnect),
            patch("simconnect.cli.SimConnect", MockSimConnect),
        ):
            yield sc
        sc.Close()


def test_live_get_simdata_various_types(live_sc):
    data = live_sc.get_simdata(
        [
            "TITLE",
            "ATC ID",
            "Indicated Altitude",
            "GENERAL ENG THROTTLE LEVER POSITION:1",
            "YOKE X POSITION",
            "SIM ON GROUND",
            "TRANSPONDER CODE:1",
            "ZULU TIME",
            "ABSOLUTE TIME",
            dict(name="ENG FUEL FLOW PPH:1", units="pounds per hour"),
        ]
    )
    assert isinstance(data["TITLE"], str) and len(data["TITLE"]) > 0
    assert isinstance(data["ATC ID"], str)
    assert isinstance(data["Indicated Altitude"], float)
    assert isinstance(data["GENERAL ENG THROTTLE LEVER POSITION:1"], float)
    assert isinstance(data["YOKE X POSITION"], float)
    assert data["SIM ON GROUND"] in (0, 1, -1)
    assert isinstance(data["TRANSPONDER CODE:1"], int)
    assert isinstance(data["ZULU TIME"], float) and data["ZULU TIME"] >= 0
    assert isinstance(data["ABSOLUTE TIME"], float) and data["ABSOLUTE TIME"] > 0
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
        time.sleep(0.025)
        if live_sc.receive(timeout_seconds=0.2) and received:
            break
    assert len(received) >= 1
    assert "Indicated Altitude" in dd.simdata
    assert dd.simdata.latest() > 0


def test_live_reconnect_separate_instance(live_sc):
    with type(live_sc)(name="pytest_reconnect") as sc2:
        alt = sc2.get_simdatum("Indicated Altitude")
        assert isinstance(alt, float)


def test_live_readme_cli_e2e(live_sc):
    """Run the actual README CLI commands (search, get, set, send) against live MSFS 2020."""
    from unittest.mock import patch

    from typer.testing import CliRunner

    from simconnect.cli import app

    runner = CliRunner()

    with patch("simconnect.cli.webbrowser.open") as mock_open:
        res_search = runner.invoke(app, ["search", "altitude"])
        assert res_search.exit_code == 0
        assert "https://patricksurry.github.io/pysimconnect/#search=altitude" in res_search.stdout
        mock_open.assert_called_once()

    res_get = runner.invoke(app, ["get", "PLANE_ALTITUDE"])
    assert res_get.exit_code == 0
    assert "PLANE ALTITUDE =" in res_get.stdout

    # Read current altitude in meters, set it back to the same value in meters so flight isn't disrupted
    cur_alt_m = live_sc.get_simdatum("PLANE ALTITUDE", units="meters")
    res_set = runner.invoke(app, ["set", "PLANE_ALTITUDE", str(round(cur_alt_m, 2)), "--units", "meters"])
    assert res_set.exit_code == 0
    assert "Setting PLANE ALTITUDE =" in res_set.stdout

    res_send = runner.invoke(app, ["send", "KOHLSMAN_INC"])
    assert res_send.exit_code == 0
    assert "Sending KOHLSMAN_INC" in res_send.stdout


def test_live_g3_bridge(live_sc):
    """Verify SimConnectG3Bridge polls live MSFS 2020 metrics and units."""
    from time import sleep

    from simconnect.g3 import SimConnectG3Bridge

    bridge = SimConnectG3Bridge(sc=live_sc)
    for _ in range(15):
        bridge.poll_metrics()
        if "altitude" in bridge.state and "heading" in bridge.state:
            break
        sleep(0.05)
    assert "altitude" in bridge.state
    assert "heading" in bridge.state
    units = bridge.metric_units()
    assert units["altitude"] == "ft"
    assert units["airspeed"] == "knot"
