# Tracker · GitHub Issues (`tracker: gh`)

Read before the first tracker operation when `.mstack.yml` says `tracker: gh`, or the spec reference is `#<n>` or a GitHub issue URL.

Specs are GitHub issues; the state is one issue labelled `feature:map`; each step is a sub-issue of it labelled `build`; the run also opens `found-by-prove` and `mstack:contradiction` issues. A ref is the issue number. The tool is `gh` 2.94.0 or later, the first release with `--parent` and `--add-blocked-by`.

## Every operation

- A body reaches `gh` on stdin or from a file, never inside a shell string: specs and evidence are full of backticks and `$`, which a shell expands. `--body-file -` fed by a quoted heredoc (`<<'EOF'`) keeps them literal.
- Run `gh` from the Bash tool (Git Bash on Windows): PowerShell mangles heredocs, `$(...)` and native stderr, and so corrupts bodies.
- A title is one line inside single quotes, so a `'` in it is written `’`. A search query is a few plain words, without quotes, `$` or backticks.
- A create that exits non-zero after printing a URL did create the issue: use that URL, since creating again leaves two.

## check

```bash
gh --version | head -1                      # 2.94.0 or later
gh auth status --active                     # exit 0: authenticated; exit 1: not
gh repo view --json nameWithOwner --jq .nameWithOwner   # a default repo resolves
```

Not installed or too old: the fix is installing `gh` 2.94.0 or later. Not authenticated: the login command is `gh auth login`. `gh` also takes a token from `GH_TOKEN` or `GITHUB_TOKEN` (`GH_ENTERPRISE_TOKEN` on GitHub Enterprise Server); a token is never asked for, printed or stored.

## read-spec `<ref>`

`<ref>` is `#<n>`, `<n>` or an issue URL, and may be any issue the run made. Returns text = body, title, url, and the milestone title when there is one, which the PR reuses: e.g. `gh issue view <n|url> --json number,title,body,url,milestone`. A pull request number is not an issue: that is the setup stop, saying so.

## create-state `<name>` `<title>` `<body>`

`<name>` is unused here; the md tracker needs it. Creates an issue labelled `feature:map`; returns its number, the last path segment of the URL `gh issue create` prints.

## read-state `<ref>`

Any issue, state or step: the body, then every comment oldest first, each headed `<!-- comment <id> <date> -->` so comments split unambiguously. A long thread spans pages, so fetch every one; run this as written:

```bash
gh api --paginate "repos/{owner}/{repo}/issues/<n>/comments" --jq '.[] | "<!-- comment \(.id) \(.created_at) -->\n\(.body)\n"'
```

## write-state `<ref>` `<body>`

`gh issue edit <n> --body-file -` replaces the whole body, so read it first and write all of it back with the one section changed. A body holds at most 65,536 characters: over that, move the longest section's detail into a comment and leave a one-line pointer to it.

## comment `<ref>` `<body>`

Adds a comment (`gh issue comment <n> --body-file -`); returns the comment URL it prints, which is the link to cite. A body over 65,536 characters, such as a long frozen spec, goes in several comments headed `(part <i>/<k>)`, which `read-state` returns in order.

## create-step `<state ref>` `<title>` `<body>`

Creates an issue labelled `build` as a sub-issue of the state (`--parent <state n>`), so the state shows its progress. Returns its number.

## close-step `<ref>` `<comment>`

Comments, then closes as completed. `gh issue close --comment` takes the text as an argument, which is a shell string, so the comment goes first through `comment`.

## find-issue `<label>` `<query>`

Open issues with that label whose title or body match the query; returns per match ref, title, body and url, or nothing. Only open issues count: a closed one was fixed or rejected, so a failure seen again gets a new issue that names the old one. E.g. `gh issue list --label '<label>' --state open --search '<query> in:title,body' --limit 20 --json number,title,body,url`.

## open-issue `<title>` `<body>` `<labels>`

Creates an issue with those labels, one `--label` each; returns its number. `--label` fails on a label that does not exist, which `ensure-labels` at Start prevents.

## comment-issue `<ref>` `<body>`

As `comment`.

## ensure-labels `<labels>`

Afterwards every named label exists, and labels the team already had are as they were: create only the missing ones, since `gh label create --force` overwrites a label's colour and description. Compare names exactly (`grep -xF`, or `rebuild` passes for `build`) against `gh label list --limit 500`, since the default limit of 30 hides labels on a busy repo.

## link `<a>` `<b>`

- Both are steps of one state, a Blocking pair: `a` is blocked by `b`, the blocked step passed first: `gh issue edit <a> --add-blocked-by <b>`.
- Any other pair (state and spec, state and issue): a comment on `a` saying `Related: #<b>` makes GitHub show the cross-reference on both; `<b>` in another repo is written as its full URL.

## publish-issues

Nothing to publish here: returns an empty map.

## Closing by hand

Where the PR's `Closes` lines do not apply ([`closing.md`](../closing.md) decides when they do), the To merge note gives `gh issue close <state> <spec> --comment "Merged in <PR link>"` to run after merging.

## Cannot do

- Sub-issues need GitHub Enterprise Server 3.17 or later, and blocked-by links 3.19 or later; github.com has both. Refused: the step is created without `--parent` and `link`ed to the state with a `Related` comment, and a refused blocked-by link becomes a `Blocked by #<b>` comment on `a`.
