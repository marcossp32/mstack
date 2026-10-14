#!/usr/bin/env python3
"""Step check. Deterministic, no model judgement.

  step_check.py baseline --test-cmd "<cmd>" | --test-cmd none [--test-file-cmd "<cmd with {test}>"]
      Once, on the feature branch before the first step. Records the suite's
      state for that branch, so later steps can be compared against it, and
      the command that runs one test file, for the pinned check.

  step_check.py check --base origin/<feature branch> [--pr <n>] [--secrets-cmd "<cmd>"]
      Fetch first: a stale local feature branch puts earlier steps in the diff.
      After each build, on the step branch, with a clean checkout.
      Exit 0 = PASS, 1 = FAIL; an abort exits non-zero and prints no verdict.

Checks:
  1. Suite no worse than at the feature's start (exit-code level). Red is run
     up to 3 times: red on some runs only is a FAIL marked intermittent. Every
     run's full output is saved under the git dir and its path printed.
  2. Every existing test file changed or deleted, and every file where the
     step adds a skip, a focus or a suppression, is listed in the PR's Tests
     changed section.
  3. No credentials in the added lines.
  4. Pinned: each test file the PR's Pinned by section lists passes at HEAD
     and fails with the step's non-test changes reverted. A step that changes
     code needs one, or `none · <why>` there.
"""
import argparse
import os
import re
import subprocess
import sys

from common import (TEST_PATH, die, git, now, read_json, reached_assertion,
                    root, setup_failure, sh, state_dir, tail, tracked_changes,
                    write_json)

