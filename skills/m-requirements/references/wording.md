# Wording a requirement

A prover drives the running app and reads each line exactly as written: a word it cannot observe gives a line nobody can pass; a word it can read two ways gives a line a lazy build passes, or one it re-judges every round. Nothing below is a template.

Sources: ISO/IEC/IEEE 29148 characteristics of a well-formed requirement (tabulated in Lubos et al., arXiv:2408.10886, Table I); EARS, https://alistairmavin.com/ears/; INCOSE Guide to Writing Requirements rules, as listed at https://help.specinnovations.com/4.10-quality-check.

## What a provable line has

- **One effect.** `and`, `or`, `unless`, `otherwise` often join two; split them, each keeping the excerpt. A condition and its effect stay together.
- **One reading.** Name the thing instead of `it` or `this`; no `/` between alternatives; a parenthetical is usually a second line or part of the bound.
- **Something to watch.** What a page shows, an endpoint or command returns, a fresh read of stored data holds. Not steps, payloads or test values.
- **Its trigger or state** in the line.
- **No invented solution.** A table, library or algorithm only when the spec names it.
- **The spec's words.** Its nouns, verbs and numbers, reordered at most; a synonym can change what is asked. Present tense ("the export lists") reads as a fact to observe.

EARS frames trigger and effect where that helps: `When <trigger>, the <subject> <response>` · `While <state>, …` · `If <unwanted condition>, then the <subject> <response>`. Unwanted-behaviour lines (invalid input, a dependency down, a permission missing) are where most derived lines land.

## Comparisons

A comparison without a stopping point is open-ended: the prover compares whatever it notices, at whatever precision it can reach, and each round notices more. A comparison line therefore carries three things:

1. **The reference**, as something the prover can open: a file in the repo, the output at the base commit, a named screen or command.
2. **The aspects compared**, as a closed list.
3. **The tolerance**, or what is explicitly not compared. When the spec sets a limit ("roughly", "not pixel-perfect", "don't worry about X"), it goes here, in the line.

| Spec says | Unprovable line | Provable line |
|---|---|---|
| "The new page should look like the mockup." | `the page matches the mockup` | `the page shows the mockup's sections in the mockup's order, with its headings and button labels; spacing, colours and fonts are not compared` |
| "Output stays the same as v1." | `output is the same as v1` | `for the inputs in the fixtures folder, the command's output at this change equals its output at the base commit, byte for byte except the timestamp line` |
| "Existing exports still work." | `exports still work` | `each export format the change touches (the two listed in the export menu) still downloads a file that opens and lists the same rows as at the base commit` |

"Still works" and "nothing breaks" are comparisons with the base: name the behaviours and bound them to what the change alters. The whole app is not the bound — a failure in code the change never touched is not this change's to prove.

## Lines a local run cannot settle

Prove has what a local run has: the repo's start command, its seed or fixture data, its stubs. A line needing CI, production volume, a real third-party key or a person's account surfaces only at the final prove. Two ways out, in order:

- Reword to what is observable locally and still serves the purpose: "sends the payment request with the order total" instead of "the customer is charged", where the repo already stubs the provider.
- Otherwise keep the line and flag it in Assumed: `- R<n> needs <the key, account, CI job or environment, exactly> · why <what the local run lacks> · affects R<n>`.

## Words that usually hide a gap

- Absolutes and sets (all, every, any, both, never, always): a bound, the inputs covered.
- Vague quantity or quality (some, many, fast, large, secure, user-friendly, appropriate): a measure in the line, e.g. "fast" → "within 2 seconds for 1 000 records"; the excerpt keeps the spec's word.
- Comparisons (matches, like, same as, consistent with, still works): see above.
- Escape clauses and open ends (where possible, as required, etc., including but not limited to): when the effect holds, or close the set.
- Indefinite time (eventually, once, instantly): the triggering event or a time measure.
- Capability phrasing (be able to, allow, enable): the effect itself, "lists", not "allows listing".
- Purpose phrases (so that, in order to): the purpose is context; the effect is the line.
- Negations: what happens instead, when the spec says; otherwise the negation with a bound.

## Bounds

The domain prove drives inside and nowhere else: which users, roles, records, sizes, formats, locales, surfaces. Too wide and the next input tried fails it, or code the change never touched does; too narrow and a lazy build passes.
