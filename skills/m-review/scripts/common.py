"""Shared helpers. State lives in the git common dir, never in the checkout."""
import hashlib
import json
import os
import re
import subprocess
import sys
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


def sh(cmd, cwd=None, timeout=1800, env=None):
    try:
        p = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=timeout,
                           env={**os.environ, **env} if env else None)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"


def git(args, cwd=None):
    rc, out = sh(f"git {args}", cwd=cwd, timeout=120)
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
