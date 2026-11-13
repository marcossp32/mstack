---
name: m-scan
description: Investigates a repository before implementing something in it. Finds out the installed versions, the available libraries, how the repo does similar things, how it is tested and whether something already solves what is wanted, in whole or in part. Use before touching unfamiliar code, or when asked what the repo already has for a change.
---

# m-scan

## Goal

You are told what is to be implemented. Find out what the repo already has, so as not to reinvent it and to do it the repo's way. The main conversation will use what you find as fact, so each finding carries the path that proves it. What has no path is memory, and that is exactly what this skill replaces.

## Done when

- [ ] Each area below has an answer, or `Not found` with where you looked.
- [ ] Each finding carries `path:line`, or `path` if it refers to a whole file.
- [ ] What changes the plan goes at the very top, if there is any.
- [ ] The repo is left as it was: `git status --porcelain` gives the same before and after. Other agents may be working in it.

## Acceptance criteria

- **With proof.** Each claim carries its path. A gap is stated as `Not found`: a declared gap gets investigated, but an assumption gets taken as true and built on.
- **About the change, not the whole repo.** Report what matters for what is wanted, not an inventory.
- **What exists, not what is advisable.** Describe what exists. The main conversation decides.
- **To the point.** Another agent reads it: one line per finding, no introductions.

## Areas

1. **Versions.** Which version is installed of what the change touches. Look it up in the lockfile: the manifest gives a range and the lockfile, what is really there. If there is no lockfile, say so and give the range.
2. **Libraries.** Whether an installed library already does what is wanted, or part of it.
3. **Standards.** How the repo does similar things and what it calls them. If it does them in several ways, the most recently touched one is the current one. If two recent ways disagree, report both.
4. **Testing.** Framework, where tests go and how they are named, how fakes are made, and the command the repo declares to run them. Do not run them.
5. **Does it already exist?** Code that already solves the problem or a part of it. Also what could get in the way: an earlier attempt that was reverted or abandoned (`git log`), or tests that pin the behavior that is to be changed.

Search by meaning, not by name: the repo may call `Backoff` what the request calls `RetryPolicy`. If the code and the documentation disagree, the code wins, because it is what runs. Point out the difference.

## How to split it

Launch one subagent per area, in parallel and in a single message, so the repo is read at once and the main conversation receives only the conclusions. If the repo is small or the change is narrow, group areas into fewer agents. Give each one what is to be implemented and its area. They only read and search; you gather what they return and drop whatever arrives without a path.

## Result

First, one line for each finding that changes whether the change is made or how: it already exists, it exists in part, there was a reverted attempt, or the repo solves it another way. Then, one section per area. For example:

```
⚠ A retry with backoff already exists that covers half the case · src/http/retry.ts:18

## Versions
- axios 1.7.2 · package-lock.json:441

## Libraries
- p-retry 6.2.0 installed, unused · package-lock.json:1020

## Standards
- HTTP clients as a class with a wrapped `request()`, the most recent · src/orders/client.ts:12

## Testing
- Vitest, tests next to the code as `*.test.ts`, fakes with `vi.mock` · src/orders/client.test.ts:3
- Command: `npm test` · package.json:9

## Does it already exist?
- `withRetry()` with 3 calls · src/http/retry.ts:18
```
