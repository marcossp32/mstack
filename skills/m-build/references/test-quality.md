# Test quality

From Kent Beck's test desiderata and Khorikov's four pillars.

A good test goes red when behaviour changes and stays green when code is only rearranged (moved, renamed, split). Tests written from the code instead of the behaviour usually fail the second.

## Assert on

- Return values.
- State afterwards, read through the public interface.
- What left the system: rows written, messages sent, response bodies.

Never on which internal functions ran, their arguments or order, or private fields. "`save` was called once" passes when `save` does nothing and fails on a rename.

## Fakes

- Fake what is outside the process and your control: third-party APIs, payments, email.
- Use the real thing for what you own: your database (test container), modules, pure functions, in-memory structures.
- A test needing many fakes means the code reaches too far: say so under "What to watch" in the PR.

## Also

Order-independent · deterministic (fix or delete flaky tests) · fast · clear failure (`expected 3, got 0`) · readable without the code under test.

## Deleting

When a refactor (loop step 5) turns a test red, delete it if any holds; coverage is no reason to keep it:

- No assertion.
- Only checks that a call was made.
- Flaky, and nobody will fix it now.
- Must change for any refactor.
- Tests code with no logic: a getter, a constant.
- Another test already fails whenever it does.

Whether the tests would catch a bug: [`proving-tests.md`](proving-tests.md).
