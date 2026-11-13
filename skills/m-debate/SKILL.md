---
name: m-debate
description: Launches five subagents with no context and with different models to investigate the same question separately, and returns their five verdicts (answer, why and source) for whoever uses them to decide. Use for a hard technical question or decision where a single opinion is not enough, when several independent opinions or a sourced second opinion are wanted.
---

# m-debate

## Goal

Give you several independent, sourced answers to a hard question, so you decide on evidence and not on the first idea. The skill does not decide: it investigates and hands you the verdicts. It is a one-off aid, not a phase of any flow.

## Done when

- [ ] The five subagents answered, or it is said which one failed.
- [ ] Each verdict has an answer, a one-line why and a source that can be checked.
- [ ] The delivery is the five blocks and nothing else.

## Acceptance criteria

- **Independent.** Each subagent starts from scratch: it does not see this conversation or the others. That way their answers do not inherit your hypotheses or infect each other.
- **Neutral question.** Whatever you put in the question comes back as the answer. Ask what or how, with no options, no preference and no yes/no.
- **Minimal context.** Only what the question needs to have a correct answer: version, repo path, a real constraint. Each extra detail is a hint that biases.
- **Sourced.** An answer without a checkable source is no use for deciding. If a subagent does not give one, it stays as `no source`.
- **To the point.** Answer, why and source. No extra explanations.

## How to do it

Launch the five in a single message, so they run in parallel, and wait for all of them to finish. They are new agents (`general-purpose`), not forks. Using different models and efforts gives different points of view:

| Verdict | Model | Effort |
|---|---|---|
| V1 | opus | medium |
| V2 | opus | medium |
| V3 | sonnet | high |
| V4 | sonnet | medium |
| V5 | haiku | high |

You pass each one the same thing:

```
Use the m-research skill to answer this question. If you do not have it, investigate in the sources that have authority over the fact (official documentation, code of the installed version, specification) and quote verbatim.

Question · <neutral question>
Context  · <only the essentials>

End with exactly this:
Answer · <one sentence>
Why    · <one line>
Source · <url or file:line> · "<verbatim quote>"
```

## Delivery

The five blocks, in order:

```
V1 · opus · <answer>
Why    · <one line>
Source · <url or file:line> · "<quote>"
```
