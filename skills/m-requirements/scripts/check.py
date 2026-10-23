#!/usr/bin/env python3
"""Check an m-requirements block against the frozen spec it was drawn from.

  check.py --spec <frozen spec file> --out <requirements block file>

Checks what a reader can verify without trusting the agent:
  - R ids are R1..Rn, unique, in order; each line has the shape
    R<n> · <asked | derived> · "<requirement>" · bound <domain | —> · from "<excerpt>"[ + "<excerpt>"] | from R<m>
    (`derived · required by D<k>` and a trailing ` · retired by D<k>` parse, but fail: a debate adds them later);
  - every quoted excerpt (R, Not doing, Considered, Contradictions, Open decisions, Trace) appears
    in the spec verbatim, whitespace runs aside;
  - an asked line quotes the spec; a derived line quotes it or names an earlier R line;
  - a requirement with an absolute or a set word (every, any, all, never, ...) has a bound, not —;
  - a contradiction quotes at least two excerpts;
  - an open decision is not a yes/no question and offers no options;
  - the Trace covers the whole spec: removing every traced sentence leaves no words;
    every id a Trace line names exists.
Exit 0 = PASS, 1 = FAIL (each failure printed), 2 = bad usage. WARN lines never fail.
"""
import argparse
import re
import sys

SECTIONS = ["Requirements", "Not doing", "Considered", "Contradictions",
            "Open decisions", "Assumed", "Laziest build", "Trace"]
ABSOLUTES = re.compile(r"\b(every|each|any|all|both|never|always|whenever|everyone|everything|anything|anyone|100%)\b", re.I)
YES_NO = re.compile(r"^(should|shall|do|does|did|is|are|was|were|can|could|will|would|must|may|which|whether)\b", re.I)
OPTION_HINT = re.compile(r"\b(or|either|e\.g\.|such as|for example|option|alternatively|instead of|versus|vs\.?)\b", re.I)
R_LINE = re.compile(r'^R(\d+) · (asked|derived(?: · required by D\d+)?) · "([^"]+)" · bound (.+?) · from (.+?)( · retired by D\d+)?$')
QUOTE = re.compile(r'"([^"]+)"')


def collapse(text):
    return re.sub(r"\s+", " ", text).strip()


