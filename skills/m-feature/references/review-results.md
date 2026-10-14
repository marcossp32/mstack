# Review results

Read when the feature review returns, before acting on its report.

After the last step passes its check: `git switch feature/<name>`, `git pull --ff-only`, dispatch the feature review. Post its report on the map as it came back, and keep only its counts and finding ids here. After a replan, review only what landed since the last review: `--base <the head that review reported>`; code already reviewed is hunted once.

- **No confirmed findings**, or no test suite to review with: go to Closing; prove is the judge left.
- **Confirmed findings**: create one fix step issue (label `build`, parent = map) listing each finding's claim, condition and entry point, never the reproduction; Done when: no listed condition holds. Cut `step/<name>-fix-<n>` (github.md, Branches), dispatch `/m-build` in fix mode, run the step check, then `/m-review` recheck with `--promote` on each finding. Every finding `fixed`, or `stale` after its rewrite: commit the promoted reproductions on the fix branch and merge it. No second review: prove judges the result.
- **`still-failing` or `SUITE WORSE`**: one more round on the same branch, naming which claims still hold and the suite's failing tests, never the reproduction's output. Still failing: replan.
- **`stale`**: `/m-review` rewrites that reproduction against the fix branch and rechecks it. It stays stale: list it on the map and in the final PR's What to watch. Only `/m-review`'s recheck calls a finding fixed; the builder's checks and your own reading of the code leave it as it is.
- **The builder disputes a finding**: the reproduction did fail, so the question is what the spec wants. Show the human the claim and the builder's reason; they decide.
