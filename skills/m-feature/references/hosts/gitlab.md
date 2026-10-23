# Host · GitLab merge requests (`host: gitlab`)

Read before the first host operation when `.mstack.yml` says `host: gitlab`, or `origin` points at a GitLab instance.

The final pull request is a GitLab merge request (MR), opened with GitLab's own CLI, `glab` (docs.gitlab.com/cli). A PR ref is the MR's IID.

## Every operation

- The description reaches `glab` on stdin or from a file, never inside a shell string: it is full of backticks and `$`, which a shell expands. `--description-file -` fed by a quoted heredoc (`<<'EOF'`) keeps them literal; `--description -` opens an editor instead.
- Run `glab` from the Bash tool (Git Bash on Windows): PowerShell mangles heredocs, `$(...)` and native stderr.
- A title is one line inside single quotes, so a `'` in it is written `’`.
- After any failed `open-pr`, `edit-pr` or `attach-media`, `find-pr` before trying again, since creating again opens a duplicate.
- `glab repo view`, `mr list`, `mr view` and `label list` take `-F json` and `--jq`; `glab api` has no `--jq`, so its JSON is read with Python, Git Bash having no `jq`.

## check

```bash
glab --version
glab auth status                                # non-zero exit: not authenticated
glab repo view -F json --jq .default_branch     # the remote resolves and the token can read it
```

Not authenticated: the login command is `glab auth login` (`--hostname <host>` for a self-managed instance; `--stdin < <file>` reads a token from a file). `glab` also takes a token from `GITLAB_TOKEN`, `GITLAB_ACCESS_TOKEN` or `OAUTH_TOKEN`, which win over a stored login; a token is never asked for, printed or stored.

## default-branch

`glab repo view -F json --jq .default_branch`. Empty: the `HEAD branch:` line of `git remote show origin`.

## list-labels

The project's existing label names, e.g. `glab label list -F json -P 100 --jq '.[].name'`. An MR only ever gets labels that already exist.

## find-pr `<base>` `<head>`

Returns the open MR from `<head>` into `<base>` as `{iid, web_url, draft}`, or `none`:

```bash
glab mr list --source-branch <head> --target-branch <base> -F json --jq 'if length == 0 then "none" else .[0] | {iid, web_url, draft} end'
```

The field names are the API's merge request object; `glab` documents no JSON schema of its own, so a field missing from the output is read from the full object.

## open-pr `<base>` `<head>` `<title>` `<body>` `<draft?>` `<labels>`

Opens the MR with the labels, the caller as assignee (the `username` from `glab api user`), the spec's milestone when it has one (by title), and draft when `<draft?>` is true. What `glab mr create` prints is undocumented, so number and url come from `find-pr` afterwards.

```bash
glab mr create --source-branch <head> --target-branch <base> --title '<title>' \
  --label '<a>,<b>' --assignee '<username>' --milestone '<milestone>' --draft \
  --push=false --yes --description-file - <<'EOF'
<body>
EOF
```

- `--push=false`: the branch is already pushed. `--yes` skips the submission prompt.
- A label or milestone refused: open without it and name it on the PR line.
- Media go through `attach-media`, not `--attach`: that flag is experimental and appends files at the end of the description instead of rewriting references in place.

## edit-pr `<n>` `<body>`

Replaces the description (`glab mr update <n> --description-file -`); labels via `--label`. GitLab holds about a million characters, well above the 65,536 the body is written to.

## attach-media `<n>` `<files>`

Afterwards the description holds no local media path: each is an uploaded URL, or a line saying what the file showed and at which viewport, the file then named on the PR line.

- Upload each file to the project: `glab api --method POST projects/:fullpath/uploads --form "file=@<path>"`, where `glab` fills `:fullpath` from the current repo. The response's `url` (`/uploads/<secret>/<file>`) "can be used in Markdown contexts", so the media render inside the description; keep the `![…](…)` form.
- Rewrite the description with Python, not `sed`: paths and bodies are full of characters `sed` reads as syntax. Read the current one (`glab mr view <n> -F json --jq .description`), replace each local path with its `url`, and `edit-pr` the result.
- An image link to a video file (`.mp4`, `.mov`, `.webm`) renders as a player; keep each alone in its paragraph.
- The upload size cap is an instance setting; GitLab documents 100 MB for attachments. A refused video usually fits re-encoded at a lower frame rate.

## set-draft `<n>` `<true|false>`

`glab mr update <n> --draft` makes it a draft; `--ready` makes it ready. Drafts exist on every tier, GitLab.com and self-managed.

Refused anyway: keep it ready and put `> **Not verified: do not merge.** This project cannot hold draft merge requests.` as the verdict alert's first line after its `[!…]` marker (`edit-pr`); the PR line says `draft unavailable`. A Proved MR, or one that is a draft, carries no such line.

## Cannot do

- Alerts (`> [!TIP]`) render from GitLab 17.10 on; an older instance shows them as plain quotes, the verdict line still read first.
- Media over the instance's upload cap: a line saying what the file showed.
