#!/usr/bin/env python3
"""Replays: the checks a Q1 driver verified, kept per feature and run again.

A line is S<k> (a slice's Done when e2e) or R<n> (a requirement).

  replay.py save --feature <branch> --from <evidence dir>/q1/replay --clauses <evidence dir>/clauses.json
                 --base-check <evidence dir>/base-check.txt | --no-base "<why>" [--lines S1,R3]
      After Judge accepts Q1, naming the lines it accepted as verified. Copies each one's replay
      into <git common dir>/mstack/replay/<feature>/, replacing that line's older one. Refused:
      an entry whose clause is missing or not the line's in --clauses (it would pass a changed
      requirement); a command with shell syntax ($ % | & ; < > ` ' ") or run by a shell
      (bash, sh, cmd, powershell): replays run as plain argv, no shell, the same on every OS;
      and a line --base-check shows passing on the base: it checks nothing the change made.
      --base-check is the `batch --from <this same dir> --base` report, refused when it names
      another dir or a line's files changed since; a line it does not name (one asking that
      something keeps working) or could not run there is saved, with that recorded.
      --no-base: no base at hand (slice mode); each line is saved as `base none · <why>`, and
      the final checks it on its base (batch --feature --base).
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
  replay.py batch --feature <branch> | --from <replay dir> --clauses <evidence dir>/clauses.json
                  --out <evidence dir>/replay.txt [--spec <run.json>] [--checkout <dir>] [--base]
                  [--run <id>] [--env KEY=VALUE]... [--lines S1,R3]
      The supervisor's run of the saved replays (--from: a driver's unsaved ones), with no app up.
      --base: --checkout is the final's base worktree, and --lines (required) the lines that
      ask for new or changed behaviour. Each must fail there: one that
      passes checks nothing the change made. No solo retry. Ends `BASE: <k> of <n> fail on the
      base · vacuous <lines | none>`, exit 0 when none passed. With --feature it also records
      the result: a vacuous line's replay is invalidated (the next prove drives it), the rest
      are marked `base fails`. --spec defaults to run.json
      beside --out, then <git common dir>/mstack/run.json (runspec.py --help). Launches the
      app by the spec and waits for its health check (a spec without launch, a CLI or library:
      no app and no MSTACK_URL), runs the replays in chunks with a health check between them
      (a failed one restarts the app, at most 3 times; then the rest are `not run`), runs the
      spec's restore before each replay when it declares one, and runs each failure again
      alone on a freshly started app. One that then passes is `flaky · … passed only alone`:
      not a pass, since a frozen check that fails once is a lead for a drive, but a sign the
      batch broke it. Replays run side by side only when the spec's parallel is above 1 and it
      declares no restore. Each replay gets its own MSTACK_RUN. Stops the app and restores
      state before it exits. Prints a short table (events, the passes on one line, every other
      line with its state and last output line, then REPLAY: PASS | FAIL · <passed> of <n>,
      or BASE: …);
      --out gets that, then each replay's full output. Exit 0 = every line passed. Run it in
      the background.
  replay.py invalidate --feature <branch> --lines R3,S2 --why "<D<k> · what changed>" [--retired]
      When a decision undoes a line or changes its surface. Its words may stay the same, so
      its replay would still match its clause and could pass against what no longer holds.
      Deletes those lines' replays and records why; run, batch and list then show each as
      `stale · invalidated · <why>`, so the next prove drives it. A later save lifts it.
      --retired: the lines are retired (no prove has them any more): their replays are
      deleted and nothing is recorded, so they never show up again.
  replay.py audit --from <evidence dir>/replay.txt [--skip R1,S2] [--rate 0.2] [--seed <n>]
      A repeat final's spot audit. Picks at random about --rate (at least one) of the lines
      batch passed, minus --skip (the lines a driver drives anyway), for Q1 to drive with fresh
      values. Prints `AUDIT: <lines> · <k> of <n> passed by replay` or `AUDIT: none · no line
      passed by replay alone`. The script picks, so nobody chooses which replays get checked.
  replay.py clear --feature <branch>
      At the end of the feature. Deletes that feature's replays, nothing else.

A replay dir holds replay.json, {"R3": {"cmd": "node check.mjs", "clause": "\"each wait doubles\" · bound —"}, ...},
and one subdir per line (S1/, R3/) with the files its command uses; the command runs there.
It exits 0 when the line's observation holds and prints the observed value on
its last line. `python`/`python3` as its program run this script's interpreter.
"""
import argparse
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

