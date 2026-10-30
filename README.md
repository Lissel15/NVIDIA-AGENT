# Shippies Agent: a test-driven coding agent

An autonomous coding agent that **fixes bugs, adds features, builds new projects, optimizes code and explains repositories**, and that only calls a job done when the test suite says so. It runs on **Nebius Token Factory** with **NVIDIA Nemotron 3 Super** (`nvidia/nemotron-3-super-120b-a12b`).

Built for the **Nebius x NVIDIA Global AI Hackathon**, track: **Coding & Agentic Engineering**.

- Demo: `TODO: demo URL`
- Video (3 min): `TODO: YouTube URL`
- License: MIT

## Why it is different

Most coding agents write a patch and say "done". This one does not trust itself:

1. **Tests are the judge.** After every edit the agent re-runs the suite and is told which tests now pass and which still fail.
2. **It cannot cheat.** Original tests and pytest config files are protected and fingerprinted with SHA-256; if any of them changes, the run is not a success. Placeholder tests (`assert True`, tests that import nothing from the project, skipped tests) are rejected.
3. **It cannot silently make things worse.** An edit that breaks the syntax or increases the number of failing tests is undone automatically, and the agent is told why. If the run ends unsolved, the agent returns to the best state it reached.
4. **It is honest about its limits.** Every run ends with `RESULT: SUCCESS`, `REVIEW` (needs a human look) or `ERROR` (broken case, nothing was attempted). In scaffold mode the generated README must include a "Not verified" section listing what the tests could not check.

## Modes

| Mode | Command | What it does |
|---|---|---|
| Bug fix | `python3 agent.py <repo>` | Reads the failing tests, finds the root cause, edits the code until the suite passes. |
| Feature | `python3 agent.py <repo> --feature "<description>"` | Test-first: writes a new failing test, confirms it fails, then implements the feature. |
| Scaffold | `python3 agent.py --scaffold "<specification>"` | Builds a whole project from scratch: plan, dependencies, tests first, code, README. |
| Optimize | `python3 agent.py <repo> --optimize` | Fixes bugs, removes dead code and reduces algorithmic complexity, proving each improvement with a benchmark and with tests that compare against a naive reference. |
| Explain | `python3 agent.py <repo> --explain` | Read-only guide: explains what the repo does and how it is organized, and answers follow-up questions citing `file:line`. |

`<repo>` can be a folder, or a single Python file. Results are saved to `agent_output/<name>_fixed` (all tests pass) or `agent_output/<name>_review` (needs a human look); scaffold projects go to `scaffold_output/<name>`.

Example scaffold request:

```bash
python3 agent.py --scaffold "Create a FastAPI app with JWT auth, register and login, connected to PostgreSQL using asyncpg"
```

A generated example is in [`scaffold_output/create-a-fastapi-app-with-jwt-auth-regis`](scaffold_output/create-a-fastapi-app-with-jwt-auth-regis) (7 tests passing; tested with Python 3.14). An example of the optimize mode is in [`agent_output/demo_repo_16_fixed`](agent_output/demo_repo_16_fixed), with the patch in `changes.patch`.

External services such as PostgreSQL are never available while testing, so the agent puts them behind a small interface, tests all the logic with an in-memory implementation, and lists the real adapter under "Not verified" in the generated README.

## How it works

```
read code → write/choose a test → edit → run pytest → read traceback → fix → repeat
                                      ↑                                  │
                                      └── undo if syntax breaks or failures increase
```

The model works through tools, and the agent controls what each tool is allowed to do:

| Tool | Purpose |
|---|---|
| `list_files`, `read_file`, `read_symbol`, `search_code` | Explore the repo (`read_symbol` reads a whole function or `Class.method` using `ast`). |
| `edit_file`, `edit_lines` | Change code. `edit_lines` only accepts lines the model has read since the last edit. |
| `add_test`, `run_tests` | Create new tests (never overwrite existing ones) and run pytest, optionally on a single test. |
| `submit_plan`, `write_file`, `install_requirements` | Scaffold mode. The plan must come before any file; only a fixed list of packages can be installed, as binary wheels. |
| `analyze_code`, `benchmark` | Optimize mode. Find dead code and complexity leads, and measure before/after. |

