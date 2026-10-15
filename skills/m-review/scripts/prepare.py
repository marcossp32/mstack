#!/usr/bin/env python3
"""Step 0 of a feature review. Aborts if anything the gate needs is missing.

  prepare.py --base <the base branch, or the head the last review reported> --test-cmd "<cmd>"
             [--setup-cmd "<cmd>"]

--base       the diff is merge-base(HEAD, base)..HEAD
--test-cmd   runs the whole suite (scan Q6); a linter cannot satisfy the gate.
             Its run is timed: the gate's ceilings are 3 times it or more
--setup-cmd  prepares a fresh checkout of the base (install dependencies,
             copy env files) so a reproduction can run there. Needed when the
             suite does not run on a bare checkout

Both commands run in a shell: cmd.exe on Windows, sh elsewhere.

One base worktree serves every gate run of the review: it is checked out and
set up here, the suite runs in it once to show the setup works, and report.py
removes it.
"""
import argparse
import os
import re
import shutil
import tempfile

from common import (FIRST_RUN, SUITE_FLOOR, ceiling, die, git, now, read_json,
                    root, sh, sweep, tail, timed, timed_out, tracked_changes)
from ledger import (BASE_PREFIX, path, remove_bases, remove_tree, run_dir, run_git,
                    save, sweep_leftovers)

KEEP = 3
# Output of a suite that never ran a test: its runner or a prerequisite is
# missing. Substrings, because exit codes differ by runner; only the shell's
# "command not found" codes are generic. Used on whole-suite runs only, where
# nothing better exists; the gate judges a reproduction by its capture instead.
NOT_RUN = ("no module named", "command not found", "is not recognized as",
           "no tests ran", "no tests found", "no tests collected")
# In the base worktree a missing package is setup's fault, never the code's.
NOT_SET_UP = NOT_RUN + ("cannot find module", "cannot find package")
SHELL_NOT_FOUND = (127, 9009)


def never_ran(rc, out, markers=NOT_RUN):
    if rc == 0:
        return False
    if rc in SHELL_NOT_FOUND:
        return True
    low = out.lower()
    return any(m in low for m in markers)


def changed_files(base, r):
    rc, out = git(f"diff --unified=0 --no-color {base} HEAD", cwd=r)
    if rc != 0:
        die(f"cannot read the diff: {out}")
    if not out:
        die("the diff is empty")
    files, current = {}, None
    for line in out.splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else None
            if current:
                files.setdefault(current, [])
        elif line.startswith("@@") and current:
            try:
                new = line.split("+", 1)[1].split("@@")[0].strip()
                start = int(new.split(",")[0])
                count = int(new.split(",")[1]) if "," in new else 1
            except (IndexError, ValueError):
                continue
            # A pure deletion keeps its cut point: removed guards break things.
            end = start + count - 1 if count > 0 else max(1, start)
            files[current].append(f"{max(1, start)}-{end}")
    return {f: r for f, r in files.items() if r}


