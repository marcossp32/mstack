---
name: m-prove
description: "Proves a change does what was asked by driving the running app: a supervisor writes a short contract, two fresh agents drive it at once (one proves the requirements, one hunts what else broke), and the supervisor judges their evidence. Use as the prove stage of /m-feature, or before merging or releasing a change nobody has watched working."
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
- Base branch; none: the default branch.
- Whether evidence is kept for a pull request: yes when you are handed the final pull request below, otherwise only when asked.
- Re-prove: the last prove's verdict comment and its tree, when `/m-feature` proves again after a replan.
- The final pull request, from `/m-feature` at closing only: map issue number, feature branch, title, and its body with the Proved section as placeholders. Given it, you open that pull request (Final pull request, below), and evidence is kept for it on the terms Judge sets.

# Contract

Read files and git; start nothing.

1. `git rev-parse HEAD HEAD^{tree}`; the base is `git merge-base <base branch> HEAD`. Create the evidence dir `$(git rev-parse --path-format=absolute --git-common-dir)/mstack/prove/<short sha>-<unix time>` with `q1/` and `q2/` inside; its name is the run id.
2. **Requirements, before reading the diff.** One line per clause, quoted:
   - surface: where its user reaches it (page, HTTP endpoint, CLI command, public API from a script);
   - settled when: the observation that shows it, read back by a route that skips the code that wrote it (the record on a fresh read, the file on disk, the message off the queue). What the surface returns to its caller counts when that is the effect asked for. No such route: what the app itself shows, and the line says `via the app itself`.

   Say what settles it, not how to drive it: no payloads, values or steps. A tolerance comes from the clause ("each wait doubles"), never a number the clause does not state. Not observable: say so; the line ends not driven. Unreachable locally: the nearest surface with the same behaviour, named beside the one asked for.
3. **Environment**: the shipped defaults plus what the recipe or `.env.example` sets. Any other variable is an override, listed with the lines that need it and why. A requirement that names development, local or default settings is driven with no override.
4. **Run**: a recipe in the repo (`.claude/skills/run-*/SKILL.md`, `.claude/skills/verify/SKILL.md`) or a `~/.claude/skills/*/SKILL.md` whose description names this repo; else scan Q9. Launch · health check (no server: the entry point run once) · prerequisites. **Shared state**: whether two servers from this checkout would share a database, data dir, queue or fixed port the recipe cannot move. Any: the drives run one after the other.
5. **Risk areas**, now from `git diff <base>...HEAD`: where else this change can reach. Check each kind: callers of what changed, data it shares, start and shutdown, integrations, configuration and defaults, platform. One line per area that applies, with its `file:line`. Leave out Not doing.
6. **Re-prove only**: read `git diff <last tree> HEAD` the same way. A requirement that diff cannot reach keeps its last verdict, verified or pre-existing, as `carried <last short sha>` and is not driven again. Lines last not verified or not driven are driven, and so is every risk area the new diff reaches. Nothing the diff touches stays carried.

```
HEAD <sha> · tree <sha> · base <sha> · checkout <path> · evidence <dir>
Run  · <recipe path | none> · <launch> · <health check> · <prerequisites> · overrides <VAR=value → R2 | none> · shared state <none → parallel | what → Q1 then Q2>
R1 "<clause>" · surface <…> · settled when <observation> via <route> | carried <sha>
Risk · <area> · <file:line>
```

# Prepare

Run the recipe's dependency install and build once in the checkout, output to `<evidence>/prepare.txt`. A line or risk area reached through a page also needs a browser, outside the checkout: `agent-browser --version`, missing: `npm i -g agent-browser`; then `agent-browser install` for its Chrome, both into the same file. Then `git status --porcelain` must be empty; not empty: every line is not driven, naming the files. Drivers install and build nothing in the checkout, so two drives never write the same files.

# Drive

Dispatch both at once (one after the other when the contract names shared state), each a fresh `general-purpose` agent, prompt `Read <this skill's directory>/references/drive.md and follow it as <Q1 | Q2>.`, then the contract:

- **Q1, does it do what was asked?** You judge its evidence: a drive that reports without evidence costs one send-back, not a wrong verdict.
- **Q2, what else broke?** Inventing routes is its job.

No Agent tool: drive Q1, then Q2, yourself by that file; the header says `self-driven`.

# Judge

Read [`references/drive.md`](references/drive.md), then check both reports:

