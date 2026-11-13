---
name: principle-attack-the-premise
description: Stops repeating fixes that keep failing. When two or more attempts that share one premise about the cause have failed the same check, writes that premise down and tests it directly before trying another fix. Use when a fix did not work and the next idea is a variation of it, when a bug keeps coming back, when the history shows earlier failed fixes, or when tempted to raise a timeout, add a retry or bump a limit one more time.
---

# Attack the premise

Every fix assumes something about the cause: "it is too slow", "the cache is stale", "the input is malformed". When two fixes built on the same premise fail, the evidence points at the premise, not at the fixes.

## Why

Each failed fix is evidence against the premise behind it. A third fix on that premise spends effort exactly where the evidence says the cause is not. Variations of a wrong premise can go on forever.

## How it looks

- **Name the premise.** One sentence that every failed attempt took for granted. Earlier attempts in the git history or the conversation count.
- **Test it, not around it.** Find an observation that would come out differently if the premise were false, and make it. Look at the shape of the failures, not only their size: which cases fail, when, in what order, on which machine.
- **Follow what you saw.** If the premise is false, the cause is elsewhere: look for what the failures have in common that the premise did not predict. If it holds, ask why once more, because the earlier fixes probably treated a consequence (see `principle-fix-root-causes`).
- **Remove the condition rather than compensating for it.** Bigger timeouts, more retries and higher limits compensate. Removing the shared state, the race or the wrong input removes it.

## What good looks like

- The premise is written down, with the observation that confirmed or refuted it.
- The next fix rests on that observation, not on the old premise.
- A failure that was intermittent now passes many runs in a row, in any order. One green run proves little.

## Traps

- **Treating "it passed once" as fixed.** Intermittent failures pass by chance. Repeat the check enough times to tell.
- **Changing two things at once.** Then you cannot tell which one mattered, and the premise stays untested.
