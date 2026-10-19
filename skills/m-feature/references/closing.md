# Closing

Read after the review and any fix step, before the first closing step.

After the review and any fix step:

1. Check every step issue is closed, but a `credential?` step left open in an autonomous run.
2. Complete Decided and Sources.
3. Write the final pull request's title, labels and body in [`github.md`](github.md), keeping the Proved section's placeholders as they are. What to watch lists each `flaky` test file the step checks noted and each finding still `stale`.
4. `git switch feature/<name>` and `git pull --ff-only`. Run prove with that body and the map number; after a replan, also the last verdict comment and that prove's tree, so it re-proves. It comments its verdict on the map, opens the final PR (or edits the one an earlier prove opened) with the link to that comment, and deletes its evidence dir with its cleanup script; refused, it returns the dir, and the closing message lists every such dir once. A Not verified PR, or one with a `human check` line, is a draft, or carries a do-not-merge line atop its verdict alert where the repo cannot hold drafts. A green suite is not prove.
   - not verified on a requirement, or a `new` break: replan. The PR stays open at Not verified; the next prove updates it.
   - `human check`: a line only the human can drive, as `/m-prove` defines it. No replan, no Your call: the PR stays a draft with a Check by hand before merging list, and each check goes in the closing message's To merge; the human marks the PR ready after checking.
   - not driven, or `base not run`: Your call, naming the precondition. Clear it without changing app code (code changes go through build and the step check), then prove again. Or the human ships with it listed in the PR: `gh pr ready <n>`; a do-not-merge line comes out with `gh pr view <n> --json body --jq .body`, then `gh pr edit <n> --body-file -` without it; go to 5.
   - `pre-existing`, on a requirement or a break: no replan. It stays in the verdict comment and the pull request's Proved table.
   - `PR · not opened · tree changed`: the feature branch moved during prove; prove again.
5. The feature builds nothing more: `/m-review` step check `clear --base feature/<name>` deletes its baseline.
6. Tell the human, then stop:
   ```
   PR #<n> · <Proved | Not verified · human check | Not verified> · <draft | ready | draft unavailable> · <link>
   To merge · <each thing only the human can do: each human check, then `gh pr ready <n>`; a command the harness refused (with the `unattended.md` entry that would allow it); a changed or Assumed bound to accept> | nothing, merge it
   Shipped · Left out · What to watch in production   one line each
   Left on disk · <each evidence dir prove could not delete>   only when any
   ```
