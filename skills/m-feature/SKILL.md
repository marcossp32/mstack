---
name: m-feature
description: Takes a feature through the whole cycle without help, from a spec or any description of what has to be built to a pull request that proves it works. Use when /m-feature is run with a spec, an issue or a description, to start that feature or resume it.
disable-model-invocation: true
---

# m-feature

## Goal

You are given something to build: a spec, an issue or a description. You take it through the whole cycle, from understanding it to a pull request that proves it works and that it is well made.

Your role is to direct the work and answer for the result. Each part of the cycle has a skill, an agent or a tool that does it well: use it. What nothing covers, do yourself.

## You work alone

Nobody watches this run and nobody answers. Launching this skill is the permission for everything the delivery needs: creating branches, committing, pushing your branch, opening the pull request and issues, installing what the project declares, starting servers. Do not ask and do not wait for approval: decide, and write down what you decided and why.

When a doubt changes the result and neither the repo nor the documentation settles it, ask other agents that have not seen this conversation, so their opinion is not shaped by yours (a skill for debating decisions does this well). Then decide yourself.

Freedom has an edge, and it is the footprint. Everything you create lives in the repo, in your branch or in your work folder, and when you finish nothing of yours is left anywhere else: no servers, no temporary folders, no packages installed outside the project. You do not touch what is not yours: the base branch, other branches, other people's files. Whoever launched you trusts that the run only changes what the feature needs.

## Driven by proof

This skill follows PDD (*proof driven development*): what drives the work is proving that it works. Tests check what the test expects; the proof checks that the user gets what they asked for. A requirement is done when you have seen it work in the running app and saved the evidence, not when the tests pass.

Three ideas hold the whole cycle together:

- **Think of the proof before the code.** If you do not know how to prove a requirement, you do not understand it yet.
- **Whoever builds does not judge.** Agents that did not write the code review it and prove it, with clean context, because whoever checks their own work sees what they expect. If a skill exists for testing in the running app or for reviewing, use it: it knows how to test better than an improvised check. A failure is closed by whoever found it, when they check the fix. Your own reading of the code closes nothing.
- **A verdict speaks for the code it saw.** A review or a proof certifies one commit. What the pull request claims holds only for its last commit: if the code changes after a proof, that proof no longer covers it. Rechecking is cheap, because it only looks at the failures and at what the fix touched. Skipping it is what lets a broken fix reach the base.

## Done when

The run ends in one of three ways. Nothing else is an end.

