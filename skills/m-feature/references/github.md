# GitHub

## Prerequisites

- `gh` ≥ 2.94.0 (`gh --version`); older versions lack `--parent` and `--blocked-by`. Tell the human to upgrade; no GraphQL workaround. Below 2.99.0 there is no `--attach`: the final pull request describes its screenshots in words instead.
- `gh auth status` clean, default repo set, and its token scopes include `project` (`read:project` is not enough to move cards). Missing, as on the first run on a machine: `/m-feature` runs `gh auth refresh -h <the board's host> -s project` itself (Start check).
- Standalone `jq` on PATH: the board commands pipe `gh` output to it, because `gh --jq` takes no `--arg`.
- Once per repo, before trusting any `--json` field name here: `gh issue list --limit 1 --json bogus 2>&1 | head -40` prints the valid ones.
- Every body goes on stdin: `--body-file -` with a quoted heredoc (`<<'EOF'` keeps backticks and `$` literal). Nothing is written to the repo.

## Issues

Two kinds only: the **map** (label `feature:map`, one per feature) and one **step** issue per build step (label `build`). Everything else goes into the map's body or comments, or the chat.

One more label, `needs:human`, marks the issue the flow is waiting on the human for. `/m-feature` adds it when it stops for their answer and removes it when they give it:

| Issue | Waiting for |
|---|---|
| map | grilling's questions · plan confirmation, first or after a replan · a not driven or `base not run` prove line · a replan stop |
| step issue | a `credential?` line · a build stopped on a missing decision · a disputed review finding (on the fix step issue) |

```bash
gh issue edit 42 --add-label needs:human
gh issue edit 42 --remove-label needs:human
```

`gh issue create --label` fails on a missing label, so create all three first and confirm:

```bash
for l in feature:map build needs:human; do gh label create "$l" --force >/dev/null 2>&1; done
gh label list --limit 100 | grep -E 'feature:map|build|needs:human'
```

## Board

One shared GitHub Projects board, the dashboard for every feature. It holds a card for the map, each step issue, each step pull request and the final pull request. The human gives its URL once per feature; it goes on the map under Board: `https://github.com/users/<owner>/projects/<n>` or `https://github.com/orgs/<owner>/projects/<n>`. Every command below takes `P=<n>` and `O=<owner>` from it.

| Field | Values | Cards |
|---|---|---|
| Status, the board's own | Todo · In Progress · In Review · Done · Proved · Not verified | step issues and pull requests. In Review is for step pull requests; Proved and Not verified for the final pull request. The map sets none: its Stage says where it is |
| Stage, created by the start check | Scan · Grilling · Docs · Plan · Build · Review · Prove · Replan · Done | the map only |

Blocked needs no value: the blocked-by links `/m-plan` sets show on the card, and clear when the blocking issue closes.

Who moves which card:

| Card | Value | When | Who |
|---|---|---|---|
| map | Stage Scan | map created | `/m-feature` |
| map | Stage Grilling … Prove | the stage starts. Check stays under Build, fix under Review | `/m-feature` |
| map | Stage Replan | a replan starts | `/m-feature` |
| map | Stage Build | the human confirms the re-cut steps | `/m-feature` |
| map | Stage Done | the final pull request is open and prove said Proved, or the human chose to ship it Not verified | `/m-feature` |
| step issue, fix step issue | Status Todo | issue created | `/m-plan`; `/m-feature` for a fix step |
| step issue | Status In Progress | its step branch is cut | `/m-feature` |
| step pull request | Status In Progress | `gh pr create` | `/m-build` |
| step pull request | Status In Review | the step check starts | `/m-feature` |
| step pull request | Status In Progress | the step check FAILs and the step goes back to build | `/m-feature` |
| fix step pull request | Status In Progress | its recheck is `still-failing` or `SUITE WORSE` and it goes back to build | `/m-feature` |
| final pull request | Status Proved or Not verified | prove judges | `/m-prove` |
| any card | Status Done | the issue closes or the pull request merges or closes | the board's built-in workflows |

