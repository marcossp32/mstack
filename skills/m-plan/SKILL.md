---
name: m-plan
description: "Turns /m-scan, /m-grilling and /m-research findings into ordered build steps and checks the design before code exists. Use as the plan stage of /m-feature, to revise a plan in flight, or to cut a change into buildable pieces."
---

Cut the work into build steps and run the design checks before any code exists. Runs in the main chat; the human confirms the list before issues are created.

# Inputs

- `/m-feature`: undo verdict, map number, feature branch.
- `/m-scan`: what exists, how the repo does it, what it calls it.
- `/m-grilling`: confirmed Goal, where it runs, hard-to-undo decisions.
- `/m-research`: limits, timeouts, security guidance.

A needed answer is missing: say so and stop. "Not applicable" is an answer.

# Steps

Each step, in priority order:

1. Merges alone and leaves the feature branch working. A step that only makes sense with its sibling is one step.
2. Delivers one small working case through every layer it needs: "a user can save a draft", not "all database models".
3. Fits one subagent. Split it if not, unless splitting breaks rule 1.
4. Riskiest first: the step that could prove the approach wrong.

Name steps after what a person can see or do, in the repo's words. Each has an observable **Done when**: what a user or caller sees (`GET /drafts/<id>` returns the saved draft, `report --month 2026-09` prints one line per account), not "implemented X" and not how to verify it. One or two steps: say it may not need a plan.

Every behaviour in the Goal, Settled up front and Assumed (data state on failure, defaults, limits) lands in some step's Done when.

Record blocking only where B cannot start before A lands, never for preferred order.

# Design checks

Run [`references/design-checks.md`](references/design-checks.md) against this plan, at the depth it sets. A check you cannot answer names a decision the plan has not made.

# Output

Show the human:

```
Steps    · one line each, in order, with Done when
Blocking · which steps block which
Design   · one line per check reported at that depth: what you found; if failed, what you changed
Settled  · one line per Settled up front or Assumed decision: the step whose Done when covers it, or why none needs one
Decided  · choices made without asking
```

A failed check the plan cannot fix: ask now.

After confirmation:

- Create every step issue, then link them. The labels exist already (`/m-feature` creates them). Bodies go on stdin, so backticks and `$` stay literal:
  ```bash
  gh issue create --title "<step>" --label build --parent <map> --body-file - <<'EOF'
  ## What to do

  ## What you need to know
  <earlier decisions that matter here, stated in full — not "see parent">

  ## Done when
  <something observable>
  EOF
  gh issue edit <B> --add-blocked-by <A>
  ```
  Each body is self-contained: the builder has not seen this conversation. No checklists or method; the stage skill carries those.
- Post the design checks as a comment on the map: `gh issue comment <map> --body-file -`.
- Add what the human ruled out to Not doing. `gh issue edit` replaces the whole body: read it first (`gh issue view <map> --json body --jq .body`) and change only that section.

# Replanning

Extra inputs: what broke the plan, and which steps are merged (from `git log`, not issue state).

- Plan only unmerged work.
- Say whether the undo verdict still holds. If it changed, the re-planned part and every remaining step use the new depth.
- Name the cause (often a wrong Done when, a misplaced boundary, or two steps in one), then re-cut.
- Re-run the design checks on what changed.
- The human confirms; re-link with `--add-blocked-by`.
- One line on what changed and why, for Decided.
- The failed step survived unchanged: you found the wrong cause; look again.