TIMEOUT = 300
CHUNK = 8          # batch: replays between two health checks, per worker
MAX_RESTARTS = 3   # batch: app restarts before the remaining lines are `not run`
SHELL_CHARS = set("$%|&;<>`'\"")
SHELLS = {"bash", "sh", "zsh", "cmd", "powershell", "pwsh", "wsl"}
HERE = os.path.dirname(os.path.abspath(__file__))
CONTAIN = os.path.join(HERE, "contain.py")
sys.path.insert(0, HERE)  # runspec.py, for batch
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


def write_index(d, index, name="replay.json"):
    with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2, ensure_ascii=False)


def load_invalid(d):
    """{line: why} for the lines a decision invalidated, kept beside replay.json."""
    path = os.path.join(d, "invalidated.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def split_lines(arg):
    lines = [x.strip() for x in (arg or "").split(",") if x.strip()]
    bad = [l for l in lines if not re.fullmatch(r"[SR]\d+", l)]
    if bad:
        sys.exit(f"ABORT: lines are S<k> or R<n>: {', '.join(bad)}")
    return lines


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


def dir_hash(path):
    """sha256 over a replay dir's file names and contents: binds a base report to these files."""
    h = hashlib.sha256()
    for root, dirs, files in os.walk(path):
        dirs.sort()
        for f in sorted(files):
            full = os.path.join(root, f)
            h.update(os.path.relpath(full, path).replace(os.sep, "/").encode())
            with open(full, "rb") as fh:
                h.update(hashlib.sha256(fh.read()).digest())
    return h.hexdigest()[:16]


BOUND = re.compile(r"^# base-check of (.+) · ([SR]\d+)=([0-9a-f]+)$")
ROW = re.compile(r"^([SR]\d+) · (pass|fail|flaky|stale|missing|not run) · ?(.*)$")
VACUOUS = "passes on the base: it checks nothing the change made"


def base_report(path, src):
    """{line: (state, last output line)} from a batch --base report run on src's own files."""
    try:
        with open(path, encoding="utf-8-sig") as fh:
            text = fh.read()
    except OSError as e:
        sys.exit(f"ABORT: --base-check {path}: {e}")
    if "BASE: " not in text:
        sys.exit(f"ABORT: --base-check {path} is not a batch --base report")
    rows, bound = {}, {}
    for row in text.splitlines():
        b = BOUND.match(row)
        if b:
            if os.path.normcase(b.group(1)) != os.path.normcase(src):
                sys.exit(f"ABORT: --base-check {path} checked {b.group(1)}, not {src}")
            bound[b.group(2)] = b.group(3)
            continue
        m = ROW.match(row)
        if m and m.group(1) not in rows:
            rows[m.group(1)] = (m.group(2), m.group(3))
    for line in list(rows):
        line_dir = os.path.join(src, line)
        if bound.get(line) != (dir_hash(line_dir) if os.path.isdir(line_dir) else None):
            rows[line] = ("changed", "files changed after the base check")
    return rows


def cmd_save(a):
    src = os.path.realpath(a.source)
    new = load_index(src)
    if not new:
        sys.exit(f"ABORT: no replay.json with entries in {src}")
    clauses = load_clauses(a.clauses)
    if bool(a.base_check) == bool((a.no_base or "").strip()):
        sys.exit('ABORT: save needs --base-check <a batch --base report> or --no-base "<why>"')
    on_base = base_report(a.base_check, src) if a.base_check else None
    dst = feature_dir(a.feature)
    os.makedirs(dst, exist_ok=True)
    index, invalid = load_index(dst), load_invalid(dst)
    keep ={x.strip() for x in a.lines.split(",")} if a.lines else None
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
               or (None if os.path.isdir(line_src) else f"no dir of its own at {line_src}")
               or (on_base and on_base.get(line, ("",))[0] in ("pass", "flaky")
                   and f"{VACUOUS} · {on_base[line][1]}")
               or (on_base and on_base.get(line, ("",))[0] == "changed"
                   and "its files changed after the base check: check it again") or None)
        if why:
            print(f"refused {line} · {why}")
            refused += 1
            continue
        line_dir = os.path.join(dst, line)
        if os.path.isdir(line_dir):
            shutil.rmtree(line_dir)
        shutil.copytree(line_src, line_dir)
        base = (f"none · {a.no_base.strip()}" if on_base is None
                else "not checked · not in --base-check" if line not in on_base
                else "fails" if on_base[line][0] == "fail"
                else f"not run · {on_base[line][0]} · {on_base[line][1]}")
        index[line] = {"cmd": cmd, "clause": clauses[line], "base": base}
        invalid.pop(line, None)
        print(f"saved {line} · {cmd} · base {base}")
    write_index(dst, index)
    write_index(dst, invalid, "invalidated.json")
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


