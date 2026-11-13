---
name: principle-make-operations-idempotent
description: Designs scripts, commands, migrations, setup steps, jobs and handlers so running them twice, or again after a crash halfway, leaves the same correct result. Derives each step from the current state rather than from what a previous run meant to do. Use when writing setup, install, init, deploy or migration scripts, retryable jobs, webhook or queue handlers, or any state change that may be rerun, retried or interrupted.
---

# Make operations idempotent

An operation is idempotent when running it again changes nothing that the first successful run already did. For every operation that changes state, ask two questions: **what if this runs twice? what if the last run stopped halfway?**

## Why

Scripts get rerun, jobs get retried, deploys restart, handlers receive the same message twice. If a partial or repeated run changes the result (a duplicated line, a second row, a half-written file), every restart turns into manual cleanup and debugging.

## The idea

Read the current state, compare it with the goal, and apply only the difference. A step written this way is safe to repeat, because a repeat finds nothing left to do.

- **Create if missing**, instead of create and fail or create twice.
- **Ensure a line or a setting is present**, instead of appending it.
- **Upsert or use a unique key**, instead of a blind insert.
- **Write to a temporary file and rename it into place**, so a crash never leaves a half-written file.
- **Compare by content** or another fact the next run can check, not by what a previous run claimed.

## Two harder cases

- **Runs that overlap.** "Read, compare, apply" races when two runs happen at once. The check and the write must be one atomic step: a unique constraint, a conditional write, a lock that records its owner.
- **Effects you cannot simply read back** (an email, a payment, a call to another service). The goal is that, after any crash and rerun, each effect has happened exactly once: none lost and none doubled. Recording before the effect loses it if the run dies in between; recording after doubles it. Do not settle for one of those two failures. Close the gap: an idempotency key the receiver honours, a "pending" record that the next run resolves by checking whether the effect really happened (the outbox, the receiver's API, a log), or an effect that is harmless to repeat. Look for what the code and the receiver already offer. Only if nothing can close the gap, choose the less harmful failure and say so plainly.

## What good looks like

- Running the operation twice in a row gives the same end state as running it once, and the second run says there was nothing to do (or does nothing harmful).
- Interrupting it at any point and running it again ends correct.
- Anything a run leaves behind (a lock, a temp file, a claimed job) can be recognized as stale by the next run, wherever the previous one stopped.

## Traps

- **Testing only the clean first run.** Run it twice before calling it done.
- **"Already exists" as an error.** If the state already matches the goal, that is success.
- **Markers the next run cannot judge**, like a lock file with no owner or age. They turn every crash into a manual fix.
