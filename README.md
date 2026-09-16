# mstack

Skills for Claude Code that take one feature from idea to working code, tracked on GitHub Issues.

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
scan → grilling → docs → plan → build ⇄ review → prove
                          ↑                          │
                          └───────── replan ─────────┘
```

| Skill | Stage | Runs in |
|---|---|---|
| `m-feature` | order, routing, and state on one GitHub map issue | main chat |
| `m-scan` | what the repo already answers: versions, what exists, how it tests and runs | 4 parallel subagents |
| `m-grilling` | asks you only what is hard to undo | main chat |
| `m-research` | vendor limits, timeouts, security guidance, version changes | main chat |
| `m-plan` | ordered build steps, design checks, one issue per step | main chat |
| `m-build` | one step, test-first, one pull request into the feature branch | subagent |
| `m-review` | two passes over one step's diff, ending on PASS or CHANGES REQUIRED | subagent |
| `m-prove` | drives the running app against the Goal and hunts what else broke, then evidences the pull request | subagent |

Every skill except `m-feature` also works on its own.

No skill names a model. Each role asks for a tier — cheap, standard or strong — and `m-feature` resolves the tiers once per feature, writes them on the map, and records what each run cost in the git dir. To map the tiers onto the models you have, write `.mstack/routing.md` in the repo or `~/.mstack/routing.md`; without it, tiers fall back to what the harness offers.

Needs `gh` 2.94.0 or newer, authenticated, in a repo with a GitHub remote and a `main` branch.

## Inspired by

- [Matt Pocock](https://www.aihero.dev/), whose [skills](https://github.com/mattpocock/skills) make an agent follow a team's process — grilling the request before writing code, and test-first.
- [Addy Osmani](https://addyosmani.com/blog/agentic-engineering/), on the human owning architecture and correctness while the agent implements, and on [agent skills](https://github.com/addyosmani/agent-skills) as quality gates rather than prompts.
- [Lauren Tan](https://github.com/poteto), whose [pstack](https://github.com/cursor/plugins/tree/main/pstack) treats verification as the skill that matters: an agent proves its own work by running the real thing. `m-prove` exists because of that idea.

## Editing

```
skills/<name>/          one folder per skill, installed on its own
shared/                 documents more than one skill reads
scripts/sync-shared.mjs copies shared/ into each reader's references/
```

A skill cannot link to `../` — `npx skills` installs each folder separately, so the target would not exist. Edit the file in `shared/`, never the copy under `references/`, then:

```bash
node scripts/sync-shared.mjs
```

CI runs it with `--check` and fails on a copy that drifted.

Try an install from the working tree before pushing:

```bash
npx skills add . --list
```

## License

[MIT](LICENSE)
