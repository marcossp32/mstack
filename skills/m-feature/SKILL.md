---
name: m-feature
description: Takes one reviewed spec to a pull request proved in the running app, with nobody watching. Use only when asked to run /m-feature with a spec reference, which starts that spec's feature or resumes it.
disable-model-invocation: true
---

# m-feature

Turn one already-reviewed spec into a pull request a reviewer can merge, with nobody watching the run. `/m-feature <spec ref>` starts it or resumes it; the argument may also be the feature's state item. This skill owns order, routing, the state and the few lines the chat shows; the skills it loads or dispatches do the work.

The reviewer gets a PR whose top says whether each requirement holds in the running app, then every decision made without a human, with its sources. Success is a PR whose verdict is Proved, or `Not verified · human check` with only lines a person must check left. A Not verified PR is the run failing, never a way to end it: while something can still be fixed, researched or debated, the run goes on.

## Done when

The run ends on one of three lines:

- the final PR line ([`references/closing.md`](references/closing.md)), after every box below holds;
- the setup stop (Start), with nothing created;
- a stop for a person ([`references/escalation.md`](references/escalation.md), Stop for a person), with the state saved for a resume.

Before printing the final PR line, check on the host and the state:

- [ ] One open PR from `feature/<name>` into the state's Base; a draft (or carrying the do-not-merge line) unless Proved.
- [ ] Its verdict comes from a final prove of the tree the PR head shows (or the PR notes md's markdown-only `publish-issues` commit after it).
- [ ] The state has the headings of [`references/state.md`](references/state.md) in order; every Requirements line has its `from`; Spec holds the frozen copy's hash.
- [ ] Every slice on `Slices ·` has a closed line: `verified`, `verified · human check <lines>`, or `not verified · … · gap accepted by D<k>`; every step item is closed, or listed on its slice's not verified line.
- [ ] Every Debates line, Assumed line, `mstack:contradiction` and `found-by-prove` issue appears in the PR; each issue carries `Origin · feature <name> · PR <link>`.
- [ ] Every refused command is under To merge with the setup-mstack entry that would allow it.
- [ ] No credential value in the state, any item, issue, commit message or the PR body; no local path in the PR's media.
- [ ] The step check baseline is cleared and the final evidence dir deleted, or named in the final line.

## What holds on every route

- **Adapters.** Every tracker and host action is an adapter operation (`tracker read-spec`, `host open-pr`, …), whose commands live only in its file. Read `references/trackers/<tracker>.md` and `references/hosts/<host>.md` before the first operation of each. Git runs directly; the remote is `origin`, and anything compared against a remote branch is compared after a fetch, since a stale local branch puts other work in the diff.
- **The state is the truth.** Read [`references/state.md`](references/state.md) before creating the state or resuming one. With the pushed `feature/<name>`, it is all a new session on another machine has: write what a resume needs before relying on it, and where the state and your memory disagree, the state wins.
- **Two stops; nothing else waits for a person.** The run stops at the setup stop, before anything exists, and when a requirement cannot hold without a person (escalation.md, Stop for a person). Anywhere else a human would be asked, decide and record why under Assumed, research it, or debate it.
- **Credentials** come only from environment variables `MSTACK_SECRET_<NAME>`. Stages get their names, never their values, and a value is written nowhere: people who must not see it read the state, issues and PR.
- **A refused command** is recorded for the PR's To merge and the run goes on with what does not need it; retrying it in another form is the bypass the refusal exists to block (escalation.md, Refused commands).
- **The spec is frozen** at Start: every stage reads the frozen copy, so a mid-run edit cannot move the target; a later change is noted in the PR.
- **Chat**: what this chat prints for the human is one line per slice closed, one per debate, the final PR line or a stop line, each in the form given where it is printed. The state holds the detail.
- **Judges are not builders.** The step check (a script), the quality review and the prove judge the work. Each judge that is an agent is a fresh one that did not write the code and has not seen this chat, and only a judge clears its own finding: your reading of the code settles nothing. A judge passes only when the work changes: tests, the spec and every Done when stay as they were, since changing one to pass hides the failure it was there to find.
- **Waiting.** Prove, build and step check can idle this chat for an hour or more. The prompt cache keeps this context cheap to read back for about an hour of silence; the first call after it lapses writes the whole context again, while a wake costs almost nothing. So no silence reaches the hour: before each wait, arrange a wake 45–55 minutes after your last call (a scheduled wake, a background timer whose exit notifies you, a monitor). A stage that will end well inside the hour wakes you with its own exit notice: set no timer beside it. Each wake checks only whether the stage has ended, then arranges the next.
- **Other skills' directories**: `<m-requirements dir>`, `<m-review dir>` and `<m-prove dir>` are this skill's sibling directories, where their scripts live.

## Start

Done when: the setup stop line is printed and nothing was created, or a state item, a pushed `feature/<name>` and a frozen spec exist. Then Understand.

- **Config before anything is created**, so the setup stop leaves nothing behind. Read `.mstack.yml` (`tracker`, `host`, optional `jira: project:`, `md: dir:` default `.mstack/`). Missing: deduce `host` from `git remote get-url origin` (github.com → `gh`, gitlab → `gitlab`, bitbucket.org → `bitbucket`) and `tracker` from the spec reference (`#123` or a GitHub issue URL → `gh`, `ABC-123` or an atlassian URL → `jira`, a path to a `.md` file → `md`). Then `tracker check`, `host check` and `tracker read-spec`. A value that cannot be deduced, a missing adapter file, a failed check or an unreadable spec: print this line and end.
  ```
  Stop · <what is missing: tracker | host | <tool> not installed or not authenticated | spec <ref> unreadable> · run /setup-mstack
  ```
- **One state per spec**, since two would split the truth. The argument is itself a state (it has the state's headings), or a `feature:map` item already names this spec (`tracker find-issue`): go to Resume.
- **`<name>`** is kebab-case from the spec title, and `feature/<name>` is new on the remote, so two features never share a branch.
- **Frozen spec**: the text `read-spec` returned, saved at `<git common dir>/mstack/spec/<name>.md` (`git rev-parse --path-format=absolute --git-common-dir`), its sha256 on the state, the text as a state comment so a resume elsewhere can restore it.
- **Base**: the branch the spec names, else `host default-branch`.
- **Labels** `feature:map build found-by-prove mstack:contradiction` exist (`tracker ensure-labels`).
- **`feature/<name>`** cut from `origin/<base>` and pushed.
- **State** created (`tracker create-state <name> <title> <body>`) with Spec, Base and a provisional How hard to undo; linked to the spec when the spec is a tracker item.

## Resume

The session may be new: rebuild from the state and the remote. Re-run Start's config and checks; settle the base. Read the state with its comments; restore the frozen copy from its comment when it is missing on disk; if the live spec's hash differs from Spec's, note `Spec changed · <date>` once and go on with the frozen copy. Read the feature branch's first-parent log and any local `step/<name>-*` branches: steps push nothing, so unmerged work exists only on the machine that built it. Bring up the prerequisites and the baseline unless resuming at Closing. Then continue at the first milestone below that the state does not yet show; inside a slice or at Closing, at the point state.md (Resume points) names.

## How hard to undo

If this ships wrong, how hard is it to undo? You decide; stages only report evidence. Hard is a change others come to depend on or data gets stored in (a schema, a public API, a stored format, a core dependency); easy is one a later commit reverses whole (names, folders, internal structure). Build runs strong when it is hard, and quality review and plan receive it. Settle it again after scan and after docs, since a vendor limit can change it; then it holds unless a debate changes it.

## Understand

Done when the state holds the requirements block, the scan answers, the docs answers, every open decision debated (`→ D<k>`), every contradiction with its issue, and every line only a person can unlock either has its credential set or has stopped the run; the prerequisites run and the step check baseline is recorded. Then Plan.

- **Requirements and scan** start together, since neither needs the other: one fresh agent for requirements and the scan split by question group, each dispatched as Dispatch says.
- **The requirements block is accepted** once `python3 <m-requirements dir>/scripts/check.py --spec <frozen copy> --out <block file>` passes it. A failing block goes back with its FAIL lines while each resend fixes some; when one stops improving, accept it and list each FAIL line under Assumed and the PR's What to watch. Its seven state sections (Requirements, Not doing, Considered, Contradictions, Open decisions, Assumed, How to build) go into the body verbatim; Laziest build and Trace go in a comment. It never runs again on resume: its ids are what everything after cites.
- **Scan answers** go on the state as one comment; Where it runs comes from Q8.
- **Prerequisites and the baseline** need scan Q6 and Q9 and exist before the first step check, which compares against the baseline. Read [`references/slice-loop.md`](references/slice-loop.md) before starting them.
- **Docs.** Once scan has returned the installed versions (Q1) and infrastructure (Q8), and requirements the open decisions, call the Skill tool with `m-research`, in this chat. Ask: the hard limits of the service or library; the documented timeout, as a number; the vendor's security guidance (auth, secrets, what never to log); what changed in the installed version; and, for each hard-to-undo open decision, what the standard and vendor docs say and which alternatives they document. A question with no subject is answered "not applicable". Done when its quoted answers are a state comment, their links under Sources.
- **Debates before planning.** Each open decision `O<n>` (all hard to undo; easy ones are Assumed), each hard-to-undo contradiction, and each derived requirement that is the only line covering a hard-to-undo behaviour (whether it is required) goes to a debate, with scan's versions and limits among its Facts, since requirements ran without them. Read [`references/escalation.md`](references/escalation.md) before the first.
- **What only a person can unlock.** Some lines can only be driven with something a person holds: a login of a given kind (a buyer, an admin), a service key, an approval. Found at the final prove, the gap leaves the PR Not verified after all the work; found now, it costs one stop. Start from the requirements block's Assumed lines `R<n> needs …`, and read every line's bound and the spec for others. An agent can drive a line once its credential is set as an `MSTACK_SECRET_<NAME>` variable; one a line needs that is not set is a stop for a person (escalation.md) now, naming the variable and what it unlocks. A line settled by the host's CI needs no person: Closing settles it.
- **Contradiction issues**: each contradiction gets one `mstack:contradiction` issue saying the reading built, its ref beside the entry, never opened twice. Read [`references/closing.md`](references/closing.md) (Issues) for its body before opening the first.

## Plan

Done when the plan block is a state comment, each step has an item with its blocking links, and the `Slices ·` line (item refs) heads Decided. Nobody confirms the plan: then Per slice.

`m-plan` runs in its own context and writes the plan and every step body to files, so the tens of thousands of tokens it reads and writes never enter this chat; its reply is the few lines this chat acts on.

- Its inputs go as files, never retyped, since a requirement retyped can drift by a word every step then quotes. Save `tracker read-state` (body and comments) to a file under `Out` by redirecting its output; on `md` the state files are already files. `Out` is `<git common dir>/mstack/plan/<name>/<cut>/`, absolute, `<cut>` being `1` for the first plan and the `D<k>` that leads to each later one.
- Call the Skill tool with `m-plan`, its argument those paths (and any input already a file: the frozen spec, a debate record, the previous plan's `Out`), Where it runs, and `Out`. Done when its reply ends `Check · PLAN CHECK: PASS`. A reply `Stop · no <Out | requirements> given` names what your call lacked: call again with it.
- The plan and step files go to the adapter by path and are never opened here: `plan.md` becomes a state comment; step `<n>` is `tracker create-step` with its reply line's title and `step-<n>.md` as the body, fed from the file as the adapter says. A body retyped or filled into a template drifts, or ships a placeholder instead of the work.
- From the reply: `tracker link <blocked> <blocking>` for each Blocking pair; the `Slices ·` line with numbers rewritten to item refs; the `Slice S<k>` lines, which review and prove receive verbatim; its `Assumed ·` line holds several choices, each with its why: each becomes one line under the state's Assumed (state.md gives the shape).
- An `Open ·` line is debated, then `m-plan` is called again with the decision and the previous `Out`; each step number without an item then gets one (`Changed · new` and those that waited), and each `dropped` one is closed with `Replaced by D<k>`. A step whose reply line ends `· waits D?` gets its item only after that decision, so nothing is built on a guess.
- A resume that finds the plan comment but not every item, on a machine without the plan files, calls `m-plan` again with the same inputs and the plan comment as the plan given: m-plan keeps each number on its work, and only steps with no item get one.

## Per slice

Read [`references/slice-loop.md`](references/slice-loop.md) before the first slice. Done, per slice in plan order, when its Decided line is closed (state.md, Slice lines) and its line printed:

```
S<k> · verified | verified · human check <lines> | not verified · <what works now | why>
```

Then the next slice; after the last, Closing.

- Steps are built one at a time, each merged into `feature/<name>` only after its step check passes, so each builds on checked work; every merge is pushed for resume.
- After the slice's steps merge: quality review ⇄ fix, then slice prove ⇄ fix. Quality fixes come first: they change code the prove must see, and a prove is the costly judge.
- A failure is fixed by the builder in fix mode. One that one more fix cannot settle goes to a debate (escalation.md). Rounds go on while they make progress; a loop changes the question or stops for a person (escalation.md, Progress or loop).

## Closing

Starts once every slice line is closed. A slice whose last prove was not verified is open, however much was merged after it: it goes back to its own loop (fix, then slice prove) or to a debate, since a final over a slice known to fail ends Not verified on it. Read [`references/closing.md`](references/closing.md) before Closing's first act: the draft PR, so CI runs while the final prove does; final prove ⇄ fix; found-by-prove issues; the PR with its media; cleanup; the final line.

## Dispatch

A stage that runs as an agent runs as a fresh one, never a fork, which inherits this conversation's reasoning. It has not seen this chat and runs no tracker or host command: paste verbatim every state section, step item and spec excerpt it needs, read just before; a section that needs changing changes on the state first.

The prompt opens by having the agent load its stage's skill, so it works under that skill's rules:

```
Call the Skill tool with `<m-requirements | m-scan | m-build | m-prove>`. Then do the work below.
```

A dispatch is done when its reply is the return its skill defines, which only a run under that skill produces: requirements, the block `check.py` judges; scan, one `Q<n>` line per question its question group owns; build, a notes path or a `Stop ·` line; prove, its Return block. Any other reply, or one missing part of its return, was not made under the skill: dispatch again. A second such reply means a resend will not fix it: inside a slice, that slice is failing (Progress or loop, then a debate); in Understand, what is missing goes under Assumed and the PR's What to watch, and the run goes on.

Models are tiers: cheap, standard and strong, the harness's quickest, middle and most capable. A tier that does not resolve runs on the session's.

| Stage | Runs in | subagent_type | Model |
|---|---|---|---|
| requirements | fresh agent loading `m-requirements` | `general-purpose` | standard; `check.py` checks its block |
| scan question group A (Q1) | fresh agent loading `m-scan` | `Explore` | cheap |
| scan question groups B (Q2–5), C (Q6, Q9), D (Q7–8) | fresh agent loading `m-scan` | `Explore` | standard |
| docs | this chat, `m-research` loaded; it dispatches its own agents | — | its own |
| debate | `m-debate` through the Skill tool, the block as its argument; it runs in its own context and dispatches its own agents, so only its reply lines reach this chat | — | its own |
| plan, re-cut | `m-plan` through the Skill tool, the paths of its inputs as its argument; it runs in its own context, so only its reply lines reach this chat | — | the session's |
| build, fix mode included | fresh agent loading `m-build`, one at a time | `general-purpose` | standard; strong when How hard to undo is hard |
| step check | this chat, `step_check.py` | — | none |
| quality review, re-review | this chat, `m-review` loaded; it dispatches its own fresh reviewer | — | its own, from How hard to undo |
| prove, slice and final | fresh agent loading `m-prove` (the supervisor) | `general-purpose` | strong; it dispatches its own drivers |

Inputs each stage needs:

| Stage | Inputs |
|---|---|
| requirements | the frozen copy's path · the spec's ref · the checkout path (read-only) |
| scan | the spec title and frozen copy's path · the question group it owns |
| build | the step item's ref and body verbatim, or the path of its step file, which reaches the builder as written · Not doing and How to build verbatim · scan Q2–Q9 · docs answers or "not applicable" · the step branch it is on (checked out) and its feature branch |
| build, fix mode | the same, with the fix step item, whose body lists what to fix: step check output, quality findings (`F<n>` lines with their kind, `file:line` and evidence), or prove failures (the requirement or slice Done when, the value seen, an evidence excerpt; for a comparison, every differing cell), never prove's replays · a debate decision, when one led here |
| debate | the block in escalation.md (Running a debate) |
| quality review | the diff range `<slice start sha>..<slice end sha>` · the slice's `Slice S<k> · Done when e2e …` line verbatim · the Requirements lines it serves, verbatim, and the Assumed lines that name those ids · How hard to undo · Not doing verbatim · the repo's rule files that exist (`CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `.claude/rules/`, `.cursor/rules/`, style guides the repo names) · scan Q1, Q4, Q5 · the docs answers with their quotes and links |
| re-review | only the findings to recheck and the fix range |
| prove, slice | `mode: slice` · the feature branch · the slice id and its `Slice S<k> · Done when e2e …` line verbatim · the Requirements lines it serves, verbatim · diff range `<slice start sha>..HEAD` · scan Q9, and Q6's `env` (its regression hunt runs tests) · Not doing · each `MSTACK_SECRET_<NAME>` set in the environment, by name, with what it unlocks |
| prove, final | `mode: final` · the feature branch · every Requirements line verbatim but those `retired by D<k>` · every `Slice S<k>` line · base: the bare base branch name (m-prove adds `origin/`), after `git fetch` · scan Q9, and Q6's `env` · Not doing, Assumed · credential variable names · the PR body with its `<!-- prove: … -->` placeholders (closing.md, Body) · after a fix round, `previous final:` the previous final's Return block |
