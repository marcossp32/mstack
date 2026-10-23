# mstack

Claude Code skills that turn a reviewed spec into a pull request proved in the running app, unattended.

You hand mstack a spec. Nobody answers questions: it extracts the requirements, plans the work in slices a user can check, and for each slice builds, reviews the code against your repo's rules and the official docs, and drives the running app to prove the slice works. At the end it proves the whole feature again for regressions and opens one pull request, marked **Proved** or **Not verified**.

- **Proof driven.** A change is done when the end-to-end proof in the running app passes. Fresh agents that did not write the code drive it, and every verdict cites saved evidence.
- **Review with sources.** The quality review reports a finding only with its source: a rule of your repo (`file:line`) or a verbatim quote from the official docs for the installed version.
- **Tests that pin something.** A script checks each step: the suite is no worse, every test the step changed or loosened is declared, each test it names fails without the change, and no credentials were added.
- **Unattended.** Where a person would once have been asked, mstack decides and records why, runs a debate between five fresh agents for hard-to-undo decisions, or delivers the pull request as Not verified. It never waits.
- **Works with your tools.** Specs and state live in GitHub Issues, Jira or plain markdown files; the pull request opens on GitHub, GitLab or Bitbucket.

## Contents

- [Install](#install)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [How it works](#how-it-works)
- [Unattended by design](#unattended-by-design)
- [Using a skill on its own](#using-a-skill-on-its-own)
- [Contributing](#contributing)
- [Credits](#credits)
- [License](#license)

## Install

```bash
npx skills add marcossp32/mstack -g -a claude-code --skill '*'
```

This installs into `~/.claude/skills/`. Drop `-g` to install into the current project's `.claude/skills/` instead. Install all skills together: `m-feature` and `setup-mstack` use the others' files.

Update with `npx skills update`.

## Requirements

| Tool | Version | Used by |
|---|---|---|
| [Claude Code](https://claude.com/claude-code) | current | all |
| git | 2.31 or newer | all |
| Python | 3.9 or newer | `m-build`, `m-review`, `m-prove`, `m-requirements`, `setup-mstack` scripts |
| The tracker's and host's CLI, logged in | see `m-feature/references/trackers/` and `hosts/` | `m-feature`, `setup-mstack` |
| Node.js and npm | any current | `m-prove`, only for changes with a web page |
| ffmpeg | any current | `m-prove`, only to record the pull request's videos; installed the first time it is missing |

`m-prove` drives web pages with [agent-browser](https://github.com/vercel-labs/agent-browser) and installs it globally with npm the first time a change has a page.

Every test run, server and browser script the skills start goes through `contain.py`. When the command ends or is stopped, everything it started ends too: on Windows a job object, on POSIX a process session ended with SIGTERM then SIGKILL, plus a watchdog. `step_check.py` and prove first end what earlier runs left in the repo, and orphaned automation browsers. Contained commands get `BROWSER=none` and `PW_TEST_HTML_REPORT_OPEN=never`, so dev servers and test reports do not open your browser. Set `MSTACK_PRIORITY=low` to run them at below-normal priority (off by default: under load it makes timing tests flaky).

Run one mstack feature per git worktree: two runs in one checkout share its servers and its step check baseline.

Suites and test files have a ceiling, 3 times their last measured run (at least 30 minutes for a suite, 5 for one file). A run that reaches it is reported as not finished, never as a failure.

## Quick start

Once per repo, run:

```
/setup-mstack
```

It writes `.mstack.yml` (commit it), checks your tools are installed and logged in, and checks Claude Code's auto mode lets an unattended run finish:

```yaml
# mstack: where work lives. See setup-mstack.
tracker: gh      # gh | jira | md   — where specs are read, state lives, issues open
host: gh         # gh | gitlab | bitbucket — where the pull request opens
```

Then point mstack at a spec:

```
/m-feature #412
/m-feature ABC-123
/m-feature docs/specs/newsletter.md
```

The spec is taken as reviewed: mstack builds what it says. A contradiction in it is resolved in favour of the app and opened as an issue linking the spec, saying what was built and where. The spec is frozen when the run starts; if it changes during the run, the pull request says so.

At the end you get one pull request into the base branch, written for a reviewer who will only look: the verdict at the top, a demo video, each requirement with its clip and before and after screenshots (or the command and its output), what else was checked against the base, every decision made without a person and its sources, steps to try it yourself, and how to roll it back. A check only a person can make (a real account's login, a captcha) keeps it a draft, listed under **Check by hand before merging**.

Run `/m-feature <spec>` again in a new session to resume the feature in flight: the state lives in your tracker, never in the chat.

App credentials that prove needs to drive the app (a test account, a store password) are read only from environment variables `MSTACK_SECRET_<NAME>`. They are never written to a file, an issue, a comment or a pull request.

## How it works

`/m-feature` only runs when you type it. It routes the work through the other skills:

```
0 Start       .mstack.yml · freeze the spec · feature branch · state
1 Understand  requirements ∥ scan  →  docs
2 Plan        steps grouped into slices
3 Per slice   build ⇄ step check (each step)  →  quality review ⇄ fix  →  slice prove ⇄ fix
4 Closing     final prove ⇄ fix  →  issues for what was already broken  →  pull request

m-debate: whenever a hard-to-undo decision or a failure a fix cannot settle comes up
```

| Skill | Stage | Runs in |
|---|---|---|
| `setup-mstack` | Writes `.mstack.yml`, checks the tools and auto mode. Run once per repo | Main chat |
| `m-feature` | Order, routing and state, through the tracker and host adapters | Main chat |
| `m-requirements` | Numbered, observable, bounded requirements, each tracing to a verbatim excerpt of the spec | Subagent |
| `m-scan` | What the repo already answers: versions, what exists, how it tests and runs | 4 parallel subagents |
| `m-research` | Vendor limits, timeouts, security guidance, version changes, quoted from primary sources | Main chat, one subagent per source |
| `m-plan` | Build steps grouped into slices, each slice ending at something a user can check; design checks | Main chat |
| `m-build` | One step into pinned commits on its branch, and a notes file | Subagent |
| `m-review` | A script checks each step; a static quality review per slice reports only sourced findings | Script in main chat; the review in a subagent |
| `m-prove` | Drives the running app: per slice, does it meet its Done when; at the end, replays everything and hunts regressions against the base | Subagent |
| `m-debate` | Five fresh agents research a hard question; the answer best backed by checked sources wins | Main chat, 5 subagents |

### Slices

A slice ends where something a user can check appears: a page, an endpoint, a command. Usually it is one step; a step with nothing to see on its own (a migration) joins the next one. Each slice has one end-to-end Done when that names the requirements it serves. Building, reviewing and proving slice by slice means a mistake is caught in the slice that made it.

### What each gate checks

**Build.** The builder chooses its own method, with one duty: a test that fails without its change (**Pinned by**). It commits on its step branch, pushes nothing and opens no pull request; `m-feature` merges the step into the feature branch locally once the step check passes.

**Step check** (`m-review/scripts/step_check.py`). After each step, a script:

| Check | Fails when |
|---|---|
| Suite | A test file fails that did not fail when the feature started. Failing files run alone first, so a real failure needs no suite rerun; files that fail only under load, a different set each run, give **not run · unstable under load** and the suite is switched to fewer files at once. A step that changes no code and meets a test failing on one run only, passing alone, gets it noted **flaky** |
| Tests changed | An existing test file or snapshot was changed or deleted, or a skip, `.only`, suppression, `\|\| true` or a runner exclusion was added, without being listed in the step's notes |
| Pinned | A test the notes name under Pinned by does not pass at HEAD, or still passes with the step's code reverted |
| Credentials | An added line holds a key format, a secret-like literal, a password in a URL to another host or a committed `.env`. The builder moves it to an environment variable |

**Quality review.** Once per slice, one agent reads the slice's diff without running it. A finding counts only with its source (your repo's rule file and line, or a verbatim quote from the official docs for the installed version, with its link) and the line of code that breaks it. What a linter catches does not count. Findings go back to the builder, and only those findings are re-reviewed.

**Slice prove.** A fresh agent drives the running app against the slice's Done when and every requirement the slice completes. Each check that passes is saved as a **replay**: a frozen script that runs again in seconds.

**Final prove.** When every slice is done:

1. every replay runs, so a slice that broke an earlier one is caught;
2. requirements without a passing replay are driven again;
3. a second agent hunts what else the whole feature broke, comparing every finding with the base branch.

| What failed | What happens |
|---|---|
| One of the requirements, even if the base already failed it | Not verified: fixed and proved again |
| Something else, broken by this feature | Fixed and proved again |
| Something else, already broken on the base | An issue labelled `found-by-prove`, with steps, base and head values and evidence, linked from the pull request. Not fixed: it is not this feature's work. An existing issue for the same failure gets a comment instead |

### Requirements

`m-requirements` turns the spec into lines a prover can judge. Each is observable, bounded where it says every, any or never, and quotes the excerpt of the spec it comes from. **Asked** requirements come from the spec and decide the verdict. **Derived** ones (failure states, empty states, limits the spec implies) are proved and reported, and block only when a debate marks them required. Ids and words never change once written.

### Models

Each stage asks for a model tier: cheap, standard or strong. Strong models go where a change is hard to undo and where nothing checks the agent's work, such as the regression hunt in prove and three of the five debaters. Map the tiers in your `~/.claude/CLAUDE.md` if you want specific models:

```markdown
# Models

When a skill asks for a model tier, pass it to the Agent tool as:

- cheap: `haiku`
- standard: `sonnet`
- strong: `opus`
```

## Unattended by design

| Would have waited on a person | Now |
|---|---|
| Questions about the spec | `m-requirements` decides what is easy; `m-debate` settles what is hard to undo |
| Confirming the plan | Nobody: it is saved and run |
| A finding the builder disputes, a fix that does not hold twice, a slice that keeps failing | `m-debate`, at most 2 per slice; after that the slice is Not verified and the run moves on |
| Credentials in a step | A failed step check; the builder moves them to an environment variable |
| Repeated failures, a refused command | The pull request ships Not verified, saying what is missing and why; a refused command goes under **To merge** |

The only stop is at the very start: no `.mstack.yml` and nothing to deduce it from, a tool not logged in, or a spec it cannot read. Then nothing has been created, and the line says to run `/setup-mstack`.

**Debates.** `m-debate` sends only the problem, never options or a preference, to five agents with a clean context (three strong, two standard). They research the official docs, the internet and your code; they never start the app or run anything. A second round runs only without consensus, with the other verdicts anonymised. The decision best backed by sources the orchestrator checked wins, not the most votes. Every debate is recorded, with the positions against, and listed in the pull request.

**Auto mode.** An unattended run merges step branches into the feature branch, pushes it, runs mstack's scripts and writes prove's run recipe under `~/.claude/skills/`. Claude Code's auto mode can refuse some of these by default, and a permission typed in a chat does not lift that. `/setup-mstack` checks your `~/.claude/settings.json` once and prints the block to add; mstack never edits that file. The block lives in `setup-mstack/references/auto-mode.md`. The final merge into the base branch stays yours.

## Using a skill on its own

Every skill except `m-feature` and `setup-mstack` also works outside the flow, and Claude Code loads it when your request matches its description. For example:

| Ask | Skill |
|---|---|
| "Prove this branch does what this spec asks" | `m-prove` |
| "Review this branch against our rules and the docs" | `m-review` |
| "Turn this spec into testable requirements" | `m-requirements` |
| "Decide how we should store these events, without me" | `m-debate` |
| "What are Stripe's webhook timeouts and retry rules?" | `m-research` |

## Contributing

Each skill is one folder:

```
skills/<name>/SKILL.md      objective, Done when, acceptance criteria, then the rules; loaded when it runs
skills/<name>/references/   read only when needed, or by the agents the skill dispatches
skills/<name>/scripts/      run, never read
skills/<name>/agents/       display metadata for other agent hosts
```

Adding a tracker or a host is adding a file under `m-feature/references/trackers/` or `hosts/` that implements the same operations as the others.

Some text is repeated across skills, so change these together:

- The requirement line format lives in `m-requirements/SKILL.md` (and its `scripts/check.py`), `m-feature/references/state.md`, `m-plan/SKILL.md` and `m-prove/SKILL.md`.
- The plan block and step body live in `m-plan/SKILL.md` and `m-feature/references/state.md`.
- The step notes file (path and sections) lives in `m-build/SKILL.md`, `m-review/scripts/step_check.py` and `m-feature/references/slice-loop.md`.
- The quality finding format lives in `m-review/references/quality.md`, `m-build/SKILL.md` (Fix mode) and `m-feature/references/slice-loop.md`.
- The debate input and record live in `m-debate/SKILL.md` and `m-feature/references/escalation.md`.
- Prove's inputs, return and issue drafts live in `m-prove/SKILL.md`, `m-prove/references/pull-request.md` and `m-feature/references/closing.md`.
- The label names live in `m-feature/SKILL.md`, `m-feature/references/state.md`, the tracker adapters and this README.
- The `.mstack.yml` shape lives in `setup-mstack/SKILL.md`, `m-feature/SKILL.md` and this README.
- The `autoMode.allow` block lives only in `setup-mstack/references/auto-mode.md`.
- `scripts/contain.py` is the same file in `m-build`, `m-prove` and `m-review`; CI fails when the copies differ.
- Where a run recipe is looked for lives in `m-prove/SKILL.md` and `m-scan/SKILL.md` (Q9).

The skills follow the writing-for-agents conventions: each SKILL.md opens with its objective, a Done when and acceptance criteria a different agent could check; then short rules, each with its reason, and no rule that does not change what the agent does.

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
