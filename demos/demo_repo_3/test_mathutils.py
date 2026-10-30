from mathutils import average


def test_average():
    assert average([2, 4, 6]) == 4


def test_average_empty():
    assert average([]) is None
