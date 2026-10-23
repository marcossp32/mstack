---
name: m-review
description: "Reviews a change without running the app: a script checks each build step against the suite's recorded baseline, and a static review reports only findings that a repo rule or the installed version's official docs condemn. Use when asked to check a build step, review a change, or recheck its findings after a fix."
---

Tells the caller whether a change is well made; whether it works is judged by driving the running app, not here. The step check is a script that gates each build step before it merges into the feature branch. The quality review is one fresh static agent that reads a range of commits and reports only what a written source condemns, so a builder can fix each finding and the caller can check it without trusting the reviewer.

# Done when

- Step check: `step_check.py`'s output was returned whole, ending in `STEP CHECK: PASS`, `STEP CHECK: FAIL` or `STEP CHECK: NOT RUN · <why>`, or, where the script aborted, its message, which carries no verdict.
- Quality review: `F<n>` lines in the format below, or none, followed by `QUALITY REVIEW: <n> findings` or `QUALITY REVIEW: clean`.
- Re-review: one `F<n> · fixed` or `F<n> · still-failing · <why>` line per finding given, followed by `RE-REVIEW: <n> fixed · <m> still failing`.

# Acceptance criteria

- [ ] A step check result is the script's own output, unedited, with at most one `STEP CHECK:` line.
- [ ] Every quality finding names a source with its location: a repo rule `file:line` with its words verbatim (present at HEAD), or a verbatim official-doc quote with its URL and the installed version.
- [ ] Every quality finding names the `file:line` of a line the reviewed range adds or changes.
- [ ] No quality finding is something a linter, formatter or type checker the repo runs would catch, or anything on Not doing.
- [ ] No quality finding cites a test run, an app run or a reproduction as evidence.
- [ ] No finding carries a severity, a confidence or a "consider".
- [ ] The count line matches the number of `F<n>` lines.
- [ ] A re-review has exactly one line per finding it was given, the same ids, and no new finding.
- [ ] Everything is returned as text: no tracker item, comment or pull request was created or changed by this run.

Models are tiers: strong is the harness's most capable, standard its middle one; a tier that does not resolve runs on the session's model. Scripts are in this skill's `scripts/` directory and keep their state in the git common dir, so nothing they write shows in the checkout.

# Step check

A script, no model judgement: it gates each build step on its branch before the step merges. Its CLI is the interface:

```bash
python3 scripts/step_check.py baseline --test-cmd "<suite command | none>" --test-file-cmd "<command for one test file, {test} for its path>"
python3 scripts/step_check.py check --base origin/feature/<name> --notes <step notes file>
python3 scripts/step_check.py set-cmd --base feature/<name> --test-cmd "<suite command>"
python3 scripts/step_check.py clear --base feature/<name>
```

The baseline is recorded on the feature branch before the first check, because every step is judged against the suite as it was when the feature started: a suite already red records its failing files, and a step then fails only on files failing beyond those. A baseline aborts when the suite fails before any test runs (a missing module, a refused connection), since a suite that never ran judges nothing; provide what it names and record it again. `clear` deletes the baseline when the feature ends. The check diffs against `origin/feature/<name>`, so fetch first: a stale branch puts earlier steps in the diff.

What `check` judges, reading the step notes' `## Tests changed` and `## Pinned by` (without `--notes` nothing counts as listed or pinned):

- **Suite no worse** than at the baseline. It reruns enough to tell a real failure from flakiness: a file red only sometimes is `intermittent` (a FAIL) when the step touched code a test could load, else a `flaky` note.
- **Weakened tests declared**: every existing test file or snapshot changed or deleted, and every added skip, focus, suppression or runner exclusion, is listed in Tests changed.
- **No credentials** in the added lines: `credential` and `credential?` fail; the value belongs in an environment variable.
- **Pinned**: each Pinned by test passes at HEAD and fails with the step's non-test changes reverted. It reverts in place, so it needs a checkout with no tracked changes and restores HEAD before exiting; a check killed mid-revert leaves a marker, and the next check restores those files itself, so they are never committed.

What its output means:

- `STEP CHECK: PASS` (exit 0): the step may merge. Its notes still travel to the caller: `credential placeholder`, `unpinned?`, `flaky` and `pinned · not judgeable · dependency change` (left for the app-level proof) do not fail the step.
- `STEP CHECK: FAIL` (exit 1): the `- FAIL` lines say what to fix, and go to the builder.
- `STEP CHECK: NOT RUN · <why>` (exit 2): a run hit its time ceiling or the suite was unstable under load; nothing was judged, so it is neither a pass nor the step's fault. Return it as it is. `suite unstable under load` (different files failing each run, all passing alone) means too many files ran at once: `set-cmd` to a suite command that runs fewer, then check again.
- The `suite logs` line holds every run's full output: read failures there rather than rerunning. The `sweep` line is cleanup of earlier runs, not a finding.

A suite run can outlast the shell tool's time limit, and a pipe or a timeout loses the verdict, so run each call in the background, unpiped, and read its whole output before acting.

# Quality review

Reviews a range of merged commits statically: nothing runs, since whether the code works is the app-level proof's question.

What it reviews, and with what, comes from the caller where given:

- the range `<start sha>..<end sha>`; with none given, the current branch from its merge-base with the base branch to HEAD;
- How hard to undo, and Not doing (none given: nothing is excluded);
- installed versions (scan Q1), how the repo does similar things and its names (scan Q4, Q5), and docs answers already researched, with their quotes and links; where missing, the reviewer finds them itself;
- which repo rule files exist.

Dispatch one fresh `general-purpose` agent with web access for docs: model standard, strong when How hard to undo is hard or not given, since a missed rule there is costly to undo. Fresh, because whoever wrote or merged the code reads it with the author's eyes. Its prompt opens `Read <this skill's directory>/references/quality.md and follow it.`, then gives the inputs above verbatim. Its reply, the lines below, shows it done. With no Agent tool, read [`references/quality.md`](references/quality.md) before reviewing yourself, unless this session wrote the code under review: then return one line saying a fresh reviewer is needed and why.

Before returning, hold the output to the bar, since the caller acts on each line: drop any `F<n>` line without a code `file:line` or a source, and any whose rule `file:line` does not hold its quoted words at HEAD; renumber from F1 and fix the count line. Return the rest verbatim:

```
F<n> · <file:line> · <what is wrong, one sentence> · source <rule file:line "<words>" | "<doc quote>" <url> (<version>)> · fix <what would satisfy the source>
QUALITY REVIEW: <n> findings | clean
```

# Re-review

After a fix for quality findings has merged. It rechecks only the findings handed to the builder, never the whole range again, so a fix round converges instead of growing.

Dispatch one fresh `general-purpose` agent at the review's tier, its prompt opening as above and pointing it at the Re-review section of `references/quality.md`, with the `F<n>` lines verbatim and the fix range `<sha before the fix merge>..<sha after it>`. Return its output verbatim:

```
F<n> · fixed
F<n> · still-failing · <why>
RE-REVIEW: <n> fixed · <m> still failing
```

What happens to a `still-failing` finding is the caller's decision.
