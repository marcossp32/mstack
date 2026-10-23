---
name: m-debate
description: "Settles one hard engineering decision with nobody to ask: five fresh agents research it, the decision best backed by checked sources wins, and dissent is recorded. Use when asked to settle a hard-to-undo choice, or a failure one more fix will not settle, with no human to ask."
---

Settles one hard question with no human: five fresh agents research it from docs, the internet and the repo, and the decision best backed by sources checked in this run wins. Returns one `D<k>` line and the full record, for whoever called it to store and for a later reviewer to read what was decided and why. Nobody is there to answer, so it decides every time and returns its decision instead of writing it anywhere: the caller owns where decisions live.

# Done when

The reply is the `D<k> · <question> → <decision>` line followed by the `## D<k> · record` block in the shape under Output; the chosen decision rests only on sources checked in this run; and nothing outside the reply changed: no tracker item, comment, file, repo or git state, and no app, test or project code ran.

# Acceptance criteria

- [ ] `Dispatched` contains no option, no named candidate approach, no preference and no yes/no or either-or question; `Asked` holds the caller's wording verbatim.
- [ ] Round 1 lists exactly 5 verdicts: 3 from `strong`, 2 from `standard`.
- [ ] Every verdict has `Decision`, `Why`, `Sources` and `Rejected`; a verdict with no source a reader can check (URL and quote, `file:line`, or spec excerpt) is marked `unsourced`.
- [ ] Round 2 verdicts appear only when `Rounds` says round 1 reached no consensus, and `Rounds` says why.
- [ ] Every source under `Chosen · Rests on` is marked `checked ✓`.
- [ ] `Chosen · Basis` is `sourced`, or `most reversible · no verified source` naming why it is the most reversible proposed.
- [ ] The chosen decision is one a debater proposed, and it does not break a fact under `Facts`, nor the spec excerpt unless the problem is a spec contradiction and the decision names the reading it keeps.
- [ ] `Adds` appears only when the decision has an effect someone can observe from outside the code that no requirement covers; its words are observable and contain no `"`.
- [ ] `Against` lists every position not chosen and every shared rejection of the chosen decision, each with why it lost or why it does not hold.
- [ ] No line mentions asking a human or waiting.

# Input

One block:

```
Id       · D<k>
Problem  · <the problem: what must hold, under which conditions; how would you do it?>
Spec     · <spec reference> · "<verbatim excerpt behind the problem>"
Facts    · <one per line: installed versions · infrastructure limits · what the spec excludes (Not doing) · what was tried, how it failed, with evidence (command + output lines, file:line, replay)>
Requirements · <the R lines the decision touches>     optional
Repo     · <absolute path of the checkout the debaters read>
```

No `Id`: use `D?` and say so in the record, since the caller numbers debates.

# How a debate works

The whole debate reads and never runs: no debater and no check starts the app, runs tests or runs project code, because others build and prove whatever is chosen and anything run here could disturb their work.

**A neutral question.** Debaters see only what is dispatched, so a hint in the question comes back as their answer. Make `Problem` an open how/what question that keeps what must hold, in the spec's words where it has them, with no candidate option (a library, pattern or design offered as the answer), no preference or leading word, and no yes/no or either-or. Something installed or fixed is a fact, and a failed attempt is a fact with its evidence: both go in `Facts`, not the question. An opinion posing as a fact is dropped. Record `Asked` (verbatim) and `Dispatched` (yours).

**Five independent debaters.** Dispatch five fresh `general-purpose` agents with clean context, not forks, so the caller's reasoning cannot leak in: three on `strong`, two on `standard` (a tier that does not resolve runs on the session's model). Read [`references/debater.md`](references/debater.md) before dispatching: each gets its "Round 1" prompt, filled from the dispatched block, and none sees labels, tiers or the others in round 1. The five verdicts in the record are what show the dispatch happened.

