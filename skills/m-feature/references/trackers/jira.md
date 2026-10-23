# Tracker · Jira Cloud (`tracker: jira`)

Read before the first tracker operation when `.mstack.yml` says `tracker: jira`, or the spec reference is a key like `ABC-123` or an `atlassian.net` URL. This file holds:

- What the items are, and the tool
- Every operation: bodies as ADF, the helper that converts them, the size cap
- `check`, then one section per operation, in the order the other trackers use
- Closing by hand, and what Jira cannot do

Specs are Jira work items; the state is one Task labelled `feature:map`, its description holding the state body; each step is a sub-task of it labelled `build`; the run also opens `found-by-prove` and `mstack:contradiction` work items. A ref is the work item key. The project key is `.mstack.yml`'s `jira:` → `project:`, else the spec key's prefix.

The tool is Atlassian's own CLI, `acli` (developer.atlassian.com/cloud/acli), which covers every operation; REST API v3 with `curl` is the fallback where an `acli` command is refused or its output cannot be read.

## Every operation

- **Bodies are ADF.** Jira Cloud stores descriptions and comments as Atlassian Document Format, not Markdown: plain text sent to it is converted, and headings, tables and backticks do not survive the trip back, so `read-state` would not return what `write-state` wrote. Every body the run writes is therefore one ADF `codeBlock`, whose text nodes keep it verbatim, and is unwrapped on read. People see the Markdown as raw text in a code block; the run gets back exactly what it wrote. A spec a person wrote is ordinary ADF and comes back flattened to text: headings, paragraphs and list items survive, tables and media lose their layout.
- **Bodies never enter a shell string.** Write the body to a file under `<git common dir>/mstack/jira/` (`$TMP` below), wrap it with the helper, and pass the JSON with `--description-file` or `--body-file`, which `acli` documents as reading "plain text or Atlassian Document Format (ADF)". REST bodies are JSON files built by Python.
- **A body holds at most 32,767 characters**, descriptions and comments alike, and Jira Cloud refuses more. A state body near it moves its longest section's detail into a comment with a one-line pointer; a longer comment, such as the frozen spec, goes in parts headed `(part <i>/<k>)`, which `read-state` returns in order.
- A summary is one line inside single quotes, so a `'` in it is written `’`. JQL text is a few plain words.
- Run from the Bash tool (Git Bash on Windows): PowerShell mangles heredocs and native stderr.
- A create that exits non-zero may still have created the item: search for it (`labels = "<label>" ORDER BY created DESC`) before creating again, since creating again leaves two.

The helper, saved once to `<git common dir>/mstack/adapters/jira_adf.py` and run as `python3 -I "$ADF" wrap IN.md OUT.json | issues IN.json | comments IN.json`. `issues` prints `=== <KEY> | <summary>` then the description as text; `comments` prints each comment headed `<!-- comment <id> <created> -->`. It searches any JSON for work item objects (`key` with `summary` or `description`) and comment objects (`body`), so REST and `acli` output both read, whatever shape `acli --json` takes.

```python
"""mstack Jira adapter: Markdown <-> ADF. wrap IN OUT | issues IN | comments IN"""
import json, sys


def wrap(src, dst):
    text = open(src, encoding="utf-8").read()
    doc = {"version": 1, "type": "doc", "content": [
        {"type": "codeBlock", "attrs": {"language": "markdown"},
         "content": [{"type": "text", "text": text}]}]}
    json.dump(doc, open(dst, "w", encoding="utf-8"), ensure_ascii=False)


def plain(node):
    """ADF (or a plain string) -> text. A lone codeBlock comes back verbatim."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    kids = node.get("content", [])
    if node.get("type") == "doc" and len(kids) == 1 and kids[0].get("type") == "codeBlock":
        return "".join(k.get("text", "") for k in kids[0].get("content", []))
    if node.get("type") == "text":
        return node.get("text", "")
    if node.get("type") == "hardBreak":
        return "\n"
    inner = "".join(plain(k) for k in kids)
    t = node.get("type")
    if t == "heading":
        return "#" * node.get("attrs", {}).get("level", 1) + " " + inner + "\n\n"
    if t == "listItem":
        return "- " + inner.strip() + "\n"
    if t in ("paragraph", "codeBlock", "blockquote", "rule"):
        return inner + "\n\n"
    return inner


def walk(obj, want):
    """Yield every dict holding all keys in `want` (shape-tolerant: REST and acli JSON)."""
    if isinstance(obj, dict):
        if all(k in obj for k in want):
            yield obj
            return
        for v in obj.values():
            yield from walk(v, want)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v, want)


def field(d, name):
    return d.get(name, (d.get("fields") or {}).get(name))


def issues(src):
    data = json.load(open(src, encoding="utf-8"))
    for d in walk(data, ["key"]):
        if field(d, "summary") is None and field(d, "description") is None:
            continue
        print(f"=== {d['key']} | {field(d, 'summary') or ''}")
        print(plain(field(d, "description")).rstrip())


def comments(src):
    data = json.load(open(src, encoding="utf-8"))
    for d in walk(data, ["body"]):
        print(f"<!-- comment {d.get('id', '')} {d.get('created', '')} -->")
        print(plain(d["body"]).rstrip() + "\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    mode = sys.argv[1]
    if mode == "wrap":
        wrap(sys.argv[2], sys.argv[3])
    elif mode == "issues":
        issues(sys.argv[2])
    elif mode == "comments":
        comments(sys.argv[2])
    else:
        sys.exit("usage: wrap IN OUT | issues IN | comments IN")
```

