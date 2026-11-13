# Tracker · Markdown files

No tool or account: the spec, the progress and the issues are `.md` files. A reference is the file's path.

- `<md dir>` is `md: dir:` from `.mstack.yml`, by default `.mstack/`.
- `<name>` is a short lowercase hyphenated name, taken from the spec's title. If you were only given text, pick it yourself and save that text as `<git common dir>/m-feature/<name>/spec.md`.

## Where each thing goes

```
<git common dir>/m-feature/<name>/progress.md     the progress
<git common dir>/m-feature/<name>/issues/         the issues you open during the work
<md dir>/issues/                                  the repo's issues, which are pushed with a commit
```

`<git common dir>` comes from `git rev-parse --path-format=absolute --git-common-dir`.

While you work, do not write anything inside the repo. Builds, reviews and tests look at the repo's changes, and a half-written file that shows up confuses them. That is why the progress and the issues live outside until the end.

## Check

`git rev-parse --git-common-dir` works: you are inside a git repo. There is no session to log in.

## Read the spec

Read the file. The title is the first `# ` and, if there is none, the file's name. If the path does not exist, there is no spec.

## Save and read progress

A single file, `progress.md`. Write and read it with the file tools, never passing the text through the shell.

## Find an issue

Search with the search tool in `<git common dir>/m-feature/*/issues/` and in `<md dir>/issues/`. Only those with `status: open` count.

## Open an issue and comment

- Open: write `<git common dir>/m-feature/<name>/issues/<n>-<short-title>.md`, starting like this:
  ```
  ---
  title: <title>
  status: open
  ---
  ```
- Comment: add the text at the end, under `## Comments`, with the date.

## Publish the issues at the end

Just before opening the pull request, copy the new issues to `<md dir>/issues/`, numbered after the ones already there. Push them in a commit that only has those files. That way the commit changes nothing of what was already proven. Then, in the pull request, replace the links to the issues with their new paths.

## Not possible

Resuming on another machine: the progress only exists in this clone.
