import os
import json
import time


def find_duplicates(items):
    """Return the values that appear more than once, each listed once."""
    dups = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j] and items[i] not in dups:
                dups.append(items[i])
    return dups


def has_pair_with_sum(nums, target):
    """True if two different positions add up to target."""
    for i in range(len(nums)):
        for j in range(len(nums)):
            if i != j and nums[i] + nums[j] == target:
                return True
    return False


def moving_average(values, k):
    """Average of every window of k consecutive values."""
    result = []
    for i in range(len(values) - k):
        window = values[i:i + k]
        total = 0
        for v in window:
            total += v
        result.append(total / k)
    return result


def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


def median(numbers):
    ordered = sorted(numbers)
    mid = len(ordered) // 2
    if len(ordered) % 2 == 0:
        return ordered[mid]
    return ordered[mid]


def word_frequency(text):
    words = text.lower().split()
    unique = []
    for w in words:
        if w not in unique:
            unique.append(w)
    return {w: words.count(w) for w in unique}


def word_counts(text):
    words = text.lower().split()
    unique = []
    for w in words:
        if w not in unique:
            unique.append(w)
    return {w: words.count(w) for w in unique}


def legacy_normalize(values):
    lo = min(values)
    hi = max(values)
    return [(v - lo) / (hi - lo) for v in values]


def build_report(rows):
    start = time.time()
    report = ""
    for name, score in rows:
        report += name + ": " + str(score) + "\n"
    return report
