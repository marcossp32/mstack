# Host · Bitbucket Cloud pull requests (`host: bitbucket`)

Read before the first host operation when `.mstack.yml` says `host: bitbucket`, or `origin` points at bitbucket.org.

Bitbucket Cloud has no first-party CLI for pull requests (`acli` covers Jira, not Bitbucket), so every operation is a REST API 2.0 call with `curl`. A PR ref is its numeric `id`. `$API` is `https://api.bitbucket.org/2.0/repositories/<ws>/<repo>`, as `check` derives it from `origin`.

## Every operation

- A request body is a JSON file Python built from files the Write tool made, sent with `--data @<file>`, never a shell string: a title or body in one breaks on the first quote or `$`. Responses are read with Python, Git Bash having no `jq`.
- Run from the Bash tool (Git Bash on Windows). Scratch files go under `<git common dir>/mstack/bitbucket/`.
- After any failed `open-pr`, `edit-pr` or `attach-media`, `find-pr` before trying again, since creating again opens a duplicate.
- Pull requests have `draft`; they have no labels, assignee or milestone, and the API cannot attach a file to a pull request or its description.

## check

```bash
curl --version | head -1
python3 --version
API="https://api.bitbucket.org/2.0/repositories/$(git remote get-url origin | sed -E 's#.*bitbucket\.org[:/]##; s#\.git$##')"
curl -fsS -o /dev/null -H "Authorization: Bearer $BITBUCKET_API_TOKEN" "$API"    # token set, repo readable
```

- The `API` line reads `<ws>/<repo>` from an https, `git@bitbucket.org:` or `ssh://` remote alike.
- The token is an Atlassian API token created for Bitbucket under Bitbucket personal settings → API tokens, with the scopes `read:repository:bitbucket`, `write:repository:bitbucket` (the API marks Downloads uploads as repository writes), `read:pullrequest:bitbucket` and `write:pullrequest:bitbucket`, exported by the human as `BITBUCKET_API_TOKEN`, a name this adapter chose. There is no login command: a missing or failing token is fixed by creating and exporting one. It is never asked for, printed or stored, and expands at run time only.
- Atlassian documents `Authorization: Bearer <api token>` for API tokens, which needs no email, beside basic auth `<atlassian account email>:<api token>`. App passwords were removed in 2026.

## default-branch

`GET $API` → `mainbranch.name`.

## list-labels

Returns nothing: Bitbucket PRs have no labels.

## find-pr `<base>` `<head>`

Returns the open PR from `<head>` into `<base>` as `{id, url, draft}` (`url` = `links.html.href`), or `none`. List `GET $API/pullrequests?state=OPEN`, following each page's `next`, and match `source.branch.name` and `destination.branch.name` in Python. A `q` filter on those fields might narrow the list, but Atlassian does not document them as filterable.

## open-pr `<base>` `<head>` `<title>` `<body>` `<draft?>` `<labels>`

`POST $API/pullrequests` with `{"title", "description", "source": {"branch": {"name": <head>}}, "destination": {"branch": {"name": <base>}}, "draft": <bool>}`. Returns `id` and `links.html.href`.

- `<labels>` and the assignee have no place on the PR; labels m-feature wants seen go on one `Labels: <a>, <b>` line under Notes for reviewers. Bitbucket documents the repo's default reviewers as added to every new pull request.

## edit-pr `<n>` `<body>`

`PUT $API/pullrequests/<n>` with `{"description": …}`; "Only open pull requests can be mutated." Atlassian does not say a PUT may leave out `title`: refused, include the title from a `GET` of the PR. No size cap is documented; the body stays under the 65,536 characters it is written to.

## attach-media `<n>` `<files>`

Afterwards the body holds no local media path. Bitbucket has no inline upload for PR descriptions; the nearest place is the repository's Downloads.

- Upload: `curl -fsS -X POST -H "Authorization: Bearer $BITBUCKET_API_TOKEN" "$API/downloads" -F "files=@<path>;filename=<unique name>"`. An upload with an existing name replaces that file, so names are unique per run, e.g. `<feature>-<pr id>-<file name>`.
- In the body each reference becomes a link, not an image embed, plus one line saying what it shows and at which viewport: Downloads are not documented to render inline, and on a private repo only people with read access open them. Link form: `https://bitbucket.org/<ws>/<repo>/downloads/<unique name>`. Neither that form nor the `;filename=` override is documented: after the first upload, `GET $API/downloads` shows the name stored, and a link that does not open is replaced by the text line.
- Downloads refused (token scope, storage, disabled): each reference becomes its text line and the files are named on the PR line. The evidence dir is kept until the PR holds that text.

## set-draft `<n>` `<true|false>`

`PUT $API/pullrequests/<n>` with `{"draft": <bool>}`. `draft` is documented on create, not on update, so re-read the PR to confirm it changed. Refused or ignored: keep it open and put `> **Not verified: do not merge.** This repo cannot hold draft pull requests.` as the verdict alert's first line after its `[!…]` marker (`edit-pr`); the PR line says `draft unavailable`. A Proved PR, or one that is a draft, carries no such line.

## Cannot do

- Labels, assignee, milestone: none on Bitbucket PRs.
- Inline media: Downloads links with a text description, or text alone.
- Alerts (`> [!TIP]`) render as plain quotes; the verdict line still reads first.
