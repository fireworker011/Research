#!/usr/bin/env node
'use strict';

/**
 * Secret 重ねが空キーを埋めたとき、link_key 付きテンプレが本文に載るか。
 * URL はログに出さない。実投稿しない。
 *
 *   node scripts/verify-secret-overlay.js
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');
const { loadLinks, redactAffiliateUrls, escapeCSV, readJSON } = require('../src/util');
const seed = require('../data/seed_templates.json');

function resolveLink(row, links) {
  return links[row.link_key] || links[row.genre] || '';
}

function jstSlotMinutesAgo(mins) {
  const t = new Date(Date.now() - mins * 60000 + 9 * 3600 * 1000);
  const date = t.toISOString().split('T')[0];
  const hh = String(t.getUTCHours()).padStart(2, '0');
  const mm = String(t.getUTCMinutes()).padStart(2, '0');
  return { date, time: `${hh}:${mm}` };
}

function pickDueSlot(posted) {
  for (const mins of [4, 8, 12, 17, 23, 31]) {
    const slot = jstSlotMinutesAgo(mins);
    if (!posted[`${slot.date}_${slot.time}_education`]) return slot;
  }
  throw new Error('no free dry-run slot');
}

function assertPosterDryRunRedacts(dummy) {
  const t = seed.posting_templates.find((x) => x.id === 'education_20260828_eyes_01');
  if (!t) throw new Error('missing education_20260828_eyes_01');
  const posted = readJSON(path.join(__dirname, '..', 'output', 'state', 'posted.json'), { posted: {} }).posted || {};
  const slot = pickDueSlot(posted);
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'poster-verify-'));
  const csvPath = path.join(dir, 'sched.csv');
  const header = 'date,time,account,platform,genre,content,emoji,engagement_prediction,cta_type,link_key';
  const fields = [slot.date, slot.time, 'education', 'threads', '教育', t.content, t.emoji || '', 'medium', 'direct', '教育_アイズ'];
  fs.writeFileSync(csvPath, `${header}\n${fields.map(escapeCSV).join(',')}\n`);
  const result = spawnSync(process.execPath, ['src/threads-poster.js', '--dry-run'], {
    cwd: path.join(__dirname, '..'),
    encoding: 'utf-8',
    timeout: 20000,
    env: {
      ...process.env,
      AFFILIATE_LINKS_JSON: JSON.stringify({ 教育_アイズ: dummy }),
      SCHEDULE_CSV: csvPath,
      CATCHUP_HOURS: '6',
      JITTER: '0'
    }
  });
  const out = `${result.stdout || ''}${result.stderr || ''}`;
  if (result.status !== 0) {
    throw new Error(`poster dry-run exit ${result.status}: ${out.slice(0, 500)}`);
  }
  if (out.includes('example.invalid')) throw new Error('poster dry-run leaked URL');
  if (!/投稿対象 [1-9]/.test(out)) {
    throw new Error(`poster dry-run had no due posts: ${out.slice(0, 400)}`);
  }
  if (!out.includes('[link]')) throw new Error('poster dry-run did not redact');
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

  assertPosterDryRunRedacts(dummy);

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
