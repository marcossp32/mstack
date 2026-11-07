# Auto mode

What a `scripts/check_auto_mode.py` line means, where the settings live, the block the script checks against, and why each entry is there.

An mstack run nobody watches still merges step branches into the feature branch, pushes it, runs mstack's scripts and writes prove's run recipe. Claude Code's auto mode classifier can refuse these ("Merge Without Review", "CI Bypass", "Self-Modification" for writes under `~/.claude/skills/`). An approval typed in a chat does not lift a refusal that happens hours later in a run nobody watches; only the human's settings do, and the run does not retry a refused command in another form, so a refused step merge leaves every later slice not verified. So setup checks the settings once, while a human is present.

## Where the settings live

- The classifier reads `autoMode` only from `~/.claude/settings.json` (`%USERPROFILE%\.claude\settings.json` on Windows; `$CLAUDE_CONFIG_DIR/settings.json` when that variable is set), managed settings, or the `--settings` flag. It ignores `.claude/settings.json` and `.claude/settings.local.json` in the repo, so a repo cannot grant itself rules.
- `autoMode.allow` entries are prose, read as exceptions to the built-in soft-deny rules. Entries from every scope are concatenated.
- The literal `"$defaults"` keeps the built-in allow rules at that position. An `allow` list without it replaces them.
- `permissions.defaultMode: "auto"` takes effect only from `~/.claude/settings.json` or managed settings, never from a project file. The per-session alternative is `claude --permission-mode auto` (also for `claude -p`).
- `claude auto-mode config` prints the effective rules (defaults spliced in, every scope merged); `claude auto-mode defaults` prints the built-in ones. The check uses both.

Sources: https://code.claude.com/docs/en/auto-mode-config, https://code.claude.com/docs/en/settings, https://code.claude.com/docs/en/permission-modes (read 2026-10-23, Claude Code 2.1.309).

## The block

The script reads the entries from this block; change them only here.

```json
{
  "autoMode": {
    "allow": [
      "$defaults",
      "mstack step merges: a local `git merge` (or `git merge --squash`) of a `step/*` branch into a `feature/*` branch, the `git push` of that `feature/*` branch, and deleting the merged `step/*` branch, after mstack's step_check.py printed `STEP CHECK: PASS` for that step. Never a merge into, or a push to, the base or default branch. The step check, the quality review and the prove are the user's chosen review for steps; a feature branch reaches the base only through a final pull request a human merges. Not Merge Without Review.",
      "mstack review scripts: running mstack's scripts (step_check.py, contain.py, cleanup.py, replay.py, prepare.py, runspec.py, plan_check.py, m-plan's plan checker, find_issue.mjs, the md tracker's issue search, and check.py, m-requirements' output checker, run unattended by m-feature and m-plan) from an installed `m-*/scripts` skill directory (`m-requirements/scripts` for check.py). They run the test suite, install, build, start and stop the app under test in containment, replay saved proofs, check requirements against their spec and plans against their requirements, and delete only the evidence directories mstack created; they skip, disable or loosen no check. Not CI Bypass.",
      "mstack run recipes: m-prove writing or editing a run recipe under `~/.claude/skills/run-<repo>/` (its `SKILL.md`, `run.json` and `surfaces/*.md`: how to install, launch, health-check and stop the repo under test, and the traps its drivers hit), from commands its drivers ran. It grants no permission and changes no setting or other skill. Not Self-Modification."
    ]
  },
  "permissions": {
    "defaultMode": "auto"
  }
}
```

Merge it into the existing file: append the three `mstack …` entries to an existing `autoMode.allow` (add `"$defaults"` if the list lacks it; never replace the list), and set `permissions.defaultMode` inside the existing `permissions` object. An older mstack entry (`mstack regression tests`, or a `mstack step merges` naming `gh pr merge`) is replaced, not kept beside the new one. Then run `claude auto-mode config` to confirm the entries appear.

## Why each entry

- **step merges**: m-feature merges each passing step locally and pushes `feature/*` so a later session can resume from the remote. "Git Push Destination" already allows the push; the entry frames the local merge as reviewed. Base and default branch are excluded so a human always merges the final pull request.
- **review scripts**: the step check and prove run the suite, containment and replays unattended, and the plan and requirements checkers run with nobody to approve them. They must not read as skipping checks.
- **run recipes**: m-prove records how to start the app in a skill under `~/.claude/skills/`, a config surface "Self-Modification" guards.
