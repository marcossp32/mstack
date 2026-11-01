---
name: m-debate
description: "Settles one hard engineering decision with nobody to ask: five fresh agents research it, the decision best backed by checked sources wins, and the full record goes to a file. Use when asked to settle a hard-to-undo choice, or a failure one more fix will not settle, with no human to ask."
argument-hint: "<debate block: Id, Problem, Spec, Facts, Requirements, Repo, Out>"
context: fork
agent: general-purpose
background: false
---

Settle the question in the block below with no human. Five fresh agents research it from the docs, the internet and the repo; the decision best backed by sources you checked in this run wins. The full record goes to a file, because it is long and the caller keeps it, not reads it. Your reply is a few lines the caller acts on.

The block:

$ARGUMENTS

```
Id           · D<k>
Problem      · <what must hold, under which conditions; how would you do it?>
Spec         · <reference> · "<verbatim excerpt>"
Facts        · <one per line: versions · limits · Not doing · what was tried and how it failed, with evidence>
Requirements · <the R lines the decision touches>      optional
Repo         · <absolute path of the checkout the debaters read>
Out          · <path to write the record to>           optional: else debate-D<k>.md in the current directory
```

No `Id`: use `D?` and say so in the record, since the caller numbers debates.

# Done when

The record is written to `Out` in the shape of [references/record.md](references/record.md), its chosen decision rests only on sources checked in this run, and your reply is exactly the lines under Reply. Nothing else changed: no tracker item, comment, repo file or git state, and no app, test or project code ran.

# How a debate works

Everything reads; nothing runs. No debater and no check of yours starts the app, runs tests or project code, installs anything or touches git: others build and prove what is chosen, and anything run here could disturb their work.

**A neutral question.** Debaters see only what you dispatch, so a hint in the question comes back as their answer. `Dispatched` is an open how/what question that keeps what must hold, in the spec's words where it has them, with no candidate option, no preference or leading word, no yes/no or either-or. Something installed or fixed is a fact; a failed attempt is a fact with its evidence; both go in `Facts`. An opinion posing as a fact is dropped.

**Five independent debaters.** Dispatch five fresh `general-purpose` agents in one message, so they run in parallel, and in the foreground, so you hold until every verdict is in: a debater left in the background is lost when you reply. Not forks: three on `strong`, two on `standard` (a tier that does not resolve runs on the session's model). Each gets the "Round 1" prompt of [references/debater.md](references/debater.md), filled from the block; none sees labels, tiers or the others. Round 2 is dispatched the same way.

**Usable verdicts.** A verdict weighs only through sources a reader can check: a quoted page, a `file:line`, or the spec. A claim backed by running code is not one. A verdict missing a field or a checkable source gets one more ask; still without, it stays in the record as `unsourced` and weighs nothing.

**Round 2 only without consensus.** Consensus: an implementer handed any of the sourced verdicts would build the same thing (mechanism, where data lives, interface, failure behaviour); wording does not split them. Without it, each debater gets the others' verdicts anonymised, in no order ("Round 2" in debater.md), continuing its own conversation where the harness allows. It changes only for a reason a source supports. There is no round 3.

**Decided by checked sources, not votes.** How many agree is evidence neither way. Check yourself, read-only, the sources the choice rests on: the quote is on the raw page (say when it came through a summarising fetch), the `file:line` says what is claimed, the excerpt is in the spec. Check enough of the losing positions' sources to know they lost on evidence. A source that fails is dropped. Then:

- A position that breaks a `Fact` (repeats a failed attempt without answering why it failed, exceeds a limit, needs a version not installed) or the spec excerpt is out, unless the problem is a spec contradiction and it says which reading it keeps.
- A rejection several debaters share stands against a position unless its checked sources answer it.
- Primary sources for the installed version (official docs, the repo's code, the spec) and sources about this problem outweigh general advice. A tie goes to the more reversible decision.
- With no checked source anywhere, the most reversible proposal wins (writes no persisted data, changes no public interface, least work to undo), said so in `Basis`.

The decision is always one a debater proposed: the caller cannot go on without one, and a decision nobody researched has no sources.

**A repeated decision is a finding.** When `Facts` show an earlier attempt and the chosen decision is that attempt again in other words, say so in the reply's `Repeats` line: the caller needs to know the debate found nothing new.

**Buildable.** Write the decision in its proposers' words, concrete enough to build. When it adds behaviour observable from outside the code that no listed requirement covers, add one `Adds` line worded as a requirement (what someone outside the code observes, no `"` inside; a bound naming the inputs it covers when the words hold every, any, never or all, else `bound —`). When it makes an existing derived requirement necessary, add `Requires`.

# Reply

The caller parses this; nothing before or after it:

```
D<k> · <Dispatched question> → <chosen decision, one sentence>
Record · <path written>
Basis · sourced | most reversible · no verified source
Repeats · no | <the earlier attempt in Facts it repeats>
Requires · R<n>                                     only when there is one
Adds · "<requirement words>" · bound <domain | —>   only when there is one
```

Example:

```
D3 · How must order exports keep running when the carrier API is down for minutes at a time? → Queue each export in the existing jobs table and retry with the backoff the carrier documents, marking it failed after 24 h.
Record · /repo/.git/mstack/debates/D3.md
Basis · sourced
Repeats · no
```
