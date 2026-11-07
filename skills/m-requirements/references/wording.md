# Wording a requirement

A prover reads each line exactly as written: a word it cannot observe gives a line nobody can pass; a word it can read two ways gives a line a lazy build passes, or one it re-judges every round. Nothing below is a template.

## What a provable line has

- **One effect.** `and`, `or`, `unless`, `otherwise` often join two; split them, each keeping the excerpt. A condition and its effect stay together.
- **One reading.** Name the thing instead of `it` or `this`; no `/` between alternatives; a parenthetical is usually a second line or part of the bound.
- **Something to watch**, not steps, payloads or test values.
- **The spec's words.** Its nouns, verbs and numbers, reordered at most; a synonym can change what is asked. Present tense ("the export lists") reads as a fact to observe.

EARS frames trigger and effect where that helps: `When <trigger>, the <subject> <response>` · `While <state>, …` · `If <unwanted condition>, then the <subject> <response>`. Unwanted-behaviour lines (invalid input, a dependency down, a permission missing) are where most derived lines land.

## Comparisons

A comparison without a stopping point is open-ended: the prover compares whatever it notices, at whatever precision it can reach, and each round notices more. Write the list of aspects in the line rather than leaving it to the builder: a builder that draws up its own list and a prover that draws up another disagree every round. A whole page can need dozens of aspects; write them all.

- **The reference** is something the prover can open: a file in the repo, the output at the base commit, a named screen or command.
- **The aspects** are things a script can measure on both sides (text, order, count, size, colour, duration, presence), per element and per condition the spec names (viewport, state), each with its tolerance.

Illustrative pairs, not templates:

| Spec says | Unprovable line | Provable line |
|---|---|---|
| "The new page should look like the mockup." | `the page matches the mockup` | `the page shows the mockup's sections in the mockup's order, with its headings and button labels; spacing, colours and fonts are not compared` |
| "Match the prototype, details included." | `the hero matches prototype.html` | `at 1280x720 and 390x844, each hero element of prototype.html (heading, subheading, button, image) has the prototype's text exactly, font size and weight within 1px and one step, colour exactly, position and size within 4px, and its entrance animation's duration within 50 ms; image content is not compared` + a separate `the hero feels like the prototype's · human` only if the spec asks for feel |
| "Output stays the same as v1." | `output is the same as v1` | `for the inputs in the fixtures folder, the command's output at this change equals its output at the base commit, byte for byte except the timestamp line` |
| "Existing exports still work." | `exports still work` | `each export format the change touches (the two listed in the export menu) still downloads a file that opens and lists the same rows as at the base commit` |

"Still works" and "nothing breaks" are comparisons with the base: name the behaviours.

## Words that usually hide a gap

- Absolutes and sets (all, every, any, both, never, always): a bound, the inputs covered.
- Vague quantity or quality (some, many, fast, large, secure, user-friendly, appropriate): a measure in the line, e.g. "fast" → "within 2 seconds for 1 000 records"; the excerpt keeps the spec's word.
- Escape clauses and open ends (where possible, as required, etc., including but not limited to): when the effect holds, or close the set.
- Indefinite time (eventually, once, instantly): the triggering event or a time measure.
- Capability phrasing (be able to, allow, enable): the effect itself, "lists", not "allows listing".
- Negations: what happens instead, when the spec says; otherwise the negation with a bound.