def parse_env(pairs):
    extra = {}
    for kv in pairs or []:
        k, sep, v = kv.partition("=")
        if not sep or not k:
            sys.exit(f"ABORT: --env {kv!r} needs KEY=VALUE")
        extra[k] = v
    secret_env = [v for k, v in os.environ.items() if k.upper().startswith("MSTACK_SECRET_")]
    secrets = sorted({v for v in [*extra.values(), *secret_env] if v}, key=len, reverse=True)
    return extra, secrets


def why_stale(index, line, clauses, check, invalid=None):
    """Why a line cannot be replayed against these clauses, as (state, why), or None."""
    if line not in index:
        if invalid and line in invalid:
            return "stale", f"invalidated · {invalid[line]}"
        return "missing", "no replay for this line"
    saved, cmd = index[line].get("clause"), index[line]["cmd"]
    why = "no clause" if not saved else shell_syntax(cmd)
    if not why and check:
        why = ("clause gone" if line not in clauses
               else None if same_clause(saved, clauses[line]) else "clause changed")
    return ("stale", why) if why else None


def run_one(d, index, line, env, secrets):
    """Run one replay. Returns (state, last output line, log block)."""
    cmd = index[line]["cmd"]
    cwd = os.path.join(d, line)
    argv = resolve(cmd.split(), env, cwd)
    if argv is None:
        return ("fail", f"cannot run: {cmd.split()[0]} not found",
                f"$ {cmd}  # {line}\n{cmd.split()[0]} not found\n")
    # Contained: a timeout ends the browser or server the check started too.
    full = [PYTHON, CONTAIN, "--with-parent", "--timeout", str(TIMEOUT), "--"] + argv
    try:
        p = subprocess.run(full, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
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
    return state, (lines or [""])[-1][:200], f"$ {mask(cmd, secrets)}  # {line}\n{out}\n"


def no_replays(a):
    msg = "REPLAY: none · no replays for this feature"
    if a.out:  # the drive reads it whatever happened
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(msg + "\n")
    print(msg)
    sys.exit(1)


def cmd_run(a):
    d = os.path.realpath(a.source) if a.source else feature_dir(a.feature)
    index, invalid = load_index(d), load_invalid(d)
    wanted = ([x.strip() for x in a.lines.split(",")] if a.lines
              else sorted({*index, *invalid}, key=order))
    if not index and not invalid:
        no_replays(a)
    clauses = load_clauses(a.clauses) if a.clauses else {}
    extra, secrets = parse_env(a.env)
    run_id = f"{a.run or 'replay'}-{int(time.time() * 1000)}"
    env = {**os.environ, **extra, "MSTACK_URL": a.url, "MSTACK_RUN": run_id}
    if a.data:
        env["MSTACK_DATA"] = os.path.realpath(a.data)
    results, log = [], [f"# MSTACK_RUN={run_id}\n"]
    for line in wanted:
        stale = why_stale(index, line, clauses, bool(a.clauses), invalid)
        if stale:
            results.append((line, *stale))
            log.append(f"# {line} {stale[0]} · {stale[1]}\n")
            continue
        state, last, block = run_one(d, index, line, env, secrets)
        results.append((line, state, last))
        log.append(block)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write("".join(log))
    for line, state, last in results:
        print(f"{line} · {state} · {last}")
    passed = sum(1 for _, s, _ in results if s == "pass")
    ok = passed == len(results)
    print(f"REPLAY: {'PASS' if ok else 'FAIL'} · {passed} of {len(results)}")
    sys.exit(0 if ok else 1)


def cmd_batch(a):
    """Every saved replay against an app this script launches, keeps healthy and stops."""
    import runspec
    if a.base and not a.lines:
        sys.exit("ABORT: --base needs --lines: the lines asking new or changed behaviour "
                 "(one asking that something keeps working rightly passes on the base)")
    d = os.path.realpath(a.source) if a.source else feature_dir(a.feature)
    index, invalid = load_index(d), load_invalid(d)
    if not index and not invalid:
        no_replays(a)
    wanted = ([x.strip() for x in a.lines.split(",")] if a.lines
              else sorted({*index, *invalid}, key=order))
    clauses = load_clauses(a.clauses)
    checkout = os.path.realpath(a.checkout)
    spec = runspec.load(runspec.locate(a.spec, os.path.dirname(os.path.realpath(a.out)), checkout))
    launches = bool(spec.get("launch"))
    extra, secrets = parse_env(a.env)
    data = runspec.data_of(spec, checkout)
    workers = runspec.parallel(spec)
    out_dir = os.path.dirname(os.path.realpath(a.out))
    app_log = os.path.join(out_dir, "replay-app.log")
    restore_log = os.path.join(out_dir, "replay-restore.log")
    results, log, events = {}, [], []
    t0 = time.monotonic()
    state = {"app": None, "restarts": 0}

    def start_app():
        if not launches:
            return True
        if state["app"]:
            state["app"].stop()
        state["app"] = runspec.App(spec, checkout, app_log)
        up, secs, why = state["app"].start()
        events.append(f"launch · {'up' if up else 'not up'} in {secs}s" + (f" · {why}" if why else ""))
        return up

    def ensure_up():
        if not launches or (state["app"] and state["app"].healthy()):
            return True
        if state["restarts"] >= MAX_RESTARTS:
            return False
        state["restarts"] += 1
        events.append("health check failed · restarting the app")
        return start_app()

    def restore():
        if spec.get("restore"):
            port = state["app"].port if state["app"] else spec.get("port")
            rc, last, _ = runspec.shell(spec["restore"], spec, checkout, port, restore_log)
            if rc != 0:
                events.append(f"restore failed exit {rc} · {last}")

    def one(line, attempt):
        restore()
        app = state["app"]
        env = {**runspec.env_of(spec, checkout, app.port if app else spec.get("port")), **extra,
               "MSTACK_RUN": f"{a.run or 'replay'}-{line}-{attempt}-{int(time.time() * 1000)}"}
        if app:
            env["MSTACK_URL"] = app.url
        if data:
            env["MSTACK_DATA"] = data
        return (line, *run_one(d, index, line, env, secrets))

    runnable = []
    for line in wanted:
        stale = why_stale(index, line, clauses, True, invalid)
        if stale:
            results[line] = stale
            log.append(f"# {line} {stale[0]} · {stale[1]}\n")
        else:
            runnable.append(line)
    try:
        if runnable and not start_app():
            for line in runnable:
                results[line] = ("not run", "app not up on its health check")
            runnable = []
        chunk = CHUNK * workers
        for i in range(0, len(runnable), chunk):
            if not ensure_up():
                for line in runnable[i:]:
                    results[line] = ("not run", "app down after restarts")
                break
            batch = runnable[i:i + chunk]
            if workers > 1:
                with ThreadPoolExecutor(workers) as pool:
                    done = list(pool.map(lambda l: one(l, 1), batch))
            else:
                done = [one(l, 1) for l in batch]
            for line, st, last, block in done:
                results[line] = (st, last)
                log.append(block)
        failed = [] if a.base else [l for l in runnable if results[l][0] == "fail"]
        if failed:
            # Alone, on a fresh app: tells a replay broken by another beside it, or by state an
            # earlier one left, from one that fails on its own.
            events.append(f"solo retry of {len(failed)}" + (" on a fresh app" if launches else ""))
            if start_app():
                for line in failed:
                    if not ensure_up():
                        break
                    _, st, last, block = one(line, 2)
                    log.append(f"# {line} retried alone\n{block}")
                    results[line] = (("flaky", f"{last} · passed only alone, failed in the batch")
                                     if st == "pass" else (st, last))
    finally:
        if state["app"]:
            state["app"].stop()
        restore()  # leave shared state as the replays found it
    rows = [(l, *results[l]) for l in wanted]
    passed = [l for l, s, _ in rows if s == "pass"]
    ok = len(passed) == len(rows)
    bind = []
    tail = f"{round(time.monotonic() - t0)}s · at once {workers} · restarts {state['restarts']}"
    if a.base:
        ok = not passed
        failing = [l for l, s, _ in rows if s == "fail"]
        summary = (f"BASE: {len(failing)} of {len(rows)} fail on the base · "
                   f"vacuous {' '.join(passed) or 'none'} · {tail}")
        if a.feature:
            record_base(d, index, invalid, passed, failing)
        else:
            bind = [f"# base-check of {d} · {l}={dir_hash(os.path.join(d, l))}"
                      for l in wanted if os.path.isdir(os.path.join(d, l))]
    else:
        summary = f"REPLAY: {'PASS' if ok else 'FAIL'} · {len(passed)} of {len(rows)} · {tail}"
    table = events + ([f"pass · {' '.join(passed)}"] if passed else [])
    table += [f"{l} · {s} · {last}" for l, s, last in rows if s != "pass"] + bind
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(table + [summary, ""]))
        fh.write("\n".join(f"{l} · {s} · {last}" for l, s, last in rows) + "\n\n" + "".join(log))
    print("\n".join(table + [summary]))
    sys.exit(0 if ok else 1)