Other safeguards: the agent works on a temporary copy of your repo and never touches the original; generated code runs without API keys in its environment; repeated reads are blocked and the model is steered toward editing; if the agent makes no progress for several iterations it can escalate to a stronger model.

### How Nemotron and Token Factory are used

- All reasoning and tool calling goes through Token Factory's OpenAI-compatible chat completions API (`https://api.tokenfactory.nebius.com/v1/`) with **Nemotron 3 Super** as the default model.
- Nemotron is a reasoning model: reasoning tokens count against `max_tokens`. The agent sets a generous limit and, if a reply is cut off before the tool call is complete, asks the model to repeat it.
- **Model routing (optional):** if `AGENT_ESCALATION_MODEL` is set (for example a larger Nemotron model), the agent switches to it after `STUCK_AFTER` iterations without progress and uses the smaller model for everything else. The benchmark below was run **without** escalation, with Nemotron 3 Super only.
- Other Nebius tools: `TODO: list anything else the team used, or delete this line`.

## Quick start

Requirements: Python 3.10+ (developed and tested with Python 3.14) and a Nebius Token Factory API key.

```bash
git clone https://github.com/Lissel15/NVIDIA-AGENT.git
cd NVIDIA-AGENT
python3 -m venv .venv && source .venv/bin/activate
pip install openai python-dotenv pytest
cp .env.example .env          # then put your key in .env
python3 agent.py demo_repo    # a tiny bug-fix example
```

`.env` is git-ignored. Never commit your key.

### Configuration (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `NEBIUS_API_KEY` | required | Token Factory API key |
| `AGENT_MODEL` | `nvidia/nemotron-3-super-120b-a12b` | Main model |
| `AGENT_ESCALATION_MODEL` | unset | Stronger model used when the agent is stuck |
| `AGENT_LANG` | `English` | Language of the first overview in explain mode |
| `MAX_ITERS` | 60 (80 in scaffold and optimize) | Maximum model calls per run |
| `MAX_TOKENS` | 16000 | Token limit per reply (includes reasoning) |
| `TEST_TIMEOUT` | 240 | Seconds allowed for one pytest run |
| `STUCK_AFTER` | 6 | Iterations without progress before escalating |
| `READ_LIMIT` | 6 | Read-only calls in a row before the agent must act |
| `AUTO_TEST` | 1 | Re-run the tests automatically after every edit |

## Benchmark

`python3 benchmark.py` runs the agent on every case in `cases.json` and writes `results.md`. `python3 check_cases.py` checks each case *without* the agent, so no tokens are spent on a broken case.

There are 15 cases:

- **Cases 1 to 7:** small hand-written repositories (five bugs and two features).
- **Cases 8 to 15:** real bugs reproduced from open-source projects. Each is built from the commit just before the upstream fix, plus the test added by that fix, so the failing test is genuine. `make_real_cases.sh` rebuilds all eight; every case folder has a `CASE_SOURCE.txt` with the upstream project and commit, and keeps the project's original license.

