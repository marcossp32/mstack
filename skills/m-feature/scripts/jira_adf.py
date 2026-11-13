"""Converts text between Markdown and Jira's format (ADF) without losing anything.

Usage:
  jira_adf.py wrap INPUT.md OUTPUT.json   Markdown -> ADF, ready for --description-file or --body-file
  jira_adf.py issues INPUT.json           acli's --json output -> "=== KEY | title" and the description
  jira_adf.py comments INPUT.json         acli's --json output -> each comment with its date

Everything we write goes inside a single code block, which Jira stores as is.
When read, that block comes back identical. Text written by a person comes back as plain text.
"""
import json
import sys


def wrap(src, dst):
    text = open(src, encoding="utf-8").read()
    doc = {"version": 1, "type": "doc", "content": [
        {"type": "codeBlock", "attrs": {"language": "markdown"},
         "content": [{"type": "text", "text": text}]}]}
    json.dump(doc, open(dst, "w", encoding="utf-8"), ensure_ascii=False)


def plain(node):
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    kids = node.get("content", [])
    if node.get("type") == "doc" and len(kids) == 1 and kids[0].get("type") == "codeBlock":
        return "".join(k.get("text", "") for k in kids[0].get("content", []))
    if node.get("type") == "text":
        return node.get("text", "")
    if node.get("type") == "hardBreak":
        return "\n"
    inner = "".join(plain(k) for k in kids)
    t = node.get("type")
    if t == "heading":
        return "#" * node.get("attrs", {}).get("level", 1) + " " + inner + "\n\n"
    if t == "listItem":
        return "- " + inner.strip() + "\n"
    if t in ("paragraph", "codeBlock", "blockquote", "rule"):
        return inner + "\n\n"
    return inner


def walk(obj, keys):
    """Finds the objects with those keys, whatever the shape of acli's JSON."""
    if isinstance(obj, dict):
        if all(k in obj for k in keys):
            yield obj
            return
        for v in obj.values():
            yield from walk(v, keys)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v, keys)


def field(d, name):
    return d.get(name, (d.get("fields") or {}).get(name))


def issues(src):
    for d in walk(json.load(open(src, encoding="utf-8")), ["key"]):
        if field(d, "summary") is None and field(d, "description") is None:
            continue
        print(f"=== {d['key']} | {field(d, 'summary') or ''}")
        print(plain(field(d, "description")).rstrip())


def comments(src):
    for d in walk(json.load(open(src, encoding="utf-8")), ["body"]):
        print(f"<!-- {d.get('created', '')} -->")
        print(plain(d["body"]).rstrip() + "\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    mode, args = sys.argv[1], sys.argv[2:]
    if mode == "wrap":
        wrap(*args)
    elif mode == "issues":
        issues(*args)
    elif mode == "comments":
        comments(*args)
    else:
        sys.exit(__doc__)
