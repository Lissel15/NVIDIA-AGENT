"""Leaderboard ranking helpers."""


def rank_players(scores):
    """Return [(rank, name, score)] with the best score first.

    Ties share the same rank (1, 2, 2, 4 style) and are listed
    alphabetically by name.
    """
    ordered = sorted(scores.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    result = []
    prev_score = None
    rank = 0
    for position, (name, score) in enumerate(ordered, start=1):
        if score != prev_score:
            rank = position
            prev_score = score
        result.append((rank, name, score))
    return result


def top_n(scores, n):
    return [name for _, name, _ in rank_players(scores)[:n]]


def average_score(scores):
    if not scores:
        return 0.0
    return sum(scores.values()) / len(scores)


def above_average(scores):
    avg = average_score(scores)
    return sorted(name for name, s in scores.items() if s > avg)