| Case folder | Upstream project |
|---|---|
| `demo_repo_8` | [more-itertools](https://github.com/more-itertools/more-itertools) |
| `demo_repo_9` | [boltons](https://github.com/mahmoud/boltons) |
| `demo_repo_10` | [toolz](https://github.com/pytoolz/toolz) |
| `demo_repo_11` | [requests](https://github.com/psf/requests) |
| `demo_repo_12` | [click](https://github.com/pallets/click) |
| `demo_repo_13` | [marshmallow](https://github.com/marshmallow-code/marshmallow) |
| `demo_repo_14` | [sortedcontainers](https://github.com/grantjenks/python-sortedcontainers) |
| `demo_repo_15` | [tabulate](https://github.com/astanin/python-tabulate) |

`demo_repo_16` is a separate hand-written demo for the optimize mode; it is not part of the benchmark.

### Results (Nemotron 3 Super, one run per case, no escalation)

| Case | Result | Original tests intact | Iterations | Tokens | Time (s) |
|---|---|---|---|---|---|
| average-off-by-one | SUCCESS | YES | 5 | 10899 | 7 |
| cart-and-stats | SUCCESS | YES | 7 | 19349 | 12 |
| median-feature | SUCCESS | YES | 8 | 18422 | 12 |
| mutable-default-tracker | SUCCESS | YES | 9 | 34257 | 18 |
| ranking-ties | SUCCESS | YES | 5 | 18780 | 9 |
| text-edge-cases | SUCCESS | YES | 5 | 16067 | 12 |
| low-stock-feature | SUCCESS | YES | 53 | 701027 | 318 |
| more-itertools-falsy-exception | SUCCESS | YES | 14 | 96918 | 81 |
| boltons-barrellist | SUCCESS | YES | 12 | 139841 | 68 |
| toolz-interpose-empty | SUCCESS | YES | 30 | 221903 | 103 |
| requests-url-header-bug | SUCCESS | YES | 46 | 827298 | 979 |
| click-variadic-option-bug | REVIEW | YES | 60 | 797900 | 261 |
| marshmallow-nested-schema-bug | SUCCESS | YES | 9 | 42476 | 95 |
| sortedcontainers-bug | REVIEW | YES | 60 | 1175097 | 561 |
| tabulate-edgecase | SUCCESS | YES | 25 | 276722 | 171 |

**13 of 15 cases solved**: 7 of 7 hand-written cases and 6 of 8 real open-source bugs. The two unsolved cases (`click-variadic-option-bug` and `sortedcontainers-bug`) ended in `REVIEW`: the agent used all 60 iterations without making every test pass. In all 15 runs the original tests stayed intact.

Cost grows with difficulty: the small cases need 10 to 35 thousand tokens, while the harder real-world bugs and the multi-function feature need 100 thousand to 1.2 million.

These are single runs. The model is not deterministic, so a repeated run can give a different result. Some of these cases (for example `demo_repo_8` and `demo_repo_9`) were also used while developing the agent, so they are not a fully blind test.

## Limitations

- The agent targets Python projects tested with pytest.
- Generated code runs on the machine that runs the agent, without API keys in its environment but without a container sandbox. Use a throwaway environment for untrusted tasks.
- In scaffold mode the tests run in the environment where the agent runs, so a dependency missing from `requirements.txt` can go unnoticed. We hit this once in our own example and fixed its `requirements.txt` by hand.
- In scaffold mode, real external services (for example a PostgreSQL adapter) are not exercised by the tests; the generated README says so.
- Optimize mode relies on the model's judgement for what is safe to remove; the test suite and the comparisons against a naive reference are the safety net, not a proof.

## Repository layout

```
agent.py             the agent (all modes)
benchmark.py         runs every case and writes results.md
check_cases.py       validates the cases without using the model
cases.json           the 15 benchmark cases
results.md           benchmark results
demo_repo*/          the cases (see CASE_SOURCE.txt for the real ones)
agent_output/        example results of the fix and optimize modes
scaffold_output/     example project generated by --scaffold
make_real_cases.sh   rebuilds the eight real-bug cases from upstream commits
```

## Team

David Miguel Medina Raymundo
Maria Fernanda Morales Hernández
Lissel Erandi Flores Polvo
Miguel Ángel Sarmiento Luna

## AI assistance and third-party code

We used AI coding assistants (Claude and aider) while developing this project.

The real-bug cases in `demo_repo_8` to `demo_repo_15` contain code from the open-source projects listed above, each under its own license (kept inside the case folder). They are included only as benchmark inputs. Some of them include test fixtures, such as TLS certificates in `demo_repo_11/tests/certs`, that come from the upstream project.

This project is released under the MIT License (see `LICENSE`).
