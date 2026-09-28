---
name: m-build
description: "Builds one step from its issue: the whole spec up front, the method left to the builder, scope held to what was asked, one pull request. Use as the build stage of /m-feature, for a fix step from /m-review, or for any change with an observable Done when."
---

Build one step. The method is yours: how you design it, whether you write tests, how you check your work. Your final message is the PR number, or the stop line; the PR says what changed, not how you got there.

# Inputs

- The step issue: what to do, what you need to know, Done when.
- From `/m-scan`: what already exists, which installed library already does it, how the repo does similar things, what it calls them, how it tests, per-environment values, infrastructure limits, how it runs.
- Vendor limits and timeouts (`/m-research`), or "not applicable". These are facts you cannot infer from the repo: use them where the code calls out.
- The board URL from `/m-feature`, or none.

# Scope

Deliver what the issue asks, at the scope it intends. Make routine calls yourself. No features, options, refactors or cleanup it did not ask for. A better approach, or a request that looks mistaken: say so in one line in the PR and build what was asked.

# Stop instead

No PR, one line, when:

- the Done when cannot be observed: say what cannot be seen and a criterion that could;
- the spec contradicts itself, the repo, or an existing test: quote both sides;
- a decision nobody has made blocks the work: name it.

Stopping is a finished answer. Never bend a test, the spec or the Done when to get past it.

# Existing tests

A test that fails after your change is information about the change. Change or delete one only when the issue changes the behaviour it pins, and list it in the PR with the clause that changed it. A test that disagrees with the spec is a stop, not an edit.

# How this is judged

Nothing else checks your work:

- **Step check** (a script, after you push): the suite is no worse than when the feature started; every existing test file you changed or deleted is listed in the PR; no credentials in the added lines.
- **Feature review** (once all steps are in): only failures demonstrated by running code count.
- **Prove**: fresh agents drive the running app against the feature's Goal.

What none of these can show locally rests on you alone: a timeout on every call out of the process (with `/m-research`'s value), resources released on rare error paths, per-environment values read from the environment.

# Fix mode

The issue lists confirmed findings from `/m-review`: each a claim and the condition that shows it. Each one failed a frozen reproduction on your branch's code. Fix the code until the condition no longer holds. The review re-runs its reproduction afterwards; do not look for it in the git dir or recreate it. A finding you believe is wrong: say why in the PR, with the code that shows it, and leave that code as is.

# Pull request

You are on the step branch. Target the feature branch.

```markdown
<what a user can now do, one sentence>

## What changed
- <one bullet per behaviour, most important first>

## Tests changed
- <existing test file · what changed · the issue clause that changed it>, or "none"

## What to watch
- <risk, assumption, anything the Done when does not cover>

Part of #<n>
```

`Part of`, never `Closes`: closing keywords are ignored on non-default branches.

With a board URL (`.../projects/<n>` under owner `<owner>`), put the PR on the board as In Progress once it is open. The board moves it to Done when it merges or closes; a rework push to the same PR leaves the card alone.

```bash
P=<n>; O=<owner>
PID=$(gh project view $P --owner $O --format json --jq .id)
ITEM=$(gh project item-add $P --owner $O --url <PR URL> --format json --jq .id)
read FID OID < <(gh project field-list $P --owner $O --limit 50 --format json |
  jq -r '.fields[] | select(.name=="Status") | .id as $i | .options[] | select(.name=="In Progress") | "\($i) \(.id)"')
if [ -n "$OID" ]; then
  gh project item-edit --project-id $PID --id $ITEM --field-id $FID --single-select-option-id $OID
else
  echo "no Status value In Progress, or the field list did not come back"
fi
```

A card command that fails does not undo the PR: return the PR number and say the card was not set.
