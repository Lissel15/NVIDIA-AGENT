from stats import largest


def test_largest_negatives():
    assert largest([-5, -2, -9]) == -2


def test_largest_empty():
    assert largest([]) is None
