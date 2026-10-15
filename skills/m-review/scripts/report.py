#!/usr/bin/env python3
"""The report, generated from the ledger, never from the model's recall.
Confirmed findings (and their recheck state) appear in full; unjudgeable ones
with their reason, since nothing judged them.

The review is over once it reports: the base worktree is removed."""
import os

from common import root
from ledger import load, remove_bases, save

LIMITS = """Limits
- Only failures a reproduction demonstrated are reported. Real bugs are lost:
  anything that needs production, real concurrency, the network or hardware.
- A finding whose reproduction could not run at the base, or failed there
  while the base suite was red, ends unjudgeable.
- Not a substitute for the linter, the type checker or /m-prove."""


def main():
    data = load()
    rows = [f for f in data["findings"]
            if f["state"] in ("confirmed", "fixed", "still-failing", "stale")]
    unjudged = [f for f in data["findings"] if f["state"] == "unjudgeable"]
    counts = {}
    for f in data["findings"]:
        counts[f["state"]] = counts.get(f["state"], 0) + 1

    print(f"REVIEW · base {data['base'][:12]} · head {data['head'][:12]}")
    print("Counts · " + " · ".join(f"{k} {v}" for k, v in sorted(counts.items()))
          if counts else "Counts · no candidates")
    if not rows and not unjudged:
        print("\nNo confirmed findings. A valid result: no candidate survived "
              "execution.")
    elif not rows:
        print("\nNo confirmed findings, but not every candidate was judged.")
    for f in rows:
        ev = f["evidence"]
        print(f"\n{f['id']} · {f['state']} · {f['file']}:{f['line']}")
        print(f"Claim     · {f['claim']}")
        print(f"Condition · {f['condition']}")
        print(f"Entry     · {f.get('entry', '?')}")
        print(f"Kind      · {ev['kind']} · {ev['base_note']}")
        rewrites = [c for c in f.get("rechecks", []) if c.get("rewritten")]
        if rewrites and f["state"] in ("fixed", "still-failing"):
            n = len(rewrites[-1]["runs"]["repro"])
            print(f"Repro     · rewritten at {rewrites[-1]['head'][:12]}, {n} runs · "
                  f"frozen {ev['repro']['frozen']}")
        else:
            n = len(ev["repro_runs"])
            print(f"Repro     · fails {n}/{n} at head · frozen {ev['repro']['frozen']}")
    if unjudged:
        print("\nNot judged")
        for f in unjudged:
            reason = (f.get("reason") or "?").splitlines()[0]
            print(f"{f['id']} · {f['file']}:{f['line']} · {f['claim']}\n"
                  f"          {reason}")
    print("\n" + LIMITS)

    wt = data.get("base_worktree")
    if wt:
        remove_bases(root(), say=lambda line: None)
        if not os.path.isdir(wt):
            data["base_worktree"] = None
            save(data)


if __name__ == "__main__":
    main()
