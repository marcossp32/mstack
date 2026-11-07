---
name: m-debate
description: "Settles one hard engineering decision with nobody to ask: five fresh agents research it, the decision best backed by checked sources wins, and dissent is recorded. Use when asked to settle a hard-to-undo choice, or a failure one more fix will not settle, with no human to ask."
argument-hint: "debate block · Id, Problem, Spec, Facts, Requirements, Decisions, Repo, Runs, Out"
context: fork
agent: general-purpose
background: false
---

Settle the question in the block below with no human. The record goes to a file the caller stores without reading; your reply is the few lines it acts on.

The block:

$ARGUMENTS

```
Id           · D<k>
Problem      · <what must hold, under which conditions; how would you do it?>
Spec         · <reference> · "<verbatim excerpt>"
Facts        · <one per line, each with its evidence and where/when it was seen (commit, time): versions · limits · Not doing · what was tried and how it failed>
Requirements · <every R line in the area the decision touches, with its status now: proved · failing · not proved yet>
Decisions    · <earlier D lines on the same requirements, files or mechanism>      optional
Repo         · <absolute path of the checkout the debaters read>
Runs         · <where the system runs and how to reach it, what in it is shared>   optional
Out          · <path to write the record to>           optional: else debate-D<k>.md in the current directory
```

No `Id`: use `D?` and say so in the record, since the caller numbers debates; with no `Out` either, the file is `debate-unnumbered.md`, since `?` is no valid file name on every system.

# Done when

The record is written to `Out` in the shape of [references/record.md](references/record.md), its checks hold, and your reply is exactly the lines under Reply. The debate changes nothing it found: no tracker item, comment, file or git state of the checkout, no data or state of a running system, and nothing it started still runs.

A debate costs minutes; a wrong one costs a prove round, a follow-up debate, sometimes a requirement shipped unverified.

# How a debate works

