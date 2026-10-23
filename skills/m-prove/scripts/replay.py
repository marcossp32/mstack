#!/usr/bin/env python3
"""Replays: the checks a Q1 driver verified, kept per feature and run again.

A line is S<k> (a slice's Done when e2e) or R<n> (a requirement).

  replay.py save --feature <branch> --from <evidence dir>/q1/replay --clauses <evidence dir>/clauses.json [--lines S1,R3]
      After Judge accepts Q1, naming the lines it accepted as verified. Copies each one's replay
      into <git common dir>/mstack/replay/<feature>/, replacing that line's older one. Refused:
      an entry whose clause is missing or not the line's in --clauses (it would pass a changed
      requirement), and a command with shell syntax ($ % | & ; < > ` ' ") or run by a shell
      (bash, sh, cmd, powershell): replays run as plain argv, no shell, the same on every OS.
  replay.py list --feature <branch>
      The lines that have a replay, one per line with its command and clause, or `none`.
  replay.py run --feature <branch> | --from <replay dir> --url <app url> [--data <dir>] [--clauses <file>]
                [--run <id>] [--env KEY=VALUE]... [--lines S1,R3] [--out <file>]
      With the app up. --from: a driver's own replay dir, unsaved, checked the way it will be
      replayed. Runs each replay from its own dir, without a shell, with MSTACK_URL,
      MSTACK_RUN and MSTACK_DATA (--data: the app's data dir, as the contract's Run line names it).
      --env: a variable for the replays (repeatable); its value is masked in the output. The
      value of every MSTACK_SECRET_* variable in the environment is masked too: replays read
      credentials from there.
      --clauses: JSON, {"S1": "<the slice's Done when e2e>", "R3": "<the R line's requirement as
      the contract quotes it>"}. A replay saved
      for another clause is not run (`stale · clause changed`, or `stale · clause gone` when the file
      lacks the line): its pass would verify a requirement it never checked. One saved without a
      clause, or with shell syntax, is `stale` too.
      --run: the run id; MSTACK_RUN is <run id>-<unix ms>, so a second attempt never meets the
      values the first created. Default replay-<unix ms>.
      Exit 0 = every replay passed, 1 = some failed, went stale or could not run.
  replay.py clear --feature <branch>
      At the end of the feature. Deletes that feature's replays, nothing else.

A replay dir holds replay.json, {"R3": {"cmd": "node check.mjs", "clause": "\"each wait doubles\" · bound —"}, ...},
and one subdir per line (S1/, R3/) with the files its command uses; the command runs there.
It exits 0 when the line's observation holds and prints the observed value on
its last line. `python`/`python3` as its program run this script's interpreter.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

TIMEOUT = 300
SHELL_CHARS = set("$%|&;<>`'\"")
SHELLS = {"bash", "sh", "zsh", "cmd", "powershell", "pwsh", "wsl"}
CONTAIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contain.py")
# The interpreter itself, not a venv launcher in front of it: contain watches
# its parent, and a launcher outlives the script that started it.
PYTHON = getattr(sys, "_base_executable", None) or sys.executable

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


def order(line):
    """S lines first, then R lines, each by number; anything else last."""
    m = re.fullmatch(r"([SR])(\d+)", line)
    return (0 if m.group(1) == "S" else 1, int(m.group(2))) if m else (2, 0)


def load_index(d):
    path = os.path.join(d, "replay.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8-sig") as fh:  # a BOM is how Windows tools write UTF-8
        return json.load(fh)


def write_index(d, index):
    with open(os.path.join(d, "replay.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2, ensure_ascii=False)


def same_clause(a, b):
    # Quotes and spacing are how a clause was copied, not what it says.
    def norm(s):
        return " ".join(str(s).strip().strip('"“”').split())
    return norm(a) == norm(b)


def load_clauses(path):
    try:
        with open(path, encoding="utf-8-sig") as fh:
            clauses = json.load(fh)
    except (OSError, ValueError) as e:
        sys.exit(f"ABORT: --clauses {path}: {e}")
    if not isinstance(clauses, dict):
        sys.exit('ABORT: --clauses needs {"S<k>" | "R<n>": "<clause>"}')
    return clauses


def shell_syntax(cmd):
    """Why a command needs a shell, or None. Without one it runs the same on every OS."""
    words = str(cmd).split()
    if not words:
        return "empty command"
    if any(c in SHELL_CHARS for c in cmd):
        return "shell syntax ($ % | & ; < > ` ' \"): read values from the environment in the script"
    if os.path.splitext(os.path.basename(words[0]))[0].lower() in SHELLS:
        return f"runs a shell ({words[0]}): run the script's own interpreter"
    return None


def cmd_save(a):
    src = os.path.realpath(a.source)
    new = load_index(src)
    if not new:
        sys.exit(f"ABORT: no replay.json with entries in {src}")
    clauses = load_clauses(a.clauses)
    dst = feature_dir(a.feature)
    os.makedirs(dst, exist_ok=True)
    index = load_index(dst)
    keep = {x.strip() for x in a.lines.split(",")} if a.lines else None
    refused = 0
    for line, entry in new.items():
        if keep is not None and line not in keep:
            continue
        line_src = os.path.join(src, line)
        entry = entry if isinstance(entry, dict) else {}
        cmd, clause = entry.get("cmd"), entry.get("clause")
        why = ("needs an S<k> or R<n> key and a cmd" if not re.fullmatch(r"[SR]\d+", line) or not cmd
               else "no clause" if not clause
               else "clause is not this line's in --clauses"
               if line not in clauses or not same_clause(clause, clauses[line])
               else shell_syntax(cmd)
               or (None if os.path.isdir(line_src) else f"no dir of its own at {line_src}"))
        if why:
            print(f"refused {line} · {why}")
            refused += 1
            continue
        line_dir = os.path.join(dst, line)
        if os.path.isdir(line_dir):
            shutil.rmtree(line_dir)
        shutil.copytree(line_src, line_dir)
        index[line] = {"cmd": cmd, "clause": clauses[line]}
        print(f"saved {line} · {cmd}")
    write_index(dst, index)
    sys.exit(1 if refused else 0)


def resolve(argv, env, cwd):
    """argv with its program found on the replay's PATH (or in its dir), or None."""
    prog = argv[0]
    if os.path.splitext(os.path.basename(prog))[0].lower() in ("python", "python3"):
        return [PYTHON] + argv[1:]  # `python3` is missing or a store stub on some Windows
    local = os.path.join(cwd, prog)
    found = (os.path.abspath(local) if os.path.dirname(prog) and os.path.isfile(local)
             else shutil.which(prog, path=env.get("PATH")))
    return [found] + argv[1:] if found else None


