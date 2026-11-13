---
name: principle-redesign-from-first-principles
description: Integrates a new requirement into an existing design as if it had been known from the start, instead of bolting it on with special cases, flags and exceptions next to the old design. Asks what the code would look like if written today with the requirement, and updates every affected type, call site, test and doc. Use when adding a feature that does not fit the current structure, when a change needs a special case or an "if new_mode" branch, or when extending a model, API or schema.
---

# Redesign from first principles

When a new requirement arrives, do not glue it onto the current design. Ask: **if we were writing this today, knowing this requirement, what would we build?** Then move the code toward that.

## Why

A bolted-on requirement leaves two designs living side by side: the old one, and special cases that patch around it. Each new requirement adds more patches, and soon nobody can say what the design is. Folding the requirement into the design keeps one clear model, and that keeps the next change cheap too.

## What good looks like

- **Understand before changing.** You read the code the requirement touches and can say what the current design is and why.
- **One model, not two.** The result reads as if the requirement had always been there: no `if legacy` / `if new_feature` branches, no parallel structures doing almost the same thing.
- **Every reference follows.** Types, call sites, tests, docs and examples all reflect the new design. A half-moved concept is worse than either end.
- **Delivered in steps.** Think about the whole redesign, then deliver it in small changes that each keep things working.

## When not to

The redesign must be proportional. If the requirement fits the current design with a small natural change, that is the design: no need to rebuild anything. Redesign when the honest fit needs special cases, duplicated paths or a flag that changes what a thing means.

## Traps

- **Preserving the old shape out of caution.** If no external user depends on it, migrate the callers and remove the old path in the same change instead of keeping compatibility code. If external users do depend on it, keep one deprecated adapter at the boundary, not two paths through the core.
- **Redesigning beyond the requirement.** Change what the requirement touches. Unrelated improvements are a separate change.
