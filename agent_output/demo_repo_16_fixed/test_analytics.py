import pytest
from analytics import (find_duplicates, has_pair_with_sum, moving_average, fib,
                       median, word_frequency, build_report)


def test_find_duplicates():
    assert sorted(find_duplicates([1, 2, 3, 2, 1, 4])) == [1, 2]
    assert find_duplicates([]) == []
    assert find_duplicates([5]) == []


def test_has_pair_with_sum():
    assert has_pair_with_sum([1, 4, 6], 10) is True
    assert has_pair_with_sum([1, 4, 6], 12) is False
    assert has_pair_with_sum([5], 10) is False      # one element cannot pair with itself
    assert has_pair_with_sum([5, 5], 10) is True


def test_moving_average():
    assert moving_average([1, 2, 3, 4], 2) == [1.5, 2.5, 3.5]
    assert moving_average([1, 2], 3) == []


def test_fib():
    assert [fib(n) for n in range(8)] == [0, 1, 1, 2, 3, 5, 8, 13]


def test_median():
    assert median([3, 1, 2]) == 2
    assert median([4, 1, 3, 2]) == 2.5


def test_word_frequency():
    assert word_frequency("a b A c b a") == {"a": 3, "b": 2, "c": 1}
    assert word_frequency("") == {}


def test_build_report():
    assert build_report([("ana", 9), ("luis", 7)]) == "ana: 9\nluis: 7\n"
