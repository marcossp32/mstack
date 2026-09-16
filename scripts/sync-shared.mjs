#!/usr/bin/env node
// `npx skills` installs each skill folder on its own, so a skill cannot link
// outside itself. Documents several skills read live once in shared/ and are
// copied into the references/ folder of every skill that reads them.
//
//   node scripts/sync-shared.mjs          write the copies
//   node scripts/sync-shared.mjs --check  exit 1 if any copy has drifted

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');

const readers = {
  'writing.md': ['m-feature', 'm-scan', 'm-grilling', 'm-research', 'm-plan', 'm-build', 'm-review', 'm-prove'],
  'design-checks.md': ['m-plan', 'm-review'],
  'proving-tests.md': ['m-build', 'm-review'],
  'github.md': ['m-feature', 'm-plan'],
  'routing.md': ['m-feature', 'm-research', 'm-prove'],
};

const check = process.argv.includes('--check');
let stale = 0;

for (const [file, skills] of Object.entries(readers)) {
  const expected =
    `<!-- Copied from shared/${file} by scripts/sync-shared.mjs. Edit the source, not this copy. -->\n\n` +
    readFileSync(join(root, 'shared', file), 'utf8');

  for (const skill of skills) {
    const rel = `skills/${skill}/references/${file}`;
    const dest = join(root, rel);
    if (existsSync(dest) && readFileSync(dest, 'utf8') === expected) continue;

    if (check) {
      console.error(`stale: ${rel}`);
      stale++;
      continue;
    }
    mkdirSync(dirname(dest), { recursive: true });
    writeFileSync(dest, expected);
    console.log(`wrote: ${rel}`);
  }
}

if (stale) {
  console.error(`\n${stale} stale ${stale === 1 ? 'copy' : 'copies'}. Run: node scripts/sync-shared.mjs`);
  process.exit(1);
}
