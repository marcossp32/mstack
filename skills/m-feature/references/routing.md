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

`checked after` is the exact signal that judges this role's output later. A role with one can start lower and be escalated by that signal. A role with none is the last judge of its own work and starts strong. `starts at` is the tier a role takes with no ledger data.

| Role | Judgement | Cost of a mistake | Volume | Checked after | Starts at |
|---|---|---|---|---|---|
| scan A | low | low | low | grilling, by the human | cheap |
| scan B–D | medium | low | high | plan and build hitting the repo | standard |
| research | medium | medium | medium | the `/m-research` supervisor, who finds every number on its page | standard |
| build | medium | the undo verdict | high | step check, review gate, prove | standard; strong when the undo verdict is hard |
| review hunters | high | high | medium | none: nothing checks what they miss | strong |
| repro writer | medium | low | high | the gate | standard |
| prove supervisor | high | high | low | none | strong |
| Q1, requirements | low | low | high | the supervisor judges the evidence | cheap with a run recipe; strong when the launch is improvised |
| Q2, what else broke | high | medium | high | the supervisor judges the evidence | strong: inventing routes is its job |

# Choosing

1. **The ledger decides when it can.** Three or more runs of this role on an option: take the cheapest option whose accepted share equals the best option's. Fewer: rule 2.
2. **No data: the role's `starts at` tier, at the lowest effort the catalogue lists.** Raise the effort before raising the tier; the effort is the first knob ([OpenAI: the lowest effort that holds quality](https://developers.openai.com/api/docs/guides/reasoning), [Anthropic: sweep effort again for each new model](https://platform.claude.com/docs/en/build-with-claude/effort)).
3. **A role with no check after never goes below strong**, whatever the ledger or the budget says. Review hunters, the prove supervisor and a build whose undo verdict is hard.
4. **A role with a check after is escalated only by its signal**, never by an impression: a failed step check, a build with no PR, a `still-failing` recheck, a driver error in prove. Escalate the role one tier for the rest of the feature and record it.
5. **Resolve once, at the start.** Write the line on the map and use it for every dispatch of that role in this feature. Re-resolving mid-flight breaks the prompt cache and makes the runs incomparable. Two exceptions, each recorded as a dated line under the Routing heading: an escalation (rule 4), and build, whose tier follows the undo verdict: at the start it uses the provisional verdict; when the verdict changes after scan, after docs or in a replan, re-resolve build only.

```
Routing · scan A <tier>/<effort> · scan B–D <tier>/<effort> · research <tier>/<effort> · build <tier>/<effort> · hunt <tier>/<effort> · repro <tier>/<effort> · prove <tier>/<effort> · Q1 <recipe tier>|<improvised tier>/<effort> · Q2 <tier>/<effort> · catalogue <path | none> · budget <share left | unknown>
```

# The ledger

`$(git rev-parse --path-format=absolute --git-common-dir)/mstack/routing.tsv`, appended after every dispatch. It sits in the git dir, so it is never in the checkout and never committed.

```
<date>	<repo>	<role>	<tier>	<effort>	<tokens>	<seconds>	<accepted | rejected | not driven>	<escalations>
```

The outcome is the exact signal, never an impression: PASS or FAIL from the step check, confirmed or dead from the gate for a repro writer, verified or not verified from prove, a PR from build, the human's answer for grilling. Tokens and seconds come from what the harness reports for that agent; unknown, leave the field `?`.

# Budget

Ask the harness what is left. Nothing reported is `unknown`, a state of its own, not an excuse to spend.

- **Unknown or ample:** rules 1–5.
- **Tight:** cut work, never judgement. In order: Q2 drives only the risk areas of files the diff touched; the supervisor drives Q1 itself; research only asks the questions scan found a subject for; review runs 2 hunters instead of 3; scan B–D run as one agent.
- **Out:** stop and tell the human what is left to run and what it needs, on the map.

Never pay for the same judgement twice: a second opinion on a passing verdict buys nothing ([self-refinement rarely pays for itself](https://arxiv.org/abs/2504.13359)).
