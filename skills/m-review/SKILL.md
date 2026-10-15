---
name: m-review
description: "Reviews a change by execution: a script checks each build step, and a feature review reports only failures a frozen reproduction demonstrated. Use as the check and review stages of /m-feature, or to review any branch with a runnable test suite before it merges."
---

Judge a change only by what running code shows. A finding without a reproduction that failed at the gate does not exist: no confidence scores, no severity, no "possible issues". An empty report is the expected outcome, and a complete one.

The step check and recheck run where they are called. The feature review dispatches its own agents; from `/m-feature` it runs in a fresh agent, so its hunts stay out of the orchestrator's context, and returns only `report.py`'s output. With no Agent tool there, return `Review · not run · no Agent tool` and the caller runs it in its own chat.

Models are tiers: strong is the harness's most capable, standard its middle one. A tier that does not resolve runs on the session's model.

Scripts are in this skill's `scripts/` directory; run them with `python3` (`python` where `python3` is absent). If one aborts, stop and report its message. State lives in the git dir, never in the checkout. `step_check.py`, `prepare.py` and `gate.py` run the whole suite, `step_check.py` up to three times: start each with the Bash tool's `run_in_background` and read its output when the harness says it exited, so no run hits the tool's 10-minute limit. `sweep` and `REAP` lines in their output are cleanup of earlier runs, not findings. A run that hits its ceiling (3 times its last measured run, 30 minutes at least for a suite, 5 for one file) judges nothing: the step check prints `STEP CHECK: NOT RUN` and exits 2, `prepare.py` aborts, and the gate closes the finding `unjudgeable`. Report a NOT RUN as it is; never rerun it to get a verdict.

# Step check

After each build, on the step branch. No model judgement.

```bash
python3 scripts/step_check.py baseline --test-cmd "<scan Q6 suite | none>" --test-file-cmd "<scan Q6 one file, {test} for its path>"   # once, before the first step
git fetch origin && python3 scripts/step_check.py check --base origin/feature/<name> --pr <n>
python3 scripts/step_check.py clear --base feature/<name>   # once, when the feature ends
```

