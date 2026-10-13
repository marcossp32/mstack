---
name: m-review
description: "Reviews a change by execution: a script checks each build step, and a feature review reports only failures a frozen reproduction demonstrated. Use as the check and review stages of /m-feature, or to review any branch with a runnable test suite before it merges."
---

Judge a change only by what running code shows. A finding without a reproduction that failed at the gate does not exist: no confidence scores, no severity, no "possible issues". An empty report is the expected outcome, and a complete one.

The step check and recheck run where they are called. The feature review dispatches its own agents; from `/m-feature` it runs in a fresh agent, so its hunts stay out of the orchestrator's context, and returns only `report.py`'s output. With no Agent tool there, return `Review · not run · no Agent tool` and the caller runs it in its own chat.

Models are tiers: strong is the harness's most capable, standard its middle one. A tier that does not resolve runs on the session's model.

Scripts are in this skill's `scripts/` directory; run them with `python3` (`python` where `python3` is absent). If one aborts, stop and report its message. State lives in the git dir, never in the checkout. `step_check.py`, `prepare.py` and `gate.py` run the whole suite, `step_check.py` up to three times: start each with the Bash tool's `run_in_background` and read its output when the harness says it exited, so no run hits the tool's 10-minute limit.

# Step check

After each build, on the step branch. No model judgement.

```bash
python3 scripts/step_check.py baseline --test-cmd "<scan Q6 | none>"     # once, before the first step
git fetch origin && python3 scripts/step_check.py check --base origin/feature/<name> --pr <n>
```

Return its output. `STEP CHECK: FAIL` lists what failed; `credential?` lines are for the human to look at and do not fail the step. A red suite runs up to three times: `intermittent` means red on some runs only, and still fails. `suite logs` gives the full output of every run: read the failing tests there, never rerun the suite to see them.

# Feature review

Once, after every step has passed its check, on the feature branch, before prove.

**Needs** a test suite that runs, and a committed state. No suite: say so and stop; `/m-prove` is the only judge left.

## 0. Prepare

```bash
git fetch origin && python3 scripts/prepare.py --base origin/<base branch> --test-cmd "<scan Q6>" --setup-cmd "<how a fresh checkout gets its dependencies and env files>"
```

The setup command runs inside a fresh checkout of the base, with `MSTACK_ROOT` set to this checkout (to copy env files from). Take it from scan Q9 or the run recipe. Leave it out only when the suite runs on a bare checkout.

## 1. Hunt

Dispatch 3 fresh `general-purpose` agents at once, model strong: nothing downstream checks what they miss. They do not see each other. Prompt:

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

The gate removes a reproduction's files on every outcome; `--remove` does it for a writer that gave up. A leftover failing file turns every later suite run red.

## 3. Gate

One at a time, per returned reproduction:

```bash
python3 scripts/gate.py confirm --id <id> --capture <path> --repro <path> --cmd "<cmd with {test}>"
```

The only route to `confirmed`. A killed reproduction is not sent back or adjusted.

## 4. Report

```bash
python3 scripts/report.py
```

Return its output verbatim. Stop: no second round, no suggestions.

# Recheck

After a fix step for confirmed findings has passed its step check, on the fix branch:

```bash
python3 scripts/gate.py recheck --id <id> --promote
```

`fixed` leaves the reproduction in the checkout: commit it on the fix branch as a regression test. `still-failing` or `SUITE WORSE`: the fix did not hold.

`stale`: the reproduction now fails before its assertion (the markup or API it set up against changed), so it says nothing about the claim. Dispatch a fresh repro writer as in step 2, with the claim, condition and entry point, told it is a recheck (`references/repro.md`). Then:

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
