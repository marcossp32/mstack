---
name: principle-test-behavior-not-implementation
description: Writes and judges tests by what the code's users can observe (return values, errors, saved state, requests sent), so a test fails when behavior breaks and keeps passing when only the internals change. Avoids mocking private helpers, asserting internal call order or recomputing the expected value with the code under test. Use when writing, changing, reviewing or deleting tests, adding a regression test for a bug, or deciding what to mock.
---

# Test behavior, not implementation

A test is a claim about what the code does for whoever uses it: a caller, an end user, another service. Test that, through the interface they use.

- **Behavior** is what users can observe: return values, raised errors, state they can read back, effects outside the code (a file written, a request sent, a message emitted).
- **Implementation** is what they cannot: private helpers, internal call order, intermediate data, which collaborator did the work.

## Why

A test pinned to internals breaks on every refactor and still misses real bugs, so people learn to ignore or rewrite it. A test pinned to behavior is the thing that lets you refactor safely.

## Two questions for each test

1. **If I break the behavior, does it fail?** Make the code return a wrong value, skip an effect or do it twice. If the test still passes, it proves nothing. Usual causes: an assertion looser than the contract, an expected value computed by the code under test, mocking the very thing being tested, or asserting on data the test built itself.
2. **If I change only the internals, does it still pass?** Rename a private helper, merge two functions, change the order of internal steps while keeping every result. If the test fails, it is pinned to the implementation.

A good test answers yes to both.

## What good looks like

- Expected values are written out by hand from the requirement, not produced by the code.
- Mocks sit only at real boundaries the test cannot or should not cross (network, clock, randomness, a paid API), not between the code's own parts.
- Each test name says the behavior it protects, in the user's terms.
- A regression test for a bug fails on the code before the fix (see `principle-prove-it-works`).

## Traps

- **Testing what is easy to reach instead of what matters.** A private helper is easy to call; the public function is what users rely on.
- **Coverage as a goal.** Lines executed say nothing about whether a wrong result would be caught.
