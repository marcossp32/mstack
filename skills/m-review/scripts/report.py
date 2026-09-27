#!/usr/bin/env python3
"""The report, generated from the ledger, never from the model's recall.
Only confirmed findings (and their recheck state) appear."""
from ledger import load

LIMITS = """Limits
- Only failures a reproduction demonstrated are reported. Real bugs are lost:
  anything that needs production, real concurrency, the network or hardware.
- A finding in code that existed at the base, whose base checkout could not
  run, ends unjudgeable.
- Not a substitute for the linter, the type checker or /m-prove."""


def main():
    data = load()
    rows = [f for f in data["findings"]
            if f["state"] in ("confirmed", "fixed", "still-failing")]
    counts = {}
    for f in data["findings"]:
        counts[f["state"]] = counts.get(f["state"], 0) + 1

    print(f"REVIEW · base {data['base'][:12]} · head {data['head'][:12]}")
    print("Counts · " + " · ".join(f"{k} {v}" for k, v in sorted(counts.items()))
          if counts else "Counts · no candidates")
    if not rows:
        print("\nNo confirmed findings. A valid result: no candidate survived "
              "execution.")
    for f in rows:
        ev = f["evidence"]
        print(f"\n{f['id']} · {f['state']} · {f['file']}:{f['line']}")
        print(f"Claim     · {f['claim']}")
        print(f"Condition · {f['condition']}")
        print(f"Entry     · {f.get('entry', '?')}")
        print(f"Kind      · {ev['kind']} · {ev['base_note']}")
        n = len(ev["repro_runs"])
        print(f"Repro     · fails {n}/{n} at head · frozen {ev['repro']['frozen']}")
    print("\n" + LIMITS)


if __name__ == "__main__":
    main()
