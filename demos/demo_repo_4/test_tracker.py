from tracker import Tracker


def test_create_and_complete():
    t = Tracker()
    a = t.create("write docs", priority=2)
    t.complete(a)
    assert t.open_tasks() == []


def test_priority_order():
    t = Tracker()
    t.create("b", priority=1)
    t.create("a", priority=3)
    assert [x.title for x in t.by_priority()] == ["a", "b"]


def test_tags_are_per_task():
    t = Tracker()
    a = t.create("first")
    b = t.create("second")
    t.tag(a, "urgent")
    assert [x.title for x in t.with_tag("urgent")] == ["first"]
    assert t.store.get(b).tags == []