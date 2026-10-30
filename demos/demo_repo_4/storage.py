"""Tiny in-memory storage layer."""

class MemoryStore:
    def __init__(self):
        self._items = {}
        self._next_id = 1

    def add(self, obj):
        item_id = self._next_id
        self._items[item_id] = obj
        self._next_id += 1
        return item_id

    def get(self, item_id):
        return self._items[item_id]

    def all(self):
        return [self._items[k] for k in sorted(self._items)]

    def remove(self, item_id):
        del self._items[item_id]

    def __len__(self):
        return len(self._items)