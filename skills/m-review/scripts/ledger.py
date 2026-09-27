#!/usr/bin/env python3
"""Findings ledger. State on disk, not in the model's context.

States: proposed -> duplicate | unjudgeable | dead | confirmed
        confirmed | still-failing -> fixed | still-failing   (gate.py recheck)
Only gate.py writes confirmed, fixed and still-failing. This script refuses to.
"""
import argparse
import os
import sys

from common import die, git, now, read_json, root, state_dir, write_json

TERMINAL = {"duplicate", "unjudgeable", "dead", "confirmed", "fixed",
            "still-failing"}


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
    failing leftover turns later suite runs red."""
    r = root()
    for rel in a.remove:
        rel = rel.replace("\\", "/")
        if git(f"ls-files --error-unmatch -- {rel}", cwd=r)[0] == 0:
            die(f"{rel} is a tracked file; only a writer's new files are removed")
    close(a.id, "unjudgeable", a.reason)
    for rel in a.remove:
        full = os.path.join(r, rel)
        if os.path.exists(full):
            os.remove(full)
            print(f"removed {rel}")


def cmd_add(a):
    data = load()
    fid = f"F-{data['next_id']:03d}"
    data["next_id"] += 1
    data["findings"].append({
        "id": fid, "state": "proposed", "claim": a.claim, "file": a.file,
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
    p.add_argument("--file", required=True)
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
