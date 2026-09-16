<!-- Copied from shared/proving-tests.md by scripts/sync-shared.mjs. Edit the source, not this copy. -->

# Proving a test catches bugs

Use when there was no red step (tests for existing code), when the step is hard to undo, or when reviewing a step.

1. Start green.
2. Make one small production change that breaks the behaviour: flip a comparison (`>`→`>=`, `==`→`!=`), swap `&&`/`||`, return a constant, delete a line inside a condition, remove a validation, shift a boundary by one.
3. Run the tests. One must go red. None does: that behaviour is untested, whatever coverage says, and the next test goes there.
4. Undo the change.

Repeat 2–4 for each change that applies, one at a time.

Mutation tools automate this: Stryker (JS, TS, C#, Scala), PIT (Java), mutmut and Cosmic Ray (Python), Infection and Pest (PHP), go-mutesting (Go). They are slow: use them only on the core logic of hard-to-undo work. Each surviving mutant is a line no test noticed: add a test there from the intended behaviour, not one written to kill that mutant. Ignore the score.
