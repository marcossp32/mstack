# Tracker · Jira

Tool: `acli`, Atlassian's official CLI. A reference is the key (`ABC-123`) or its URL. The project is `jira: project:` from `.mstack.yml`, or the prefix of the spec's key.

## Always

- **Jira does not store Markdown.** It stores its own format (ADF) and, when read back, headings, tables and code blocks are lost. So that what you write comes back the same, pass all text through [`scripts/jira_adf.py`](../../scripts/jira_adf.py):
  - Write: `python -I <this skill's folder>/scripts/jira_adf.py wrap text.md text.json` and pass the `.json` with `--description-file` or `--body-file`.
  - Read: save `acli`'s `--json` output to a file and pass it through `jira_adf.py issues` or `jira_adf.py comments`.
- Temporary files go in `<git common dir>/m-feature/jira/`, never in the repo.
- A body or comment accepts at most 32,767 characters. If something is longer, split it into several comments: `(part 1/3)`, `(part 2/3)`…
- Run from Bash (Git Bash on Windows).
- If creating fails, search before retrying: it may have been created anyway.

## Check

```bash
acli --version
acli jira workitem search --jql "project = <PROJECT>" --limit 1 --json   # session logged in and project visible
```

No session: the person runs `acli jira auth login --web`.

## Read the spec

`acli jira workitem view <KEY> --fields summary,description --json`, and then `jira_adf.py issues`. A spec written by a person comes back as plain text: tables lose their shape.

## Save progress

In a Task with the `m-feature` label, titled `m-feature: <spec key>`, that links the spec. In Jira, a label exists as soon as a task carries it.

- Create: `acli jira workitem create --project <PROJECT> --type Task --summary '<title>' --label m-feature --description-file progress.json --json`
- Update: `acli jira workitem edit --key <KEY> --description-file progress.json --yes`. It replaces the whole description, so read it first.
- What accumulates goes as a comment: `acli jira workitem comment create --key <KEY> --body-file <json> --json`.

## Read progress

List the candidates with `acli jira workitem search --jql 'labels = "m-feature" AND statusCategory != Done' --fields key,summary --json` and keep the one whose title is exactly `m-feature: <spec key>`. Text search is approximate and can return another spec's. The comments, in order: `acli jira workitem comment list --key <KEY> --paginate --json`, and then `jira_adf.py comments`.

## Find an issue

```bash
acli jira workitem search --jql 'project = <PROJECT> AND statusCategory != Done AND text ~ "<words>"' --fields key,summary,description --limit 20 --json
```

## Open an issue and comment

- Open: `acli jira workitem create --project <PROJECT> --type Task --summary '<title>' --description-file <json> --json`
- Comment: same as in "Save progress".
