# Final pull request body

Final mode, after Judge. You settle the verdict, fill the body and write the issue drafts; the caller opens or edits the pull request, turns local media paths into hosted ones, sets draft state and opens the issues, so everything here is files and return lines, never a tracker or host command.

## Verdict

- **Proved**: every blocking R line (`asked`, `derived · required by D<k>`) is `verified` or `verified · replay`; no R line carries `was:` (a changed bound needs a person to accept it); no B line is `new` or `base not run`; no `S<k>` line is `not verified` or `not driven` (a slice a later slice broke, or one nobody could re-check).
- **Not verified · human check**: short of Proved only by blocking lines that are `human check`. Nobody has seen those lines work.
- **Not verified**: anything else.

A plain `derived` line never changes the verdict: it is reported. Neither does an `S<k>` that is `superseded by S<j> | R<n>` (a later line changed that surface on purpose), nor a `pre-existing` B line (it becomes an issue).

## Media

Per R line, pick what shows it to a reviewer who will only look: for a page, Q1's clip and after screenshot beside Q2's before screenshot; otherwise the command and up to 15 lines of its output (for `verified · replay`, its block in `replay.txt`). Plus the demo.

- Look at each before it goes (a clip through its contact sheet): one showing a blank page, an error, a login wall, another page or a value other than the reported one is dropped and named on Harness. Media settle nothing, so dropping one never changes a verdict.
- Mask tokens, secrets and personal data in screenshots and outputs; drop a clip that shows one, since a video cannot be masked.
- Keep each file at most 10 MB, the smallest limit among common hosts; re-encode larger clips (e.g. `<ffmpeg> -y -i <in> -vf "fps=12,scale='min(1280,iw)':-2" -c:v libx264 -crf 32 -pix_fmt yuv420p -an <out>.mp4`). At most 50 files: a reviewer looks at the few that matter.

## Fill the body

If `git rev-parse HEAD^{tree}` no longer equals the contract's tree, the evidence is for another tree: fill nothing and return `Body — none · tree changed`.

Otherwise replace every `<!-- prove: … -->` placeholder in the body you were handed and write the result to `<evidence dir>/pr-body.md`. Placeholders you have nothing for (no breaks, no human check) are removed, never left as comments.

Write for a reviewer who never saw the run: what a user does and sees, values as the page or command showed them, no driver jargon. A line not verified shows its verdict and the value seen; a verified one shows its evidence. The body stays under 65,536 characters, GitHub's cap and the lowest among the hosts: trim outputs first, then fold sections into `<details>`, never the verdict lines. What each placeholder must give the reader:

- **Verdict alert**, the first block, so the verdict is the first thing seen. It opens with its alert marker line, `> [!TIP]` Proved, `> [!WARNING]` human check, `> [!CAUTION]` Not verified (the host adapters write after that marker; hosts that do not render alerts still show the text). It says how many required requirements were proved and, for Proved, how many other areas were checked against the base; for human check, how many only a person can check; for Not verified, what failed and the value seen.
- **Demo video**, alone in its own paragraph (`![](<path>)`): a video plays only there, inside a table or sentence it becomes a link. No demo: drop the placeholder and say in one line why.
- **Requirements table**: every R line with its id, the requirement quoted, its level and its result (verified, not verified with the value, not driven with the precondition, check by hand). Blocking lines first in id order, then plain `derived` lines as their own group marked as not blocking. A changed bound shows `was: <old bound>`.
- **One section per R line** below the table: the requirement quoted, the result (what was driven → value, via what route), then its evidence: the clip in its own paragraph, the before/after screenshots side by side (or after alone), or the command with up to 15 lines of output folded in `<details>`.
- **Regressions checked**: each covered area and what was driven, same as the base or `intended R<n>`; each break with head and base values: `new`, `base not run`, or `pre-existing` with `<!-- issue: B<n> -->` after it, where the caller puts the issue link; each `S<k>` whose replay did not pass (still works, broken by a later slice, or changed on purpose by which line); areas not driven with why.
- **Try it yourself**: how to launch (prerequisites, command, URL) and, per requirement, the steps Q1 drove ending in what the reviewer should see. Credentials by role and variable only, never a value.
- **Check by hand**, only with a `human check` line: `## Check by hand before merging` and one `- [ ]` item per line saying what to check, where, and what should be seen; one missing a credential adds `(set MSTACK_SECRET_<NAME> to let mstack prove it)`.

**Media paths** are matched by the caller when it uploads them, so they are exact: each clip and image referenced by the absolute path of its file in the evidence dir, forward slashes, inside angle brackets (`![<what it shows, viewport>](<C:/…/q1/R1-head-1280x720.png>)`; a video gets no alt text), and each path also on the return's Media line exactly as written in the body.

## Issue drafts

One per `pre-existing` B line, in the return, exactly this shape, since the caller parses it:

```
Issue B<n> · <title: what is broken, one sentence>
Where · <page | endpoint | command> · <file:line when Q2 found it>
Repro · <numbered steps the driver followed>
Base vs head · base <value> · head <value>
Evidence · <command> + up to 15 lines of its output · <screenshot path if any>
```

Write it for someone who never saw this feature: the break is in the base, not in this change. No credential values, no run ids beyond what the output shows. Leave out where it was found and any link: the caller adds them, and decides whether it joins an issue already open.
