---
name: m-build
description: "Builds one step from its issue into one pull request, scope held to what was asked. Use as the build stage of /m-feature, for a fix step from /m-review, or for any change with an observable Done when."
---

Build one step. The method is yours: how you design it, how you test it, how you check your work. One result is not: a test that fails without your change pins what the step delivers. Your final message is the PR number, or the stop line; the PR says what changed, not how you got there.

# Inputs

- The step issue: what to do, what you need to know, Done when.
- Not doing, from the map issue you are given: hold your scope against it.
- From `/m-scan`: what already exists, which installed library already does it, how the repo does similar things, what it calls them, how it tests, per-environment values, infrastructure limits, how it runs.
- Vendor limits and timeouts (`/m-research`), or "not applicable". These are facts you cannot infer from the repo: use them where the code calls out.
- The run recipe (launch, health check, teardown, traps), or how the app runs from scan Q9: for Driven.

# Scope

Deliver what the issue asks, at the scope it intends, and make routine calls yourself. Anything beyond that scope (a feature, an option, a refactor, cleanup), a better approach, or a request that looks mistaken: one line in the PR, and build what was asked.

# Stop instead

No PR, one line, when:

- the Done when cannot be observed: say what cannot be seen and a criterion that could;
- the spec contradicts itself, the repo, or an existing test: quote both sides;
- a decision nobody has made blocks the work: name it.

Stopping is a finished answer. Never bend a test, the spec or the Done when to get past it.

# Existing tests

A test that fails after your change is information about the change. Change or delete one only when the issue changes the behaviour it pins, and list it in the PR with the clause that changed it. A test that disagrees with the spec is a stop, not an edit.

Tests changed lists every existing test file with M or D in `git diff --name-status --no-renames origin/<feature branch>...HEAD` (snapshots included: an updated snapshot changes what its test accepts), and every file where you add a skip, a focus (`.only`), a suppression (`@ts-ignore`, `eslint-disable`, `# noqa`, `|| true`) or an exclusion (`--deselect`, `--ignore`, `-k "not …"`, `collect_ignore`, `testPathIgnorePatterns`, `exclude` in a test runner's config): each one stops a check from checking, so each needs the clause that asks for it. The step check fails on any it misses.

# Pinned

A green suite says nothing the old suite did not: the step's behaviour is pinned only by a test that fails without the step. Pinned by lists those test files; the check reads only test paths from it (a `::` test id names its file), so the clause may name code. The step check runs each one at your HEAD, where it must exit 0, then with your non-test changes reverted, where it must fail. A test that passes either way pins nothing, and fails the step.

A test's worth is its assertion: assert the value the Done when names, through the entry point a caller uses. A fake stands in only for what leaves the process (network, clock, another service); a test whose fakes stand in for the code under test passes whatever that code does.

Nothing a test can pin (config, a build file, wiring only the running app shows): `none · <why>` in Pinned by. Prove then judges it alone. A step that changes only manifests and lockfiles (a dependency bump) is not judged by the revert, since reverting them leaves what they installed: the check notes it, and prove judges it.

# Driven

Prove drives the running app only after every step, so a step wrong in the app costs a whole round: a fix build, a review and a re-prove, an hour or more. Before the PR, drive your own Done when once where a user reaches it, when the app can be launched (the recipe, else scan Q9) and the Done when has a surface it reaches (a page, an endpoint, a command): launch it, check what the Done when names, and on a page look past it too (console errors, the layout at the recipe's viewport; `agent-browser` where it is installed, else fetch the page), then stop everything you started. Launch contained (Contained, below); a browser runs headless, never hides its automation from the page, and a login or bot check you were not given a way through ends the drive there, named in Driven. Ten minutes at most; what you find wrong, fix before the PR. Wait as the recipe says, never a fixed sleep.

This is your own look, not a verdict: prove still judges with agents that did not write the code. Nothing that launches, or nothing a drive reaches: `none · <why>` in Driven.

# How this is judged

Nothing else checks your work:

- **Step check** (a script, after you push, on a clean checkout): the suite is no worse than when the feature started; every existing test file you changed or deleted, and every skip, focus or suppression you added, is listed in the PR; each Pinned by file fails without your change; no credentials in the added lines.
- **Feature review** (once all steps are in): only failures demonstrated by running code count.
- **Prove**: fresh agents drive the running app against the feature's Goal.

What none of these can show locally rests on you alone: a timeout on every call out of the process (with `/m-research`'s value), resources released on rare error paths, per-environment values read from the environment.

# Contained

Every command that starts processes (the suite, a test file, a server, a script that launches a browser) runs through `python3 <this skill's directory>/scripts/contain.py -- <command>` (`python` where `python3` is absent; `--env KEY=VALUE` for variables; `--shell "<command line>"` only for pipes and `&&`, cmd.exe on Windows). When it exits or is stopped, everything it started ends too: a suite's workers and their browsers otherwise outlive a stop, and pile up under the next run until the machine crawls. A server: start it contained with `run_in_background`, never `&` or `Start-Process`, and stop it by the pid its first stderr line prints. The next step check ends whatever you leave running. contain will not start: say so in Driven and run nothing uncontained. `agent-browser` commands are not wrapped: each session's daemon owns its browser. Pass no `--timeout`: it cuts a slow run that was fine, and the cut reads as a failure.

# Long commands

A command that runs for minutes (a suite, a build, a render): start it contained with the Bash tool's `run_in_background` and do nothing else on it; the harness tells you when it exits. Waiting on something else to happen (a file, a port): the Monitor tool, loaded first with ToolSearch (`select:Monitor`). These two are how you wait: a `sleep` or `until` loop in Bash holds the turn, hits the tool's 10-minute limit and starts over.

# Fix mode

The issue lists confirmed findings from `/m-review`: each a claim and the condition that shows it. Each one failed a frozen reproduction on your branch's code. Fix the code until the condition no longer holds, working from the claim and condition alone: the review re-runs its own frozen reproduction afterwards. A finding you believe is wrong: say why in the PR, with the code that shows it, and leave that code as is. The review's reproductions pin the fix once they pass, and become its regression tests: Pinned by says `none · pinned by the review's reproductions` unless you add a test of your own. Tests you write to check a listed finding stay out of the commit (keep them in your scratchpad): committed, they would test the same condition twice and slow every later suite run. Commit a test of your own only for behaviour no listed finding covers, and list it under Pinned by.

# Pull request

You are on the step branch. Target the feature branch.

```markdown
<what a user can now do, one sentence>

## What changed
- <one bullet per behaviour, most important first>

## Tests changed
- <existing test file, or file with a skip, focus, suppression or exclusion added · what changed · the issue clause that asks for it>, or "none"

## Driven
- <what you drove, where → what you saw>, or "none · <why>"

## Pinned by
- <test file that fails without this change · the Done when clause it pins>, or "none · <why nothing can>"

## What to watch
- <risk, assumption, anything the Done when does not cover>

Part of #<n>
```

`Part of`, never `Closes`: closing keywords are ignored on non-default branches.
