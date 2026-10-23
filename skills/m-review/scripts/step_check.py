#!/usr/bin/env python3
"""Step check. Deterministic, no model judgement. Run it for its output.

Reads: the git diff from the merge-base with --base to HEAD, the step notes
file, and the baseline it recorded under <git common dir>/mstack/baseline/.
Prints, for check: one `- <note>` line per note (`sweep · …`, `suite logs ·
<paths>`, `flaky · …`, `unpinned? · …`, `credential placeholder · …`,
`pinned · …`), one `- FAIL <what>` line per failure, then a blank line and
exactly one of `STEP CHECK: PASS`, `STEP CHECK: FAIL`,
`STEP CHECK: NOT RUN · <why>`. An abort prints `ABORT: <reason>` to stderr and
no verdict line.

  step_check.py baseline --test-cmd "<cmd>" | --test-cmd none [--test-file-cmd "<cmd with {test}>"]
      Once, on the feature branch before the first step. Records the suite's
      state for that branch, so later steps can be compared against it, and
      the command that runs one test file, for the pinned check.

  step_check.py check --base origin/<feature branch> --notes <file> [--secrets-cmd "<cmd>"]
      Fetch first: a stale local feature branch puts earlier steps in the diff.
      After each build, on the step branch, with a clean checkout. --notes is
      the builder's step notes (markdown); its Tests changed and Pinned by
      sections are read. Without it nothing counts as listed.
      Exit 0 = PASS, 1 = FAIL, 2 = NOT RUN (a run hit its ceiling: no
      verdict, report it); an abort exits non-zero and prints no verdict.

  step_check.py set-cmd --base <feature branch> --test-cmd "<cmd>"
      Swaps the suite command of the recorded baseline (e.g. fewer files at
      once after an unstable-under-load NOT RUN); keeps its verdict.

  step_check.py clear --base <feature branch>
      When the feature ends. Deletes its baseline, nothing else.

Checks:
  1. Suite no worse than at the feature's start: red where it was green, or,
     where it was red, failing on a file that was not failing then. The
     worse files run alone first: one that fails alone fails the step. All
     pass alone: a second suite run. Not worse then: a file this step changed
     is a FAIL marked intermittent, others a `flaky` note. A file worse on
     both runs is a FAIL (they depend on running together); different files
     each run, none changed by the step, is NOT RUN · suite unstable under
     load. No failing file found: the suite runs up to 3 times, as red on
     some runs only is intermittent. Every run's full output is saved under
     the git dir and its path printed.
  2. Every existing test file changed or deleted, and every file where the
     step adds a skip, a focus, a suppression or an exclusion, is listed in
     the notes' Tests changed section.
  3. No credentials in the added lines: a key-shaped secret, a literal
     assigned to a secret-like name, a password in a URL to another host or
     a committed .env fails; the value belongs in an environment variable.
     A key-shaped value that says it is not real is a note.
  4. Pinned: each test file the notes' Pinned by section lists passes at HEAD
     and fails with the step's non-test changes reverted. A step that changes
     code needs one, or `none · <why>` there.
"""
import argparse
import os
import re
import subprocess
import sys
import time

from common import (FILE_FLOOR, FIRST_RUN, SUITE_FLOOR, TEST_PATH, NotRun,
                    ceiling, die, git, now, read_json, reached_assertion, root,
                    setup_failure, sh, state_dir, sweep, tail, timed,
                    timed_out, tracked_changes, write_json)

