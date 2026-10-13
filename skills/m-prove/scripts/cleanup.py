#!/usr/bin/env python3
"""Delete prove evidence dirs, and nothing else.

  cleanup.py <evidence dir>     one run's dir
  cleanup.py --all              every run's dir in this repo

Only paths inside <git common dir>/mstack/prove/ are deleted, so one allow
rule for this script is safe where `rm -rf` is not.
"""
import os
import shutil
import subprocess
import sys


def prove_root():
    p = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit("ABORT: not a git repository (needs git 2.31 or newer)")
    return os.path.realpath(os.path.join(p.stdout.strip(), "mstack", "prove"))


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    root = prove_root()
    if sys.argv[1] == "--all":
        targets = [os.path.join(root, d) for d in os.listdir(root)] if os.path.isdir(root) else []
    else:
        targets = [os.path.realpath(sys.argv[1])]
    for t in targets:
        if os.path.dirname(t) != root:
            sys.exit(f"ABORT: {t} is not a run dir under {root}")
        if os.path.isdir(t):
            shutil.rmtree(t)
            print(f"deleted {t}")
    if not targets:
        print("nothing to delete")


if __name__ == "__main__":
    main()