The first time on a site, compare what `read-state` returns after `create-state` with the body written. `acli` documents that the file may be ADF, not that it stores an ADF file as ADF rather than as literal text: a mismatch means writes go through REST too.

## check

```bash
acli --version
acli jira workitem search --jql "project = <KEY>" --limit 1 --json     # authenticated and the project visible
python3 --version
```

- `acli jira auth status` shows the account, but its exit code when logged out is undocumented, so the search is the check. Not authenticated: the login command is `acli jira auth login --web` (browser OAuth), or `acli jira auth login --site "<site>.atlassian.net" --email "<email>" --token < <file>`, which reads the token on stdin. A token is never asked for, printed or stored.
- The REST fallback reads its credentials from the environment only: `JIRA_API_TOKEN` (an Atlassian API token), `JIRA_EMAIL` and `JIRA_SITE` (`<site>.atlassian.net`), names this adapter chose. Basic auth is `<email>:<api token>`, e.g. `curl -fsS -o /dev/null -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "https://$JIRA_SITE/rest/api/3/myself"`. The variables expand at run time; never echo them or write them to a file.

## read-spec `<ref>`

`<ref>` is a key, or a URL whose path ends in one (`…/browse/ABC-123`), and may be any work item the run made. Returns text = the description as text, title = summary, url = `https://<site>/browse/<KEY>`, the site taken from the spec URL, `JIRA_SITE` or `acli jira auth status`. E.g. `acli jira workitem view <KEY> --fields summary,description --json` into a file, then the helper's `issues`. REST: `GET /rest/api/3/issue/<KEY>?fields=summary,description`, same helper.

## create-state `<name>` `<title>` `<body>`

`<name>` is unused here; the md tracker needs it. Creates a Task labelled `feature:map` with the wrapped body; returns its key.

```bash
acli jira workitem create --project <KEY> --type Task --summary '<title>' --label feature:map --description-file "$TMP/state.json" --json
```

## read-state `<ref>`

Any work item: the description, then every comment oldest first, through the helper: `acli jira workitem comment list --key <KEY> --paginate --json`, whose order defaults to `+created`. REST: `GET /rest/api/3/issue/<KEY>/comment?orderBy=created&startAt=<n>`, paging with `startAt` until `startAt` plus the comments returned reaches `total`.

## write-state `<ref>` `<body>`

Replaces the whole description, so read it first and write all of it back with the one section changed: `acli jira workitem edit --key <KEY> --description-file "$TMP/state.json" --yes`. REST: `PUT /rest/api/3/issue/<KEY>` with `{"fields": {"description": <wrapped ADF>}}`.

## comment `<ref>` `<body>`

Adds a comment (`acli jira workitem comment create --key <KEY> --body-file <json> --json`); returns its link, `https://<site>/browse/<KEY>?focusedCommentId=<id>`. That URL form is Jira's usual permalink, not one Atlassian documents; where `--json` gives no id, the link is the work item's own URL.

## create-step `<state ref>` `<title>` `<body>`

Creates a sub-task of the state labelled `build`; returns its key.

```bash
acli jira workitem create --project <KEY> --type Sub-task --parent <STATE KEY> --summary '<title>' --label build --description-file "$TMP/step.json" --json
```

The sub-task type's name differs between projects (`Sub-task`, `Subtask`): refused, try the other. A project with neither gets a Task labelled `build`, `link`ed to the state.

## close-step `<ref>` `<comment>`

Comments, then moves the item to a done status: `acli jira workitem transition --key <KEY> --status "Done" --yes`. Status names belong to each workflow: `Done` refused, take the transition whose `to.statusCategory.key` is `done` (`GET /rest/api/3/issue/<KEY>/transitions`). None reachable: it stays open, and the comment says the step landed.

## find-issue `<label>` `<query>`

Open work items with that label matching the query; returns per match ref = key, title = summary, body = description text, or nothing. `text ~` searches summary, description and comments. E.g.

```bash
acli jira workitem search --jql 'project = <KEY> AND labels = "<label>" AND statusCategory != Done AND text ~ "<words>"' --fields key,summary,description --limit 20 --json
```

## open-issue `<title>` `<body>` `<labels>`

Creates a Task with those labels (`--label` takes them comma-separated) and the wrapped body; returns its key.

## comment-issue `<ref>` `<body>`

As `comment`.

## ensure-labels `<labels>`

Nothing to create: a Jira label exists once a work item carries it. Labels hold no spaces, and Atlassian lists no other forbidden character: a label refused for its `:` is written with `-` instead, in every operation and JQL of the run.

## link `<a>` `<b>`

Both are steps of one state: `a` is blocked by `b`, the blocked step passed first. Any other pair: a relates link.

```bash
acli jira workitem link create --out <B> --in <A> --type Blocks --yes
acli jira workitem link create --out <A> --in <B> --type Relates --yes
```

`--out` is the outward side, which for `Blocks` is the one that blocks. `Blocks` and `Relates` are Jira's default link types, and an admin can rename them (`GET /rest/api/3/issueLinkType` lists a site's). Refused: a `comment` on `a` naming `b`.

## publish-issues

Nothing to publish here: returns an empty map.

## Closing by hand

Merging a pull request closes no Jira work item that the run can rely on, since automation is a site setting. The To merge note lists the state and spec keys to move to Done after merging.

## Cannot do

- Rendered Markdown: bodies show as one code block, the price of a faithful round trip.
- Hosted media: the PR host carries screenshots, and Jira bodies point to the PR.
