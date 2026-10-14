---
name: m-prove
description: "Proves a change does what was asked by driving the running app, and hunts what else broke, judged on saved evidence. Use as the prove stage of /m-feature, or before merging or releasing a change nobody has watched working."
---

Supervise a proof that the change holds in the running app: contract, two drives, judgement. A verdict line's reference is what was driven and its route.

This conversation wrote or watched the code: dispatch a fresh `general-purpose` agent whose prompt opens `Invoke the Skill tool with m-prove.` with the inputs below, and relay its verdict.

# Inputs

- Requirements verbatim: the Goal, or what the human asked. Never take them from the diff. Given a map issue, read them from its body, never from a summary in your prompt. None: ask; as a subagent, return `Not driven · no requirements`.
- Settled up front: decisions the human confirmed. Each one with an observable effect (data state on failure, a default, a limit) is a requirement.
- Assumed: decisions made without the human. Context, never requirements: no R line quotes one. Q2 may take the behaviour one describes as a risk area.
- A build step's Done when is not a requirement: it serves one that already is.
- Not doing.
- How the app runs: scan Q9; none: look where m-scan Q9 looks.
- Credentials the human gave for driving (a store password, a test account), if any. Pass them to the drivers; never write them to the contract, a verdict comment or the pull request.
- Base branch; none: the default branch.
- Whether evidence is kept for a pull request: yes when you are handed the final pull request below, otherwise only when asked.
- Re-prove: the last prove's verdict comment and its tree, when `/m-feature` proves again after a replan.
- The final pull request, from `/m-feature` at closing only: map issue number, feature branch, title, and its body with the Proved section as placeholders. Given it, you open that pull request (Final pull request, below), and evidence is kept for it on the terms Judge sets.

# Contract

Read files and git; start nothing.

1. `git rev-parse HEAD HEAD^{tree}`; the base is `git merge-base origin/<base branch> HEAD` after `git fetch origin` (a local branch may be missing or stale). Create the evidence dir `$(git rev-parse --path-format=absolute --git-common-dir)/mstack/prove/<short sha>-<unix time>` with `q1/` and `q2/` inside; its name is the run id. First `python3 <this skill's directory>/scripts/cleanup.py --stale`: it deletes the dirs of runs that stopped before their cleanup.
2. **Requirements, before reading the diff.** One line per clause, quoted:
   - surface: where its user reaches it (page, HTTP endpoint, CLI command, public API from a script);
   - settled when: the observation that shows it, read back by a route that skips the code that wrote it (the record on a fresh read, the file on disk, the message off the queue). What the surface returns to its caller counts when that is the effect asked for. No such route: what the app itself shows, and the line says `via the app itself`.

   Say what settles it, not how to drive it: no payloads, values or steps. A tolerance comes from the clause ("each wait doubles"), never a number the clause does not state. Not observable: say so; the line ends not driven. Unreachable locally: the nearest surface with the same behaviour, named beside the one asked for.
3. **Environment**: the shipped defaults plus what the recipe or `.env.example` sets. Any other variable is an override, listed with the lines that need it and why. A requirement that names development, local or default settings is driven with no override.
4. **Run**: a recipe in the repo (`.claude/skills/run-*/SKILL.md`, `.claude/skills/verify/SKILL.md`) or a `~/.claude/skills/*/SKILL.md` whose description names this repo; else scan Q9. Launch · health check (no server: the entry point run once) · prerequisites. **Shared state**: whether two servers from this checkout would share a database, data dir, queue or fixed port the recipe cannot move. Any: the drives run one after the other.
5. **Risk areas**, now from `git diff <base>...HEAD`: where else this change can reach. Check each kind: callers of what changed, data it shares, start and shutdown, integrations, configuration and defaults, platform. One line per area that applies, with its `file:line`. Leave out Not doing.
6. **Re-prove only**: read `git diff <last tree> HEAD` the same way. A line last verified that has a **replay** (`python3 <this skill's directory>/scripts/replay.py list --feature <branch>`) is replayed by Q1, reachable or not: a replay is a check an earlier driver saved, so running it costs seconds and catches what a fix broke. Without a replay, a requirement that diff cannot reach keeps its last verdict, verified or pre-existing, as `carried <last short sha>` and is not driven again. Lines last not verified or not driven are driven, and so is every risk area the new diff reaches. Nothing the diff touches stays carried.

```
HEAD <sha> · tree <sha> · base <sha> · checkout <path> · evidence <dir>
Run  · <recipe path | none> · <launch> · <health check> · <prerequisites> · overrides <VAR=value → R2 | none> · shared state <none → parallel | what → Q1 then Q2>
R1 "<clause>" · surface <…> · settled when <observation> via <route> | carried <sha> | replay
Risk · <area> · <file:line>
```

# Prepare

`python3 <this skill's directory>/scripts/contain.py sweep --kill` first, into `<evidence>/prepare.txt`: it ends automation browsers an earlier run left orphaned, which would slow both drives and skew their timings. Run the recipe's dependency install and build once in the checkout, contained (`contain.py --shell "<command>"`, see [`references/drive.md`](references/drive.md)), output to the same file. A line or risk area reached through a page also needs a browser, outside the checkout: `agent-browser --version`, missing: `npm i -g agent-browser`; then `agent-browser install` for its Chrome, both into the same file. Then `git status --porcelain` must be empty; not empty: every line is not driven, naming the files. Drivers install and build nothing in the checkout, so two drives never write the same files.

