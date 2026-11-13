---
name: principle-prove-it-works
description: Checks that a change works by observing the real thing (running the actual command, app, endpoint or script and reading what it returns) before saying it is done, instead of trusting proxies like "the tests pass", "it compiles", a log line or an agent's own report. Use before declaring any task done, fixed or working, before writing a summary of a change, and when reviewing whether someone else's change really works.
---

# Prove it works

Before you say something works, watch it work. Run the real entry point the user would use and read the real output.

## Why

Proxies feel cheaper than looking: the tests pass, the build is green, the file changed, a subagent says it is done. But a proxy can be green while the thing is broken. The tests may not cover the path, the CLI may call old code, the config may not load, the server may serve a cached page. Saying "done" on a wrong inference costs far more than one more command.

## What counts as proof

- **The real path.** The command, page, endpoint or job a user would actually run, with realistic input. Not only the function you changed.
- **The real value.** Read the output, the file, the row or the response itself, not a derived sign that it probably changed.
- **Before and after.** For a bug, see it fail first, then see it pass. A check that never failed may not be checking anything.
- **What the change can affect.** Also run what already worked and touches the same code.

The strongest proof is a check someone else can rerun (a command, a short script, a test of the real entry point) with its output saved or quoted.

## What good looks like

- Your final message says what you ran and what it returned, so the reader can trust it without redoing it.
- If something could not be checked (no credentials, no browser, no service), you say so plainly instead of implying it works.

## Traps

- **Unit tests green, feature broken.** Wiring, entry points, config and registration are where changes often fail, and unit tests rarely see them.
- **Believing a report.** A subagent's "done" or a log saying "success" is a claim. Check the artifact it claims to have produced.
- **A failure you did not expect.** Confirm you observed the right process, port, file or version before blaming the system or the check. Never dismiss a failure without that evidence.
- **Proving with real effects.** Do not trigger irreversible or paid effects (production data, real emails, real charges) to prove something. Use a safe environment or input, and say what you could not run.
