---
name: m-feature
description: Takes one feature from idea to working code over GitHub Issues; `/m-feature #<map>` resumes one in a new session.
disable-model-invocation: true
---

Run one feature through GitHub: one map issue plus one issue per build step. You own order, routing, state and what the human sees; stage skills do the work. Spend depth where a change is hard to undo; move fast elsewhere.

- Read [`references/github.md`](references/github.md) before the first command.
- A decision nobody has made that everything else waits on: stop and say so. Never invent a step to cover it.
- The human stays in this session until the final PR, unless they ask for an autonomous run (below): `--auto`, or they say they are away or to decide everything.

# What the human sees

Result first, one line per finding or decision, no recap. Between steps, write only when they must see or decide something. After each stage, short, no paragraphs:

```
Checked   · up to 5 lines, one per finding
Decided   · up to 3 lines, one per decision, with why
Your call · what is left to ask (usually one thing)
Sources   · links
```

Always raise what changes the plan, even if a stage already settled it: it already exists, it breaks the repo's pattern, the infrastructure does not allow it. Say when a stage returned no answer.

A turn that ends to wait on something running says the stage, step n of N, what runs and roughly how long.

# Start

1. `gh --version` ≥ 2.94.0 and `gh auth status`.
2. Split the arguments into the request and run instructions: `--auto` or words asking not to be asked (an autonomous run), credentials, budgets. Run instructions are not the request.
   - A credential stays in this conversation and reaches prove as its own input. It is never in text that gets posted: an issue, a comment, a PR body.
   - A budget goes on the map under Settled up front.
   - An autonomous run: `Mode: autonomous` goes there too, so a compacted or resumed session keeps the mode. Read [`references/unattended.md`](references/unattended.md) and run its check now, while the human is still here.
3. The target. A request that is, or names, `#<n>`: `gh issue view <n>`. An open issue labelled `feature:map` is a feature in flight: go to Resume. Any other open issue is the source issue: its body is the human's words, quoted in the provisional Goal. A pull request, a closed issue or no match: stop and ask which issue is meant, even in an autonomous run. What to build is never assumed.
4. The base: the branch the source issue says to target, else the default branch (`gh repo view --json defaultBranchRef --jq .defaultBranchRef.name`). Every branch a stage compares against is the remote one, after `git fetch`: `origin/<base>`, `origin/feature/<name>`. Merges land on GitHub, so a local copy may be missing or stale.
5. Create labels `feature:map`, `build` and `needs:human`.
6. Cut and push `feature/<name>` from `<base>`. First `git ls-remote --heads origin feature/<name>` must print nothing; a line is another feature's branch: pick another name.
7. Create the map: the request verbatim as provisional Goal, without the run instructions, Base with the feature branch and the source issue, your provisional undo verdict, other headings empty.
8. Start scan.

# Resume

A feature in flight is picked up from GitHub, never from memory: the session that started it may be gone.

1. Start's steps 1 and 4. Credentials are never stored: ask for them again. `Mode: autonomous` under Settled up front: the run stays autonomous; run [`references/unattended.md`](references/unattended.md)'s check.
2. Read the map body and its comments, its steps (`gh issue view <map> --json subIssues`), the feature branch under Base and its `git log`, and the step branches (`git ls-remote --heads origin`).
3. Continue at the first unfinished stage: no scan comment → scan; no numbered Goal → grilling; no docs comment → docs; no step issues → plan (a proposed list in the comments is shown again for confirmation); an open step → its build, or its step check when its PR is open; every step closed and no review report → review; else Closing. Start scan Q9's prerequisites again first (Routing).

# Undo verdict

If this ships wrong, how hard is it to undo? You decide it; stages only report evidence.

- Hard: schema, public API, stored data format, core dependency.
- Easy: names, folders, internal structure.

It sets the depth of grilling and plan. Settle it and write it to the map three times: at the start; after scan (grilling uses it); after docs (plan and build use it — a vendor limit can change it). It stays fixed until a replan re-settles it, and remaining steps then run at the new depth. Whenever it changes, tell the human.

# Stages

The order is fixed, but for docs: its questions 1–4 need only scan's versions and Q8's infrastructure, so they start when scan returns, in the background while grilling runs. A grilling answer that changes a docs subject re-asks only that question. Question 5 waits for grilling; plan waits for both.

```
scan → grilling → docs → plan → build ⇄ check → review ⇄ fix → prove
                          ↑                                      │
                          └────────────────── replan ────────────┘
```

| Stage | Returns | Runs in | Skill |
|---|---|---|---|
| scan | 9 numbered answers | 4 fresh agents, parallel | `/m-scan` |
| grilling | Goal as numbered clauses · where it runs · boundary and data-state answers if asked · Considered · Not doing · decisions made alone | main chat | `/m-grilling` |
| docs | 4 answers (5 in an autonomous run), each with a primary link | main chat | `/m-research` |
| plan | ordered steps · blocking · design checks | main chat | `/m-plan` |
| build | step branch · PR into the feature branch and its number, or a stop line | fresh agent | `/m-build` |
| check | `STEP CHECK: PASS`, `FAIL` or `NOT RUN`, per step | main chat, a script | `/m-review` |
| review | `report.py`'s output: confirmed findings, each failed by a frozen reproduction · counts | fresh agent, dispatches its own agents | `/m-review` |
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
5. Autonomous run only: each hard-to-undo decision grilling put under Assumed. The answer confirms it or revises it on the map.