SECRETS = [
    ("private key", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("AWS access key", r"\bAKIA[0-9A-Z]{16}\b"),
    ("GitHub token", r"\bgh[pousr]_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{22,}"),
    ("Slack token", r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    ("Stripe live key", r"\b[rs]k_live_[0-9a-zA-Z]{20,}"),
    ("Google API key", r"\bAIza[0-9A-Za-z_\-]{35}\b"),
    ("Anthropic key", r"\bsk-ant-[A-Za-z0-9_\-]{20,}"),
    ("OpenAI key", r"\bsk-(proj-)?[A-Za-z0-9_\-]{32,}"),
    ("SendGrid key", r"\bSG\.[A-Za-z0-9_\-]{22}\.[A-Za-z0-9_\-]{43}\b"),
]
# A key-shaped value that says it is not real (AWS's documented
# AKIAIOSFODNN7EXAMPLE) is a note, not a FAIL: nothing could accept it.
PLACEHOLDER = re.compile(r"(?i)example|dummy|fake|placeholder|changeme|(?<![a-z])test(?![a-z])")
# The rest are `credential?`: likely secrets, which fail the step too.
SECRET_NAME = (r"(?i)(password|passwd|secret(?:[_-]?key)?|api[_-]?key"
               r"|access[_-]?token|auth[_-]?token)\s*[:=]\s*")
SUSPECT = re.compile(SECRET_NAME + r"['\"]([^'\"\s]{8,})['\"]")
# In config files a value needs no quotes; in code an unquoted value is an
# expression (process.env.X), so it is matched there quoted only.
SUSPECT_BARE = re.compile(SECRET_NAME + r"([^\s'\"$%{<#][^\s'\"#]{7,})\s*(#.*)?$")
CONFIG_FILE = re.compile(r"(^|/)\.env(\.[^/]*)?$|\.(ya?ml|ini|cfg|conf|properties"
                         r"|toml|env)$", re.IGNORECASE)
URL_CREDENTIAL = re.compile(r"(?i)\b[a-z][a-z0-9+.\-]*://[^\s:/@'\"]*:"
                            r"([^\s@'\"/$%{]{3,})@")
# A password for a database on this machine (docker-compose, a dev .env) is
# a dev default, not a secret; a parked step would cost an unattended run.
LOCAL_HOST = re.compile(r"(?i)(localhost|127\.0\.0\.1|\[::1\])(?![.\w-])")
ENV_FILE = re.compile(r"(^|/)\.env(\.[^/]+)?$")
ENV_TEMPLATE = re.compile(r"\.(example|sample|template)$", re.IGNORECASE)

# Test runner config files: `exclude` there drops tests from the run, while
# elsewhere (tsconfig, a linter, a bundler) it means something else.
RUNNER_CONFIG = re.compile(
    r"(^|/)(vitest|jest|playwright|cypress|karma)\.config\.[cm]?[jt]s$"
    r"|(^|/)vitest\.workspace\.[cm]?[jt]s$|(^|/)jest\.config\.json$"
    r"|(^|/)\.mocharc(\.[a-z]+)?$")

# Lines that make a check stop checking. Counted per file, added minus
# removed, so code that only moves is not flagged. A third element limits
# the pattern to the paths it matches.
LOOSENERS = [
    ("excluded", re.compile(
        r"--deselect\b|--exclude\b|--ignore(-glob)?(=|\s+)(?!-)\S"
        r"|(^|[\s'\"\[,])-k['\"]?[\s=,]+\\?['\"]?([^'\"\n]*?\s)?not\s"
        r"|\bcollect_ignore(_glob)?\b|\btestPathIgnorePatterns\b|\btestIgnore\b")),
    # coverage.exclude only drops files from the coverage report.
    ("excluded", re.compile(r"^(?!.*\bcoverage\b).*\bexclude\b"), RUNNER_CONFIG),
    ("skip", re.compile(
        r"\b(it|test|describe|context|suite)\.(skip|todo)\b|\b(xit|xdescribe|xtest)\s*\("
        r"|@pytest\.mark\.(skip|xfail)|\bpytest\.skip\(|@unittest\.skip|\bskipTest\("
        r"|@Disabled\b|@Ignore\b|\bt\.Skip(Now|f)?\(|#\[ignore\]")),
    ("focus", re.compile(
        r"\b(it|test|describe|context|suite)\.only\b|\b(fit|fdescribe)\s*\(")),
    ("suppression", re.compile(
        r"@ts-(ignore|nocheck|expect-error)|eslint-disable|biome-ignore|#\s*noqa\b"
        r"|#\s*type:\s*ignore|pylint:\s*disable|//\s*nolint|#\[allow\(|@SuppressWarnings"
        r"|rubocop:disable|@phpstan-ignore|NOSONAR|pragma:\s*no cover"
        r"|(istanbul|c8|v8)\s+ignore")),
    ("check bypassed", re.compile(
        r"\|\|\s*true\b|continue-on-error:\s*true|--passWithNoTests|--no-verify")),
]

# Files that carry no behaviour a test could pin.
DOC_PATH = re.compile(r"\.(md|mdx|rst|txt|adoc)$|(^|/)(LICENSE|CHANGELOG)[^/]*$",
                      re.IGNORECASE)
# Dependency manifests and the files that pin installed versions. Reverting
# them leaves what they installed in place, so a test cannot be judged on it.
MANIFEST = re.compile(r"(^|/)(package\.json|pyproject\.toml|Pipfile|Cargo\.toml|go\.mod"
                      r"|Gemfile|composer\.json)$")
LOCKFILE = re.compile(r"(^|/)(package-lock\.json|npm-shrinkwrap\.json|yarn\.lock"
                      r"|pnpm-lock\.yaml|bun\.lockb?|Pipfile\.lock|poetry\.lock|uv\.lock"
                      r"|requirements[^/]*\.(txt|in)|Cargo\.lock|go\.sum|Gemfile\.lock"
                      r"|composer\.lock|packages\.lock\.json)$")
# Output that says a service the suite needs is not running.
PREREQUISITE = re.compile(r"(?i)econnrefused|connection refused|could not connect to"
                          r"|can't connect to|failed to connect to")
# Left in the git dir while the step's changes are reverted: a check killed
# then is recognised and its revert undone by the next one.
REVERT_MARKER = "mstack-pinned-revert.json"

SUITE_RUNS = 3
LOG_DAYS = 7
# A red suite's failing files are run alone first, up to this many.
MAX_ALONE = 30
FAIL_MARK = re.compile(r"(?i)\b(fail|failed|failing|failures?|error)\b|[✖✗×]")
PASS_MARK = re.compile(r"\b(PASS|PASSED)\b|^\s*ok\b|[✔✓]")
FAIL_WINDOW = 3


def run_git(args, cwd):
    """git with an argument list: paths reach it unquoted on every platform."""
    p = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()


def save_log(label, run, out):
    """The suite's full output, kept so a FAIL never needs a rerun to read.
    Logs older than LOG_DAYS go: by then their step was fixed or abandoned."""
    d = state_dir("check")
    cutoff = time.time() - LOG_DAYS * 86400
    for name in os.listdir(d):
        old = os.path.join(d, name)
        if name.endswith(".log") and os.path.getmtime(old) < cutoff:
            os.remove(old)
    stamp = now().replace(":", "")
    path = os.path.join(d, f"{label}-{stamp}-run{run}.log")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(out)
    return path


def baseline_path(branch):
    """One baseline per feature branch, so two features never share one."""
    if branch.startswith("origin/"):
        branch = branch[len("origin/"):]
    name = re.sub(r"[^A-Za-z0-9._-]", "_", branch)
    return os.path.join(state_dir("baseline"), f"{name}.json")


def cmd_baseline(a):
    r = root()
    rc, branch = git("rev-parse --abbrev-ref HEAD")
    if rc != 0 or branch == "HEAD":
        die("baseline runs on the feature branch, not a detached HEAD")
    if a.test_file_cmd and "{test}" not in a.test_file_cmd:
        die("--test-file-cmd must contain {test}, replaced by the file to run")
    _, head = git("rev-parse HEAD")
    if a.test_cmd == "none":
        data = {"cmd": None, "rc": None, "head": head, "created": now()}
        print("baseline: no test suite")
    else:
        print(f"running {a.test_cmd} ...")
        rc, out, secs = timed(a.test_cmd, cwd=r, timeout=FIRST_RUN)
        if timed_out(rc, out):
            die(f"NOT RUN · the suite did not finish within {FIRST_RUN}s: no "
                "baseline recorded\n" + tail(out, 1500), 2)
        # A setup failure in one file among others is a red test like any
        # other; one no test file shows means the suite never ran.
        if rc != 0 and (PREREQUISITE.search(out)
                        or (setup_failure(out) and not failing_files(out, r)
                            and not PASS_MARK.search(out))):
            # Every later step would be red for the same reason, and judged
            # against a suite that never ran.
            die("the suite fails before its tests run at the feature's start (a "
                "missing module, a service not running): start the prerequisites "
                "first, or fix the test command, then record the baseline again\n"
                + tail(out, 1500))
        data = {"cmd": a.test_cmd, "rc": rc, "head": head, "created": now(),
                "seconds": round(secs, 1), "tail": tail(out, 4000)}
        if rc == 0:
            print(f"baseline: suite green at {head[:12]}")
        else:
            data["failing"] = failing_files(out, r)
            print(f"baseline: suite red at {head[:12]} · failing · "
                  + (", ".join(data["failing"]) or "no file found in its output: "
                     "later steps cannot be compared"))
    data["file_cmd"] = a.test_file_cmd
    data["branch"] = branch
    write_json(baseline_path(branch), data)
    print(f"baseline for {branch}")


def notes_section(path, title):
    """A `## <title>` section of the step notes file, or "" when absent."""
    try:
        with open(path, encoding="utf-8") as fh:
            body = fh.read()
    except OSError as e:
        die(f"cannot read the step notes {path}: {e}")
    m = re.search(rf"^##\s*{title}\s*$(.*?)(^##\s|\Z)", body,
                  re.MULTILINE | re.DOTALL | re.IGNORECASE)
    return m.group(1) if m else ""


def failing_files(out, r):
    """Tracked test files the suite's output names near a failure marker.
    Runner-agnostic and heuristic: a passing file caught here only costs one
    run on its own; none found falls back to whole-suite reruns."""
    _, tracked = run_git(["ls-files"], r)
    tests = [p for p in tracked.splitlines() if TEST_PATH.search(p)]
    lines = out.splitlines()
    near = set()
    for i, line in enumerate(lines):
        if FAIL_MARK.search(line):
            near.update(range(max(0, i - FAIL_WINDOW), i + FAIL_WINDOW + 1))
    # A line that reports a pass names a file that did not fail there.
    text = "\n".join(lines[i] for i in sorted(near)
                     if i < len(lines) and not PASS_MARK.search(lines[i]))
    return sorted(p for p in tests
                  if p in text or p.replace("/", "\\") in text)


def alone(cmd, files, r, limit):
    """Each file run on its own: the ones that fail that way, and the ones
    that hit their ceiling, which judges nothing about them."""
    bad, hung = [], []
    for path in files:
        rc, out, _ = run_pinned(cmd, path, r, limit)
        if timed_out(rc, out):
            hung.append(path)
        elif rc != 0:
            bad.append(path)
    return bad, hung


def check_suite(a, base_info, r, changed, fails, notes):
    if base_info["cmd"] is None:
        notes.append("suite · none in this repo")
        return
    limit = ceiling(base_info.get("seconds"), SUITE_FLOOR)

    def suite(run):
        rc, out, secs = timed(base_info["cmd"], cwd=r, timeout=limit)
        if timed_out(rc, out):
            raise NotRun(f"the suite did not finish within {limit}s, 3 times its "
                         f"baseline run or more · log {save_log(a.label, run, out)}")
        if base_info.get("seconds") is None:
            # set-cmd cleared it: the first finished run sets the ceiling.
            base_info["seconds"] = round(secs, 1)
            write_json(baseline_path(a.base), base_info)
        return rc, out

    rc, out = suite(1)
    if rc == 0:
        notes.append("suite · green")
        return
    logs = [save_log(a.label, 1, out)]
    try:
        judge_red(a, base_info, r, changed, fails, notes, suite, rc, out, logs)
    finally:
        notes.append("suite logs · " + " · ".join(logs))


def judge_red(a, base_info, r, changed, fails, notes, suite, rc, out, logs):
    # A red start is compared file by file: the files failing then may fail
    # now, and only another failing file makes the suite worse.
    red_start = base_info["rc"] != 0
    known = set(base_info.get("failing") or [])
    start = ("was green at the feature's start" if not red_start else
             "on files that passed at the feature's start")

    def worse(rc, out):
        """The failing files beyond the start's: [] is no worse. None: red
        from a green start with no file named, so none can run alone."""
        if rc == 0:
            return []
        named = failing_files(out, r)
        if not named:
            return None   # nothing to compare with the start's failing set
        return sorted(set(named) - known)

    if red_start and not known:
        notes.append("suite · red, was already red at the feature's start, with "
                     "no failing file found in its output then: not comparable, "
                     "record it on the map")
        return
    first = worse(rc, out)
    if red_start and first == []:
        notes.append("suite · red on the files already failing at the feature's "
                     "start: " + ", ".join(sorted(known)))
        return

    file_cmd = base_info.get("file_cmd")
    if not file_cmd or not first or len(first) > MAX_ALONE:
        rerun_suite(suite, worse, out, logs, fails, a.label, start)
        return

    # Run the failing files on their own first: a file that fails alone is a
    # real failure, found without two more whole-suite runs.
    file_limit = ceiling(base_info.get("seconds"), FILE_FLOOR)
    bad, hung = alone(file_cmd, first, r, file_limit)
    if bad:
        fails.append("suite · red, and fails alone too: " + ", ".join(bad)
                     + "\n" + tail(out, 2500))
        return
    if hung:
        raise NotRun(f"{', '.join(hung)} failed in the suite and did not finish "
                     f"alone within {file_limit}s: nothing judged")

    rc2, out2 = suite(2)
    if rc2 != 0:
        logs.append(save_log(a.label, 2, out2))
    second = worse(rc2, out2)
    if second == []:
        touched = sorted(set(first) & changed)
        code = [p for p in changed if not TEST_PATH.search(p) and not DOC_PATH.search(p)]
        if touched or code:
            why = ("this step changed them" if touched else
                   "this step changed code they may load: "
                   + ", ".join(sorted(code)[:5]))
            fails.append("suite · intermittent · red 1 of 2 runs, " + start
                         + f"; {', '.join(first)} pass alone, and {why}\n"
                         + tail(out, 2500))
        else:
            # The step changed no code: someone else's flaky test.
            notes.append(f"flaky · {', '.join(first)} · red on 1 of 2 suite runs, "
                         "passes alone, not changed by this step")
        return
    if not second:
        fails.append("suite · red 2 of 2 runs, " + start + "; the second run's "
                     "output names no failing file, and the first run's pass alone: "
                     + ", ".join(first) + "\n" + tail(out2, 2500))
        return
    both = sorted(set(first) & set(second))
    if both:
        fails.append("suite · red 2 of 2 runs on " + ", ".join(both)
                     + ", which pass alone: they depend on running together\n"
                     + tail(out2, 2500))
        return
    bad, hung = alone(file_cmd, second, r, file_limit)
    touched = sorted((set(first) | set(second)) & changed)
    if bad:
        fails.append("suite · red, and fails alone too: " + ", ".join(bad)
                     + "\n" + tail(out2, 2500))
    elif touched:
        fails.append("suite · red on 2 runs, on files this step changed: "
                     + ", ".join(touched) + "\n" + tail(out2, 2500))
    elif hung:
        raise NotRun(f"{', '.join(hung)} failed in the suite and did not finish "
                     f"alone within {file_limit}s: nothing judged")
    else:
        raise NotRun("suite unstable under load: each run fails on different "
                     f"files ({', '.join(first)} · then {', '.join(second)}), "
                     "every one passes alone, and this step changed none of "
                     "them. Run fewer test files at once: set-cmd")


def rerun_suite(suite, worse, out, logs, fails, label, start):
    """No failing file to run alone: run the whole suite again, up to 3 times."""
    reds = [out]
    for i in range(2, SUITE_RUNS + 1):
        rc_i, out_i = suite(i)
        logs.append(save_log(label, i, out_i))
        if worse(rc_i, out_i) != []:
            reds.append(out_i)
    runs = f"red {len(reds)} of {SUITE_RUNS} runs"
    if len(reds) == SUITE_RUNS:
        fails.append(f"suite · {runs}, {start}\n" + tail(out, 2500))
    else:
        fails.append(f"suite · intermittent · {runs}, {start}\n"
                     + tail(reds[0], 2500))


def check_listed(a, status, diff, listed, fails, notes):
    """Existing tests changed, and skips or suppressions added: each listed."""
    flagged = []
    for code, path in status:
        if code in ("M", "D") and TEST_PATH.search(path):
            flagged.append((path, f"test changed · {code} {path}"))

    # Per file and kind, added minus removed: a line that only moves nets zero.
    counts, current, in_hunk = {}, None, False
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            in_hunk = False
            continue
        if not in_hunk:
            if line.startswith("+++ "):
                current = line[6:] if line.startswith("+++ b/") else None
            in_hunk = line.startswith("@@")
            continue
        if line.startswith("@@") or line[:1] not in ("+", "-") or current is None:
            continue
        sign = 1 if line[0] == "+" else -1
        kinds = {kind for kind, pat, *where in LOOSENERS
                 if (not where or where[0].search(current)) and pat.search(line[1:])}
        for kind in kinds:
            counts[(current, kind)] = counts.get((current, kind), 0) + sign
    for (path, kind), n in sorted(counts.items()):
        if n > 0:
            flagged.append((path, f"loosened · {kind} · {path} · {n} added"))

    if not flagged:
        notes.append("tests changed · none")
        return
    for path, line in flagged:
        if a.notes and path in listed:
            notes.append(f"{line} · listed in the notes")
        else:
            fails.append(f"{line} · not listed in the step notes' Tests changed "
                         "section")


def check_credentials(a, r, status, diff, fails, notes):
    current, found, suspects, placeholders = None, False, [], []

    def suspect(what, path):
        # Nobody reviews it before the run goes on: the builder moves the
        # value to an environment variable instead.
        line = (f"credential? · {what} · {path} · move the value to an "
                "environment variable")
        if line not in suspects:
            suspects.append(line)

    def placeholder(what, path):
        # Says it is not real, so nothing could accept it; still shown.
        line = f"credential placeholder · {what} · {path}"
        if line not in placeholders:
            placeholders.append(line)

    for code, path in status:
        name = path.rsplit("/", 1)[-1]
        if code == "A" and ENV_FILE.search(name) and not ENV_TEMPLATE.search(name):
            suspect("env file committed", path)
    for line in diff.splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else None
            continue
        if not line.startswith("+") or current is None:
            continue
        for name, pat in SECRETS:
            for m in re.finditer(pat, line):
                if PLACEHOLDER.search(m.group(0)):
                    placeholder(name, current)
                else:
                    fails.append(f"credential · {name} · {current} · move the "
                                 "value to an environment variable")
                    found = True
        values = [m.group(2) for m in SUSPECT.finditer(line)]
        if CONFIG_FILE.search(current):
            values += [m.group(2) for m in SUSPECT_BARE.finditer(line)]
        if any(not PLACEHOLDER.search(v) for v in values):
            suspect("literal assigned to a secret-like name", current)
        if any(not PLACEHOLDER.search(m.group(1)) and not LOCAL_HOST.match(line, m.end())
               for m in URL_CREDENTIAL.finditer(line)):
            suspect("password in a URL", current)
    fails.extend(suspects)
    notes.extend(placeholders)
    found = found or bool(suspects)
    if a.secrets_cmd:
        rc, out = sh(a.secrets_cmd, cwd=r, timeout=600)
        if timed_out(rc, out):
            notes.append("credentials · scanner not run · did not finish within 600s")
        elif rc != 0:
            fails.append("credential · secrets scanner failed\n" + tail(out, 1500))
            found = True
    if not found and not placeholders:
        notes.append("credentials · none found")


def pinned_files(section, r):
    """The tracked test files the Pinned by section names, or a none reason.
    Only test paths count: a code file named in a clause would otherwise be
    kept unreverted, and the test judged against the step's own code."""
    text = section.strip()
    m = re.match(r"^[-*\s]*none\b\s*[·:\-]*\s*(.*)", text, re.IGNORECASE)
    if m:
        return [], (m.group(1).splitlines()[0].strip() or "no reason given")
    _, tracked = run_git(["ls-files"], r)
    known = set(tracked.splitlines())
    found = []
    for tok in re.findall(r"`([^`]+)`|([^\s`·,()'\"]+)", text):
        path = (tok[0] or tok[1]).strip().replace("\\", "/")
        # A test id (tests/test_x.py::test_y) names its file.
        path = path.split("::")[0].rstrip(".:;")
        if path in known and TEST_PATH.search(path) and path not in found:
            found.append(path)
    return found, None


def run_pinned(cmd, path, r, limit):
    return timed(cmd.replace("{test}", path), cwd=r, timeout=limit)


def marker_path():
    """In this checkout's own git dir: the revert is of this checkout."""
    rc, d = git("rev-parse --absolute-git-dir")
    if rc != 0:
        die("cannot resolve the git dir")
    return os.path.join(d, REVERT_MARKER)


def undo_killed_revert(r):
    """A check killed during the pinned run leaves the step's non-test changes
    reverted and staged. Its marker names the files and the HEAD they belong
    to: restore exactly those, so the leftovers are never committed."""
    path = marker_path()
    mark = read_json(path)
    if mark is None:
        return
    _, head = git("rev-parse HEAD")
    if mark.get("head") != head:
        if not tracked_changes(r):
            os.remove(path)   # stale: that checkout was cleaned since
            return
        die(f"an interrupted step check reverted files at {mark.get('head', '')[:12]} "
            f"({', '.join(mark.get('files', []))}): check that commit out and run "
            "the check again, which restores them. Never commit them")
    files = mark.get("files", [])
    for i in range(0, len(files), 100):
        # restore, not checkout: a file the step deleted is absent at HEAD.
        rc, out = run_git(["restore", "--source", head, "--staged", "--worktree",
                           "--", *files[i:i + 100]], r)
        if rc != 0:
            die(f"cannot restore the files an interrupted step check reverted: {out}")
    os.remove(path)
    print(f"restored {len(files)} file(s) an interrupted step check had reverted")


def check_pinned(a, base_info, r, base, status, listed, fails, notes):
    code_changed = [p for c, p in status if not TEST_PATH.search(p)
                    and (LOCKFILE.search(p) or not DOC_PATH.search(p))]
    if not code_changed:
        notes.append("pinned · nothing to pin: the step changes only tests or docs")
        return
    if (all(MANIFEST.search(p) or LOCKFILE.search(p) for p in code_changed)
            and any(LOCKFILE.search(p) for p in code_changed)):
        notes.append("pinned · not judgeable · dependency change: reverting "
                     "manifests leaves installed what they installed")
        return
    if base_info["cmd"] is None:
        notes.append("pinned · not run · no test suite in this repo")
        return
    if not base_info.get("file_cmd"):
        notes.append("pinned · not run · no command that runs one test file: "
                      "record it with baseline --test-file-cmd")
        return
    files, reason = pinned_files(listed, r)
    if reason is not None:
        notes.append(f"unpinned? · none · {reason} · look before merging")
        return
    if not files:
        fails.append("pinned · nothing pins this step: list in the step notes' "
                     "Pinned by section a test file (a path a test runner finds: tests/, "
                     "*.test.*, test_*.py and the like) that fails without it, or "
                     "`none · <why>`")
        return

    cmd = base_info["file_cmd"]
    limit = ceiling(base_info.get("seconds"), FILE_FLOOR)
    at_head = {}
    for path in files:
        rc, out, secs = run_pinned(cmd, path, r, limit)
        # The exit code alone: a passing test may print any word.
        if timed_out(rc, out):
            notes.append(f"pinned · not run · {path} did not finish within {limit}s "
                         "at HEAD")
        elif rc != 0:
            fails.append(f"pinned · {path} · fails at HEAD\n" + tail(out, 1200))
        else:
            at_head[path] = secs
    if not at_head:
        return

    # Revert the step's non-test changes in place, keeping its tests and the
    # installed dependencies, then restore HEAD whatever happens.
    keep = set(files)
    revert = [p for c, p in status if c in ("M", "D")
              and not TEST_PATH.search(p) and p not in keep]
    added = [p for c, p in status if c == "A"
             and not TEST_PATH.search(p) and p not in keep]
    _, head = git("rev-parse HEAD")
    marker = marker_path()
    write_json(marker, {"head": head, "files": revert + added, "created": now()})
    try:
        for i in range(0, len(revert), 100):
            rc, out = run_git(["checkout", base, "--", *revert[i:i + 100]], r)
            if rc != 0:
                die(f"cannot revert the step's changes for the pinned check: {out}")
        for p in added:
            full = os.path.join(r, p)
            if os.path.exists(full):
                os.remove(full)
        for path, secs in at_head.items():
            cut = ceiling(secs, FILE_FLOOR)
            rc, out, _ = run_pinned(cmd, path, r, cut)
            if timed_out(rc, out):
                # It finished at HEAD and hangs without the step: what it
                # waits for is what the step delivers.
                notes.append(f"pinned · {path} · fails without the step: did not "
                             f"finish within {cut}s")
            elif rc == 0:
                fails.append(f"pinned · {path} · passes without this step: it pins "
                             "nothing this step changed")
            elif reached_assertion(out) or not setup_failure(out):
                notes.append(f"pinned · {path} · fails without the step")
            else:
                notes.append(f"pinned · {path} · fails without the step before any "
                             "assertion: new code")
    finally:
        rc, out = run_git(["reset", "-q", "--hard", "HEAD"], r)
        if rc != 0:
            die(f"cannot restore HEAD after the pinned check: {out}")
        os.remove(marker)


def cmd_check(a):
    r = root()
    base_info = read_json(baseline_path(a.base))
    if base_info is None:
        die(f"no baseline for {a.base}. On that branch, run: "
            "step_check.py baseline --test-cmd <cmd>")
    undo_killed_revert(r)
    if tracked_changes(r):
        die("tracked files differ from HEAD (git status): the check runs on the "
            "step exactly as pushed. Set them aside (git stash) or discard them, "
            "never commit them to get past this, and check again")

    rc, base = git(f"merge-base HEAD {a.base}")
    if rc != 0:
        die(f"cannot resolve merge-base with {a.base}")

    _, raw = run_git(["diff", "--name-status", "--no-renames", base, "HEAD"], r)
    status = [(ln.split("\t")[0][:1], ln.split("\t")[1].replace("\\", "/"))
              for ln in raw.splitlines() if "\t" in ln]
    _, diff = run_git(["diff", "-U0", "--no-renames", base, "HEAD"], r)
    tests_listed = notes_section(a.notes, "Tests changed") if a.notes else ""
    pinned_listed = notes_section(a.notes, "Pinned by") if a.notes else ""

    fails, notes = [], [f"sweep · {sweep()}"]
    try:
        check_suite(a, base_info, r, {p for _, p in status}, fails, notes)
        check_listed(a, status, diff, tests_listed, fails, notes)
        check_credentials(a, r, status, diff, fails, notes)
        check_pinned(a, base_info, r, base, status, pinned_listed, fails, notes)
    except NotRun as e:
        for n in notes:
            print(f"- {n}")
        print(f"\nSTEP CHECK: NOT RUN · {e}")
        sys.exit(2)

    for n in notes:
        print(f"- {n}")
    for f in fails:
        print(f"- FAIL {f}")
    print(f"\nSTEP CHECK: {'FAIL' if fails else 'PASS'}")
    sys.exit(1 if fails else 0)


def cmd_set_cmd(a):
    """Swaps the suite command of a recorded baseline, keeping its verdict and
    head; the next finished run measures the new command's time."""
    path = baseline_path(a.base)
    data = read_json(path)
    if data is None:
        die(f"no baseline for {a.base}: record one with baseline")
    if data.get("cmd") is None:
        die("this baseline has no test suite")
    print(f"suite command: {data['cmd']} -> {a.test_cmd}")
    data.update({"cmd": a.test_cmd, "seconds": None, "cmd_set": now()})
    write_json(path, data)


def cmd_clear(a):
    """Deletes a finished feature's baseline, nothing else."""
    path = baseline_path(a.base)
    if os.path.exists(path):
        os.remove(path)
        print(f"deleted {path}")
    else:
        print("nothing to delete")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("baseline")
    p.add_argument("--test-cmd", required=True,
                   help="the command that runs the whole suite, or 'none'")
    p.add_argument("--test-file-cmd",
                   help="the command that runs one test file, with {test} for its path")
    p.set_defaults(fn=cmd_baseline)
    p = sub.add_parser("check")
    p.add_argument("--base", required=True, help="the feature branch")
    p.add_argument("--notes", help="the step notes file m-build wrote, to read "
                   "its Tests changed and Pinned by sections")
    p.add_argument("--secrets-cmd", help="optional scanner; non-zero exit fails")
    p.set_defaults(fn=cmd_check)
    p = sub.add_parser("set-cmd")
    p.add_argument("--base", required=True, help="the feature branch")
    p.add_argument("--test-cmd", required=True,
                   help="the new command that runs the whole suite")
    p.set_defaults(fn=cmd_set_cmd)
    p = sub.add_parser("clear")
    p.add_argument("--base", required=True, help="the feature branch that ended")
    p.set_defaults(fn=cmd_clear)
    a = ap.parse_args()
    if getattr(a, "notes", None) is not None:
        a.notes = os.path.abspath(a.notes)
    # Names the step's suite logs.
    a.label = (re.sub(r"[^A-Za-z0-9._-]", "_",
                      os.path.splitext(os.path.basename(a.notes))[0])
               if getattr(a, "notes", None) else "nonotes")
    a.fn(a)


if __name__ == "__main__":
    main()
