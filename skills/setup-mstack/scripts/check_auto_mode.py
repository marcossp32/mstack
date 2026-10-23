#!/usr/bin/env python3
"""Check that Claude Code's auto mode allows what mstack does unattended.

Read-only: never writes a settings file. Prints one line per check,
`PASS · <check>` or `FAIL · <check> · <why> · fix: <what to do>`, then,
when an autoMode check failed, the block to add. Exit 0 all pass, 1 any FAIL.
Prints only the keys it checks, never the rest of the settings file.
"""
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REFERENCE = os.path.join(HERE, "..", "references", "auto-mode.md")


def load_block():
    text = open(REFERENCE, encoding="utf-8").read()
    match = re.search(r"## The block.*?```json\n(.*?)\n```", text, re.S)
    if not match:
        sys.exit("abort: no json block under '## The block' in references/auto-mode.md")
    block = json.loads(match.group(1))
    entries = [e for e in block["autoMode"]["allow"] if e != "$defaults"]
    return block, entries


def user_settings_path():
    root = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    return os.path.join(root, "settings.json")


def read_user_settings(path):
    if not os.path.exists(path):
        return {}, None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), None
    except (OSError, ValueError) as e:
        return {}, f"{path} is not valid JSON ({e.__class__.__name__})"


def claude_json(*args):
    exe = shutil.which("claude")
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "auto-mode", *args], capture_output=True, text=True,
                             encoding="utf-8", timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout)
    except ValueError:
        return None


def name(entry):
    return entry.split(":", 1)[0]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    block, entries = load_block()
    path = user_settings_path()
    settings, broken = read_user_settings(path)
    lines, auto_fail = [], False

    def report(ok, check, why="", fix="", auto=False):
        nonlocal auto_fail
        if ok:
            lines.append(f"PASS · {check}")
        else:
            lines.append(f"FAIL · {check} · {why} · fix: {fix}")
            auto_fail = auto_fail or auto

    if broken:
        report(False, "settings file", broken, f"repair the JSON in {path}, then run `claude doctor`")

    effective = claude_json("config")
    defaults = claude_json("defaults")
    if effective is not None and defaults is not None:
        allow = effective.get("allow", [])
        source = "`claude auto-mode config`"
        kept = all(rule in allow for rule in defaults.get("allow", []))
    else:
        raw = (settings.get("autoMode") or {}).get("allow") or []
        allow = raw
        source = path
        kept = "$defaults" in raw or not raw
        lines.append(f"NOTE · `claude auto-mode config` unavailable; read {path} only (managed settings not seen)")

    report(kept, "auto mode keeps the built-in allow rules",
           f"autoMode.allow in {path} lacks \"$defaults\", so it replaces them",
           f"add \"$defaults\" as the first entry of autoMode.allow in {path}", auto=True)

    for entry in entries:
        present = entry in allow
        stale = [a for a in allow if a != entry and name(a) == name(entry)]
        if present and not stale:
            report(True, f"auto mode entry '{name(entry)}'")
        elif stale:
            report(False, f"auto mode entry '{name(entry)}'", f"an older wording is in {source}",
                   f"replace it in {path} with the entry from the block below", auto=True)
        else:
            report(False, f"auto mode entry '{name(entry)}'", f"missing from {source}",
                   f"append it to autoMode.allow in {path} (block below)", auto=True)

    current = {name(e) for e in entries}
    for extra in allow:
        if extra.startswith("mstack ") and name(extra) not in current:
            report(False, f"auto mode entry '{name(extra)}'", "mstack no longer uses it",
                   f"remove it from autoMode.allow in {path}", auto=True)

    mode = (settings.get("permissions") or {}).get("defaultMode")
    report(mode == "auto", "permissions.defaultMode is auto",
           f"it is {json.dumps(mode)} in {path} (project files cannot set auto)",
           f"set \"permissions\": {{\"defaultMode\": \"auto\"}} in {path}, "
           "or start each mstack run with `claude --permission-mode auto`")

    print("\n".join(lines))
    if auto_fail:
        print(f"\nAdd to {path}, merged into the existing file: append to an existing "
              "autoMode.allow, keep \"$defaults\", never replace the list. "
              "Then run `claude auto-mode config` to confirm.\n")
        print(json.dumps(block, indent=2, ensure_ascii=False))
    return 1 if any(l.startswith("FAIL") for l in lines) else 0


if __name__ == "__main__":
    sys.exit(main())
