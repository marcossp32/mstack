---
name: m-requirements
description: "Turns a frozen, already-reviewed spec into numbered, observable, bounded requirements, each traced to a verbatim excerpt, plus what the spec excludes, contradicts and leaves open. Use when asked to turn a spec into testable requirements."
---

Turn a frozen spec into the requirement lines the rest of an unattended pipeline works from: plan cuts steps from them, build builds them, and prove drives the running app and judges each line exactly as written, inventing no tolerance and filling no gap. Nobody answers questions: decide what is easy, state what is hard as a neutral problem for a debate, and record why. The spec and the repo are only read; the block is the whole output.

**Where the cost lands.** This step is cheap; proving is the costliest stage, and a line prove cannot settle leaves the PR "Not verified", a failure. Every ambiguity left is paid for at prove, often several rounds over: write each line for a prover that tries hard, reads literally, and keeps looking for a difference until the line says where to stop.

# Done when

One block is returned with the sections `## Requirements`, `## Not doing`, `## Considered`, `## Contradictions`, `## Open decisions`, `## Assumed`, `## How to build`, `## Laziest build` and `## Trace`, in that order, each holding its lines or `none`, and `python3 <this skill's directory>/scripts/check.py --spec <frozen spec file> --out <block file>` prints `PASS`. `check.py` settles shape, verbatim excerpts and Trace coverage; everything in The bar is your judgement. A WARN never fails the block.

# Acceptance criteria

- [ ] Every sentence that asks for an observable effect reaches an R line, and every asked line says what its excerpt says, adding only measures and bounds an `## Assumed` line names against that id.
- [ ] Each line is one effect someone outside the code can observe, with one reading; every vague term and every comparison carries its measure, and an `## Assumed` line says where it came from.
- [ ] Every line a local run cannot settle is reworded to what one can observe, or has an `## Assumed` line naming what settles it.
- [ ] Each contradiction names the reading chosen, why, and `undo hard | easy`; every `O<n>` is hard to undo and neutral; every easy decision is an `## Assumed` line.
- [ ] `## Laziest build` names one build that passes every line and still misses the spec, and the change that closed the gap.

# Inputs

- The frozen spec, in a file. It is the only spec: the live one may have moved.
- The repo, to learn what the spec's terms mean (glossary, names in the code, limits it already enforces), what it already guarantees (stored formats, existing behaviour, public interfaces), and how it runs locally (which services, keys and data a local run has).

Once returned, ids and words are final: everything downstream cites them, and only a bound may change later, at the cost of the change not counting as proved.

# The bar

