import logging
import pytest
from simconnect.scdefs import DATATYPE_INT32, DATATYPE_FLOAT64, DATATYPE_STRING256
from simconnect.scvars import (
    UNITS,
    type_for_unit,
    validate_simvar,
    validate_event,
    validate_units,
)


@pytest.mark.parametrize("unit", [
    "percent",
    "PERCENT",
    "percentage",
    "percent over 100",
    "number",
    "position",
    "ratio",
    "scaler",
    "decibel",
])
def test_type_for_unit_misc_float64(unit, caplog):
    with caplog.at_level(logging.WARNING):
        assert type_for_unit(unit) == DATATYPE_FLOAT64
    assert caplog.records == []


@pytest.mark.parametrize("unit", [
    "Bool",
    "Boolean",
    "Enum",
    "Bco16",
    "BCO16",
    "mask",
    "flags",
])
def test_type_for_unit_int32(unit, caplog):
    with caplog.at_level(logging.WARNING):
        assert type_for_unit(unit) == DATATYPE_INT32
    assert caplog.records == []


def test_type_for_unit_string(caplog):
    with caplog.at_level(logging.WARNING):
        assert type_for_unit("string") == DATATYPE_STRING256
    assert caplog.records == []


@pytest.mark.parametrize("unit", [
    "pounds per hour",
    "feet per second squared",
    "radians per second",
    "gallons per hour",
    "foot-pounds",
    "Slugs per cubic feet",
])
def test_type_for_unit_canonicalized_names(unit, caplog):
    with caplog.at_level(logging.WARNING):
        assert type_for_unit(unit) == DATATYPE_FLOAT64
    assert caplog.records == []


def test_type_for_unit_all_non_struct_units_no_warnings(caplog):
    with caplog.at_level(logging.WARNING):
        for key, u in UNITS.items():
            if u["dimensions"] == "Structs And Other Complex Units":
                continue
            type_for_unit(key)
            type_for_unit(u["name_std"])
    assert caplog.records == []


def test_type_for_unit_struct_warns(caplog):
    with caplog.at_level(logging.WARNING):
        assert type_for_unit("PID_STRUCT") == DATATYPE_FLOAT64
    assert len(caplog.records) == 1
    assert "complex types not supported" in caplog.records[0].message


def test_type_for_unit_unknown_warns(caplog):
    with caplog.at_level(logging.WARNING):
        assert type_for_unit("not_a_real_unit") == DATATYPE_FLOAT64
    assert len(caplog.records) == 1
    assert "unrecognized unit" in caplog.records[0].message


def test_validate_simvar_known_and_indexed(caplog):
    with caplog.at_level(logging.WARNING):
        sv = validate_simvar("Indicated Altitude", settable=True)
        assert sv["name_std"] == "INDICATED ALTITUDE"
        sv_idx = validate_simvar("GENERAL ENG THROTTLE LEVER POSITION:1", settable=True)
        assert sv_idx["indexed"] is True
    assert caplog.records == []


def test_validate_simvar_missing_index_warns(caplog):
    with caplog.at_level(logging.WARNING):
        validate_simvar("GENERAL ENG THROTTLE LEVER POSITION", settable=False)
    assert any("expected indexed simvar" in r.message for r in caplog.records)


def test_validate_simvar_not_settable_warns(caplog):
    with caplog.at_level(logging.WARNING):
        validate_simvar("AMBIENT WIND VELOCITY", settable=True)
    assert any("is not settable" in r.message for r in caplog.records)


def test_validate_simvar_unknown_no_close_match(caplog):
    """Regression test for Issues #5 and #15: slicing SIMVARS dict when no close match exists."""
    with caplog.at_level(logging.WARNING):
        sv = validate_simvar("C:fs9gps:FlightPlanDepartureAirportIdent", settable=False)
        assert sv == {}
        sv2 = validate_simvar("ABSOLUTE TIME", settable=False)
        assert sv2 == {}
    assert len(caplog.records) == 2
    assert "unrecognized simvar" in caplog.records[0].message


def test_validate_event(caplog):
    with caplog.at_level(logging.WARNING):
        assert validate_event("kohlsmann_inc") != ""
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        assert validate_event("KOHLSMAN_INC") == "KOHLSMAN_INC"
    assert caplog.records == []


def test_validate_units(caplog):
    sv = validate_simvar("Indicated Altitude", settable=False)
    with caplog.at_level(logging.WARNING):
        assert validate_units("Indicated Altitude", None, sv) == "feet"
        assert validate_units("Indicated Altitude", "meters", sv) == "meters"
        assert validate_units("Indicated Altitude", "", sv) == ""
    assert caplog.records == []
