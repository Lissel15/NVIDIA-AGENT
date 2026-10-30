from report import summary, tag_counts, render
from tracker import Tracker


def build():
    t = Tracker()
    a = t.create("ship release", priority=3)
    b = t.create("fix typo", priority=1)
    t.create("plan sprint", priority=2)
    t.tag(a, "release")
    t.tag(b, "docs")
    t.complete(b)
    return t


def test_summary():
    assert summary(build()) == {"total": 3, "done": 1, "open": 2}


def test_tag_counts():
    assert tag_counts(build()) == {"release": 1, "docs": 1}


def test_render_first_line():
    first = render(build()).splitlines()[0]
    assert first == "[ ] ship release (high) tags: release"