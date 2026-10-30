from inventory import Inventory
from valuation import total_value, value_of, most_valuable


def make():
    inv = Inventory()
    inv.add("A1", 10, 2.5)
    inv.add("B2", 3, 10.0)
    return inv


def test_total_value():
    assert total_value(make()) == 55.0


def test_value_of():
    assert value_of(make(), "B2") == 30.0
    assert value_of(make(), "ZZ") == 0.0


def test_most_valuable():
    assert most_valuable(make()) == "B2"
    assert most_valuable(Inventory()) is None