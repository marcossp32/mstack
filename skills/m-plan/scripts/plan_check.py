#!/usr/bin/env python3
"""Plan check. Deterministic, no model judgement. Run it for its output.

    plan_check.py <Out dir> --requirements <file> [--previous <earlier Out dir>]

Reads <Out>/plan.md (the plan block) and <Out>/step-<n>.md (one body per step),
and the requirement lines (`R<n> · …`) from --requirements. With --previous,
also checks that a step whose body changed took a new number.
Prints one `- FAIL <what>` line per failure, then `PLAN CHECK: PASS | FAIL`.
Exit 0 = PASS, 1 = FAIL, 2 = could not read the inputs.
"""
import argparse
import pathlib
import re
import sys

LABELS = ["Steps", "Slices", "Slice", "Blocking", "Design", "Assumed", "Open", "Revised"]
REQ = re.compile(r'^(R\d+)\s*·\s*(asked|derived(?:\s*·\s*required by D\d+)?)\s*·\s*"(.*)"\s*·\s*bound\s', re.M)
SERVES_TAIL = re.compile(r'serves (R\d+) "(.*)"\s*$')


def read(path):
    return pathlib.Path(path).read_text(encoding="utf-8")


def requirements(text):
    reqs = {}
    needs = set(re.findall(r"^\s*-\s*(R\d+) needs ", text, re.M))
    for line in text.splitlines():
        m = REQ.match(line.strip())
        if m:
            rid, level, words = m.groups()
            reqs[rid] = {
                "level": "derived" if level == "derived" else "required",
                "env": rid in needs or bool(re.search(r"·\s*CI\s+\S.*$", line.strip())),
                "words": words,
                "retired": bool(re.search(r"·\s*retired by D\d+\s*$", line.strip())),
            }
    return reqs


def block(text):
    """Split the plan block into labelled entries; continuation lines join the entry above."""
    entries = []
    for line in text.splitlines():
        m = re.match(r"^(Steps|Slices|Slice S\d+|Blocking|Design|Assumed|Open|Revised)\s*·\s?(.*)$", line)
        if m:
            entries.append([m.group(1), m.group(2)])
        elif entries and line.strip():
            entries[-1][1] += "\n" + line
    return entries


