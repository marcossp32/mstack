---
name: m-review
description: "Judges a change by execution, never by opinion: a script checks each build step, and a feature review reports only failures a frozen reproduction demonstrated. Use as the check and review stages of /m-feature, or on any branch with a runnable test suite before it merges."
---

Judge a change only by what running code shows. A finding without a reproduction that failed at the gate does not exist: no confidence scores, no severity, no "possible issues". An empty report is the expected outcome; never pad it.

Runs in the main chat: the feature review dispatches its own agents. Models are tiers, never names: strong is the harness's most capable model, standard its middle one. `/m-feature`'s Routing line overrides the tiers below.

Scripts are in this skill's `scripts/` directory; run them with `python3` (`python` where `python3` is absent). If one aborts, stop and report its message. State lives in the git dir, never in the checkout.

# Step check

After each build, on the step branch. No model judgement.

```bash
python3 scripts/step_check.py baseline --test-cmd "<scan Q6 | none>"     # once, before the first step
git fetch origin && python3 scripts/step_check.py check --base origin/feature/<name> --pr <n>
```

Return its output. `STEP CHECK: FAIL` lists what failed; `credential?` lines are for the human to look at and do not fail the step.

# Feature review

Once, after every step has passed its check, on the feature branch, before prove.

**Needs** a test suite that runs, and a committed state. No suite: say so and stop; `/m-prove` is the only judge left.

## 0. Prepare

```bash
python3 scripts/prepare.py --base main --test-cmd "<scan Q6>" --setup-cmd "<how a fresh checkout gets its dependencies and env files>"
```

The setup command runs inside a fresh checkout of the base, with `MSTACK_ROOT` set to this checkout (to copy env files from). Take it from scan Q9 or the run recipe. Leave it out only when the suite runs on a bare checkout.

## 1. Hunt

Dispatch 3 fresh `general-purpose` agents at once, on the strong tier: nothing downstream checks what they miss. They do not see each other. Prompt:

```
Read <this skill's directory>/references/hunt.md and follow it.
```

then: the ledger command (`python3 <scripts>/ledger.py add`), the base and head from prepare, the changed files, the Goal, Settled up front and Not doing verbatim (from `/m-feature`: the map number, for the hunter to read them from), and which repo rule files exist (`CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `.claude/rules/`).

Over about 1,500 changed lines: split the files into groups by directory and give each group 2 hunters. Every hunter may read the whole repo.

Mark a candidate `duplicate` only when its claim, condition and file match another's (`python3 scripts/ledger.py duplicate --id <id> --of <id>`). Never drop one for looking unlikely: the gate decides.

## 2. Reproduce

One fresh `general-purpose` agent per candidate, on the standard tier (the gate checks its work), never a hunter. Prompt:

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

# Never

- Write `confirmed`, `fixed` or `still-failing` by any route but the gate.
- Score confidence or severity, or count agreement between agents as evidence either way.
- Edit a frozen reproduction, an existing test, the harness or the code under review.
- Show the builder a reproduction: it gets the claim and the condition.
- Review outside the diff, or anything on Not doing.