A replan closes the discarded issue and pull request, so their cards reach Done too; nothing is deleted from the board.

### Start check

Stop on any failure and give the human the fix. Two parts, in order. Each code block is one call, and opens with its own values, because a shell may start fresh on each call: `H` is the board URL's host (`github.com` for a github.com board), `P` its project number, `O` its owner.

**1. Scope.** Check it:

```bash
H=<host>
gh auth status --active --hostname $H 2>&1 | grep -q "'project'" && echo "scope ok" || echo "scope missing"
```

`scope ok`: go to part 2. `scope missing`: start the refresh as a background run of the harness (its option for a command that keeps running after the call returns; a bare `&` may die with the call), and nothing else until it ends:

```bash
H=<host>
gh auth refresh -h $H -s project </dev/null >/tmp/gh-refresh.txt 2>&1
```

- It needs `-h` and no terminal: with a terminal it waits for Enter forever, and without `-h` it exits at once. Run that way, it writes a one-time code and `https://<host>/login/device` into `/tmp/gh-refresh.txt`, then polls until the code is approved or expires (15 minutes).
- Read the file, show the human the code and the URL, and name the account it refreshes (the active one).
- Its exit code may be out of reach: a shell that starts fresh on each call cannot `wait` on it. The signal is the scope check above: run it again after the human says they approved, and at most every minute until 15 have passed. `scope ok`: part 2. Still missing after 15 minutes, or the file shows an error: stop.

**2. Board.** One call; it stops at the first failure, and creates Stage only when the field list came back and has none:

```bash
( P=<n>; O=<owner>
gh project view $P --owner $O --format json --jq .title || { echo "board not reachable"; exit 1; }
F=$(gh project field-list $P --owner $O --limit 50 --format json) && [ -n "$F" ] || { echo "field list failed"; exit 1; }
echo "Status:"; jq -r '.fields[] | select(.name=="Status") | .options[].name' <<<"$F"   # all six values present?
if jq -e '.fields[] | select(.name=="Stage")' <<<"$F" >/dev/null; then
  echo "Stage:"; jq -r '.fields[] | select(.name=="Stage") | .options[].name' <<<"$F"   # all nine values present?
else
  gh project field-create $P --owner $O --name Stage --data-type SINGLE_SELECT \
    --single-select-options "Scan,Grilling,Docs,Plan,Build,Review,Prove,Replan,Done"
fi )
```

- Status or an existing Stage is missing a value: `gh` cannot add options to an existing field. The human adds it in the board's settings, under that field; then run the check again.
- Tell the human once that the board's hidden Parent issue and Sub-issue progress fields show each step under its map; they turn them on in the board's view settings.
- Tell the human once to leave the "Code review approved" and "Code changes requested" workflows off. Every agent runs under the human's account and GitHub does not let a pull request's author approve it, so they never fire.
- Tell the human once to keep the board's workflows "Item closed" and "Pull request merged" on, both setting Status to Done. `gh` cannot read them, and nothing else moves a card to Done.

### Setting a card

`item-add` returns the card already on the board when the issue or pull request is there, so it doubles as the lookup. One call:

```bash
P=<n>; O=<owner>
PID=$(gh project view $P --owner $O --format json --jq .id)
ITEM=$(gh project item-add $P --owner $O --url <issue or pull request URL> --format json --jq .id)
read FID OID < <(gh project field-list $P --owner $O --limit 50 --format json |
  jq -r --arg f "<Status | Stage>" --arg o "<value>" \
  '.fields[] | select(.name==$f) | .id as $i | .options[] | select(.name==$o) | "\($i) \(.id)"')
if [ -n "$OID" ]; then
  gh project item-edit --project-id $PID --id $ITEM --field-id $FID --single-select-option-id $OID
else
  echo "no <Status | Stage> value <value>, or the field list did not come back"   # stop and tell the human
fi
```

