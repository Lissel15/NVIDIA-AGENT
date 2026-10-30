"""Text reports built on top of the tracker."""


def summary(tracker):
    tasks = tracker.store.all()
    done = sum(1 for t in tasks if t.done)
    return {"total": len(tasks), "done": done, "open": len(tasks) - done}


def tag_counts(tracker):
    counts = {}
    for task in tracker.store.all():
        for tag in task.tags:
            counts[tag] = counts.get(tag, 0) + 1
    return counts


def render(tracker):
    lines = []
    for task in tracker.by_priority():
        mark = "x" if task.done else " "
        tags = ",".join(task.tags) or "-"
        lines.append(f"[{mark}] {task.title} ({task.priority_label()}) tags: {tags}")
    return "\n".join(lines)