---
name: m-scan
description: "Scans a repository for what its code can settle about a change: installed versions, existing code, conventions, testing, how it runs, per-environment config, infrastructure limits. Use before changing an unfamiliar codebase."
---

# m-scan

Settles from the repository what a builder, a reviewer and a prover would otherwise look up in docs or decide by argument, before code is written. Each answer is acted on as fact, so it carries the path that shows it.

# Done when

The reply is the report: every owned question has exactly one line in the shape under [Report](#report), none missing or merged with another, each answer with a path (`file:line` where it points at code) or `Not found` with where it looked, and above them a line for each finding that changes whether or how the change should be made. The checkout is as found: `git status --porcelain` prints the same before and after, since other agents work on this machine.

# How to answer

- **From the repo, with a path.** The repo's files and git history are the whole input; run something where it settles an answer. An answer without a path is memory, which is what the scan replaces.
- **A gap is `Not found`.** A stated gap gets researched or decided; a guess gets built on.
- **By meaning.** The repo may name things differently from the request (`Backoff` where the request says `RetryPolicy`).
- **Current practice over stale.** Where the repo does something several ways, the most recently changed way is the one to follow; two recent ways that disagree are both reported.
- **Code over docs.** Code and CI config are what runs; where a README disagrees, report the disagreement.
- **What exists, not what to choose**: the reader decides with all of it.

# Questions

A request naming a question group answers only its questions: A = 1 · B = 2–5 · C = 6, 9 · D = 7, 8. Otherwise answer all nine. Callers dispatch by these letters and cite answers as `Q<n>`, so they stay as written.

1. **Installed version**, from the lockfile, not the manifest: the manifest gives a range, the lockfile what is installed. Where several lockfiles exist, the one that governs the code the change touches. No lockfile: say so and give the manifest range.
2. Does this already exist in the repo? Also what would trip it: an earlier attempt reverted or abandoned, and tests that pin the behaviour the request changes.
3. Does an installed library already do it?
4. How does the repo do similar things?
5. What does the repo call these things?
6. How does it test: framework, test file location and naming, assertion style, how fakes are set up; whether test files launch a browser or a server, and the runner's flag for how many files run at once (e.g. `--maxWorkers` for Jest), since such files collide when many run at once and the flag is how a caller caps them. Then the two commands a script runs unattended from the repo root, through cmd.exe on Windows and `sh` elsewhere: the whole suite, and one test file with `"{test}"` where its path goes.
   - **Environment apart.** What the tests need set (a variable, e.g. a path to dependencies a fresh worktree lacks) is reported as `env NAME=<value or where it comes from>`, never inside a command: an inline assignment works in one shell only, and the caller sets it on every run and every agent that runs tests. A secret by name only.
   - **Tried, not guessed.** The caller records the baseline every step is judged against from these commands; a wrong one costs it a useless baseline and a long hand debug. Run them as the script will (through cmd.exe on Windows, whatever shell you are in): the one-file command on a real test file, and the suite command only far enough to show it finds the test files (the runner's list or dry-run mode, or stopped once files run), since a full suite can take many minutes. Say what each trial showed; one you could not run is `untried · <why>`. A trial that fails before any test runs names what the tests lack, which is part of the answer.
7. Which values differ between local and production, and which do not?
8. Infrastructure limits: what the platform the app runs on caps (run time, memory, disk, outbound network), from the config that names that platform.
9. How the app runs (start command, URL or entry point, prerequisites such as a seeded DB, env file or services); the path of a launch recipe in the repo (a `SKILL.md` under `.claude/skills/` or `.agents/skills/` whose name or description says it launches the app); how a fresh checkout gets its dependencies; and whether PRs land squashed or merged on the default branch.

# Report

One line per owned question in the shape `- Q<n> <title> — <answer> · <path>`, which callers parse. Illustrative:

```
- Q1 Installed version — `axios 1.7.2` · package-lock.json:441
- Q2 Already exists — retry logic with 3 callers · src/http/retry.ts:18
- Q4 How they do it — newest example, changed 3 weeks ago · src/orders/client.ts
- Q6 How it tests — suite `make test` (tried: listed 212 files) · one file `make test FILE="{test}"` (tried: tests/cart_test.x passed) · env `DEPS_PATH=<main checkout>/deps` (worktree has none) · Makefile:12
- Q7 Per-environment values — Not found · searched config/, .env.example, deploy/
```

Above the lines, one line for each finding that changes whether or how the change should be made at all, such as that it already exists, an earlier attempt was reverted, the request breaks the repo's pattern, or the infrastructure does not allow it.
