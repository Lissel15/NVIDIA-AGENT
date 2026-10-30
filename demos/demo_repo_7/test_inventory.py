import pytest
from inventory import Inventory


def make():
    inv = Inventory()
    inv.add("A1", 10, 2.5)
    inv.add("B2", 3, 10.0)
    return inv


def test_add_and_qty():
    inv = make()
    inv.add("A1", 5, 3.0)
    assert inv.qty("A1") == 15
    assert inv.price("A1") == 3.0


def test_remove():
    inv = make()
    inv.remove("B2", 2)
    assert inv.qty("B2") == 1


def test_remove_too_much():
    with pytest.raises(ValueError):
        make().remove("B2", 99)


def test_add_rejects_nonpositive():
    with pytest.raises(ValueError):
        make().add("C3", 0, 1.0)