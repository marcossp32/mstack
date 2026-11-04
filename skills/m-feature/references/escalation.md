# Escalation

When a failure or a decision goes to a debate, how to run one and act on it, how to tell progress from a loop, and refused commands.

## When to debate

A normal failure (a FAIL, a quality finding, a not verified prove line) is fixed by the builder in fix mode. **Debate what one more fix cannot settle**: a decision that is hard to undo, a spec that contradicts itself, or a cut or approach that keeps failing. Each trigger below is a case of that; a case that fits it and is not listed is a trigger too. There is no limit on debates: each one costs minutes, a wrong patch costs a prove round.

- A hard-to-undo open decision (Understand, or an `Open ·` line from `m-plan`).
- A derived requirement that is the only line covering a hard-to-undo behaviour (data state on failure, a stored format, a public interface): whether it is required.
- A spec contradiction that is hard to undo.
- The same step fails its check twice.
- A quality finding still failing after two fix rounds, or disputed by the builder (`## Disputed`).
- A slice prove, or a final prove line, still failing after two fix rounds.
- A patching loop (below).
- A build stop: `Stop · <unobservable Done when | contradiction | missing decision> · <what>`.
- An approach that cannot meet a requirement; a badly cut slice; a spec that asks what the environment cannot do.

## Patching loop

Patches to one file that each satisfy the latest condition and break an earlier one never converge: what is missing is one design that holds all the conditions at once. So before a fix item, look at the non-test files the failure names: one already changed by two or more of this feature's merged fix steps (merge commits whose `Part of` names a fix item, e.g. from `git log --first-parent --name-only origin/feature/<name>`) goes to a debate instead of another fix, naming every condition the earlier findings and failures on that file set.

## Progress or loop

Before each fix item and each debate, put the new failure beside the earlier ones on the same requirement: the slice line, its fix items, the Debates lines.

- **Progress**: each round closed what it targeted, and what fails now is new or smaller (fewer items, other values, other files). Go on with the next fix or debate; there is no round limit while the work moves.
- **Loop**: the same requirement fails with the same value after a fix or decision aimed at it, a debate replies `Repeats`, or two decisions build the same mechanism in other words. Another round of the same fails the same way, so change the question: research whether the platform can do it and by which route (`m-research`), debate with every failed mechanism and its value as facts, or re-cut the slice on a route no attempt used. When nothing documented allows it, or it needs a person (a credential, an account, an approval), stop (below): building around it ships a requirement that does not hold.

## Stop for a person

The run stops in two places only: the setup stop at Start, and here, when a requirement cannot hold without a person. Stop before more work is built on it: write the reason on the state (`Stop · R<n> · <what is needed from a person> · <evidence: the docs quote, or the variable that is missing>`), print that line, and end. A resume after the person answers picks up from the state. Everything else is decided without asking: Assumed, a debate, or a fix.

## Bound rule

A requirement failing again on an input its earlier fix did not cover (another character, another page of what its words name) has no domain yet, and fixing input by input never ends. Give it one before another fix: the domain the standard or vendor documents, found by calling the Skill tool with `m-research`. It becomes the bound, with `was: <old bound>` beside it and a line under Assumed, when it covers the failed input and everything the words name; one that would narrow the requirement (from `bound —` included) goes to a debate, since the spec is frozen. Then one fix item for the whole new bound. A changed bound keeps the PR from Proved: a person accepts it, under Notes for reviewers. A requirement that fails past a documented bound goes to a debate, not to another bound.

## Running a debate

- **Ground** a hard-to-undo decision in quotable facts first: where docs did not already answer it, call the Skill tool with `m-research` for it.
- **Ask neutrally.** Call the Skill tool with `m-debate` and this block as its argument, with the next unused `D<k>`. It runs in its own context and dispatches its own five agents, so its research never enters this chat:
  ```
  Id           · D<k>
  Problem      · <what must hold, under which conditions; how would you do it?>
  Spec         · <spec ref> · "<verbatim excerpt behind it>"
  Facts        · <installed versions · infrastructure limits · Not doing · what was tried, how it failed, with evidence: command + output lines, file:line, replay; each with the commit or time it was seen>
  Requirements · <every R line on the slices and files the decision touches, with its status now: proved · failing · not proved yet>
  Decisions    · <the Debates lines on the same requirements, files or mechanism>
  Repo         · <absolute checkout path>
  Runs         · <Where it runs: how the running system is reached, what in it is shared>
  Out          · <git common dir>/mstack/debates/D<k>.md
  ```
  The Problem states what must hold and asks how, since a framed question gets its frame back: no options, no preference, no yes/no ("X must process N items without blocking Y; how?", not "Should we use a queue?"). A failed attempt is a fact, not part of the problem. Requirements include those already passing: a decision only sees the lines it is given, and one it was not given is one it may break. The debate re-checks Facts against the current state, but a fact without when it was seen cannot be told from a stale one. Done when it replies with the `D<k> · <question> → <decision>` line and `Record · <path>`.