- **Delivered.** A pull request against the base branch, open on the host, that meets all the acceptance criteria and is marked as ready.
- **Failed.** You tried several approaches and something still does not work. The pull request stays as a draft and says at the top what fails and what you tried.
- **Blocked.** Something only someone outside this run can give is missing (see [Blocked](#blocked)). You found it before building, or as soon as it appeared.

A substitute for something external is not that thing: a file that describes a pull request is not a pull request, and a check you ran instead of the CI is not the CI. If the real thing cannot exist, the run is Blocked, and it says so.

## The cycle

An order that usually works. Adapt it when the work asks for it, but each phase reaches its result before the work leans on it.

### 1. Start

Check everything external before creating anything: the tracker, the host, the tools and the sessions logged in, the credentials the requirements need. Finding a gap at the end means having worked for nothing; finding it now costs one message.

Then look for saved progress for this spec. If there is, continue from where it stopped, on its branch. If not, create your own branch from the base.

The spec as you read it now is the target. If it changes during the work, keep building what you read and say so in the pull request.

**Done when** you know where the spec, the issues and the pull request live, nothing external is missing, and you are on the feature's branch.

### 2. Understand

Write what is asked as requirements that can be checked, each one tied to the words of the spec it comes from. Note what the spec leaves out, what contradicts itself and what it leaves open.

**Done when** each requirement says what a person would see if it works, and each contradiction or gap is written down.

### 3. Investigate

Find out what the repo already is: the versions it uses, how it does similar things, how it is tested and how it runs. Facts the repo cannot settle (a library's limit, what changed in a version, what a standard requires) come from their owner's documentation, quoted with its link, not from memory. There are skills for scanning a repo and for researching documentation.

**Done when** you could explain to someone how you will build it in this repo, and each outside fact you rely on has its source.

### 4. Decide

Before planning, settle what is open, above all what would be hard to undo: a stored format, a public API, a dependency others will rely on. The harder it is to undo, the more care it deserves: more opinions, stronger models, more proof. What is easy to undo, decide it yourself and write down why.

**Done when** every open point has a decision with its reason, and each contradiction in the spec has an issue saying what you built.

### 5. Plan

Split the work into parts. A part is a group of requirements that a user can check on its own: something they would see working in the app. A feature with three things a user does is three parts, even if each is small. Only when the requirements cannot be checked separately is the whole feature one part.

Parts exist so that a failure shows up where it is cheap to fix. Seen at the end, a failure forces you to redo work built on top of it.

**Done when** each part names the requirements it covers and how a user would check it, in an order where each part builds on finished work.

### 6. Build, review and prove each part

For each part, in order:

1. **Build** it, with tests that would fail without it.
2. **Review** it: that it does what was asked, follows the official documentation and the standards of what it uses, and respects the repo's rules and architecture.
3. **Prove** it in the running app.
4. **Fix** what they found and send it back to whoever found it to check, until nothing remains open.

Review comes before proof because its fixes change the code that the proof must see.

The `principle-*` skills hold the engineering habits that most often decide whether a part passes review: fixing root causes, the smallest change, tests that pin behavior, checking the real thing. Load the ones that fit what you are doing at that moment, for example the root-cause one when a fix fails.

**Done when** the part's last commit has a review with no open failures and a proof that says it works.

### 7. Prove the whole feature

When all the parts are done, prove the whole feature against the base branch: each requirement once more together, and what your change could have broken in what already worked. Earlier parts can break when later ones arrive.

**Done when** the proof of the last commit says it works, with evidence for each requirement and no new breakage against the base.

### 8. Deliver

Open the pull request as a draft and mark it ready only when it meets every acceptance criterion and its proof covers its last commit. If you change code after that, it goes back to review and proof.

**Done when** the run has ended Delivered, Failed or Blocked, and your footprint is clean.

## Acceptance criteria

Each one is answered yes or no before marking the pull request ready.

**It works**
- [ ] Each requirement has been seen working in the running app: in the open app, running the command or calling the API.
- [ ] The pull request shows the proof of each requirement: a video, a screenshot, or the command and what it returned.
- [ ] What already worked and the spec does not ask to change still works.
- [ ] The proof covers the pull request's last commit.

Check only what is needed: one clear proof per requirement and what your change can affect. Repeating checks that already passed spends time without adding confidence.

**It is trustworthy**
- [ ] Agents that did not build it reviewed it and proved it, and every failure they found was closed by them.
- [ ] No test or requirement was changed to make something pass. That hides the failure, it does not fix it.
- [ ] The tests pass. CI passes or, if the host has none, the pull request says so.

**It is simple**
- [ ] There is no simpler way to get the same result, with fewer pieces, layers or code, without doing less or doing it worse.

**It is understandable without reading the code**
- [ ] The first thing the pull request says is whether it works or not.
- [ ] It explains what changes for the user.
- [ ] Each decision you made alone appears with its reason.

**It is safe and clean**
- [ ] No key or password is written in the code, the pull request or the issues.
- [ ] Nothing of this run is left outside the repo and its work folder: no processes running, no temporary files, no global installs.

## Along the way

- **Save progress after each phase and each part**, so a new session can continue if this one is cut off. The progress says where you are, what you decided and why, and which commit each verdict covers.
- **A failure that comes back after fixing it** asks for a different approach, not the same one again: investigate, ask for another opinion or rethink that part. If several approaches fail, the run ends Failed.
- **What does not belong to this feature goes to an issue**: a failure that was already in the base or a contradiction in the spec. Mention it in the pull request.
- **Skills leave things behind too.** At the end, check that what the skills you used created outside the repo is gone, and clean it yourself if not. The saved progress stays until the pull request is merged.

## Where the tasks are and where the pull request goes

The **tracker** is where the spec and the issues are: GitHub Issues, Jira or markdown files in the repo. If the repo has `.mstack.yml`, it says which one. If not, deduce it from the reference you were given (`#123` is GitHub, `ABC-123` is Jira, a path to a `.md` is files). If you were only given text, use markdown files.

Before using the tracker, read its file. It has the commands and the usual errors of each tool.

| [GitHub Issues](references/trackers/gh.md) | [Jira](references/trackers/jira.md) | [Markdown](references/trackers/md.md) |
|---|---|---|

The pull request opens on the **host** `origin` points to. If it cannot be opened there (a host with no way to open one, or no session logged in), the run is Blocked.

## Blocked

Some things only someone outside the run can give: a host where the pull request can be opened, a tool or a logged-in session, a key, an account, a permission. Nothing else blocks: a doubt is decided, a hard question is investigated or debated.

Look for all of them at Start and report them together, so whoever reads it can fix everything at once. Save progress and end with this message, which is read by someone arriving later without context:

```
⏸ m-feature blocked · needs something from outside

Missing:      <what is missing, e.g. the payments API key>
What for:     <which requirement or phase needs it>
How to give:  <exactly what to do, e.g. set PAYMENTS_SECRET=<your key>>
Then:         run /m-feature <the same as before> again; it resumes from the saved progress
```
