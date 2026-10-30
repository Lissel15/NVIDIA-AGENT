"""High-level operations over tasks."""
from storage import MemoryStore
from task import Task


class Tracker:
    def __init__(self):
        self.store = MemoryStore()

    def create(self, title, priority=1, tags=None):
        task = Task(title, priority) if tags is None else Task(title, priority, list(tags))
        for tag in (tags or []):
            task.add_tag(tag)
        return self.store.add(task)

    def tag(self, task_id, tag):
        self.store.get(task_id).add_tag(tag)

    def complete(self, task_id):
        self.store.get(task_id).complete()

    def with_tag(self, tag):
        return [t for t in self.store.all() if t.has_tag(tag)]

    def open_tasks(self):
        return [t for t in self.store.all() if not t.done]

    def by_priority(self):
        return sorted(self.store.all(), key=lambda t: (-t.priority, t.title))