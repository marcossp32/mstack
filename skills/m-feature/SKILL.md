---
name: m-feature
description: Takes one feature from idea to working code in a single conversation, over GitHub Issues.
disable-model-invocation: true
---

Run one feature through GitHub: one map issue plus one issue per build step. You own order, routing, state and what the human sees; stage skills do the work. Spend depth where a change is hard to undo; move fast elsewhere.

- A decision nobody has made that everything else waits on: stop and say so. Never invent a step to cover it.
- Read [`references/github.md`](references/github.md) before the first command.
- The human stays in this session until the final PR, unless they ask for an autonomous run (below).
- To the human: result first, one line per finding or decision, no recap. Between steps, write only when they must see or decide something.
- Agent prompts carry the inputs listed below, never this conversation's reasoning.
- Map sections reach an agent verbatim: name the map issue and the sections, and the agent reads them itself (`gh issue view <map> --json body --jq .body`). Never summarise, shorten or reword them in a prompt. A section that needs changing changes on the map first.

# Start

1. `gh --version` ≥ 2.94.0 and `gh auth status`.
2. Create labels `feature:map`, `build` and `needs:human`.
3. Cut and push `feature/<name>` from `main`.
4. Create the map: the request verbatim as provisional Goal, your provisional undo verdict, other headings empty.
5. Start scan.

# Undo verdict

If this ships wrong, how hard is it to undo? You decide it; stages only report evidence.

- Hard: schema, public API, stored data format, core dependency.
- Easy: names, folders, internal structure.

It sets the depth of grilling and plan. Settle it and write it to the map three times: at the start; after scan (grilling uses it); after docs (plan and build use it — a vendor limit can change it). It stays fixed until a replan re-settles it, and remaining steps then run at the new depth. Whenever it changes, tell the human.

# Stages

The order is fixed.

```
scan → grilling → docs → plan → build ⇄ check → review ⇄ fix → prove
                          ↑                                      │
                          └────────────────── replan ────────────┘
```

| Stage | Returns | Runs in | Skill |
|---|---|---|---|
| scan | 9 numbered answers | 4 fresh agents, parallel | `/m-scan` |
| grilling | confirmed Goal · where it runs · boundary and data-state answers if asked · Not doing · decisions made alone | main chat | `/m-grilling` |
| docs | 4 answers, each with a primary link | main chat | `/m-research` |
| plan | ordered steps · blocking · design checks | main chat | `/m-plan` |
| build | step branch · PR into the feature branch and its number, or a stop line | fresh agent | `/m-build` |
| check | `STEP CHECK: PASS` or `FAIL`, per step | main chat, a script | `/m-review` |
| review | confirmed findings, each failed by a frozen reproduction · counts | main chat, dispatches its own agents | `/m-review` |
| prove | a verdict per requirement · what else broke · at closing, the final PR open | fresh agent | `/m-prove` |

Whenever the flow stops for the human's answer, add `needs:human` to the issue it waits on, and remove it when they answer ([`references/github.md`](references/github.md), Issues).

"Runs in" is fixed. A thin "Returns": tell the human and continue, except:

- Scan slices: A owns Q1, B Q2–5, C Q6 and Q9, D Q7–8. A slice missing one of its questions goes back naming it. You assemble the nine lines.
- Docs uses the version scan reported, never the newest.
- A review without `report.py`'s output did not finish: rerun from the step that aborted.
- Build returns no PR: see Step results.

## Docs

Hand these to `/m-research`. No subject (e.g. no external call, so no vendor timeout) → "not applicable", a finished answer.

1. Hard limits of the service or library: rate limits, payload sizes, quotas.
2. The documented timeout, as a number. `/m-build` gets it as a fact for code that calls out.
3. Vendor security guidance: auth, secrets, what never to log.
4. What changed in the installed version.

Post the reply as a comment on the map; links under Sources.

## Routing

