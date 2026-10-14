#!/usr/bin/env python3
"""Replays: the checks a Q1 driver verified, kept per feature and run again.

  replay.py save --feature <branch> --from <evidence dir>/q1/replay [--lines R1,R3]
      After Judge accepts Q1, naming the lines it accepted as verified. Copies each one's replay into
      <git common dir>/mstack/replay/<feature>/, replacing that line's older one.
  replay.py list --feature <branch>
      The lines that have a replay, one per line, or `none`.
  replay.py run --feature <branch> --url <app url> [--lines R1,R3] [--out <file>]
      With the app up. Runs each replay with MSTACK_URL set, from its own dir.
      Exit 0 = every replay passed, 1 = some failed or could not run.
  replay.py clear --feature <branch>
      At the end of the feature. Deletes that feature's replays, nothing else.

A replay dir holds replay.json, {"R3": {"cmd": "node check.mjs"}, ...}, and one
subdir per line (R3/) with the files its command uses; the command runs there.
It exits 0 when the line's observation holds and prints the observed value on
its last line.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

TIMEOUT = 300
CONTAIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contain.py")

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def replay_root():
    p = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit("ABORT: not a git repository (needs git 2.31 or newer)")
    return os.path.realpath(os.path.join(p.stdout.strip(), "mstack", "replay"))


def feature_dir(feature):
    name = re.sub(r"[^A-Za-z0-9._-]", "_", feature.removeprefix("origin/"))
    return os.path.join(replay_root(), name)


def load_index(d):
    path = os.path.join(d, "replay.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_index(d, index):
    with open(os.path.join(d, "replay.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2, ensure_ascii=False)


def cmd_save(a):
    src = os.path.realpath(a.source)
    new = load_index(src)
    if not new:
        sys.exit(f"ABORT: no replay.json with entries in {src}")
    dst = feature_dir(a.feature)
    os.makedirs(dst, exist_ok=True)
    index = load_index(dst)
    keep = {x.strip() for x in a.lines.split(",")} if a.lines else None
    for line, entry in new.items():
        if keep is not None and line not in keep:
            continue
        if not re.fullmatch(r"R\d+", line) or not entry.get("cmd"):
            sys.exit(f"ABORT: {line} needs an R<n> key and a cmd")
        line_src = os.path.join(src, line)
        if not os.path.isdir(line_src):
            sys.exit(f"ABORT: {line} has no dir of its own at {line_src}")
        line_dir = os.path.join(dst, line)
        if os.path.isdir(line_dir):
            shutil.rmtree(line_dir)
        shutil.copytree(line_src, line_dir)
        index[line] = {"cmd": entry["cmd"]}
        print(f"saved {line} · {entry['cmd']}")
    write_index(dst, index)


def cmd_run(a):
    d = feature_dir(a.feature)
    index = load_index(d)
    wanted = [x.strip() for x in a.lines.split(",")] if a.lines else sorted(
        index, key=lambda k: int(k[1:]))
    if not index:
        print("REPLAY: none · no replays for this feature")
        sys.exit(1)
    env = {**os.environ, "MSTACK_URL": a.url}
    results, log = [], []
    for line in wanted:
        if line not in index:
            results.append((line, "missing", "no replay for this line"))
            continue
        cmd = index[line]["cmd"]
        # Contained: a timeout ends the browser or server the check started too.
        argv = [sys.executable, CONTAIN, "--timeout", str(TIMEOUT), "--shell", cmd]
        try:
            p = subprocess.run(argv, cwd=os.path.join(d, line), env=env,
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=TIMEOUT + 60)
            out = (p.stdout or "") + (p.stderr or "")
            state = "pass" if p.returncode == 0 else "fail"
            if "contain: TIMEOUT" in out:
                out += "\nTIMEOUT"
        except subprocess.TimeoutExpired:
            out, state = "TIMEOUT", "fail"
        lines = [l for l in out.strip().splitlines()
                 if not l.startswith("contain: ") or l.startswith("contain: TIMEOUT")]
        last = (lines or [""])[-1][:200]
        results.append((line, state, last))
        log.append(f"$ {cmd}  # {line}\n{out}\n")
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write("".join(log))
    for line, state, last in results:
        print(f"{line} · {state} · {last}")
    passed = sum(1 for _, s, _ in results if s == "pass")
    ok = passed == len(results)
    print(f"REPLAY: {'PASS' if ok else 'FAIL'} · {passed} of {len(results)}")
    sys.exit(0 if ok else 1)


def cmd_list(a):
    index = load_index(feature_dir(a.feature))
    for line in sorted(index, key=lambda k: int(k[1:])):
        print(f"{line} · {index[line]['cmd']}")
    if not index:
        print("none")


def cmd_clear(a):
    root, d = replay_root(), os.path.realpath(feature_dir(a.feature))
    if os.path.normcase(os.path.dirname(d)) != os.path.normcase(root):
        sys.exit(f"ABORT: {d} is not a feature dir under {root}")
    if os.path.isdir(d):
        shutil.rmtree(d)
        print(f"deleted {d}")
    else:
        print("nothing to delete")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("save")
    p.add_argument("--feature", required=True)
    p.add_argument("--from", dest="source", required=True)
    p.add_argument("--lines")
    p.set_defaults(fn=cmd_save)
    p = sub.add_parser("run")
    p.add_argument("--feature", required=True)
    p.add_argument("--url", required=True)
    p.add_argument("--lines")
    p.add_argument("--out")
    p.set_defaults(fn=cmd_run)
    p = sub.add_parser("list")
    p.add_argument("--feature", required=True)
    p.set_defaults(fn=cmd_list)
    p = sub.add_parser("clear")
    p.add_argument("--feature", required=True)
    p.set_defaults(fn=cmd_clear)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
