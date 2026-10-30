"""Pre-flight check for the benchmark cases. Runs pytest on a copy of each case, WITHOUT the agent.

Usage (from the bugfix-agent folder, with the .venv active):
    python3 check_cases.py              # every case in cases.json
    python3 check_cases.py demo_repo_14 demo_repo_15     # with or without the demos/ prefix

A bug case is OK when some tests fail for the right reason. A feature case is OK when the
suite passes before the feature exists. Anything else is reported so you can fix the case
before spending tokens on it.
"""
import json, os, re, shutil, subprocess, sys, tempfile, time

TIMEOUT = int(os.environ.get("TEST_TIMEOUT", "240"))   # same limit the agent uses
only = {a if a.startswith('demos/') else 'demos/' + a for a in sys.argv[1:]}
cases = [c for c in json.load(open("cases.json")) if not only or c["repo"] in only]


def run_env(work):
    """Same PYTHONPATH logic as agent.py, so the copy is the code that gets imported."""
    env = dict(os.environ)
    paths = [p for p in (os.path.join(work, "src"), work) if os.path.isdir(p)]
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def num(pattern, text):
    m = re.search(pattern, text)
    return int(m.group(1)) if m else 0


rows = ["| Case | Folder | Files | Passed | Failed | Seconds | Verdict |", "|---|---|---|---|---|---|---|"]
for c in cases:
    repo, is_feature = c["repo"], bool(c.get("feature"))
    if not os.path.isdir(repo):
        rows.append(f"| {c['name']} | {repo} | - | - | - | - | MISSING FOLDER |")
        continue
    work = tempfile.mkdtemp(prefix="check_")
    shutil.copytree(repo, work, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    n_files = sum(len([f for f in fs]) for r, ds, fs in os.walk(work)
                  if ".git" not in r.split(os.sep) and "__pycache__" not in r.split(os.sep))
    t0, note = time.time(), ""
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "--tb=line", "-p", "no:cacheprovider"],
                           cwd=work, env=run_env(work), capture_output=True, text=True, timeout=TIMEOUT)
        out = r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        out = ""
        note = f"TIMEOUT (> {TIMEOUT}s): too slow for the agent"
    secs = round(time.time() - t0)
    passed, failed = num(r"(\d+) passed", out), num(r"(\d+) failed", out) + num(r"(\d+) errors?", out)
    if note:
        verdict = note
    elif n_files == 0:
        verdict = "EMPTY FOLDER: rebuild the case"
    elif "no tests ran" in out or "collected 0 items" in out:
        verdict = "NO TESTS COLLECTED: check test names and layout"
    elif "during collection" in out or (failed and not passed and re.search(r"ImportError|ModuleNotFoundError", out)):
        err = next((ln for ln in out.splitlines() if re.search(r"(ImportError|ModuleNotFoundError)", ln)), "")
        verdict = f"COLLECTION ERROR (install dependencies or check layout): {err.strip()[:90]}"
    elif is_feature:
        verdict = "OK (suite passes, ready for the feature)" if failed == 0 else f"CHECK: {failed} tests fail before the feature"
    else:
        verdict = f"OK ({failed} failing as expected)" if failed else "NOT A BUG CASE: every test passes"
    rows.append(f"| {c['name']} | {repo} | {n_files} | {passed} | {failed} | {secs} | {verdict} |")
    shutil.rmtree(work, ignore_errors=True)

print("\n".join(rows))