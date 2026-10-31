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


def touched_lines(patch_text):
    # {file: line numbers (in the fixed file) that the patch added}
    touched = {}
    current = None
    new_line = 0
    for line in patch_text.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            touched[current] = set()
        elif line.startswith("@@"):
            new_line = int(re.search(r"\+(\d+)", line).group(1))
        elif current and line.startswith("+"):
            touched[current].add(new_line)
            new_line += 1
        elif current and not line.startswith(("-", "\\")):
            new_line += 1
    return touched


# ---- hardcoding check (uses ast) ----

def literal(node):
    # (True, value) if the node is a plain literal like 4, [1, 2] or "abc"
    try:
        return True, ast.literal_eval(node)
    except Exception:
        return False, None


def norm(value):
    # turns a value into a string so 4 and 4.0, or two equal lists, match
    if isinstance(value, (list, tuple)):
        return "seq:" + ",".join(norm(v) for v in value)
    if isinstance(value, (set, frozenset)):
        return "set:" + ",".join(sorted(norm(v) for v in value))
    if isinstance(value, dict):
        return "map:" + ",".join(sorted(norm(k) + "=" + norm(v) for k, v in value.items()))
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"num:{float(value)}"
    return f"{type(value).__name__}:{value!r}"


def interesting(value, in_return):
    # skip values that show up in any code (0, 1, True, None, [], "a"...)
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (int, float)):
        return abs(value) > COMMON_NUMBER_LIMIT
    if isinstance(value, str):
        return in_return and len(value) >= 3
    if isinstance(value, (list, tuple, set, frozenset, dict)):
        return len(value) >= 2
    return False


def expected_values(folder):
    # literals the tests compare against: assert x == 4, assertEqual(x, [1, 2])
    values = set()
    test_files = list(folder.rglob("test_*.py")) + list(folder.rglob("*_test.py"))
    for test_file in test_files:
        try:
            tree = ast.parse(test_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            parts = []
            if isinstance(node, ast.Compare) and any(isinstance(o, ast.Eq) for o in node.ops):
                parts = [node.left, *node.comparators]
            elif isinstance(node, ast.Call) and getattr(node.func, "attr", "") in ("assertEqual", "assertEquals"):
                parts = node.args
            for part in parts:
                ok, value = literal(part)
                if ok and interesting(value, True):
                    values.add(norm(value))
    return values


def check_hardcoding(folder, patch_text):
    expected = expected_values(folder)
    findings = []
    for name, lines in touched_lines(patch_text).items():
        path = folder / name
        if not name.endswith(".py") or Path(name).name.startswith("test_") or not path.exists():
            continue
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        source_lines = source.splitlines()
        returned = {id(n.value) for n in ast.walk(tree) if isinstance(n, ast.Return) and n.value}
        flagged = set()

        def flag(node, why):
            if node.lineno not in flagged:
                flagged.add(node.lineno)
                findings.append(f"{name}:{node.lineno} {why}: {source_lines[node.lineno - 1].strip()}")

        for node in ast.walk(tree):
            if getattr(node, "lineno", None) not in lines:
                continue
            # if x == <fixed value>: return <fixed value>
            if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
                test = node.test
                if len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
                    ok, value = literal(test.comparators[0])
                    returns_literal = any(isinstance(n, ast.Return) and n.value is not None
                                          and literal(n.value)[0] for b in node.body for n in ast.walk(b))
                    if ok and returns_literal and (interesting(value, False) or norm(value) in expected):
                        flag(node, "returns a fixed value when the input equals a fixed value")
            # a literal that is the same as one the tests expect
            ok, value = literal(node) if isinstance(node, (ast.Constant, ast.List, ast.Tuple, ast.Dict, ast.Set, ast.UnaryOp)) else (False, None)
            if ok and interesting(value, id(node) in returned) and norm(value) in expected:
                flag(node, "uses a value that is in the test asserts")
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
    for name, lines in touched_lines(patch_text).items():
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
    r = subprocess.run(["git", "apply", "-R", "--unsafe-paths", "--ignore-whitespace", str(patch_file)],
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
