---
name: m-feature
description: Takes one reviewed spec to a pull request proved in the running app, with nobody watching. Use only when asked to run /m-feature with a spec reference, which starts that spec's feature or resumes it.
disable-model-invocation: true
---

Turn one already-reviewed spec into a pull request a reviewer can merge, with nobody watching the run. The user starts or resumes it with `/m-feature <spec ref>`; the argument may also be the feature's state item. This skill owns order, routing, the state and the few lines the chat shows; the stage skills it loads do the work. The reviewer gets a PR whose top shows whether each requirement holds in the running app, and every decision made without a human, with its sources.

# Done when

A pull request from `feature/<name>` into the base is open on the host, its verdict Proved or Not verified from a final prove of the tree it shows, every slice of the plan closed under the state's Decided (verified with its evidence, or not verified with why and `gap accepted by D<k>`), every debate listed in the PR, every `found-by-prove` and `mstack:contradiction` issue linked from it, and the final line printed. Or the run printed a stop line: the setup stop, with nothing created, or a stop for a person ([`references/escalation.md`](references/escalation.md), Stop for a person), with the state saved for a resume.

# Acceptance criteria

- [ ] The host shows one open PR from `feature/<name>` into the base named under the state's Base; it is a draft (or carries the do-not-merge line) unless its verdict is Proved.
- [ ] The state item has the headings of [`references/state.md`](references/state.md) in order; every Requirements line has a `from`; Spec holds the frozen copy's hash.
- [ ] The `Slices ·` line lists every slice, and each has a closed Decided line: `verified` with its evidence, or `not verified` with why and `gap accepted by D<k>`.
- [ ] Every Debates line appears in the PR's Debates section, and its record is a state comment.
- [ ] Every Contradictions entry names an open `mstack:contradiction` issue; every pre-existing break prove returned names a `found-by-prove` issue (opened or commented); each is linked from the PR and carries an `Origin · feature <name> · PR <link>` line.
- [ ] Every step item is closed, or listed in its slice's not verified line.
- [ ] No credential value appears in the state, any item, issue, commit message or the PR body; no PR media is a local path.
- [ ] Every refused command appears under To merge with the setup-mstack entry that would allow it.
- [ ] Every Assumed line appears under the PR's Decisions made without a human.
- [ ] The PR verdict comes from a final prove whose tree equals the PR head's tree, or the PR notes the markdown-only publish-issues commit after it.
- [ ] The step check baseline is cleared and the final evidence dir is deleted, or named in the final line.
- [ ] Every message addressed to the human is a slice line, a debate line, the final PR line or a stop line.

# Ground rules

