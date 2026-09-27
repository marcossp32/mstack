#!/usr/bin/env python3
"""Step 0 of a feature review. Aborts if anything the gate needs is missing.

  prepare.py --base <main, or the head the last review reported> --test-cmd "<cmd>"
             [--setup-cmd "<cmd>"]

--base       the diff is merge-base(HEAD, base)..HEAD
--test-cmd   runs the whole suite (scan Q6); a linter cannot satisfy the gate
--setup-cmd  prepares a fresh checkout of the base (install dependencies,
             copy env files) so a reproduction can run there. Needed when the
             suite does not run on a bare checkout
"""
import argparse
import os
import shutil

from common import die, git, now, root, sh, tail, tracked_changes
from ledger import path, run_dir, save


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

    # Keep the previous run for the record; one active run at a time.
    if os.path.exists(path()):
        old = os.path.join(os.path.dirname(run_dir()),
                           f"review-{now().replace(':', '')}")
        shutil.move(run_dir(), old)
        print(f"previous run moved to {old}")

    print(f"running {a.test_cmd} at {head[:12]} ...")
    rc, out = sh(a.test_cmd, cwd=r, timeout=3600)
    if rc != 0:
        print("NOTE: the suite is red at HEAD. Recheck compares against this.")

    save({
        "created": now(), "root": r, "base": base, "head": head,
        "test_cmd": a.test_cmd, "setup_cmd": a.setup_cmd,
        "baseline": {"rc": rc, "tail": tail(out, 4000)},
        "files": files, "findings": [], "next_id": 1,
    })

    total = 0
    for f, ranges in files.items():
        n = sum(int(x.split("-")[1]) - int(x.split("-")[0]) + 1 for x in ranges)
        total += n
        print(f"  {n:>5}  {f}")
    print(f"\nbase {base[:12]} · head {head[:12]} · {len(files)} files · "
          f"{total} changed lines\nledger {path()}")
    if not a.setup_cmd:
        print("NOTE: no --setup-cmd. If the suite needs installed dependencies "
              "or env files, findings in files that existed at the base will "
              "end unjudgeable.")


if __name__ == "__main__":
    main()
