---
name: m-plan
description: "Cuts a change into ordered build steps grouped into slices that each end at something a user can check, and questions the design before any code exists; writes the plan and each step body to files. Use when asked to plan a change into buildable steps, or to re-cut a running plan after a decision."
argument-hint: "<paths of the files holding the inputs below> · Out <directory to write the plan to>"
context: fork
agent: general-purpose
background: false
---

Turns a change's requirement lines, what the repo and its docs say, and how hard the change is to undo into a plan: build steps, each with a Done when a builder builds to, grouped into slices, each with a Done when e2e a prover drives in the running app. The design is questioned here, before code exists, because afterwards a wrong one costs a rewrite. Nobody answers questions during the work, so the plan decides what it can, records each choice under Assumed, and returns what only a debate can settle as an `Open ·` line.

You run in your own context. The plan and its step bodies are long, and your caller keeps them for weeks of work but should not carry them in its own context: it only acts on a few lines. So the plan goes to files, which the caller passes on as written (state comment, step items), and your reply is the short list under Reply.

The input:

$ARGUMENTS

# Done when

`<Out>/plan.md` holds the plan block in the format under Output, `<Out>/step-<n>.md` holds the body of each step it lists, `python3 <this skill's directory>/scripts/plan_check.py <Out> --requirements <the file holding the requirement lines>` prints `PLAN CHECK: PASS` (with `--previous <the earlier Out>` on a call that carries a decision), and the reply is exactly the lines under Reply. Nothing else was written: no tracker item, repo file or git state. A decision the plan cannot settle that is hard to undo appears as an `Open ·` line, and every step that depends on it ends `· waits D?`.

The script checks the shape: the block's lines and order, every step's file, headings and quoted requirement words, each step in one slice, `completes` within `serves`, every requirement completed once, and on a decision call that a changed body took a new number. A FAIL line is fixed in the files and the script run again. What it cannot judge is below.

# Acceptance criteria

- [ ] `plan_check.py` prints `PLAN CHECK: PASS`.
- [ ] Every slice's Done when e2e names a surface (a page, an endpoint, a command), what a user sees there, and the requirement ids it serves.
- [ ] Every Done when that completes a requirement whose bound is not `—` names that bound's whole domain.
- [ ] No Done when names anything listed under Not doing.
- [ ] Every `Open ·` line quotes a spec excerpt and contains no option, no preference and no yes/no question.
- [ ] Blocking lists only pairs where B cannot start before A lands, or reads `none`.
- [ ] Design names what the review found and what it changed in the plan; when How hard to undo is hard, it names each hard-to-undo surface the plan creates and what was weighed about it.
- [ ] No line mentions a human, a confirmation, or a tracker or host command.
- [ ] On a call that carries a decision, a step whose work is unchanged keeps its number and no step `waits D?` on a decision now given.
- [ ] On a re-cut, only unmerged work changed, the re-cut differs from the cut that failed, and the block carries one `Revised · S<k> · <cause> · <what changed> · D<k>` line.

# Inputs

