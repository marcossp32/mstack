# Host · GitLab

In GitLab the pull request is called a *merge request* (MR). Tool: `glab`, the official CLI. A reference is the MR's number (IID).

## Always

- The text goes through stdin, never inside the command: `--description-file -` with a heredoc `<<'EOF'`. Watch out: `--description -` opens an editor. Run `glab` from Bash (Git Bash on Windows).
- A title goes on one line in single quotes. If it contains `'`, write it as `’`.
- If opening, editing or uploading something fails, look for the MR before retrying: retrying duplicates it.
- `glab api` has no `--jq`: read its JSON with Python.

## Check

```bash
glab --version
glab auth status                                 # session logged in
glab repo view -F json --jq .default_branch      # the repo can be read
```

No session: the person runs `glab auth login` (with `--hostname <host>` if it is a self-hosted GitLab).

## Base branch

`glab repo view -F json --jq .default_branch`

## Find the MR

`glab mr list --source-branch <branch> --target-branch <base> -F json --jq '.[0] | {iid, web_url, draft}'`

## Open and edit the MR

```bash
glab mr create --source-branch <branch> --target-branch <base> --title '<title>' \
  --draft --push=false --yes --description-file - <<'EOF'
<body>
EOF
```

- `--push=false`: the branch is already pushed. `--yes`: it does not ask.
- What it prints on create is not documented. Get the number and the URL with "Find the MR".
- Edit: `glab mr update <n> --description-file -`.

## Template and issues

- Template: `.gitlab/merge_request_templates/Default.md`. A default set in the project's settings wins over that file.
- `Closes #<n>` closes the issue on merge into the default branch, unless the project turned automatic closing off. Against another base, write `Related to #<n>`.

## Upload screenshots and videos

1. Upload each file: `glab api --method POST projects/:fullpath/uploads --form "file=@<path>"`. The response carries a `url`.
2. Replace each local path in the body with its `url`. Do it with Python, not with `sed`: the paths have characters that `sed` interprets.
3. Save the body with "Edit".

A video linked as an image shows as a player. Put it alone in its paragraph.

## Draft

- Mark as draft: `glab mr update <n> --draft`.
- Mark as ready: `glab mr update <n> --ready`.

## CI

Wait for it to finish with `glab ci status --branch <branch> --wait` and then read the result with `glab ci status --branch <branch> -F json --jq .status`. They are two calls because `-F json` does not work together with `--wait`.

Taken from `glab`'s documentation, not yet tested against a real GitLab. If it does not work, say in the pull request that CI could not be checked.
