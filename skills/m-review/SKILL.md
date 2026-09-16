---
name: m-review
description: "Reviews one build step's diff in two independent passes, verifying the builder's test claims, and ends on PASS or CHANGES REQUIRED. Use after every /m-build step, or on any step diff with a known fixed point."
---

Review one step's diff and report. Change nothing. You have not seen the conversation that produced the code; do not seek it out. Everything you write follows [`references/writing.md`](references/writing.md); your final message is the report template below.

# Setup

Gather all of this before either pass. Stop only where an item says so; items with a fallback use it; anything else missing goes under Not checked.

1. Diff: `git diff <fixed-point>...HEAD` (three dots). The fixed point is where the step branch left the feature branch; if not given, `git merge-base HEAD <feature-branch>`. It must resolve with `git rev-parse`, or stop.
2. Empty diff: stop and say so.
3. The step issue and its Done when. None: say "no issue available" and run only Pass B. Never invent the requirement.
4. Repo standards: `CONTRIBUTING.md`, `CODING_STANDARDS.md`, `AGENTS.md`, lint config. Apply them first; on smells and style they win.
5. Design-check answers from `/m-plan`.
6. The PR, with the builder's answers about its tests: verify them.
7. Undo verdict. Missing: treat as hard.
8. Timeout values from docs, or "not applicable" (no external call).
9. The map's Not doing list.
10. The test command (scan Q6).
11. The map's Settled up front.

# Two passes

Run Pass A first, judging without the standards or design notes, then Pass B. A's findings do not decide B's.

- **Pass A** reads the issue, Settled up front and the diff.
- **Pass B** reads the diff, the standards and the design notes.

## Pass A — spec

- Done when met, checked in the code.
- Done when covered by a test of that behaviour.
- Every Settled up front decision the diff touches holds in the code.
- Nothing added beyond the step.
- Nothing asked for left out, compared line by line.
- The feature branch still works with this merged.

## Pass B — code

**B1 Tests** — green tests are not evidence; a step whose tests prove nothing fails however green.

- Every test asserts.
- No test file changed after its production code (`git log` order).
- Every test failed on its assertion before the code existed (commit order).
- Tests assert on results, not on calls.
- Break the code once per Done when and once per test named after a behaviour, at either depth: the smallest change that breaks that behaviour ([`references/proving-tests.md`](references/proving-tests.md)). Run the tests; one must go red; undo. A break nothing catches is an untested Done when or behaviour: name the break.

**B2 Design** (hard to undo only): run [`references/design-checks.md`](references/design-checks.md) on the code.

**B3 Production**

- No credentials, keys, tokens or internal URLs: could this repo be made public today?
- Every call outside the process has a timeout.
- Resources released on error paths.
- Environment-specific values come from the environment.
- Failure logs allow diagnosis without reproducing.

**B4 Smells**, after the repo's standards. If the repo documents none, Fowler's twelve: Mysterious Name, Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change, Speculative Generality, Message Chains, Middle Man, Refused Bequest. Smells only go under Worth noting.

# Depth

- Hard to undo: everything.
- Easy: Pass A, B1, B3. B2 and B4 only if something is obviously wrong.

Out of scope: what linters and formatters cover, style with no repo rule, code outside the diff (note it as separate work), anything on Not doing.

# Verdict

**CHANGES REQUIRED** if any:

- Done when not met, or not tested.
- A Settled up front decision broken.
- A test with no assertion, written to fit the code, or asserting only on calls.
- Credentials in the diff.
- An external call without timeout, or a resource leak on an error path.
- A hardcoded environment-specific value.
- The feature branch broken by the merge.
- Work the step did not ask for.

Otherwise **PASS**. Smells, naming and preference never block.

Fill every section:

```
VERDICT: <PASS | CHANGES REQUIRED>

Must fix
- <what is wrong> · <file:line> · <what it should be>

Worth noting
- <what you saw> · <file:line>

Checked and clean
- <one line each>

Not checked
- <what, and why>
```
