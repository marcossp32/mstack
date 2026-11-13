# Tracker · GitHub Issues

Tool: `gh` 2.94 or later. A reference is the issue's number (`#123`) or its URL.

## Always

- The text goes through stdin, never inside the command: `--body-file -` with a heredoc `<<'EOF'`. Specs are full of `` ` `` and `$`, and the shell breaks them.
- Run `gh` from Bash (Git Bash on Windows). PowerShell mangles heredocs.
- A title goes on one line in single quotes. If it contains `'`, write it as `’`.
- If creating fails but it printed a URL, the issue was created. Use that URL and do not create it again.
- A body or comment accepts at most 65,536 characters.

## Check

```bash
gh --version              # 2.94 or later
gh auth status --active   # session logged in
gh repo view --json nameWithOwner
```

No session: the person runs `gh auth login`.

## Read the spec

`gh issue view <n|url> --json number,title,body,url`. A pull request number is not a spec.

## Save progress

In an issue with the `m-feature` label, titled `m-feature: <spec ref>`, that links the spec. Create it the first time with `gh issue create --label m-feature`. If the label does not exist, create it first with `gh label create m-feature`.

- `gh issue edit <n> --body-file -` replaces the whole body. Read it first and write it complete.
- What accumulates (reports, decisions) goes as a comment: `gh issue comment <n> --body-file -`.

## Read progress

List the candidates with `gh issue list --label m-feature --state open --json number,title,url` and keep the one whose title is exactly `m-feature: <spec ref>`. Text search does not work: it is approximate and can return another spec's. Read the body with `gh issue view <n>` and the comments, all of them, in order:

```bash
gh api --paginate "repos/{owner}/{repo}/issues/<n>/comments" --jq '.[] | "<!-- \(.created_at) -->\n\(.body)\n"'
```

## Find an issue

`gh issue list --state open --search '<words> in:title,body' --limit 20 --json number,title,body,url`. Search with a few simple words, without quotes or `$`. Only open ones count: a closed one was already fixed or discarded.

## Open an issue and comment

- Open: `gh issue create --title '<title>' --body-file -`
- Comment: `gh issue comment <n> --body-file -`
