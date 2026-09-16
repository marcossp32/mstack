---
name: m-feature
description: Takes one feature from idea to working code in a single conversation, over GitHub Issues.
disable-model-invocation: true
---

Run one feature through GitHub: one map issue plus one issue per build step. You own order, routing, state and what the human sees; stage skills do the work. Spend depth where a change is hard to undo; move fast elsewhere.

- A decision nobody has made that everything else waits on: stop and say so. Never invent a step to cover it.
- Read [`references/github.md`](references/github.md) before the first command.
- The human stays in this session until the final PR.
- Everything you write — chat, agent prompts, GitHub — follows [`references/writing.md`](references/writing.md).

# Start

1. `gh --version` ≥ 2.94.0 and `gh auth status`.
2. Create labels `feature:map` and `build`.
3. Cut and push `feature/<name>` from `main`.
4. Create the map: the request verbatim as provisional Goal, your provisional undo verdict, other headings empty.
5. Resolve routing for the whole feature and write its line to the map ([`references/routing.md`](references/routing.md)).
6. Start scan.

# Undo verdict

If this ships wrong, how hard is it to undo? You decide it; stages only report evidence.

- Hard: schema, public API, stored data format, core dependency.
- Easy: names, folders, internal structure.

It sets the depth of grilling, plan, build and review. Settle it and write it to the map three times: at the start; after scan (grilling uses it); after docs (plan, build and review use it — a vendor limit can change it). It stays fixed until a replan re-settles it, and remaining steps then run at the new depth. Tell the human whenever it changes.

# Stages

The order is fixed.

```
scan → grilling → docs → plan → build ⇄ review → prove
                          ↑                          │
                          └───────── replan ─────────┘
```

| Stage | Returns | Runs in | Skill |
|---|---|---|---|
| scan | 9 numbered answers | 4 fresh agents, parallel | `/m-scan` |
| grilling | confirmed Goal · where it runs · boundary and data-state answers if asked · Not doing · decisions made alone | main chat | `/m-grilling` |
| docs | 4 answers, each with a primary link | main chat | `/m-research` |
| plan | ordered steps · blocking · design checks | main chat | `/m-plan` |
| build | step branch · PR into the feature branch, its number, 4 test checks answered | fresh agent | `/m-build` |
| review | PASS or CHANGES REQUIRED · must-fix · what was checked | fresh agent | `/m-review` |
| prove | a verdict per requirement · what else broke · evidence for the pull request | fresh agent | `/m-prove` |

"Runs in" is fixed. A thin "Returns": tell the human and continue, except:

- Scan slices: A owns Q1, B Q2–5, C Q6 and Q9, D Q7–8. A slice missing one of its questions goes back naming it. You assemble the nine lines.
- Docs uses the version scan reported, never the newest.
- A review without a verdict did not finish: rerun it.
- Build returns no PR: see Step results.

## Docs

Hand these to `/m-research`. No subject (e.g. no external call, so no vendor timeout) → "not applicable", a finished answer.

1. Hard limits of the service or library: rate limits, payload sizes, quotas.
2. The documented timeout, as a number. `/m-build` writes it into code; `/m-review` checks it.
3. Vendor security guidance: auth, secrets, what never to log.
4. What changed in the installed version.

Post the reply as a comment on the map; links under Sources.

## Routing

- grilling and plan need the human; docs dispatches its own agents. These three stay in the main chat.
- Run all four scan slices at once.
- One build at a time: one step branch, one PR, one issue in flight.
- One review after every build, on that step's diff only.
- prove after the last PASS, before the final PR; again after any replan.

## Dispatch

Always a fresh agent, never a fork: a fork inherits the plan's reasoning and agrees with it.

First line of every prompt (without it, build skips the red-test gate):

```
Invoke the Skill tool with `<m-scan | m-build | m-review | m-prove>`. Then do the work below.
```

Models come from [`references/routing.md`](references/routing.md): tiers, never names. You resolved them at Start and wrote the line to the map; every dispatch below uses that line, and only its escalation signal changes it.

| Stage | subagent_type | tier |
|---|---|---|
| scan A | `Explore` | cheap |
| scan B, C, D | `Explore` | standard |
| build | `general-purpose` | one below the review tier; strong when the undo verdict is hard |
| review | `general-purpose` | strong |
| prove | `general-purpose` | strong; it routes its own drivers |