def base_worktree(a, r, base, head_secs):
    """Checks out the base once, sets it up and runs the suite there. Returns
    (path, the suite's exit code). Aborts, removing it, when it cannot run:
    otherwise every gate run on it would end unjudgeable, or wrong."""
    wt = tempfile.mkdtemp(prefix=BASE_PREFIX)
    rc, out = run_git(["worktree", "add", "--detach", wt, base], r)
    if rc != 0:
        remove_tree(wt)
        die(f"cannot create the base worktree: {out}")

    def fail(msg, code=1):
        remove_tree(wt)
        run_git(["worktree", "prune"], r)
        die(msg, code)

    if a.setup_cmd:
        print(f"running {a.setup_cmd} in the base worktree ...", flush=True)
        rc, out = sh(a.setup_cmd, cwd=wt, timeout=FIRST_RUN, env={"MSTACK_ROOT": r})
        if timed_out(rc, out):
            fail(f"NOT RUN · --setup-cmd did not finish within {FIRST_RUN}s in "
                 "the base worktree\n" + tail(out, 1500), 2)
        if rc != 0:
            fail(f"--setup-cmd failed in the base worktree (exit {rc}). Fix it and "
                 "prepare again\n" + tail(out, 1500))
    limit = ceiling(head_secs, SUITE_FLOOR)
    print(f"running {a.test_cmd} in the base worktree ...", flush=True)
    rc, out = sh(a.test_cmd, cwd=wt, timeout=limit)
    if timed_out(rc, out):
        fail(f"NOT RUN · the suite did not finish within {limit}s in the base "
             "worktree\n" + tail(out, 1500), 2)
    if never_ran(rc, out, NOT_SET_UP):
        fail("the suite ran no test in the base worktree: "
             + ("--setup-cmd does not install what it needs. Fix it"
                if a.setup_cmd else "it needs a --setup-cmd. Give one")
             + " and prepare again\n" + tail(out, 1500))
    return wt, rc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--test-cmd", required=True)
    ap.add_argument("--setup-cmd")
    a = ap.parse_args()

    r = root()
    if tracked_changes(r):
        die("tracked files have uncommitted changes. Review a committed state")
    rc, base = git(f"merge-base HEAD {a.base}", cwd=r)
    if rc != 0:
        die(f"cannot resolve merge-base with {a.base}")
    _, head = git("rev-parse HEAD", cwd=r)

    files = changed_files(base, r)
    if not files:
        die("the diff touches no lines")

    # What a killed gate or prepare left behind: reproduction files of
    # findings still proposed, and base worktrees.
    old = read_json(path())
    if old:
        sweep_leftovers(old, r)
    remove_bases(r)

    # Keep the previous runs for the record, the last KEEP of them; one
    # active run at a time.
    if os.path.exists(path()):
        parent = os.path.dirname(run_dir())
        old = os.path.join(parent, f"review-{now().replace(':', '')}")
        shutil.move(run_dir(), old)
        print(f"previous run moved to {old}")
        archived = sorted(d for d in os.listdir(parent)
                          if re.fullmatch(r"review-\d{4}-\d\d-\d\dT\d{6}\+0000", d))
        for d in archived[:-KEEP]:
            shutil.rmtree(os.path.join(parent, d))
            print(f"deleted {d}")

    print(sweep())
    print(f"running {a.test_cmd} at {head[:12]} ...", flush=True)
    rc, out, secs = timed(a.test_cmd, cwd=r, timeout=FIRST_RUN)
    if timed_out(rc, out):
        die(f"NOT RUN · the suite did not finish within {FIRST_RUN}s at HEAD: "
            "the review cannot compare against it\n" + tail(out, 1500), 2)
    if never_ran(rc, out):
        die("the suite ran no test at HEAD: its runner or a prerequisite is "
            "missing. Fix --test-cmd, or start what it needs, and prepare again\n"
            + tail(out, 1500))
    if rc != 0:
        print("NOTE: the suite is red at HEAD. Recheck compares against this.")

    wt, base_rc = base_worktree(a, r, base, secs)
    save({
        "created": now(), "root": r, "base": base, "head": head,
        "test_cmd": a.test_cmd, "setup_cmd": a.setup_cmd,
        "baseline": {"rc": rc, "seconds": round(secs, 1), "tail": tail(out, 4000)},
        "base_worktree": wt, "base_suite_rc": base_rc,
        "files": files, "findings": [], "next_id": 1,
    })

    total = 0
    for f, ranges in files.items():
        n = sum(int(x.split("-")[1]) - int(x.split("-")[0]) + 1 for x in ranges)
        total += n
        print(f"  {n:>5}  {f}")
    print(f"\nbase {base[:12]} · head {head[:12]} · {len(files)} files · "
          f"{total} changed lines\nledger {path()}\nbase worktree {wt}")
    if base_rc != 0:
        print("NOTE: the suite is red in the base worktree. If --setup-cmd misses "
              "something, fix it and prepare again; until then a finding whose "
              "capture fails at the base ends unjudgeable, since the checkout may "
              "be what fails.")


if __name__ == "__main__":
    main()
