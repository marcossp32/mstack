#!/usr/bin/env python3
"""The gate. The only route to confirmed, fixed, still-failing and stale.

  gate.py confirm --id F-001 --capture <path> --repro <path> --cmd "<cmd with {test}>"
  gate.py recheck --id F-001 [--id F-002 ...] [--promote]
  gate.py recheck --id F-001 --capture <path> --repro <path> --cmd "<cmd>" [--promote]   stale only

--cmd runs in a shell: cmd.exe on Windows, sh elsewhere.

The capture is the repro before its assertion was inverted: the two differ only
there. So when the capture passes, the repro reaches its assertion, and which
of the two passes says which behaviour the code has. No verdict reads the
runner's output.

confirm, all mandatory:
  1. The capture passes at HEAD on every run: the writer's model of the code is
     right, and the file sets up cleanly.
  2. The repro fails at HEAD on every run, with one exit code.
  3. At the base, in the review's base worktree: the repro passes (regression);
     or it fails and so does the capture, so the broken behaviour is new
     (new-behaviour). The capture passing there too: the bug was already there
     (dead, pre-existing). Both failing while the base suite was red at
     prepare: unjudgeable, since the checkout may be what fails.
Both files are new, frozen by hash before the first run and recorded in the
ledger, and removed from the checkout and the base worktree afterwards. A kill
skips that: the next confirm or prepare removes what the ledger recorded.

recheck: the frozen repro, restored at its path, at the current HEAD, every
run. It passes: fixed. Else the frozen capture runs: it passes on a run, the
broken behaviour is still there: still-failing. Neither passes: stale, the code
they set up against changed and they say nothing about the claim. Several --id
run one after another, then the suite once for all of them, which must be no
worse than when the review started. An exact untracked copy of a frozen file,
left by an interrupted recheck, is removed. A stale finding is rechecked with
a capture and repro rewritten against the current code: the repro passes and
the capture fails on every run, fixed; the reverse, still-failing; else stale.

Every run has a ceiling, 3 times the review's suite run or more. A run that
reaches it judges nothing: confirm closes the finding unjudgeable, recheck
prints NOT RUN, exits 2 and leaves every state as it was.
"""
import argparse
import os
import shutil
import sys

from common import (FILE_FLOOR, SUITE_FLOOR, ceiling, die, git, now, root, sh,
                    sha, tail, timed_out, tracked_changes)
from ledger import (find, load, remove_bases, run_dir, run_git, save,
                    sweep_leftovers, tracked)

RUNS = 5


def frozen_dir(fid):
    d = os.path.join(run_dir(), "repro", fid)
    os.makedirs(d, exist_ok=True)
    return d


def file_limit(data):
    """A ceiling for one test file: 3 times the review's suite run or more."""
    return ceiling(data["baseline"].get("seconds"), FILE_FLOOR)


def cut(results):
    """The ceiling a run hit, or None: such a run judges nothing."""
    return next((x["limit"] for x in results if x.get("timed_out")), None)


def runs(cmd, rel, cwd, n, watch, limit):
    """Run the test n times; abort if any watched file changes. A run that
    hits its ceiling stops the series: nothing is judged on it."""
    out = []
    for i in range(n):
        rc, text = sh(cmd.replace("{test}", rel), cwd=cwd, timeout=limit)
        if timed_out(rc, text):
            out.append({"run": i + 1, "rc": rc, "tail": tail(text),
                        "timed_out": True, "limit": limit})
            break
        for path, digest in watch:
            if not os.path.exists(path) or sha(path) != digest:
                die(f"{path} changed during the gate", 3)
        out.append({"run": i + 1, "rc": rc, "tail": tail(text)})
    return out


def passes(res):
    return all(x["rc"] == 0 for x in res)


def fails(res):
    return all(x["rc"] != 0 for x in res)


def close(data, f, state, reason, evidence, cleanup):
    for p in cleanup:
        if os.path.exists(p):
            os.remove(p)
    f.update({"state": state, "reason": reason, "evidence": evidence,
              "closed": now()})
    save(data)
    print(f"{f['id']} -> {state}: {reason.splitlines()[0]}")
    sys.exit(0)


def clean_base(data, wt):
    """Puts back every recorded reproduction path in the base worktree: the
    frozen file a killed gate left there is removed, a base file it covered
    restored."""
    for f in data["findings"]:
        for g in f.get("gate_files", []):
            full = os.path.join(wt, g["path"])
            if os.path.isfile(full) and sha(full) == g["sha256"]:
                if tracked(g["path"], wt):
                    run_git(["checkout", "--", g["path"]], wt)
                else:
                    os.remove(full)


