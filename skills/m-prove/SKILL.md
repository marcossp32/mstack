---
name: m-prove
description: "Proves a change does what was asked by driving the running app: a supervisor writes a short contract, two fresh agents drive it at once (one proves the requirements, one hunts what else broke), and the supervisor judges their evidence. Use as the prove stage of /m-feature, or before merging or releasing a change nobody has watched working."
---

Supervise a proof that the change holds in the running app: contract, two drives, judgement. Everything you write follows [`references/writing.md`](references/writing.md); a verdict line's reference is what was driven and its route.

Models come from [`references/routing.md`](references/routing.md): tiers, never names. `/m-feature` hands you its Routing line; without one, resolve the drivers' tiers yourself and put them in the header you return.

This conversation wrote or watched the code: dispatch a fresh `general-purpose` agent on the strong tier, whose prompt opens `Invoke the Skill tool with m-prove.` with the inputs below, and relay its verdict.

# Inputs

- Requirements verbatim: the Goal, or what the human asked. Never take them from the diff. None: ask; as a subagent, return `Not driven · no requirements`.
- Settled up front: decisions the human confirmed. Each one with an observable effect (data state on failure, a default, a limit) is a requirement.
- Not doing.
- Undo verdict; none: hard.
- How the app runs: scan Q9; none: look where m-scan Q9 looks.
- Base branch; none: the default branch.
- Whether evidence is kept for a pull request. `/m-feature` asks for it.

# Contract

Read files and git; start nothing.

1. `git rev-parse HEAD HEAD^{tree}`; the base is `git merge-base <base branch> HEAD`. Create the evidence dir `$(git rev-parse --absolute-git-dir)/m-prove/<short sha>-<unix time>` with `q1/` and `q2/` inside; its name is the run id.
2. **Requirements, before reading the diff.** One line per clause, quoted:
   - surface: where its user reaches it (page, HTTP endpoint, CLI command, public API from a script);
   - settled when: the observation that shows it, read back by a route that skips the code that wrote it (the record on a fresh read, the file on disk, the message off the queue). What the surface returns to its caller counts when that is the effect asked for. No such route: what the app itself shows, and the line says `via the app itself`.

   Say what settles it, not how to drive it: no payloads, values or steps. A tolerance comes from the clause ("each wait doubles"), never a number the clause does not state. Not observable: say so; the line ends not driven. Unreachable locally: the nearest surface with the same behaviour, named beside the one asked for.
3. **Environment**: the shipped defaults plus what the recipe or `.env.example` sets. Any other variable is an override, listed with the lines that need it and why. A requirement that names development, local or default settings is driven with no override.
4. **Run**: a recipe in the repo (`.claude/skills/run-*/SKILL.md`, `.claude/skills/verify/SKILL.md`) or a `~/.claude/skills/*/SKILL.md` whose description names this repo; else scan Q9. Launch · health check (no server: the entry point run once) · prerequisites.
5. **Risk areas**, now from `git diff <base>...HEAD`: where else this change can reach. Check each kind: callers of what changed, data it shares, start and shutdown, integrations, configuration and defaults, platform. One line per area that applies, with its `file:line`. Leave out Not doing.

```
HEAD <sha> · tree <sha> · base <sha> · checkout <path> · evidence <dir>
Run  · <recipe path | none> · <launch> · <health check> · <prerequisites> · overrides <VAR=value → R2 | none>
R1 "<clause>" · surface <…> · settled when <observation> via <route>
Risk · <area> · <file:line>
```

# Drive

Dispatch both at once, each a fresh `general-purpose` agent, prompt `Read <this skill's directory>/references/drive.md and follow it as <Q1 | Q2>.`, then the contract:

- **Q1, does it do what was asked?** The cheap tier when a recipe exists; the strong tier when the launch is improvised. You judge its evidence, so a cheap drive that reports without evidence costs one send-back, not a wrong verdict.
- **Q2, what else broke?** The strong tier: inventing routes is its job.

No Agent tool: drive Q1, then Q2, yourself by that file; the header says `self-driven`.

# Judge

Read [`references/drive.md`](references/drive.md), then check both reports:

- HEAD and tree match the contract; checkout clean; teardown stopped everything and freed the port.
- Every R line has a result; every risk area is covered or not driven, with its routes.
- Each reported value appears in its evidence file, in the output of the command or script saved there. A value with nothing printed behind it is not evidence.
- Every variable set in the evidence is an override the contract lists for that line.
- Every host the app was pointed at is on this machine, and no break is about Not doing; a break that is gets dropped.
- Each deviation is one of: **product** (repeats on a fresh run with the control passing), **harness** (the control fails too), **driver error** (the evidence contradicts the report). Only product makes a line not verified.
- A Q2 break is `new` when the base, driven the same way, behaves differently; `pre-existing` when the base fails the same way; `base not run` when the base could not be driven.

A line failing a check goes back once to a fresh agent on the strong tier, with the contract, that line and the check it failed; passing lines keep their result. Failing again: not driven. An empty report: dispatch once more; twice, its open lines are not driven. You accept, send back or mark not driven; verified and not verified come only from a drive.

Evidence kept for a pull request, and nothing not verified: keep the evidence dir and, per requirement, pick what shows it best. A screenshot for anything visible, cropped to the element, viewport in its name, base and head side by side when it changed; otherwise the command and up to 15 lines of its output. Mask tokens, secrets and personal data first. In every other case, delete the evidence dir.

Return:

```
HEAD <sha> · tree <sha> · recipe <path | improvised> · Q1 <tier>/<effort> · Q2 <tier>/<effort> | self-driven
R1 "<requirement>" — <verdict> · <what was driven, where> (asked <surface>, if different) → <value> via <route>
B1 <what broke> — <new | pre-existing | base not run> · <what was driven> → head <value> · base <value> · <file:line>
Covered — <risk area> · <what was driven> | not driven · <two routes tried>
Not driven — <line> · <precondition> · <routes tried>
Harness — <launch> · <health check> · <traps hit>                          improvised only
Evidence — R1 <file>#<alt text> · R2 <file>                                kept for a pull request only
```
