---
name: m-feature
description: Takes one reviewed spec to a pull request proved in the running app, with nobody watching. Use only when asked to run /m-feature with a spec reference, which starts that spec's feature or resumes it.
disable-model-invocation: true
---

Turn one already-reviewed spec into a pull request a reviewer can merge, with nobody watching the run. The user starts it, or resumes it, with `/m-feature <spec ref>`; the argument may also be the feature's state item. This skill owns order, routing, the state and the few lines the chat shows; the stage skills it loads do the work. The reviewer gets a PR whose top shows whether each requirement holds in the running app, and every decision made without a human, with its sources.

# Done when

A pull request from `feature/<name>` into the base is open on the host, its verdict Proved or Not verified from a final prove of the tree it shows, every slice of the plan closed under the state's Decided (verified with its evidence, or not verified with why), every debate listed in the PR, every `found-by-prove` and `mstack:contradiction` issue linked from it, and the final line printed. Or the run printed the single setup stop line and created nothing.

# Acceptance criteria

- [ ] The host shows one open PR from `feature/<name>` into the base named under the state's Base; it is a draft (or carries the do-not-merge line) unless its verdict is Proved.
- [ ] The state item has the headings of [`references/state.md`](references/state.md) in order; every Requirements line has a `from`; Spec holds the frozen copy's hash.
- [ ] The `Slices ·` line lists every slice, and each has a closed Decided line: `verified` with its evidence, or `not verified` with why.
- [ ] No slice has more than 2 debates; every Debates line appears in the PR's Debates section.
- [ ] Every Contradictions entry names an open `mstack:contradiction` issue; every pre-existing break prove returned names a `found-by-prove` issue (opened or commented); each is linked from the PR and carries an `Origin · feature <name> · PR <link>` line.
- [ ] Every step item is closed, or listed in its slice's not verified line.
- [ ] No credential value appears in the state, any item, issue, commit message or the PR body; no PR media is a local path.
- [ ] Every refused command appears under To merge with the setup-mstack entry that would allow it.
- [ ] Every Assumed line appears under the PR's Decisions made without a human.
- [ ] The PR verdict comes from a final prove whose tree equals the PR head's tree, or the PR notes the markdown-only publish-issues commit after it.
- [ ] The step check baseline is cleared and the final evidence dir is deleted, or named in the final line.
- [ ] Every message addressed to the human is a slice line, a debate line, the final PR line or the setup stop line.

# Ground rules

- **Adapters.** Every tracker and host action is an adapter operation (`tracker read-spec`, `host open-pr`, …). Read `references/trackers/<tracker>.md` and `references/hosts/<host>.md` before the first operation: tool commands live only there, which is what lets a run use any tracker and host. Git runs directly; the remote is `origin`, and anything compared against a remote branch is compared after a fetch, since a stale local branch puts other work in the diff.
- **The state is the truth.** Read [`references/state.md`](references/state.md) before creating the state or resuming one: its headings, branches and resume points. It lives in the tracker and, with the pushed `feature/<name>`, is all a new session on another machine has. Write what a resume needs before relying on it; where the state and your memory disagree, the state wins.
- **Nothing waits.** Where a human would once have been asked, decide and record why (Assumed), take it to a debate, or deliver the PR Not verified. The setup stop, before anything exists, is the run's only stop.
- **Credentials** come only from environment variables `MSTACK_SECRET_<NAME>`. Stages get their names, never their values, and a value is written nowhere: the state, issues and PR are read by people who must not see it.
- **A refused command** is recorded for the PR's To merge, and the run goes on with what does not depend on it; it is never retried in another form, since that is the bypass the refusal exists to block ([`references/escalation.md`](references/escalation.md), Refused commands).
- **The spec is frozen** at Start: every stage reads the frozen copy, so a spec edited mid-run cannot move the target. A later change is noted in the PR.
- **Chat is minimal**: one line per slice closed, one per debate, the final PR line, each in the form given where it is printed. Nobody is reading progress; the state holds the detail.
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

The session may be new, so rebuild from the state and the remote. Re-run Start's config and checks and settle the base. Read the state with its comments; restore the frozen copy from its comment when it is missing on disk; compare the live spec's hash with Spec's and note `Spec changed · <date>` once if it moved, continuing on the frozen copy. Read the feature branch's first-parent log and any local `step/<name>-*` branches: steps push nothing, so unmerged work exists only on the machine that built it. Bring up prerequisites and the baseline unless resuming at Closing. Then continue at the first outcome below that the state does not yet show; inside a slice, at the point [`references/state.md`](references/state.md) (Resume points) names.

