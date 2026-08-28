#!/usr/bin/env node
'use strict';

/**
 * Secret に埋まっている link_key 名と件数だけ出す。
 * URL は出さない。実投稿しない。cron は触らない。
 *
 *   node scripts/print-overlay-status.js
 */

const { loadLinks } = require('../src/util');

function overlayStatus(links) {
  const names = Object.entries(links)
    .filter(([k, v]) => !k.startsWith('_') && String(v || '').trim())
    .map(([k]) => k)
    .sort();
  const line = `filled ${names.length}\nkeys ${names.join(',') || '(none)'}\n`;
  if (/https?:\/\//i.test(line) || names.some((n) => /https?:/i.test(n))) {
    throw new Error('url leak');
  }
  return { names, line };
}

function main() {
  const { names, line } = overlayStatus(loadLinks());
  process.stdout.write(line);
  if (names.includes('申込_auひかり')) {
    console.error('WARN 申込_auひかり is filled; SNS listing is missing so this key should stay empty');
    process.exit(1);
  }
}

if (require.main === module) {
  try {
    main();
  } catch (err) {
    console.error(`print-overlay-status failed: ${err.message}`);
    process.exit(1);
  }
}

module.exports = { overlayStatus };