SECRETS = [
    ("private key", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("AWS access key", r"\bAKIA[0-9A-Z]{16}\b"),
    ("GitHub token", r"\bgh[pousr]_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{22,}"),
    ("Slack token", r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    ("Stripe live key", r"\b[rs]k_live_[0-9a-zA-Z]{20,}"),
    ("Google API key", r"\bAIza[0-9A-Za-z_\-]{35}\b"),
    ("Anthropic key", r"\bsk-ant-[A-Za-z0-9_\-]{20,}"),
    ("OpenAI key", r"\bsk-(proj-)?[A-Za-z0-9_\-]{32,}"),
]
# Reported for a human to look at; does not fail the step on its own.
SUSPECT = re.compile(
    r"(?i)(password|passwd|secret|api[_-]?key|access[_-]?token)\s*[:=]\s*"
    r"['\"][^'\"\s]{8,}['\"]")

# Lines that make a check stop checking. Counted per file, added minus
# removed, so code that only moves is not flagged.
LOOSENERS = [
    ("skip", re.compile(
        r"\b(it|test|describe|context|suite)\.(skip|todo)\b|\b(xit|xdescribe|xtest)\s*\("
        r"|@pytest\.mark\.(skip|xfail)|\bpytest\.skip\(|@unittest\.skip|\bskipTest\("
        r"|@Disabled\b|@Ignore\b|\bt\.Skip(Now|f)?\(|#\[ignore\]")),
    ("focus", re.compile(
        r"\b(it|test|describe|context|suite)\.only\b|\b(fit|fdescribe)\s*\(")),
    ("suppression", re.compile(
        r"@ts-(ignore|nocheck|expect-error)|eslint-disable|biome-ignore|#\s*noqa\b"
        r"|#\s*type:\s*ignore|pylint:\s*disable|//\s*nolint|#\[allow\(|@SuppressWarnings"
        r"|rubocop:disable|@phpstan-ignore|NOSONAR|pragma:\s*no cover"
        r"|(istanbul|c8|v8)\s+ignore")),
    ("check bypassed", re.compile(
        r"\|\|\s*true\b|continue-on-error:\s*true|--passWithNoTests|--no-verify")),
]

# Files that carry no behaviour a test could pin.
DOC_PATH = re.compile(r"\.(md|mdx|rst|txt|adoc)$|(^|/)(LICENSE|CHANGELOG)[^/]*$",
                      re.IGNORECASE)

SUITE_RUNS = 3


def run_git(args, cwd):
    """git with an argument list: paths reach it unquoted on every platform."""
    p = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()


def save_log(pr, run, out):
    """The suite's full output, kept so a FAIL never needs a rerun to read."""
    stamp = now().replace(":", "")
    path = os.path.join(state_dir("check"), f"{pr or 'nopr'}-{stamp}-run{run}.log")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(out)
    return path


def baseline_path(branch):
    """One baseline per feature branch, so two features never share one."""
    if branch.startswith("origin/"):
        branch = branch[len("origin/"):]
    name = re.sub(r"[^A-Za-z0-9._-]", "_", branch)
    return os.path.join(state_dir("baseline"), f"{name}.json")


def cmd_baseline(a):
    r = root()
    rc, branch = git("rev-parse --abbrev-ref HEAD")
    if rc != 0 or branch == "HEAD":
        die("baseline runs on the feature branch, not a detached HEAD")
    if a.test_file_cmd and "{test}" not in a.test_file_cmd:
        die("--test-file-cmd must contain {test}, replaced by the file to run")
    _, head = git("rev-parse HEAD")
    if a.test_cmd == "none":
        data = {"cmd": None, "rc": None, "head": head, "created": now()}
        print("baseline: no test suite")
    else:
        print(f"running {a.test_cmd} ...")
        rc, out = sh(a.test_cmd, cwd=r, timeout=3600)
        data = {"cmd": a.test_cmd, "rc": rc, "head": head, "created": now(),
                "tail": tail(out, 4000)}
        print(f"baseline: suite {'green' if rc == 0 else 'red'} at {head[:12]}")
    data["file_cmd"] = a.test_file_cmd
    data["branch"] = branch
    write_json(baseline_path(branch), data)
    print(f"baseline for {branch}")


def pr_section(pr, title):
    rc, body = sh(f"gh pr view {pr} --json body --jq .body", timeout=60)
    if rc != 0:
        die(f"cannot read PR #{pr}: {body.strip()}")
    m = re.search(rf"^##\s*{title}\s*$(.*?)(^##\s|\Z)", body,
                  re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


def check_suite(a, base_info, r, fails, notes):
    if base_info["cmd"] is None:
        notes.append("suite · none in this repo")
        return
    rc, out = sh(base_info["cmd"], cwd=r, timeout=3600)
    logs = [save_log(a.pr, 1, out)] if rc != 0 else []
    if rc == 0:
        notes.append("suite · green")
    elif base_info["rc"] == 0:
        # Red once may be a flaky test: run it again before judging.
        reds = [out]
        for i in range(2, SUITE_RUNS + 1):
            rc_i, out_i = sh(base_info["cmd"], cwd=r, timeout=3600)
            logs.append(save_log(a.pr, i, out_i))
            if rc_i != 0:
                reds.append(out_i)
        runs = f"red {len(reds)} of {SUITE_RUNS} runs"
        if len(reds) == SUITE_RUNS:
            fails.append(f"suite · {runs}, was green at the feature's start\n"
                         + tail(out, 2500))
        else:
            fails.append(f"suite · intermittent · {runs}, was green at the "
                         "feature's start\n" + tail(reds[0], 2500))
        notes.append("suite logs · " + " · ".join(logs))
    else:
        notes.append("suite · red, was already red at the feature's start: "
                      "not comparable, record it on the map · log " + logs[0])


def check_listed(a, status, diff, listed, fails, notes):
    """Existing tests changed, and skips or suppressions added: each listed."""
    flagged = []
    for code, path in status:
        if code in ("M", "D") and TEST_PATH.search(path):
            flagged.append((path, f"test changed · {code} {path}"))

    # Per file and kind, added minus removed: a line that only moves nets zero.
    counts, current, in_hunk = {}, None, False
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            in_hunk = False
            continue
        if not in_hunk:
            if line.startswith("+++ "):
                current = line[6:] if line.startswith("+++ b/") else None
            in_hunk = line.startswith("@@")
            continue
        if line.startswith("@@") or line[:1] not in ("+", "-") or current is None:
            continue
        sign = 1 if line[0] == "+" else -1
        for kind, pat in LOOSENERS:
            if pat.search(line[1:]):
                counts[(current, kind)] = counts.get((current, kind), 0) + sign
    for (path, kind), n in sorted(counts.items()):
        if n > 0:
            flagged.append((path, f"loosened · {kind} · {path} · {n} added"))

    if not flagged:
        notes.append("tests changed · none")
        return
    for path, line in flagged:
        if a.pr and path in listed:
            notes.append(f"{line} · listed in the PR")
        else:
            fails.append(f"{line} · not listed in the PR's Tests changed section")


def check_credentials(a, r, diff, fails, notes):
    current, found = None, False
    for line in diff.splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else None
            continue
        if not line.startswith("+") or current is None:
            continue
        for name, pat in SECRETS:
            if re.search(pat, line):
                fails.append(f"credential · {name} · {current}")
                found = True
        if SUSPECT.search(line):
            notes.append(f"credential? · literal assigned to a secret-like "
                         f"name · {current} · look before merging")
    if a.secrets_cmd:
        rc, out = sh(a.secrets_cmd, cwd=r, timeout=600)
        if rc != 0:
            fails.append("credential · secrets scanner failed\n" + tail(out, 1500))
            found = True
    if not found:
        notes.append("credentials · none found")


def pinned_files(section, r):
    """The tracked files the Pinned by section names, or a none reason."""
    text = section.strip()
    m = re.match(r"^[-*\s]*none\b\s*[·:\-]*\s*(.*)", text, re.IGNORECASE)
    if m:
        return [], (m.group(1).splitlines()[0].strip() or "no reason given")
    _, tracked = run_git(["ls-files"], r)
    known = set(tracked.splitlines())
    found = []
    for tok in re.findall(r"`([^`]+)`|([^\s`·,()]+)", text):
        path = (tok[0] or tok[1]).strip().replace("\\", "/")
        if path in known and path not in found:
            found.append(path)
    return found, None


def run_pinned(cmd, path, r):
    return sh(cmd.replace("{test}", path), cwd=r, timeout=1800)


def check_pinned(a, base_info, r, base, status, listed, fails, notes):
    code_changed = [p for c, p in status
                    if not TEST_PATH.search(p) and not DOC_PATH.search(p)]
    if not code_changed:
        notes.append("pinned · nothing to pin: the step changes only tests or docs")
        return
    if base_info["cmd"] is None:
        notes.append("pinned · not run · no test suite in this repo")
        return
    if not base_info.get("file_cmd"):
        notes.append("pinned · not run · no command that runs one test file: "
                      "record it with baseline --test-file-cmd")
        return
    files, reason = pinned_files(listed, r)
    if reason is not None:
        notes.append(f"unpinned? · none · {reason} · look before merging")
        return
    if not files:
        fails.append("pinned · nothing pins this step: list in the PR's Pinned by "
                     "section a test file that fails without it, or "
                     "`none · <why>`")
        return

    cmd = base_info["file_cmd"]
    at_head = {}
    for path in files:
        rc, out = run_pinned(cmd, path, r)
        if rc != 0 or setup_failure(out):
            fails.append(f"pinned · {path} · fails at HEAD\n" + tail(out, 1200))
        else:
            at_head[path] = out
    if not at_head:
        return

    # Revert the step's non-test changes in place, keeping its tests and the
    # installed dependencies, then restore HEAD whatever happens.
    keep = set(files)
    revert = [p for c, p in status if c in ("M", "D")
              and not TEST_PATH.search(p) and p not in keep]
    added = [p for c, p in status if c == "A"
             and not TEST_PATH.search(p) and p not in keep]
    try:
        for i in range(0, len(revert), 100):
            rc, out = run_git(["checkout", base, "--", *revert[i:i + 100]], r)
            if rc != 0:
                die(f"cannot revert the step's changes for the pinned check: {out}")
        for p in added:
            full = os.path.join(r, p)
            if os.path.exists(full):
                os.remove(full)
        for path in at_head:
            rc, out = run_pinned(cmd, path, r)
            if rc == 0:
                fails.append(f"pinned · {path} · passes without this step: it pins "
                             "nothing this step changed")
            elif reached_assertion(out) or not setup_failure(out):
                notes.append(f"pinned · {path} · fails without the step")
            else:
                notes.append(f"pinned · {path} · fails without the step before any "
                             "assertion: new code")
    finally:
        rc, out = run_git(["reset", "-q", "--hard", "HEAD"], r)
        if rc != 0:
            die(f"cannot restore HEAD after the pinned check: {out}")


def cmd_check(a):
    r = root()
    base_info = read_json(baseline_path(a.base))
    if base_info is None:
        die(f"no baseline for {a.base}. On that branch, run: "
            "step_check.py baseline --test-cmd <cmd>")
    if tracked_changes(r):
        die("tracked files changed in the checkout: commit or remove them first")

    rc, base = git(f"merge-base HEAD {a.base}")
    if rc != 0:
        die(f"cannot resolve merge-base with {a.base}")

    _, raw = run_git(["diff", "--name-status", "--no-renames", base, "HEAD"], r)
    status = [(ln.split("\t")[0][:1], ln.split("\t")[1].replace("\\", "/"))
              for ln in raw.splitlines() if "\t" in ln]
    _, diff = run_git(["diff", "-U0", "--no-renames", base, "HEAD"], r)
    tests_listed = pr_section(a.pr, "Tests changed") if a.pr else ""
    pinned_listed = pr_section(a.pr, "Pinned by") if a.pr else ""

    fails, notes = [], []
    check_suite(a, base_info, r, fails, notes)
    check_listed(a, status, diff, tests_listed, fails, notes)
    check_credentials(a, r, diff, fails, notes)
    check_pinned(a, base_info, r, base, status, pinned_listed, fails, notes)

    for n in notes:
        print(f"- {n}")
    for f in fails:
        print(f"- FAIL {f}")
    print(f"\nSTEP CHECK: {'FAIL' if fails else 'PASS'}")
    sys.exit(1 if fails else 0)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("baseline")
    p.add_argument("--test-cmd", required=True,
                   help="the command that runs the whole suite, or 'none'")
    p.add_argument("--test-file-cmd",
                   help="the command that runs one test file, with {test} for its path")
    p.set_defaults(fn=cmd_baseline)
    p = sub.add_parser("check")
    p.add_argument("--base", required=True, help="the feature branch")
    p.add_argument("--pr", help="step PR number, to read its Tests changed and "
                   "Pinned by sections")
    p.add_argument("--secrets-cmd", help="optional scanner; non-zero exit fails")
    p.set_defaults(fn=cmd_check)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
