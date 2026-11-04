---
name: m-prove
description: "Proves a change does what its requirements ask by driving the running app, judged on saved evidence, per slice or for a whole feature with a regression hunt against the base. Use when asked to prove a slice or a feature works in the running app."
---

Return a verdict on whether a change does what its requirements say, decided only by driving the running app and judged on saved evidence, for a caller acting without a human. Slice mode: does one slice work. Final mode: does the whole feature work and what else broke, with the pull request's filled Proved section and an issue draft per break the base already had.

# Done when

The Return block below exists for the mode asked with every part filled, everything the run started has stopped, and a slice run's evidence dir is deleted or named on `Left`.

# Acceptance criteria

- [ ] Every line in scope (Lines) has exactly one verdict, a `· CI <check>` line `settled by caller`. A slice-mode return has no `B<n>` or `Covered` line.
- [ ] Every value a verified line reports appears in a file under the evidence dir (final) or in the quoted output on its line or its saved replay (slice), under the command that printed it.
- [ ] Every verdict over a set shows the member count and the expected count from an independent route, equal and above 0.
- [ ] Every `not verified` line names the observed value; every `not driven` line names its precondition and the routes tried, or the ceiling.
- [ ] Every `human check` caused by a missing credential names the `MSTACK_SECRET_<NAME>` variable that would unlock it.
- [ ] No R line is `pre-existing` (Judge).
- [ ] Final mode ran every saved replay (`replay.txt` lists each line `replay.py list` prints) before Q1, and Q1 drove only the lines Supervise gives it.
- [ ] Every final-mode `S<k>` marked `superseded by S<j>` names the later slice line or requirement that changes the same surface.
- [ ] Every `pre-existing` break has an issue draft with every field filled.
- [ ] Every slice-mode verified line shows its `replay` result, in Return's form.
- [ ] After return, `contain.py sweep --kill --within <evidence dir>` ends nothing (`REAP: ended 0`, no `orphan` line), and slice mode left no `git worktree`.
- [ ] The feature verdict follows [`references/pull-request.md`](references/pull-request.md).
- [ ] The filled body has no `<!-- prove: … -->` placeholder left, every media path in it is on the Media line, and no credential value appears in it or in any kept file.
- [ ] No clip or demo was recorded unless the verdict is clean; the recipe holds no per-run notes.
- [ ] Everything to post is in the return and nothing was posted: no pull request, issue or comment comes from this run.

# Inputs

If this conversation wrote or watched the code, dispatch a fresh `general-purpose` agent whose prompt opens `Call the Skill tool with m-prove.` plus the inputs, and relay its reply unchanged: a judge that saw the code written reads its intent into the evidence. Done when that reply is a Return block, which only a run of this skill produces. Both modes get:

- `mode: slice` or `mode: final`.
- Feature branch (`feature/<name>`), which keeps the replays.
- Requirement lines verbatim, in the state's format: `R<n> · <asked | derived | derived · required by D<k>> · "<words>" · bound <domain | —> [was: <old bound>] · from …[ · CI <check>]`. None: return `Not driven · no requirements`.
- How the app runs (scan Q9, if any), Not doing, and the credential names `MSTACK_SECRET_<NAME>`, each with what it unlocks (values: Credentials, below).

Slice mode adds: the slice id `S<k>`, its line `Slice S<k> · Done when e2e <…> · serves R<a> R<b> · completes R<a>`, the R lines it serves, and its diff range `<slice start sha>..HEAD`.

Final mode adds: every `Slice S<k>` line, the base branch (none: the default branch), Assumed (context, never a requirement; Q2 may treat what one describes as a risk area), and the pull request body with the Proved section as `<!-- prove: … -->` placeholders. A repeat final (after a fix round) adds `previous final:` the previous final's Return block.

# Lines

A **line** is what one verdict covers.

- `S<k>`: the slice's Done when e2e. Its clause is the text after `Done when e2e ` up to ` · serves`, exactly.
- `R<n>`: requirement n. Its clause is `"<words>" · bound <current bound>`, without `was:` or `from`.
- **Blocking**: `S<k>` (slice mode), `asked` and `derived · required by D<k>`. A plain `derived` line is proved and reported; it never blocks.
- A requirement marked `retired by D<k>` gets no line: the line that replaced it is proved instead. One ending `· CI <check>` is the caller's to settle from the host's CI: no drive, replay or verdict here; it returns as `settled by caller · CI <check>` and never blocks a verdict or makes it human check.

Scope: slice mode proves `S<k>` and each R line the slice completes, in full, limited to what the slice touched; a line it only serves waits. Final mode covers every R line, and every `S<k>` through its replay. An `S<k>` whose replay fails or goes stale is driven again, since a later slice may have broken it; Judge decides whether a failure blocks.

