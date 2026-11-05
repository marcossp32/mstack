---
name: m-requirements
description: "Turns a frozen, already-reviewed spec into numbered, observable, bounded requirements, each traced to a verbatim excerpt, plus what the spec excludes, contradicts and leaves open. Use when asked to turn a spec into testable requirements."
---

Turn a frozen spec into requirement lines that someone else proves later, with nobody to ask. The prover runs the app as the repo runs it locally, reads each line literally, invents no tolerance, fills no gap, and keeps looking for a difference until the line says where to stop. A line it cannot settle leaves the change unproven, a failure paid for after all the building, so every ambiguity you leave costs more there than it costs to close here. Decide what is easy, state what is hard as a neutral problem for someone else to settle, and record why. The spec and the repo are only read; the block is the whole output.

# Done when

The block in [Output](#output) is returned, each section holding its lines or `none`, and this prints `PASS`:

```sh
python3 <this skill's directory>/scripts/check.py --spec <frozen spec file> --out <block file>
```

`check.py` settles shape, verbatim excerpts and that the Trace covers the whole spec; fix each FAIL and run it again. A WARN never fails the block. Where it cannot run, or a round fixes no FAIL, return the block as it stands. What the script cannot see is the rest of this skill.

# Inputs

- The frozen spec, in a file. It is the only spec: the live one may have moved. A file it attaches or references (a mockup, a prototype) is part of what it asks: the line for the sentence naming it carries what that file holds, quoting the spec's sentence.
- The repo, read for what the spec's terms mean (glossary, names in the code, limits it enforces), what it already guarantees (stored formats, existing behaviour, public interfaces), and what a local run has (its start command, services, keys, accounts, data, browsers) and what only CI or another environment has.

Once returned, ids and words are final: everything after cites them.

# Every sentence lands once

Read the whole spec, attached files included, before finalising any line: a later sentence may bound, exclude or contradict an earlier one, and a limit such as "not pixel-perfect" or "don't chase X" belongs in the line it limits, or the prover chases exactly that.

Every spec sentence, headings and list items included, ends in one Trace line. Where it goes:

- An observable effect the spec asks for: an `asked` R line, saying what its excerpt says in the spec's terms, adding only measures and bounds an `## Assumed` line names against that id. A spec that already lists requirements is normalised, not reinterpreted; its labels (REQ-7) stay inside the excerpt.
- One effect the spec states twice: **one** line whose `from` joins both excerpts with ` + `, both sentences tracing to it. A duplicate line is proved twice and can be judged two ways.
- What the spec itself excludes: `## Not doing`, which build, review and proof leave out.
- What the spec leaves optional or future, or an idea set aside: `## Considered`, with why; it excludes nothing.
- How to do the work (make an inventory first, use this tool, this order): quoted verbatim under `## How to build`, which reaches the builders; `context` never does.
- Two excerpts that cannot both hold: a `C<n>` line ([Contradictions](#contradictions)).
- A hard-to-undo choice the spec leaves open: an `O<n>` line ([Decisions](#decisions)).
- Purpose, background, history: `context · <why>`.

A `derived` line is an effect the spec implies (an empty state, a failing input or dependency, a limit reached), written only where a user of an asked effect would see it, since each one costs a drive.

# Writing a line

Each line is one effect someone outside the code can watch hold, with its trigger or state, and one reading: what a page shows, a command or endpoint returns, a fresh read of stored data holds. Two effects are two lines. Name an implementation only where the spec does. Read [references/wording.md](references/wording.md) before wording a comparison, a judgement, or a line that resists one reading.

- **Bounded to what the change touches.** An absolute or a set names the inputs it covers in `bound`; a vague word gets a measure in the line. Take the spec's figure first, then a limit the repo enforces (its `file:line` in Assumed), then the narrowest domain that still serves the spec's purpose. "Nothing else changes" bounded to the whole app fails on code the change never touched: bound it to the surfaces the change alters and what depends on them, and say how sameness is seen.
- **Comparisons and judgements finite.** "Matches", "looks like", "same as before", "still works" let each prover pick its own set and tolerance and find a finer difference each round. Such a line names the reference (a file, the base commit, a named screen), a closed list of measurable aspects each with its tolerance, and what is not compared, the spec's own limit included where it gives one, so one proof checks the whole list and one fix round closes it. What no measure captures (does it feel calm) is its own line ending ` · human`, which a person judges beside the reference; never one a measure settles.
- **Settleable by a local run.** A line whose surface is the host's CI ends ` · CI <check>`, the check's name in the repo's CI config, or `all` when the spec names none; the host's checks settle it, nobody drives it. A line needing production scale or data, an external service's key or a person's account fails only at the end: where the spec's purpose survives, word it as what a local run can observe (the request sent, the repo's stub); otherwise keep it and add `- R<n> needs <the key, account or environment, exactly> · why <what the local run lacks> · affects R<n>` under `## Assumed`, so it is asked for before any building.

# Contradictions

Two excerpts that cannot both hold are a contradiction; a vague word is not (it needs a measure). They hide where **two sentences act on the same thing** (the same field, screen, command, state or limit), so read side by side every sentence touching each thing the spec changes. A sentence that adopts a standard, a syntax or a format (a regex dialect, semantic versioning, ISO 8601 dates) brings all of that standard's rules along, those it does not spell out included: another sentence that breaks one of them contradicts it. Choose the reading that serves the app best (often the more specific sentence, the one naming a surface, the safer one where data or access is at stake), word the lines in it, and trace the other excerpt to `C<n>`. `undo` follows [Decisions](#decisions).

A new rule can also break what the repo already guarantees (a stored format, an existing behaviour, a public contract). With no second spec excerpt it is not a `C` line: where keeping both is hard to undo it is an `O` line with the guarantee and its `file:line` in `facts`; where easy, an Assumed line naming the guarantee and the reading chosen.

# Decisions

A decision is **hard to undo** when reversing it costs more than a code change: what was stored, called or sent under it must be migrated, broken or lost, or what others built on it (a public interface, a core dependency) must change. Otherwise it is **easy**.

- Easy: take the reading that serves the app's users best and stays closest to the spec, as an Assumed line whose why names its source when there is one.
- Hard: an `O<n>` line stating what must hold, with what the spec and repo fix under `facts`, ending at most with `how?`: "Existing orders must survive the new status field; how?". An option, a preference or a yes/no question steers whoever settles it. No requirement is written for the outcome; it is added once settled.

# Laziest build

Name the cheapest build that passes every line yet misses the spec (a hard-coded value, the empty case only, one input of a set) and close it by tightening a line's wording or bound within its excerpt, or with a `derived` line. Record the last one found.

# Output

Return exactly this block, nothing before or after: it is parsed. A section with nothing in it holds `none`. Quotes delimit the fields, so requirement text uses `'` and an excerpt is cut to a verbatim span of the spec file with no `"` in it. A Trace line quotes its spec sentence whole, any `"` in it included.

```
## Requirements
R<n> · <asked | derived> · "<the requirement, observable>" · bound <domain | —> · from "<verbatim spec excerpt>"[ + "<excerpt>"] | from R<m>[ · CI <check | all> | · human]
## Not doing
- <what> · from "<excerpt>"
## Considered
- <what> · why <reason>[ · from "<excerpt>"]
## Contradictions
C<n> · "<excerpt A>" vs "<excerpt B>" · reading <chosen> · why <reason> · undo <hard | easy> · affects R<a>
## Open decisions
O<n> · <neutral problem> · from "<excerpt>" | from R<m> · facts <constraints from the spec>
## Assumed
- <decision> · why <reason> · affects R<n>
## How to build
- "<spec sentence on how to do the work, verbatim>"
## Laziest build
<the build that passes every line and misses the spec> · closed by <what changed>
## Trace
"<spec sentence, verbatim>" → R<a> R<b> | Not doing | Considered | How to build | C<n> | O<n> | context · <why>
```

- Ids run R1..Rn in order. A line never carries `required by D<k>` or `retired by D<k>`: those are added once a decision is settled.
- `bound` is the inputs the line covers ("orders of one store, 0 to 10 000", "each role in the roles table"); `—` only when the line has no absolute or set.