**Usable verdicts.** A verdict weighs only through sources a reader can check: a quoted page, a `file:line`, or the spec; a claim backed by running code is not one. A debater whose verdict lacks a field or a checkable source, or who returned none, gets one more ask; still without one, its verdict stays in the record as `unsourced` and weighs nothing.

**Round 2 only without consensus.** Consensus means an implementer handed any of the sourced verdicts would build the same thing: mechanism, where data lives, interface, failure behaviour; wording and incidental detail do not split them. Consensus only skips round 2. Without it, each debater gets the others' verdicts anonymised and in no order ("Round 2" in debater.md), continuing its own conversation where the harness allows, else as a fresh agent on the same tier given its round 1 prompt and verdict first; it may change only for a reason a source supports. There is no round 3.

**Decided by checked sources, not votes.** How many agents agree is evidence neither way. Check yourself, read-only, the sources the choice would rest on: the quote is on the raw page (a fetch tool that summarises can paraphrase it, so say when a quote came through one), the `file:line` says what is claimed, the excerpt is in the spec. Check enough of the other positions' sources to know they lost on the evidence, not by default. A source that fails is dropped. Then:

- A position that breaks a `Fact` (repeats a failed attempt without answering why it failed, exceeds a limit, needs a version not installed) or the spec excerpt is out, unless the problem is a spec contradiction and it says which reading it keeps.
- A rejection several debaters share stands against a position unless that position's checked sources answer it.
- Primary sources for the installed version (official docs, the repo's code, the spec) and sources about this problem outweigh general advice. A tie goes to the more reversible decision.
- With no checked source on any position, the most reversible one proposed wins (writes no persisted data, changes no public interface or contract, least work to undo), said so in `Basis`.

The decision is always one a debater proposed: the caller cannot go on without one, and a decision nobody researched has no sources.

**Buildable.** Write the chosen decision in its proposers' words, concrete enough to build. When it introduces behaviour observable from outside the code that no line under `Requirements` covers, state it as one `Adds` line, worded as a requirement is: what someone outside the code can observe, with no `"` inside; its bound names the inputs it covers when the words hold an absolute or a set (every, any, never, all), else `bound —`. The caller appends it as `derived · required by D<k>`. An effect only the code sees (a column, an internal name) gets no `Adds`. When the decision makes an existing derived requirement necessary, name it under `Requires`.

# Output

The caller parses this: keep the first line, the headings and the `Requires` / `Adds` lines exactly in this shape.

```
D<k> · <Dispatched question> → <chosen decision, one sentence>

## D<k> · record
Asked      · <the caller's Problem, verbatim>
Dispatched · <the neutral version sent to the debaters>
Spec       · <reference> · "<excerpt>"
Facts      · <as dispatched, one per line>
Rounds     · 1 · consensus | 2 · no consensus after round 1: <why>

### Verdicts
V<n> · <strong|standard> · round <1|2> · <changed from round 1: yes · why | no>   (round field and change only in round 2)
  Decision · <one sentence>
  Why      · <…>
  Sources  · <source> · <checked ✓ | failed · <what the page says instead> | not checked>   one per line
  Rejected · <alternative · why>   one per line
  <unsourced>   when it is

### Groups
G<n> · <decision> · V<a> V<b> …          round 1, then round 2 when it ran

### Chosen
Decision · <the decision, concrete enough to build>
Group    · G<n>
Basis    · sourced | most reversible · no verified source · <why it is the most reversible proposed>
Rests on · <each source the choice relies on> · checked ✓
Why      · <why this position beat the others, by sources>
Requires · R<n>   only when the decision makes a derived requirement required (the caller marks it `derived · required by D<k>`)
Adds     · "<requirement words>" · bound <domain | —>   only when the decision adds an observable behaviour no requirement covers (the caller appends it as `derived · required by D<k>`)

### Against
- G<n> · <decision> · V<a> … · <its strongest source> · lost because <…>
- Rejection · "<shared reason>" · V<a> V<b> · <why it does not hold against the choice>
```

The first line is the short form a caller keeps; the record is the long form it keeps beside it.
