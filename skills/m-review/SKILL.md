---
name: m-review
description: "Reviews a change without running the app: a script checks each build step against the suite's recorded baseline, and a static review reports only findings a reader can prove from the diff, by a requirement's words, a concrete input, a repo rule or the installed version's docs. Use when asked to check a build step, review a change against its requirements, or recheck its findings after a fix."
---

Tells the caller whether a change is well made and does what was asked, as far as reading can tell; whether it works in the running app is judged elsewhere, by driving it. Three parts, each started on its own request: the step check, the quality review and the re-review. Each ends on the lines its Done when names, which are what the caller branches on.

Models are tiers: strong is the harness's most capable, standard its middle one; a tier that does not resolve runs on the session's model. Scripts are in this skill's `scripts/` directory and keep their state in the git common dir, so nothing they write shows in the checkout.

# Step check

A script judges, with no model judgement: a build step may merge into the feature branch only if the suite is no worse than when the feature started, every weakened test is declared in the step notes, no credential is added, and each test the notes say pins the step passes at HEAD and fails with the step's code changes reverted. Its CLI is the interface:

```bash
python3 scripts/step_check.py baseline --test-cmd "<suite command | none>" --test-file-cmd "<command for one test file, {test} for its path>" --env <NAME=VALUE>
python3 scripts/step_check.py check --base origin/feature/<name> --notes <step notes file>
python3 scripts/step_check.py set-cmd --base feature/<name> --test-cmd "<suite command>"
python3 scripts/step_check.py clear --base feature/<name>
```

- `baseline` runs once, on the feature branch, before the first check, since every step is judged against the suite as it was then. Give one `--env` per variable the tests need (a bare `NAME` for a secret already set in the environment, which is never stored); the script refuses a variable set inline in the command. A suite that fails before any test runs records nothing and names what it lacked: provide it, then record again.
- `check` runs on the step branch with no tracked changes, after a fetch, since a stale feature branch puts earlier steps in the diff. It reads the notes' `## Tests changed` and `## Pinned by`; without `--notes`, nothing counts as declared or pinned.
- `set-cmd` swaps the recorded suite command, keeping its verdict and its environment unless `--env` is given again, which replaces it; `clear` deletes the baseline when the feature ends.

A suite run can outlast the shell tool's time limit, and a pipe or a timeout loses the verdict, so run each call in the background, unpiped, and read its whole output before acting.

What the output means, by its last line rather than its exit code, since an abort and a FAIL can share exit 1:

- `STEP CHECK: PASS` (exit 0): the step may merge. Its `- ` notes still travel to the caller, and none fails the step.
- `STEP CHECK: FAIL` (exit 1): the `- FAIL` lines say what to fix, for the builder.
- `STEP CHECK: NOT RUN · <why>` (exit 2): nothing was judged, so it is neither a pass nor the step's fault. After `suite unstable under load` (different files failing each run, all passing alone), `set-cmd` to a suite command that runs fewer files at once, then check again.
- `ABORT: <reason>` on stderr, with no `STEP CHECK:` line: no verdict. Where the reason names something to provide (a prerequisite, a baseline, a fetch), provide it and run again; changes in the checkout that you did not make belong to whoever made them, so return the message as it is rather than committing or discarding them.
- The `suite logs` note holds every run's full output: read failures there rather than rerunning. The `sweep` note is cleanup of earlier runs, not a finding.

**Done when** the script's output is returned whole and unedited, ending in its one `STEP CHECK:` line, or its abort message, which carries no verdict.

# Quality review

One fresh static reviewer reads a range of merged commits next to the requirements it serves, and reports only findings that carry their own evidence, so the builder can fix each one to a clear end and the caller can check it without trusting the reviewer. Nothing runs.

The inputs, from the caller where given:

- the range `<start sha>..<end sha>`; with none given, the current branch from its merge-base with the base branch to HEAD;
- the slice's `Slice S<k> · Done when e2e …` line and the Requirements lines it serves, verbatim, with the Assumed lines that name those ids (none given: the review judges no requirement, and the coverage line says so);
- How hard to undo, and Not doing (none given: nothing is excluded);
- installed versions (scan Q1), how the repo does similar things and its names (scan Q4, Q5), and docs answers already researched, with their quotes and links; where missing, the reviewer finds them itself;
- which repo rule files exist.

Dispatch one fresh `general-purpose` agent with web access for docs: model standard, strong when How hard to undo is hard or not given, since a miss there is costly to undo. Fresh, because whoever wrote or merged the code reads it with the author's eyes. Its prompt opens `Read <this skill's directory>/references/quality.md and follow it.`, then gives the inputs above verbatim.

With no Agent tool, read [`references/quality.md`](references/quality.md) and review yourself, unless this session wrote the code under review: then return only `Fresh reviewer needed · <why>`.

The reviewer has a stake in its own findings, so hold its output to what you can check cheaply before returning it: drop any `F<n>` line whose code `file:line` is outside the range's changed lines, whose requirement words are not verbatim in the lines given, whose rule `file:line` does not hold its quoted words at HEAD, or that lacks its kind's evidence (a `bug` without a concrete input, a `simpler` without the shorter code). If the coverage line misses a requirement id given or a changed file, send the reviewer back once to cover them. Renumber from F1, fix the count line, and return the rest verbatim.

**Done when** this is returned, and nothing else:

```
F<n> · <file:line> · <requirement | bug | standard | simpler> · <what is wrong, one sentence> · source <evidence, by kind, as in quality.md> · fix <the end state that clears it>
COVERAGE · <requirement ids and Done when checked | no requirements given> · <k>/<k> changed files
QUALITY REVIEW: <n> findings | clean
```

# Re-review

After a fix for quality findings has merged, recheck only the findings handed to the builder, never the whole range again, so a fix round converges instead of growing.

Dispatch one fresh `general-purpose` agent at the review's tier, its prompt opening as above and pointing it at the Re-review section of `references/quality.md`, with the `F<n>` lines verbatim and the fix range `<sha before the fix merge>..<sha after it>`. What happens to a `still-failing` finding is the caller's decision.

**Done when** its output is returned verbatim, one line per finding given, the same ids, and no new finding:

```
F<n> · fixed
F<n> · still-failing · <why>
RE-REVIEW: <n> fixed · <m> still failing
```
