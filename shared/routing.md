# Routing

Which model runs each role. No skill names a model: a role says what its work needs, a catalogue the human owns says what this harness offers, and a ledger of finished runs says what that cost.

Price per token does not decide this. A stronger model at low effort can use fewer tokens, fewer retries and less wall time than a weaker one at high effort: one vendor measured a top model at medium effort matching the score of its mid model while using [76% fewer output tokens](https://www.anthropic.com/news/claude-opus-4-5). What counts is the cost of a run the flow accepted.

# Tiers

Three, never a model name: **cheap** the quickest model the harness offers, **strong** its most capable, **standard** the one between.

# The catalogue

`.mstack/routing.md` in the repo, else `~/.mstack/routing.md`. One line per tier:

```
<tier> · <what the harness is passed as the model> · <efforts it takes, lowest first | none> · <relative price, cheap = 1>
```

No catalogue: pass the tier's model as the harness names it, take the effort the session runs at, and say so in the Routing line. Where the harness sets effort only in an agent definition and none exists for that effort, the effort is the session's: record what was used, not what was asked for.

A tier the harness rejects: dispatch again inheriting the session's model, and record `inherit`.

# What each role needs

`checked after` is the exact signal that judges this role's output later. A role with one can start lower and be escalated by that signal. A role with none is the last judge of its own work and starts strong.

| Role | Judgement | Cost of a mistake | Volume | Checked after |
|---|---|---|---|---|
| scan A | low | low | low | grilling, by the human |
| scan B–D | medium | low | high | plan and build hitting the repo |
| research | medium | medium | medium | review checks the numbers |
| build | medium | the undo verdict | high | review |
| review | high | high | medium | none |
| prove supervisor | high | high | low | none |
| Q1, requirements | low | low | high | the supervisor judges the evidence |
| Q2, what else broke | high | medium | high | the supervisor judges the evidence |

# Choosing

1. **The ledger decides when it can.** Three or more runs of this role on an option: take the cheapest option whose accepted share equals the best option's. Fewer: rule 2.
2. **No data: strong tier at the lowest effort the catalogue lists.** Raise the effort before dropping a tier; the effort is the first knob ([OpenAI: the lowest effort that holds quality](https://developers.openai.com/api/docs/guides/reasoning), [Anthropic: sweep effort again for each new model](https://platform.claude.com/docs/en/build-with-claude/effort)).
3. **A role with no check after never goes below strong**, whatever the ledger or the budget says. Review, the prove supervisor and a build whose undo verdict is hard.
4. **A role with a check after starts one tier down and is escalated by its signal**, never by an impression: CHANGES REQUIRED, a build with no PR, a driver error in prove, a rework. Escalate the role for the rest of the feature and record it.
5. **Resolve once, at the start.** Write the line on the map and use it for every dispatch of that role in this feature. Re-resolving mid-flight breaks the prompt cache and makes the runs incomparable.

```
Routing · scan <tier>/<effort> · research <tier>/<effort> · build <tier>/<effort> · review <tier>/<effort> · prove <tier>/<effort> · catalogue <path | none> · budget <share left | unknown>
```

# The ledger

`$(git rev-parse --absolute-git-dir)/mstack/routing.tsv`, appended after every dispatch. It sits in the git dir, so it is never in the checkout and never committed.

```
<date>	<repo>	<role>	<tier>	<effort>	<tokens>	<seconds>	<accepted | rejected | not driven>	<escalations>
```

The outcome is the exact signal, never an impression: PASS or CHANGES REQUIRED from review, verified or not verified from prove, a PR from build, the human's answer for grilling. Tokens and seconds come from what the harness reports for that agent; unknown, leave the field `?`.

# Budget

Ask the harness what is left. Nothing reported is `unknown`, a state of its own, not an excuse to spend.

- **Unknown or ample:** rules 1–5.
- **Tight:** cut work, never judgement. In order: Q2 drives only the risk areas of files the diff touched; the supervisor drives Q1 itself; research only asks the questions scan found a subject for; scan B–D run as one agent.
- **Out:** stop and tell the human what is left to run and what it needs, on the map.

Never pay for the same judgement twice: a second opinion on a passing verdict buys nothing ([self-refinement rarely pays for itself](https://arxiv.org/abs/2504.13359)).
