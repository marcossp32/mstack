# Unattended

Read at Start of an autonomous run, before scan.

A run nobody watches still has to merge step pull requests, run the review scripts, commit reproductions and write prove's run recipe. Claude Code's auto mode classifier refuses some of these by default ("Merge Without Review", "CI Bypass", "Security Test Removal"). An approval typed in the chat does not lift those refusals; only the human's settings do. Found at hour ten, a refusal waits for a human who is gone, so check now, while they are still here.

## Check

1. Read `~/.claude/settings.json`. The classifier reads `autoMode` only from there (or from managed settings), never from the repo's `.claude/settings*.json`.
2. `autoMode.allow` holds `"$defaults"` and the four entries below, each starting with its name (`mstack step merges`, `mstack review scripts`, `mstack regression tests`, `mstack run recipes`). Without `"$defaults"`, the list replaces the built-in exceptions.
3. `permissions.defaultMode` is `auto`. Otherwise every command that needs approval waits on a prompt.

All three hold: go on. Otherwise stop with one question: show the block below, say that it goes in `~/.claude/settings.json` (merged into an existing `autoMode.allow`, not replacing it), and wait. Never edit that file yourself: a run granting itself permissions is the bypass the classifier exists to stop. The human declines: go on, and every refusal later goes under To merge with the command it refused.

## The block

```json
{
  "autoMode": {
    "allow": [
      "$defaults",
      "mstack step merges: `gh pr merge` of a step pull request into a `feature/*` branch, never into the base or default branch, after mstack's step_check.py printed `STEP CHECK: PASS` for it. The step check and the review are the user's chosen review for step pull requests; a feature branch reaches the base only through a final pull request a human merges. Not Merge Without Review.",
      "mstack review scripts: running mstack's scripts (step_check.py, prepare.py, gate.py, ledger.py, report.py, contain.py, cleanup.py, replay.py) from an installed `m-*/scripts` skill directory, including `gate.py recheck --promote`. They run the test suite and record verdicts; they skip, disable or loosen no check. Not CI Bypass.",
      "mstack regression tests: committing and pushing, on a `step/*` fix branch, the reproduction test files gate.py left in the checkout after `recheck --promote` printed `fixed`. This adds tests and removes none. Not CI Bypass or Security Test Removal.",
      "mstack run recipes: m-prove writing, or appending to, a run recipe `SKILL.md` under `~/.claude/skills/` (how to launch, health-check and stop the repo under test, and the traps its drivers hit), from commands its drivers ran. It grants no permission and changes no setting or other skill."
    ]
  }
}
```

## Refused anyway

A refusal later in the run: do not retry it in another form (that is the bypass the classifier blocks). A refused step merge stops the run (`replan.md`, Stop): every later step, the review and prove build on the feature branch, so nothing is left that does not depend on it. `Stopped ·` names the refused command and the entry above that would allow it. Any other refusal: put the command under To merge in the closing message, naming that entry, and go on with what does not depend on it.
