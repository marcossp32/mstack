#!/usr/bin/env python3
"""The gate. The only route to confirmed, fixed and still-failing.

  gate.py confirm --id F-001 --capture <path> --repro <path> --cmd "<cmd with {test}>"
  gate.py recheck --id F-001 [--promote]

confirm, all mandatory:
  1. The capture (the repro before its assertion was inverted) passes at HEAD
     on every run: the writer's model of the code is right, and the file
     imports and sets up cleanly.
  2. The repro fails at HEAD on every run, and not before an assertion.
  3. At the base, the repro passes (regression), or the code it exercises does
     not exist there (new code). Failing on code that existed: dead.
Both files are new, frozen by hash before the first run, and removed from the
checkout afterwards, aborts included. The frozen copies live in the git dir, out of the
builder's way.

recheck: the frozen repro, restored at its path, passes on every run at the
current HEAD, and the suite is no worse than when the review started.
"""
import argparse
import os
import re
import shutil
import sys
import tempfile

from common import (SETUP_FAILURE, die, git, now, reached_assertion, root, sh,
                    setup_failure, sha, tail, tracked_changes)
from ledger import find, load, run_dir, save

RUNS = 5
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")


def frozen_dir(fid):
    d = os.path.join(run_dir(), "repro", fid)
    os.makedirs(d, exist_ok=True)
    return d


def runs(cmd, rel, cwd, n, watch):
    """Run the test n times; abort if any watched file changes."""
    out = []
    for i in range(n):
        rc, text = sh(cmd.replace("{test}", rel), cwd=cwd)
        for path, digest in watch:
            if not os.path.exists(path) or sha(path) != digest:
                die(f"{path} changed during the gate", 3)
        out.append({"run": i + 1, "rc": rc, "tail": tail(text), "full": text})
    return out


def strip(results):
    return [{k: v for k, v in x.items() if k != "full"} for x in results]


def new_symbols(output, base, r):
    """Names in a setup failure that this diff added and the base lacks."""
    names = set()
    for line in output.splitlines():
        if any(m in line.lower() for m in SETUP_FAILURE):
            names.update(IDENT.findall(line))
    if not names:
        return []
    _, diff = git(f"diff -U0 {base} HEAD", cwd=r)
    added = "\n".join(l[1:] for l in diff.splitlines()
                      if l.startswith("+") and not l.startswith("+++"))
    found = []
    for name in sorted(names):
        if not re.search(rf"\b{re.escape(name)}\b", added):
            continue
        rc, _ = git(f"grep -q -w -e {name} {base} --", cwd=r)
        if rc == 1:
            found.append(name)
    return found


def close(data, f, state, reason, evidence, cleanup):
    for p in cleanup:
        if os.path.exists(p):
            os.remove(p)
    f.update({"state": state, "reason": reason, "evidence": evidence,
              "closed": now()})
    save(data)
    print(f"{f['id']} -> {state}: {reason.splitlines()[0]}")
    sys.exit(0)


def base_run(data, f, rel, repro_abs, cmd, r):
    """Returns (kind, note) or (None, reason-for-death-or-unjudgeable)."""
    base = data["base"]
    rc, _ = git(f"cat-file -e {base}:{f['file']}", cwd=r)
    if rc != 0:
        return "new-code", "file absent from the base", None

    wt = tempfile.mkdtemp(prefix="mstack-base-")
    try:
        rc, out = git(f"worktree add --detach {wt} {base}", cwd=r)
        if rc != 0:
            die(f"cannot create the base worktree: {out}")
        if data.get("setup_cmd"):
            rc, out = sh(data["setup_cmd"], cwd=wt, timeout=3600,
                         env={"MSTACK_ROOT": r})
            if rc != 0:
                return None, "base not run: setup failed\n" + tail(out), "unjudgeable"
        dst = os.path.join(wt, rel)
        os.makedirs(os.path.dirname(dst) or wt, exist_ok=True)
        shutil.copy2(repro_abs, dst)
        rc, out = sh(cmd.replace("{test}", rel), cwd=wt)
        if rc == 0:
            return "regression", "passes at the base, fails at HEAD", None
        added = new_symbols(out, base, r) if setup_failure(out) else []
        if added:
            return "new-code", f"symbol absent from the base: {', '.join(added)}", None
        if reached_assertion(out) or not setup_failure(out):
            return None, ("fails at the base too, on code that existed there: "
                          "pre-existing bug or invalid repro\n" + tail(out)), "dead"
        return None, ("base failed before any assertion, for a reason this "
                      "diff does not explain\n" + tail(out)), "unjudgeable"
    finally:
        git(f"worktree remove --force {wt}", cwd=r)
        shutil.rmtree(wt, ignore_errors=True)


