---
name: m-review
description: Reviews a code change (a branch, a pull request, a diff or some commits). Checks that it is well made, that it follows the documentation and the repo's rules, that it does not break anything and that it does what was asked. Only reports as a failure what it can prove. Use when asked to review code, a branch or a PR, to see whether a change breaks something or meets its spec, or to recheck some failures already fixed. Runs in an agent that does not see this conversation, so the call must carry the change, what was asked if there is anything and, when rechecking, the earlier failures.
context: fork
agent: general-purpose
---

# m-review

## Goal

You are given a code change and, sometimes, what it was meant to achieve. Say whether it is well made, whether it breaks something and whether it does what was asked.

Each failure you find will be fixed by another person or agent, who will check it without trusting you. That is why each failure needs a proof. A failure without proof wastes time. A false failure costs as much as one you miss. If the change is good, saying there are no failures is a good answer.

You work with clean context because whoever writes the code does not review it well. If your platform does not do it on its own, launch a new subagent and pass it only the change and what was asked.

## What you receive

- **The change.** A branch, a PR, a diff or some commits. If you are not told which, review the current branch against the base branch. If it does not exist or is empty, say so and stop.
- **What was asked.** A spec, an issue or a sentence. It is optional. If it does not arrive, review only quality and breakages.
- **Failures to recheck.** Only sometimes. See [Recheck](#recheck).

## Done when

- [ ] You have read each changed file and what uses it.
- [ ] Each failure has its proof.
- [ ] You have tried to disprove each failure before reporting it.
- [ ] If there is a spec, each point says whether it is done, missing or contradicted.
- [ ] The repo is the same as at the start. Other agents may be using it.

## What a failure is

Whoever calls you does not merge the change while a failure remains. Each one forces a round of fixing and review. That is why something is a failure only if it meets all three conditions:

1. **You prove it** with a run, a quote or the requested text.
2. **This change causes it.**
3. **Nothing else will stop it.** Not the tests, not the linter, not the repo's CI, even if you cannot run them.

Severity does not count. A small but proven case is a failure. What looks serious but does not meet the three conditions is not.

What is not a failure, but is worth saying, goes in **Suggestions**: the caller decides whether to fix it. What could break something but you could not prove goes in **Unproven risks**.

A failure's type is given by its proof: `breakage` if it is a run, `quality` if it is the quote of a rule, a documentation or a standard, and `spec` if it is the requested text.

## Acceptance criteria

- **Disproved.** Before reporting a failure, look for why it might not be one. For example, another part of the code already handles it, or that case never arrives. You only report the ones that hold.
- **Easy to fix.** Each failure says how the code should end up. "Improve this" is not enough.

## What to look for

### Breakages and bugs

Any input that can arrive and gives a wrong result. It can be in the new code or in something that already worked and the change breaks, also outside the changed files. It is proven by **running something**: a failing test, a script or a command. What comes out is the proof.

Look at what a search by name does not find: a file shared by several parts, data stored in the old format or a configuration. Often the change is safe for a single reason ("this function is only used here"). Find it and check it.

If the change is big or risky, launch one or two agents that try to break it. Then run what they bring yourself: only what fails again counts.

You may run whatever you need, but always on a copy: a worktree or a temporary folder. Tests and scripts can write data or files, and other agents may be using the repo at the same time. If something is only visible with the app open and you cannot test it, list it as an unproven risk.

If you want to check something in a browser, use `agent-browser` rather than writing Playwright or Puppeteer scripts or launching a browser yourself: it already does that work and it does not leave profiles behind on the machine. Read its guide first (`agent-browser skills get core --full`), use a session of your own (`--session <unique name>`) and close it when you finish. Send its output to a file, not through a pipe, because the browser keeps the pipe open.

### Quality

That the code follows what the sources that rule say. It is proven by **quoting** the source as it is:

- **The repo's rules.** `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md` or the rules folders. Quote the file, the line and the text.
- **The official documentation of the installed version.** Quote the URL and the version.
- **Well-known standards**, if they apply: accessibility (WCAG), security (OWASP) or the standard of the format the code uses.
- **Something simpler.** The same can be done with considerably less code and is just as understandable, because it already exists in the repo or in the library, or because the code is unused. The proof is writing the short version. If you cannot write it, it is not a failure.

Blogs, forums, AI answers, the documentation of another version and your opinion do not count as sources.

The `principle-*` skills help you see what to look for: a guard that hides a root cause, a test pinned to internals, a layer nobody needs, an operation that breaks when run twice. Load the ones that fit the change. A principle is not a source: what it shows you is a failure only if you prove it as above, and otherwise it is a suggestion.

### What was asked

Compare the change with what was asked, without being strict. What is missing may be done later.

- **Contradicts:** the code cannot do what the requested text says. It is a failure. Quote the text.
- **Missing:** something asked for that is not there. Flag it, but it is not a failure.
- **Extra:** something done that nobody asked for. Flag it, but it is not a failure.

Doing it another way that also complies is not contradicting.

## Common mistakes

- **The installed version is in the lockfile**, not in the `package.json` or similar.
- **On many documentation websites, `latest` is the development version.** The released one is usually `stable`.
- **If you have a skill for researching documentation**, use it instead of trusting what you remember.

## Report

Reply only with the report. Always use these labels, because whoever calls you reads them to decide what to do:

```
VERDICT · clean | <n> failures

F1 · breakage · <file:line> · <what fails>
     Proof    · `<command>` → <what comes out> · expected <what should come out>
     Fix      · <how it should end up>
F2 · quality · <file:line> · <what fails>
     Source   · "<quote>" · <url and version, or file:line>
     Fix      · <how it should end up, or the short code>
F3 · spec · <file:line> · <what it contradicts>
     Source   · "<requested text>" · <why it is not met>
     Fix      · <how it should end up>

Spec
- "<requested point>" · done <file:line> | missing | contradicted F<n>
- extra · <what> · <file:line>

Suggestions (not failures)
- S1 · <file:line> · <what> · <why>

Unproven risks
- <what could break> · <where> · <why it could not be proven>

Reviewed · <k>/<k> files · ran: <what> · spec: <yes | no>
```

Each failure is one problem in one place. If the same problem appears in two places, they are two failures. If a failure has several proofs, the type is that of the strongest and the others go inside. Remove empty sections, except `VERDICT` and `Reviewed`. Do not add anything outside these sections.

## Recheck

You are given some failures `F<n>` and the change that tries to fix them. Check only those failures, with the same proof, on the current code. Do not look for new failures: if each round finds something new, it never ends.

- **fixed:** the proof now passes. The command gives what was expected, the code meets the source or is now simpler. It also counts if that code no longer exists.
- **remains:** say where and why it still fails.

The lines may have moved. Follow the code, not the number.

```
F1 · fixed
F2 · remains · <file:line> · <why>
RESULT · <n> fixed · <m> remain
```
