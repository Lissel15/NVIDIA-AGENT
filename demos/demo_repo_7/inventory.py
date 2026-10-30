"""Inventory data structure."""


class Inventory:
    def __init__(self):
        self._stock = {}

    def add(self, sku, qty, price):
        if qty <= 0:
            raise ValueError("qty must be positive")
        if sku in self._stock:
            self._stock[sku]["qty"] += qty
            self._stock[sku]["price"] = price
        else:
            self._stock[sku] = {"qty": qty, "price": price}

    def remove(self, sku, qty):
        if sku not in self._stock:
            raise KeyError(sku)
        if qty > self._stock[sku]["qty"]:
            raise ValueError("not enough stock")
        self._stock[sku]["qty"] -= qty

    def qty(self, sku):
        return self._stock.get(sku, {}).get("qty", 0)

    def price(self, sku):
        return self._stock[sku]["price"]

    def skus(self):
        return sorted(self._stock)

    def items(self):
        return {sku: dict(v) for sku, v in self._stock.items()}