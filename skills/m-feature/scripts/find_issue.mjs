#!/usr/bin/env node
// find-issue for the md tracker: open issues and states carrying a label whose
// text holds at least half the query's words.
//
//   node find_issue.mjs <label> <query> <dir> [<dir> ...]
//
// Reads every .md file under each dir (a missing dir is skipped; files under a
// `pending` folder are comments, not issues). A file counts when its front
// matter lists the label and says `status: open`. Prints, per match,
// `=== <path> | <title>` then its body; prints `no match` when none does.
// Exit 0 with or without matches, 2 on a wrong call. Node's own modules only.
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const usage = "usage: node find_issue.mjs <label> <query> <dir> [<dir> ...]\n  example: node find_issue.mjs found-by-prove 'login button 500' /repo/.git/mstack/md .mstack/issues";
const args = process.argv.slice(2);
if (args.includes("--help")) { console.log(usage); process.exitCode = 0; }
else if (args.some((a) => a.startsWith("--"))) { console.log(`unknown flag; this script takes no flags but --help\n${usage}`); process.exitCode = 2; }
else if (args.length < 3) { console.log(usage); process.exitCode = 2; }
else {
  const [label, query, ...roots] = args;
  // words of three letters or more: shorter ones (a, of, to) match every file
  const words = (query.toLowerCase().match(/\w+/g) || []).filter((w) => w.length > 2);
  const files = [];
  const walk = (d) => {
    for (const e of readdirSync(d, { withFileTypes: true }).sort((a, b) => (a.name < b.name ? -1 : 1))) {
      const p = join(d, e.name);
      if (e.isDirectory()) { if (e.name !== "pending") walk(p); }
      else if (e.isFile() && e.name.endsWith(".md")) files.push(p);
    }
  };
  for (const r of roots) if (existsSync(r) && statSync(r).isDirectory()) walk(r);
  let found = 0;
  for (const f of files) {
    const t = readFileSync(f, "utf8").replace(/\r\n/g, "\n");
    const m = t.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
    if (!m) continue;
    const meta = Object.fromEntries(m[1].split("\n").filter((l) => l.includes(":")).map((l) => [l.slice(0, l.indexOf(":")).trim(), l.slice(l.indexOf(":") + 1).trim()]));
    const labels = (meta.labels || "").split(",").map((x) => x.trim());
    if (!labels.includes(label) || meta.status !== "open") continue;
    const low = t.toLowerCase();
    // at least half the query's words: a reworded title of the same break still matches
    if (words.filter((w) => low.includes(w)).length * 2 < words.length) continue;
    found++;
    console.log(`=== ${f.split(String.fromCharCode(92)).join("/")} | ${meta.title || ""}\n${m[2]}`);
  }
  if (!found) console.log("no match");
  process.exitCode = 0;
}
