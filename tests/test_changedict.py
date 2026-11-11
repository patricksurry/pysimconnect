from simconnect.changedict import ChangeDict


def test_changedict_basic_and_tolerance():
    d = ChangeDict()
    d["a"] = 1.0
    t1 = d.latest()
    assert t1 > 0
    assert d["a"] == 1.0

    # Within default tolerance (1e-6), should not update
    d["a"] = 1.0 + 1e-9
    assert d["a"] == 1.0

    # Outside tolerance, should update
    d["a"] = 2.0
    assert d["a"] == 2.0


def test_changedict_custom_comparator():
    d = ChangeDict(comparators={"coarse": lambda a, b: abs(a - b) < 10})
    d["coarse"] = 100
    d["coarse"] = 105
    assert d["coarse"] == 100
    d["coarse"] = 115
    assert d["coarse"] == 115


def test_changedict_delitem():
    d = ChangeDict()
    d["a"] = 1
    d["b"] = 2
    del d["a"]
    assert "a" not in d
    assert d.pop("b") == 2
    assert d.latest() == 0
