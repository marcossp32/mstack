# Slice loop

How a slice gets built, checked, reviewed and proved, from the prerequisites and baseline the first step check needs to the slice's closed Decided line.

## Prerequisites and baseline

Outcome: the prerequisites scan Q9 lists (a database, a service) running, and a step check baseline recorded on `feature/<name>` before the first step check, because every check is a comparison against it.

- Nothing a skill starts outlives it: start each prerequisite under `python3 <m-review dir>/scripts/contain.py`, in the background, and keep its pid. Prove starts its own, so stop them before each prove and start them again after.
- Record the baseline with `python3 <m-review dir>/scripts/step_check.py baseline --test-cmd "<scan Q6 suite | none>" --test-file-cmd "<scan Q6 one file, {test} for its path>"`; `set-cmd` swaps the suite command later without losing the verdict. A baseline that aborts at setup names what it lacked: provide it and record again.
- A red baseline is fine: the check then fails a step only for files outside the already-failing set. Comment that set on the state once; it goes under the PR's What to watch.

Pitfalls, each a property of how the check runs:

- The step check ends every contained process started inside the checkout, so a prerequisite started from there dies at the next check. Start them from outside it.
- Test runners run many files at once, commonly one per core, and test files that each launch a browser or a server then stall the machine. Cap files at once (the runner's flag, from scan Q6) well below the core count, and give a resumed baseline the cap with `set-cmd`.
- The verdict is the script's last lines and its exit code, and suite runs are long: run every `step_check.py` call on its own, unpiped, in the background, and read its result before acting, since a pipe or a tool timeout loses it.

## Step

Outcome: the step's work merged into `feature/<name>` and pushed, its step branch gone, its item closed with the notes' What changed, the slice line updated.

- Re-read the state and the step item first: another session may have changed them, and the state wins.
- Cut the step branch from `origin/feature/<name>` after a fetch ([`state.md`](state.md), Branches) and dispatch the build on it (SKILL.md, Dispatch). It returns the notes path, or `Stop · <kind> · <what>`, which goes to a debate.
- Judge it with `python3 <m-review dir>/scripts/step_check.py check --base origin/feature/<name> --notes <notes path>` on the step branch, after a fetch. Exit 0 PASS, 1 FAIL, 2 NOT RUN.
- On PASS, merge locally into an up-to-date `feature/<name>`: `--no-ff`, or squash when scan Q9 says the repo squashes. The message is the notes' first line, a blank line, `Part of <step ref>`, since the patching-loop count reads it. Push, so a resume elsewhere sees it; delete the step branch; `tracker close-step`.
- Each `## Disputed` entry in fix-mode notes goes to a debate ([`escalation.md`](escalation.md)).

## Step check results

The principle: **a step fails only for what it caused; what the check could not judge is neither a pass nor the step's fault.** A FAIL goes back to the builder in fix mode with the output (commented on the step item); only a PASS after a build clears it. Two FAILs on one step go to a debate. A check that judged nothing (NOT RUN, an intermittent result on files the step did not touch) is never a FAIL for the builder and does not count toward the second one. Check once more without a build; judged nothing again, record it on the slice line and under the PR's What to watch, and take it to a debate as a failure a fix cannot settle, rather than send the builder to fix what it did not cause.

What the principle does not make obvious:

- `credential` and `credential?` are FAILs: the builder moves the value to an environment variable (`MSTACK_SECRET_<NAME>` when the app reads a secret to run). `credential placeholder` (a key-shaped value that says it is not real) is a note.
- `unpinned?` is a note: the builder says no test can pin this step, so the slice prove judges it. Put the reason on the slice line.
- `flaky · <files>` on a PASS: merge, and note each file once on the state for the PR's What to watch. It is someone else's flake.
- `NOT RUN · suite unstable under load` means too many files ran at once, not a broken step: lower the files at once with `set-cmd` and check again. Unstable even one file at a time: no step check can judge this machine's suite. Record it, put it under What to watch, close every remaining slice not verified and go to Closing.
- `pinned · not run`: the check lacked what it names (a service, a command). Comment it on the state once, provide it, check again.
- A suite "not comparable" (red baseline naming no failing file): record it for What to watch; the pinned tests and the slice prove still judge.
- A re-cut step with the same Done when, under a new item, is the same step: its next FAIL is the second. A changed Done when starts at zero.

## Quality review

Outcome: the slice's diff reviewed to `QUALITY REVIEW: clean`, or every remaining finding taken to a debate.

- After the last step merges, record the slice end sha, call the Skill tool with `m-review` and ask for its quality review of `<slice start sha>..<slice end sha>` with the inputs SKILL.md's Dispatch lists. Done when it returns `F<n>` lines and its `QUALITY REVIEW:` count line; comment them on the state. A reply that a fresh reviewer is needed instead goes, with the same request, to a fresh `general-purpose` agent that calls the Skill tool with `m-review`.
- Fix the findings as one fix item (every `F<n>` line verbatim; Done when: no listed finding holds), built, checked and merged like a step. Record the feature-branch sha before and after the merge: the re-review sees only that range.
- Then ask `m-review` for its re-review of only those findings on that range. Done when it returns `F<n> · fixed | still-failing · <why>` per finding and `RE-REVIEW: <n> fixed · <m> still failing`. The whole diff is never reviewed again, since a fresh read of it finds new findings forever.
- A finding still failing after two fix rounds, or disputed by the builder, goes to a debate on its own; the rest go on. Only m-review calls a finding fixed.

## Slice prove

Outcome: `Slice S<k> — verified`, or the failure taken to a debate.

- Stop the prerequisites, dispatch the prove `mode: slice` (SKILL.md, Dispatch), start them again after. Comment its verdict lines on the state, without local paths, which nobody else can open.
- Verified: close the slice with what a user can now do, the verdict comment and its replays (`S<k>`, `R<n>`). `verified · human check`: close it the same way with `· human check <lines>`; no fix can drive those lines, and they go under To merge.
- Not verified: a fix item listing each line driven and wrong (the Done when e2e or requirement, the value seen, its evidence excerpt), built, checked, merged; prove again. A slice short only by not driven lines (ceiling, harness) has nothing to fix in code: prove again with what it lacked provided, and debate if it still cannot drive them. Count the patching loop before each fix item.
- Still not verified after two fix rounds: debate. A requirement failing again on an input the earlier fix did not cover: the bound rule ([`escalation.md`](escalation.md)) before another fix.
