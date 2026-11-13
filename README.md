# mstack

Claude Code skills that take a spec to a pull request proved in the running app, unattended.

You hand mstack a spec, an issue or a description. Nobody answers questions: it turns what is asked into requirements a person could check, investigates the repo and the docs, splits the work into parts a user can see working, and for each part builds it, has it reviewed and has it proved in the running app by agents that did not write it. At the end it proves the whole feature against the base branch and opens one pull request that shows it working.

- **Proof driven.** A requirement is done when it has been seen working in the running app and the evidence is saved, not when the tests pass.
- **Whoever builds does not judge.** Review and proof run in fresh agents that do not see the conversation, and a failure is closed only by whoever found it.
- **Review with proof.** A review failure counts only with its proof: a run that shows it, a quote of your repo's rules or the official docs, or the text that was asked.
- **Engineering principles in context.** Ten short principle skills (root causes, smallest change, tests that pin behavior, checking the real thing…) shape how the agents build and review.
- **Unattended.** Where a person would once have been asked, mstack decides and writes down why, or asks fresh agents for independent opinions. It ends Delivered, Failed or Blocked, never waiting.
- **Works with your tools.** Specs and progress live in GitHub Issues, Jira or markdown files; the pull request opens on GitHub, GitLab, Bitbucket or Azure DevOps.

## Contents

