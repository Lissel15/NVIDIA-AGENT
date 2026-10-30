from pricing import apply_discount


def cart_total(items, discount_percent=0):
    subtotal = sum(i["price"] * i["qty"] for i in items)
    return round(apply_discount(subtotal, discount_percent), 2)
