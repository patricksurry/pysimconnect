import time
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from simconnect import PERIOD_VISUAL_FRAME, MockSimConnect
from simconnect.cli import app, scoped_autocomplete

runner = CliRunner()


def test_readme_cli_search():
    """Mirror README 'simconnect search altitude' example (opens web SimVar Explorer)."""
    with patch("simconnect.cli.webbrowser.open") as mock_open:
        res = runner.invoke(app, ["search", "altitude"])
        assert res.exit_code == 0
        assert "https://patricksurry.github.io/pysimconnect/#search=altitude" in res.stdout
        mock_open.assert_called_once_with("https://patricksurry.github.io/pysimconnect/#search=altitude")


def test_readme_cli_tab_completion():
    """Mirror README 'simconnect get PLA<TAB>' auto-completion."""
    complete_vars = scoped_autocomplete("VARIABLES")
    matches = complete_vars("PLA")
    assert "PLANE_ALTITUDE" in matches


def test_readme_cli_get_set_send():
    """Mirror README 'simconnect get PLANE_ALTITUDE', 'set --units meters', and 'send KOHLSMAN_INC'."""
    shared_sc = MockSimConnect()
    with patch("simconnect.cli.SimConnect", return_value=shared_sc):
        res_get = runner.invoke(app, ["get", "PLANE_ALTITUDE"])
        assert res_get.exit_code == 0
        assert "PLANE ALTITUDE =" in res_get.stdout

        res_set = runner.invoke(app, ["set", "PLANE_ALTITUDE", "1500", "--units", "meters"])
        assert res_set.exit_code == 0
        assert "Setting PLANE ALTITUDE = 1500.0 (meters)" in res_set.stdout
        assert shared_sc.get_simdatum("PLANE ALTITUDE") == pytest.approx(1500.0 / 0.3048)

        res_send = runner.invoke(app, ["send", "KOHLSMAN_INC"])
        assert res_send.exit_code == 0
        assert "Sending KOHLSMAN_INC" in res_send.stdout
        assert ("KOHLSMAN_INC", 0) in shared_sc.event_history


def test_readme_python_demo_e2e():
    """Mirror README / examples/demo.py end-to-end flow using MockSimConnect."""
    with MockSimConnect() as sc:
        altitude = sc.get_simdatum("Indicated Altitude")
        assert isinstance(altitude, float)

        datadef = sc.subscribe_simdata(
            [
                "Indicated Altitude",
                dict(name="Kohlsman setting hg:1", units="hectopascal"),
                "ELECTRICAL BATTERY BUS VOLTAGE",
            ],
            period=PERIOD_VISUAL_FRAME,
            interval=10,
        )
        assert datadef.get_units() == {
            "Indicated Altitude": "feet",
            "Kohlsman setting hg:1": "hectopascal",
            "ELECTRICAL BATTERY BUS VOLTAGE": "volts",
        }

        latest = datadef.simdata.latest()
        time.sleep(0.025)
        sc.set_simdatum("PLANE ALTITUDE", 1500.0, units="meters")
        sc.send_event("KOHLSMAN_INC")
        while sc.receive():
            pass
        updated = datadef.simdata.changedsince(latest)
        assert updated["Indicated Altitude"] == pytest.approx(1500.0 / 0.3048)
        assert updated["Kohlsman setting hg:1"] > 1013.25
        assert datadef.simdata["ELECTRICAL BATTERY BUS VOLTAGE"] == pytest.approx(24.5)
        sc.Close()
