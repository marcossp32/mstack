#!/usr/bin/env python3
"""Step check. Deterministic, no model judgement.

  step_check.py baseline --test-cmd "<cmd>" | --test-cmd none
      Once, on the feature branch before the first step. Records the suite's
      state for that branch, so later steps can be compared against it.

  step_check.py check --base origin/<feature branch> [--pr <n>] [--secrets-cmd "<cmd>"]
      Fetch first: a stale local feature branch puts earlier steps in the diff.
      After each build, on the step branch. Exit 0 = PASS, 1 = FAIL.

Checks:
  1. Suite no worse than at the feature's start (exit-code level).
  2. Every existing test file changed or deleted is listed in the PR.
  3. No credentials in the added lines.
"""
import argparse
import os
import re
import sys

from common import (TEST_PATH, die, git, now, read_json, root, sh, state_dir,
                    tail, write_json)

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
    data["branch"] = branch
    write_json(baseline_path(branch), data)
    print(f"baseline for {branch}")


def pr_tests_section(pr):
    rc, body = sh(f"gh pr view {pr} --json body --jq .body", timeout=60)
    if rc != 0:
        die(f"cannot read PR #{pr}: {body.strip()}")
    m = re.search(r"^##\s*Tests changed\s*$(.*?)(^##\s|\Z)", body,
                  re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


def cmd_check(a):
    r = root()
    base_info = read_json(baseline_path(a.base))
    if base_info is None:
        die(f"no baseline for {a.base}. On that branch, run: "
            "step_check.py baseline --test-cmd <cmd>")

    rc, base = git(f"merge-base HEAD {a.base}")
    if rc != 0:
        die(f"cannot resolve merge-base with {a.base}")

    fails, notes = [], []

    # 1. suite
    if base_info["cmd"] is None:
        notes.append("suite · none in this repo")
    else:
        rc, out = sh(base_info["cmd"], cwd=r, timeout=3600)
        if rc == 0:
            notes.append("suite · green")
        elif base_info["rc"] == 0:
            fails.append("suite · red, was green at the feature's start\n"
                         + tail(out, 2500))
        else:
            notes.append("suite · red, was already red at the feature's start: "
                         "not comparable, record it on the map")

    # 2. existing tests changed or deleted
    _, status = git(f"diff --name-status -M {base} HEAD")
    touched = []
    for line in status.splitlines():
        parts = line.split("\t")
        code = parts[0][:1]
        if code in ("M", "D", "R") and TEST_PATH.search(parts[1].replace("\\", "/")):
            touched.append(f"{code} {parts[1]}")
    if touched:
        listed = pr_tests_section(a.pr) if a.pr else ""
        for t in touched:
            path = t.split(" ", 1)[1]
            if a.pr and path in listed:
                notes.append(f"test changed · {t} · listed in the PR")
            else:
                fails.append(f"test changed · {t} · not listed in the PR's "
                             "Tests changed section")
    else:
        notes.append("tests changed · none")

    # 3. credentials
    _, diff = git(f"diff -U0 {base} HEAD")
    current = None
    found = False
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
    p.set_defaults(fn=cmd_baseline)
    p = sub.add_parser("check")
    p.add_argument("--base", required=True, help="the feature branch")
    p.add_argument("--pr", help="step PR number, to read its Tests changed section")
    p.add_argument("--secrets-cmd", help="optional scanner; non-zero exit fails")
    p.set_defaults(fn=cmd_check)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
