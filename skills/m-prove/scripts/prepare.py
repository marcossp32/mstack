#!/usr/bin/env python3
"""Prepare a prove: everything before the first drive that needs no judgement.

  prepare.py --evidence <evidence dir> [--spec <run.json>] [--checkout <dir>]
             [--base-branch <name> | --base <sha>] [--recipe <recipe SKILL.md>] [--no-launch]

--spec defaults to <evidence dir>/run.json, then <git common dir>/mstack/run.json
(runspec.py --help). --checkout defaults to the current directory.
In order, each step one line of output, its full output in <evidence dir>/prepare/:
  stale      cleanup.py --stale: evidence dirs of runs that died before their cleanup
  sweep      contain.py sweep --kill --within <checkout>: what earlier runs left running here
  clean      `git status --porcelain` empty, else stop: PREPARE: DIRTY, exit 2;
             `git status --porcelain --ignored` saved to <evidence dir>/ignored-before.txt
  recipe     with --recipe: a warning when its SKILL.md is over 150 lines (compact it)
  base sha   with --base-branch: `git fetch origin <name>` (the local branch when that fails),
             then the merge-base with HEAD, printed as `base sha · <sha>` for the contract
  base       final mode: a detached worktree at <evidence dir>/base, the env files the
             checkout ignores copied in, then installed and built alongside the head
  install    the spec's install lines, then build, in the checkout (contained, each line cut
             after the spec's build_timeout, default 3600 s)
  clean      again after the build: a build that changes tracked files is a recipe trap
  launch     the app started, up on its health check, stopped (skipped by --no-launch, or
             when the spec has no launch)
Last line, always: PREPARE: OK | FAIL · <what failed, which log> | DIRTY, with the seconds.
Exit 0, 1 or 2. Run it in the background: the harness says when it exits.
"""
import argparse
import fnmatch
import os
import shutil
import subprocess
import sys
import threading
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import runspec  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEP_DIRS = {"node_modules", ".venv", "venv", "vendor", "target", ".git", "dist", "build"}
RECIPE_CAP = 150
T0 = time.monotonic()


