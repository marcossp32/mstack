---
name: m-pr
description: Opens or updates the pull request (merge request) of a branch on GitHub, GitLab, Bitbucket or Azure DevOps, with a short, clear description of what changes and why, and the screenshots, videos or command output that show it working. Use when asked to open, create, update or publish a PR or MR, or to deliver a finished branch for review.
---

# m-pr

## Goal

You are given a branch with finished work. Open its pull request, or update it if it already exists, so that a reviewer who never saw the work understands in a minute what changes, why, and whether it was seen working, without reading the code or running anything.

A pull request is read twice: today by whoever reviews it, and in a year by whoever finds it in the history looking for why the code is the way it is. The diff already says *what lines* changed. The description says what the diff cannot: what changes for the user, why it was done this way, how we know it works and what could go wrong.

## What you receive

All optional. What does not arrive, deduce it from the branch, its commits and the repo. If the branch has no commits against the base, there is nothing to open: say so and stop. Uncommitted changes are not part of the pull request: say they were left out.

- **The branch and the base.** By default, the current branch against the host's default branch.
- **What was asked.** A spec, an issue or a sentence. It gives the *why*.
- **The proof.** A report from whoever tested the change in the running app (for example m-prove's `VERDICT`, its `✓`/`F`/`?` lines, `Media · <paths>` and `Evidence · <folder>`). It gives the evidence.
- **Notes.** Decisions taken without a person and their reason, what was left out, issues found, issues the change closes.
- **Ready for review or not.** Whether whoever calls you considers the work finished. If nobody says, it is, unless the proof shows failures.

## Done when

- [ ] One open pull request from the branch into the base, never two. If it already existed, it was updated, not duplicated.
- [ ] Its title and description meet the criteria below.
- [ ] Each image and video in the description is hosted on the host: no local path is left, because nobody else can open it.
- [ ] It is a draft unless the work is ready for review and its CI is not red.
- [ ] You end with the result line (see [Result](#result)).

## Acceptance criteria

**The title**
- Says what changes, in one short line that stands alone in a one-line log: `Add CSV export to the orders list`, not `Fix bug`, `Phase 1` or the branch name.
- Follows the repo's convention: the recent commit subjects on the base show it (Conventional Commits, a ticket prefix, imperative mood).

**The description**
- **Starts with the essential:** in one or two sentences, what a user can now do or what is fixed, and whether it was seen working. Someone who reads only that knows what the PR is.
- **Says why:** the problem, and why this approach if there was a reasonable alternative. Context goes in the description itself, because links break and tickets get closed.
- **Shows it working.** For each thing asked, the evidence that shows it: a screenshot, before and after side by side, a short video of the flow, or the command and the lines of its output that matter. A reviewer should not have to pull the branch to believe it.
- **Says how to try it:** how to start it and what to do to see each change, credentials by variable name only.
- **Says what to watch:** risk, what is hard to undo (a migration, a stored format, a new env var) and how to roll back when a revert is not enough.
- **Says what is not done:** each thing that was not proved or does not work, decisions taken without a person and their reason, issues found that are not this change's.
- **Is brief.** Behaviour, not a list of files. The detail that only some readers want (long outputs, decision records) goes inside `<details>`. If a section has nothing to say, it is left out.
- **Is honest.** It claims only what the evidence shows. "Not verified" is said as plainly as "works".

**The repo's own rules come first.** If the repo has a pull request template, fill its sections and keep its checklists, ticking only what is true. What it does not ask for but the reviewer needs (above all the evidence) goes in its closest section, or after the last one.

## Evidence

The proof's media are the most persuasive part of the description and the easiest to get wrong.

- **Look at each one before it goes up**, a video through a few of its frames. A screenshot of a blank page, an error, a login wall, another page or a value other than the one claimed proves nothing and misleads: drop it and say what it should have shown.
- **Choose few.** One clear piece of evidence per thing asked, plus a video of the whole flow when there is a page. A reviewer looks at the few that matter.
- **Before and after side by side**, in a two-column table, so the difference is seen in one glance. Bare screenshots stacked one under another are huge and hard to compare.
- **A video alone in its own paragraph.** Inside a table or a sentence most hosts turn it into a link instead of a player.
- **Nothing private.** Mask tokens, keys and personal data in images and outputs. A video cannot be masked: if one shows something private, drop it.
- **Within the host's limits.** Each host caps file size and description length (see its file). Re-encode a video that is too large before dropping it; trim outputs and fold sections before cutting evidence.

## The host

The host is where `origin` points: GitHub, GitLab, Bitbucket or Azure DevOps. If the URL does not say (a self-hosted server), a repo config such as `.mstack.yml`'s `host:` or the CLI that is logged in tells you.

Before the first command against a host, read its file. It has the tool, the commands, how to upload media, the limits and the usual errors.

| [GitHub](references/hosts/gh.md) | [GitLab](references/hosts/gitlab.md) | [Bitbucket](references/hosts/bitbucket.md) | [Azure DevOps](references/hosts/azure.md) |
|---|---|---|---|

Another host: use its official CLI or API, from its documentation, with the same criteria. If there is no way to open a pull request there, or no logged-in session, end Blocked.

## What must hold

- **Look before you create, and before you retry.** Search for an open pull request from this branch first. If opening, editing or uploading fails, search again before retrying: the host may have created it anyway, and a retry duplicates it.
- **Only what is yours.** You may push the branch you are delivering, never force-push and never touch the base or other branches. Use only labels that already exist and fit; create none. Do not add reviewers unless asked: the repo's code owners or its people decide that.
- **Keep what people wrote.** Before replacing the description of an existing pull request, read it: a person may have added a note, an answer or ticked a box. What they added stays.
- **Texts go through files or stdin**, never inside the command line: shells break markdown, quotes and newlines.
- **No secrets** in the title, the description, the media or the comments. Credentials only from environment variables, never printed.
- **Issues close only where they should.** Link each issue the change resolves with the host's closing keyword (see its file). Where the keyword would not close it (another base branch, a tracker the host does not know), link it as related and say so.

## CI

A pull request with red CI is not ready for review, and on most repos CI only runs once the pull request exists. So open it as a draft, wait for its checks to finish and read their result:

- **Pass:** if the work is ready for review, mark it ready.
- **Fail:** leave it as a draft and report which checks failed, with their link. Fixing them belongs to whoever called you.
- **No CI** on the repo: it is not a failure. Say so in the description.
- **Cannot be read** (the host or its tool does not report it): say so in the description and in the result.

If the host or the repo has no drafts, a pull request that is not ready carries a do-not-merge line at the very top instead (its file has it).

## Result

End with this line, which whoever called you reads:

```
PR <number> · <draft | ready> · CI <pass | fail · <checks> | none | unknown> · <url>
```

Followed, only when there is something to say, by:

```
Media · <n> uploaded · dropped <file · why>, …
Blocked · <what is missing> · <how to give it>
```

If the pull request could not be opened, the result is only the `Blocked` line: say exactly what is missing (a tool, a session, a token, a host where to open it) and how to give it.