def record_base(d, index, invalid, vacuous, failing):
    """A saved replay that passes on the base is no check: drop it, so the next prove drives it."""
    for line in vacuous:
        index.pop(line, None)
        if os.path.isdir(os.path.join(d, line)):
            shutil.rmtree(os.path.join(d, line))
        invalid[line] = VACUOUS
    for line in failing:
        if line in index:
            index[line]["base"] = "fails"
    write_index(d, index)
    write_index(d, invalid, "invalidated.json")


def cmd_list(a):
    d = feature_dir(a.feature)
    index, invalid = load_index(d), load_invalid(d)
    for line in sorted({*index, *invalid}, key=order):
        if line not in index:
            print(f"{line} · invalidated · {invalid[line]}")
            continue
        c, b = index[line].get("clause"), index[line].get("base")
        print(f"{line} · {index[line]['cmd']}" + (f" · {c}" if c else "")
              + f" · base {b or 'none · saved before base checks'}")
    if not index and not invalid:
        print("none")


def cmd_invalidate(a):
    lines = split_lines(a.lines)
    if not lines or not a.why.strip():
        sys.exit("ABORT: invalidate needs --lines and a --why naming the decision")
    d = feature_dir(a.feature)
    os.makedirs(d, exist_ok=True)
    index, invalid = load_index(d), load_invalid(d)
    for line in lines:
        had = index.pop(line, None) is not None
        line_dir = os.path.join(d, line)
        if os.path.isdir(line_dir):
            shutil.rmtree(line_dir)
        if a.retired:
            invalid.pop(line, None)
            print(f"retired {line} · {'replay deleted' if had else 'had no replay'} · {a.why.strip()}")
            continue
        invalid[line] = a.why.strip()
        print(f"invalidated {line} · {'replay deleted' if had else 'had no replay'} · {invalid[line]}")
    write_index(d, index)
    write_index(d, invalid, "invalidated.json")