- **Adapters.** Every tracker and host action is an adapter operation (`tracker read-spec`, `host open-pr`, …). Read `references/trackers/<tracker>.md` and `references/hosts/<host>.md` before the first operation: tool commands live only there, so a run can use any tracker and host. Git runs directly; the remote is `origin`, and anything compared against a remote branch is compared after a fetch, since a stale local branch puts other work in the diff.
- **The state is the truth.** Read [`references/state.md`](references/state.md) before creating the state or resuming one: its headings, branches and resume points. It lives in the tracker and, with the pushed `feature/<name>`, is all a new session on another machine has. Write what a resume needs before relying on it; where the state and your memory disagree, the state wins.
- **Two stops, nothing else waits.** The run stops at the setup stop, before anything exists, and when a requirement cannot hold without a person ([`references/escalation.md`](references/escalation.md), Stop for a person). Anywhere else a human would be asked, decide and record why (Assumed), research it, or debate it. A Not verified PR is a failure, never a way out.
- **Credentials** come only from environment variables `MSTACK_SECRET_<NAME>`. Stages get their names, never their values, and a value is written nowhere: the state, issues and PR are read by people who must not see it.
- **A refused command** is recorded for the PR's To merge, and the run goes on with what does not need it; never retried in another form, the bypass the refusal exists to block ([`references/escalation.md`](references/escalation.md), Refused commands).
- **The spec is frozen** at Start: every stage reads the frozen copy, so a mid-run edit cannot move the target; a later change is noted in the PR.
- **Chat is minimal**: one line per slice closed, one per debate, the final PR line, each in the form given where it is printed. The state holds the detail.
- **Waiting keeps the context warm.** Long stages (prove, build, step check) idle this chat for an hour or more. The prompt cache lives about an hour; the first call after it lapses rewrites this whole context (a tenth of the orchestrator's cost in past runs), while a wake costs almost nothing. So no idle gap or foreground wait may outlast the cache: before each wait, arrange a wake about 45-55 min after your last call (a scheduled wake, a timer or command whose exit notifies you, a monitor); sooner is calls for nothing. When the awaited stage's own exit notice comes well inside the hour, it is the wake: set no timer beside it. Each wake checks the stage, reads nothing else, and arranges the next.
- **Other skills' directories**: `<m-requirements dir>`, `<m-review dir>` and `<m-prove dir>` are this skill's sibling directories, where their scripts live.

# Start

Outcome: either the setup stop line and nothing created, or a state item, a pushed `feature/<name>` and a frozen spec, ready for Understand.

- **Config first, before creating anything**, so the setup stop leaves nothing behind. Read `.mstack.yml` (`tracker`, `host`, optional `jira: project:`, `md: dir:` default `.mstack/`). Missing: deduce `host` from `git remote get-url origin` (github.com → `gh`, gitlab → `gitlab`, bitbucket.org → `bitbucket`) and `tracker` from the spec reference (`#123` or a GitHub issue URL → `gh`, `ABC-123` or an atlassian URL → `jira`, a path to a `.md` file → `md`). Then `tracker check`, `host check` and `tracker read-spec`. A value that cannot be deduced, a missing adapter file, a failed check or an unreadable spec: print this line and end.
  ```
  Stop · <what is missing: tracker | host | <tool> not installed or not authenticated | spec <ref> unreadable> · run /setup-mstack
  ```
- **One state per spec**, since two would split the truth. The argument may itself be a state (it has the state's headings), or a `feature:map` item may already name this spec (`tracker find-issue`): either way, Resume.
- **A name of its own.** `<name>` is kebab-case from the spec title, and `feature/<name>` is new on the remote: branch names carry it, so two features never share a branch.
- **Frozen spec**: the text `read-spec` returned, saved at `<git common dir>/mstack/spec/<name>.md` (`git rev-parse --path-format=absolute --git-common-dir`), its sha256 on the state, the text itself as a state comment so a resume elsewhere can restore it.
- **Base**: the branch the spec names, else `host default-branch`.
- **Labels** `feature:map build found-by-prove mstack:contradiction` exist (`tracker ensure-labels`).
- **`feature/<name>`** cut from `origin/<base>` and pushed.
- **State** created (`tracker create-state <name> <title> <body>`) with Spec, Base and a provisional How hard to undo; linked to the spec when the spec is a tracker item.

# Resume

The session may be new: rebuild from the state and the remote. Re-run Start's config and checks; settle the base. Read the state with its comments; restore the frozen copy from its comment when it is missing on disk; if the live spec's hash differs from Spec's, note `Spec changed · <date>` once and go on with the frozen copy. Read the feature branch's first-parent log and any local `step/<name>-*` branches: steps push nothing, so unmerged work exists only on the machine that built it. Bring up prerequisites and the baseline unless resuming at Closing. Then continue at the first outcome below that the state does not yet show; inside a slice, at the point [`references/state.md`](references/state.md) (Resume points) names.

# How hard to undo

If this ships wrong, how hard is it to undo? You decide; stages only report evidence. Hard is a change others come to depend on or data gets stored in (a schema, public API, stored format, core dependency); easy is one a later commit reverses whole (names, folders, internal structure). It sets depth and tiers: build and quality review run strong when hard. Settle it again after scan and after docs, since a vendor limit can change it; then it holds unless a debate changes it.

# Understand

Outcome: on the state, the requirements block, the scan's nine lines, the docs answers, every open decision debated (`→ D<k>`), every contradiction with its issue; prerequisites running and the step check baseline recorded.

- **Requirements and scan** start together, since neither needs the other: one fresh agent for requirements and the scan split by question group, each dispatched as [Dispatch](#dispatch) says.
- **The requirements block is accepted** only once `python3 <m-requirements dir>/scripts/check.py --spec <frozen copy> --out <block file>` has judged it. A failing block goes back with its FAIL lines while each resend fixes some; when one stops improving, accept it and list each FAIL line under Assumed and the PR's What to watch, since nothing waits. Its seven state sections go into the body verbatim; Laziest build and Trace go in a comment. It never runs again on resume: its ids are what everything after cites.
- **Scan answers** go on the state as one comment; Where it runs comes from Q8. A scan agent missing one of its questions goes back for it, as [Dispatch](#dispatch) says.
- **Prerequisites and the baseline** need scan Q6 and Q9 and exist before the first step check, which compares against the baseline. Read [`references/slice-loop.md`](references/slice-loop.md) before starting them.
- **Docs.** Call the Skill tool with `m-research`, in this chat, once scan has returned the installed versions (Q1) and infrastructure (Q8) and requirements has returned the open decisions, since its questions need both. Ask: the hard limits of the service or library; the documented timeout, as a number; the vendor's security guidance (auth, secrets, what never to log); what changed in the installed version; and, for each hard-to-undo open decision, what the standard and vendor docs say and which alternatives they document, as quotable facts that ground its debate. A question with no subject is answered "not applicable". Done when its quoted answers are a state comment, their links under Sources.
- **Debates before planning.** Each open decision `O<n>` (all hard to undo; easy ones are Assumed) and each hard-to-undo contradiction goes to a debate with scan's versions and limits among the Facts, since requirements ran without them; so does a derived requirement that is the only line covering a hard-to-undo behaviour (whether it is required). Read [`references/escalation.md`](references/escalation.md) before the first.
- **What only a person can give.** Some requirements can only be driven with something a person holds: a login (a buyer, an admin), a service key, an approval. Found at the final prove, the gap leaves the PR Not verified after all the work; found now, asking costs nothing. The requirements block names each line a local run cannot settle as an Assumed line `R<n> needs …`; start from those. Credentials arrive as `MSTACK_SECRET_<NAME>` environment variables; one a requirement needs and that is not set is a Stop for a person ([`references/escalation.md`](references/escalation.md)), naming the variable and what it unlocks. A `· CI <check>` line needs no person: Closing settles it from the host's checks.
- **Contradiction issues**: each contradiction gets one `mstack:contradiction` issue saying the reading built, its ref beside the entry, never opened twice. Read [`references/closing.md`](references/closing.md) (Issues) for its body before opening the first.

# Plan

Outcome: the plan block as a state comment, one step item per step with its blocking links, and the `Slices ·` line (item refs) at the top of Decided. No confirmation: the plan is saved and run.

`m-plan` runs in its own context and writes the plan to files: what it reads and writes (the repo, the plan, every step body) is tens of thousands of tokens this chat would otherwise carry on every later call. Its reply is the few lines this chat acts on.

- Its inputs go as files, never retyped: a requirement retyped by hand can drift by a word that every step then quotes. Save `tracker read-state` (body and comments: Requirements with their `retired by D<k>` markers, Not doing, Considered, Contradictions, Assumed, How to build, Debates, How hard to undo, scan Q1–Q9, the docs answers) to a file under `Out` by redirecting its output; on `md` the state files are already files. `Out` is `<git common dir>/mstack/plan/<name>/<cut>/`, absolute (`git rev-parse --path-format=absolute --git-common-dir`), `<cut>` being `1` for the first plan and the `D<k>` that leads to each later one.
- Call the Skill tool with `m-plan`, its argument those paths (and any input already a file: the frozen spec, a debate record, the previous plan's `Out`), Where it runs, and `Out`. Done when its reply ends `Check · PLAN CHECK: PASS`.
- Never open the plan or step files: hand them to the adapter by path, so neither passes through this chat. `plan.md` is a state comment; step `<n>` is `tracker create-step` with its reply line's title and `step-<n>.md` as the body, fed from the file as the adapter says. A body retyped or filled into a template by hand drifts, or ships a placeholder instead of the work.
- From the reply: `tracker link <blocked> <blocking>` for each Blocking pair; the `Slices ·` line with numbers rewritten to item refs; the `Slice S<k>` lines, which review and prove receive verbatim; its Assumed lines join the state's.
- An `Open ·` line is debated, then `m-plan` is called again with the decision and the previous `Out`; each step number without an item then gets one (`Changed · new` and those that waited), and each `dropped` one is closed with `Replaced by D<k>`. A step whose reply line ends `· waits D?` gets its item only after that decision, so nothing is built on a guess.
- A resume that finds the plan comment but not every item, on a machine without the plan files, calls `m-plan` again with the same inputs and the plan comment as the plan given: **Numbers** in m-plan keeps each number on its work, and only steps with no item get one.

# Per slice

Read [`references/slice-loop.md`](references/slice-loop.md) before the first slice. Outcome per slice, in plan order: its Decided line closed (`verified` with what works now and its evidence, or `not verified` with why), and its line printed:

```
S<k> · verified | not verified · <what works now | why>
```

- Steps are built one at a time, each merged into `feature/<name>` only after its step check passes, so each builds on checked work; every merge is pushed for resume.
- After the slice's steps merge: quality review ⇄ fix, then slice prove ⇄ fix. Quality fixes come first: they change code the prove must see, and a prove is the costly judge.
- A failure is fixed by the builder in fix mode. A failure one more fix cannot settle goes to a debate ([`references/escalation.md`](references/escalation.md)). Rounds go on while they progress; a loop changes the question or stops for a person ([`references/escalation.md`](references/escalation.md), Progress or loop).

# Closing

Once every slice is verified (or `· human check`) or has `gap accepted by D<k>`, read [`references/closing.md`](references/closing.md) before the final prove; a slice known to fail goes back to its fix loop first (4 of 8 finals started on one and ended Not verified on it). Then: final prove ⇄ fix, found-by-prove issues, the PR through the host adapter with its media attached, cleanup, the final line.

# The judges

The step check (a script), the quality review and the prove judge the work; the builder never judges its own. Each judge that is an agent is a fresh one that did not write the code and has not seen this chat, since an agent that shares the builder's reasoning agrees with it. For the same reason only the judge clears its own finding: your reading of the code settles nothing. A judge passes only when the work changes: tests, the spec and every Done when stay as they were, since changing one to pass hides the failure it was there to find.

# Dispatch

A stage that runs as an agent runs as a fresh one, never a fork, which inherits this conversation's reasoning. It has not seen this chat and runs no tracker or host command: paste verbatim every state section, step item and spec excerpt it needs, read just before; a section that needs changing changes on the state first.

The prompt opens by having the agent load its stage's skill, so it works under that skill's rules:

```
Call the Skill tool with `<m-requirements | m-scan | m-build | m-prove>`. Then do the work below.
```

A dispatch is done when its reply is the return the stage's skill defines, which only a run under that skill produces: requirements, the block `check.py` judges; scan, one `Q<n>` line per question it owns; build, a notes path or a `Stop ·` line; prove, its Return block. Any other reply, or one missing part of its return (a scan question it owns), was not made under the skill: dispatch again. A second such reply means a resend will not fix it: inside a slice it is that slice failing (Progress or loop, then a debate); in Understand, what is missing goes under Assumed and the PR's What to watch, and the run goes on.

Models are tiers, cheap, standard and strong: the harness's quickest, middle and most capable. A tier that does not resolve runs on the session's.

| Stage | Runs in | subagent_type | Model |
|---|---|---|---|
| requirements | fresh agent loading `m-requirements` | `general-purpose` | standard; `check.py` checks its block |
| scan A (Q1) | fresh agent loading `m-scan` | `Explore` | cheap |
| scan B (Q2–5), C (Q6, Q9), D (Q7–8) | fresh agent loading `m-scan` | `Explore` | standard |
| docs | this chat, `m-research` loaded; it dispatches its own agents | — | its own (standard) |
| debate | `m-debate` through the Skill tool, the block as its argument; it runs in its own context and dispatches its own 5 agents, so only its reply lines reach this chat | — | its own (3 strong, 2 standard) |
| plan, re-cut | `m-plan` through the Skill tool, the paths of its inputs as its argument; it runs in its own context and writes the plan and step bodies to files, so only its reply lines reach this chat | — | the session's (the fork inherits it) |
| build, fix mode included | fresh agent loading `m-build`, one at a time | `general-purpose` | standard; strong when How hard to undo is hard |
| step check | this chat, `step_check.py` | — | none |
| quality review, re-review | this chat, `m-review` loaded; it dispatches its own fresh reviewer | — | standard; strong when How hard to undo is hard |
| prove, slice and final | fresh agent loading `m-prove` (the supervisor) | `general-purpose` | strong; it dispatches its own drivers (Q1 standard, Q2 strong) |

Inputs each stage needs:

| Stage | Inputs |
|---|---|
| requirements | the frozen copy's path · the spec's ref · the checkout path (read-only) |
| scan | the spec title and frozen copy's path · the question group it owns |
| build | the step item's ref and body verbatim, or the path of its step file, which reaches the builder as written · Not doing and How to build verbatim · scan Q2–Q9 · docs answers or "not applicable" · the step branch it is on (checked out) and its feature branch |
| build, fix mode | the same, with the fix step item, whose body lists what to fix: step check output, quality findings (`F<n>` lines with their kind, `file:line` and evidence), or prove failures (the requirement or slice Done when, the value seen, an evidence excerpt; for a comparison, every differing cell), never prove's replays · a debate decision, when one led here |
| debate | the block in [`references/escalation.md`](references/escalation.md) (Running a debate) |
| quality review | the diff range `<slice start sha>..<slice end sha>` · the slice's `Slice S<k> · Done when e2e …` line verbatim · the Requirements lines it serves, verbatim, and the Assumed lines that name those ids · How hard to undo · Not doing verbatim · the repo's rule files that exist (`CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `.claude/rules/`, `.cursor/rules/`, style guides the repo names) · scan Q1, Q4, Q5 · the docs answers with their quotes and links |
| re-review | only the findings to recheck and the fix range |
| prove, slice | `mode: slice` · the feature branch · the slice id and its `Slice S<k> · Done when e2e …` line verbatim · the Requirements lines it serves, verbatim · diff range `<slice start sha>..HEAD` · scan Q9, and Q6's `env` (its regression hunt runs tests) · Not doing · each `MSTACK_SECRET_<NAME>` set in the environment, by name, with what it unlocks |
| prove, final | `mode: final` · the feature branch · every Requirements line verbatim but those `retired by D<k>` · every `Slice S<k>` line · base: the bare base branch name (m-prove adds `origin/`), after `git fetch` · scan Q9, and Q6's `env` · Not doing, Assumed · credential variable names · the PR body with the Proved section's placeholders ([`references/closing.md`](references/closing.md)) · after a fix round, `previous final:` the previous final's Return block |