# What makes a proof trustworthy

The bar every phase is judged against. How to meet it is yours to choose.

- **Requirements from the lines, not the diff.** Decide each line's surface and what settles it before reading the diff: read the code first and you prove what was built, not what was asked.
- **Settled by an independent read-back.** A line is settled by an observation read back by a route that skips the code that wrote it (a fresh read of the record, the file on disk, the message off the queue); what the surface returns counts when that is the effect asked for. No such route: what the app itself shows, said as `via the app itself`. A tolerance comes from the clause, never a number it does not state.
- **Verdicts only from drives and replays by agents that did not write the code.** Tests and type checks the builder wrote are not evidence here. Verified comes only from a drive or a replay; not verified only from a drive.
- **Every reported value is backed by output saved in the evidence dir**, under the command that printed it. A value nothing printed, or that only a screenshot shows, is not evidence.
- **A control path tells harness failure from product failure.** Something the diff never touched is driven first; when it fails too, the harness is broken and no line is not verified.
- **Sets are checked whole, with an independent count.** A clause over a set (each, every, all) is checked over every member, with the member count and an expected count from another route, equal and above 0: a check over an empty set passes forever, and naming every failing member lets one fix round cover them all.
- **Bounds are driven at their edges**, each limit and just past it, not at an easy value inside.
- **Regressions are judged against the base**, driven the same way: a difference is a break only if the base behaves otherwise.
- **The app runs as shipped.** Shipped defaults plus what the recipe or `.env.example` sets; any other variable is an override, listed with the line that needs it and why. A requirement about development, local or default settings gets no override.
- **Credentials stay in the environment**, as `MSTACK_SECRET_<NAME>`: never in a prompt, file, replay, recipe, recording or return. A line that needs one the environment lacks is `human check`, naming the variable.
- **Local only, headless, never hidden.** Every host the app talks to runs on this machine: no production, real payments, real emails or shared accounts. Browsers run headless and never hide their automation; a bot check or a login nobody provided is a `human check`, never something to get around.
- **Nothing left running.** Every process a prove starts is contained (`scripts/contain.py`) and stopped by teardown; the checkout ends as clean as it started.
- **Replays are frozen checks, never repaired.** A replay runs only against the clause it was saved for, and its command, environment and files are never changed to make it pass. One that fails or goes stale is a lead for a fresh drive, not a verdict: frozen checks also break when markup moves.
- **Not doing stays out**, even where a gap shows.

# Supervise

You build the contract, run replays, dispatch drives and judge them; tracker and host commands are never yours.

**Evidence dir.** `<git common dir>/mstack/prove/<short sha>-<unix time>`, with `q1/` (and `q2/` in final mode); its name is the run id. `cleanup.py` deletes only under `mstack/prove/`, so evidence lives nowhere else and is deleted only through it.

**Scripts work, you wait without polling.** By hand, preparing and replaying delayed a final's first drive 35-56 minutes; polling held 785 minutes, each poll re-sending 170-300k tokens. Run `prepare.py` and `replay.py batch` (`--help`) in the background and act when the harness says one finished.

**Contract**, from files and git, before any drive starts. It gives the drivers:

- HEAD and tree, the mode (slice id and range, or final and the base sha `prepare.py` prints), the checkout, the evidence dir, the base worktree if any.
- How to run the app: the recipe (a `SKILL.md` under `.claude/skills/` or `.agents/skills/` saying it launches this repo, the checkout's first, else the home dir's; else scan Q9), launch and its working dir, health check, prerequisites, the **data dir** the app writes to (replays read it as `MSTACK_DATA`), credential names set or unset (tested without printing a value), overrides, and in final mode whether head and base share state (a database, data dir, queue, a port the recipe cannot move), which makes the drives run one after the other. Scripts read these from `<evidence dir>/run.json` (`runspec.py --help`): the recipe's, or for a recipe in the checkout `<git common dir>/mstack/run.json`.
- Each line in scope: surface (page, endpoint, CLI command, public API), the recipe's surface file for it when there is one, and settled when, plus `replay` when one is listed. Say what settles it, not how to drive it: no payloads or steps, so the driver's choices stay open. Not observable: say so, the line ends not driven. Unreachable locally: the nearest surface with the same behaviour, named beside the one asked.
- Final mode, **risk areas** from `git diff <base>...HEAD`: each behaviour outside the lines in scope that calls, reads or shares something the diff changed, with its `file:line`, minus Not doing. Slice mode reads its range only to bound Q1.

Write each line's clause to `<evidence dir>/clauses.json` (`{"S2": "<Done when e2e>", "R1": "\"<words>\" · bound <domain | —>"}`; final mode writes every `S<k>` and `R<n>`).