Return its output. `STEP CHECK: FAIL` lists what failed; `credential?` (a secret-like literal, a password in a URL, a committed `.env`, a key-shaped placeholder such as AWS's `…EXAMPLE`), `unpinned?` and `flaky` lines are for the human to look at and do not fail the step.

The baseline aborts when the suite fails before its tests run (a missing module, a service refusing connections): start the prerequisites or fix the test command, and record it again, since every step would be judged against a suite that never ran. A suite red for other reasons records its failing files; a step then fails only on a file failing beyond those.

The check reverts the step's non-test changes in place to run the Pinned by tests (the test paths that section names), so it aborts on a checkout with tracked changes and restores HEAD before it exits. A check killed mid-revert leaves a marker in the git dir, and the next check restores those files itself: never commit them. `pinned · not run` names what it lacked; `pinned · not judgeable · dependency change` means the step changes only manifests and lockfiles, a lockfile among them, and reverting them leaves what they installed, so prove judges it.

A red suite first runs the files its output names as failing on their own: one that fails alone fails the step without more suite runs. Otherwise the suite runs again. A file red on both runs fails the step: it depends on running together. Red on one run only: `intermittent`, a FAIL, when the step changed that file; otherwise a `flaky · <files>` note, someone else's flaky test, not this step's. `NOT RUN · suite unstable under load` means each run failed on different files, all passing alone and none changed by the step, so the machine is overloaded and nothing was judged. Then switch the baseline to a command that runs fewer files at once, and check again:

```bash
python3 scripts/step_check.py set-cmd --base feature/<name> --test-cmd "<suite command, fewer files at once>"
```

`suite logs` gives the full output of every run: read the failing tests there, never rerun the suite to see them.

# Feature review

Once, after every step has passed its check, on the feature branch, before prove.

**Needs** a test suite that runs, and a committed state. No suite: say so and stop; `/m-prove` is the only judge left.

## 0. Prepare

```bash
git fetch origin && python3 scripts/prepare.py --base origin/<base branch> --test-cmd "<scan Q6>" --setup-cmd "<how a fresh checkout gets its dependencies and env files>"
```

Prepare checks out the base once, runs the setup command there with `MSTACK_ROOT` set to this checkout (to copy env files from), then the suite; every gate run reuses that checkout. Take the setup command from scan Q9 or the run recipe. Leave it out only when the suite runs on a bare checkout. Prepare aborts when the setup fails or the suite runs no test, at HEAD or at the base: fix the command, or start what it needs, and prepare again.

`--test-cmd`, `--setup-cmd` and the gate's `--cmd` run under cmd.exe on Windows, sh elsewhere: quote `"{test}"`, write no `$VAR` (cmd.exe reads `%VAR%`), and prefer a command with no shell syntax, which the two shells read differently.

## 1. Hunt

Dispatch fresh `general-purpose` agents at once, model strong: nothing downstream checks what they miss. They do not see each other. How many: 1 when the map's How hard to undo is easy and the diff is under 300 changed lines, since hunters overlap most on a small diff and an easy miss costs a later fix; otherwise 3, and 3 when no verdict was given. Prompt:

```
Read <this skill's directory>/references/hunt.md and follow it.
```

then: the ledger command (`python3 <scripts>/ledger.py add`), the base and head from prepare, the changed files, the Goal, Settled up front, Assumed and Not doing verbatim (from `/m-feature`: the map number, for the hunter to read them from), and which repo rule files exist (`CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `.claude/rules/`).

Over about 1,500 changed lines: split the files into groups by directory and give each group 2 hunters. Every hunter may read the whole repo.

Mark a candidate `duplicate` only when its claim, condition and file match another's (`python3 scripts/ledger.py duplicate --id <id> --of <id>`). Every other candidate goes on, however unlikely it looks: the gate decides.

## 2. Reproduce

One fresh `general-purpose` agent per candidate, model standard, never a hunter: the gate checks its work. Prompt:

```
Read <this skill's directory>/references/repro.md and follow it.
```

then: the finding's id, claim, condition and entry point, the test command, and how the repo tests (scan Q6). It does not get the hunter's reasoning.

Up to 4 at once when tests share nothing (database, ports, files); otherwise one at a time. It returns `capture · repro · cmd`, or `unjudgeable · <reason> · files <paths | none>`:

```bash
python3 scripts/ledger.py unjudgeable --id <id> --reason "<reason>" --remove <files it left>
```

The gate removes a reproduction's files on every outcome, and those of a gate that was killed on its next run; `--remove` does it for a writer that gave up, and skips anything that is not a file inside the repo. A leftover failing file turns every later suite run red.

## 3. Gate

One at a time, per returned reproduction:

```bash
python3 scripts/gate.py confirm --id <id> --capture <path> --repro <path> --cmd "<cmd with {test}>"
```

The only route to `confirmed`. The capture must pass and the repro fail at HEAD, 5 runs each; then the repro runs once in the base checkout, and the capture when the repro fails there. The repro passes there: `regression`. Both fail: the broken behaviour is new, `new-behaviour` (`unjudgeable` when prepare found the base suite red, since the checkout may be what fails). The capture passes there: the bug was already in the base, `dead`. A killed reproduction is not sent back or adjusted.

## 4. Report

```bash
python3 scripts/report.py
```

Return its output verbatim. It removes the base checkout: a confirm after it needs a new prepare. Stop: no second round, no suggestions.

# Recheck

After a fix step for confirmed findings has passed its step check, on the fix branch, every finding in one call: the suite runs once for all of them.

```bash
python3 scripts/gate.py recheck --id F-001 --id F-002 --promote
```

The frozen repro runs first; `fixed` when it passes every run. Otherwise the frozen capture runs: it passes, the broken behaviour is still there, `still-failing`.

`fixed` leaves the reproduction in the checkout: commit it on the fix branch as a regression test. A copy an interrupted recheck left behind, identical to the frozen one, is removed by the gate itself: never delete a reproduction by hand. `still-failing` or `SUITE WORSE`: the fix did not hold.

`RECHECK NOT RUN` (exit 2): the suite hit its ceiling, so nothing was judged and every state is as it was.

`stale`: the repro and the capture both fail now (the markup or API they set up against changed), so they say nothing about the claim. Dispatch a fresh repro writer as in step 2, with the claim, condition and entry point, told it is a recheck (`references/repro.md`). Then:

```bash
python3 scripts/gate.py recheck --id <id> --capture <path> --repro <path> --cmd "<cmd with {test}>" --promote
```

The writer gives up: delete the files it lists that git does not track (`git ls-files --error-unmatch <path>` fails), and the finding stays `stale`: that is the answer.

# Rules

- Only the gate writes `confirmed`, `fixed`, `still-failing` or `stale`; the builder's checks and your own reading settle nothing.
- Agreement between agents is evidence neither way.
- Frozen reproductions, existing tests, the harness and the code under review stay exactly as they are.
- The builder gets the claim and the condition; the reproduction stays with the review.
- The review covers the diff, minus anything on Not doing.
