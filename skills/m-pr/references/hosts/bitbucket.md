# Host · Bitbucket Cloud

Bitbucket has no CLI for pull requests: everything is done with `curl` against its REST API. A reference is the pull request's `id`.

## Always

- Authentication: an Atlassian token in the `BITBUCKET_API_TOKEN` variable. Send it as `-H "Authorization: Bearer $BITBUCKET_API_TOKEN"`. Never print it or write it to a file.
- `$API` is `https://api.bitbucket.org/2.0/repositories/<workspace>/<repo>`. Get `<workspace>/<repo>` from `git remote get-url origin`.
- Build each request as a JSON file with Python and send it with `--data @<file>`. Read the responses with Python (Git Bash does not ship `jq`).
- If opening, editing or uploading something fails, look for the pull request before retrying: retrying duplicates it.
- Bitbucket pull requests have no labels, assignee or milestone.

## Check

```bash
curl -fsS -o /dev/null -H "Authorization: Bearer $BITBUCKET_API_TOKEN" "$API"
```

If it fails, the person has to create a token in Bitbucket (Personal settings → API tokens) and export it as `BITBUCKET_API_TOKEN`. The token needs these permissions: `read:repository:bitbucket`, `write:repository:bitbucket`, `read:pullrequest:bitbucket` and `write:pullrequest:bitbucket`.

## Base branch

`GET $API` → `mainbranch.name`

## Find the pull request

`GET $API/pullrequests?state=OPEN`, following `next` on each page. Look for the one with `source.branch.name` = your branch and `destination.branch.name` = the base.

## Open and edit the pull request

- Open: `POST $API/pullrequests` with `{"title", "description", "source": {"branch": {"name": <branch>}}, "destination": {"branch": {"name": <base>}}, "draft": true}`. The response carries `id` and `links.html.href`.
- Edit: `PUT $API/pullrequests/<id>` with `{"title", "description"}`.

## Template and issues

- Bitbucket's default description lives in the repo settings, not in a file: if the API returns one when the pull request is created empty, keep its sections.
- A Jira key (`ABC-123`) in the title links the pull request to that Jira issue when the site is connected. Merging does not close it: say it under what is left for a person.

## Upload screenshots and videos

Bitbucket does not allow putting images in the description. The closest thing is the repo's Downloads section:

1. Upload each file with a unique name: `curl -fsS -X POST -H "Authorization: Bearer $BITBUCKET_API_TOKEN" "$API/downloads" -F "files=@<path>;filename=<feature>-<id>-<file>"`.
2. In the body, replace each image with a link to `https://bitbucket.org/<workspace>/<repo>/downloads/<name>` and add a line that says what is shown.

If the upload fails, leave only the line that says what was shown.

## Draft

`PUT $API/pullrequests/<id>` with `{"draft": true}` or `{"draft": false}`. Then read the pull request again to check that it has changed. If it does not change, put at the very top: `> **Not verified: do not merge.**`

## CI

`GET $API/pullrequests/<id>/statuses`: each build reports its `state`. `SUCCESSFUL` passes, `FAILED` fails, `INPROGRESS` is not finished (wait), `STOPPED` counts as failed. An empty list means no build reported on this pull request: the repo has no CI for it, which is not a failure; say so.

Taken from Bitbucket's REST documentation, not yet tested against a real repo. If it does not work, say in the pull request that CI could not be checked.