One field per `item-edit`: a card that needs two runs it twice.

## Where results land

| Stage | Destination |
|---|---|
| scan | one comment: the four slices as nine lines. You then decide the undo verdict and write it to the body |
| grilling | body: Goal, Where it runs, Settled up front, Not doing |
| docs | a comment with the answers; links under Sources |
| plan | the step issues; design checks as a comment; descoped items under Not doing |
| build | its step issue and pull request |
| step check | chat. On FAIL, you comment its output on the step issue |
| review | a comment with the report. Confirmed findings become one fix step issue: claim and condition, never the reproduction |
| prove | `/m-prove` posts a comment with the verdict on the map, without its Evidence line, then opens the final pull request, which carries the requirements, their evidence and a link to that comment, and sets its card |

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

Created with Goal and How hard to undo filled, other headings empty. Re-read before every build and the review.

```markdown
## Goal
<done, in 1–2 observable lines. Starts as the request verbatim; /m-grilling confirms it; /m-prove judges against it>

## How hard to undo
<hard or easy, and why. Provisional → after scan → after docs → fixed from plan unless a replan changes it>

## Where it runs
<platform and what it limits. From scan Q8, else asked in grilling>

## Board
<the shared board's URL, given by the human at the start>

## Routing
<the Routing line, resolved once at the start. A stage escalated later adds a dated line under it: role, new tier, the signal>

## Settled up front
<!-- what /m-grilling returned -->

## Decided
<!-- one line per closed step: link + summary. Replan changes and why -->

## Sources
<!-- links /m-research used -->

## Not doing
<!-- out of scope for review. Filled by grilling and plan before the review -->

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

- One step, one branch, one pull request. A failed step check: push fixes to the same branch.
- A fix step (`step/fix-<n>`) is a step like any other, cut from the feature branch after the review.
- No direct commits to `main` or the feature branch.
- Blocking and progress use GitHub's blocked-by and sub-issues, not checklists in the body.

## Closing

`Closes #n` only works on pull requests to the default branch.

- Step PR body: `Part of #45`. After merging: `gh issue close 45 --comment "<what landed>"`.
- Final PR to main: `Closes #<map>`. Every step issue is closed before `/m-prove` opens it.

## Final pull request body

`/m-feature` writes this body, leaving the Proved section's placeholders as they are, and hands it to `/m-prove`. Prove fills that section from its verdict, links the verdict comment it posted on the map, and opens the pull request. The repo has `.github/pull_request_template.md`: fill its sections with the same content. Otherwise:

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
gh issue create --title "<feature>" --label feature:map --body-file -    # then its card: Stage Scan

# /m-plan: create every step, then link
gh issue create --title "<step>" --label build --parent 42 --body-file -   # then its card: Status Todo
gh issue edit 45 --add-blocked-by 44

# each step
gh issue develop 45 --base feature/<name> --name step/<name> --checkout   # --name required; then the issue's card: Status In Progress
gh pr create --base feature/<name> --title "<step>" --body-file -         # /m-build; then its card: Status In Progress
gh pr merge --squash --delete-branch                                       # or --merge, per scan Q9
gh issue close 45 --comment "<what landed>"

# replan
gh pr close 45 --delete-branch
gh issue close 45 --comment "Replanned: <what broke>"
gh issue edit 46 --remove-blocked-by 45

# end: /m-prove opens it, a draft unless Proved, then sets its card
gh pr list --base main --head feature/<name> --state open --json number,isDraft --jq '.[0] // "none"'   # not none: an earlier prove opened it; edit it instead
gh pr create --base main --head feature/<name> --title "<feature>" --body-file - [--draft]   # drafts refused: without it, a do-not-merge first line
gh pr ready <n>            # Proved, or the human ships it; `gh pr ready <n> --undo` puts a Not verified one back to draft
```

Every card move uses Setting a card, under Board.