# Drive

Dispatch both at once (one after the other when the contract names shared state), each a fresh `general-purpose` agent, prompt `Read <this skill's directory>/references/drive.md and follow it as <Q1 | Q2>.`, then the contract:

- **Q1, does it do what was asked?** Model standard (the harness's middle tier; the session's model where tiers do not resolve): you judge its evidence, so a drive that reports without evidence costs one send-back, not a wrong verdict.
- **Q2, what else broke?** Model strong (its most capable): inventing routes is its job, and nothing checks the routes it missed.

Re-prove with shared state, so Q1 before Q2: Q1 returns not verified on a line verified before, and your check accepts it. That is a regression a replan will fix first, so Q2 is not dispatched; its risk areas are not driven, naming the regression, and the next prove drives them.

No Agent tool: drive Q1, then Q2, yourself by that file; the header says `self-driven`.

# Judge

Read [`references/drive.md`](references/drive.md), then check both reports:

- HEAD and tree match the contract; checkout clean; teardown stopped everything, closed its browser sessions and freed the port. Then `contain.py sweep --kill`: an orphaned browser it ends is a teardown the drive missed, named on the Harness line.
- No drive ran a visible browser or hid its automation from a page; a line that did is sent back.
- Every R line has a result; every risk area is covered or not driven, with its routes.
- Each reported value appears in its evidence file, in the output of the command or script saved there. A value with nothing printed behind it is not evidence, and neither is a page value only a screenshot shows.
- Every variable set in the evidence is an override the contract lists for that line.
- Every host the app was pointed at is on this machine, and no break is about Not doing; a break that is gets dropped.
- Each deviation is one of: **product** (repeats on a fresh run with the control passing), **harness** (the control fails too), **driver error** (the evidence contradicts the report). Only product makes a line not verified.
- An R line is `pre-existing` when the base, driven the same way, fails it the same way: the change did not cause it. It is not a not verified, unless the Goal asks to change that existing behaviour.
- A Q2 break is `new` when the base, driven the same way, behaves differently; `pre-existing` when the base fails the same way; `base not run` when the base could not be driven.

A not driven line whose precondition only the human can meet is `human check`: a real account's login, a login a command wanted that you were not given, a third-party admin setting, a bot check meant to stop automation, content not yet published. It names what to check by hand. A precondition you could meet locally (data, a flag, a server) is not one.

**Recipe.** The contract's Run was improvised and the harness held (health check and control passed): write it down as a recipe at `~/.claude/skills/run-<repo name>/SKILL.md`, never in the checkout (prove needs it clean), from the drivers' reports: launch, health check, prerequisites, shared state, the traps they hit, teardown. Its description names the repo, so the next prove finds it (Contract, step 4). One already there: add the new traps to it. Name it on the Harness line.

A line failing a check goes back once to a fresh agent with the contract, the credentials, that line and the check it failed; passing lines keep their result. Failing again: not driven. An empty report: dispatch once more; twice, its open lines are not driven. You accept, send back or mark not driven; verified and not verified come only from a drive.

Evidence kept for a pull request, and nothing not verified: keep the evidence dir and, per requirement, pick what shows it best. A screenshot for anything visible, cropped to the element, viewport in its name, base and head side by side when it changed; otherwise the command and up to 15 lines of its output. Mask tokens, secrets and personal data first. In every other case, delete the evidence dir (Cleanup, below).

# Final pull request

Only when `/m-feature` handed you one: read [`references/pull-request.md`](references/pull-request.md) after Judge and follow it. It settles the **Proved** or **Not verified** verdict and opens the pull request.

# Cleanup

Before the evidence dir goes, keep the replays of the lines you accepted as verified this run: `python3 <this skill's directory>/scripts/replay.py save --feature <branch> --from <evidence dir>/q1/replay --lines <those lines>`. They live outside the evidence dir, per feature branch, for the next re-prove. A final pull request opened as **Proved** ends the feature: `replay.py clear --feature <branch>` instead.

`python3 <this skill's directory>/scripts/cleanup.py <evidence dir>` (`python` where `python3` is absent): it deletes only inside `mstack/prove/`. Never `rm -rf`. Refused or failed: leave the dir, put it on the return's Left line, and do not try again.

Return:

```
HEAD <sha> · tree <sha> · recipe <path | improvised> | self-driven
R1 "<requirement>" — <verdict> · <what was driven, where> (asked <surface>, if different) → <value> via <route>
R2 "<requirement>" — <verified | pre-existing> · carried <sha> | verified · replay <sha>        re-prove only
B1 <what broke> — <new | pre-existing | base not run> · <what was driven> → head <value> · base <value> · <file:line>
Covered — <risk area> · <what was driven> | not driven · <two routes tried>
Not driven — <line> · <precondition> · <routes tried>
Human check — <line> · <what the human checks by hand>
Harness — <launch> · <health check> · <traps hit> · recipe written <path>  improvised only
Evidence — R1 <file>#<alt text> · R2 <file>                                kept for a pull request only
Left — <evidence dir cleanup could not delete>                            only then
PR #<n> · <Proved | Not verified> · <draft | ready | draft unavailable> · verdict <comment URL>   final pull request only
```