def git(args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def say(msg):
    print(msg, flush=True)


def done(word, code):
    say(f"PREPARE: {word} · {round(time.monotonic() - T0)}s")
    sys.exit(code)


def build(spec, where, port, log):
    """Install then build in one tree. Returns (ok, line); never raises."""
    total = 0
    timeout = spec.get("build_timeout", runspec.BUILD_TIMEOUT)
    for key in ("install", "build"):
        for line in spec.get(key, []):
            rc, last, secs = runspec.shell(line, spec, where, port, log, timeout=timeout)
            total += secs
            if rc != 0:
                why = "timed out" if rc == 124 else f"exit {rc}"
                return False, f"{key} · fail {why} after {secs}s · {last}"
    return True, f"install+build · ok {total}s"


def env_files(spec, ignored, checkout):
    """Ignored files a fresh worktree lacks and the app reads: the spec's, else .env*."""
    wanted = spec.get("env_files")
    out = []
    for path in ignored:
        parts = path.rstrip("/").split("/")
        if wanted is not None:
            if any(fnmatch.fnmatch(path, w) for w in wanted):
                out.append(path)
        elif parts[-1].startswith(".env") and not DEP_DIRS & set(parts[:-1]) \
                and os.path.isfile(os.path.join(checkout, path)):
            out.append(path)
    return out


def base_sha(branch, checkout):
    p = git(["fetch", "--quiet", "origin", branch], checkout)
    ref, note = f"origin/{branch}", ""
    if p.returncode != 0:
        ref, note = branch, " · fetch failed, local branch used"
    m = git(["merge-base", ref, "HEAD"], checkout)
    if m.returncode != 0:
        say(f"base sha · none · no merge-base of {ref} and HEAD{note}")
        done("FAIL · base sha", 1)
    sha = m.stdout.strip()
    say(f"base sha · {sha} · merge-base of {ref} and HEAD{note}")
    return sha


def prepare(a, step):
    checkout, ev = os.path.realpath(a.checkout), os.path.realpath(a.evidence)
    logs = os.path.join(ev, "prepare")
    os.makedirs(logs, exist_ok=True)
    step[0] = "run spec"
    spec_path = runspec.locate(a.spec, ev, checkout)
    spec = runspec.load(spec_path)
    say(f"spec · {spec_path}")

    step[0] = "stale sweep"
    p = subprocess.run([runspec.PYTHON, os.path.join(HERE, "cleanup.py"), "--stale"],
                       cwd=checkout, capture_output=True, text=True)
    say(f"stale · {sum(1 for l in p.stdout.splitlines() if l.startswith('deleted'))} deleted")

    step[0] = "process sweep"
    p = subprocess.run([runspec.PYTHON, runspec.CONTAIN, "sweep", "--kill", "--within", checkout],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    with open(os.path.join(logs, "sweep.txt"), "w", encoding="utf-8") as fh:
        fh.write(p.stdout + p.stderr)
    summary = " · ".join(l for l in p.stdout.splitlines() if l.startswith(("REAP", "SWEEP")))
    say(f"sweep · {summary or 'done'}")

    step[0] = "clean check"
    status = git(["status", "--porcelain"], checkout).stdout.splitlines()
    if status:
        say(f"clean · no · {len(status)} paths: " + ", ".join(s[3:] for s in status[:5]))
        done("DIRTY", 2)
    ignored = git(["status", "--porcelain", "--ignored"], checkout).stdout
    with open(os.path.join(ev, "ignored-before.txt"), "w", encoding="utf-8") as fh:
        fh.write(ignored)
    say("clean · yes · ignored-before.txt saved")

    if a.recipe:
        try:
            with open(a.recipe, encoding="utf-8", errors="replace") as fh:
                n = sum(1 for _ in fh)
            say(f"recipe · {n} lines" + (f" · WARNING over {RECIPE_CAP}: compact it into the "
                                         "main file and surfaces/ before adding to it"
                                         if n > RECIPE_CAP else ""))
        except OSError as e:
            say(f"recipe · unreadable · {e}")

    step[0] = "base sha"
    sha = base_sha(a.base_branch, checkout) if a.base_branch else a.base
    result, thread = {"ok": False, "line": "not built", "copied": []}, None
    if sha:
        step[0] = "base worktree"
        base = os.path.join(ev, "base")
        p = git(["worktree", "add", "--detach", base, sha], checkout)
        if p.returncode != 0:
            result["line"] = "git worktree add failed: " + (p.stderr.strip().splitlines() or [""])[-1]
        else:
            paths = [l[3:].strip('"') for l in ignored.splitlines() if l.startswith("!! ")]
            try:
                for rel in env_files(spec, paths, checkout):
                    dst = os.path.join(base, rel)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(os.path.join(checkout, rel), dst)
                    result["copied"].append(rel)
            except OSError as e:
                say(f"base · env file copy failed · {e}")

            def build_base():
                try:
                    result["ok"], result["line"] = build(spec, base, spec.get("port"),
                                                         os.path.join(logs, "base.log"))
                except Exception as e:  # a thread's failure must not hide the PREPARE line
                    result["line"] = f"fail · {type(e).__name__}: {e}"
            thread = threading.Thread(target=build_base)
            thread.start()

    step[0] = "install/build head (prepare/head.log)"
    ok, line = build(spec, checkout, spec.get("port"), os.path.join(logs, "head.log"))
    say(f"head {line}")
    if thread:
        thread.join()
    if sha:
        say(f"base · {os.path.join(ev, 'base')} · env files {len(result['copied'])} · "
            f"{result['line']}" + ("" if result["ok"] else " · prepare/base.log"))
    if not ok:
        done("FAIL · install/build head (prepare/head.log)", 1)

    step[0] = "clean check after build"
    after = git(["status", "--porcelain"], checkout).stdout.splitlines()
    if after:
        say(f"clean after build · no · {len(after)} paths: " + ", ".join(s[3:] for s in after[:5]))
        done("FAIL · the build changed the checkout", 1)
    say("clean after build · yes")

    step[0] = "launch (prepare/launch.log)"
    if not spec.get("launch"):
        say("launch · none in the spec · skipped")
    elif not a.no_launch:
        app = runspec.App(spec, checkout, os.path.join(logs, "launch.log"))
        try:
            up, secs, why = app.start()
        finally:
            app.stop()
        say(f"launch · {'up' if up else 'not up'} in {secs}s · {app.url}"
            + (f" · {why}" if why else "") + " · stopped")
        if not up:
            done("FAIL · launch (prepare/launch.log)", 1)
    if sha and not result["ok"]:
        done("OK · head only, base failed: Q2 builds its own", 0)
    done("OK", 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec")
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--checkout", default=os.getcwd())
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--base")
    g.add_argument("--base-branch")
    ap.add_argument("--recipe")
    ap.add_argument("--no-launch", action="store_true")
    a = ap.parse_args()
    step = ["start"]
    try:
        prepare(a, step)
    except SystemExit as e:
        if isinstance(e.code, str):  # an ABORT message from a helper
            say(e.code)
            done(f"FAIL · {step[0]}", 1)
        raise
    except Exception as e:
        say(f"error · {type(e).__name__}: {e}")
        traceback.print_exc()
        done(f"FAIL · {step[0]}", 1)


if __name__ == "__main__":
    main()
