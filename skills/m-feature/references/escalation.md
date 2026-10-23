# Escalation

When a failure or a decision goes to a debate, how to run one, and what follows from its decision; also refused commands.

## When to debate

A normal failure (a FAIL, a quality finding, a not verified prove line) is fixed by the builder in fix mode, never debated. **Debate what one more fix cannot settle**: a decision that is hard to undo, a spec that contradicts itself, or a cut or approach that keeps failing. Each trigger below is a case of that; a case that fits it and is not listed is a trigger too.

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

## Bound rule

A requirement failing again on an input its earlier fix did not cover (another character, another page of what its words name) has no domain yet, and fixing input by input never ends. Give it one before another fix: the domain the standard or vendor documents, found by calling the Skill tool with `m-research`. It becomes the bound, with `was: <old bound>` beside it and a line under Assumed, when it covers the failed input and everything the words name; one that would narrow the requirement (from `bound —` included) goes to a debate, since the spec is frozen. Then one fix item for the whole new bound. A changed bound keeps the PR from Proved: a person accepts it, under Notes for reviewers. A requirement that fails past a documented bound goes to a debate, not to another bound.

## Running a debate

- **Cap.** At most 2 debates per slice (Debates lines with that `S<k>`, or `final` for the final prove). At the cap the slice is not verified (below). Understand and plan debates, and those on whether a derived requirement is required, have no cap.
- **Ground** a hard-to-undo decision in quotable facts first: where docs did not already answer it, call the Skill tool with `m-research` for it.
- **Ask neutrally.** Call the Skill tool with `m-debate`, in this chat (it dispatches its own five agents), with the next unused `D<k>` and this block:
  ```
  Id           · D<k>
  Problem      · <what must hold, under which conditions; how would you do it?>
  Spec         · <spec ref> · "<verbatim excerpt behind it>"
  Facts        · <installed versions · infrastructure limits · Not doing · what was tried, how it failed, with evidence: command + output lines, file:line, replay>
  Requirements · <the R lines it touches>
  Repo         · <absolute checkout path>
  ```
  The Problem states what must hold and asks how, since a framed question gets its frame back: no options, no preference, no yes/no ("X must process N items without blocking Y; how?", not "Should we use a queue?"). A failed attempt is a fact, not part of the problem. Done when it returns the `D<k> · <question> → <decision>` line and the `## D<k> · record` block.
- **Record.** That first line plus `· record: state comment · <understand | plan | S<k> | final>` under Debates; the `## D<k> · record` block as a state comment; `→ D<k>` beside the Open decisions or Contradictions entry it settles. Print `D<k> · <question> → <decision>`.
  - `Requires · R<n>` makes that line `derived · required by D<k>`; its words stay.
  - `Adds · "<words>" · bound <domain | —>` appends `R<n> · derived · required by D<k> · "<words>" · bound <…> · from "<the record's Spec excerpt>"` with the next unused id; the affected slice is then revised (or planned, before Plan).
- **A debate decides how, not what**: the spec is frozen, so a requirement keeps its words and reach and Not doing stays as the spec wrote it, whatever the decision.

## Acting on the decision

- Open decision or contradiction: an input to `m-plan`, now or at its next load.
- A contradiction whose debate overturns the reading m-requirements chose: mark each affected R line `retired by D<k>` (kept, not proved, listed in the PR) and add a new line with the next unused id, the decision's words, the retired line's level and `from` the same excerpt; ids are never reused or reworded. Revise the plan for those lines when one exists.
- A failing step, slice or final prove line, patching loop, build stop, approach or badly cut slice: call the Skill tool with `m-plan` to revise only that slice's unmerged work, given the record, the current plan, the failure with its evidence and the merged steps. Done when it returns the block plus `Revised · S<k> · <cause> · <what changed> · D<k>`: put that line under Debates beside D<k> and on the slice line, comment the block, create the new step items, close the replaced ones with `Replaced by D<k>`, rewrite `Slices ·`, and resume at the first unmerged step.
- A disputed or still-failing finding: the decision says whether it stands. Stands: a fix item carrying the decision. Does not: record it rejected on the slice line with D<k>.
- The environment cannot do it: the decision says what the slice does instead, within the requirement's words; when nothing can, the slice is not verified, naming D<k>.

## Not verified slice

A slice still failing at its cap: close its line `not verified · <why> · <D<a> D<b>> · open steps <refs>`, leave its merged steps on the feature branch, comment each open step item with why and leave it open, print the slice line, and go on. A later slice that depends on it still runs; its prove says what fails. The PR ships Not verified, naming the slice and why. The `final` scope works the same: after two debates, the lines still failing stay not verified and Closing goes on.

## Refused commands

A refused command goes under the PR's To merge, never retried in another form: the command, what it was for, and the `/setup-mstack` auto-mode entry that would allow it (`mstack step merges`, `mstack review scripts` or `mstack run recipes`). Permissions are setup-mstack's job, so this skill leaves them as it finds them. A refused step merge or push of `feature/<name>` makes every later slice impossible: close each remaining one `not verified · <command> refused` and go to Closing.
