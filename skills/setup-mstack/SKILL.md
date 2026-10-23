---
name: setup-mstack
description: "Sets up mstack in a repository: writes .mstack.yml (the tracker that holds specs and state, the host that opens the pull request), checks each tool is installed and logged in, and checks Claude Code's auto mode allows unattended runs. Use when asked to set up mstack in a repository or to re-check its setup."
disable-model-invocation: true
---

Prepares a repository for unattended mstack runs, for the human who runs it once per repo and again after fixing what it reported. It produces `.mstack.yml` at the repository root, naming the tracker (where specs are read, state lives and issues open) and the host (where the pull request opens), and a report saying whether each tool and Claude Code's auto mode will let a run nobody watches finish. An unattended run asks nobody anything and stops when its tools fail, so whatever it would need a person for is settled here, while one is present; this is why setup is the one mstack skill that asks the human questions.

# Done when

The report gives every check's result, each failure with the command or edit that fixes it, and the auto mode block when an entry is missing; and either `.mstack.yml` holds a valid tracker and host (written, or left as it was when nothing changed), or the report names the value that stayed unsettled and nothing was written.

# Acceptance criteria

- [ ] `.mstack.yml` has the shape under The file: the header line, `tracker` and `host`, a nested `jira:` → `project:` only when tracker is `jira` and a project key is known, a nested `md:` → `dir:` only when tracker is `md` and the directory is not `.mstack/`.
- [ ] `tracker` names a file `../m-feature/references/trackers/<tracker>.md` and `host` a file `../m-feature/references/hosts/<host>.md`.
- [ ] `.mstack.yml` contains no token, password, key, URL with credentials or run command; when git ignores it, the report lists it as a FAIL with the ignoring rule and its fix (un-ignore it so the team's runs share it).
- [ ] `.mstack.yml` is the only file created or changed: `~/.claude/settings.json`, `.claude/settings*.json`, the git history and the tracker and host are as they were.
- [ ] The report has one result per check (tracker, host, each line of `check_auto_mode.py`), and every failure names the command or edit that fixes it.
- [ ] No credential was asked for, printed or stored.
- [ ] The human was asked only what the repository and their arguments could not settle, at most the tracker and the host, each question with a recommended answer and why.

# Boundaries

Setup reads and reports; the human makes every change outside `.mstack.yml`, because each one is theirs to see and own.

- **Credentials stay with their tools.** Each tool has its own login, and setup only checks that it works; it never asks for, prints or stores a credential. Where an adapter reads a token from an environment variable, name the variable, never its value. The app credentials a prove run uses live in `MSTACK_SECRET_<NAME>` environment variables the human sets, never in this file.
- **The human adds the auto mode block.** Setup prints it and where it goes, and runs nothing that writes a settings file (`claude auto-mode reset` among them): a run granting itself permissions is what the classifier exists to stop, and the human must see what they allow. mstack never edits `~/.claude/settings.json`.
- **Git and logins are the human's.** Setup changes no git state and starts no interactive login; it names the commit and the tool's own login command for the human to run.
- **The tracker and host are only checked.** Run each adapter's `check` operation and nothing else: creating, editing or commenting there belongs to a run.
- **No run commands in the file**: `/m-scan` and the run recipe own how the app runs.

# The file

`.mstack.yml` sits at the top of the git work tree and is committed, so the whole team's runs read the same values. m-feature parses it; keep its shape:

```yaml
# mstack: where work lives. See setup-mstack.
tracker: gh      # gh | jira | md   — where specs are read, state lives, issues open
host: gh         # gh | gitlab | bitbucket — where the pull request opens
```

With `tracker: jira` and a known project key, add it; with `tracker: md` and a directory other than the default `.mstack/`, add that (one or the other, matching the tracker):

```yaml
jira:
  project: ABC
md:
  dir: docs/mstack/
```

A value is valid when an adapter file of that name exists: `../m-feature/references/trackers/<value>.md` for `tracker`, `../m-feature/references/hosts/<value>.md` for `host`. The comments list the values actually found there. Adding a tool is adding a file there; without those directories nothing validates, since mstack's skills are installed together.

A re-run keeps every valid value unless the human's arguments name another, drops any other key or anything that looks like a credential and says so, and rewrites the file only when its content changes, so a committed file that did not change stays clean.

# Settling the values

Deduce before asking. The `origin` remote usually names the host. The human's arguments usually name the tracker: a tool name, or a spec reference (`#123` or a GitHub issue URL → `gh`, `ABC-123` or an Atlassian URL → `jira` with that project, a path to a `.md` file → `md`). Ask only what is still open, recommending an answer with its reason (code on GitHub suggests `gh` for both; with no tracker that has an adapter, `md` needs no account). An answer of `jira` may carry the project key; without one the file has no `jira:` key, a run takes the key from the spec reference, and the report says the project check was skipped.

An answer with no adapter file: say so, say that adding a tool is adding a file, and ask once more. Still invalid, or outside a git repository: report what stayed unsettled and write nothing.

# Checking it works

- **Tracker and host:** run the commands under each adapter's `check` heading as written; they establish that the tool is installed at the version the adapter needs and authenticated. A failure is reported with the fix the adapter names (the install, or the tool's own login command). An adapter with no `check` is itself a failure, fixed in that file. When the tracker and host are the same tool, one check covers both.
- **Auto mode:** run `python3 scripts/check_auto_mode.py` from this skill's directory (`python` where `python3` is absent). It is read-only and prints `PASS · <check>` or `FAIL · <check> · <why> · fix: <what to do>` per check, a `NOTE ·` line when it could read only the settings file, and, when an `autoMode` entry fails, the block to add and where; it exits 1 on any FAIL. Pass its output through unchanged. Read [`references/auto-mode.md`](references/auto-mode.md) before explaining a line to the human, or when the script aborts.

# Report

What the human needs to act on: each check's result and, for each failure, its fix; the auto mode block and where it goes, only when the script printed it; and, unless `.mstack.yml` was already committed and unchanged, the commit that shares it with the team (e.g. `git add .mstack.yml && git commit -m "Add mstack config"`). After any failure, the last line tells them to run `/setup-mstack` again once it is fixed.
