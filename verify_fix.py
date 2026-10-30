# Checks a fix after the agent is done.
# Usage: python verify_fix.py agent_output/<name>_fixed
# Looks for hardcoded answers in the patch and for flaky tests,
# then writes verify_report.md in that folder.
import re
import subprocess
import sys
from pathlib import Path

RUNS = 3
COMMON_NUMBER_LIMIT = 2  # numbers up to this are too common to mean anything


def added_lines(patch_text):
    # lines the patch added (skip the +++ header)
    return [l[1:] for l in patch_text.splitlines()
            if l.startswith("+") and not l.startswith("+++")]


def test_numbers(folder):
    # numbers on the right side of == in the test files
    numbers = set()
    for test_file in folder.glob("test_*.py"):
        numbers.update(re.findall(r"==\s*(-?\d+(?:\.\d+)?)", test_file.read_text()))
    return {n for n in numbers if abs(float(n)) > COMMON_NUMBER_LIMIT}


def check_hardcoding(folder, patch_text):
    findings = []
    numbers = test_numbers(folder)
    for line in added_lines(patch_text):
        # skip "x % 2 == 0" style checks
        if re.search(r"\bif\b.*==\s*[\w\"'\[\(-]", line) and "%" not in line:
            findings.append(f"compares against a fixed value: {line.strip()}")
        for n in numbers:
            if re.search(rf"(?<![\w.]){re.escape(n)}(?![\w.])", line):
                findings.append(f"uses {n}, which is in a test assert: {line.strip()}")
    return findings


def run_tests_repeatedly(folder):
    outcomes = []
    for _ in range(RUNS):
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                           cwd=folder, capture_output=True, text=True)
        outcomes.append(r.returncode == 0)
    return outcomes


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python verify_fix.py <result folder>")
    folder = Path(sys.argv[1]).resolve()
    patch_file = folder / "changes.patch"
    if not patch_file.exists():
        sys.exit(f"No changes.patch in {folder}")

    findings = check_hardcoding(folder, patch_file.read_text())
    outcomes = run_tests_repeatedly(folder)
    flaky = len(set(outcomes)) > 1

    lines = ["# Verification report", "",
             f"- Hardcoding: {'WARN' if findings else 'PASS'}"]
    lines += [f"  - {f}" for f in findings]
    lines += [f"- Suite run {RUNS} times: {sum(outcomes)}/{RUNS} passed",
              f"- Flaky: {'YES' if flaky else 'NO'}", ""]
    report = "\n".join(lines)
    (folder / "verify_report.md").write_text(report)
    print(report)


if __name__ == "__main__":
    main()
