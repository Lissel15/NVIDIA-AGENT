"""Task model for a small task tracker."""

PRIORITIES = {1: "low", 2: "medium", 3: "high"}


class Task:
    def __init__(self, title, priority=1, tags=[]):
        self.title = title
        self.priority = priority
        self.tags = tags
        self.done = False

    def add_tag(self, tag):
        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)

    def has_tag(self, tag):
        return tag.strip().lower() in self.tags

    def complete(self):
        self.done = True

    def priority_label(self):
        return PRIORITIES.get(self.priority, "unknown")

    def __repr__(self):
        return f"Task({self.title!r}, priority={self.priority}, done={self.done})"