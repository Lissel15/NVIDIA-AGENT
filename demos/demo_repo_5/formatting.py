"""Pretty-printing for leaderboards."""
from ranking import rank_players


def format_table(scores):
    rows = rank_players(scores)
    width = max((len(name) for _, name, _ in rows), default=4)
    lines = [f"{'#':>2}  {'Name':<{width}}  Score"]
    for rank, name, score in rows:
        lines.append(f"{rank:>2}  {name:<{width}}  {score}")
    return "\n".join(lines)


def podium(scores):
    medals = ["gold", "silver", "bronze"]
    return {medals[i]: name for i, (_, name, _) in enumerate(rank_players(scores)[:3])}