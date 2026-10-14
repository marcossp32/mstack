"""Shared helpers. State lives in the git common dir, never in the checkout."""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# Output that means the test never reached its assertion.
SETUP_FAILURE = (
    "importerror", "modulenotfounderror", "attributeerror", "nameerror",
    "syntaxerror", "is not defined", "has no attribute", "cannot find module",
    "cannot find symbol", "undefined reference", "no such module",
    "unresolved import", "cannot import name", "is not a function",
    "collection error", "errors during collection", "no tests ran",
    "no tests found", "command not found", "is not recognized as",
)
# Output that means an assertion ran and failed. Heuristic, runner-dependent.
ASSERTION = ("assertionerror", "assertion failed", "assertionfailed", "assert ",
             "expected:", "received:", "toequal", "tobe(", "tostrictequal",
             "not equal", "comparisonfailure", "assert_eq", "--- fail")

TEST_PATH = re.compile(
    r"(^|/)(tests?|__tests__|specs?)/"
    r"|(^|/)test_[^/]*\.py$|_test\.(py|go|rb|exs?)$"
    r"|\.(test|spec)\.[cm]?[jt]sx?$|_spec\.rb$|Tests?\.(cs|java|kt|swift)$"
)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def die(msg, code=1):
    print(f"ABORT: {msg}", file=sys.stderr)
    sys.exit(code)


CONTAIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contain.py")
# The interpreter itself, not a venv or `py` launcher in front of it: contain
# watches its parent, and a launcher outlives the script that started it.
PYTHON = getattr(sys, "_base_executable", None) or sys.executable

# Ceilings. Reaching one is never a failure: the run is reported as not
# finished, and nothing is judged on it. They exist so a hung run ends
# instead of holding the whole feature forever.
FIRST_RUN = 7200    # seconds, when nothing has been measured yet
SUITE_FLOOR = 1800  # a suite gets at least this, else 3 times its last run
FILE_FLOOR = 300    # one test file gets at least this
FACTOR = 3
TIMEOUT_RC = 124


def ceiling(measured, floor):
    """FACTOR times a measured run, never under floor; FIRST_RUN if unmeasured."""
    if measured is None:
        return FIRST_RUN
    return max(floor, int(FACTOR * measured))


def timed_out(rc, out):
    return rc == TIMEOUT_RC and "contain: TIMEOUT" in out


def sh(cmd, cwd=None, timeout=None, env=None, contain=True):
    """Runs a shell command, contained: when it exits, times out, or this
    script dies, everything it started ends too. On Windows, killing the shell
    alone leaves its children running and holding the output pipes.

    A timeout here is a ceiling: check timed_out() and report the run as not
    finished, never as a failure."""
    argv = cmd
    if contain:
        argv = [PYTHON, CONTAIN, "--with-parent", "--shell", cmd]
        if timeout:
            argv[2:2] = ["--timeout", str(timeout)]
    try:
        p = subprocess.run(argv, shell=not contain, cwd=cwd, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=timeout + 60 if contain and timeout else timeout,
                           env={**os.environ, **env} if env else None)
    except subprocess.TimeoutExpired:
        return TIMEOUT_RC, "contain: TIMEOUT · the wrapper itself did not return"
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def timed(cmd, cwd=None, timeout=None, env=None):
    """sh(), plus how long it took in seconds."""
    start = time.monotonic()
    rc, out = sh(cmd, cwd=cwd, timeout=timeout, env=env)
    return rc, out, time.monotonic() - start


class NotRun(Exception):
    """A run hit its ceiling: report it as not finished and judge nothing."""


def sweep():
    """Ends what an earlier run left behind in this repo (contained trees whose
    owner is gone) and orphaned automation browsers, so they neither slow this
    run nor skew its timing. Returns contain.py's summary lines."""
    try:
        _, common = git("rev-parse --path-format=absolute --git-common-dir")
        p = subprocess.run([PYTHON, CONTAIN, "sweep", "--kill", "--within", root(),
                            "--within", common],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=180)
        out = (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        out = "timed out"
    lines = [l for l in out.splitlines() if l.startswith(("SWEEP:", "REAP:"))]
    return " · ".join(lines) if lines else "SWEEP: not run · " + tail(out.strip(), 200)


def git(args, cwd=None):
    rc, out = sh(f"git {args}", cwd=cwd, timeout=120, contain=False)
    return rc, out.strip()


def root():
    rc, out = git("rev-parse --show-toplevel")
    if rc != 0:
        die("not a git repository")
    return out


def state_dir(*parts):
    rc, out = git("rev-parse --path-format=absolute --git-common-dir")
    if rc != 0:
        die("cannot resolve the git dir (needs git 2.31 or newer)")
    path = os.path.join(out, "mstack", *parts)
    os.makedirs(path, exist_ok=True)
    return path


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return None


def write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def tracked_changes(cwd=None):
    """Modified or staged tracked files. Untracked files are ignored."""
    _, out = git("status --porcelain --untracked-files=no", cwd=cwd)
    return out


def reached_assertion(output):
    low = output.lower()
    return any(a in low for a in ASSERTION)


def setup_failure(output):
    low = output.lower()
    return any(m in low for m in SETUP_FAILURE) and not reached_assertion(output)


def tail(text, n=1500):
    return text[-n:]