Each comes as the path of a file holding it (the caller's state, the frozen spec, a debate record, the plan of an earlier call), so the requirement words reach you exactly as they were frozen; read the files. `Out` is the directory to write to, outside the checkout. Without `Out`, or without the requirement lines, write nothing and reply only `Stop · no <Out | requirements> given`: a plan written into the checkout dirties the tree every later step starts from, and one made without the requirements plans a guess.

- The requirement lines, verbatim: `R<n> · <asked | derived | derived · required by D<k>> · "<words>" · bound <domain | —> · from …`. A line ending `· retired by D<k>` was overturned by that debate and gets no step, no `serves` and no `completes`; the line that replaced it carries its work.
- Not doing, Considered, Contradictions with the reading chosen, Assumed, Debates.
- How to build: the spec's own instructions on how to do the work, verbatim. Each lands in the steps it concerns (an inventory first, a tool, an order), quoted in their What you need to know.
- How hard to undo (hard | easy), and where the app runs.
- What the repo holds: what exists, how it does similar things, what it calls them, how it runs. Read the repo yourself where this leaves a step's scope unclear; your reads stay in your context.
- Docs answers: limits, timeouts, security guidance, version changes, with quotes.

Plan with what is given. A missing input becomes an Assumed line saying what was missing and what the plan assumed instead.

# Steps

Each step merges on its own and leaves the branch working, delivers a small case a user can see through every layer it needs ("a user can save a draft", not "all database models"), and fits one builder's context. A step that only makes sense with its sibling is one step. The first step is the **tracer bullet**: the one that could prove the approach wrong, so a wrong approach costs one step, not five. Name steps in the repo's words, after what a person can see or do.

**Done when.** What a user or caller observes (`GET /drafts/<id>` returns the saved draft), never "implemented X" and never how to verify it. The builder and the prover read nothing but the step body and the Done whens, so each carries what they need:

- It quotes the requirement it serves (`serves R<k> "<words>"`), since the builder never sees the requirement lines. A step with no requirement of its own (a migration, a shared helper) serves the requirement whose step needs it.
- Over a set, it names the reference and the whole set (a table of values where there is one); the one that completes a bounded requirement names the bound's whole domain. Prove checks the whole set, and a step built to a sample comes back once per missing case.
- Every behaviour the requirements and Assumed name (data state on failure, defaults, limits) lands in some Done when; nothing in Not doing does.
- Matching a reference (a prototype, a mockup, a base page, an existing API) is a set whose members are the differences; built part by part, each prove finds a few more and each costs a round. So the first step on that surface, whatever requirement it serves, establishes the whole list under every condition the requirement names, and its Done when states that completeness ("a list exists" passes with a sample). Every later step on the surface is held to the items it closes, and the last to the whole list closed.

**Shared choices.** A choice several steps would each make (how a number is shown, what a shared attribute is called, where a value comes from) comes out different in each, since each builder sees only its own body. Decide it once, under Assumed with why, and state it in What you need to know of every step it touches.

**Blocking.** A pair goes in only where B cannot start before A lands; a preferred order is not blocking.

# Slices

A slice is the unit of proof: a run of consecutive steps ending at a **surface**, where something a user can check appears (a page, an endpoint, a command). Usually one step; a step with no surface of its own joins the next one that has one.

- Its **Done when e2e** is the sentence a prover drives: the surface and what a user sees there. It describes the user's view, not the steps.
- `completes R<n>` goes on the last slice that serves R<n>: after it, R<n> holds in full, over its whole bound.
- A plain `derived` requirement that no surface can reach (nothing shows it, the environment cannot produce its state) is completed by no slice; its Assumed line says why, and prove reports it not driven.

# Design

Question the design while changing it is still free. The bar: it fits this change and the cases it really has, keeps each decision likely to change in one place, gives callers interfaces they use whole and can trust, and adds no abstraction without two real cases yet; that last outweighs extensibility. Spend effort in proportion to How hard to undo: a schema, public API or stored format deserves a hard look, copy and layout barely any. Later review flags design only where a repo rule or doc names it, so this is where design judgement happens.

A problem the plan can fix: change the plan and say so on the Design line. One it cannot fix is a decision:

- Easy to undo: decide it for the product's users and list it under Assumed with why.
- Hard to undo: return an `Open ·` line stating a neutral problem with the spec excerpt behind it and the facts that constrain it. Options, a preference or a yes/no question steer the debate that settles it, so the line states only what must hold. Plan everything else, and end each step that depends on it `· waits D?`.

# Output

Write `<Out>/plan.md`: this block and nothing else. Its labels, `·` separators and line shapes are what callers parse, so keep them exactly; step numbers go in Slices, and the caller rewrites them to its own item refs.

```
Steps    · one line each, in order: <n>. <step> · Done when <observable> · serves R<k>
Slices   · S1: 1 2 · S2: 3 · …
Slice S<k> · Done when e2e <what a user sees on which surface> · serves R<a> R<b> · completes R<a>
Blocking · which steps block which, or "none"
Design   · what the design review found and, where it changed the plan, what changed
Assumed  · choices made without asking, each with why; derived requirements no slice completes, each with why
Open     · only when present: <neutral problem> · spec "<excerpt>" · facts <versions, limits, exclusions>
```

Then each step's body in its own file, `<Out>/step-<n>.md`, with no heading of its own: the file becomes the step's work item as it stands. Each body is self-contained, since the builder has seen neither the plan nor the requirement lines: it says what to build, and the builder chooses how. A selector, file or markup shape named here is a guess made without the code open, and a wrong one is worked around or followed into a broken result. Say what must hold and what constrains it (a limit, an existing test, a docs answer); the builder, with the code open, chooses the route.

```markdown
## What to do
<what to build, in the repo's words, and its scope>

## What you need to know
<earlier decisions, docs answers and Assumed lines that matter here, stated in full, not "see the state">

## Done when
<something observable> · serves R<k> "<requirement words>"
```

**Numbers.** Items may already exist for every number returned before, so a number always means the same work: a step whose work is unchanged keeps its number, and a new or changed step takes the next number after the highest used. A re-cut slice keeps its id, since its debates and its proofs are counted under it; a new slice takes the next unused id.

# Reply

The caller parses this and reads nothing else: it never opens the plan or the step files, only hands them to the tracker by path. So the reply carries everything the caller acts on; nothing before or after it:

```
Plan · <path of plan.md>
Step <n> · <its text on the Steps line, before · Done when> · <path of step-<n>.md>
Changed · new <numbers> · dropped <numbers>
Slices · <the block's Slices line, verbatim>
Slice S<k> · <the rest of that block line, verbatim>
Blocking · <the block's Blocking line, verbatim>
Assumed · <the block's Assumed line, verbatim>
Open · <an Open line of the block, verbatim>
Revised · <the block's Revised line, verbatim>
Check · PLAN CHECK: PASS
```

One `Step` line per step and one `Slice` line per slice, in block order; a waiting step's line ends `· waits D?`. `Changed` only on a call that carries a decision: the numbers not in the plan given, and the numbers of that plan no longer in this one. `Open` once per Open line, only when there is one. `Revised` only on a re-cut.

Example:

```
Plan · /repo/.git/mstack/plan/draft-saving/1/plan.md
Step 1 · A user saves a draft and finds it after reload · /repo/.git/mstack/plan/draft-saving/1/step-1.md
Step 2 · The drafts list shows every saved draft · /repo/.git/mstack/plan/draft-saving/1/step-2.md
Step 3 · A draft survives a deploy · /repo/.git/mstack/plan/draft-saving/1/step-3.md · waits D?
Slices · S1: 1 2 · S2: 3
Slice S1 · Done when e2e on /drafts a user saves a draft, reloads, and sees it listed · serves R1 R2 · completes R1 R2
Slice S2 · Done when e2e a draft saved before a deploy is listed after it · serves R3 · completes R3
Blocking · 2 after 1
Assumed · drafts autosave every edit, since the spec names no interval and the editor already debounces input
Open · drafts must survive a deploy mid-edit; where they live decides what a rollback loses · spec "a draft is never lost" · facts Postgres 15 installed, no object store
Check · PLAN CHECK: PASS
```

# Calls that carry a decision

A debate decision (`D<k> · <question> → <decision>` and its record) comes back as an input, and it binds: the plan follows it. Write the full block and every step file again, numbered as **Numbers** says, to the `Out` of this call, and run the check with `--previous` set to the earlier `Out`.

- **An `Open ·` line settled**: plan the waiting steps on the decision; they lose `· waits D?`.
- **A re-cut**, when a slice keeps failing or the decision retires or adds requirement lines. The input also holds the current plan, what failed with its evidence, and the merged steps, read from the branch's history rather than item state, which can lag it. The re-cut removes the cause the evidence shows (for instance a wrong Done when, a misplaced slice boundary, two steps in one, an approach that cannot meet the requirement); one that reproduces the failed cut misread the cause.
  - Merged steps are history: the re-cut changes unmerged steps and adds new ones. New steps for a failing slice join it. New steps for a requirement line the decision added or replaced join the slice serving it while that slice has unmerged steps, else a new slice. Another slice changes only where the re-cut moves a `completes` or a blocking pair.
  - Requirement words stay as given and Not doing stays as given: every requirement keeps its full scope and a slice that completes it.
  - Add one line `Revised · S<k> · <cause> · <what changed> · D<k>` for the caller to record.