def cmd_confirm(a):
    if "{test}" not in a.cmd:
        die("--cmd must contain {test}, replaced by the file to run")
    r = root()
    data = load()
    f = find(data, a.id)
    if f["state"] != "proposed":
        die(f"{a.id} is {f['state']}, not proposed", 2)
    _, head = git("rev-parse HEAD", cwd=r)
    if head != data["head"]:
        die("HEAD moved since prepare.py. Prepare again")
    if tracked_changes(r):
        die("tracked files changed: a repro writer may only add new files")

    files = {}
    for role, rel in (("capture", a.capture), ("repro", a.repro)):
        rel = rel.replace("\\", "/")
        full = os.path.join(r, rel)
        if not os.path.exists(full):
            die(f"{role} not found: {rel}")
        if git(f"ls-files --error-unmatch -- {rel}", cwd=r)[0] == 0:
            die(f"{role} is a tracked file; it must be new: {rel}")
        frozen = os.path.join(frozen_dir(a.id), os.path.basename(rel) + f".{role}")
        shutil.copy2(full, frozen)
        files[role] = {"path": rel, "abs": full, "frozen": frozen,
                       "sha256": sha(full)}
    cap, rep = files["capture"], files["repro"]
    cleanup = [cap["abs"], rep["abs"]]
    watch = [(cap["abs"], cap["sha256"]), (rep["abs"], rep["sha256"])]
    evidence = {"cmd": a.cmd,
                "capture": {k: cap[k] for k in ("path", "frozen", "sha256")},
                "repro": {k: rep[k] for k in ("path", "frozen", "sha256")}}
    try:
        judge(a, data, f, r, cap, rep, watch, evidence, cleanup)
    finally:
        # An abort must not leave either file behind: a failing leftover
        # turns later suite runs red.
        for p in cleanup:
            if os.path.exists(p):
                os.remove(p)


def judge(a, data, f, r, cap, rep, watch, evidence, cleanup):
    # 1. capture passes at HEAD, every run
    res = runs(a.cmd, cap["path"], r, a.runs, watch)
    evidence["capture_runs"] = strip(res)
    if any(x["rc"] != 0 for x in res):
        close(data, f, "dead", "the capture fails at HEAD: the writer's model "
              "of the code is wrong, or the file does not set up", evidence, cleanup)

    # 2. repro fails at HEAD, every run, after reaching an assertion
    res = runs(a.cmd, rep["path"], r, a.runs, watch)
    evidence["repro_runs"] = strip(res)
    if any(x["rc"] == 0 for x in res):
        close(data, f, "dead", "the repro passes at HEAD: the claim is false",
              evidence, cleanup)
    if len({x["rc"] for x in res}) > 1:
        close(data, f, "dead", "inconsistent exit codes across runs: flaky",
              evidence, cleanup)
    if any(setup_failure(x["full"]) for x in res):
        close(data, f, "dead", "the repro fails before any assertion",
              evidence, cleanup)

    # 3. the base
    kind, note, verdict = base_run(data, f, rep["path"], rep["abs"], a.cmd, r)
    if kind is None:
        close(data, f, verdict, note, evidence, cleanup)
    evidence.update({"kind": kind, "base_note": note})
    close(data, f, "confirmed", f"{kind}: {note}", evidence, cleanup)


def cmd_recheck(a):
    r = root()
    data = load()
    f = find(data, a.id)
    if f["state"] not in ("confirmed", "still-failing"):
        die(f"{a.id} is {f['state']}; only confirmed or still-failing can be rechecked")
    ev = f["evidence"]
    rep = ev["repro"]
    full = os.path.join(r, rep["path"])
    if os.path.exists(full):
        die(f"{rep['path']} exists in the checkout. The repro is restored by the "
            "gate only; remove that file")
    if sha(rep["frozen"]) != rep["sha256"]:
        die("the frozen repro changed on disk", 3)
    os.makedirs(os.path.dirname(full) or r, exist_ok=True)
    shutil.copy2(rep["frozen"], full)

    _, head = git("rev-parse HEAD", cwd=r)
    res = runs(ev["cmd"], rep["path"], r, a.runs, [(full, rep["sha256"])])
    fixed = all(x["rc"] == 0 for x in res)
    keep = fixed and a.promote
    if not keep:
        # A still-failing repro must not count as collateral damage.
        os.remove(full)
    rc_suite, out_suite = sh(data["test_cmd"], cwd=r, timeout=3600)
    worse = data["baseline"]["rc"] == 0 and rc_suite != 0

    f.setdefault("rechecks", []).append({
        "at": now(), "head": head, "runs": strip(res),
        "suite_rc": rc_suite, "suite_tail": tail(out_suite)})
    f["state"] = "fixed" if fixed else "still-failing"
    save(data)

    if keep:
        print(f"{a.id} -> fixed. Repro left at {rep['path']}: commit it as a "
              "regression test")
    else:
        print(f"{a.id} -> {f['state']}")
    if worse:
        print("SUITE WORSE: green when the review started, red now\n"
              + tail(out_suite, 2000))
    sys.exit(0 if fixed and not worse else 1)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("confirm")
    p.add_argument("--id", required=True)
    p.add_argument("--capture", required=True,
                   help="repo-relative new file: the test before inversion")
    p.add_argument("--repro", required=True,
                   help="repo-relative new file: the test after inversion")
    p.add_argument("--cmd", required=True,
                   help="runs one test file; {test} is replaced by its path")
    p.add_argument("--runs", type=int, default=RUNS)
    p.set_defaults(fn=cmd_confirm)
    p = sub.add_parser("recheck")
    p.add_argument("--id", required=True)
    p.add_argument("--promote", action="store_true",
                   help="leave a passing repro in the checkout to be committed")
    p.add_argument("--runs", type=int, default=RUNS)
    p.set_defaults(fn=cmd_recheck)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
