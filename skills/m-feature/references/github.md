# GitHub

## Prerequisites

- `gh` ≥ 2.99.0 (`gh --version`); older versions lack `--parent`, `--blocked-by` and `--attach`, which uploads the pull request's screenshots and videos. Tell the human to upgrade; no GraphQL workaround.
- `gh auth status` clean, default repo set.
- Once per repo, before trusting any `--json` field name here: `gh issue list --limit 1 --json bogus 2>&1 | head -40` prints the valid ones.
- Every body goes on stdin: `--body-file -` with a quoted heredoc (`<<'EOF'` keeps backticks and `$` literal). Nothing is written to the repo.
- Run these commands with the Bash tool (Git Bash on Windows), never PowerShell: heredocs, `$(...)` and `2>&1` are POSIX, and PowerShell breaks every body.

## Issues

Two kinds only: the **map** (label `feature:map`, one per feature) and one **step** issue per build step (label `build`). Everything else goes into the map's body or comments, or the chat.

One more label, `needs:human`, marks the issue the flow is waiting on the human for. `/m-feature` adds it when it stops for their answer and removes it when they give it:

| Issue | Waiting for |
|---|---|
| map | grilling's questions · plan confirmation, first or after a replan · a not driven or `base not run` prove line · a stop (`replan.md`) |
| step issue | a `credential?` line · a build stopped on a missing decision · a disputed review finding (on the fix step issue) |

```bash
gh issue edit 42 --add-label needs:human
gh issue edit 42 --remove-label needs:human
```

`gh issue create --label` fails on a missing label, so create all three first and confirm:

```bash
for l in feature:map build needs:human; do gh label create "$l" --force >/dev/null 2>&1; done
gh label list --limit 200 --json name --jq '.[].name' | grep -cxE 'feature:map|build|needs:human'   # must print 3: exact names, so `rebuild` does not count
```

## Where results land

| Stage | Destination |
|---|---|
| scan | one comment: the four slices as nine lines. You then decide the undo verdict and write it to the body |
| grilling | body: Goal, Where it runs, Settled up front, Assumed, Considered, Not doing |
| docs | a comment with the answers; links under Sources |
| plan | the proposed list with its design checks as a comment, before confirmation; then the step issues; what the human ruled out under Not doing, what plan left out itself under Considered |
| build | its step issue and pull request |
| step check | chat. On FAIL, you comment its output on the step issue |
| review | a comment with the report. Confirmed findings become one fix step issue: claim and condition, never the reproduction |
| prove | `/m-prove` posts a comment with the verdict on the map, without its Evidence line, then opens the final pull request, which carries the requirements, their evidence and a link to that comment |

Comments append. `gh issue edit` replaces the whole body, so read it first:

```bash
gh issue comment 42 --body-file - <<'EOF'
<report>
EOF

gh issue view 42 --json body --jq .body
gh issue edit 42 --body-file - <<'EOF'
<whole body, one section changed>
EOF
```

## Map body

Created with Goal, Base and How hard to undo filled, other headings empty.

```markdown
## Goal
<numbered clauses: <n>. "<the human's words>" · bound <domain | —> (<source>). Starts as the request verbatim; /m-grilling numbers and bounds it; ids never change; /m-prove judges R<n> against clause n>

## Base
<the branch the feature is cut from and merges into · feature/<name> · source issue #<n>, or none>

## How hard to undo
<hard or easy, and why. Provisional → after scan → after docs → fixed from plan unless a replan changes it>

## Where it runs
<platform and what it limits. From scan Q8, else asked in grilling>

## Settled up front
<!-- the human's answers to questions grilling asked; one with an observable effect is a Goal clause instead. Mode: autonomous and any budget -->

## Assumed
<!-- decisions the agent made or stated, even ones the human said go to, and answers that left it to the agent. Built like Settled up front; /m-prove does not turn them into requirements -->

## Decided
<!-- one line per closed step: link + summary. Replan changes and why -->

## Sources
<!-- links /m-research used -->

## Considered
<!-- what an agent thought of and is not building, with why. Excludes nothing from review or prove -->

## Not doing
<!-- out of scope for review. What the human ruled out, filled by grilling and plan before the review -->

## Replans
<!-- one dated line each, opening with its trigger (check · review · prove · bound ·): what broke, what changed. Two lines = stop, except in an autonomous run -->
```

Open step issues are not listed in the map; `/m-feature` queries them before every build and the review.

## Step issue body

Self-contained context: the builder has not seen the conversation. No checklists or method; the stage skill carries those.

```markdown
## What to do

## What you need to know
<earlier decisions that matter here, stated in full — not "see parent">

## Done when
<something observable> · serves <n>. "<clause>"
```

## Branches

