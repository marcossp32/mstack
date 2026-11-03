---
name: m-review
description: "Reviews a change without running the app: a script checks each build step against the suite's recorded baseline, and a static review reports only what a reader can prove from the diff: a changed line that cannot do what its requirement's words say, a bug with a concrete input that breaks it, a break of a repo rule or an official doc or standard for the installed version, or the same behaviour in clearly less code. Use when asked to check a build step, review a change against its requirements, or recheck its findings after a fix."
---

Tells the caller whether a change is well made and does what was asked, as far as reading can tell; whether it works in the running app is judged there, not here. The step check is a script that gates each build step before it merges into the feature branch. The quality review is one fresh static agent that reads a range of commits next to the requirements it serves and reports only findings that carry their own evidence, so a builder can fix each one to a clear end and the caller can check it without trusting the reviewer.

# Done when

- Step check: `step_check.py`'s output was returned whole, ending in `STEP CHECK: PASS`, `STEP CHECK: FAIL` or `STEP CHECK: NOT RUN · <why>`, or, where the script aborted, its message, which carries no verdict.
- Quality review: `F<n>` lines in the format below, or none, then one `COVERAGE ·` line, then `QUALITY REVIEW: <n> findings` or `QUALITY REVIEW: clean`.
- Re-review: one `F<n> · fixed` or `F<n> · still-failing · <why>` line per finding given, followed by `RE-REVIEW: <n> fixed · <m> still failing`.

# Acceptance criteria

- [ ] A step check result is the script's own output, unedited, with at most one `STEP CHECK:` line.
- [ ] Every quality finding names the `file:line` of a line the reviewed range adds or changes, and nothing on Not doing.
- [ ] Every quality finding carries evidence a sceptical reader can check by reading: requirement words verbatim from the lines given; a concrete input or state with where it comes from; a repo rule `file:line` with its words verbatim at HEAD, or a verbatim official doc or standard quote with its URL and version; or the shorter code itself.
- [ ] No quality finding is something a linter, formatter or type checker the repo runs would catch, depends on running the code, or is taste.
- [ ] No finding carries a severity, a confidence or a "consider".
- [ ] The coverage line names every requirement id given and counts every changed file; the count line matches the number of `F<n>` lines.
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

- **Suite no worse** than at the baseline. It reruns enough to tell a real failure from flakiness: a file red only sometimes is `intermittent` (a FAIL) when the step touched code a test could load, else a `flaky` note. A file already intermittent at another step of the feature is a `flaky` note unless this step changed that test file: it flakes whatever the step does, and failing every step on it only buys a suite rerun.
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

Reviews a range of merged commits statically: nothing runs. Why it exists: the app-level proof is the costliest stage, and many of its failures are visible to anyone who reads the diff next to the requirement (a hard-coded value where the requirement names a setting, a guard that drops a case the requirement names, a value read from the wrong place, a shared file changed for surfaces the requirement leaves out). Catching those here costs cents; catching them at prove costs a round. A wrong finding costs a fix round too, so the review reports only what it can show.

What it reviews, and with what, comes from the caller where given:

- the range `<start sha>..<end sha>`; with none given, the current branch from its merge-base with the base branch to HEAD;
- the slice's `Slice S<k> · Done when e2e …` line and the Requirements lines it serves, verbatim, with the Assumed lines that name those ids (none given: the review judges no requirement, and the coverage line says so);
- How hard to undo, and Not doing (none given: nothing is excluded);
- installed versions (scan Q1), how the repo does similar things and its names (scan Q4, Q5), and docs answers already researched, with their quotes and links; where missing, the reviewer finds them itself;
- which repo rule files exist.

Dispatch one fresh `general-purpose` agent with web access for docs: model standard, strong when How hard to undo is hard or not given, since a miss there is costly to undo. Fresh, because whoever wrote or merged the code reads it with the author's eyes. Its prompt opens `Read <this skill's directory>/references/quality.md and follow it.`, then gives the inputs above verbatim. Its reply, the lines below, shows it done. With no Agent tool, read [`references/quality.md`](references/quality.md) before reviewing yourself, unless this session wrote the code under review: then return one line saying a fresh reviewer is needed and why.

Before returning, hold the output to what you can check cheaply, since the caller acts on each line: drop any `F<n>` line whose code `file:line` is outside the range's changed lines, whose requirement words are not verbatim in the lines given, whose rule `file:line` does not hold its quoted words at HEAD, or that lacks its kind's evidence (a `bug` without an input, a `simpler` without the shorter code). If the coverage line misses a requirement id given or a changed file, send the reviewer back once to cover them. Renumber from F1, fix the count line, and return the rest verbatim:

```
F<n> · <file:line> · <requirement | bug | standard | simpler> · <what is wrong, one sentence> · source <evidence, by kind, as in quality.md> · fix <the end state that clears it>
COVERAGE · <requirement ids and Done when checked | no requirements given> · <k>/<k> changed files
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
