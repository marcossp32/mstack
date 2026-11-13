---
name: principle-model-the-domain
description: Encodes the real domain in a data structure (a state machine, a typed model, an enum, a lookup table) instead of scattering it across booleans and if/else chains, so invalid states cannot be represented and branches disappear. A new state goes into one status with its allowed transitions, not into one more boolean that can contradict the others. Use when adding a state, step or outcome to something that has a lifecycle (cancelled, archived, on hold, refunded, rejected, expired...), when code checks several flags together, when the same branching repeats across files, or when adding one more case to a long conditional.
---

# Model the domain

Put what the domain is into the shape of the data. A structure that matches the domain makes wrong states impossible to write and turns branches into lookups.

## Why

Scattered conditionals hide the rules: to learn what states exist you must read every `if`. Booleans combine into states that make no sense (`is_paid and is_cancelled and not is_created`), and each new case is one more branch in many places. Choosing the right structure while writing is cheap. Recovering it later is a refactor that keeps getting postponed.

## Structures to reach for

- **A state machine or a single status enum** instead of several booleans, phases or lifecycle checks. Allowed transitions are written once.
- **A typed model** (class, dataclass, record, typed dict) instead of loose parameters and dicts whose shape every reader must guess.
- **A lookup table, map or registry** instead of a long if/elif or switch spread across files. A new case becomes one entry.
- **A discriminated union** when different kinds of thing carry different data.
- **A module organized around one piece of domain knowledge**, not around steps like load, validate, save.

When none fits, write down what the code must never allow and how the data is read, then pick the structure that encodes exactly that.

## What good looks like

- Invalid combinations cannot be built, or are rejected in one place.
- Adding a case touches one place, not every conditional.
- A reader can learn the domain's states and rules by reading one definition.

## Traps

- **Forcing an abstraction.** If the code is already clear, local and unlikely to grow, plain code is better. A structure must remove more complexity than it adds.
- **Modeling the database or the API instead of the domain.** Storage and wire shapes belong at the boundaries.
- **Breaking what others rely on.** If other code, services or saved records depend on the current fields, the new structure must keep them working, for example by deriving the old fields from the status and reading old records. If that is not possible, a contained change that guards the transitions in one place is better than a rewrite.