```
<base>
 └── feature/<name>              from <base> at the start. You never merge it; PR to <base> at the end
      └── step/<name>-<n>        one per step, cut from the feature branch when the step starts; merged into it on PASS, then deleted
      └── step/<name>-fix-<n>    a fix step, cut from the feature branch after the review
```

`<base>` is the map's Base: the branch the source issue targets, else the default branch.

- One step, one branch, one pull request. A failed step check: push fixes to the same branch.
- A fix step is a step like any other.
- A step branch name carries the feature's name, so two features never share one. Before cutting it, `git ls-remote --heads origin <branch>` must print nothing. It prints a line: take the next number; never push over a branch that exists.
- `<base>` and the feature branch change only through merges: steps into the feature branch, the final PR into `<base>`.
- Blocking and progress use GitHub's blocked-by and sub-issues, not checklists in the body.

## Closing

`Closes #n` only works on pull requests to the default branch.

- Step PR body: `Part of #45`. After merging: `gh issue close 45 --comment "<what landed>"`.
- Final PR to `<base>`: `Closes #<map>`, and `Closes #<source>` when the map has a source issue. Every step issue is closed before `/m-prove` opens it, but a `credential?` step an autonomous run left open for the human.
- `<base>` is not the default branch: those lines close nothing. The closing message's To merge then gives the human `gh issue close <map> <source> --comment "Merged in #<PR>"` to run after merging.

## Final pull request body

A reviewer should see that the feature works from the top of the page, without reading code or running anything: the verdict, a demo video, then each requirement with its clip and its before and after. `/m-feature` writes the parts only it knows (Summary, Why, What changed, Risk and rollback, Notes for reviewers, the closing lines) and leaves every `<!-- prove: … -->` placeholder as it is: together they are the **Proved section**, which `/m-prove` fills from its verdict before it opens the pull request (`m-prove/references/pull-request.md`).

Write for a reviewer who has not seen the map: plain words, the user's view first, no stage names (`Q1`, `R line`, `carried`, `base not run`) outside the requirement ids. The repo has `.github/pull_request_template.md`: fill its sections with this content, the Proved section under its testing or screenshots heading, or after its last section when it has none.

**Title**: what a user can now do, under 72 characters, in the repo's convention (`git log --format=%s -20 <base>`: Conventional Commits there, `feat: …` or `fix: …` here; else plain imperative). Never the branch name.

````markdown
<!-- prove: verdict alert -->

## Summary
<what a user can now do and why it matters to them, 1–2 sentences, no file names>

<!-- prove: demo video -->

## Why
<the problem and the approach, 2–4 sentences; why this approach over the one named under Considered, when there is one>

## What changed
- **<behaviour or area>**: <what it does now that it did not> (`<main file>`)
<most important first; behaviour, not a file list: the diff tab lists the files>

## Proof in the running app
<!-- prove: requirements table, then one section per requirement -->

## Regressions checked
<!-- prove: what else was driven against the base, and anything found -->

## Try it yourself
<!-- prove: how to launch and the steps a reviewer follows to see each requirement -->

<!-- prove: check by hand, only when there is a human check -->

## Risk and rollback
- **How hard to undo:** <hard | easy> · <why, from the map>
- **What to watch:** <risk, regression surface, each flaky test file and stale finding>
- **Rollback:** <revert the merge commit; plus each data or config step a revert does not undo (a migration, a new env var, a cache to clear)>

## Notes for reviewers
<where to start reading (one or two files); each Assumed decision and each changed bound the human should accept; or none>

Closes #<map>
Closes #<source>   only when the map has a source issue
````

Hand prove the labels too: those `gh label list --json name --jq '.[].name'` already has that fit the change (a type such as `enhancement` or `bug`, an area), never one you create. `/m-prove` adds them, assigns the pull request to `@me`, and gives it the source issue's milestone, if any. Reviewers come from CODEOWNERS, which GitHub requests on its own.

## Commands

```bash
# start
gh issue view <n> --json state,title,body,url                               # the source issue; fails on a pull request
gh repo view --json defaultBranchRef --jq .defaultBranchRef.name           # <base>, when the issue names no target branch
git ls-remote --heads origin feature/<name>                                 # must print nothing
git fetch origin && git switch -c feature/<name> origin/<base>
git push -u origin feature/<name>
gh issue create --title "<feature>" --label feature:map --body-file -

# /m-plan: create every step, then link
gh issue create --title "<step>" --label build --parent 42 --body-file -
gh issue edit 45 --add-blocked-by 44

# each step
git ls-remote --heads origin step/<name>-<n>                                 # must print nothing
gh issue develop 45 --base feature/<name> --name step/<name>-<n> --checkout   # --name required
gh pr merge --squash --delete-branch                                       # or --merge, per scan Q9
git switch feature/<name> && git pull --ff-only                            # gh can leave the checkout on another branch
gh issue close 45 --comment "<what landed>"

# replan: the commands are in replan.md, beside this file
```