- [Install](#install)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [How it works](#how-it-works)
- [The skills](#the-skills)
- [Principle skills](#principle-skills)
- [Using a skill on its own](#using-a-skill-on-its-own)
- [Contributing](#contributing)
- [Credits](#credits)
- [License](#license)

## Install

```bash
npx skills add marcossp32/mstack -g -a claude-code --skill '*'
```

This installs into `~/.claude/skills/`. Drop `-g` to install into the current project's `.claude/skills/` instead. Install all skills together: `m-feature` relies on the others, and the principle skills work best as a set.

Update with `npx skills update`.

## Requirements

| Tool | Version | Used by |
|---|---|---|
| [Claude Code](https://claude.com/claude-code) | current | all |
| git | 2.31 or newer | all |
| Python | 3.9 or newer | `m-prove` (`scripts/contain.py`); `m-feature` on Jira (`scripts/jira_adf.py`) |
| The tracker's CLI, logged in: `gh` or `acli` | see `m-feature/references/trackers/` | `m-feature` |
| The host's CLI or token, logged in | see `m-pr/references/hosts/` | `m-pr` |
| [agent-browser](https://github.com/vercel-labs/agent-browser) and its browser | any current | `m-prove` and `m-review`, only for changes with a web page |

`m-prove` and `m-review` drive web pages with agent-browser, never with their own Playwright or Puppeteer scripts. They do not install it: without it, what needs a browser is reported as not tested. Install it once:

```bash
npm install -g agent-browser
agent-browser install        # downloads its browser
agent-browser doctor --fix   # if something fails
```

`m-prove` launches servers and scripts through `scripts/contain.py`, so that when a command ends or is stopped, everything it started ends too (a job object on Windows, a process session on POSIX). agent-browser is the exception: its browser stays alive between commands, so each skill opens its own session and closes it when it finishes. Set `MSTACK_PRIORITY=low` to run contained commands at below-normal priority.

Run one feature per git worktree: two runs in one checkout share its servers and its files.

## Quick start

Point mstack at a spec:

```
/m-feature #412
/m-feature ABC-123
/m-feature docs/specs/newsletter.md
/m-feature "Let users export their orders as CSV"
```

The tracker is deduced from the reference: `#123` is GitHub Issues, `ABC-123` is Jira, a path to a `.md` is markdown files, plain text uses markdown files. To fix it per repo, commit a `.mstack.yml`:

```yaml
# mstack: where work lives
tracker: gh      # gh | jira | md   — where the spec is read, progress is saved and issues open
host: gh         # gh | gitlab | bitbucket | azure — where the pull request opens (default: where origin points)
jira:
  project: ABC   # only for tracker: jira
md:
  dir: .mstack/  # only for tracker: md
```

The spec is the target as it reads when the run starts; if it changes during the run, the pull request says so. A contradiction in the spec gets an issue saying what was built.

The run ends in one of three ways:

- **Delivered.** A pull request into the base branch, marked ready, that meets every acceptance criterion.
- **Failed.** Several approaches tried and something still does not work. The pull request stays a draft and says at the top what fails and what was tried.
- **Blocked.** Something only a person can give is missing (a logged-in tool, a key, a host where to open the pull request). It is found at the start whenever possible, and the run ends with one message saying what is missing, what for and how to give it.

Run `/m-feature <the same spec>` again in a new session to resume: progress lives in the tracker, never in the chat.

Credentials the app needs are read only from environment variables, and never written to code, issues or the pull request.

## How it works

`/m-feature` only runs when you type it. It directs the work and answers for the result; each part of the cycle is done by the skill or agent that does it best.

```
1 Start        check the tracker, host, tools and credentials · resume or create the feature branch
2 Understand   requirements a person could check, each tied to the spec's words
3 Investigate  the repo (m-scan) and outside facts from their owners' docs (m-research)
4 Decide       settle open points, more care the harder they are to undo (m-debate for opinions)
5 Plan         parts a user can check on their own, in an order where each builds on finished work
6 Per part     build with tests → review (m-review) → prove in the running app (m-prove) → fix ⇄ recheck
7 Whole        prove the whole feature against the base branch: every requirement and what it could break
8 Deliver      open the pull request (m-pr) as a draft · ready only when every criterion holds
```

Review comes before proof because its fixes change the code the proof must see. A verdict covers the commit it saw: if the code changes after a proof, it goes back to review and proof. Progress is saved after each phase and each part, so a cut session can continue.

Before marking the pull request ready, `m-feature` checks that each requirement was seen working with evidence in the pull request, that what already worked still works, that agents that did not build it reviewed and proved it, that no test or requirement was changed to make something pass, that CI passes, that there is no simpler way to the same result, and that nothing of the run is left outside the repo.

### Models

Skills that dispatch agents ask for a model tier: cheap, standard or strong. Map the tiers in your `~/.claude/CLAUDE.md` if you want specific models:

```markdown
# Models

When a skill asks for a model tier, pass it to the Agent tool as:

- cheap: `haiku`
- standard: `sonnet`
- strong: `opus`
```

## The skills

| Skill | What it does | Runs in |
|---|---|---|
| `m-feature` | Takes a feature from spec to pull request, directing the others. Only runs when you type `/m-feature` | Main chat |
| `m-scan` | Investigates the repo before a change: installed versions, available libraries, how it does similar things, how it is tested, what already solves the problem | Main chat, parallel agents per area |
| `m-research` | Answers factual questions (limits, timeouts, library behavior, version changes, standards) from the sources with authority, each with a verbatim quote and its link | Fresh agent |
| `m-debate` | Five fresh agents with different models investigate the same question separately and return their verdicts with sources; it does not decide for you | Main chat, 5 agents |
| `m-review` | Reviews a change without trusting its author: breakages proven by a run, quality proven by a quote, the spec checked point by point; also rechecks failures after a fix | Fresh agent |
| `m-prove` | Tries to prove a change does not work in the running app, checks breakages against the base, and leaves screenshots or video when it works; also retests failures after a fix | Fresh agent |
| `m-pr` | Opens or updates the pull request with a short description of what changes and why, the evidence hosted on the host, draft until ready and CI green | Main chat |

The report formats are read by other skills: `m-review`'s `VERDICT`/`F<n>` report and `m-prove`'s `VERDICT`/`✓`/`F`/`?` report are what `m-feature` acts on and `m-pr` turns into the pull request's evidence.

## Principle skills

Ten short skills, each holding one engineering principle: what it is, why it matters, what good looks like and the usual traps. They are loaded by the model itself, and their descriptions are always in context, so they shape how agents build and review even when not opened. `m-feature` and `m-review` point to them at the moments they matter.

| Skill | The principle |
|---|---|
| `principle-fix-root-causes` | Fix a bug where it starts, not where it shows; a guard is a fix only for a legitimate state |
| `principle-attack-the-premise` | When fixes that share one premise keep failing, test the premise instead of trying another fix |
| `principle-prove-it-works` | Before saying done, watch the real thing work, not a proxy like "the tests pass" |
| `principle-test-behavior-not-implementation` | Tests fail when behavior breaks and survive refactors |
| `principle-smallest-change` | The smallest change that fully solves the problem; remove before adding |
| `principle-boundary-discipline` | Parse outside input once at the boundary into proper types, and trust them inside |
| `principle-model-the-domain` | Put the domain in a data structure so invalid states cannot be represented |
| `principle-minimize-reader-load` | Fewer layers to trace and less hidden state to hold |
| `principle-redesign-from-first-principles` | Fold a new requirement in as if it had been known from the start |
| `principle-make-operations-idempotent` | Running twice, concurrently or after a crash ends in the same correct state |

In A/B tests on coding and review tasks, with and without these skills and against a placebo of generic quality advice, they raised Claude Sonnet's success rate the most, and did not make any model worse on tasks where applying a principle blindly would be wrong.

## Using a skill on its own

Every skill except `m-feature` also works outside the flow, and Claude Code loads it when your request matches its description. For example:

| Ask | Skill |
|---|---|
| "Check this branch works in the app" | `m-prove` |
| "Review this PR against our rules and the docs" | `m-review` |
| "What does this repo already have for sending emails?" | `m-scan` |
| "What are Stripe's webhook timeouts and retry rules?" | `m-research` |
| "Get me independent opinions on how to store these events" | `m-debate` |
| "Open a PR for this branch with the screenshots" | `m-pr` |

## Contributing

Each skill is one folder:

```
skills/<name>/SKILL.md      goal, Done when, acceptance criteria, then the rules; loaded when it runs
skills/<name>/references/   read only when needed
skills/<name>/scripts/      run, never read
```

Adding a tracker is adding a file under `m-feature/references/trackers/` with the same operations as the others. Adding a host is adding a file under `m-pr/references/hosts/` and a column to the table in `m-pr/SKILL.md`.

Some text is read across skills, so change these together:

- `m-review`'s report labels (`VERDICT`, `F<n>`, `Recheck`) and `m-prove`'s report (`VERDICT`, `✓`/`F`/`?`, `Media`, `Evidence`, `Retest`) are read by `m-feature` and `m-pr`.
- The `.mstack.yml` shape lives in `m-feature/SKILL.md`, its tracker files, `m-pr/SKILL.md` and this README.
- The `principle-*` names are referenced from `m-feature/SKILL.md`, `m-review/SKILL.md` and from each other.

The skills shape rather than constrain: each SKILL.md states its goal, a Done when and acceptance criteria another agent could check, then only the rules that change what the agent does, each with its reason.

Try an install from the working tree before pushing:

```bash
npx skills add . --list
```

## Credits

- [Matt Pocock](https://www.aihero.dev/), whose [skills](https://github.com/mattpocock/skills) make an agent follow a team's process: grilling the request before writing code, and test-first.
- [Addy Osmani](https://addyosmani.com/blog/agentic-engineering/), on the human owning architecture and correctness while the agent implements, and on [agent skills](https://github.com/addyosmani/agent-skills) as quality gates rather than prompts.
- [Lauren Tan](https://github.com/poteto), whose [pstack](https://github.com/cursor/plugins/tree/main/pstack) treats verification as the skill that matters, and whose principle skills inspired mstack's `principle-*` set.

## License

[MIT](LICENSE)
