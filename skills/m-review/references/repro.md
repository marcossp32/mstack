# Reproduce

You get one finding: a claim, the condition that shows it, the entry point real input takes. You did not find it. Prove it with two new test files, or give up. Your final message is one of:

```
capture <path> · repro <path> · cmd <command that runs one test file, with {test} where the path goes>
unjudgeable · <why> · files <every file you created | none>
```

## Two files, one assertion apart

Models write tests that pass far more reliably than tests meant to fail. So:

1. **Capture**: a test that drives the entry point into the condition and asserts what the code does today, the broken behaviour included. Run it. It must pass. If it does not, your model of the code is wrong: fix your understanding, never weaken the assertion to get it green.
2. **Repro**: a copy of the capture with only the assertion inverted to the correct behaviour the claim describes. Run it. It must fail, and its message must show the claim (`expected 400, got 201`).

The gate runs the capture, then the repro, 5 times each at HEAD, then the repro at the base. A capture that fails, a repro that passes, or one that fails before reaching its assertion kills the finding.

## Rules

- New files only, named with the finding id, where the repo's runner discovers them (scan Q6). Follow the repo's test conventions.
- Enter through the given entry point. Calling private internals to reach the condition proves nothing about real input.
- One behaviour, one assertion that can fail.
- Deterministic: no clock, network, randomness, file ordering or shared global state. Local only.
- Never touch existing tests, fixtures, config, the harness or the code under test.
- Once handed over, do not touch either file.

## Give up when

- the condition needs infrastructure that is not here: network, hardware, real concurrency, production data;
- you cannot isolate it without dragging in half the system;
- the capture will not pass and you cannot see why.

Giving up is correct and common. A repro that fails for the wrong reason is worse than none. List every file you created, so the caller removes them.
