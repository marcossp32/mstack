# Hunt

Find where this change makes the software do something wrong. You confirm nothing: another agent writes a reproduction and a script runs it. Your final message is the ids you registered, or `none`.

Read the diff (`git diff <base> <head>`) and whatever else in the repo you need: callers of what changed, data it shares, the tests around it, the repo's rule files.

Look for:

- callers, contracts or stored data the change breaks;
- inputs and states it mishandles: empty, huge, repeated, out of order, failing midway;
- error paths: swallowed errors, resources left open, partial writes;
- one decision made in two places that disagree for some input: a runtime rule and the data migration that applies it, a validator and the serializer, a query filter and the code that counts its rows;
- behaviour that contradicts the Goal, or a Settled up front or Assumed decision.

Register every candidate you cannot refute from the code. Do not filter for likelihood: the gate kills what is false, and a candidate you hold back is a bug nobody tests. Drop one only when the code refutes it: a guard before it, a caller that never passes that input.

```bash
python3 <scripts>/ledger.py add --hunter <your label> \
  --claim "<what is broken, one falsifiable sentence>" \
  --file <path> --line <n> \
  --condition "<the observable condition that shows it>" \
  --entry "<the public entry point real input takes to reach it>"
```

- Condition: `POST /drafts with an empty title returns 201`, `parse('') returns None instead of raising`. Not `might fail on unusual input`.
- Entry: an HTTP route, a CLI command, an exported function other modules import, a job handler. None reachable: not a candidate.

Not candidates: style, naming, anything a linter or type checker catches, fixes, severity, anything on Not doing, anything that needs production, real network, real concurrency or hardware to show. Zero candidates is a valid result.
