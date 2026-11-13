# Host · Azure DevOps

Tool: `az` with the `azure-devops` extension (it installs itself the first time an `az repos` command runs). A reference is the pull request's `pullRequestId`.

## Always

- `--org`, `--project` and `--repository` come from `git remote get-url origin` (`https://dev.azure.com/<org>/<project>/_git/<repo>`, or `<org>.visualstudio.com`). Pass them on each command, or set them once with `az devops configure -d organization=<url> project=<project>`.
- **The description holds at most 4,000 characters.** Keep there the essential: what changes, whether it was seen working, the evidence that matters most and the issues. The rest (more evidence, how to try it, decision records) goes as the pull request's first comment, and the description says it is there.
- `--description` takes each value as a new line. To pass a whole file, use `--description @<file>` (the Azure CLI reads a value starting with `@` from the file); check after creating that the markdown arrived intact, since quoting differs between shells.
- If opening, editing or uploading something fails, look for the pull request before retrying: retrying duplicates it.
- Read JSON output with `--query` (JMESPath) or with Python.

## Check

```bash
az --version
az account show                 # session logged in
az repos show --repository <repo> --org <url> --project <project> --query defaultBranch
```

No session: the person runs `az login` (or `az devops login` with a personal access token in `AZURE_DEVOPS_EXT_PAT`).

## Base branch

`az repos show --repository <repo> --query defaultBranch` → `refs/heads/<base>`; drop the `refs/heads/`.

## Find the pull request

`az repos pr list --repository <repo> --source-branch <branch> --target-branch <base> --status active --query "[0].{id:pullRequestId, draft:isDraft}"`

## Open and edit the pull request

```bash
az repos pr create --repository <repo> --source-branch <branch> --target-branch <base> \
  --title '<title>' --description @<body file> --draft true --work-items <ids>
```

- `--work-items` links Azure Boards work items (space separated). That is how an issue is linked here: a closing keyword in the text does not close anything.
- Edit: `az repos pr update --id <n> --title '<title>' --description @<body file>`.
- The pull request's URL: `https://dev.azure.com/<org>/<project>/_git/<repo>/pullrequest/<n>`.

## Template

Azure looks in `.azuredevops/`, `.vsts/`, `docs/` and the root, in that order, and uses the first it finds, read from the default branch:

- For the base branch: `pull_request_template/branches/<base>.md` (or `.txt`) inside one of those folders. It wins over the default one.
- Default: `pull_request_template.md` (or `.txt`).

## Upload screenshots and videos

Files are attached to the pull request, so it must exist first.

1. Token: `az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv` (or the PAT). Never print it or write it to a file.
2. Upload each file with a unique name (names cannot be reused):
   `POST https://dev.azure.com/<org>/<project>/_apis/git/repositories/<repo id>/pullRequests/<n>/attachments/<name>?api-version=7.1`, body the file as `application/octet-stream`. The response carries `url`.
3. Replace each local path in the body with its `url` (with Python, not `sed`) and save it with "Edit".

Images render inline. Whether a video plays inline is not documented: link it on its own line and say what it shows.

## First comment

For what does not fit in the description: `POST https://dev.azure.com/<org>/<project>/_apis/git/repositories/<repo id>/pullRequests/<n>/threads?api-version=7.1` with `{"comments": [{"content": "<markdown>", "commentType": 1}], "status": 4}` (status 4 is closed, so it does not count as an open comment that blocks completion).

## Draft

- Publish (ready): `az repos pr update --id <n> --draft false`.
- Back to draft: `az repos pr update --id <n> --draft true`.

## CI

Builds run as branch policies. `az repos pr policy list --id <n> --query "[].{name:configuration.type.displayName, status:status}"`: `approved` passes, `rejected` fails, `queued` or `running` is not finished. Wait while any is running. If there is no build policy, the repo has no CI for pull requests: it is not a failure, say so.

Taken from the documentation of `az repos` and the Azure DevOps REST API 7.1, not yet tested against a real organization. If something does not work, say in the pull request what could not be done.