- **Record.** That first line plus `· record: state comment · <understand | plan | S<k> | final>` under Debates; the record file as a state comment (`tracker comment <state> <body>`, the body fed from the file, e.g. `< <path>` where the adapter reads stdin), never read into this chat; `→ D<k>` beside the Open decisions or Contradictions entry it settles. Print `D<k> · <question> → <decision>`.
  - `Requires · R<n>` makes that line `derived · required by D<k>`; its words stay.
  - `Adds · "<words>" · bound <domain | —>` appends `R<n> · derived · required by D<k> · "<words>" · bound <…> · from "<the record's Spec excerpt>"` with the next unused id; the affected slice is then revised (or planned, before Plan).
  - `Repeats · <attempt>`: the debate found nothing new; treat it as a loop (Progress or loop).
  - `Undoes · D<j> · <what> · R<n> …`: those lines lose their proof (invalidate their replays, below); mark them on their slice lines and prove them again once the decision is built, with the slice it changes or in the next prove that covers them. Write `undone in part by D<k>` beside D<j> under Debates.
  - `Stale · <fact> · now <what>`: correct the fact where the state holds it, so no later stage or debate is handed it again.
- **A debate decides how, not what**: the spec is frozen, so a requirement keeps its words and reach and Not doing stays as the spec wrote it, whatever the decision.

## Acting on the decision

- Open decision or contradiction: an input to `m-plan`, now or at its next call.
- A contradiction whose debate overturns the reading m-requirements chose: mark each affected R line `retired by D<k>` (kept, not proved, listed in the PR) and add a new line with the next unused id, the decision's words, the retired line's level and `from` the same excerpt; ids are never reused or reworded. Revise the plan for those lines when one exists.
- A failing step, slice or final prove line, patching loop, build stop, approach or badly cut slice: call the Skill tool with `m-plan` to revise only that slice's unmerged work, as SKILL.md (Plan) calls it, with `Out` ending `/D<k>/`; its argument adds the decision line and the record's path, the previous `Out`, the failure with its evidence and the merged steps. Done when it replies with its file lines plus `Revised · S<k> · <cause> · <what changed> · D<k>`: put that line under Debates beside D<k> and on the slice line, comment the plan file, create an item from the step file of each step number without one (the `Changed · new` ones), close each `dropped` one with `Replaced by D<k>`, rewrite `Slices ·`, and resume at the first unmerged step.
- **Replays a decision makes stale.** A line the decision retires or undoes, or whose surface it moves (the same words, another page, command or endpoint), keeps a replay that can still pass against what no longer holds, found only at the next prove. At once: `python3 <m-prove dir>/scripts/replay.py invalidate --feature feature/<name> --lines <S<k>,R<n>…> --why "D<k> · <what changed>"`, so the next prove drives them; for retired lines add `--retired`, since no prove has them any more.
- A slice that cannot be made to pass, and a decision that it ships without it (the line is retired, re-cut elsewhere, or out of reach and recorded): close it `not verified · … · gap accepted by D<k>`. Only that lets the final start over a failing slice.
- A disputed or still-failing finding: the decision says whether it stands. Stands: a fix item carrying the decision. Does not: record it rejected on the slice line with D<k>.
- The environment cannot do it: Stop for a person.

## Refused commands

A refused command goes under the PR's To merge, never retried in another form: the command, what it was for, and the `/setup-mstack` auto-mode entry that would allow it (`mstack step merges`, `mstack review scripts` or `mstack run recipes`). Permissions are setup-mstack's job, so this skill leaves them as it finds them. A refused step merge or push of `feature/<name>` makes every later slice impossible: stop for a person, naming the command and the entry.
