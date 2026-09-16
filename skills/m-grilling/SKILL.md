---
name: m-grilling
description: "Asks the human only the hard-to-undo decisions that the repo and docs cannot settle. Use as the grilling stage of /m-feature, or to pin down one decision before a build. For open-ended stress-testing of an idea, use grilling instead."
---

Interview the human in the main chat, only about decisions that are hard to undo. Decide the rest yourself. Everything you write follows [`references/writing.md`](references/writing.md).

Inputs: the feature as asked · the `/m-scan` report, read before drafting any question · the undo verdict.

# What to ask

Ask only when all three hold:

1. It is an open decision: not a fact (facts come from scan or `/m-research`), not already answered.
2. It is hard to undo, or decides something that is.
3. Only the human knows it: intent, priorities, unwritten constraints.

Otherwise decide it and state it, one line each, so they can object. Do not ask permission.

Default questions:

1. Where does it deploy (cloud, on-prem, container, serverless)? Only if scan found no `Dockerfile`, Kubernetes manifest, `serverless.yml`, Terraform or CI deploy config; otherwise state what it found in one line.
2. Where does this module end? Only if hard to undo and scan (Q2, Q4) found no precedent.
3. If it fails halfway, what state is the data left in? Only if it writes data.

When the verdict is easy to undo, decide 2 and 3 yourself.

The defaults are a minimum. Also ask any hard-to-undo decision a scan finding raises, e.g. it already exists → reuse it or build beside it; the infrastructure caps it → synchronous or deferred; an output others will depend on.

# Rounds

Ask every question whose prerequisites are settled, together in one round; questions that depend on an open answer wait for the next. Expect one round with one question. At round four, stop and re-test each open question against the three conditions.

```
❓ **Q1 — <title>**: <one or two lines; options as bullets>

➡️ <recommended answer>

---

❓ **Q2 — <title>**: <question>

➡️ <recommended answer>
```

- Always give a recommendation, so "yes" is a complete reply.
- Before writing a recommendation, find the clauses of the feature as asked that it touches. Quote any it contradicts under the ➡️ line (`breaks "<clause>"`); a recommendation that breaks one is not the recommendation.
- Plain words, short sentences; the repo's own terms are fine. Describe the consequence ("keep the old records or overwrite them?"), not the concept.
- One question per question. Needing more than two lines means it is several questions, or not yet understood.
- Cut any question whose answer would not change the work.

# Finish

Stop when nothing hard to undo is open. Confirm you share an understanding; work starts when the human says so.

Hand back:

- **Goal**: 1–2 lines of what done looks like, concrete enough to watch: what comes out, in what shape, what the empty case does. Confirm it with the human together with your last question. `/m-prove` judges the feature against it.
- Where it runs, and what that limits.
- Module boundary and data state on failure, if asked.
- Decisions you made, one line each, checked against the request the same way.
- Not doing: what the human ruled out. If it did not come up, ask, even though it fails the three conditions: review measures scope against it.

Goal, Where it runs and Not doing go under their map headings; the rest under Settled up front.
