"""Monetary calculations over an Inventory."""


def total_value(inv):
    return round(sum(v["qty"] * v["price"] for v in inv.items().values()), 2)


def value_of(inv, sku):
    return round(inv.qty(sku) * inv.price(sku), 2) if inv.qty(sku) else 0.0


def most_valuable(inv):
    items = inv.items()
    if not items:
        return None
    return max(items, key=lambda s: items[s]["qty"] * items[s]["price"])