**Current, not remembered.** What the debate relies on must be true now: the caller's Facts, the installed versions, the repo as it is, the running system. Facts are the caller's last observation, and the code may have moved since. Before dispatch, note what identifies the state you read (the checkout's commit; where none can be read, say so and give the time) and re-check each Fact that describes the present (a version, a limit, what a file says, how the system behaves) the cheapest safe way. One that no longer holds goes to the debaters corrected and marked stale, with what is true now; a Fact quoting docs no longer holds where the code or the system shows otherwise. A Fact about an attempt that failed is history: keep it, with when it was seen. Docs count for the version installed now, read from the repo, not from memory or the latest release.

**Observe, don't disturb.** A fact the running system or the code can show is settled by looking: docs say what should happen, an observation says what does, and the requirement will be proved against what does. Others may be building or proving on the same machine and system at the same time, so the debate reads the code, queries the running system read-only, and tries things on a scratch copy outside the checkout: the checkout ends as found, shared data and services are only read, nothing is installed where others run, and every process an agent starts ends before it replies. What could be seen only by changing shared state is not observed: the record says what and why.

**A neutral question.** Debaters see only what you dispatch, so a hint in the question comes back as their answer. `Dispatched` is an open how/what question that keeps what must hold, in the spec's words where it has them, with no candidate option, preference or leading word, no yes/no or either-or. What is installed, an attempt that failed (with its evidence) and earlier decisions are facts and go in `Facts`; an opinion posing as a fact is dropped.

**Five independent debaters.** Dispatch five fresh `general-purpose` agents in one message, so they run in parallel, and in the foreground, so you hold until every verdict is in: a debater left in the background is lost when you reply. Not forks: three on `strong`, two on `standard` (strong is the harness's most capable model, standard its middle one; a tier that does not resolve runs on the session's model). Each gets the "Round 1" prompt of [references/debater.md](references/debater.md), filled from the block; none sees labels, tiers or the others. Later rounds are dispatched the same way.

**Usable verdicts.** A verdict weighs only through sources a reader can check: a quoted page, a `file:line`, the spec, or an observation (what was run and where, its output verbatim, and when). A verdict missing a field or a checkable source gets one more ask; still without, it stays in the record as `unsourced` and weighs nothing.

**Round 2 only without consensus.** Consensus: an implementer handed any of the sourced verdicts that no rule below puts out would build the same thing (mechanism, where data lives, interface, failure behaviour); wording does not split them. Without it, each debater gets the others' verdicts anonymised, in no order ("Round 2" in debater.md), continuing its own conversation where the harness allows, else as a fresh agent given its Round 1 prompt and verdict first. Then choose by the rules below, whether or not round 2 agrees.

**Decided by checked sources, not votes.** How many agree is evidence neither way. Check yourself the sources the choice rests on: the quote is on the raw page (say when it came through a summarising fetch), the `file:line` says it now, the excerpt is in the spec, the observation gives the same result when you repeat it the same safe way. Check enough of the losing positions' sources to know they lost on evidence. A source that fails is dropped; one you cannot reach (the network, the system down) is `not checked`, not failed. Then:

- A position that breaks a `Fact` (repeats a failed attempt without answering why it failed, exceeds a limit, needs a version not installed), the spec excerpt, or a requirement given as proved is out, unless the problem is a spec contradiction and it says which reading it keeps.
- A rejection several debaters share stands against a position unless its checked sources answer it.
- On what the system does now, an observation outweighs docs and reasoning. Otherwise primary sources for the installed version (official docs, the repo's code, the spec) and sources about this problem outweigh general advice. A tie goes to the more reversible decision.
- With no checked source anywhere, the most reversible proposal wins (writes no persisted data, changes no public interface, least work to undo), said so in `Basis`.

The decision is always one a debater proposed: the caller cannot go on without one, and a decision nobody researched has no sources.

**Buildable and consistent.** Write the decision in its proposers' words, concrete enough to build. When it adds behaviour observable from outside the code that no listed requirement covers, add one `Adds` line worded as a requirement (what someone outside the code observes, no `"` inside; a bound naming the inputs it covers when the words hold every, any, never or all, else `bound —`). When it makes an existing derived requirement necessary, add `Requires`. The decision, its `Adds` and the requirements must agree: a decision that accepts what its own `Adds` forbids sends a prove round to find it.

**Reviewed before it returns.** Dispatch one fresh `general-purpose` agent on `strong` with the "Review" prompt of debater.md, in the foreground, on the chosen decision with its `Adds` and `Requires`. A break it reports that you confirm is a new Fact: choose again among the positions that answer it, or, when none does, give it to the debaters as a Fact for another round; review whatever is chosen. When a round brings no position or source that answers a confirmed break, or its answer only moves the break to another requirement or back to one an earlier pass raised, more rounds will not: choose the position that breaks the fewest requirements given as proved, then by the rules above, and the record's Review says what stays broken and why. An earlier decision undone on purpose is not a failure, but the caller must know (`Undoes`), since what was proved under it is no longer proved.

**A repeated decision is a finding.** When `Facts` show an earlier attempt and the chosen decision is that attempt again in other words, say so in `Repeats`: the caller needs to know the debate found nothing new.

Before replying, confirm the checkout is as you noted it and nothing the debate started still runs.

# Reply

The caller parses exactly these lines, nothing else: a caveat, a correction or anything not run goes in the record (or a Stale line), never another line.

```
D<k> · <Dispatched question> → <chosen decision, one sentence>
Record · <path written>
Basis · sourced | most reversible · no verified source
Repeats · no | <the earlier attempt in Facts it repeats>
Undoes · no | D<j> · <what of it is undone> · R<n> … <the requirements that lose their proof>
Stale · <the Fact, in a few words> · now <what is true, in a few words>    one per stale Fact, only when there is one; the record holds the detail
Requires · R<n>                                     only when there is one
Adds · "<requirement words>" · bound <domain | —>   only when there is one
```

Illustrative:

```
D3 · How must order exports keep running when the carrier API is down for minutes at a time? → Queue each export in the existing jobs table and retry with the backoff the carrier documents, marking it failed after 24 h.
Record · /repo/.git/mstack/debates/D3.md
Basis · sourced
Repeats · no
Undoes · no
Stale · exports run synchronously in the request · now queued by the jobs runner since a1b2c3d
```
