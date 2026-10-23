---
name: m-scan
description: "Scans a repository for what its code can settle about a change: installed versions, existing code, conventions, testing, how it runs, per-environment config, infrastructure limits. Use before changing an unfamiliar codebase."
---

Answers, from the repository alone, what a builder, a reviewer and a prover need settled before code is written: installed versions, what already exists, how the repo does and names things, how it tests and runs, per-environment values and infrastructure limits. Every question the repo settles is one nobody has to look up in docs or decide by argument.

# Done when

A report is returned with one line per owned question (all nine when the request names none), each answer carrying a repo path or `Not found` with where it looked, and above them a line for each finding that changes whether or how the change should be made.

# Acceptance criteria

- [ ] Every owned question has exactly one line in the report shape; none is missing or merged with another.
- [ ] Every answer names a path (`file:line` where it points at code); every gap says `Not found` and where it looked.
- [ ] Q1 versions come from a lockfile, or the line says there is none and gives the manifest range.
- [ ] Q6 gives the whole-suite command and the single-file command with `"{test}"`, each written so both cmd.exe and `sh` run it.
- [ ] The checkout is unchanged: `git status --porcelain` prints the same before and after.

# The bar

- **From the repo, with a path.** The repo's files and git history are the whole input, read without changing anything: the checkout ends as found. An answer without a path is memory, and memory about this repo is what the scan replaces.
- **A gap is `Not found`.** A stated gap gets researched or decided; a guess gets built on.
- **Current practice over stale.** Where the repo does something several ways, the most recently changed way is the one to follow; two recent ways that disagree are both reported.
- **Code over docs.** Code and CI config are what runs; where a README disagrees, report the disagreement.
- **Report what exists, not what to choose**: the reader decides with all of it.

The repo may name things differently from the request (`Backoff` where the request says `RetryPolicy`), so search by meaning, not by the request's words.

# Questions

When the request names a slice, answer only its questions: A = 1 · B = 2–5 · C = 6, 9 · D = 7, 8. Otherwise answer all nine. These numbers and slices are a convention: callers dispatch by them and cite answers as `Q<n>`, so they stay as written.

1. **Installed version**, from the lockfile, not the manifest: the manifest gives a range, the lockfile what is installed. Where several lockfiles exist, the one that governs the code the change touches. No lockfile: say so and give the manifest range.
2. Does this already exist in the repo? Also what would trip it: an earlier attempt reverted or abandoned, and tests that pin the behaviour the request changes.
3. Does an installed library already do it?
4. How does the repo do similar things?
5. What does the repo call these things?
6. How does it test: framework, test file location and naming, assertion style, how fakes are set up; the exact command that runs the whole suite and the one that runs a single test file, with `"{test}"` where the file path goes; whether test files launch a browser or a server; and the runner's flag for how many files run at once (e.g. `--maxWorkers` for Jest). A script runs both commands through cmd.exe on Windows and `sh` elsewhere, so write them in what both accept: double quotes only, no `$VAR`. Test files that each launch a browser or a server collide when many run at once, and the flag is how a caller caps them.
7. Which values differ between local and production, and which do not?
8. Infrastructure limits: what the platform the app runs on caps (run time, memory, disk, outbound network), from the config that names that platform.
9. How the app runs (start command, URL or entry point, prerequisites such as a seeded DB, env file or services); the path of a launch recipe in the repo (a `SKILL.md` under `.claude/skills/` or `.agents/skills/` whose name or description says it launches the app); how a fresh checkout gets its dependencies; and whether PRs land squashed or merged on the default branch.

# Report

One line per owned question in the shape `- Q<n> <title> — <answer> · <path>`, which callers parse. Illustrative:

```
- Q1 Installed version — `axios 1.7.2` · package-lock.json:441
- Q2 Already exists — retry logic with 3 callers · src/http/retry.ts:18
- Q4 How they do it — newest example, changed 3 weeks ago · src/orders/client.ts
- Q7 Per-environment values — Not found · searched config/, .env.example, deploy/
```

Above the lines, one line for each finding that changes whether or how the change should be made at all; the common ones are that it already exists, an earlier attempt was reverted, the request breaks the repo's pattern, or the infrastructure does not allow it.
