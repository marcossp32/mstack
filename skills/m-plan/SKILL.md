---
name: m-plan
description: "Cuts a change into ordered build steps grouped into slices that each end at something a user can check, and questions the design before any code exists. Use when asked to plan a change into buildable steps, or to re-cut a running plan after a decision."
---

Turns a change's requirement lines, what the repo and its docs say, and how hard the change is to undo into a plan: build steps, each with a Done when a builder builds to, grouped into slices, each with a Done when e2e a prover drives in the running app. The design is questioned here, before code exists, because afterwards a wrong one costs a rewrite. Nobody answers questions during the work, so the plan decides what it can, records each choice under Assumed, and returns what only a debate can settle as an `Open ·` line. The reply is the whole output: whoever called creates the work items from it.

# Done when

The reply holds one plan block in the format under Output, followed by one `Step <n>` body per step it lists, and nothing else was written anywhere. A decision the plan cannot settle that is hard to undo appears as an `Open ·` line, and every step that depends on it ends `· waits D?`.

# Acceptance criteria

- [ ] The block has the lines `Steps`, `Slices`, one `Slice S<k>` per slice, `Blocking`, `Design`, `Assumed`, in that order, and `Open` only when there is one; each uses the labels and `·` separators of the Output format.
- [ ] Every step line ends in `serves R<k>` (then `· waits D?` where it waits), naming a requirement id present in the input and not `retired by D<k>`.
- [ ] Every step body has the three headings of the Output format, and its `## Done when` ends `serves R<k> "<words>"` with the words verbatim from R<k>.
- [ ] Every step number appears in exactly one slice; no slice is empty.
- [ ] Every slice's Done when e2e names a surface (a page, an endpoint, a command), what a user sees there, and the requirement ids it serves.
- [ ] Every `asked` and `derived · required by D<k>` requirement not `retired by D<k>` is completed by exactly one slice.
- [ ] Every plain `derived` requirement not `retired by D<k>` is completed by exactly one slice, or an Assumed line names it and why no slice can reach it.
- [ ] A slice's `completes` ids are a subset of its `serves` ids, and no later slice serves a completed id.
- [ ] Every Done when that completes a requirement whose bound is not `—` names that bound's whole domain.
- [ ] No Done when names anything listed under Not doing.
- [ ] Every `Open ·` line quotes a spec excerpt and contains no option, no preference and no yes/no question.
- [ ] Blocking lists only pairs where B cannot start before A lands, or reads `none`.
- [ ] Design names what the review found and what it changed in the plan; when How hard to undo is hard, it names each hard-to-undo surface the plan creates and what was weighed about it.
- [ ] No line mentions a human, a confirmation, or a tracker or host command.
- [ ] On a call that carries a decision, a step whose work is unchanged keeps its number, every new or changed step takes a number after the highest used, and no step `waits D?` on a decision now given.
- [ ] On a re-cut, only unmerged work changed, the re-cut differs from the cut that failed, and the block carries one `Revised · S<k> · <cause> · <what changed> · D<k>` line.

# Inputs

- The requirement lines, verbatim: `R<n> · <asked | derived | derived · required by D<k>> · "<words>" · bound <domain | —> · from …`. A line ending `· retired by D<k>` was overturned by that debate and gets no step, no `serves` and no `completes`; the line that replaced it carries its work.
- Not doing, Considered, Contradictions with the reading chosen, Assumed, Debates.
- How hard to undo (hard | easy), and where the app runs.
- What the repo holds: what exists, how it does similar things, what it calls them, how it runs.
- Docs answers: limits, timeouts, security guidance, version changes, with quotes.

Plan with what is given. A missing input becomes an Assumed line saying what was missing and what the plan assumed instead.

# Steps

Each step merges on its own and leaves the branch working, delivers a small case a user can see through every layer it needs ("a user can save a draft", not "all database models"), and fits one builder's context. A step that only makes sense with its sibling is one step. The first step is the **tracer bullet**: the one that could prove the approach wrong, so a wrong approach costs one step, not five. Name steps in the repo's words, after what a person can see or do.

**Done when.** What a user or caller observes (`GET /drafts/<id>` returns the saved draft), never "implemented X" and never how to verify it. The builder and the prover read nothing but the step body and the Done whens, so each carries what they need:

- It quotes the requirement it serves (`serves R<k> "<words>"`), since the builder never sees the requirement lines. A step with no requirement of its own (a migration, a shared helper) serves the requirement whose step needs it.
- Over a set, it names the reference and the whole set (a table of values where there is one); the one that completes a bounded requirement names the bound's whole domain. Prove checks the whole set, and a step built to a sample comes back once per missing case.
- Every behaviour the requirements and Assumed name (data state on failure, defaults, limits) lands in some Done when; nothing in Not doing does.

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

Return this block. Its labels, `·` separators and line shapes are what callers parse, so keep them exactly; step numbers go in Slices, and the caller rewrites them to its own item refs.

```
Steps    · one line each, in order: <n>. <step> · Done when <observable> · serves R<k>
Slices   · S1: 1 2 · S2: 3 · …
Slice S<k> · Done when e2e <what a user sees on which surface> · serves R<a> R<b> · completes R<a>
Blocking · which steps block which, or "none"
Design   · what the design review found and, where it changed the plan, what changed
Assumed  · choices made without asking, each with why; derived requirements no slice completes, each with why
Open     · only when present: <neutral problem> · spec "<excerpt>" · facts <versions, limits, exclusions>
```

Then one body per step, headed `Step <n>`. Each is self-contained, since the builder has seen neither the plan nor the requirement lines: it says what to build, and the builder chooses how.

```markdown
## What to do
<what to build, in the repo's words, and its scope>

## What you need to know
<earlier decisions, docs answers and Assumed lines that matter here, stated in full, not "see the state">

## Done when
<something observable> · serves R<k> "<requirement words>"
```

**Numbers.** Items may already exist for every number returned before, so a number always means the same work: a step whose work is unchanged keeps its number, and a new or changed step takes the next number after the highest used. A re-cut slice keeps its id, since its debates and its proofs are counted under it; a new slice takes the next unused id.

# Calls that carry a decision

A debate decision (`D<k> · <question> → <decision>` and its record) comes back as an input, and it binds: the plan follows it. Return the full block again, numbered as **Numbers** says.

- **An `Open ·` line settled**: plan the waiting steps on the decision; they lose `· waits D?`.
- **A re-cut**, when a slice keeps failing or the decision retires or adds requirement lines. The input also holds the current plan, what failed with its evidence, and the merged steps, read from the branch's history rather than item state, which can lag it. The re-cut removes the cause the evidence shows (for instance a wrong Done when, a misplaced slice boundary, two steps in one, an approach that cannot meet the requirement); one that reproduces the failed cut misread the cause.
  - Merged steps are history: the re-cut changes unmerged steps and adds new ones. New steps for a failing slice join it. New steps for a requirement line the decision added or replaced join the slice serving it while that slice has unmerged steps, else a new slice. Another slice changes only where the re-cut moves a `completes` or a blocking pair.
  - Requirement words stay as given and Not doing stays as given: every requirement keeps its full scope and a slice that completes it.
  - Add one line `Revised · S<k> · <cause> · <what changed> · D<k>` for the caller to record.