def at_base(wt, rel, frozen, cmd, limit):
    """Runs one frozen file once in the base worktree, then takes it out again."""
    dst = os.path.join(wt, rel)
    made = []
    d = os.path.dirname(dst)
    while d and not os.path.isdir(d):
        made.append(d)
        d = os.path.dirname(d)
    os.makedirs(os.path.dirname(dst) or wt, exist_ok=True)
    shutil.copy2(frozen, dst)
    try:
        rc, out = sh(cmd.replace("{test}", rel), cwd=wt, timeout=limit)
    finally:
        if tracked(rel, wt):
            run_git(["checkout", "--", rel], wt)
        elif os.path.exists(dst):
            os.remove(dst)
        for d in made:
            if os.path.isdir(d) and not os.listdir(d):
                os.rmdir(d)
    return {"rc": rc, "tail": tail(out), "timed_out": timed_out(rc, out)}


def base_run(data, cap, rep, cmd, evidence):
    """Returns (state, reason): confirmed with its kind, dead or unjudgeable."""
    wt, limit = data["base_worktree"], file_limit(data)
    evidence["base_runs"] = {}
    for role, files in (("repro", rep), ("capture", cap)):
        res = at_base(wt, files["path"], files["frozen"], cmd, limit)
        evidence["base_runs"][role] = res
        if res["timed_out"]:
            return "unjudgeable", (f"base not run: the {role} did not finish within "
                                   f"{limit}s at the base")
        if role == "repro" and res["rc"] == 0:
            return "confirmed", "regression: the repro passes at the base, fails at HEAD"
    if evidence["base_runs"]["capture"]["rc"] == 0:
        return "dead", ("pre-existing: the capture passes at the base too, so the "
                        "broken behaviour was already there\n"
                        + evidence["base_runs"]["capture"]["tail"])
    if data.get("base_suite_rc"):
        return "unjudgeable", ("the repro and the capture both fail at the base, and "
                               "the suite was red in the base worktree at prepare: "
                               "the checkout may be what fails")
    return "confirmed", ("new-behaviour: the repro and the capture both fail at the "
                         "base, so the broken behaviour is new")


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
    wt = data.get("base_worktree")
    if not wt or not os.path.isdir(wt):
        die("the review's base worktree is gone (report.py removes it). Prepare again")
    paths = [rel.replace("\\", "/") for rel in (a.capture, a.repro)]
    # What a killed gate left: files of other runs, in the checkout and the base.
    sweep_leftovers(data, r, skip=paths)
    clean_base(data, wt)
    remove_bases(r, keep=wt)
    if tracked_changes(r):
        die("tracked files changed: a repro writer may only add new files")

    files = {}
    for role, rel in zip(("capture", "repro"), paths):
        full = os.path.join(r, rel)
        if not os.path.isfile(full):
            die(f"{role} not found: {rel}")
        if tracked(rel, r):
            die(f"{role} is a tracked file; it must be new: {rel}")
        frozen = os.path.join(frozen_dir(a.id), os.path.basename(rel) + f".{role}")
        shutil.copy2(full, frozen)
        files[role] = {"path": rel, "abs": full, "frozen": frozen,
                       "sha256": sha(full)}
    cap, rep = files["capture"], files["repro"]
    if cap["sha256"] == rep["sha256"]:
        die("the capture and the repro are the same file; the repro inverts the "
            "capture's assertion")
    # Recorded before the first run, so a kill leaves nothing the next run
    # cannot find.
    f["gate_files"] = [{"path": x["path"], "sha256": x["sha256"]} for x in (cap, rep)]
    save(data)
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
    limit = file_limit(data)

    # 1. capture passes at HEAD, every run
    res = runs(a.cmd, cap["path"], r, a.runs, watch, limit)
    evidence["capture_runs"] = res
    if cut(res):
        close(data, f, "unjudgeable", f"the capture did not finish within "
              f"{cut(res)}s at HEAD", evidence, cleanup)
    if not passes(res):
        close(data, f, "dead", "the capture fails at HEAD: the writer's model "
              "of the code is wrong, or the file does not set up", evidence, cleanup)

    # 2. repro fails at HEAD, every run. The capture passing proves it gets
    # as far as its assertion.
    res = runs(a.cmd, rep["path"], r, a.runs, watch, limit)
    evidence["repro_runs"] = res
    if cut(res):
        close(data, f, "unjudgeable", f"the repro did not finish within "
              f"{cut(res)}s at HEAD: a hang is not an assertion", evidence, cleanup)
    if any(x["rc"] == 0 for x in res):
        close(data, f, "dead", "the repro passes at HEAD: the claim is false",
              evidence, cleanup)
    if len({x["rc"] for x in res}) > 1:
        close(data, f, "dead", "inconsistent exit codes across runs: flaky",
              evidence, cleanup)

    # 3. the base
    state, reason = base_run(data, cap, rep, a.cmd, evidence)
    if state == "confirmed":
        kind, note = reason.split(": ", 1)
        evidence.update({"kind": kind, "base_note": note})
    close(data, f, state, reason, evidence, cleanup)


