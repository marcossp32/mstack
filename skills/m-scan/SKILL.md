---
name: m-scan
description: "Reads a repository to answer what its code can settle about a feature: installed versions, existing code, conventions, testing, how it runs, per-environment config, infrastructure limits. Use as the scan stage of /m-feature, or before changing an unfamiliar codebase."
---

Answer questions about a feature by reading this repository. You run before anyone asks the human; every question you answer is one `/m-grilling` does not ask and `/m-research` does not look up.

- No network.
- Read only: no edits, new files or commits. Return the report; `/m-feature` posts it.
- Report what exists; choosing is someone else's job.
- Everything you write follows [`references/writing.md`](references/writing.md).

# Questions

1. **Installed version**, from the lockfile (`package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `poetry.lock`, `Pipfile.lock`, `go.sum`, `Cargo.lock`, `composer.lock`, `Gemfile.lock`), not the manifest. No lockfile: say so and give the manifest range.
2. Does this already exist in the repo?
3. Does an installed library already do it?
4. How does the repo do similar things?
5. What does the repo call these things?
6. How does it test: framework, test file location and naming, assertion style, how fakes are set up.
7. Which values differ between local and production, and which do not?
8. Infrastructure limits: disk, outbound network, max run time, memory.
9. How the app runs (start command, URL or entry point, prerequisites: seeded DB, env file, services) and whether PRs land squashed or merged, read from `git log` on the default branch.

Dispatched: answer only your slice — A = 1 · B = 2–5 · C = 6, 9 · D = 7, 8. Alone: all nine, Q1 first.

# Searching

- Search by meaning: business terms, the library that would do it, error strings, log messages, test names. The repo may call it `Backoff` where you would say `RetryPolicy`.
- Find several similar examples and check `git log` on each; the most recently changed is the current way. Two recent ones disagree: report both.
- Code and CI config win over READMEs; report the disagreement.
- Where to look:
  - Config: `.env.example`, `config/`, `docker-compose*.yml`, Helm values, CI workflows.
  - Limits: `Dockerfile`, Kubernetes `resources.limits`, `serverless.yml`, Terraform, CI runner settings.
  - Similar work: the tests of the closest existing feature.
  - Tests: test directory, runner config, newest test file.
  - Running: `.claude/skills/run-*/` recipes, `package.json` scripts, `Makefile`, compose files, README quickstart, the CI job that boots the app.
- Stop each question once answered.

# Report

One line per owned question, every one, with a path, or "Not found". Never fill a gap from memory.

```
- Q1 Installed version — `axios 1.7.2` · package-lock.json:441
- Q2 Already exists — retry logic in `src/http/retry.ts:18`, 3 callers
- Q4 How they do it — newest example `src/orders/client.ts`, changed 3 weeks ago
- Q7 Not found — nothing sets timeouts per environment
```

At the top, when found: it already exists · the plan breaks the repo's pattern · the infrastructure does not allow it.
