#!/usr/bin/env python3
"""Delete prove evidence dirs, and nothing else.

  cleanup.py <evidence dir>     one run's dir
  cleanup.py --stale            every run's dir older than 24 hours: runs that
                                stopped before their cleanup
  cleanup.py --all              every run's dir in this repo

Only paths inside <git common dir>/mstack/prove/ are deleted, so one allow
rule for this script is safe where `rm -rf` is not.
"""
import os
import shutil
import stat
import subprocess
import sys
import time

STALE_HOURS = 24


def remove_tree(path):
    # A base worktree's node_modules nests past Windows' 260-character path limit:
    # the \\?\ prefix lifts it. Read-only files (git objects, packed deps) are made writable first.
    if os.name == "nt" and not path.startswith("\\\\?\\"):
        path = "\\\\?\\" + os.path.abspath(path)

    def retry(fn, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        fn(p)
    shutil.rmtree(path, onexc=retry) if sys.version_info >= (3, 12) else shutil.rmtree(
        path, onerror=lambda fn, p, exc: retry(fn, p, exc))


def prove_root():
    p = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit("ABORT: not a git repository (needs git 2.31 or newer)")
    return os.path.realpath(os.path.join(p.stdout.strip(), "mstack", "prove"))


def main():
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if len(sys.argv) == 2 else 2)
    if sys.argv[1].startswith("-") and sys.argv[1] not in ("--all", "--stale"):
        sys.exit(f"ABORT: unknown option {sys.argv[1]}\n{__doc__}")
    root = prove_root()
    if sys.argv[1] in ("--all", "--stale"):
        targets = [os.path.join(root, d) for d in os.listdir(root)] if os.path.isdir(root) else []
        if sys.argv[1] == "--stale":
            cutoff = time.time() - STALE_HOURS * 3600
            targets = [t for t in targets if os.path.getmtime(t) < cutoff]
    else:
        targets = [os.path.realpath(sys.argv[1])]
    for t in targets:
        if os.path.normcase(os.path.dirname(t)) != os.path.normcase(root):
            sys.exit(f"ABORT: {t} is not a run dir under {root}")
    targets = [t for t in targets if os.path.isdir(t)]
    failed = False
    for t in targets:
        try:
            remove_tree(t)
            print(f"deleted {t}")
        except OSError as e:
            # A process still running in it: Windows locks its cwd and open files.
            print(f"ABORT: {t} in use, stop the servers first · {e.strerror or e}", file=sys.stderr)
            failed = True
    if not targets:
        print("nothing to delete")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
