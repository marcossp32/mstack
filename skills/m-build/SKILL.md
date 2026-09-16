---
name: m-build
description: "Builds one step test-first: the test comes from the spec, is watched failing, and is never edited to pass. Use as the build stage of /m-feature, or for any change whose tests must mean something."
---

Build one step test-first, so no test is shaped around code that already works. Everything you write follows [`references/writing.md`](references/writing.md); your final message is the PR number, or the stop line.

**Never edit a test to make it pass.** A test that failed on its assertion is frozen. If the code cannot satisfy it, fix the code, or stop: no PR, one line naming the spec behaviour that is wrong.

# Inputs

- The step issue and its Done when.
- How the repo tests (`/m-scan`). Write tests the same way.
- Timeouts and limits (`/m-research`).

No observable Done when: write nothing and return no PR, with one line saying what could not be observed and a testable criterion that would fix it.

# Loop

One behaviour at a time.

1. **One failing test**, from the Done when, not from code. Name it after the behaviour in the repo's words (`rejects a draft with no title`); a name needing "and" is two tests. Assert on outputs, not calls. What to assert on and what to fake: [`references/test-quality.md`](references/test-quality.md).
2. **Run it. It must fail on its assertion**, showing expected and actual. Import errors, missing functions (`x is not a function`), syntax errors, setup crashes and a bare `AssertionError` do not count: fix and rerun. Commit the red test.
3. **Minimum code** that passes: no extra cases, options or side edits. Commit.
4. **Whole suite green.** Red elsewhere means your change broke it: fix the code.
5. **Refactor** without touching tests. A test goes red: you changed behaviour, undo — unless the test was pinned to internals (see test-quality.md).
6. Next behaviour.

# Modes

- **Bug fix**: a failing test that reproduces the bug, then the fix.
- **Tests for existing code**: take the intended behaviour from the issue, docs or human, never from the code. Then break the code to prove each test reacts: [`references/proving-tests.md`](references/proving-tests.md).
- **Rework** (must-fix list from `/m-review`, same branch). Sort the list before editing:
  - Behaviour findings (unhandled case, wrong result, Done when not met): the loop, test first.
  - Construction findings, with no behaviour to pin down (timeout, resource release, environment value, credential): fix directly, and list them in the PR with why each has no test.
  - Answer every finding, disagreements included, with reasons. Tests that went red on their assertion stay frozen; the must-fix list is no licence to edit them.

# Every step, whatever the issue says

1. Same input twice gives the same result; tested.
2. Empty and huge responses handled; tested.
3. Behaviour can change in production without a code edit or redeploy; per-environment values come from the environment.
4. Failure logs are enough to diagnose without reproducing.
5. When migrating data: a deploy that stops halfway can be re-run safely.
6. Every call outside the process has a timeout, with `/m-research`'s value.
7. Resources are released on error paths.

# Pull request

You are already on the step branch. Target the feature branch.

- What changed: one bullet per behaviour.
- `Part of #<n>`, without retelling the issue. Never `Closes`: it is ignored on non-default branches.
- What to watch, including any test that needed many fakes.
- Answers, checked with `git diff` and commit order:
  - Did any test file change after its production code?
  - Does every test assert?
  - Did every test fail on its assertion before its production code existed?
  - Would the tests go red if the code broke? When hard to undo, prove it: [`references/proving-tests.md`](references/proving-tests.md).
