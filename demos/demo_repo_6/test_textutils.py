from textutils import (
    slugify, truncate, word_count, title_case,
    reading_time_minutes, first_sentence, is_palindrome,
)


def test_slugify_basic():
    assert slugify("Hello World") == "hello-world"


def test_slugify_collapses_and_trims():
    assert slugify("  Hello,   World!! ") == "hello-world"


def test_truncate_short_text_unchanged():
    assert truncate("hello", 10) == "hello"


def test_truncate_respects_max_len():
    result = truncate("hello world", 8)
    assert result == "hello..."
    assert len(result) == 8


def test_word_count():
    assert word_count("a b  c") == 3


def test_title_case():
    assert title_case("the lord OF the rings") == "The Lord of the Rings"


def test_reading_time():
    assert reading_time_minutes("word " * 400) == 2
    assert reading_time_minutes("") == 0


def test_first_sentence():
    assert first_sentence("Hi there. More text.") == "Hi there."


def test_palindrome():
    assert is_palindrome("A man, a plan, a canal: Panama")