<!-- Copied from shared/github.md by scripts/sync-shared.mjs. Edit the source, not this copy. -->

# GitHub

## Prerequisites

- `gh` ≥ 2.94.0 (`gh --version`); older versions lack `--parent` and `--blocked-by`. Tell the human to upgrade; no GraphQL workaround. Below 2.99.0 there is no `--attach`: the final pull request describes its screenshots in words instead.
- `gh auth status` clean, default repo set.
- Once per repo, before trusting any `--json` field name here: `gh issue list --limit 1 --json bogus 2>&1 | head -40` prints the valid ones.
- Every body goes on stdin: `--body-file -` with a quoted heredoc (`<<'EOF'` keeps backticks and `$` literal). Nothing is written to the repo.

## Issues

Two kinds only: the **map** (label `feature:map`, one per feature) and one **step** issue per build step (label `build`). Everything else goes into the map's body or comments, or the chat.

`gh issue create --label` fails on a missing label, so create both first and confirm:

```bash
for l in feature:map build; do gh label create "$l" --force >/dev/null 2>&1; done
gh label list --limit 100 | grep -E 'feature:map|build'
```

## Where results land

| Stage | Destination |
|---|---|
| scan | one comment: the four slices as nine lines. You then decide the undo verdict and write it to the body |
| grilling | body: Goal, Where it runs, Settled up front, Not doing |
| docs | a comment with the answers; links under Sources |
| plan | the step issues; design checks as a comment; descoped items under Not doing |
| build | its step issue and pull request |
| review | chat. On CHANGES REQUIRED, you comment the must-fix list on the step issue |
| prove | a comment with the verdict, without its Evidence line. The final pull request carries the requirements, their evidence and a link to that comment |

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

Created with Goal and How hard to undo filled, other headings empty. Re-read before every build and review.

```markdown
## Goal
<done, in 1–2 observable lines. Starts as the request verbatim; /m-grilling confirms it; /m-prove judges against it>

## How hard to undo
<hard or easy, and why. Provisional → after scan → after docs → fixed from plan unless a replan changes it>

## Where it runs
<platform and what it limits. From scan Q8, else asked in grilling>

## Routing
<the Routing line, resolved once at the start. A stage escalated later adds a dated line under it: role, new tier, the signal>

## Settled up front
<!-- what /m-grilling returned -->

## Decided
<!-- one line per closed step: link + summary. Replan changes and why -->

## Sources
<!-- links /m-research used -->

## Not doing
<!-- out of scope for review. Filled by grilling and plan before the first review -->

## Replans
<!-- one dated line each: what broke, what changed. Two lines = stop -->
```

Open step issues are not listed in the map; query them:

```bash
gh issue list --state open --json number,title,labels --search "parent:<map>"
```

## Step issue body

Self-contained context: the builder has not seen the conversation. No checklists or method; the stage skill carries those.

```markdown
## What to do

## What you need to know
<earlier decisions that matter here, stated in full — not "see parent">

## Done when
<something observable>
```

## Branches

```
main
 └── feature/<name>    from main at the start. You never merge it; PR to main at the end
      └── step/<name>  one per step, cut from the feature branch when the step starts; merged into it on PASS, then deleted
```

- One step, one branch, one pull request. CHANGES REQUIRED: push fixes to the same branch.
- No direct commits to `main` or the feature branch.
- Blocking and progress use GitHub's blocked-by and sub-issues, not checklists in the body.

## Closing

`Closes #n` only works on pull requests to the default branch.

- Step PR body: `Part of #45`. After merging: `gh issue close 45 --comment "<what landed>"`.
- Final PR to main: `Closes #<map>`. Every step issue is closed before you open it.

## Final pull request body

The repo has `.github/pull_request_template.md`: fill its sections with the same content. Otherwise:

```markdown
<what a user can now do, one sentence>

## Why
<the problem and the approach, 2–4 sentences>

## What changed
- <the change, most important files first>

## Proved in the running app
| Requirement | Verdict | Evidence |
|---|---|---|
| <R1, quoted> | verified | ![<alt text>](<absolute path from prove's Evidence line>) |
| <R2, quoted> | verified | Output R2 |

<details><summary>Output R2: <command, one line></summary>

```
<up to 15 lines prove kept>
```
</details>

Also driven: <risk areas prove covered, one line> · Not driven: <line · precondition, or none> · [Prove verdict](<link to the map comment>)

## What to watch
- <risk, regression surface, rollback>

Closes #<map>
```

- A screenshot is an image reference to its file in prove's evidence dir. `--attach "<path>#<alt text>"`, once per image, uploads it and rewrites that reference; nothing is committed. Below gh 2.99.0: replace each image with one line saying what it shows and at which viewport.
- Before and after: a two-column table with the base screenshot beside the head one.
- Mask tokens, secrets and personal data before attaching; in a public repo attachments are visible without signing in.
- The body stays under 65,536 characters: trim outputs, never the verdict lines.

## Commands

```bash
# start
git switch -c feature/<name> main
git push -u origin feature/<name>
gh issue create --title "<feature>" --label feature:map --body-file -

# /m-plan: create every step, then link
gh issue create --title "<step>" --label build --parent 42 --body-file -
gh issue edit 45 --add-blocked-by 44

# each step
gh issue develop 45 --base feature/<name> --name step/<name> --checkout   # --name required
git merge-base HEAD feature/<name>                                         # fixed point for /m-review
gh pr create --base feature/<name> --title "<step>" --body-file -
gh pr merge --squash --delete-branch                                       # or --merge, per scan Q9
gh issue close 45 --comment "<what landed>"

# replan
gh pr close 45 --delete-branch
gh issue close 45 --comment "Replanned: <what broke>"
gh issue edit 46 --remove-blocked-by 45

# end: open it, then stop
gh pr create --base main --head feature/<name> --title "<feature>" --body-file -
```