def body_parts(text):
    heads = re.findall(r"^## (.+?)\s*$", text, re.M)
    done = re.split(r"^## Done when\s*$", text, flags=re.M)
    return heads, (done[1].strip() if len(done) == 2 else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--requirements", required=True)
    ap.add_argument("--previous")
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    try:
        plan = read(out / "plan.md")
        reqs = requirements(read(a.requirements))
    except OSError as e:
        print(f"ABORT: {e}", file=sys.stderr)
        return 2
    if not reqs:
        print("ABORT: no requirement lines in --requirements", file=sys.stderr)
        return 2
    fails = []
    live = {r for r, v in reqs.items() if not v["retired"]}

    entries = block(plan)
    order = [LABELS.index(e[0].split()[0]) for e in entries]
    if order != sorted(order):
        fails.append("block lines out of order: " + " ".join(e[0] for e in entries))
    for need in ("Steps", "Slices", "Blocking", "Design", "Assumed"):
        if not any(e[0] == need for e in entries):
            fails.append(f"block has no {need} line")
    get = lambda label: next((e[1] for e in entries if e[0] == label), "")

    steps = {}
    for line in get("Steps").splitlines():
        m = re.match(r"^\s*(\d+)\.\s.*·\s*serves (R\d+)(\s*·\s*waits D\?)?\s*$", line)
        if not m:
            fails.append(f"step line not `<n>. <step> · Done when … · serves R<k>`: {line.strip()[:80]}")
            continue
        n, rid, waits = int(m.group(1)), m.group(2), bool(m.group(3))
        if n in steps:
            fails.append(f"step {n} listed twice")
        steps[n] = rid
        if rid not in live:
            fails.append(f"step {n} serves {rid}, which is not a live requirement: serve the live line that carries its work")

    for n, rid in steps.items():
        f = out / f"step-{n}.md"
        if not f.exists():
            fails.append(f"step {n} has no step-{n}.md")
            continue
        body = read(f)
        heads, done = body_parts(body)
        if heads != ["What to do", "What you need to know", "Done when"]:
            fails.append(f"step-{n}.md headings are {heads}, not What to do / What you need to know / Done when")
        m = SERVES_TAIL.search(done)
        if not m:
            fails.append(f"step-{n}.md Done when does not end `serves R<k> \"<words>\"`")
        elif m.group(1) in reqs and m.group(2) != reqs[m.group(1)]["words"]:
            fails.append(f"step-{n}.md quotes {m.group(1)} with other words than the requirement: copy its quoted words exactly")
        if re.search(r"\{[A-Z_]+\}|<placeholder>|TODO", body):
            fails.append(f"step-{n}.md holds a placeholder")
    for f in out.glob("step-*.md"):
        m = re.match(r"step-(\d+)\.md$", f.name)
        if m and int(m.group(1)) not in steps:
            fails.append(f"{f.name} has no step line in the block")

    slices = {}
    for part in get("Slices").split("·"):
        m = re.match(r"^\s*(S\d+):\s*(.*?)\s*$", part)
        if m:
            slices[m.group(1)] = [int(x) for x in m.group(2).split() if x.isdigit()]
    placed = [n for ns in slices.values() for n in ns]
    for n in steps:
        if placed.count(n) != 1:
            fails.append(f"step {n} is in {placed.count(n)} slices, not 1")
    for s, ns in slices.items():
        if not ns:
            fails.append(f"slice {s} is empty")

    completed_at = {}
    seq = list(slices)
    for s in seq:
        line = get(f"Slice {s}")
        if not line:
            fails.append(f"slice {s} has no `Slice {s} · Done when e2e …` line")
            continue
        if not line.startswith("Done when e2e"):
            fails.append(f"Slice {s} line does not open with `Done when e2e`")
        serves = set(re.findall(r"R\d+", (re.search(r"·\s*serves ([R\d\s]+)", line) or [None, ""])[1]))
        comp = set(re.findall(r"R\d+", (re.search(r"·\s*completes ([R\d\s]+)", line) or [None, ""])[1]))
        if not comp <= serves:
            fails.append(f"slice {s} completes {' '.join(sorted(comp - serves))} it does not serve: add them to its serves, or move the completes")
        for r in serves:
            if r in completed_at and seq.index(completed_at[r]) < seq.index(s):
                fails.append(f"slice {s} serves {r}, already completed by {completed_at[r]}: move the completes to the last slice serving it")
        for r in comp:
            if r in completed_at:
                fails.append(f"{r} completed by both {completed_at[r]} and {s}: keep it on the later one only")
            completed_at.setdefault(r, s)
        for r in serves - live:
            fails.append(f"slice {s} serves {r}, which is not a live requirement: drop it from serves")

    assumed = get("Assumed")
    for r in sorted(live, key=lambda x: int(x[1:])):
        if r in completed_at:
            continue
        if reqs[r]["level"] == "required" and not reqs[r]["env"]:
            fails.append(f"{r} is completed by no slice: add `completes {r}` to the last slice serving it, and a step serving it if none does")
        elif not re.search(rf"\b{r}\b", assumed):
            fails.append(f"{r} is completed by no slice and no Assumed line says why: complete it on a slice, or name it with why under Assumed")

    if a.previous:
        prev = pathlib.Path(a.previous)
        for n in steps:
            old = prev / f"step-{n}.md"
            new = out / f"step-{n}.md"
            if old.exists() and new.exists() and read(old).strip() != read(new).strip():
                fails.append(f"step {n} changed its body but kept its number: give it the next unused number")

    for f in fails:
        print(f"- FAIL {f}")
    print()
    print("PLAN CHECK: " + ("FAIL" if fails else "PASS"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
