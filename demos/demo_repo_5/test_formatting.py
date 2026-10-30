from formatting import format_table, podium

SCORES = {"zoe": 90, "adam": 90, "bea": 70, "carl": 50}


def test_podium():
    assert podium(SCORES) == {"gold": "adam", "silver": "zoe", "bronze": "bea"}


def test_table_header_and_first_row():
    lines = format_table(SCORES).splitlines()
    assert lines[0].split() == ["#", "Name", "Score"]
    assert lines[1].split() == ["1", "adam", "90"]