# Review results

Read when the feature review returns, before acting on its report.

After the last step passes its check: `git switch feature/<name>`, `git pull --ff-only`, dispatch the feature review. Post its report on the map as it came back, and keep only its counts and finding ids here. After a replan, review only what landed since the last review: `--base <the head that review reported>`; code already reviewed is hunted once.

- **No confirmed findings**, or no test suite to review with: go to Closing; prove is the judge left.
- **Confirmed findings**: first, for each non-test file a finding names, count the repair steps of this feature already merged that changed it (`git log --first-parent --name-only origin/feature/<name>`): review fix steps, and steps a replan added after a prove break. Two or more: a patching loop, replan (`SKILL.md`, Replan). Otherwise create one fix step issue (label `build`, parent = map) listing each finding's claim, condition and entry point, never the reproduction; Done when: no listed condition holds. Cut `step/<name>-fix-<n>` (github.md, Branches), dispatch `/m-build` in fix mode, run the step check, then `/m-review` recheck with `--promote` on every finding in one call. Every finding `fixed`, or `stale` after its rewrite: commit the promoted reproductions on the fix branch and merge it. No second review: prove judges the result.
- **`still-failing` or `SUITE WORSE`**: one more round on the same branch, naming which claims still hold and the suite's failing tests, never the reproduction's output. Still failing: replan.
- **`stale`**: the fix changed what the reproduction set up against, so its repro and capture both fail and say nothing. `/m-review` rewrites that reproduction against the fix branch and rechecks it. It stays stale: list it on the map and in the final PR's What to watch. Only `/m-review`'s recheck calls a finding fixed; the builder's checks and your own reading of the code leave it as it is.
- **`RECHECK NOT RUN`**: the suite hit its ceiling, so nothing was judged and every state is as it was. Post it on the map as it is; never rerun it for a verdict.
- **The builder disputes a finding**: the reproduction did fail, so the question is what the spec wants. Show the human the claim and the builder's reason; they decide.