def mask(text, secrets):
    for v in secrets:
        text = text.replace(v, "***")
    return text


def cmd_run(a):
    d = os.path.realpath(a.source) if a.source else feature_dir(a.feature)
    index = load_index(d)
    wanted = [x.strip() for x in a.lines.split(",")] if a.lines else sorted(index, key=order)
    if not index:
        msg = "REPLAY: none · no replays for this feature"
        if a.out:  # the drive reads it whatever happened
            with open(a.out, "w", encoding="utf-8") as fh:
                fh.write(msg + "\n")
        print(msg)
        sys.exit(1)
    clauses = load_clauses(a.clauses) if a.clauses else {}
    extra = {}
    for kv in a.env or []:
        k, sep, v = kv.partition("=")
        if not sep or not k:
            sys.exit(f"ABORT: --env {kv!r} needs KEY=VALUE")
        extra[k] = v
    secret_env = [v for k, v in os.environ.items() if k.upper().startswith("MSTACK_SECRET_")]
    secrets = sorted({v for v in [*extra.values(), *secret_env] if v}, key=len, reverse=True)
    run_id = f"{a.run or 'replay'}-{int(time.time() * 1000)}"
    env = {**os.environ, **extra, "MSTACK_URL": a.url, "MSTACK_RUN": run_id}
    if a.data:
        env["MSTACK_DATA"] = os.path.realpath(a.data)
    results, log = [], [f"# MSTACK_RUN={run_id}\n"]
    for line in wanted:
        if line not in index:
            results.append((line, "missing", "no replay for this line"))
            continue
        saved, cmd = index[line].get("clause"), index[line]["cmd"]
        why = "no clause" if not saved else shell_syntax(cmd)
        if not why and a.clauses:
            why = ("clause gone" if line not in clauses
                   else None if same_clause(saved, clauses[line]) else "clause changed")
        if why:
            results.append((line, "stale", why))
            log.append(f"# {line} stale · {why}\n")
            continue
        cwd = os.path.join(d, line)
        argv = resolve(cmd.split(), env, cwd)
        if argv is None:
            results.append((line, "fail", f"cannot run: {cmd.split()[0]} not found"))
            log.append(f"$ {cmd}  # {line}\n{cmd.split()[0]} not found\n")
            continue
        # Contained: a timeout ends the browser or server the check started too.
        full = [PYTHON, CONTAIN, "--with-parent", "--timeout", str(TIMEOUT), "--"] + argv
        try:
            p = subprocess.run(full, cwd=cwd, env=env,
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=TIMEOUT + 60)
            out = (p.stdout or "") + (p.stderr or "")
            state = "pass" if p.returncode == 0 else "fail"
            if "contain: TIMEOUT" in out:
                out += "\nTIMEOUT"
        except subprocess.TimeoutExpired:
            out, state = "TIMEOUT", "fail"
        out = mask(out, secrets)
        lines = [l for l in out.strip().splitlines()
                 if not l.startswith("contain: ") or l.startswith("contain: TIMEOUT")]
        last = (lines or [""])[-1][:200]
        results.append((line, state, last))
        log.append(f"$ {mask(cmd, secrets)}  # {line}\n{out}\n")
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
    for line in sorted(index, key=order):
        c = index[line].get("clause")
        print(f"{line} · {index[line]['cmd']}" + (f" · {c}" if c else ""))
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
    p.add_argument("--clauses", required=True)
    p.add_argument("--lines")
    p.set_defaults(fn=cmd_save)
    p = sub.add_parser("run")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--feature")
    g.add_argument("--from", dest="source")
    p.add_argument("--url", required=True)
    p.add_argument("--data")
    p.add_argument("--clauses")
    p.add_argument("--run")
    p.add_argument("--env", action="append")
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
