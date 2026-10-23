---
name: m-requirements
description: "Turns a frozen, already-reviewed spec into numbered, observable, bounded requirements, each traced to a verbatim excerpt, plus what the spec excludes, contradicts and leaves open. Use when asked to turn a spec into testable requirements."
---

Turn a frozen spec into the requirement lines a prover judges the change against, and that its verdict rests on: each one observable effect, bounded, traced to a verbatim excerpt. Alongside them go what the spec excludes, where it contradicts itself, the hard-to-undo decisions it leaves open, and the easy decisions taken in their place. It runs unattended: nobody answers a question, so decide what is easy, state what is hard as a neutral problem for a debate, and record why each time. The block is the whole output; the spec and the repo are only read.

# Done when

One block is returned with the sections `## Requirements`, `## Not doing`, `## Considered`, `## Contradictions`, `## Open decisions`, `## Assumed`, `## Laziest build` and `## Trace`, in that order, each holding its lines or `none`, and `python3 <this skill's directory>/scripts/check.py --spec <frozen spec file> --out <block file>` prints `PASS`.

# Acceptance criteria

- [ ] Every sentence of the spec (headings and list items included) has a `## Trace` line naming the requirements, `Not doing`, `Considered`, contradiction or open decision it maps to, or `context · <why>`, and every sentence that asks for an effect someone can observe maps to an R line.
- [ ] Every `asked` line has a `from` excerpt that appears in the spec verbatim; every `derived` line quotes the spec or names an earlier `asked` line.
- [ ] Every asked line says what its excerpt says, in the spec's terms, adding only measures and bounds that an `## Assumed` line names against that id.
- [ ] Ids run R1..Rn, unique, in order; no line carries `required by D<k>` or `retired by D<k>`.
- [ ] Every requirement with an absolute or a set (every, each, any, all, both, never, always) names its bound, never `—`.
- [ ] Every vague term the spec uses (fast, large, secure, user-friendly) has a measure in its line, and an `## Assumed` line says where the measure came from.
- [ ] Each requirement states one effect someone can observe from outside the code; none names an implementation the spec does not name.
- [ ] `## Not doing` holds only what the spec itself excludes, each with its excerpt.
- [ ] Each contradiction quotes both excerpts and names the reading chosen, why, and `undo hard | easy`.
- [ ] No open decision contains an option, a preference or a yes/no question.
- [ ] Every `O<n>` is hard to undo as Decisions defines it; every easy decision is an `## Assumed` line `- <decision> · why <reason> · affects R<n>`.
- [ ] No requirement or excerpt contains `"`.
- [ ] `## Laziest build` names one build that passes every line and still misses the spec, and the change that closed the gap.

# Inputs

- The frozen spec, in a file, and its reference. The frozen copy is the only spec: the live one may have moved since it was frozen.
- The repo, to understand the spec's terms: a glossary, the names the code uses, limits it already enforces. Read it for what the spec's terms mean: versions and infrastructure decide no line here.

Once returned, the ids and words are final: everything downstream cites them, and only a bound may change later.

# The bar

A prover drives the running app and judges each line exactly as written, inventing no tolerance and filling no gap. A word it cannot observe makes a line nobody can pass; a word it can read two ways makes a line a lazy build passes. So the lines are:

- **Faithful.** Nothing added, nothing dropped: every asked line says what its excerpt says, in its words, and every sentence of the spec ends somewhere in the Trace. A spec that already lists requirements is normalised, not re-interpreted: split, reshaped, bounded, meaning unchanged, its own labels (REQ-7) kept inside the excerpt. A later sentence may bound, exclude or contradict an earlier one, so a line is final only against the whole spec. An example that shows something its requirement's words do not (a format, a value) is asked in its own right.
- **One observable effect.** Each line is one effect someone outside the code can watch hold, with the trigger or state it depends on, and one reading. Two effects are two lines with the same excerpt. Say what is seen, not how to drive it, and name an implementation only where the spec names it.
- **Bounded and measured.** An absolute or a set names the inputs it covers, and a vague term gets a measure written into the line: an unbounded `every` fails on the next input tried, an over-narrow one lets a lazy build pass. Prefer the spec's figure, then a limit the repo already enforces (`file:line` in the Assumed line), then the narrowest domain that still serves the spec's purpose; list each choice under Assumed. Choose once: a bound changed later keeps the change from counting as proved.
- **Derived only where it shows.** What the spec implies but does not say (the empty state, a failing input or dependency, a limit reached) becomes a `derived` line only where a user of an asked effect would see the difference. Each costs a drive and never blocks, so each one has to earn that drive.
- **No lazy build passes.** Name the cheapest build that passes every line yet misses the spec (a hard-coded value, the empty case only, one input of a set) and close the gap by tightening the asked line's wording or bound within its excerpt; an asked line exists only where the spec asks. A gap the excerpt cannot close is a `derived` line. Record the last laziest build under `## Laziest build`.

Read [references/wording.md](references/wording.md) before wording a line that resists this bar: it holds what makes a line provable and the words that most often hide an ambiguity.

`check.py` settles the shape, the verbatim excerpts and the Trace's coverage; whether a line is faithful, observable and closed against the laziest build is the reader's judgement. A WARN never fails the block: it marks a word the script cannot judge, such as one in an open decision that may name an option.

# Decisions

A decision is **hard to undo** when reversing it later costs more than a code change: what was stored, called or sent under it has to be migrated, broken or lost, or what others built on it (a public interface, a core dependency) has to change with it. One a code change alone reverses is **easy**.

- Easy: decide it, taking the reading that serves the app's users best and stays closest to the spec, as one `## Assumed` line: `- <decision> · why <reason, source when there is one> · affects R<n>`.
- Hard: one `## Open decisions` line: `O<n> · <neutral problem> · from "<excerpt>" | from R<m> · facts <what the spec fixes or excludes>`. State what must hold and what constrains it, ending with `how?` at most, because an option, a preference or a yes/no question steers the debate: "Existing orders must survive the new status field; how?", not "Should we add a nullable column?". The outcome gets no requirement here: a debate that needs one adds it later as `derived · required by D<k>`.

# Contradictions

The spec was reviewed, so read it for its intent: two excerpts that cannot both hold are a contradiction; a vague word is not (it needs a measure). Choose the reading that serves the app best (often the more specific sentence, the one naming a surface, the safer one where data or access is at stake), word the affected lines in it, and trace the other excerpt to `C<n>`. `undo` says whether that reading is hard to undo as Decisions defines it, which decides whether it is debated.

# Output

Return exactly this block, nothing before or after it, since it is parsed. A section with nothing in it holds `none`. Quotes delimit the fields, so requirement text uses `'` and an excerpt is cut to a verbatim span with no `"` in it.

```
## Requirements
R<n> · <asked | derived> · "<the requirement, observable>" · bound <domain | —> · from "<verbatim spec excerpt>"[ + "<excerpt>"] | from R<m>
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
## Laziest build
<the build that passes every line and misses the spec> · closed by <what changed>
## Trace
"<spec sentence, verbatim>" → R<a> R<b> | Not doing | Considered | C<n> | O<n> | context · <why>
```

- `from` with ` + ` joins excerpts when one effect needs two sentences (the effect and its condition).
- `bound` is the inputs the line covers ("orders of one store, 0 to 10 000", "each role in the roles table"); `—` only when the line has no absolute or set.
- Not doing excludes: build, review and prove leave it out, so it holds only what the spec itself excludes. Considered excludes nothing (optional or future items, ideas left out, each with why); review and prove still judge it.
