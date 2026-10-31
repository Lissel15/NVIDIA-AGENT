# Checks a fix after the agent is done.
# Usage: python verify_fix.py agent_output/<name>_fixed [--no-model]
# 1. looks for hardcoded answers in the patch
# 2. runs the suite 3 times to find flaky tests
# 3. asks a small model for edge-case tests and runs them on the fixed code
#    and on the original code (the patch applied backwards)
# Writes verify_report.md in that folder.
import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RUNS = 3
COMMON_NUMBER_LIMIT = 2  # numbers up to this are too common to mean anything
EXTRA_TESTS = 5
MODEL = os.environ.get("VERIFY_MODEL", "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B")


def added_lines(patch_text):
    # lines the patch added (skip the +++ header)
    return [l[1:] for l in patch_text.splitlines()
            if l.startswith("+") and not l.startswith("+++")]


def test_numbers(folder):
    # numbers on the right side of == in the test files
    numbers = set()
    for test_file in folder.glob("test_*.py"):
        numbers.update(re.findall(r"==\s*(-?\d+(?:\.\d+)?)", test_file.read_text(encoding="utf-8")))
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


def pytest_passes(folder, *args):
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *args],
                       cwd=folder, capture_output=True, text=True)
    return r.returncode == 0


def run_tests_repeatedly(folder):
    return [pytest_passes(folder) for _ in range(RUNS)]


# ---- extra tests ----

def changed_functions(folder, patch_text):
    # source of the functions the patch touched, as {file: [source, ...]}
    result = {}
    current = None
    new_line = 0
    touched = {}
    for line in patch_text.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            touched[current] = set()
        elif line.startswith("@@"):
            new_line = int(re.search(r"\+(\d+)", line).group(1))
        elif current and line.startswith("+"):
            touched[current].add(new_line)
            new_line += 1
        elif current and not line.startswith("-") and not line.startswith("\\"):
            new_line += 1
    for name, lines in touched.items():
        path = folder / name
        if not name.endswith(".py") or not path.exists() or Path(name).name.startswith("test_"):
            continue
        source = path.read_text(encoding="utf-8")
        found = []
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if any(node.lineno <= n <= node.end_lineno for n in lines):
                    found.append(ast.get_source_segment(source, node))
        if found:
            result[name] = found
    return result


def ask_model_for_tests(functions):
    from dotenv import load_dotenv
    from openai import OpenAI
    load_dotenv()
    client = OpenAI(base_url="https://api.tokenfactory.nebius.com/v1/",
                    api_key=os.environ["NEBIUS_API_KEY"])
    parts = []
    for name, sources in functions.items():
        module = Path(name).stem
        parts.append(f"# module: {module} (file {name})\n" + "\n\n".join(sources))
    prompt = (
        f"Write {EXTRA_TESTS} pytest tests for edge cases of these functions "
        "(empty input, negatives, None, duplicates, single element...). "
        "Import from the module names given. Each test is a function named test_extra_N "
        "with a single assert, and must not depend on the others. "
        "Only include cases where the correct result is obvious. "
        "Answer with the Python code only.\n\n" + "\n\n".join(parts))
    reply = client.chat.completions.create(
        model=MODEL, max_tokens=4000,
        messages=[{"role": "user", "content": prompt}])
    code = reply.choices[0].message.content or ""
    match = re.search(r"```(?:python)?\n(.*?)```", code, re.S)
    return match.group(1) if match else code


def make_original(folder, patch_file, target):
    # copy of the folder with the patch undone
    shutil.copytree(folder, target, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    r = subprocess.run(["git", "apply", "-R", "--unsafe-paths", str(patch_file)],
                       cwd=target, capture_output=True, text=True)
    return r.returncode == 0


def count_passing(folder, test_file, names):
    # run each test on its own so one bad test does not hide the others
    return {n: pytest_passes(folder, f"{test_file}::{n}") for n in names}


def extra_tests_section(folder, patch_file, patch_text):
    functions = changed_functions(folder, patch_text)
    if not functions:
        return ["- Extra tests: skipped (no changed functions found)"]
    try:
        code = ask_model_for_tests(functions)
    except Exception as e:  # no key, no network, etc.
        return [f"- Extra tests: skipped ({type(e).__name__})"]
    names = re.findall(r"^def (test_extra_\w+)", code, re.M)
    if not names:
        return ["- Extra tests: skipped (the model did not return usable tests)"]

    with tempfile.TemporaryDirectory() as tmp:
        fixed = Path(tmp) / "fixed"
        original = Path(tmp) / "original"
        shutil.copytree(folder, fixed, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        (fixed / "test_extra.py").write_text(code, encoding="utf-8")
        on_fixed = count_passing(fixed, "test_extra.py", names)

        if make_original(folder, patch_file, original):
            (original / "test_extra.py").write_text(code, encoding="utf-8")
            on_original = count_passing(original, "test_extra.py", names)
        else:
            on_original = None

    lines = [f"- Extra tests on the fixed code: {sum(on_fixed.values())}/{len(names)} passed"]
    if on_original is not None:
        lines.append(f"- Extra tests on the original code: {sum(on_original.values())}/{len(names)} passed")
        # fail before, pass after = the fix really changed behaviour
        confirmed = [n for n in names if on_fixed[n] and not on_original[n]]
        lines.append(f"- Pass only after the fix: {len(confirmed)}")
    for n in names:
        if not on_fixed[n]:
            lines.append(f"  - {n} fails on the fixed code (could be a real bug or a bad test)")
    lines.append("  - (the tests are written by a model, so check any failure by hand)")
    return lines


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        sys.exit("Usage: python verify_fix.py <result folder> [--no-model]")
    folder = Path(args[0]).resolve()
    patch_file = folder / "changes.patch"
    if not patch_file.exists():
        sys.exit(f"No changes.patch in {folder}")
    patch_text = patch_file.read_text(encoding="utf-8")

    findings = check_hardcoding(folder, patch_text)
    outcomes = run_tests_repeatedly(folder)
    flaky = len(set(outcomes)) > 1

    lines = ["# Verification report", "",
             f"- Hardcoding: {'WARN' if findings else 'PASS'}"]
    lines += [f"  - {f}" for f in findings]
    lines += [f"- Suite run {RUNS} times: {sum(outcomes)}/{RUNS} passed",
              f"- Flaky: {'YES' if flaky else 'NO'}"]
    if "--no-model" in sys.argv:
        lines.append("- Extra tests: skipped (--no-model)")
    else:
        lines += extra_tests_section(folder, patch_file, patch_text)
    lines.append("")
    report = "\n".join(lines)
    (folder / "verify_report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