- grilling and plan need the human; docs and review dispatch their own agents. These four stay in the main chat.
- Run all four scan slices at once.
- One build at a time: one step branch, one PR, one issue in flight.
- When scan returns, record the step check baseline on the feature branch: `/m-review` step check `baseline` with scan Q6's command.
- A step check after every build, on its step branch.
- One review, after the last step passes its check, on the whole feature diff.
- prove after the review and any fix step, and it opens the final PR; again after any replan, as a re-prove: it drives only what the replan's diff can reach, and the rest keeps its verdict.

## Dispatch

Always a fresh agent, never a fork: a fork inherits the plan's reasoning and agrees with it.

First line of every prompt (without it, the agent works without the stage's rules):

```
Invoke the Skill tool with `<m-scan | m-build | m-prove>`. Then do the work below.
```

| Stage | subagent_type |
|---|---|
| scan A–D | `Explore` |
| build | `general-purpose` |
| prove | `general-purpose` |

Pick each agent's model by [`references/models.md`](references/models.md).

The agent has not seen this conversation. Hand it:

| Stage | Inputs |
|---|---|
| scan A–D | the feature · the questions it owns |
| docs | installed versions (scan) · the four questions · target infrastructure |
| build | step issue number and Done when · scan Q2–Q9 · docs numbers or "not applicable" · the step branch it is on |
| build, fix mode | the fix step issue (claims, conditions, entry points) · the same scan and docs inputs · the fix branch it is on |
| review (main chat) | base `main` · scan Q6's test command · a setup command for a fresh checkout, from scan Q9 · the map number, to read Goal, Settled up front, Assumed and Not doing from |
| prove | the map number, to read Goal, Settled up front, Assumed and Not doing from · scan Q9 · base branch `main` · on a re-prove, the last verdict comment and that prove's tree · closing only: the final pull request (map number, feature branch, title, and its body with the Proved section's placeholders) |

# Before every build and the review

Re-read the map and the open steps. Where they disagree with what you were about to do, the map wins, or fix the map first.

```bash
gh issue view <map> --json title,body --jq .body
gh issue list --state open --json number,title,labels --search "parent:<map>"
```

Before a build, cut the step branch, then dispatch it.

# Step results

Run the step check on the step branch with the PR number, against `origin/feature/<name>` after `git fetch`: merges land on GitHub, so the local feature branch is stale.

- **PASS**: merge the step branch into the feature branch, close the step issue, add a line to Decided, start the next build.
- **FAIL**: comment its output on the step issue; re-dispatch `/m-build` with that output, the same hand-off and the existing branch; check again.
- **Second FAIL** on one step: replan.
- **`credential?`** line: show the human before merging.
- **Suite "not comparable"**: the suite was red when the feature started, so the step check cannot judge it. Comment that on the map once, with the baseline's failing tests, and tell the human.
- **No PR**: a missing decision, ask the human; an unobservable Done when or a contradiction, replan.

After each step, compare what you learned against the plan. The approach is wrong: replan. Never redesign without the human's confirmation.

# Review results

After the last step passes its check: `git switch feature/<name>`, `git pull --ff-only`, run the feature review. Post its report on the map. After a replan, review only what landed since the last review: `--base <the head that review reported>`; code already reviewed is not hunted twice.

- **No confirmed findings**, or no test suite to review with: go to Closing; prove is the judge left.
- **Confirmed findings**: create one fix step issue (label `build`, parent = map) listing each finding's claim, condition and entry point, never the reproduction; Done when: no listed condition holds. Cut `step/fix-<n>`, dispatch `/m-build` in fix mode, run the step check, then `/m-review` recheck with `--promote` on each finding. All `fixed`: commit the promoted reproductions on the fix branch and merge it. No second review: prove judges the result.
- **`still-failing` or `SUITE WORSE`**: one more round on the same branch, naming which claims still hold and the suite's failing tests, never the reproduction's output. Still failing: replan.
- **The builder disputes a finding**: the reproduction did fail, so the question is what the spec wants. Show the human the claim and the builder's reason; they decide.

# Replan

Triggers: two failed step checks on one step · build returns no PR for an unobservable Done when or a contradiction · a finding still failing after two fix rounds · a step shows the approach is wrong · prove returns not verified on a requirement or a `new` break. Scan findings feed grilling and plan, not replan.

