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

The gate runs the capture, then the repro, 5 times each at HEAD, then the repro at the base, and the capture there when the repro fails. A capture that fails or a repro that passes at HEAD kills the finding; so does a capture that passes at the base, since the bug was already there. The gate reads only which file passes, so anything but the assertion that differs between the two can fail the repro for another reason and confirm a bug that is not there.

## Recheck

Told it is a recheck: a fix has landed since the finding was confirmed, and its old capture and repro both fail now: they no longer reach the behaviour. Write both files the same way against the code as it is now, but do not require the capture to pass: on fixed code it fails at its assertion, and that is the answer. Both must reach their assertion. The gate then runs both and reads which one passes.

## Rules

- New files only, named with the finding id, where the repo's runner discovers them (scan Q6). Follow the repo's test conventions.
- Enter through the given entry point. Calling private internals to reach the condition proves nothing about real input.
- One behaviour, one assertion that can fail.
- Deterministic: no clock, network, randomness, file ordering or shared global state. Local only.
- The cmd runs under cmd.exe on Windows, sh elsewhere: quote `"{test}"`, write no `$VAR` (cmd.exe reads `%VAR%`), and prefer a command with no shell syntax.
- Run each file through `python3 <this skill's directory>/scripts/contain.py --shell "<cmd>"` (`python` where `python3` is absent): the gate's shell, and whatever it launched, a browser included, ends with it. No `--timeout`: a slow run cut short reads as a failure. A test that launches a browser runs it headless and closes it in a `finally`. The gate runs every file 11 times or more, and a promoted repro joins the suite every later run pays for: a browser only when the claim lives in a rendered page.
- Never touch existing tests, fixtures, config, the harness or the code under test.
- Once handed over, both files are frozen.

## Give up when

- the condition needs infrastructure that is not here: network, hardware, real concurrency, production data;
- you cannot isolate it without dragging in half the system;
- the capture will not pass and you cannot see why.

Giving up is correct and common. A repro that fails for the wrong reason is worse than none. List every file you created, so the caller removes them.