def sections(block):
    out, cur = {}, None
    for line in block.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            cur = m.group(1)
            out[cur] = []
        elif cur is not None and line.strip():
            out[cur].append(line.strip())
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    try:
        spec_raw = open(a.spec, encoding="utf-8").read()
        block = open(a.out, encoding="utf-8").read()
    except OSError as e:
        print(f"usage: {e}")
        return 2
    spec = collapse(spec_raw)
    fails, warns = [], []

    def in_spec(excerpt, where):
        if collapse(excerpt) not in spec:
            fails.append(f'{where} · excerpt not in spec verbatim: "{excerpt}"')

    sec = sections(block)
    for name in SECTIONS:
        if name not in sec:
            fails.append(f"missing section ## {name}")
        elif not sec[name]:
            fails.append(f"## {name} is empty: write `none`")
    for name in sec:
        if name not in SECTIONS:
            warns.append(f"unknown section ## {name}")

    def items(name):
        return [l for l in sec.get(name, []) if l.lower() != "none"]

    # Requirements
    ids, levels = [], {}
    for line in items("Requirements"):
        m = R_LINE.match(line)
        if not m:
            fails.append(f"R line shape: {line}")
            continue
        n, level, words, bound, src = int(m.group(1)), m.group(2), m.group(3), m.group(4), m.group(5)
        rid = f"R{n}"
        if n != len(ids) + 1:
            fails.append(f"{rid} · ids must run R1..Rn in order, unique (expected R{len(ids) + 1})")
        ids.append(rid)
        levels[rid] = level
        if level.startswith("derived · required"):
            fails.append(f"{rid} · `required by D<k>` comes from a debate, never from m-requirements")
        if m.group(6):
            fails.append(f"{rid} · `retired by D<k>` comes from a debate, never from m-requirements")
        if ABSOLUTES.search(words) and bound.strip() in ("—", "-", ""):
            fails.append(f'{rid} · "{ABSOLUTES.search(words).group(0)}" needs a bound, not —')
        ref = re.fullmatch(r"R(\d+)", src.strip())
        if ref:
            if level == "asked":
                fails.append(f"{rid} · an asked line quotes the spec, never another line")
            elif f"R{ref.group(1)}" not in ids[:-1] or levels.get(f"R{ref.group(1)}") != "asked":
                fails.append(f"{rid} · from {src.strip()}: not an earlier asked line")
            continue
        quotes = QUOTE.findall(src)
        rest = QUOTE.sub("", src).replace("+", "").strip()
        if not quotes or rest:
            fails.append(f'{rid} · from must be "<excerpt>"[ + "<excerpt>"] or R<m>: {src}')
        for q in quotes:
            in_spec(q, rid)

    # Excerpt-bearing sections
    for line in items("Not doing"):
        qs = QUOTE.findall(line.split(" · from ", 1)[1]) if " · from " in line else []
        if not qs:
            fails.append(f"Not doing without a from excerpt: {line}")
        for q in qs:
            in_spec(q, "Not doing")
    for line in items("Considered"):
        if " · why " not in line:
            fails.append(f"Considered without why: {line}")
        if " · from " in line:
            for q in QUOTE.findall(line.split(" · from ", 1)[1]):
                in_spec(q, "Considered")
    for line in items("Contradictions"):
        m = re.match(r"^(C\d+) · (.+?) · reading ", line)
        qs = QUOTE.findall(m.group(2)) if m else []
        if len(qs) < 2:
            fails.append(f"Contradiction needs two excerpts: {line}")
        for q in qs:
            in_spec(q, m.group(1) if m else "Contradiction")
        if not re.search(r" · undo (hard|easy)\b", line):
            fails.append(f"Contradiction without undo hard|easy: {line}")
    for line in items("Open decisions"):
        m = re.match(r"^(O\d+) · (.+?) · from (.+?)(?: · facts .*)?$", line)
        if not m:
            fails.append(f"Open decision shape: {line}")
            continue
        problem = m.group(2)
        if YES_NO.match(problem):
            fails.append(f"{m.group(1)} · a yes/no or choice question, not a neutral problem")
        if OPTION_HINT.search(problem):
            warns.append(f'{m.group(1)} · "{OPTION_HINT.search(problem).group(0)}" may name an option')
        for q in QUOTE.findall(m.group(3)):
            in_spec(q, m.group(1))
    for line in items("Assumed"):
        if " · why " not in line:
            fails.append(f"Assumed without why: {line}")

    # Trace: coverage of the whole spec
    known = set(ids)
    known |= {re.match(r"^(C\d+|O\d+)", l).group(1) for l in items("Contradictions") + items("Open decisions")
              if re.match(r"^(C\d+|O\d+)", l)}
    remaining = spec
    for line in sec.get("Trace", []):
        m = re.match(r'^"(.+)" → (.+)$', line)
        if not m:
            fails.append(f"Trace shape: {line}")
            continue
        sentence, target = collapse(m.group(1)), m.group(2)
        if sentence not in spec:
            fails.append(f'Trace sentence not in spec verbatim: "{m.group(1)}"')
        remaining = remaining.replace(sentence, " ", 1)
        for tid in re.findall(r"\b([RCO]\d+)\b", target):
            if tid not in known:
                fails.append(f"Trace names {tid}, which does not exist")
        if not re.search(r"\b([RCO]\d+)\b|Not doing|Considered|context · \S", target):
            fails.append(f"Trace target must be ids, Not doing, Considered or context · <why>: {line}")
    remaining = re.sub(r"(?<!\w)\d+[.)](?!\w)", " ", remaining)  # list markers
    left = re.findall(r"[^\W_]{2,}", remaining)
    if left:
        fails.append("spec text no Trace line covers: " + collapse(remaining)[:400])

    for w in warns:
        print("WARN", w)
    for f in fails:
        print("FAIL", f)
    print("PASS" if not fails else f"FAIL · {len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
