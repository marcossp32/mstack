---
name: m-debate
description: "Settles one hard engineering decision with nobody to ask: five fresh agents research it against the code and system as they are now, the decision best backed by checked sources wins, a fresh reviewer tests it against the current code before it returns, and the full record goes to a file. Use when asked to settle a hard-to-undo choice, or a failure one more fix will not settle, with no human to ask."
argument-hint: "<debate block: Id, Problem, Spec, Facts, Requirements, Decisions, Repo, Runs, Out>"
context: fork
agent: general-purpose
background: false
---

Settle the question in the block below with no human. Five fresh agents research it from the repo, the running system, the docs and the internet; the decision best backed by sources you checked in this run wins, and a fresh reviewer tests it against the code as it is now before you reply. The full record goes to a file the caller keeps, not reads; your reply is a few lines it acts on.

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

No `Id`: use `D?` and say so in the record, since the caller numbers debates.

# Done when

The record is written to `Out` in the shape of [references/record.md](references/record.md); its chosen decision rests only on sources checked in this run against the current state, the reviewer found nothing it breaks, and your reply is exactly the lines under Reply. Nothing else changed: no tracker item, comment, file or git state of the checkout, no data or state of a running system, and nothing the debate started still runs.

# Why this skill is shaped this way

Debates are cheap (minutes, a small share of a run); a wrong one is not: it costs a prove round (hours, real money), a follow-up debate, sometimes a requirement shipped unverified. Wrong debates have come from three places: a question the running system could have answered was decided from docs or reasoning; a fact handed in was no longer true, or the requirements handed in left out one the decision then broke; and a decision quietly undid an earlier one, or contradicted its own `Adds`. Everything below aims at those.

# How a debate works

**Current, not remembered.** What the debate relies on must be true now: the caller's Facts, the installed versions, the repo at its current commit, the running system. Facts are the caller's last observation, and the code may have moved since. Before dispatch, note the checkout's commit and re-check each Fact that describes the present (a version, a limit, what a file says, how the system behaves) the cheapest safe way; one that no longer holds goes to the debaters corrected and marked stale, with what is true now. A Fact about an attempt that failed is history: keep it, with the commit it was seen at. Docs count for the version installed now, read from the repo, not from memory or the latest release.

**Observe, don't disturb.** A fact the running system or the code can show is settled by looking, not by docs or reasoning: docs say what should happen, an observation says what does, and the requirement will be proved against what does. So debaters and you may observe: read the code, query the running system read-only, try something on a scratch copy kept outside the checkout. Others may be building or proving on the same machine and the same system at the same time, so nothing a debate does may change what they see: the checkout ends as found (files and git state), shared data and services are only read, nothing is installed where others run, and every process started ends before its agent replies, since a debater's work outlives its reply otherwise. When the only way to see something would change shared state, it is not observed: say what was not observed and why.

**A neutral question.** Debaters see only what you dispatch, so a hint in the question comes back as their answer. `Dispatched` is an open how/what question that keeps what must hold, in the spec's words where it has them, with no candidate option, no preference or leading word, no yes/no or either-or. Something installed or fixed is a fact; a failed attempt is a fact with its evidence; earlier decisions are facts too; all go in `Facts`. An opinion posing as a fact is dropped.

**Five independent debaters.** Dispatch five fresh `general-purpose` agents in one message, so they run in parallel, and in the foreground, so you hold until every verdict is in: a debater left in the background is lost when you reply. Not forks: three on `strong`, two on `standard` (a tier that does not resolve runs on the session's model). Each gets the "Round 1" prompt of [references/debater.md](references/debater.md), filled from the block; none sees labels, tiers or the others. Later rounds are dispatched the same way.

**Usable verdicts.** A verdict weighs only through sources a reader can check: a quoted page, a `file:line`, the spec, or an observation (what was run and where, with its output verbatim and the commit or time). A verdict missing a field or a checkable source gets one more ask; still without, it stays in the record as `unsourced` and weighs nothing.

**Round 2 only without consensus.** Consensus: an implementer handed any of the sourced verdicts would build the same thing (mechanism, where data lives, interface, failure behaviour); wording does not split them. Without it, each debater gets the others' verdicts anonymised, in no order ("Round 2" in debater.md), continuing its own conversation where the harness allows. It changes only for a reason a source supports.

**Decided by checked sources, not votes.** How many agree is evidence neither way. Check yourself the sources the choice rests on: the quote is on the raw page (say when it came through a summarising fetch), the `file:line` says it at the current commit, the excerpt is in the spec, the observation gives the same result when you repeat it the same safe way. Check enough of the losing positions' sources to know they lost on evidence. A source that fails is dropped. Then:

- A position that breaks a `Fact` (repeats a failed attempt without answering why it failed, exceeds a limit, needs a version not installed), the spec excerpt, or a requirement given as proved is out, unless the problem is a spec contradiction and it says which reading it keeps.
- A rejection several debaters share stands against a position unless its checked sources answer it.
- On what the system does now, an observation outweighs docs and reasoning. Otherwise primary sources for the installed version (official docs, the repo's code, the spec) and sources about this problem outweigh general advice. A tie goes to the more reversible decision.
- With no checked source anywhere, the most reversible proposal wins (writes no persisted data, changes no public interface, least work to undo), said so in `Basis`.

The decision is always one a debater proposed: the caller cannot go on without one, and a decision nobody researched has no sources.

**Buildable and consistent.** Write the decision in its proposers' words, concrete enough to build. When it adds behaviour observable from outside the code that no listed requirement covers, add one `Adds` line worded as a requirement (what someone outside the code observes, no `"` inside; a bound naming the inputs it covers when the words hold every, any, never or all, else `bound —`). When it makes an existing derived requirement necessary, add `Requires`. The decision, its `Adds` and the requirements must agree with each other: a decision that accepts what its own `Adds` forbids sends a prove round to find it.

**Reviewed before it returns.** Debaters each test their own idea; nobody yet tested the chosen one, with its `Adds`, against everything it touches now. Dispatch one fresh `general-purpose` agent on `strong` with the "Review" prompt of debater.md, in the foreground. It tries to break the decision against the current code and running system: a requirement it would stop holding (above all one already proved), a Fact no longer true, an earlier decision it undoes, its own `Adds` or `Requires`, a part not concrete enough to build. It costs one agent a few minutes; what it catches otherwise costs a prove round and a debate. A finding you confirm is a new Fact: choose again among the positions that answer it, or, when none does, give it to the debaters as a Fact for another round; review whatever is chosen. An earlier decision undone on purpose is not a failure, but the caller must know (`Undoes`), since what was proved under it is no longer proved.

**A repeated decision is a finding.** When `Facts` show an earlier attempt and the chosen decision is that attempt again in other words, say so in `Repeats`: the caller needs to know the debate found nothing new.

Before replying, confirm the checkout is at the commit you noted, unchanged, and nothing the debate started still runs.

# Reply

The caller parses exactly these lines, nothing else: a caveat, correction or anything not run goes in the record (or a Stale line), never another line.

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

Example:

```
D3 · How must order exports keep running when the carrier API is down for minutes at a time? → Queue each export in the existing jobs table and retry with the backoff the carrier documents, marking it failed after 24 h.
Record · /repo/.git/mstack/debates/D3.md
Basis · sourced
Repeats · no
Undoes · no
Stale · exports run synchronously in the request · now queued by the jobs runner since a1b2c3d
```
