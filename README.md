# mstack

Skills for Claude Code that take one feature from idea to working code, tracked on GitHub Issues and a shared GitHub Projects board.

## Install

```bash
npx skills add marcossp32/mstack -g -a claude-code --skill '*'
```

Drop `-g` to install into the current project's `.claude/skills/` instead of `~/.claude/skills/`. Update later with `npx skills update`.

## Use

```
/m-feature <what you want built>
```

`m-feature` only runs when you type it. It routes the work through the other skills:

```
scan → grilling → docs → plan → build ⇄ check → review ⇄ fix → prove
                          ↑                                      │
                          └────────────────── replan ────────────┘
```

| Skill | Stage | Runs in |
|---|---|---|
| `m-feature` | order, routing, and state on one GitHub map issue | main chat |
| `m-scan` | what the repo already answers: versions, what exists, how it tests and runs | 4 parallel subagents |
| `m-grilling` | asks you only what is hard to undo | main chat |
| `m-research` | vendor limits, timeouts, security guidance, version changes | main chat |
| `m-plan` | ordered build steps, design checks, one issue per step | main chat |
| `m-build` | one step from its issue, method left to the builder, one pull request into the feature branch | subagent |
| `m-review` | a script checks each step; one feature review reports only failures a frozen reproduction demonstrated | main chat, scripts and its own subagents |
| `m-prove` | drives the running app against the Goal and hunts what else broke, then evidences the pull request | subagent |

Every skill except `m-feature` also works on its own.

No skill names a model. Each role asks for a tier — cheap, standard or strong — and `m-feature` resolves the tiers once per feature, writes them on the map, and records what each run cost in the git dir. To map the tiers onto the models you have, write `.mstack/routing.md` in the repo or `~/.mstack/routing.md`; without it, tiers fall back to what the harness offers.

Needs `gh` 2.94.0 or newer, authenticated, in a repo with a GitHub remote and a `main` branch. `m-feature` also needs a GitHub Projects board whose Status field has Todo, In Progress, In Review, Done, Proved and Not verified, with the "Item closed" and "Pull request merged" workflows on; on its first run it adds the `project` scope to `gh` (you approve a one-time code in the browser), and it creates the Stage field and the `needs:human` label that marks where the flow waits for you. The board commands need `jq`. `m-review` needs Python 3 and git 2.31 or newer.

## Inspired by

- [Matt Pocock](https://www.aihero.dev/), whose [skills](https://github.com/mattpocock/skills) make an agent follow a team's process — grilling the request before writing code, and test-first.
- [Addy Osmani](https://addyosmani.com/blog/agentic-engineering/), on the human owning architecture and correctness while the agent implements, and on [agent skills](https://github.com/addyosmani/agent-skills) as quality gates rather than prompts.
- [Lauren Tan](https://github.com/poteto), whose [pstack](https://github.com/cursor/plugins/tree/main/pstack) treats verification as the skill that matters: an agent proves its own work by running the real thing. `m-prove` exists because of that idea.

## Editing

```
skills/<name>/SKILL.md      what the skill does, loaded when it runs
skills/<name>/references/   read only when needed, or by the agents the skill dispatches
skills/<name>/scripts/      run, never read
```

Each folder installs on its own, so a skill never links outside itself. The step issue template lives in both `m-plan/SKILL.md` and `m-feature/references/github.md`: change them together. So do the board card commands, in `m-feature/references/github.md`, `m-plan`, `m-build` and `m-prove`, and the Status, Stage and label names, which also appear in `m-feature/SKILL.md` and in this README.

Try an install from the working tree before pushing:

```bash
npx skills add . --list
```

## License

[MIT](LICENSE)