1. Tell the human in one line what the failed step's branch contained, then clear it (nothing to clear when prove triggered):
   ```bash
   gh pr close 47 --delete-branch
   gh issue close 47 --comment "Replanned: <what broke>"
   gh issue edit 48 --remove-blocked-by 47
   ```
2. Add a dated line under Replans: what broke, what changes. Count the lines in the map body, never from memory. Second line: stop (below), except in an autonomous run.
3. Run `/m-plan` in the main chat with its four inputs, the fact that broke the plan, and the steps merged into the feature branch, read from `git log` (not issue state).
4. The human confirms the revised list.
5. Create, rewrite and re-link step issues; note the change under Decided.

A replan's steps serve requirements already on the map: their Done when never becomes a prove requirement. What the feature must do changes only through the Goal or Settled up front, with the human, or Assumed in an autonomous run.

A re-cut step with the same Done when, even under a new issue number, is the same step: its next failed step check means replan. A changed Done when starts at zero.

**Stop:**

- Leave the feature branch and merged steps as they are.
- Leave remaining step issues open, each commented that the plan is being re-cut.
- Open no PR to main. One prove already opened stays open at Not verified, as a draft or with its do-not-merge line; comment on it that the plan is being re-cut.
- Add `needs:human` to the map.
- Tell the human in four lines: what shipped, what is unbuilt, the two things that broke the plan, the question only they can answer.

# Autonomous run

The human asked not to be asked: they are away, or told you to decide everything. The rest of this skill holds, except:

- Every point that waits on the human takes your recommendation: a grilling answer, the plan's confirmation, a replan's revised list, a disputed finding, a decision nobody has made, Your call. Record each on the map with its reason; a decision goes under Assumed. Nothing waits, so nothing gets `needs:human` but the next line.
- A `credential?` line is never merged on your own: leave that step open with `needs:human` on its issue and say so on the map.
- A replan still needs a trigger from Replan above, never taste.
- Two Replans lines do not stop the run. Instead:
  - A requirement that failed because of how it was worded, not because of what the code does: fix the wording you wrote (never the human's own words) on the map, say so under Decided, and prove that line again. No build, no replan.
  - The same requirement not verified on two proves in a row, each after a step aimed at it: the approach is wrong. Stop as under Replan.
  - A budget the human set (money, time, rounds) is spent: stop as under Replan.
- Say each replan in one line as it starts, with what broke: the human may look in.

# Closing

After the review and any fix step:

1. Check every step issue is closed.
2. Complete Decided and Sources.
3. Write the final pull request body in [`references/github.md`](references/github.md), keeping the Proved section's placeholders as they are.
4. `git switch feature/<name>` and `git pull --ff-only`. Run prove with that body and the map number; after a replan, also the last verdict comment and that prove's tree, so it re-proves. It comments its verdict on the map, opens the final PR (or edits the one an earlier prove opened) with the link to that comment, and deletes its evidence dir. A Not verified PR is a draft, or carries a do-not-merge first line where the repo cannot hold drafts. A green suite is not prove.
   - not verified on a requirement, or a `new` break: replan. The PR stays open at Not verified; the next prove updates it.
   - not driven, or `base not run`: Your call, naming the precondition. Clear it without changing app code (code changes go through build and the step check), then prove again. Or the human ships with it listed in the PR: `gh pr ready <n>`; a do-not-merge first line comes out with `gh pr view <n> --json body --jq .body`, then `gh pr edit <n> --body-file -` without it; go to 5.
   - `pre-existing`, on a requirement or a break: no replan. It stays in the verdict comment and the pull request's Proved table.
   - `PR · not opened · tree changed`: the feature branch moved during prove; prove again.
5. Tell the human in three lines: shipped, left out, what to watch in production. Stop.

# What the human sees after each stage

Short, no paragraphs:

```
Checked   · up to 5 lines, one per finding
Decided   · up to 3 lines, one per decision, with why
Your call · what is left to ask (usually one thing)
Sources   · links
```

Always raise what changes the plan, even if a stage already settled it: it already exists, it breaks the repo's pattern, the infrastructure does not allow it. Say when a stage returned no answer.
