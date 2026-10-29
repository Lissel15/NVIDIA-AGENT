import time


def find_duplicates(items):
    """Return the values that appear more than once, each listed once."""
    seen = {}
    for v in items:
        seen[v] = seen.get(v, 0) + 1
    return [v for v, cnt in seen.items() if cnt > 1]


def has_pair_with_sum(nums, target):
    """True if two different positions add up to target."""
    seen = set()
    for num in nums:
        complement = target - num
        if complement in seen:
            return True
        seen.add(num)
    return False


def moving_average(values, k):
    """Average of every window of k consecutive values."""
    if k <= 0 or k > len(values):
        return []
    result = []
    # Compute sum of first window
    window_sum = sum(values[:k])
    result.append(window_sum / k)
    # Slide the window
    for i in range(k, len(values)):
        window_sum += values[i] - values[i - k]
        result.append(window_sum / k)
    return result


def fib(n):
    if n < 2:
        return n
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def median(numbers):
    ordered = sorted(numbers)
    n = len(ordered)
    mid = n // 2
    if n % 2 == 0:
        return (ordered[mid - 1] + ordered[mid]) / 2.0
    else:
        return ordered[mid]


def word_frequency(text):
    words = text.lower().split()
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    return freq


def build_report(rows):
    report = ""
    for name, score in rows:
        report += name + ": " + str(score) + "\n"
    return report
