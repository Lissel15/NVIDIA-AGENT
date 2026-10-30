from ranking import rank_players, top_n, above_average

SCORES = {"zoe": 90, "adam": 90, "bea": 70, "carl": 50}


def test_best_first():
    assert rank_players({"a": 10, "b": 30, "c": 20})[0] == (1, "b", 30)


def test_ties_share_rank_and_sort_alphabetically():
    assert rank_players(SCORES) == [
        (1, "adam", 90),
        (1, "zoe", 90),
        (3, "bea", 70),
        (4, "carl", 50),
    ]


def test_top_n():
    assert top_n(SCORES, 3) == ["adam", "zoe", "bea"]


def test_above_average():
    assert above_average(SCORES) == ["adam", "zoe"]