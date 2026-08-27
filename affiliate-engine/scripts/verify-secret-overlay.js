#!/usr/bin/env node
'use strict';

/**
 * Secret 重ねが空キーを埋めたとき、link_key 付きテンプレが本文に載るか。
 * URL はログに出さない。実投稿しない。
 *
 *   node scripts/verify-secret-overlay.js
 */

const { loadLinks } = require('../src/util');
const seed = require('../data/seed_templates.json');

function resolveLink(row, links) {
  return links[row.link_key] || links[row.genre] || '';
}

function main() {
  const dummy = 'https://example.invalid/secret-overlay-test';
  const prev = process.env.AFFILIATE_LINKS_JSON;
  process.env.AFFILIATE_LINKS_JSON = JSON.stringify({
    転職_neo: dummy,
    教育_N高: dummy,
    教育_アイズ: dummy,
    転職_チケット: dummy
  });
  const links = loadLinks();
  const dumped = JSON.stringify({
    filled: Object.keys(links).filter((k) => !k.startsWith('_') && String(links[k] || '').trim())
  });
  if (dumped.includes('example.invalid')) throw new Error('verify leaked a URL');

  const { redactAffiliateUrls } = require('../src/util');
  const redacted = redactAffiliateUrls(`see ${dummy} #PR`);
  if (redacted.includes('example.invalid')) throw new Error('redact leaked a URL');
  if (!redacted.includes('[link]')) throw new Error('redact did not replace URL');

  const ids = [
    'career_20260828_neo_01',
    'education_20260828_nko_01',
    'education_20260828_eyes_01',
    'career_20260828_ticket_01'
  ];
  for (const id of ids) {
    const t = seed.posting_templates.find((x) => x.id === id);
    if (!t) throw new Error(`missing template ${id}`);
    const link = resolveLink(t, links);
    if (!link) throw new Error(`empty link for ${id}`);
    if (!String(t.content).includes('{{AFFILIATE_LINK}}')) throw new Error(`${id} has no placeholder`);
    const text = t.content.replaceAll('{{AFFILIATE_LINK}}', link);
    if (!text.includes(dummy)) throw new Error(`${id} did not substitute`);
    if (!/#PR/i.test(text)) throw new Error(`${id} missing #PR`);
  }

  const emptyEnv = { ...process.env };
  delete emptyEnv.AFFILIATE_LINKS_JSON;
  process.env.AFFILIATE_LINKS_JSON = '';
  const empty = loadLinks();
  for (const key of ['転職_neo', '教育_N高', '教育_アイズ', '転職_チケット']) {
    if (String(empty[key] || '').trim()) throw new Error(`${key} should stay empty without secret`);
  }

  if (prev === undefined) delete process.env.AFFILIATE_LINKS_JSON;
  else process.env.AFFILIATE_LINKS_JSON = prev;
  console.log('verify-secret-overlay ok');
}

try {
  main();
} catch (err) {
  console.error(`verify-secret-overlay failed: ${err.message}`);
  process.exit(1);
}
