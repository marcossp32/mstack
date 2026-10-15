# Replan

Read when a replan trigger in `SKILL.md` fires, before its first step.

A requirement not verified again, on an input its earlier fix did not cover (another character, another page of the same clause), is a wording question, not a code fix: the clause has no domain. Bound it instead of cutting another fix step, once per clause: ask the human the domain, with the one you recommend; in an autonomous run, take the domain `/m-research` quotes from the standard or the vendor as the clause's bound, `was: <old bound>` beside it, record it under Assumed, and keep the final PR a draft for the human to accept it. The bound you take or recommend covers the input that failed and everything the clause's words name; anything less narrows the requirement, `bound —` clauses included: then keep the old bound and run the steps below. Add a `bound ·` line under Replans (step 2), then run the steps below with one step whose Done when covers the whole new bound, so one fix meets the set instead of one input per round. A clause that fails again after its re-bound is not bound again: a second re-bound would loop.

Whatever fired, count for each non-test file the failure names the repair steps that already changed it, as [`review-results.md`](review-results.md) does. Two or more is a patching loop (each repair of one file broke another case in it): a design question, not one more fix: each patch satisfied the latest condition and dropped an earlier one. The replan's step for that file gets one Done when that lists every condition the earlier findings and breaks on it named, all at once, so one design must satisfy them together. In an autonomous run, `/m-research` first quotes what the standard or the vendor documents for that behaviour; the design goes under Assumed with its sources.

1. Tell the human in one line what the failed step's branch contained, then clear it (nothing to clear when prove triggered):
   ```bash
   gh pr close 47 --delete-branch
   gh issue close 47 --comment "Replanned: <what broke>"
   gh issue edit 48 --remove-blocked-by 47
   ```
2. Add a dated line under Replans, opening with its trigger, `check ·` (a step or its check), `review ·`, `prove ·` or `bound ·`, so the stop rules count from the map: what broke, what changes. Count the lines in the map body as it stands, not from memory. Second line: stop (below), except in an autonomous run (`SKILL.md`, Autonomous run).
3. Run `/m-plan` in the main chat with its four inputs, the fact that broke the plan, and the steps merged into the feature branch, read from `git log` (not issue state).
4. The human confirms the revised list.
5. Create, rewrite and re-link step issues; note the change under Decided.

A replan's steps serve requirements already on the map: their Done when never becomes a prove requirement. What the feature must do changes only through the Goal or Settled up front, with the human, or Assumed in an autonomous run. A decision the human settles here with an observable effect becomes a new Goal clause, quoting it, with the next unused number: prove judges the Goal's clauses.

**Stop:**

- Leave the feature branch and merged steps as they are.
- Leave remaining step issues open, each commented with why the run stopped.
- Open no PR to `<base>`. One prove already opened stays open at Not verified, as a draft or with its do-not-merge line; comment on it why the run stopped.
- Add `needs:human` to the map.
- Tell the human:
  ```
  Stopped      · <the question only they can answer>
  PR           · #<n> · Not verified · <link> | none opened
  Shipped      · <what merged> · Unbuilt · <what is left>
  Broke        · <what stopped it: the two things that broke the plan, a refused command, a spent budget>
  To merge     · <each open `credential?` step · each refused command, with the `unattended.md` entry that would allow it> | nothing
  Left on disk · <each evidence dir prove could not delete>   only when any
  ```
