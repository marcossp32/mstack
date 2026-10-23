---
name: m-build
description: "Builds one step or fix from its item into commits pinned by a test that fails without them, plus a notes file, held to what the item asks. Use when asked to build a step, fix findings or failures, or make a change with an observable Done when."
---

Builds one step, unattended: commits on the step branch that deliver what its item asks, pinned by a test that fails without them, and a notes file that a step check script and the caller read. How you design, test and check the work is yours; the result is judged, not the route. Nobody answers questions mid-run: where you would ask, build what was asked and say so in the notes, or return a stop line.

# Done when

Either the step branch holds your commits, no tracked file is left modified, the notes file exists at the path under Notes with every section filled, and your final message is that path; or your final message is the one line `Stop · <unobservable Done when | contradiction | missing decision> · <what>` and no notes file was written.

# Acceptance criteria

- [ ] The step branch has at least one commit beyond the branch it was cut from, and `git status` shows no modified tracked file.
- [ ] The notes file opens with one sentence, then has the sections `What changed`, `Tests changed`, `Pinned by`, `Disputed`, `What to watch`, in that order, none empty.
- [ ] Every test file Pinned by names passes at HEAD and fails with the step's non-test changes reverted, or the section reads `none · <why nothing can>`.
- [ ] Every existing test file or snapshot the branch changes or deletes, and every file where it adds a skip, focus, suppression or runner exclusion, is listed in Tests changed with the item clause that asks for it.
- [ ] No added line holds a credential: each is read from an environment variable named in What to watch.
- [ ] `python3 <this skill's directory>/scripts/contain.py sweep --kill --within <checkout>`, run after the final message, prints `REAP: ended 0` and no `orphan` line.
- [ ] No branch was pushed and no pull request was opened.
- [ ] Fix mode: every finding or failure the item lists is addressed by a commit or listed under Disputed with the code or output that shows it.

# Inputs

- The step item, under the headings `What to do`, `What you need to know`, `Done when`.
- Not doing: what the work excludes on purpose, given or where to read it.
- When given: facts about the repo (what exists, which installed library already does it, how the repo does and names similar things, how it tests and runs, per-environment values, infrastructure limits) and docs answers, each quoted and linked. Docs answers are facts the repo cannot tell you; use them where the code calls out. What was not given, read from the repo.
- The step branch you are on and the branch it was cut from. With no step branch given, work on the branch checked out, unless it is the base or default branch: then cut a new branch from it, because nothing reaches the base except through review.

# What the result must be

**What was asked, at its scope.** Deliver what the item asks as it intends it, and make routine calls yourself. Anything the item does not ask for, a better approach, or a request that looks mistaken goes as one line in What to watch, and you build what was asked: unrequested work is unreviewed scope, and Not doing is excluded on purpose.

**Pinned.** A green suite says nothing the old suite did not; the behaviour is pinned only by a test that fails without the step. The step check runs each Pinned by test at your HEAD (it must pass) and with your non-test changes reverted (it must fail); one that passes either way pins nothing and fails the step. A test is worth its assertion: assert the value the Done when names through the entry point a caller uses, and fake only what leaves the process, since a test that fakes the code under test passes whatever that code does. Where no test can reach the change (wiring only the running app shows), write `none · <why>`, and the running app judges it alone. A step that changes only manifests and lockfiles is not judged by the revert, since reverting leaves what was installed.

**Existing tests are evidence.** A test that fails after your change is telling you something about the change. Change or delete one only where the item changes the behaviour it pins. A test that disagrees with the spec is a stop line, because the spec, the tests and the Done when are what judge you: keep each as it is and make the code meet it.

**Every loosened check declared.** Anything that makes an existing check accept more is loosening it: a changed or deleted test file or snapshot (an updated snapshot changes what its test accepts), or an added skip, focus, suppression or runner exclusion. The step check fails on any it finds unlisted in Tests changed, so list each with the item clause that asks for it.

**Credentials in the environment.** A credential is read from an environment variable, named in What to watch, because a literal in a commit is published with the branch. The step check fails on a credential-like literal in the added lines, a password in a URL to another host, or a committed `.env`; a value that says it is not real is only noted.

**Nothing you start outlives you.** Test workers, servers and the browsers they launch otherwise survive the run and pile up under later ones until the machine crawls. This repo's way is `python3 <this skill's directory>/scripts/contain.py -- <command>` (`--env KEY=VALUE`, `--shell "<line>"` for pipes; run it with no arguments for the rest). Stop everything before you finish. Where contain will not start, run nothing uncontained and say so in What to watch.

**What only you can see.** No local check exercises behaviour that appears only off this machine or on a rare path, so it rests on you: bound every call out of the process with a timeout (the documented value where a docs answer gives one), release what an error path holds, and read per-environment values from the environment.

## Known traps

- `contain.py --timeout` cuts a slow run that was fine, and the cut reads as a failure.
- A foreground wait (`sleep`, an `until` loop) holds the turn until the shell tool's time limit; run long commands in the background, where the harness reports their exit.
- A server started outside contain (`&`, `Start-Process`) escapes containment; start it contained in the background and stop it with `contain.py stop <pid>`, the pid contain prints.

# Stop instead

Return one stop line and no notes file as soon as you see one of these, before building toward it:

- the Done when cannot be observed: say what cannot be seen and a criterion that could;
- the spec contradicts itself, the repo or an existing test: quote both sides;
- a decision nobody has made blocks the work: name it.

A stop line is a finished answer: someone other than you settles it.

# Who else judges it

You never judge your own work; agents that did not write it do, against these bars:

- **Quality review**, static: a finding counts only with a source (the repo's rule files, or a verbatim quote from the official docs for the installed version) and the `file:line` that breaks it. Follow the repo's rules and the docs answers you were given.
- **Prove**: agents drive the running app against the Done when and the requirements it serves.

# Fix mode

The item's What to do lists what failed: quality findings (source and `file:line`), prove failures (the Done when or requirement, the value seen, evidence), or step-check output. Done means each is resolved at its root, not at the line named: the code satisfies the finding's source, the observation holds in the running app (pinned by a test that fails without the fix where a test can reach it), or the check passes. A missed Tests changed or Pinned by entry is fixed in the notes. A finding or failure you believe is wrong goes under Disputed with the code or output that shows it, and that code stays as it is, since someone other than you settles the dispute. Everything above still holds.

# Notes

Commit on the step branch. Push nothing and open no pull request: what happens to the branch is decided after the judges, by whoever dispatched you. Write the notes, overwriting any earlier file, to

```
<git common dir>/mstack/steps/<step branch with / replaced by ->.md
```

where the git common dir is `git rev-parse --path-format=absolute --git-common-dir`. It lives outside the checkout, so it is never committed. The step check reads `Tests changed` and `Pinned by` by their `## ` headings (test paths only; a `::` test id names its file, and a Pinned by section that opens with `none` is read as the reason nothing pins), so keep the headings exactly as below:

```markdown
<what a user can now do, one sentence>

## What changed
- <one bullet per behaviour, most important first>

## Tests changed
- <file · what changed · the item clause that asks for it>, or "none"

## Pinned by
- <test file that fails without this change · the Done when clause it pins>, or "none · <why nothing can>"

## Disputed
- <finding or failure id · why it is wrong · the code or output that shows it>, or "none"

## What to watch
- <risk, assumption, out-of-scope request, environment variable read, anything the Done when does not cover>, or "none"
```

Your final message is the notes file's absolute path, nothing else.
