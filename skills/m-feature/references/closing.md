# Closing

From every slice closed to the final line, plus the body of a contradiction issue opened during Understand. This file holds:

- Final prove ⇄ fix: what blocks the PR and is fixed, and what never is
- Issues: the found-by-prove and mstack:contradiction bodies, and searching before opening
- The pull request: opening or editing it, media, draft state, origin lines, cleanup and the final line
- Body: the PR title and the body template with the placeholders m-prove fills

Outcome: one PR from `feature/<name>` open on the host, its verdict from a final prove of the tree it shows, its media hosted, every issue opened or commented and linked both ways, the baseline cleared, the evidence dir gone, and the final line printed.

## Final prove ⇄ fix

- Before it: every step item closed (except those of not verified slices), the local `feature/<name>` equal to the remote, the prerequisites stopped (prove starts its own). Re-read the spec: a changed hash is noted under Spec and under Notes for reviewers; the run used the frozen copy.
- Write the PR title and body (below) first, keeping every `<!-- prove: … -->` placeholder: the final prove fills them.
- Dispatch the prove `mode: final` (SKILL.md, Dispatch). It returns the filled body (`<evidence dir>/pr-body.md`), the media list, the verdict, B lines, issue drafts, the evidence dir and a Cleanup line. `Body — none · tree changed` means `feature/<name>` moved during the prove: prove again, since the verdict must describe the tree the PR shows. Comment the verdict lines on the state, without local paths.
- Blocking, and fixed like a slice failure (Cleanup line first, patching-loop count, a fix item listing each with the value seen and an evidence excerpt, fix branch, step check, merge, prove again): an R line not verified, even one the base fails the same way; a `new` B line; a failing `S<k>` replay. Two failed fix rounds escalate in scope `final`, cap 2; after that the lines still failing stay not verified and Closing goes on.
- Never fixed: a `pre-existing` B line (it becomes an issue: it is not this feature's bug), `base not run` (it stays in the PR and keeps it from Proved), a plain `derived` line that fails (reported, never blocks).

## Issues

**found-by-prove**, one per issue draft. Search before opening, so a break many features hit stays one issue: `tracker find-issue found-by-prove` by the draft's title and by its Where surface; a match is the same surface with the same wrong value. Found: `tracker comment-issue` with the draft's Repro, Base vs head and Evidence under `Seen again by feature <name>`. Else `tracker open-issue … found-by-prove` with:

```
<Where>
## Repro
<Repro>
## Already broken on <base>
<Base vs head>
## Evidence
<Evidence: command + up to 15 lines; a screenshot only where the tracker can hold one, else what it showed>
Origin · feature <name> · PR pending
```

Link it to the state and put its link at the draft's `<!-- issue: B<n> -->` placeholder.

**mstack:contradiction**, opened in Understand:

```
<the spec's ref and url>
## Contradiction
"<excerpt one>" vs "<excerpt two>"
## What was built
<the reading chosen, why; the debate D<k> when one decided it>
## Where
feature/<name> · state <ref> · PR pending
```

## The pull request

- Each found-by-prove and contradiction issue this run opened or commented carries its origin: `Origin · feature <name> · PR <url>`. A tracker that publishes issues at closing (md) gets it written into each run issue before `publish-issues`, as `PR from feature/<name> into <base>`, since nothing reaches the repo after that commit; the others get it as a comment once the PR exists (below).
- `tracker publish-issues` (md commits the run's issues on `feature/<name>`; other trackers: no-op). When it committed, push, rewrite every issue link in the body with the map it returns, and name that commit under Notes for reviewers as markdown only, added after the proved tree.
- One PR per feature: `host find-pr <base> feature/<name>` finds it → `host edit-pr`; else `host open-pr`, draft unless Proved. Labels: only existing ones (`host list-labels`) that fit the change (a type, an area), never one mstack creates; none fit or no such operation: none. `open-pr` printed no number: `find-pr` again.
- `host attach-media <n> <media list>`: no local path may stay in the body, since a reviewer cannot open it.
- `host set-draft <n> false` only when Proved, `true` otherwise (the adapter's fallback is a do-not-merge line atop the verdict).
- Trackers other than md: comment the origin line on each of those issues. Comment the verdict line and PR url on the state.
- Clean up: the Cleanup line (`python3 <m-prove dir>/scripts/cleanup.py <evidence dir>` and what follows), then `python3 <m-review dir>/scripts/step_check.py clear --base feature/<name>`, then stop the prerequisites. A refused or failed cleanup is not retried: name the dir in the final line.
- Print the final line and end:
  ```
  PR <n> · <Proved | Not verified · human check | Not verified> · <draft | ready> · <url>[ · to merge <k> items][ · left on disk <dir>]
  ```

## Body

A reviewer sees from the top whether the feature works, without reading code or running anything, then every decision made without a human. Plain words, the user's view first, no stage names (`Q1`, `R line`, `slice prove`) outside requirement ids. A repo PR template (`.github/pull_request_template.md` or the host's equivalent) gets this content in its sections: the Proved section under its testing or screenshots heading, else after its last section.

**Title**: what a user can now do, short enough for a one-line log, in the repo's commit convention (recent subjects on the base show it). Never the branch name.

Keep the body under the host's cap ([`m-prove/references/pull-request.md`](../../m-prove/references/pull-request.md) says how to trim); the debate records' `<details>` blocks are trimmed before any verdict line.

The placeholders and section headings are what m-prove fills; keep them as written. The prose between them is guidance on what the reader needs.

````markdown
<!-- prove: verdict alert -->

## Summary
<what a user can now do and why it matters to them, 1–2 sentences, no file names>

<!-- prove: demo video -->

## Why
<the problem and the approach; why this approach over the one under Considered, when there is one>

## What changed
- **<behaviour or area>**: <what it does now that it did not> (`<main file>`)
<most important first; behaviour, not a file list>

## Proof in the running app
<!-- prove: requirements table, then one section per requirement -->
<derived requirements appear in the table's own group, "does not block">

## Not verified
<only when a slice or line is not verified: each slice, what does not work, why, its debates; each changed bound (`was:`) a person must accept>

## Regressions checked
<!-- prove: what else was driven against the base, and anything found -->

## Found by prove
<each found-by-prove issue opened or commented: link · what is broken, already on <base>; or "none">

## Decisions made without a human
- **Debates:** <each `D<k> · <question> → <decision>` line, then a `<details><summary>D<k> record</summary>` block with the record's Chosen, Rests on and Against (the reviewer may not be able to read the state); or none>
- **Assumed:** <each Assumed line with its why and sources; or none>
- **Contradictions in the spec:** <each mstack:contradiction issue link · the reading built; each requirement retired by a debate, with the line that replaced it; or none>

## Try it yourself
<!-- prove: how to launch and the steps a reviewer follows to see each requirement -->

<!-- prove: check by hand, only when there is a human check -->

## Risk and rollback
- **How hard to undo:** <hard | easy> · <why, from the state>
- **What to watch:** <risk, regression surface, each flaky test file, a red or not comparable baseline, unjudgeable suite>
- **Rollback:** <revert the merge commit; plus each data or config step a revert does not undo (a migration, a new env var, a cache to clear)>

## Notes for reviewers
<where to start reading; the spec changed after the run froze it, when it did; or none>

## To merge
<each thing only a person can do: each check by hand; each changed bound to accept; each refused command, with what it was for and the setup-mstack entry that would allow it; closing the state and spec items by hand, unless tracker and host are both `gh` and the PR targets the default branch; or "nothing, merge it">

Closes <state ref>      only with tracker gh, host gh and the default branch as base; otherwise those items go under To merge
Closes <spec ref>       the same, and only when the spec is a tracker item
````
