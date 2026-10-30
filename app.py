import glob
import os
import re
import subprocess
import sys

import gradio as gr

EXAMPLES = sorted(
    (d for d in glob.glob("demos/demo_repo*") if os.path.isdir(d)),
    key=lambda d: int(re.sub(r"\D", "", os.path.basename(d)) or 0),
)

try:
    import spaces

    @spaces.GPU
    def _gpu_placeholder():
        return None
except ImportError:
    pas


def _need_key():
    return not os.environ.get("NEBIUS_API_KEY")


def _stream(args, env, stdin_text=None):
    """Run agent.py as a subprocess and yield its output live."""
    proc = subprocess.Popen(
        [sys.executable, "-u", "agent.py", *args],
        stdin=subprocess.PIPE if stdin_text is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    if stdin_text is not None:
        proc.stdin.write(stdin_text)
        proc.stdin.close()
    log = ""
    try:
        for line in proc.stdout:
            log += line
            yield log
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
        log += "\n[demo] Run stopped (timeout)."
        yield log


def _summary_and_diff(log):
    """Final summary written by the agent + the diff of its changes."""
    summary = ""
    if "[agent] final summary:" in log:
        summary = log.split("[agent] final summary:", 1)[1]
        summary = summary.split("=== FINAL VERIFICATION ===", 1)[0].strip()
    diff = ""
    if "=== CHANGES ===" in log:
        diff = log.split("=== CHANGES ===", 1)[1]
        diff = diff.split("=== RESULT SAVED TO", 1)[0].strip()
    result = re.findall(r"RESULT: (\w+)", log)
    parts = []
    if result:
        parts.append(f"**Result: {result[-1]}**")
    if summary:
        parts.append("### Agent summary\n" + summary)
    parts.append("### Changes\n" + (f"```diff\n{diff}\n```" if diff else "No changes."))
    return "\n\n".join(parts)


def run_agent(mode_flag, example, extra_env):
    if _need_key():
        yield "Missing NEBIUS_API_KEY secret in the Space settings.", ""
        return
    env = {**os.environ, **extra_env}
    args = [example] + ([mode_flag] if mode_flag else [])
    log = ""
    for log in _stream(args, env):
        yield log, ""
    yield log, _summary_and_diff(log)


def fix_bug(example):
    yield from run_agent(None, example, {"MAX_ITERS": "30", "TEST_TIMEOUT": "60"})


def optimize_repo(example):
    yield from run_agent("--optimize", example, {"MAX_ITERS": "40", "TEST_TIMEOUT": "60"})


def explain_repo(example, question):
    if _need_key():
        yield "Missing NEBIUS_API_KEY secret in the Space settings."
        return
    env = {**os.environ, "AGENT_LANG": "English"}
    q = (question or "").strip().replace("\n", " ")
    stdin_text = (q + "\n" if q else "") + "exit\n"
    yield from _stream([example, "--explain"], env, stdin_text)


with gr.Blocks(title="Coding agent: fix, explain, optimize") as demo:
    gr.Markdown(
        "# Coding agent: fix, explain, optimize\n"
        "Powered by **NVIDIA Nemotron** on **Nebius Token Factory**. "
        "Pick an example repo and choose what the agent should do."
    )
    example = gr.Dropdown(EXAMPLES, value=EXAMPLES[0], label="Example repo")

    with gr.Tabs():
        with gr.Tab("Fix a bug"):
            gr.Markdown("Reproduces the failing test, patches the code and verifies the fix.")
            fix_btn = gr.Button("Fix bug", variant="primary")
            fix_log = gr.Textbox(label="Agent log (live)", lines=20, max_lines=20)
            fix_out = gr.Markdown()
            fix_btn.click(fix_bug, example, [fix_log, fix_out])

        with gr.Tab("Explain"):
            gr.Markdown("Read-only overview of the repo. Optionally ask a question about it.")
            question = gr.Textbox(label="Question (optional)",
                                  placeholder="e.g. Where is the sorting logic?")
            exp_btn = gr.Button("Explain repo", variant="primary")
            exp_out = gr.Textbox(label="Explanation (live)", lines=20, max_lines=20)
            exp_btn.click(explain_repo, [example, question], exp_out)

        with gr.Tab("Optimize"):
            gr.Markdown(
                "Fixes bugs, cleans up dead code and reduces algorithmic complexity. "
                "Every change is checked by the tests and measured with benchmarks. "
                "This can take a few minutes."
            )
            opt_btn = gr.Button("Optimize code", variant="primary")
            opt_log = gr.Textbox(label="Agent log (live)", lines=20, max_lines=20)
            opt_out = gr.Markdown()
            opt_btn.click(optimize_repo, example, [opt_log, opt_out])

demo.queue(max_size=8, default_concurrency_limit=1)
demo.launch(ssr_mode=False)