---
name: principle-smallest-change
description: Makes the smallest change that fully solves the problem and removes before it adds. Deletes dead code and duplicates first, and does not add layers, options, config, validators or abstractions that nothing asked for. Use when judging the size of a diff or a plan, refactoring, or when tempted to add a flag, option, config, extra parameter, validator or "for the future" generality.
---

# Smallest change

Solve the problem with the least new code, and leave the system no more complex than you found it. When you can, leave it simpler.

"Small" is measured by the complexity left in the system, not by diff lines. When a requirement only fits through special cases, a bigger change that folds it in is the smaller result: see `principle-redesign-from-first-principles`.

## Why

Every line added is a line someone must read, test and keep working. Speculative generality (an option nobody uses, a layer for a second implementation that never comes, a check for an input that cannot arrive) costs every day and pays only if a guess comes true. Small diffs are also easier to review and to undo.

## What good looks like

- **Subtract first.** If dead or duplicated code is in the path of your change, remove it first and build on the simpler base. Elsewhere, note it.
- **Reuse before writing.** Use what the repo, the language or the library already provides.
- **Design for what is used.** Handle the cases that really occur, as shown by the requirement and the code. Not imagined ones.
- **One place for each decision.** If the same choice would appear in several places, make it once and pass the result.
- **Fewer lines over "elegant" boilerplate.** Three plain similar lines are often better than a new abstraction.

"Smallest" does not mean doing less than asked, or doing it worse. The change must fully meet the requirement, including its error cases and tests.

## Self-check

For each piece you added (a file, a class, a function, a parameter, an option), ask: if I delete it, does a requirement stop being met? If not, delete it.

## Traps

- **Gold-plating while you are there.** Unrelated cleanups and renames make the diff bigger and the review harder. Note them, or do them in a separate change.
- **Copy-paste instead of reuse.** Duplication is a bigger diff that hides as a small one.
