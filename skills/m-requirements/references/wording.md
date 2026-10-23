# Wording a requirement

What makes a requirement line provable, and the words that most often hide a gap. A line is judged by a prover that drives the running app and reads the line exactly as written: a word it cannot observe gives a line it cannot pass; a word it can read two ways gives a line a lazy build passes. Everything below serves that; none of it is a template.

Sources: the characteristics of a well-formed requirement in ISO/IEC/IEEE 29148 (tabulated in Lubos et al., arXiv:2408.10886, Table I); the EARS patterns, https://alistairmavin.com/ears/; the INCOSE Guide to Writing Requirements rules, as listed at https://help.specinnovations.com/4.10-quality-check.

## What a provable line has

- **One effect.** `and`, `or`, `unless`, `otherwise` often join two; split them, each keeping the excerpt. A condition and its effect stay together.
- **One reading.** Name the thing instead of `it` or `this`; no `/` between alternatives; a parenthetical is usually a second line or part of the bound.
- **Something to watch.** What a page shows, an endpoint or command returns, a fresh read of stored data holds. Not steps, payloads or test values.
- **Its trigger or state.** The event or condition it depends on is in the line.
- **No invented solution.** A table, library or algorithm only when the spec names it; then it is asked.
- **The spec's words.** Its nouns, verbs and numbers, reordered at most; a synonym can change what is asked. The repo's name may stand beside the spec's only where the spec's word is ambiguous. Present tense ("the export lists") reads as a fact to observe better than `shall`.

## EARS shapes, when one helps

EARS gives a clear frame for trigger and effect; use it where it clarifies, not as a form to fill. The subject is what the user meets, in the spec's words, or left out when the spec names none (prove finds the surface).

- `The <subject> <response>` · `When <trigger>, the <subject> <response>` · `While <state>, …` · `Where <feature is present>, …` · `If <unwanted condition>, then the <subject> <response>`.

Unwanted-behaviour lines (invalid input, a dependency down, a permission missing) are where most derived lines land.

## Words that usually hide a gap

- Absolutes and sets (all, every, any, both, never, always): need a bound, the inputs covered.
- Vague quantity or quality (some, many, about, fast, large, secure, user-friendly, appropriate): need a measure the prover can observe, e.g. "fast" → "within 2 seconds for 1 000 orders". The measure goes in the line; the excerpt keeps the spec's word, so a reader sees both.
- Escape clauses and open ends (where possible, as required, etc., including but not limited to): state when the effect holds, or close the set with a bound.
- Indefinite time (eventually, once, instantly): the triggering event or a time measure.
- Capability phrasing (be able to, allow, enable): state the effect itself, "lists", not "allows listing".
- Purpose phrases (so that, in order to): the purpose is context; the effect is the line.
- Negations: what happens instead, when the spec says; otherwise keep the negation with a bound.

## Bounds

A bound is the domain prove drives inside and nowhere else: which users, roles, records, sizes, formats, locales. Too wide and the next input tried fails it; too narrow and a lazy build passes.