def passed_in(report):
    """The lines a batch report's `pass · …` row names, before its REPLAY: summary."""
    try:
        with open(report, encoding="utf-8-sig") as fh:
            for row in fh:
                if row.startswith("REPLAY:"):
                    break
                if row.startswith("pass · "):
                    return row[len("pass · "):].split()
    except OSError as e:
        sys.exit(f"ABORT: --from {report}: {e}")
    return []


def cmd_audit(a):
    if not 0 < a.rate <= 1:
        sys.exit("ABORT: --rate is above 0 and at most 1")
    skip = set(split_lines(a.skip))
    pool = sorted((l for l in passed_in(a.source) if l not in skip), key=order)
    if not pool:
        print("AUDIT: none · no line passed by replay alone")
        return
    k = min(len(pool), max(1, round(a.rate * len(pool))))
    rng = random.Random(a.seed) if a.seed is not None else random.SystemRandom()
    picked = sorted(rng.sample(pool, k), key=order)
    print(f"AUDIT: {' '.join(picked)} · {k} of {len(pool)} passed by replay")


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
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("save")
    p.add_argument("--feature", required=True)
    p.add_argument("--from", dest="source", required=True)
    p.add_argument("--clauses", required=True)
    p.add_argument("--base-check")
    p.add_argument("--no-base")
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
    p = sub.add_parser("batch")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--feature")
    g.add_argument("--from", dest="source")
    p.add_argument("--base", action="store_true")
    p.add_argument("--spec")
    p.add_argument("--clauses", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--checkout", default=os.getcwd())
    p.add_argument("--run")
    p.add_argument("--env", action="append")
    p.add_argument("--lines")
    p.set_defaults(fn=cmd_batch)
    p = sub.add_parser("list")
    p.add_argument("--feature", required=True)
    p.set_defaults(fn=cmd_list)
    p = sub.add_parser("invalidate")
    p.add_argument("--feature", required=True)
    p.add_argument("--lines", required=True)
    p.add_argument("--why", required=True)
    p.add_argument("--retired", action="store_true")
    p.set_defaults(fn=cmd_invalidate)
    p = sub.add_parser("audit")
    p.add_argument("--from", dest="source", required=True)
    p.add_argument("--skip")
    p.add_argument("--rate", type=float, default=0.2)
    p.add_argument("--seed", type=int)
    p.set_defaults(fn=cmd_audit)
    p = sub.add_parser("clear")
    p.add_argument("--feature", required=True)
    p.set_defaults(fn=cmd_clear)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
