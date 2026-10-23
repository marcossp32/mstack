# State

The state is one tracker item (label `feature:map`) plus one item per step (label `build`), written only through the tracker adapter. With the pushed `feature/<name>`, it is everything a new session on another machine has, so anything a resume needs is written here before it is relied on. This file holds:

- Rules: how the state is written and read
- State body: its headings, in order, and the Slice lines resume reads
- Step item body: the three headings the builder reads
- Branches: the feature and step branches, and what changes each
- Where results land: each stage's result and its destination
- Resume points: where an open slice or Closing picks up

## Rules

- `tracker write-state` replaces the whole body: read it first and write it all back, or another section is lost.
- The body holds current truth; reports, records and evidence summaries go in comments, which append. `read-state` returns each comment headed `<!-- comment <id> <date> -->`.
- With the `md` tracker the state lives under `<git common dir>/mstack/md/<feature>/`, never in the work tree; only issues reach the repo, through `tracker publish-issues` at Closing.
- `tracker link <a> <b>` between two steps of this state means a is blocked by b; any other pair is a plain related link.
- Write what a reviewer can open and act on: links rather than local paths, results rather than a stage's internal reasoning, a credential's `MSTACK_SECRET_<NAME>` name and never its value.

## State body

Created at Start with Spec, Base and How hard to undo filled, other headings empty. Headings in this order; other skills read them by name:

```markdown
## Requirements
<m-requirements' lines, verbatim: R<n> · <asked | derived | derived · required by D<k>> · "<words>" · bound <domain | —> · from "<spec excerpt>"[ + "<excerpt>"] | from R<m>. Ids never renumber or get reused; words never change; a changed bound keeps `was: <old bound>` beside it; a line a debate overturned ends `· retired by D<k>` and is not proved>

## Spec
<spec ref · url> · frozen sha256 <hash> · <date frozen> · copy at <git common dir>/mstack/spec/<name>.md and in a state comment
<Spec changed · <date>   only when a later read-spec hash differs>

## Base
<base branch> · feature/<name> · source <spec ref>

## How hard to undo
<hard | easy> · <why> · <provisional | after scan | after docs | D<k>>

## Where it runs
<platform and what it limits, from scan Q8>

## Assumed
<decisions made without a debate, each with why and its sources: m-requirements' easy decisions, m-plan's, yours, a changed bound>

## Decided
Slices · S1: <step ref> <step ref> · S2: <step ref> · …
<one line per slice: open while in progress, closed when done (Slice lines below)>

## Debates
<D<k> · <question> → <decision> · record: state comment · <understand | plan | S<k> | final>>

## Sources
<links m-research and the debates used>

## Considered
<what was thought of and left out, with why. Excludes nothing from review or prove>

## Not doing
<only what the spec itself excludes. Nothing joins it later>

## Contradictions
<each: the conflicting excerpts · the reading chosen · why · issue <ref>>

## Open decisions
<hard-to-undo decisions the spec leaves open, from m-requirements and m-plan; each gets `→ D<k>` once debated, then the list stays as an index>
```

### Slice lines

Resume reads these, so rewrite the open line as each point finishes:

```
S<k> · open · start <sha> · <steps merged: refs> · quality <pending | F<n>… open | clean> · prove <pending | fix round <n> | verified> · debates <n>
S<k> · verified · <what a user can now do, one sentence> · evidence <verdict comment date> · replays S<k> R<n>…
S<k> · not verified · <why, one sentence> · <D<a> D<b>> · open steps <refs | none>
```

## Step item body

Exactly the `Step <n>` body `m-plan` returned; a fix step gets the same three headings, because m-build reads them:

```markdown
## What to do
<for a fix: each F<n> line, each prove failure (Done when or requirement, value seen, evidence excerpt), or the step check output>

## What you need to know
<earlier decisions in full, never "see the state"; a debate decision that led here, verbatim>

## Done when
<observable> · serves R<k> "<requirement words>"
```

## Branches

```
<base>
 └── feature/<name>                from <base> at Start; pushed after every merge; the PR's head
      └── step/<name>-<n>          one per step, cut from origin/feature/<name>; local only; merged locally, then deleted
      └── step/<name>-fix-<n>      every fix (quality, slice prove, final prove), cut the same way
```

- A branch name is never reused, locally or on the remote: take the next number. A reused name mixes two attempts' history.
- `<base>` changes only through the final PR, and `feature/<name>` only through step merges: nothing is committed on it directly, except md's `publish-issues` commit at Closing. Every change then passes a step check.

## Where results land

| Result | Destination |
|---|---|
| frozen spec | `<git common dir>/mstack/spec/<name>.md` and one state comment |
| scan, docs, plan block, quality review, slice prove verdict | one state comment each (docs links also under Sources) |
| requirements | state body: Requirements, Not doing, Considered, Contradictions, Open decisions, Assumed |
| debate | the `D<k>` line under Debates; the `## D<k> · record` block as a state comment; a revision's `Revised ·` line beside it and on the slice line |
| build | commits on the step branch; notes at `<git common dir>/mstack/steps/<step branch with / replaced by ->.md` |
| step check not PASS | a comment on the step item |
| merge | the merge commit (notes' first line, `Part of <step ref>`); the step item closed with the notes' What changed |
| final prove | the PR body; issue drafts become issues |
| contradiction, found-by-prove | issues, linked from the state and the PR |

## Resume points

Inside an open slice, the first of these that holds:

1. An open step item with no merge commit naming it on `origin/feature/<name>`: step check its local step branch when one exists, else cut it again and rebuild.
2. Every step merged, quality not `clean`: quality review (a re-review when open findings are listed).
3. Prove not `verified`: slice prove.
4. Else close the slice line.

At Closing, run the final prove again (replays make it cheap), and edit the PR `host find-pr` finds rather than opening a second.
