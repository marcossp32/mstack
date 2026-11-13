# Host · GitHub

Tool: `gh` 2.99 or later (the first with `--attach`, which uploads screenshots and videos). A reference is the pull request's number.

## Always

- The text goes through stdin, never inside the command: `--body-file -` with a heredoc `<<'EOF'`. Run `gh` from Bash (Git Bash on Windows).
- A title goes on one line in single quotes. If it contains `'`, write it as `’`.
- If opening, editing or uploading something fails, look for the pull request before retrying: it may have been created anyway, and retrying duplicates it.
- A body accepts at most 65,536 characters.

## Check

```bash
gh --version              # 2.99 or later
gh auth status --active   # session logged in
gh repo view --json nameWithOwner
```

No session: the person runs `gh auth login`.

## Base branch

`gh repo view --json defaultBranchRef --jq .defaultBranchRef.name`

## Find the pull request

`gh pr list --base <base> --head <branch> --state open --json number,url,isDraft`

## Open and edit the pull request

```bash
gh pr create --base <base> --head <branch> --title '<title>' --assignee @me --draft \
  --attach '<path>' --body-file - <<'EOF'
<body>
EOF
```

- `--head` stops `gh` from trying to push: the branch is already pushed.
- If `--draft` fails (some plans have no drafts), open it without it and see "Draft".
- Edit: `gh pr edit <n> --body-file -` replaces the whole body.

## Template and issues

- Template: `.github/pull_request_template.md`, `pull_request_template.md` at the root or `docs/`, or one of several under `.github/PULL_REQUEST_TEMPLATE/`.
- `Closes #<n>` (or `Fixes`, `Resolves`), one keyword per issue, closes it on merge only if the pull request targets the default branch. Against another base, write `Related to #<n>`.

## Upload screenshots and videos

`--attach '<path>'` (on `pr create` or `pr edit`) uploads the file and replaces the local path in the body with its URL.

- In the body, write each path absolute, with `/` and between `<>`: `![what is shown](<C:/…/screenshot.png>)`. Pass exactly the same string to `--attach`.
- A video goes alone in its paragraph so it plays.
- If a video is too big (10 MB on free plans), lower its frames per second. If it still does not fit, put a line that says what was shown.
- When done, no local path may remain in the body: nobody else can open it.

## Draft

- Mark as ready: `gh pr ready <n>`.
- Back to draft: `gh pr ready <n> --undo`.

If the repo does not support drafts, put at the very top: `> **Not verified: do not merge.**`

## CI

Wait for them to finish with `gh pr checks <n> --watch --interval 30` and then read the result with `gh pr checks <n> --json name,bucket,link`.

- `pass` passes and `fail` fails.
- `skipping` tests nothing.
- `cancel`: rerun it once with `gh run rerun <id>`, taking the id from its `link` (`…/runs/<id>/…`). If it is canceled again, it counts as `fail`.
- If `gh pr checks` says there are no checks, the repo has no CI. It is not a failure: say so in the pull request.
