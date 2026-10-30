from cart import cart_total

ITEMS = [{"price": 10.0, "qty": 2}, {"price": 5.0, "qty": 2}]


def test_cart_no_discount():
    assert cart_total(ITEMS) == 30.0


def test_cart_with_discount():
    assert cart_total(ITEMS, 10) == 27.0
