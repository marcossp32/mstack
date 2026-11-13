---
name: principle-fix-root-causes
description: Fixes a bug where it starts, not where it shows. Traces the wrong value or state back to the first place the code made a wrong decision and changes that, instead of adding a guard, default, try/except or retry where it crashed. Use when debugging a crash, an error or a failing test, when reviewing a bug fix, or when about to add a None check, fallback or catch to make an error go away.
---

# Fix root causes

The place where an error shows is the **symptom**. The **root cause** is the first place the system did something it should not, or failed to handle a state it should handle. Fix the root cause.

## Why

A fix at the symptom hides the evidence. The wrong state is still produced, and it breaks the next piece of code that meets it, far from where it started. Each hidden bug also leaves a workaround that nobody can explain later.

## The key question

When code breaks on some state, ask: **is that state legitimate?**

- **Yes, the system can really be in it** (an empty list, a missing optional field, a slow network). Then the code that broke is the root cause: make it handle that state.
- **No, it should never exist.** Then a check where it broke hides the bug. Find the code that produced the state and fix it there.

Guards, retries, swallowed errors, clamped values and defaults are fine for legitimate states. For illegitimate ones they are how bugs get hidden.

## What good looks like

- You reproduced the failure before changing anything, and saw it pass after (see `principle-prove-it-works`).
- You can name the line where things first went wrong and say why it is wrong, from what you observed (the real error, the real values), not from a guess.
- The fix is there. Fixing it there also fixes every other consumer of that wrong state, with no change to them.
- You looked for the same mistake elsewhere: the same faulty pattern often lives in sibling code.

## Traps

- **Stopping at the first "why".** Keep asking why until the answer is a wrong decision in code, not a consequence of an earlier one.
- **Guessing instead of looking.** When the cause is not clear, print or log the real state. Reading code gives hypotheses; running it gives facts.
- **The root cause is in code you do not own** (a library, an external service). Then a guard is the right fix: put it at the boundary where that data enters your code, and say why (see `principle-boundary-discipline`).

## Reviewing a fix

A fix that only adds a guard, a default or a catch near the crash is suspicious. Ask whether the state it handles is legitimate. If not, the fix is a symptom fix: say where the state is produced.