def restore(a, r, files):
    """Puts a frozen file back at its path in the checkout."""
    full = os.path.join(r, files["path"])
    if sha(files["frozen"]) != files["sha256"]:
        die(f"the frozen {files['path']} changed on disk", 3)
    if os.path.exists(full):
        if tracked(files["path"], r) or sha(full) != files["sha256"]:
            die(f"{files['path']} exists in the checkout. The gate restores it; "
                "remove that file")
        # An exact untracked copy is what an interrupted recheck left behind.
        os.remove(full)
        print(f"{a.id}: removed {files['path']}, a copy an interrupted recheck left")
    os.makedirs(os.path.dirname(full) or r, exist_ok=True)
    shutil.copy2(files["frozen"], full)
    return full


def recheck_frozen(a, f, r, limit):
    """The repro and capture the gate froze at confirm, restored at their paths."""
    ev = f["evidence"]
    rep, cap = ev["repro"], ev["capture"]
    restored = []
    keep = False
    cap_res = []
    try:
        rep_full = restore(a, r, rep)
        restored.append(rep)
        cap_full = restore(a, r, cap)
        restored.append(cap)
        watch = [(rep_full, rep["sha256"]), (cap_full, cap["sha256"])]
        rep_res = runs(ev["cmd"], rep["path"], r, a.runs, watch, limit)
        if not cut(rep_res) and not passes(rep_res):
            cap_res = runs(ev["cmd"], cap["path"], r, a.runs, watch, limit)
        if cut(rep_res + cap_res):
            die(f"NOT RUN · a frozen file did not finish within {limit}s: "
                f"{a.id} keeps its state", 2)
        if passes(rep_res):
            state = "fixed"
        elif any(x["rc"] == 0 for x in cap_res):
            state = "still-failing"
        else:
            state = "stale"
        keep = state == "fixed" and a.promote
    finally:
        # A still-failing repro must not count as collateral damage.
        for files in restored:
            full = os.path.join(r, files["path"])
            if (os.path.exists(full) and not tracked(files["path"], r)
                    and not (keep and files is rep)):
                os.remove(full)
    return state, {"repro": rep_res, "capture": cap_res}, rep["path"]


def recheck_rewritten(a, f, r, limit):
    """A stale finding, rewritten against this code by a fresh writer.

    The capture asserts the broken behaviour, the repro the correct one. They
    must disagree on every run: the repro passing and the capture failing is
    fixed, the reverse is still-failing.
    """
    paths = {role: rel.replace("\\", "/")
             for role, rel in (("capture", a.capture), ("repro", a.repro))}
    # Each rewrite is frozen under its own name, so it never overwrites the
    # copies an earlier confirm or recheck froze.
    suffix = f"r{len(f.get('rechecks', [])) + 1}"
    keep = False
    try:
        files = {}
        for role, rel in paths.items():
            full = os.path.join(r, rel)
            if not os.path.isfile(full):
                die(f"{role} not found: {rel}")
            if tracked(rel, r):
                die(f"{role} is a tracked file; it must be new: {rel}")
            frozen = os.path.join(frozen_dir(a.id),
                                  os.path.basename(rel) + f".{role}.{suffix}")
            shutil.copy2(full, frozen)
            files[role] = {"path": rel, "abs": full, "frozen": frozen,
                           "sha256": sha(full)}
        cap, rep = files["capture"], files["repro"]
        watch = [(cap["abs"], cap["sha256"]), (rep["abs"], rep["sha256"])]

        cap_res = runs(a.cmd, cap["path"], r, a.runs, watch, limit)
        rep_res = runs(a.cmd, rep["path"], r, a.runs, watch, limit)
        if cut(cap_res + rep_res):
            die(f"NOT RUN · the rewritten repro did not finish within {limit}s: "
                f"{a.id} stays stale", 2)
        if passes(rep_res) and fails(cap_res):
            state = "fixed"
        elif fails(rep_res) and passes(cap_res):
            state = "still-failing"
        else:
            state = "stale"
        if state in ("fixed", "still-failing"):
            # The rewritten pair is the finding's repro from now on.
            f["evidence"].update({
                "cmd": a.cmd,
                "capture": {k: cap[k] for k in ("path", "frozen", "sha256")},
                "repro": {k: rep[k] for k in ("path", "frozen", "sha256")}})
        keep = state == "fixed" and a.promote
    finally:
        # Every outcome, aborts included: a leftover failing file turns
        # later suite runs red. Tracked files were refused above, never removed.
        for rel in paths.values():
            path = os.path.join(r, rel)
            if (os.path.exists(path) and not tracked(rel, r)
                    and not (keep and rel == paths["repro"])):
                os.remove(path)
    return state, {"capture": cap_res, "repro": rep_res}, rep["path"]