After each stage returns, append its ledger line ([`references/routing.md`](references/routing.md)).

The agent has not seen this conversation. Hand it:

| Stage | Inputs |
|---|---|
| scan A–D | the feature · the questions it owns |
| docs | installed versions (scan) · the four questions · target infrastructure |
| build | step issue number and Done when · scan Q2, Q4, Q5, Q6, Q7, Q8 · docs numbers or "not applicable" · plan's design-check answers · the step branch it is on · undo verdict |
| review | fixed point (`git merge-base HEAD feature/<name>`, recorded when the branch is cut) · step issue number · PR number · design-check answers · scan Q6 · docs timeouts or "not applicable" · map's Not doing and Settled up front · undo verdict |
| prove | Goal, Settled up front and Not doing from the map · scan Q9 · undo verdict · base branch `main` · keep evidence for the pull request (closing only) |

# Before every build and every review

Re-read the map and the open steps. Where they disagree with what you were about to do, the map wins, or fix the map first.

```bash
gh issue view <map> --json title,body --jq .body
gh issue list --state open --json number,title,labels --search "parent:<map>"
```

# Step results

- **PASS**: merge the step branch into the feature branch, close the step issue, add a line to Decided, start the next build.
- **Second CHANGES REQUIRED** on one step: no rework; replan.
- **CHANGES REQUIRED**: comment the must-fix list on the step issue; re-dispatch `/m-build` in rework mode with that list, the same hand-off and the existing branch; review again.
- **"Not checked"** line: if you omitted the input, re-dispatch with it; otherwise record it on the map before accepting PASS.
- **No PR** (Done when unobservable, or spec wrong): no review; replan.
- **"Worth noting"**: record on the map; never blocks.

After each step, compare what you learned against the plan. The approach is wrong: replan. Never redesign without the human's confirmation.

# Replan

Triggers: two CHANGES REQUIRED on one step · build returns no PR · a step shows the approach is wrong · prove returns not verified on a requirement or a `new` break. Scan findings feed grilling and plan, not replan.

1. Tell the human in one line what the failed step's branch contained, then clear it (nothing to clear when prove triggered):
   ```bash
   gh pr close 47 --delete-branch
   gh issue close 47 --comment "Replanned: <what broke>"
   gh issue edit 48 --remove-blocked-by 47
   ```
2. Add a dated line under Replans: what broke, what changes. Count the lines in the map body, never from memory. Second line: stop (below).
3. Run `/m-plan` in the main chat with its four inputs, the fact that broke the plan, and the steps merged into the feature branch, read from `git log` (not issue state).
4. The human confirms the revised list.
5. Create, rewrite and re-link step issues; note the change under Decided.

A re-cut step with the same Done when, even under a new issue number, is the same step: its next CHANGES REQUIRED means replan. A changed Done when starts at zero.

**Stop:**

- Leave the feature branch and merged steps as they are.
- Leave remaining step issues open, each commented that the plan is being re-cut.
- Open no PR to main.
- Tell the human in four lines: what shipped, what is unbuilt, the two things that broke the plan, the question only they can answer.

# Closing

After the last PASS:

1. `git switch feature/<name>` and `git pull --ff-only`. Run prove with evidence kept for the pull request; comment its verdict on the map, without the Evidence line. A green suite is not prove.
   - not verified on a requirement, or a `new` break: replan.
   - not driven, or `base not run`: Your call, naming the precondition. Clear it without changing app code (code changes go through build and review), then prove again; or the human ships with it listed in the PR.
   - `pre-existing`: stays in the comment.
2. Check every step issue is closed.
3. Complete Decided and Sources.
4. `HEAD^{tree}` differs from prove's: prove again first. Open the PR from the feature branch to main with the final pull request body in [`references/github.md`](references/github.md), attaching prove's Evidence files.
5. Delete prove's evidence dir.
6. Tell the human in three lines: shipped, left out, what to watch in production. Stop.

# What the human sees after each stage

Short, no paragraphs:

```
Checked   · up to 5 lines, one per finding
Decided   · up to 3 lines, one per decision, with why
Your call · what is left to ask (usually one thing)
Sources   · links
```

Always raise what changes the plan, even if a stage already settled it: it already exists, it breaks the repo's pattern, the infrastructure does not allow it. Say when a stage returned no answer.
