"""Text helpers used by a small blogging tool."""
import re


def slugify(text):
    """Lowercase, ASCII-ish slug: words joined by single hyphens, no edge hyphens."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]", "-", text)
    return text


def truncate(text, max_len, suffix="..."):
    """Return text cut to at most max_len characters INCLUDING the suffix."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + suffix


def word_count(text):
    return len(text.split())


def title_case(name):
    small = {"of", "the", "and", "in", "on"}
    words = name.lower().split()
    out = []
    for i, w in enumerate(words):
        out.append(w if (w in small and i > 0) else w.capitalize())
    return " ".join(out)


def reading_time_minutes(text, wpm=200):
    words = word_count(text)
    if words == 0:
        return 0
    return max(1, round(words / wpm))


def first_sentence(text):
    match = re.search(r"[.!?]", text)
    if not match:
        return text.strip()
    return text[: match.end()].strip()


def is_palindrome(text):
    cleaned = re.sub(r"[^a-z0-9]", "", text.lower())
    return cleaned == cleaned[::-1]