# How hard to undo

If this ships wrong, how hard is it to undo? You decide; stages only report evidence. Hard is a change others come to depend on or data gets stored in (a schema, a public API, a stored format, a core dependency, for instance); easy is one a later commit reverses whole (names, folders, internal structure). It sets depth and tiers: build and quality review run strong when hard. Settle it again after scan and after docs, since a vendor limit can change it; then it holds unless a debate changes it.

# Understand

Outcome: on the state, the requirements block, the scan's nine lines, the docs answers, every open decision debated (`→ D<k>`), every contradiction with its issue; prerequisites running and the step check baseline recorded.

- **Requirements and scan** start together, since neither needs the other: one fresh agent for requirements and the scan split by question group, each dispatched as [Dispatch](#dispatch) says.
- **The requirements block is accepted** only once `python3 <m-requirements dir>/scripts/check.py --spec <frozen copy> --out <block file>` has judged it. A failing block goes back with its FAIL lines while each resend fixes some; when one stops improving, accept it and list each FAIL line under Assumed and the PR's What to watch, since nothing waits. Its six state sections go into the body verbatim; Laziest build and Trace go in a comment. It never runs again on resume: its ids are what everything after cites.
- **Scan answers** go on the state as one comment; Where it runs comes from Q8. A scan agent missing one of its questions goes back for it, as [Dispatch](#dispatch) says.
- **Prerequisites and the baseline** need scan Q6 and Q9 and exist before the first step check, which compares against the baseline. Read [`references/slice-loop.md`](references/slice-loop.md) before starting them.
- **Docs.** Call the Skill tool with `m-research`, in this chat, once scan has returned the installed versions (Q1) and infrastructure (Q8) and requirements has returned the open decisions, since its questions need both. Ask: the hard limits of the service or library; the documented timeout, as a number; the vendor's security guidance (auth, secrets, what never to log); what changed in the installed version; and, for each hard-to-undo open decision, what the standard and vendor docs say and which alternatives they document, as quotable facts that ground its debate. A question with no subject is answered "not applicable". Done when its quoted answers are a state comment and their links are under Sources.
- **Debates before planning.** Each open decision `O<n>` (all hard to undo; easy ones are already under Assumed) and each hard-to-undo contradiction goes to a debate with scan's versions and limits among the Facts, since requirements ran without them; so does a derived requirement that is the only line covering a hard-to-undo behaviour (whether it is required). Read [`references/escalation.md`](references/escalation.md) before the first. None of these count toward a slice's cap.
- **Contradiction issues**: each contradiction gets one `mstack:contradiction` issue saying the reading built, its ref beside the entry; a ref already there is never opened twice. Read [`references/closing.md`](references/closing.md) (Issues) for its body before opening the first.

# Plan

Outcome: the plan block as a state comment, one step item per step with its blocking links, and the `Slices ·` line (item refs) at the top of Decided. No confirmation: the plan is saved and run.

- Call the Skill tool with `m-plan`, in this chat, giving it the state ref and, verbatim, Requirements (`retired by D<k>` markers included), Not doing, Considered, Contradictions, Assumed, Debates and How hard to undo; scan Q1–Q9; the docs answers; Where it runs. Done when it has returned the plan block and one `Step <n>` body per step.
- An `Open ·` line is debated, then `m-plan` is loaded again with the decision. A step marked `· waits D?` gets its item only after that decision, so nothing is built on a guess.
- Step items carry the `Step <n>` body verbatim (`tracker create-step`); `tracker link <blocked> <blocking>` for each Blocking pair. The plan's Assumed lines join the state's.

# Per slice

Read [`references/slice-loop.md`](references/slice-loop.md) before the first slice. Outcome per slice, in plan order: its Decided line closed (`verified` with what works now and its evidence, or `not verified` with why), and its line printed:

```
S<k> · verified | not verified · <what works now | why>
```

- Steps are built one at a time, and each merges into `feature/<name>` only after its step check passes, so every step builds on checked work and every merge is pushed for resume.
- After the slice's steps merge: quality review ⇄ fix, then slice prove ⇄ fix. Quality fixes come first because they change code the prove must see, and a prove is the expensive judge.
- A failure is fixed by the builder in fix mode. A failure one more fix cannot settle goes to a debate ([`references/escalation.md`](references/escalation.md)); after 2 debates on a slice it is not verified and the run moves on.

# Closing

When every slice is closed, read [`references/closing.md`](references/closing.md) before the final prove: final prove ⇄ fix, found-by-prove issues, the PR through the host adapter with its media attached, cleanup, the final line.

# The judges

The step check (a script), the quality review and the prove judge the work; the builder never judges its own. Each judge that is an agent is a fresh one that did not write the code and has not seen this chat, since an agent that shares the builder's reasoning agrees with it. For the same reason only the judge clears its own finding: your reading of the code settles nothing. A judge passes only when the work changes: tests, the spec and every Done when stay as they were, since changing one to pass hides the failure it was there to find.

# Dispatch

A stage that runs as an agent runs as a fresh one, never a fork, since a fork inherits this conversation's reasoning. It has not seen this chat and runs no tracker or host command, so paste verbatim every state section, step item and spec excerpt it needs, read just before; a section that needs changing changes on the state first.

The prompt opens by having the agent load its stage's skill, so it works under that skill's rules:

```
Call the Skill tool with `<m-requirements | m-scan | m-build | m-prove>`. Then do the work below.
```

A dispatch is done when its reply is the return the stage's skill defines, which only a run under that skill produces: requirements, the block `check.py` judges; scan, one `Q<n>` line per question it owns; build, a notes path or a `Stop ·` line; prove, its Return block. Any other reply, or one missing part of its return (a scan question it owns), was not made under the skill: dispatch again. A second such reply means a resend will not fix it, since nothing waits: inside a slice it is that slice failing (a debate, counted toward its cap); in Understand, what is missing goes under Assumed and the PR's What to watch, and the run goes on.

Models are tiers, cheap, standard and strong: the harness's quickest, middle and most capable. A tier that does not resolve runs on the session's model.

| Stage | Runs in | subagent_type | Model |
|---|---|---|---|
| requirements | fresh agent loading `m-requirements` | `general-purpose` | standard; `check.py` checks its block |
| scan A (Q1) | fresh agent loading `m-scan` | `Explore` | cheap |
| scan B (Q2–5), C (Q6, Q9), D (Q7–8) | fresh agent loading `m-scan` | `Explore` | standard |
| docs | this chat, `m-research` loaded; it dispatches its own agents | — | its own (standard) |
| debate | this chat, `m-debate` loaded; it dispatches its own 5 agents | — | its own (3 strong, 2 standard) |
| plan | this chat, `m-plan` loaded | — | session |
| build, fix mode included | fresh agent loading `m-build`, one at a time | `general-purpose` | standard; strong when How hard to undo is hard |
| step check | this chat, `step_check.py` | — | none |
| quality review, re-review | this chat, `m-review` loaded; it dispatches its own fresh reviewer | — | standard; strong when How hard to undo is hard |
| prove, slice and final | fresh agent loading `m-prove` (the supervisor) | `general-purpose` | strong; it dispatches its own drivers (Q1 standard, Q2 strong) |

Inputs each stage needs:

| Stage | Inputs |
|---|---|
| requirements | the frozen copy's path · the spec's ref · the checkout path (read-only) |
| scan | the spec title and frozen copy's path · the question group it owns |
| build | the step item's ref and body verbatim · Not doing verbatim · scan Q2–Q9 · docs answers or "not applicable" · the step branch it is on (checked out) and its feature branch |
| build, fix mode | the same, with the fix step item, whose body lists what to fix: step check output, quality findings (`F<n>` lines with source and `file:line`), or prove failures (the requirement or slice Done when, the value seen, an evidence excerpt) · a debate decision, when one led here |
| debate | the block in [`references/escalation.md`](references/escalation.md) (Running a debate) |
| quality review | the diff range `<slice start sha>..<slice end sha>` · How hard to undo · Not doing verbatim · the repo's rule files that exist (`CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `.claude/rules/`, `.cursor/rules/`, style guides the repo names) · scan Q1, Q4, Q5 · the docs answers with their quotes and links |
| re-review | only the findings to recheck and the fix range |
| prove, slice | `mode: slice` · the feature branch · the slice id and its `Slice S<k> · Done when e2e …` line verbatim · the Requirements lines it serves, verbatim · diff range `<slice start sha>..HEAD` · scan Q9 · Not doing · each `MSTACK_SECRET_<NAME>` set in the environment, by name, with what it unlocks |
| prove, final | `mode: final` · the feature branch · every Requirements line verbatim but those `retired by D<k>` · every `Slice S<k>` line · base: the bare base branch name (m-prove adds `origin/`), after `git fetch` · scan Q9 · Not doing, Assumed · credential variable names · the PR body with the Proved section's placeholders ([`references/closing.md`](references/closing.md)) |
