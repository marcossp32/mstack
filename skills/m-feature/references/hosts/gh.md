# Host · GitHub pull requests (`host: gh`)

Read before the first host operation when `.mstack.yml` says `host: gh`, or `origin` points at github.com.

The final pull request opens on GitHub through `gh` 2.99.0 or later, the first release with `--attach`, which uploads screenshots and videos into the body. A PR ref is its number.

## Every operation

- The body reaches `gh` on stdin or from a file, never inside a shell string: it is full of backticks and `$`, which a shell expands. `--body-file -` fed by a quoted heredoc (`<<'EOF'`) keeps them literal.
- Run `gh` from the Bash tool (Git Bash on Windows): PowerShell mangles heredocs, `$(...)` and native stderr, and so corrupts bodies.
- A title is one line inside single quotes, so a `'` in it is written `’`.
- After any failed `open-pr`, `edit-pr` or `attach-media`, `find-pr` before trying again: a failed upload still leaves the PR created or edited, and creating again opens a duplicate.

## check

```bash
gh --version | head -1                      # 2.99.0 or later
gh auth status --active                     # exit 0: authenticated; exit 1: not
gh repo view --json nameWithOwner --jq .nameWithOwner   # a default repo resolves
```

Not installed or too old: the fix is installing `gh` 2.99.0 or later. Not authenticated: the login command is `gh auth login`. `gh` also takes a token from `GH_TOKEN` or `GITHUB_TOKEN`; a token is never asked for, printed or stored.

## default-branch

Returns the repo's default branch name, e.g. `gh repo view --json defaultBranchRef --jq .defaultBranchRef.name`.

## list-labels

Returns the repo's existing label names, from `gh label list --limit 500`, since the default limit of 30 hides some. A PR only ever gets labels that already exist.

## find-pr `<base>` `<head>`

Returns the open PR from `<head>` into `<base>` as `{number, url, isDraft}`, or `none`:

```bash
gh pr list --base <base> --head <head> --state open --json number,url,isDraft --jq '.[0] // "none"'
```

## open-pr `<base>` `<head>` `<title>` `<body>` `<draft?>` `<labels>`

Opens the PR assigned to the caller, with the labels, the spec's milestone when it has one, draft when `<draft?>` is true, and the media uploaded, which saves a second edit. Returns number and url: the URL `gh pr create` prints, the number its last segment.

```bash
gh pr create --base <base> --head <head> --title '<title>' --assignee @me \
  --label <label> --milestone '<milestone>' --draft \
  --attach '<path>' --body-file - <<'EOF'
<body>
EOF
```

- `--head` skips `gh`'s push and fork prompts; the branch is already pushed.
- A label or milestone refused: open without it and name it on the PR line.
- `--draft` refused (drafts need a public repo, or a plan that has them): open without it and apply the `set-draft` fallback.

## edit-pr `<n>` `<body>`

Replaces the whole body (`gh pr edit <n> --body-file -`; `--add-label` and `--attach` fit in the same call). A body holds at most 65,536 characters.

## attach-media `<n>` `<files>`

Afterwards the body holds no local media path: each is a hosted URL, or a line saying what the file showed and at which viewport, the file then named on the PR line.

- `--attach '<path>'` uploads an image or video and rewrites the body's references to that local path into the asset's URL; a file the body does not reference is appended instead. So the body writes each path as an absolute forward-slash path in angle brackets (`![<what it shows, viewport>](<C:/…/R1-head-1280x720.png>)`), and `--attach` gets the identical string. Text after a `#` in an `--attach` value is read as alt text, so a path holding `#` is renamed first. `gh pr edit <n> --attach …` without a body flag keeps the current body. At most 50 files per command.
- A video has no alt text and plays only alone in its own paragraph.
- Some uploads failed: the PR is still edited with those that succeeded, and the command exits non-zero. Attach again each path still in the body.
- A video refused for size (the limit depends on the plan, 10 MB on free ones): re-encoded at a lower frame rate it usually fits; still refused, it becomes its text line.
- Uploads work on github.com and GitHub Enterprise Cloud only: on GitHub Enterprise Server every reference becomes its text line.

## set-draft `<n>` `<true|false>`

`gh pr ready <n>` makes it ready; `gh pr ready <n> --undo` makes it a draft, "if supported by your plan".

Drafts unavailable: keep the PR ready and put `> **Not verified: do not merge.** This repo cannot hold draft pull requests.` as the verdict alert's first line after its `[!…]` marker (`edit-pr`); the PR line says `draft unavailable`. A Proved PR, or one that is a draft, carries no such line.

## Cannot do

- Drafts on private repos of plans without them: the do-not-merge line above.
- Media over the plan's size limit, or on GitHub Enterprise Server: a line saying what the file showed.
