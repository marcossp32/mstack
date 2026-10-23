# Tracker · Markdown files (`tracker: md`)

Read before the first tracker operation when `.mstack.yml` says `tracker: md`, or the spec reference is a path to a `.md` file. This file holds:

- Where the files live, and why outside the work tree
- The file format `read-state` and `find-issue` parse
- `check`, then one section per operation, in the order the other trackers use, `publish-issues` the one that does work here
- Closing by hand, and what this tracker cannot do

No tool and no account: spec, state, steps and issues are plain Markdown files. The spec is a file in the repo, read as it is. `<md.dir>` is `.mstack.yml`'s `md:` → `dir:`, default `.mstack/`.

## Every operation

- Every file is written with the Write or Edit tool, so no body passes through a shell string.
- A ref is an absolute forward-slash path for a run file, or a repo-relative path for the spec and a published issue.

## Where the files live, and why

```
$MD = <git common dir>/mstack/md                  (git rev-parse --path-format=absolute --git-common-dir)
$MD/<feature>/state.md                            the state body
$MD/<feature>/comments.md                         state comments, oldest first
$MD/<feature>/steps/<n>-<slug>.md                 step items
$MD/<feature>/issues/<k>-<slug>.md                issues opened during the run
$MD/<feature>/pending/<file name>                 comments for issues already published
<md.dir>/issues/<n>-<slug>.md                     published issues, committed
```

Everything written during a run stays outside the work tree and is never committed. A builder has a step branch checked out, the step check, quality review and prove read diffs, and prove needs a clean tree: a file dropped into the checkout mid-run breaks all four. The git common dir survives a new session on this machine, not a move to another. Issues are for the team, so they reach the repo once, at closing, after prove has judged everything, in a commit of Markdown only that changes nothing prove drove.

## File format

State, step and issue files start with front matter:

```markdown
---
title: <one line>
labels: <comma-separated, e.g. found-by-prove>
status: open
parent: <state ref, steps only>
---
```

Then the body. Comments on a step or issue go under a final `## Comments` heading; links under `## Links`, one `- <relation> <ref>` per line. Every comment, wherever it lives, is headed `<!-- comment <n> <ISO date> -->`, `<n>` its position among that ref's comments, never by a Markdown heading: a debate record holds `###` headings, and comments must split unambiguously.

## check

```bash
git rev-parse --path-format=absolute --git-common-dir     # inside a git repo; $MD lives under it
python3 --version
```

Nothing to authenticate, so no login command: the only failures are being outside a git repo and having no Python.

## read-spec `<ref>`

`<ref>` is a path to a `.md` file: the spec, a state, a step or an issue. Returns text = the file without front matter; title = front matter `title:`, else the first `# ` heading, else the file name; url = the ref. A missing path is the setup stop.

## create-state `<name>` `<title>` `<body>`

`<name>` is the feature name and becomes `<feature>`. Writes `state.md` (`labels: feature:map`) and an empty `comments.md`; returns the state path.

## read-state `<ref>`

The state: `state.md`'s body, then `comments.md`. A step or issue: its file, comments included.

## write-state `<ref>` `<body>`

Replaces everything after the front matter with `<body>`; the front matter stays.

## comment `<ref>` `<body>`

Appends a headed comment: to `comments.md` for the state, under `## Comments` for a run step or issue. A published issue (`<md.dir>/issues/…`) is in the work tree, which stays untouched mid-run, so its comment goes to `$MD/<feature>/pending/<its file name>` and `publish-issues` applies it. Returns `<ref>#comment-<n>`.

## create-step `<state ref>` `<title>` `<body>`

Writes `steps/<n>-<slug>.md` with `labels: build` and `parent: <state ref>`, `<n>` the next free number, `<slug>` a short filesystem-safe form of the title. Returns the path.

## close-step `<ref>` `<comment>`

Appends the comment and sets `status: closed`.

## find-issue `<label>` `<query>`

Searches every run's files under `$MD`, so a state in flight for a spec is found, and the published issues. A match carries the label, `status: open`, and at least half the query's words; returns per match ref = path, title, body, or nothing. An issue another unmerged feature opened is visible only on this machine.

Run this script as written: it is the match rule above, and `grep -iF` aborts on the GNU grep 3.0 that Git for Windows ships.

```bash
python3 -I - '<label>' '<query>' "$MD" "<md.dir>/issues" <<'EOF'
import pathlib, re, sys
label, query, roots = sys.argv[1], sys.argv[2], sys.argv[3:]
words = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]
for root in roots:
    if not pathlib.Path(root).is_dir(): continue
    for f in sorted(pathlib.Path(root).rglob("*.md")):
        if "pending" in f.parts: continue
        t = f.read_text(encoding="utf-8").replace("\r\n", "\n")
        m = re.match(r"---\n(.*?)\n---\n?(.*)", t, re.S)
        if not m: continue
        meta = dict(l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)
        labels = [x.strip() for x in meta.get("labels", "").split(",")]
        if label not in labels or meta.get("status", "").strip() != "open": continue
        if sum(w in t.lower() for w in words) * 2 >= len(words):
            print(f"=== {f.as_posix()} | {meta.get('title', '').strip()}\n{m.group(2)}")
EOF
```

## open-issue `<title>` `<body>` `<labels>`

Writes `$MD/<feature>/issues/<k>-<slug>.md`, `<k>` the next free number, with `labels: <labels>` and `status: open`; returns the path. It gets its repo number at `publish-issues`.

## comment-issue `<ref>` `<body>`

As `comment`.

## ensure-labels `<labels>`

Nothing to create: a label is text in `labels:`.

## link `<a>` `<b>`

Only run files are written: the spec and published issues get no back-link mid-run. Both are steps of one state: `- blocked-by <b>` under `a`'s `## Links`, the blocked step passed first. Any other pair: `- related <b>` on `a`, and `- related <a>` on `b` when `b` is a run file.

## publish-issues

Runs at closing, after the final prove and before `host open-pr`, with `feature/<name>` checked out and clean. Afterwards:

- each run issue is in `<md.dir>/issues/<n>-<slug>.md`, numbered after the highest already there, with run refs inside it rewritten to published paths and state or step refs replaced by the feature name;
- each pending comment is appended under `## Comments` of its published issue;
- one commit, `mstack: publish issues for <feature>`, holds only `<md.dir>/issues`, pushed on `feature/<name>`. Stage that path alone: anything else in the commit would be code no prove judged.

Returns the map `<run ref> → <published path>`, with which the PR body's issue links are rewritten. Nothing to publish: no commit, an empty map.

## Closing by hand

Merging changes no `status:`. The To merge note names the published issues, if any, to set `status: closed` by hand; the spec is not the run's to edit, and the run dir is local.

## Cannot do

- Resume on another machine: the state is local to this clone's git dir.
- Assignees, notifications, web links: none. The PR names each issue path.
- Hosted media in issue files: evidence is text, the command and up to 15 lines of its output; screenshots and videos are never committed.