- **Faithful.** Every asked line says what its excerpt says, in the spec's terms, adding only measures and bounds that an `## Assumed` line names. Every sentence of the spec (headings and list items too) ends somewhere in the Trace, and every sentence asking for an observable effect reaches an R line. A spec that already lists requirements is normalised, not reinterpreted; its labels (REQ-7) stay inside the excerpt. Read the whole spec before finalising any line: a later sentence may bound, exclude or contradict an earlier one — including a limit like "not pixel-perfect" or "don't chase X", which must land in the line it limits, or prove will chase exactly that.
- **One effect, one line.** Each line is one effect someone outside the code can watch hold, with its trigger or state, and one reading. Two effects are two lines. One effect the spec states twice is **one** line whose `from` joins both excerpts with ` + `, and both sentences trace to it: a duplicate line is proved twice and can be judged two ways. Name an implementation only where the spec does.
- **Bounded to what the change touches.** An absolute or a set names the inputs it covers; a vague term gets a measure in the line. Prefer the spec's figure, then a limit the repo enforces (`file:line` in Assumed), then the narrowest domain that still serves the spec's purpose. "Nothing else breaks" bounded to the whole app fails on code the change never touched: bound it to the surfaces the change alters and what depends on them.
- **Comparisons and judgements finite.** "Matches", "looks like", "same as before", "still works" cost the most: each prover picks its own set and tolerance and finds a finer difference every round (3-5 proves for one page). Such a line names the reference (a file, the base commit, a named screen), a closed list of measurable aspects each with its tolerance, and what is not compared — the spec's own limit where it gives one. Prove checks the whole list in one pass, naming every difference, so one fix round closes them. What no measure captures (does it feel right) is its own line ending ` · human`, shown to a person beside the reference in the PR; never one a measure could settle. See [references/wording.md](references/wording.md#comparisons).
- **Settleable by a local run.** Prove runs the app as the repo runs it locally. A line whose surface is the host's CI is not prove's: end it ` · CI <check>`, the check's name in the repo's CI config, or `all` when the spec names none; the orchestrator settles it from the host's checks. A line that needs production scale or data, an external service's key, or a person's account fails only at the end. Word it, where the spec's purpose survives, as what a local run can observe (the request sent, the repo's stub); otherwise keep it and say so in `## Assumed` as `- R<n> needs <the key, account or environment, exactly> · why <what the local run lacks> · affects R<n>`, so it is asked for before any building.
- **Derived only where it shows.** An implied effect (empty state, failing input or dependency, a limit reached) is a `derived` line only where a user of an asked effect would see the difference; each costs a drive.
- **How to build is kept.** A sentence on how to do the work (make an inventory first, use this tool) is quoted verbatim under `## How to build`, not left as `context`, or it never reaches the builders.
- **No lazy build passes.** Name the cheapest build that passes every line yet misses the spec (a hard-coded value, the empty case only, one input of a set) and close it by tightening wording or bound within the excerpt, or with a `derived` line. Record the last one under `## Laziest build`.

Read [references/wording.md](references/wording.md) before wording a line that resists this bar.

# Decisions

A decision is **hard to undo** when reversing it costs more than a code change: what was stored, called or sent under it must be migrated, broken or lost, or what others built on it (a public interface, a core dependency) must change too. Otherwise it is **easy**.

- Easy: take the reading that serves the app's users best and stays closest to the spec, as `- <decision> · why <reason, source when there is one> · affects R<n>` under `## Assumed`.
- Hard: `O<n> · <neutral problem> · from "<excerpt>" | from R<m> · facts <what the spec and repo fix>`. State what must hold and what constrains it, ending at most with `how?`; an option, a preference or a yes/no question steers the debate: "Existing orders must survive the new status field; how?". No requirement is written for the outcome; a debate adds it later.

# Contradictions

Two excerpts that cannot both hold are a contradiction; a vague word is not (it needs a measure). They hide most often where **two sentences act on the same thing** — the same field, screen, command, state or limit — so for each thing the spec changes, read every sentence that touches it side by side. Choose the reading that serves the app best (often the more specific sentence, the one naming a surface, the safer one where data or access is at stake), word the lines in it, and trace the other excerpt to `C<n>`. `undo` follows Decisions.

A new rule can also contradict what the repo **already guarantees** (a stored format, an existing behaviour, a public contract). That has no second spec excerpt, so it is not a `C` line: if keeping both is hard to undo it is an `O` line with the guarantee and its `file:line` in `facts`; if easy, an Assumed line naming the guarantee and the reading chosen.

# Output

Return exactly this block, nothing before or after it, since it is parsed. A section with nothing in it holds `none`. Quotes delimit the fields, so requirement text uses `'` and an excerpt is cut to a verbatim span with no `"` in it.

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

- Ids run R1..Rn in order; never write `required by D<k>` or `retired by D<k>` (a debate adds them).
- `bound` is the inputs the line covers ("orders of one store, 0 to 10 000", "each role in the roles table"); `—` only when the line has no absolute or set.
- Not doing holds only what the spec itself excludes, each with its excerpt: build, review and prove leave it out. Considered excludes nothing (optional or future items, ideas left out, each with why); prove still judges it.