- HEAD and tree match the contract; checkout clean; teardown stopped everything, closed its browser sessions and freed the port.
- Every R line has a result; every risk area is covered or not driven, with its routes.
- Each reported value appears in its evidence file, in the output of the command or script saved there. A value with nothing printed behind it is not evidence, and neither is a page value only a screenshot shows.
- Every variable set in the evidence is an override the contract lists for that line.
- Every host the app was pointed at is on this machine, and no break is about Not doing; a break that is gets dropped.
- Each deviation is one of: **product** (repeats on a fresh run with the control passing), **harness** (the control fails too), **driver error** (the evidence contradicts the report). Only product makes a line not verified.
- An R line is `pre-existing` when the base, driven the same way, fails it the same way: the change did not cause it. It is not a not verified, unless the Goal asks to change that existing behaviour.
- A Q2 break is `new` when the base, driven the same way, behaves differently; `pre-existing` when the base fails the same way; `base not run` when the base could not be driven.

A line failing a check goes back once to a fresh agent with the contract, that line and the check it failed; passing lines keep their result. Failing again: not driven. An empty report: dispatch once more; twice, its open lines are not driven. You accept, send back or mark not driven; verified and not verified come only from a drive.

Evidence kept for a pull request, and nothing not verified: keep the evidence dir and, per requirement, pick what shows it best. A screenshot for anything visible, cropped to the element, viewport in its name, base and head side by side when it changed; otherwise the command and up to 15 lines of its output. Mask tokens, secrets and personal data first. In every other case, delete the evidence dir.

# Final pull request

Only when `/m-feature` handed you one. The verdict is **Proved** when every R line is verified or pre-existing, no line is not driven, and no B line is `new` or `base not run`; anything else is **Not verified**. A Not verified pull request is a draft, so nobody merges it by accident.

1. `git rev-parse HEAD^{tree}` still equals the contract's tree. Changed: open nothing, and return `PR · not opened · tree changed`.
2. Comment your verdict on the map, without the Evidence line: `gh issue comment <map> --body-file -`. It prints the comment's URL; that is the body's Prove verdict link.
3. Fill the body's Proved section: one table row per R line (requirement quoted, verdict, evidence), and one `<details>` block per output, holding the command and up to 15 lines of it. Then one line: `Also driven: <covered risk areas> · Not driven: <line · precondition, or none> · [Prove verdict](<comment URL>)`. Each verified line shows its evidence while the evidence dir is kept, so a PR Not verified only for a not driven or `base not run` line still carries it; a line not verified shows its verdict and value only. A carried line keeps its row, evidence included, from the pull request an earlier prove opened; its verdict cell adds `carried <sha>`. The body stays under 65,536 characters: trim outputs, never the verdict lines.
4. Look for one an earlier prove opened: `gh pr list --base main --head <feature branch> --state open --json number,isDraft --jq '.[0] // "none"'`. It prints `none` when there is none, else the PR's number and draft state.
   - Found: `gh pr edit <n> --body-file -`. The do-not-merge first line below is in the body only when the PR is Not verified and not a draft; step 5 settles which. `gh pr edit` has no `--attach` in 2.96.0: images become one line each, saying what it shows and at which viewport, unless the installed `gh pr edit --help` lists the flag.
   - None: `gh pr create --base main --head <feature branch> --title "<title>" --body-file -`, with `--draft` when Not verified. Attach each screenshot with `--attach "<path>#<alt text>"` where the installed `gh pr create --help` lists the flag; without it, one line per image as above.
   - `--draft` refused (drafts need a public repo or a GitHub Team or Enterprise plan): create it again without `--draft`, with `**Not verified: do not merge.** This repo cannot hold draft pull requests.` as the body's first line. The PR line says `draft unavailable`.
5. Proved and a draft: `gh pr ready <n>`. Not verified and ready: `gh pr ready <n> --undo`; refused, the PR line says `draft unavailable`, as on create. Then the do-not-merge line: Not verified and still not a draft, it is the body's first line; a draft or Proved, it is not in the body. Change the body with `gh pr edit <n> --body-file -` when it does not match.
6. Delete the evidence dir once the pull request holds what it needs.

Return:

```
HEAD <sha> · tree <sha> · recipe <path | improvised> | self-driven
R1 "<requirement>" — <verdict> · <what was driven, where> (asked <surface>, if different) → <value> via <route>
R2 "<requirement>" — <verified | pre-existing> · carried <sha>                                  re-prove only
B1 <what broke> — <new | pre-existing | base not run> · <what was driven> → head <value> · base <value> · <file:line>
Covered — <risk area> · <what was driven> | not driven · <two routes tried>
Not driven — <line> · <precondition> · <routes tried>
Harness — <launch> · <health check> · <traps hit>                          improvised only
Evidence — R1 <file>#<alt text> · R2 <file>                                kept for a pull request only
PR #<n> · <Proved | Not verified> · <draft | ready | draft unavailable> · verdict <comment URL>   final pull request only
```