Post the reply as a comment on the map; links under Sources.

## Routing

- grilling and plan need the human; docs dispatches its own agents. These three stay in the main chat. Review runs in a fresh agent so its hunt stays out of this conversation; it returns `Review · not run · no Agent tool`: run it here.
- Run all four scan slices at once.
- One build at a time: one step branch, one PR, one issue in flight.
- When scan returns, start the prerequisites scan Q9 lists (a database, a service), each contained with `run_in_background` (m-review's `scripts/contain.py`), from a directory outside the checkout: the step check ends every contained process started inside it. Keep them up while steps are checked and reviewed; stop them by the pid contain printed before each prove, which starts its own, and start them again for a replan's steps. Without them the baseline is red, and no step check can judge the suite.
- Then record the step check baseline on the feature branch: `/m-review` step check `baseline` with scan Q6's two commands, the whole suite and one test file. Where scan says test files launch a browser or a server, the suite command caps the files run at once at half the machine's cores, 4 at most, with the runner's flag scan names: one browser per core stalls the machine. A baseline recorded without that cap (a feature started before this rule) gets it with `step_check.py set-cmd` before the next step check. That baseline command is the suite command every later stage gets, the review included. A baseline that aborts at setup names what was missing: start it, record again. A red one: tell the human now, with its failing tests.
- A step check after every build, on its step branch.
- One review, after the last step passes its check, on the whole feature diff. After a replan prove triggered, skip it when what landed since the last review is under 300 changed lines and How hard to undo is easy, and go to Closing: the step checks, the replays and the re-prove judge a small fix, and a review there costs a round of hunters for little.
- prove after the review and any fix step, and it opens the final PR; again after any replan, as a re-prove: it drives only what the replan's diff can reach, and the rest keeps its verdict.

## Dispatch

Always a fresh agent, never a fork: a fork inherits the plan's reasoning and agrees with it. The agent has not seen this conversation: its prompt carries only the inputs below. Map sections reach it verbatim: name the map issue and the sections, and the agent reads them itself (`gh issue view <map> --json body --jq .body`). A section that needs changing changes on the map first.

First line of every prompt (without it, the agent works without the stage's rules):

```
Invoke the Skill tool with `<m-scan | m-build | m-review | m-prove>`. Then do the work below.
```

Each agent's model is a tier: cheap, standard or strong, the harness's quickest, middle and most capable, by its own names. A harness that offers no choice, or a tier that does not resolve, runs the agent on the session's model. Three judges stand after a build (step check, review, prove), so build runs on standard by default. `/m-research` and `/m-review` name the tier of the agents they dispatch.

| Stage | subagent_type | Model |
|---|---|---|
| scan A | `Explore` | cheap |
| scan B–D | `Explore` | standard |
| build, fix mode included | `general-purpose` | standard; strong when the undo verdict is hard |
| review | `general-purpose` | standard |
| prove | `general-purpose` | strong |

Inputs:

| Stage | Inputs |
|---|---|
| scan A–D | the feature · the questions it owns |
| docs | installed versions (scan) · the questions under Docs · target infrastructure (scan Q8) |
| build | step issue number and Done when · the map number, to read Not doing from · scan Q2–Q9 · docs numbers or "not applicable" · the run recipe's path: scan Q9's, else a `SKILL.md` under `~/.claude/skills/` or `~/.agents/skills/` whose description names this repo (where `/m-prove` writes one), else scan Q9 · the step branch it is on |
| build, fix mode | the fix step issue (claims, conditions, entry points) · the map number, to read Not doing from · the same scan, docs and recipe inputs · the fix branch it is on |
| review | the feature review · base `origin/<base>`, after `git fetch` · the step check baseline's suite command (Routing) · a setup command for a fresh checkout, from scan Q9 · the map number, to read Goal, How hard to undo, Settled up front, Assumed and Not doing from |
| prove | the map number, to read Goal, Settled up front, Assumed and Not doing from · scan Q9 · base branch `origin/<base>`, after `git fetch` · credentials from the run instructions or grilling, if any · each review finding still `stale`, as a risk area: a confirmed bug never shown fixed · on a re-prove, the last verdict comment and that prove's tree · closing only: the final pull request (map number, feature branch, title, and its body with the Proved section's placeholders) |

# Before every build and the review

Re-read the map and the open steps. Where they disagree with what you were about to do, the map wins, or fix the map first.

```bash
gh issue view <map> --json title,body --jq .body
gh issue view <map> --json subIssues --jq '.subIssues.nodes[] | select(.state=="OPEN") | "#\(.number) \(.title)"'
```

Before a build, cut the step branch, then dispatch it.

# Step results

Run the step check on the step branch with the PR number, against `origin/feature/<name>` after `git fetch`. Run it as its own command, unpiped, and read its result before a merge or anything else.

- **PASS**: merge the step branch into the feature branch, close the step issue, add a line to Decided, start the next build.
- **FAIL**: comment its output on the step issue; re-dispatch `/m-build` with that output, the same hand-off and the existing branch; check again. Only a PASS after a change clears a FAIL: running the check again without a build fixes nothing.
- **`flaky · <files>`** on a PASS: test files this step did not touch failed on one run only and pass alone. Merge; note each file on the map once; it goes under the final PR's What to watch. A file the step touched that fails on one run only is still a FAIL.
- **NOT RUN · suite unstable under load**: each suite run failed on different files, all passing alone: the machine runs too many at once. `step_check.py set-cmd` with the suite command running half as many files at once (scan's flag), then check again; it does not count toward a second FAIL. Still unstable at one file at a time: tell the human (in an autonomous run, stop with it).
- **NOT RUN**, any other: a run hit its ceiling, 3 times its baseline run: something hangs, and nothing was judged. Comment it on the step issue and tell the human (in an autonomous run, stop with it). It is not a FAIL and does not count toward a second one.
- **Second FAIL** on one step: replan. A re-cut step with the same Done when, even under a new issue number, is the same step: its next failed step check means replan. A changed Done when starts at zero.
- **`credential?`** line: show the human before merging.
- **`unpinned?`** line: the builder says no test can pin this step. Add its reason to the step's Decided line; prove judges the step alone.
- **`credential placeholder`** line: a key-shaped value that says it is not real. It holds no merge; it stays in the step check output.
- **`pinned · not run`**: the check lacked what it names. Comment that on the map once and tell the human.
- **Baseline red**: the suite was red when the feature started. The step check fails a step only on files outside the baseline's failing set, so comment that set on the map once and tell the human.
- **No PR**: a missing decision, ask the human; an unobservable Done when or a contradiction, replan.

After each step, compare what you learned against the plan. The approach is wrong: replan. A redesign waits for the human's confirmation.

# Review results

Read [`references/review-results.md`](references/review-results.md) when the review returns, then act on its report by it.

# Replan

Triggers: two failed step checks on one step · build returns no PR for an unobservable Done when or a contradiction · a finding still failing after two fix rounds · a patching loop: a new finding or `new` break in a non-test file that two repair steps of this feature already changed (review fix steps, and steps a replan added after a prove break) · a step shows the approach is wrong · prove returns not verified on a requirement or a `new` break. Scan findings feed grilling and plan, not replan.

A trigger fires: read [`references/replan.md`](references/replan.md), then replan by it.

# Autonomous run

The human asked not to be asked: `--auto`, or they are away, or told you to decide everything. The rest of this skill holds, except:

- Every point that waits on the human takes your recommendation: a grilling answer, the plan's confirmation, a replan's revised list, a disputed finding, a decision nobody has made, Your call. Record each on the map with its reason; a decision goes under Assumed. Nothing waits, so `needs:human` goes only where the lines below put it.
- A recommendation that is hard to undo, or one you would otherwise stop for, is grounded first: run `/m-research` on it, asked as facts it can quote: what the standard or the vendor's docs say to do, and the alternatives they document. Decide on what serves the product's users best, and put the sources beside it under Assumed.
- A `credential?` line stays unmerged for the human: leave that step open with `needs:human` on its issue, say so on the map, and go on with the steps that do not depend on it. Closing then runs with that step open, and the closing message puts it under To merge.
- A replan still needs a trigger from Replan, never taste.
- Requirements hold still:
  - Every requirement keeps its full scope through a failure: no narrowing, no dropped clause, no addition to Not doing. Not doing is fixed once plan is done: a replan's `/m-plan` adds nothing to it.
  - A clause's words are the human's and never change. Only its bound may change, once, as [`references/replan.md`](references/replan.md) says, and never to one that narrows it, a `bound —` clause included: keep `was: <old bound>` beside it on the map, say so under Assumed, and prove that line again: no build. The final PR stays a draft for the human to accept the new bound.
- Two Replans lines do not stop the run. Stop as [`references/replan.md`](references/replan.md) says, under Stop, only when:
  - The same requirement is not verified on two proves in a row, each after a step aimed at it, and `/m-research` on it quotes no documented alternative you have not tried: the approach is wrong.
  - Two re-proves in a row fail only on `new` breaks, every requirement verified; or prove has triggered three replans (three `prove ·` lines under Replans). List the breaks still open under the PR's What to watch; it stays Not verified.
  - The harness refuses a step merge ([`references/unattended.md`](references/unattended.md), Refused anyway): every later step, the review and prove build on the feature branch.
  - A budget the human set (money, time, rounds) is spent. A replans budget counts every line under Replans.
- Say each replan in one line as it starts, with what broke: the human may look in.

# Closing

After the review and any fix step: read [`references/closing.md`](references/closing.md), then close by it. The run ends on its message to the human.