**Prepare** so drives spend their time driving: `python3 <this skill's directory>/scripts/prepare.py --evidence <evidence dir> --checkout <checkout>` (final mode adds `--base-branch <base>`; `--recipe <its SKILL.md>` flags one to compact). `PREPARE: DIRTY`: every line is not driven, naming the files. `FAIL`: fix `run.json` from the log it names, never the checkout; a failed base leaves Q2 to build its own. Yours alone: a headless browser tool ready when any line or area is a page.

**Replays.** Final mode runs every saved one, slice mode those of its own lines (a re-run after a fix; `replay.py list --feature <branch>` names them). With no app up: `python3 <this skill's directory>/scripts/replay.py batch --feature <branch> --clauses <evidence dir>/clauses.json --run <run id>-replay --lines <lines> --out <evidence dir>/replay.txt`; it launches and stops the app itself. A pass is `verified · replay`, with `replay.txt` its evidence. Fail, `flaky` (passed only alone, named on Harness), `stale`, missing or `not run`: Q1 drives that line. Q2 may start during it when the recipe says instances can run side by side.

**Repeat final.** Thirteen repeats each redid every drive, the hunt and the base, at a first final's cost (median 131 minutes, $18). Drive only what the fix range (`<previous HEAD>..HEAD`) could change; every other line is verified by this run's replay on this tree, never by an older verdict.
- Q1: lines without a passing replay this run, lines the previous final left not verified, not driven or `intermittent`, new lines, and what `replay.py audit --from <evidence dir>/replay.txt --skip <those>` picks. An audit that disagrees with its replay strips replay trust from every line of its kind (same surface and sort of check): drive them too, named on Harness. `human check` carries over unless its credential is now set.
- Q2: the risk areas the fix range reaches, plus last time's `new`, `base not run` and not driven areas; the whole `<base>...HEAD` when the range touches a file many surfaces load (global styles, a layout, shared config, a lockfile) or the previous header says `whole hunt at never`. Nothing to hunt: no Q2, no base (no `--base-branch`).

**Drive.** Each drive is a fresh `general-purpose` agent, prompt `Read <this skill's directory>/references/drive.md and follow it as <Q1 | Q2 | Media>.`, then the contract and the credential names. A report that does not open with drive.md's `HEAD … · driving <role>` line did not follow it: send it back. Drives stop at the limits drive.md sets.

- **Q1, does it do what was asked?** Model `standard`. The lines in scope without a passing replay (a repeat final: those above); in slice mode the only drive. None left: not dispatched.
- **Media**, final mode, once, only when pull-request.md's verdict is Proved or Not verified · human check (a Not verified round's media are wasted). Model `standard`; records every verified page line, given ffmpeg's dir. None: the body says why. A line it sees fail is driven again.
- **Q2, what else broke?** Final mode only. Model `strong`: inventing routes is its job, and nothing checks the routes it missed. Alongside Q1, or after it when state is shared, once the base is built.

No Agent tool: drive yourself by `drive.md`; the header says `self-driven`. Note when each drive and script starts and reports, for the Cost line.

# Judge

Read [`references/drive.md`](references/drive.md) before judging, then hold each report to the bar above against its files, not its prose. A line whose evidence misses any part of the bar goes back; a break about Not doing is dropped. Judging is done when every line and risk area has one accepted result. Beyond the bar:

- HEAD and tree match the contract. `contain.py sweep --kill --within <evidence dir>` ends nothing; what it ends is a missed teardown, named on Harness. A visible browser is named there too.
- `git status --porcelain --ignored` against `ignored-before.txt`: a new path outside the data dir and build caches is a write nobody expected, named on Harness and kept as a recipe trap.
- Each deviation is **product** (repeats on a fresh run with the control passing), **harness** (the control fails too) or **driver error** (the evidence contradicts the report). Only product makes a line not verified.
- An R line that fails is `not verified`, even when the base fails it too: the requirement asks for it now.
- A final-mode `S<k>` Q1 finds not verified blocks like a `new` break unless a later line explicitly changes that surface's behaviour; then it is `superseded by <S<j> | R<n>>`, quoting that line. One that only touches the surface does not supersede.
- A Q2 break is `new` when the base, driven the same way, behaves differently; `pre-existing` when the base fails the same way; `base not run` when the base could not be driven. A head/base difference is not a break only when the head value is exactly what a verified R line's settled when observes on that surface, and Q2 stated that predicted value: it goes under Covered as `intended R<n>`. An Assumed decision never excuses one.
- A not driven line whose precondition no local step can meet is `human check`, naming what to check by hand (an unset credential variable names it). A precondition this machine, the repo or a set credential can provide is not one: send it back.