def cmd_recheck(a):
    r = root()
    data = load()
    ids = list(dict.fromkeys(a.id))
    findings = [find(data, i) for i in ids]
    rewritten = bool(a.capture or a.repro)
    if rewritten:
        if len(ids) > 1:
            die("a rewritten recheck takes one --id")
        f = findings[0]
        if not (a.capture and a.repro and a.cmd):
            die("a rewritten recheck needs --capture, --repro and --cmd")
        if "{test}" not in a.cmd:
            die("--cmd must contain {test}, replaced by the file to run")
        if f["state"] != "stale":
            die(f"{f['id']} is {f['state']}; only a stale finding takes a rewritten repro")
        if tracked_changes(r):
            die("tracked files changed: a repro writer may only add new files")
    for f in findings if not rewritten else []:
        if f["state"] == "stale":
            die(f"{f['id']} is stale: recheck it with a rewritten --capture, --repro "
                "and --cmd")
        if f["state"] not in ("confirmed", "still-failing"):
            die(f"{f['id']} is {f['state']}; only confirmed or still-failing can be "
                "rechecked")

    _, head = git("rev-parse HEAD", cwd=r)
    limit = file_limit(data)
    results = []
    for f in findings:
        a.id = f["id"]
        if rewritten:
            results.append((f, *recheck_rewritten(a, f, r, limit)))
        else:
            results.append((f, *recheck_frozen(a, f, r, limit)))
    # One suite run judges every finding rechecked here: it is the slow part.
    limit = ceiling(data["baseline"].get("seconds"), SUITE_FLOOR)
    rc_suite, out_suite = sh(data["test_cmd"], cwd=r, timeout=limit)
    if timed_out(rc_suite, out_suite):
        # Judges nothing: no state changes, and no promoted repro stays behind.
        for f, state, _, path in results:
            full = os.path.join(r, path)
            if state == "fixed" and a.promote and os.path.exists(full) \
                    and not tracked(path, r):
                os.remove(full)
        die(f"RECHECK NOT RUN · the suite did not finish within {limit}s. Nothing "
            "judged, states unchanged: " + ", ".join(f["id"] for f in findings), 2)
    worse = data["baseline"]["rc"] == 0 and rc_suite != 0

    for f, state, res, _ in results:
        f.setdefault("rechecks", []).append({
            "at": now(), "head": head, "rewritten": rewritten, "runs": res,
            "suite_rc": rc_suite, "suite_tail": tail(out_suite)})
        f["state"] = state
    save(data)

    for f, state, _, path in results:
        if state == "fixed" and a.promote:
            print(f"{f['id']} -> fixed. Repro left at {path}: commit it as a "
                  "regression test")
        elif state == "stale":
            print(f"{f['id']} -> stale: neither the repro nor the capture passes on "
                  "this code, so it cannot tell whether the claim still holds. A "
                  "fresh repro writer gets the claim and condition; recheck its "
                  "files with --capture, --repro and --cmd")
        else:
            print(f"{f['id']} -> {state}")
    if worse:
        print("SUITE WORSE: green when the review started, red now\n"
              + tail(out_suite, 2000))
    fixed = all(state == "fixed" for _, state, _, _ in results)
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
    p.add_argument("--id", required=True, action="append",
                   help="repeat for each finding: one suite run judges them all")
    p.add_argument("--promote", action="store_true",
                   help="leave a passing repro in the checkout to be committed")
    p.add_argument("--capture", help="stale only: rewritten capture, a new file")
    p.add_argument("--repro", help="stale only: rewritten repro, a new file")
    p.add_argument("--cmd", help="stale only: runs one test file; {test} is its path")
    p.add_argument("--runs", type=int, default=RUNS)
    p.set_defaults(fn=cmd_recheck)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
