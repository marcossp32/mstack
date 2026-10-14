# mstack

Claude Code skills that take one feature from idea to a proven pull request, tracked on GitHub Issues.

You describe what you want. mstack asks only what is hard to undo, plans it in small steps, builds each step in its own pull request, reviews the whole feature, and drives the running app to prove it does what you asked before it opens the final pull request.

- **Proven, not claimed.** Fresh agents that did not write the code drive the running app against your Goal and hunt what else broke. Every verdict cites saved evidence.
- **Tests that pin something.** A script checks each step: the suite is no worse, every test the step changed or loosened is declared, each test it names fails without the change, and no credentials were added.
- **Review that demonstrates.** The feature review reports only failures a frozen reproduction shows on running code.
- **State on GitHub.** One map issue holds the Goal, the decisions and the progress. You can stop and pick up later, or watch it from a project board.

## Contents

- [Install](#install)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [How it works](#how-it-works)
- [Autonomous runs](#autonomous-runs)
- [What you get on GitHub](#what-you-get-on-github)
- [Using a skill on its own](#using-a-skill-on-its-own)
- [Contributing](#contributing)
- [Credits](#credits)
- [License](#license)

## Install

```bash
npx skills add marcossp32/mstack -g -a claude-code --skill '*'
```

This installs into `~/.claude/skills/`. Drop `-g` to install into the current project's `.claude/skills/` instead.

Update with `npx skills update`.

## Requirements

| Tool | Version | Used by |
|---|---|---|
| [Claude Code](https://claude.com/claude-code) | current | all |
| [`gh`](https://cli.github.com/), authenticated | 2.94.0 or newer | `m-feature`, `m-plan`, `m-review`, `m-prove` |
| git | 2.31 or newer | `m-review`, `m-prove` |
| Python | 3.9 or newer | `m-build`, `m-review`, `m-prove` scripts |
| Node.js and npm | any current | `m-prove`, only for changes with a web page |

The repo needs a GitHub remote. `m-prove` drives web pages with [agent-browser](https://github.com/vercel-labs/agent-browser) and installs it globally with npm the first time a change has a page.

Every test run, server and browser script the skills start goes through `contain.py`. When the command ends or is stopped, everything it started ends too: on Windows a job object, on POSIX a process session ended with SIGTERM then SIGKILL, plus a watchdog. `step_check.py`, `prepare.py` and prove first end what earlier runs left in the repo, and orphaned automation browsers. Contained commands get `BROWSER=none` and `PW_TEST_HTML_REPORT_OPEN=never`, so dev servers and test reports do not open your browser. Set `MSTACK_PRIORITY=low` to run them at below-normal priority (off by default: under load it makes timing tests flaky).

Suites and test files have a ceiling, 3 times their last measured run (at least 30 minutes for a suite, 5 for one file). A run that reaches it is reported as not finished, never as a failure.

## Quick start

In a repo with a GitHub remote, open Claude Code and run:

```
/m-feature Add a newsletter signup to the footer that saves the email to the customer list
```

Or point it at an issue:

```
/m-feature #412
```

mstack works through the stages below. It asks you a few questions at the start, shows you the plan, and stops for you only when a decision is yours. At the end you get a pull request into the base branch, marked **Proved** or **Not verified**, with the evidence in its body.

A feature branches from the branch its issue targets, else the default branch.

## How it works

`/m-feature` only runs when you type it. It routes the work through the other skills:

```
scan → grilling → docs → plan → build ⇄ check → review ⇄ fix → prove
                          ↑                                      │
                          └────────────────── replan ────────────┘
```

| Skill | Stage | Runs in |
|---|---|---|
| `m-feature` | Order, routing, and state on one GitHub map issue | Main chat |
| `m-scan` | What the repo already answers: versions, what exists, how it tests and runs | 4 parallel subagents |
| `m-grilling` | Asks you only what is hard to undo, and fixes a Goal that can be watched | Main chat |
| `m-research` | Vendor limits, timeouts, security guidance, version changes, one subagent per source | Main chat |
| `m-plan` | Ordered build steps, design checks, one issue per step | Main chat |
| `m-build` | One step from its issue into one pull request on the feature branch | Subagent |
| `m-review` | A script checks each step; one feature review reports only demonstrated failures | Scripts in main chat; the review in a subagent |
| `m-prove` | Drives the running app against the Goal, hunts what else broke, opens the final pull request | Subagent |

### What each gate checks

**Build.** The builder chooses its own method, with two duties:

- it adds a test that fails without its change (**Pinned by**);
- when the app can be launched, it drives its own Done when once before the pull request (**Driven**), so a mistake visible in the app does not cost a whole prove round.

**Step check** (`m-review/scripts/step_check.py`). After each step is pushed, a script runs on a clean checkout:

| Check | Fails when |
|---|---|
| Suite | More tests fail than when the feature started |
| Tests changed | An existing test file was changed or deleted, or a skip, `.only`, suppression or `\|\| true` was added, without being listed in the pull request |
| Pinned | A test the pull request names under Pinned by does not pass at HEAD, or still passes with the step's code reverted |
| Credentials | An added line looks like a secret |

**Feature review.** Hunter agents look for failures across the whole feature: 1 for a small, easy-to-undo change, 3 otherwise. A finding counts only when a frozen reproduction fails on the branch. Confirmed findings become fix steps.

**Prove.** Two fresh agents drive the running app:

- **Q1** checks each requirement of the Goal, with evidence saved for each verdict.
- **Q2** looks for anything else the change broke, and compares it with the base branch.

Each check Q1 verifies is saved as a **replay**. On a re-prove after a fix, the replays run first, in seconds, and catch what the fix broke.

### Replan

A failing step check, review or prove can trigger a replan: a revised list of steps, shown to you before it builds. A replan needs one of the fixed triggers, never taste. In an interactive run it stops for you at the second replan.

### Models

Each stage asks for a model tier: cheap, standard or strong. Strong models go where a change is hard to undo and where nothing checks the agent's work, such as Q2's hunt in prove. Map the tiers in your `~/.claude/CLAUDE.md` if you want specific models:

```markdown
# Models

When a skill asks for a model tier, pass it to the Agent tool as:

- cheap: `haiku`
- standard: `sonnet`
- strong: `opus`
```

## Autonomous runs

Run without being asked anything:

```
/m-feature --auto #412 · store password 1234 · budget 3 replans
```

Saying you are away, or telling it to decide everything, starts the same mode. Everything else stays the same, except:

- **Every wait takes the recommendation.** Each decision goes on the map under **Assumed**, with its reason. That section is what you read when you come back.
- **Hard-to-undo decisions are researched first.** `/m-research` quotes what the standard or the vendor's docs recommend, and the sources go beside the decision.
- **Requirements keep their full scope.** A failing requirement is never narrowed, and nothing is added to Not doing after the plan. Only a requirement mstack worded itself may be reworded, never your own words. The old wording stays on the map and the final pull request stays a draft for you to accept it.
- **A step that may contain credentials is never merged.** It stays open with `needs:human` and is listed under To merge in the closing message.

It stops, leaving the pull request as Not verified with `needs:human` on the map, when:

- the same requirement fails two proves in a row and research finds no documented alternative left to try;
- two re-proves in a row fail only on new breaks, or prove has triggered three replans;
- a budget you set (money, time or rounds) is spent.

When it stops, its message opens with `Stopped ·` and the one question only you can answer.

**Credentials** you pass, such as a store password or a test account, are used only to drive the app. They are never written to an issue, a comment or a pull request.

**Budgets** are recorded on the map under Settled up front. Set one: without it, only the first two stop rules apply.

## What you get on GitHub

| Item | What it holds |
|---|---|
| Map issue, labelled `feature:map` | Goal, Settled up front, Assumed, Not doing, steps and replans |
| Step issues, labelled `build` | One per step, with its Done when, linked as sub-issues of the map |
| Step pull requests | One per step, into `feature/<name>`, each with Tests changed, Driven and Pinned by |
| Final pull request | Into the base branch, with a **Proved** or **Not verified** verdict, its evidence and a **How hard to undo** line |

Whichever issue is waiting on you is labelled `needs:human`.

A GitHub Projects board is optional, and the skills never touch it. To follow features there:

1. Turn on the board's built-in **Auto-add to project** workflow, filtered on those labels.
2. Keep **Item closed** and **Pull request merged** on, so cards reach Done by themselves.

## Using a skill on its own

Every skill except `m-feature` also works outside it, and Claude Code loads it when your request matches its description. For example:

| Ask | Skill |
|---|---|
| "Prove this branch does what issue #88 asks" | `m-prove` |
| "Review this branch before I merge it" | `m-review` |
| "Grill me on this design before I build it" | `m-grilling` |
| "What are Stripe's webhook timeouts and retry rules?" | `m-research` |

## Contributing

Each skill is one folder:

```
skills/<name>/SKILL.md      what the skill does, loaded when it runs
skills/<name>/references/   read only when needed, or by the agents the skill dispatches
skills/<name>/scripts/      run, never read
skills/<name>/agents/       display metadata for other agent hosts
```

Each folder installs on its own, so a skill never links outside itself. Some text is repeated across skills, so change these together:

- The step issue template lives in `m-plan/SKILL.md` and `m-feature/references/github.md`.
- The label names live in those files, in `m-feature/SKILL.md` and in this README.
- `scripts/contain.py` is the same file in `m-build`, `m-prove` and `m-review`; CI fails when the copies differ.

The skills follow the writing-for-agents conventions: short rules, each with its reason, and no rule that does not change what the agent does.

Try an install from the working tree before pushing:

```bash
npx skills add . --list
```

## Credits

- [Matt Pocock](https://www.aihero.dev/), whose [skills](https://github.com/mattpocock/skills) make an agent follow a team's process: grilling the request before writing code, and test-first.
- [Addy Osmani](https://addyosmani.com/blog/agentic-engineering/), on the human owning architecture and correctness while the agent implements, and on [agent skills](https://github.com/addyosmani/agent-skills) as quality gates rather than prompts.
- [Lauren Tan](https://github.com/poteto), whose [pstack](https://github.com/cursor/plugins/tree/main/pstack) treats verification as the skill that matters: an agent proves its own work by running the real thing. `m-prove` exists because of that idea.

## License

[MIT](LICENSE)
