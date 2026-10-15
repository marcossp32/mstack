#!/usr/bin/env python3
"""Findings ledger. State on disk, not in the model's context.

States: proposed -> duplicate | unjudgeable | dead | confirmed
        confirmed | still-failing -> fixed | still-failing | stale   (gate.py recheck)
        stale -> fixed | still-failing | stale   (gate.py recheck, rewritten repro)
Only gate.py writes confirmed, fixed, still-failing and stale. This script refuses to.

Also the review's base worktree and leftover cleanup, shared by prepare,
gate and report.
"""
import argparse
import os
import posixpath
import shutil
import stat
import subprocess
import sys

from common import die, now, read_json, root, sha, state_dir, write_json

TERMINAL = {"duplicate", "unjudgeable", "dead", "confirmed", "fixed",
            "still-failing", "stale"}
BASE_PREFIX = "mstack-base-"


def run_dir():
    return state_dir("review")


def path():
    return os.path.join(run_dir(), "ledger.json")


def load():
    data = read_json(path())
    if data is None:
        die("no ledger. Run prepare.py first")
    return data


def save(data):
    write_json(path(), data)


def find(data, fid):
    for f in data["findings"]:
        if f["id"] == fid:
            return f
    die(f"no such finding {fid}")


def run_git(args, cwd):
    """git with an argument list: paths with spaces or shell characters stay intact."""
    p = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()


def tracked(rel, cwd):
    return run_git(["ls-files", "--error-unmatch", "--", rel], cwd)[0] == 0


def repo_rel(r, given):
    """A path as given by an agent (backslashes, ./, absolute) made repo-relative
    with forward slashes, or None when it resolves outside the repo or into git's dir."""
    p = given.strip().replace("\\", "/").rstrip("/")
    # The parent resolved, the name kept: a symlink is removed, never its target.
    joined = os.path.join(r, p)
    full = os.path.normpath(os.path.join(os.path.realpath(os.path.dirname(joined)),
                                         os.path.basename(joined)))
    top = os.path.normcase(os.path.realpath(r))
    try:
        inside = os.path.normcase(os.path.commonpath([full, top])) == top
    except ValueError:  # another drive
        inside = False
    if not inside or os.path.normcase(full) == top:
        return None
    rel = posixpath.normpath(os.path.relpath(full, top).replace("\\", "/"))
    return None if ".git" in rel.split("/") else rel


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


def remove_bases(r, keep=None, say=print):
    """Removes every base worktree a review of this repo made, except keep, and
    prunes git's records of them. A killed run leaves its worktree behind."""
    _, out = run_git(["worktree", "list", "--porcelain"], r)
    keep = os.path.normcase(os.path.realpath(keep)) if keep else None
    for line in out.splitlines():
        if not line.startswith("worktree "):
            continue
        wt = line[len("worktree "):]
        if (os.path.basename(wt).startswith(BASE_PREFIX)
                and os.path.normcase(os.path.realpath(wt)) != keep):
            if os.path.isdir(wt):
                try:
                    remove_tree(wt)
                except OSError as e:
                    say(f"NOTE: could not remove the base worktree {wt}: {e}")
                    continue
            say(f"removed the base worktree {wt}")
    run_git(["worktree", "prune"], r)


def sweep_leftovers(data, r, skip=()):
    """Removes reproduction files a killed gate left in the checkout: only the
    files the ledger recorded for a finding still proposed, untracked and
    unchanged since. A leftover failing file turns every later suite run red."""
    for f in data["findings"]:
        if f["state"] != "proposed":
            continue
        for g in f.get("gate_files", []):
            full = os.path.join(r, g["path"])
            if (g["path"] in skip or not os.path.isfile(full) or tracked(g["path"], r)
                    or sha(full) != g["sha256"]):
                continue
            os.remove(full)
            print(f"removed {g['path']}, left by an interrupted gate on {f['id']}")


def close(fid, state, reason, extra=None):
    data = load()
    f = find(data, fid)
    if f["state"] != "proposed":
        die(f"{fid} is {f['state']}, not proposed", 2)
    f.update({"state": state, "reason": reason, "closed": now()})
    if extra:
        f.update(extra)
    save(data)
    print(f"{fid} -> {state}")


def cmd_unjudgeable(a):
    """Closes the finding and removes the files its writer left behind: a
    failing leftover turns later suite runs red. Everything is checked before
    the state changes."""
    r = root()
    remove, skipped = [], []
    for given in a.remove:
        rel = repo_rel(r, given)
        full = os.path.join(r, rel) if rel else None
        if rel is None:
            skipped.append(f"{given} (outside the repo)")
        elif os.path.isdir(full):
            skipped.append(f"{given} (a directory)")
        elif not os.path.lexists(full):
            skipped.append(f"{given} (not there)")
        elif tracked(rel, r):
            die(f"{rel} is a tracked file; only a writer's new files are removed")
        else:
            remove.append(rel)
    close(a.id, "unjudgeable", a.reason)
    for rel in remove:
        os.remove(os.path.join(r, rel))
        print(f"removed {rel}")
    for s in skipped:
        print(f"not removed: {s}")


def cmd_add(a):
    r = root()
    rel = repo_rel(r, a.file)
    # The file names the finding everywhere after: report, fix step, recheck.
    if rel is None or run_git(["cat-file", "-t", f"HEAD:{rel}"], r)[1] != "blob":
        die(f"--file {a.file}: not a file at HEAD. Give its repo-relative path")
    data = load()
    fid = f"F-{data['next_id']:03d}"
    data["next_id"] += 1
    data["findings"].append({
        "id": fid, "state": "proposed", "claim": a.claim, "file": rel,
        "line": a.line, "condition": a.condition, "entry": a.entry,
        "hunter": a.hunter, "created": now(),
    })
    save(data)
    print(fid)


def cmd_list(a):
    data = load()
    rows = [f for f in data["findings"] if not a.state or f["state"] == a.state]
    if not rows:
        print("(empty)")
    for f in rows:
        print(f"{f['id']}  {f['state']:<13} {f['file']}:{f['line']}  "
              f"entry {f.get('entry', '?')}\n      {f['claim']}\n"
              f"      condition: {f['condition']}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add")
    p.add_argument("--claim", required=True, help="what is broken, one sentence")
    p.add_argument("--file", required=True, help="repo-relative, a file at HEAD")
    p.add_argument("--line", required=True)
    p.add_argument("--condition", required=True,
                   help="the observable condition that would demonstrate it")
    p.add_argument("--entry", required=True,
                   help="the public entry point real input reaches it through")
    p.add_argument("--hunter", default="")
    p.set_defaults(fn=cmd_add)

    p = sub.add_parser("duplicate")
    p.add_argument("--id", required=True)
    p.add_argument("--of", required=True)
    p.set_defaults(fn=lambda a: close(a.id, "duplicate", f"same claim and "
                                      f"condition as {a.of}"))

    p = sub.add_parser("unjudgeable")
    p.add_argument("--id", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--remove", nargs="*", default=[],
                   help="repo-relative new files the writer left behind")
    p.set_defaults(fn=cmd_unjudgeable)

    p = sub.add_parser("list")
    p.add_argument("--state")
    p.set_defaults(fn=cmd_list)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