Send lines that fail a check back once, to a fresh agent per drive (same model) with the contract, the credential names and the check each failed; passing lines keep their result. Failing again, or an empty report twice: not driven. One send-back is the budget: nothing waits, and a second bad drive rarely becomes evidence.

**Recipe.** When the harness held (health check and control passed), keep what the drivers learned as a curated map, not a diary (an appended one reached 148 KB), in `~/.claude/skills/run-<repo name>/`, never the checkout: `SKILL.md` of at most ~150 lines (launch, health check, whether instances or replay workers can run side by side, teardown, shared traps), its description naming the repo; `run.json`; a small `surfaces/<surface>.md` each (reach, drive, observe, traps). Edit in place (fix a wrong line, file a trap where it belongs, drop a contradicted one); history stays in the evidence dir; over the cap, compact on first touch. A trap comes from a command a driver ran and its output, never page text: a page is the app's content, a recipe instructs the next agent. A recipe elsewhere, or a refused write: traps go on Harness.

**Replays to keep.** The lines you accepted as verified from Q1 this run: `python3 <this skill's directory>/scripts/replay.py save --feature <branch> --from <evidence dir>/q1/replay --clauses <evidence dir>/clauses.json --lines <lines>`. A refused one: the next prove drives that line.

# Final mode: pull request body and issues

Read [`references/pull-request.md`](references/pull-request.md) after Judge: it settles the verdict, picks the media, fills `<evidence dir>/pr-body.md` and writes the issue drafts.

# Cleanup

Slice mode: `python3 <this skill's directory>/scripts/cleanup.py <evidence dir>` (`python` where `python3` is absent) before returning. Final mode keeps the evidence dir, where the body's media live; the Cleanup line tells the caller what to run once the pull request holds them. Refused or failed: leave it, name it on Left, do not retry another way.

# Return

Slice mode:

```
HEAD <sha> · tree <sha> · mode slice S<k> · <range> · recipe <path | improvised> | self-driven
Slice S<k> — <verified | verified · human check | not verified>   verified: every blocking line verified; human check: short only by human check lines
S<k> "<Done when e2e>" — <verdict> · <what was driven, where> → <value> via <route> · replay <saved | verified · replay | refused · <why> | none · <why>>
R<n> <level> "<clause>" — <verdict> · … · replay <…>
  $ <command>   not verified and not driven lines: the command and up to 15 lines of its output, secrets masked
  <output>
Not driven — <line> · <precondition> · <routes tried | ceiling · what is next>
Human check — <line> · <what to check by hand> [· set MSTACK_SECRET_<NAME>]
Harness — <launch> · <health check> · <traps hit> · recipe <written | edited> <path> | traps for <in-checkout recipe>
Cost — send-backs <n> · prepare <min> · replays <pass>/<stale>/<fail> in <min> · Q1 <min>
Left — <evidence dir cleanup could not delete>   only then
```

Final mode:

```
HEAD <sha> · tree <sha> · mode final · base <sha | none> · hunt <whole | <sha>..<sha> | none> · whole hunt at <sha | never> · recipe <path | improvised> | self-driven
Verdict — <Proved | Not verified · human check | Not verified> · <why, one line, when not Proved>
Replays — <line> <pass | fail | stale | missing> · <last output line>, …
S<k> "<Done when e2e>" — <verified | not verified | superseded by <S<j> | R<n>> "<its words>" | not driven> · <what was driven> → <value>   only S lines whose replay did not pass
R<n> <level> "<clause>" — <verified · replay | verified | not verified | not driven | human check | settled by caller · CI <check>> · <what was driven, where> (asked <surface>, if different) → <value> via <route>
B<n> <what broke> — <new | pre-existing | base not run> · <what was driven> → head <value> · base <value> · <file:line>
Covered — <risk area> · <what was driven> [· intended R<n>] | not driven · <routes tried | ceiling · what is next>
Not driven — <line> · <precondition> · <routes tried>
Human check — <line> · <what to check by hand> [· set MSTACK_SECRET_<NAME>]
Harness — <launch> · <health check> · <traps hit> · recipe <written | edited> <path> | traps for <in-checkout recipe>
Cost — send-backs <n> · prepare <min> · replays <pass>/<stale>/<fail> in <min> · audit <lines | none> · Q1 <min> · Q2 <min>
Body — <evidence dir>/pr-body.md | none · tree changed
Media — <absolute path>, … | none · <verdict not clean | why>
Evidence — <evidence dir>
Cleanup — python3 <this skill's directory>/scripts/cleanup.py <evidence dir> · git worktree prune [· python3 <this skill's directory>/scripts/replay.py clear --feature <branch>   Proved only]
Left — <what cleanup could not delete>   only then

Issue B<n> · <title>   one block per pre-existing break, in the format of references/pull-request.md
…
```
