#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const ISSUE_TITLE = 'Affiliate — 確定円';
const HEADER = 'date,source,program,clicks,cv,approved_yen,note';
const CSV_PATH = path.join(__dirname, '../data/conversions.csv');
const LINE_RE = /^\s*A8_YEN:\s*(\d{4}-\d{2}-\d{2}),(A8),([^,\n]+),(\d+),(\d+),(\d+),(.*)\s*$/;

function parseYenComment(body) {
  const raw = String(body || '').trim();
  if (!raw) return { skipped: true, reason: 'empty' };
  if (/https?:\/\//i.test(raw)) return { skipped: true, reason: 'url' };
  const line = raw.split(/\r?\n/).map((s) => s.trim()).find((s) => /^A8_YEN:/i.test(s));
  if (!line) return { skipped: true, reason: 'no_command' };
  if (/,(\d{1,3}(?:,\d{3})+)(?:,|$)/.test(line) && !/"\d{1,3}(?:,\d{3})+"/.test(line)) {
    return { skipped: true, reason: 'comma_number' };
  }
  const m = line.match(LINE_RE);
  if (!m) return { skipped: true, reason: 'bad_format' };
  const row = {
    date: m[1],
    source: m[2],
    program: m[3].trim(),
    clicks: Number(m[4]),
    cv: Number(m[5]),
    approved_yen: Number(m[6]),
    note: m[7].trim()
  };
  if (!row.program) return { skipped: true, reason: 'bad_program' };
  if (/https?:\/\//i.test(row.note) || /https?:\/\//i.test(row.program)) {
    return { skipped: true, reason: 'url' };
  }
  if (/カタログ/.test(row.note) && row.approved_yen > 0) {
    return { skipped: true, reason: 'catalog_yen' };
  }
  return { skipped: false, row };
}

function applyRow(csvText, row) {
  const lines = String(csvText || '').replace(/^\uFEFF/, '').split(/\r?\n/);
  const out = [];
  let hasHeader = false;
  for (const line of lines) {
    if (!line.trim()) continue;
    if (line.startsWith('#')) {
      out.push(line);
      continue;
    }
    if (!hasHeader && line.startsWith('date,')) {
      hasHeader = true;
      out.push(HEADER);
      continue;
    }
    const cols = line.split(',');
    if (cols.length >= 3 && cols[0] === row.date && cols[1] === row.source && cols[2] === row.program) {
      continue;
    }
    out.push(line);
  }
  if (!hasHeader) out.unshift(HEADER);
  const note = row.note.replace(/,/g, ' ');
  out.push([row.date, row.source, row.program, row.clicks, row.cv, row.approved_yen, note].join(','));
  return `${out.join('\n')}\n`;
}

function selfTest() {
  const ok = parseYenComment('A8_YEN: 2026-09-09,A8,all,33,0,0,screen');
  if (ok.skipped || ok.row.approved_yen !== 0) throw new Error('valid row');
  const url = parseYenComment('A8_YEN: 2026-09-09,A8,all,1,0,0,https://example.com');
  if (!url.skipped || url.reason !== 'url') throw new Error('url');
  const cw = parseYenComment('A8_YEN: 2026-09-09,CW,all,1,0,100,no');
  if (!cw.skipped) throw new Error('cw');
  const comma = parseYenComment('A8_YEN: 2026-09-09,A8,all,1,0,1,000,screen');
  if (!comma.skipped) throw new Error('comma');
  const cat = parseYenComment('A8_YEN: 2026-09-09,A8,all,1,0,15000,カタログ');
  if (!cat.skipped || cat.reason !== 'catalog_yen') throw new Error('catalog');
  const csv = applyRow('date,source,program,clicks,cv,approved_yen,note\n2026-08-27,A8,all,33,0,0,old\n', ok.row);
  if (!csv.includes('2026-09-09,A8,all,33,0,0,screen')) throw new Error('append');
  if ((csv.match(/2026-09-09,A8,all,/g) || []).length !== 1) throw new Error('dedupe');
  const created = applyRow('', ok.row);
  if (!created.startsWith(HEADER)) throw new Error('missing csv header');
  if (!created.includes('2026-09-09,A8,all,33,0,0,screen')) throw new Error('missing csv row');
  process.stdout.write('apply-a8-yen self-test ok\n');
}

function readEvent() {
  const p = process.env.GITHUB_EVENT_PATH;
  if (p && fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, 'utf-8'));
  return null;
}

function main() {
  if (process.argv.includes('--self-test')) {
    selfTest();
    return;
  }
  const event = readEvent();
  if (event) {
    if (event.issue?.title !== ISSUE_TITLE) {
      console.log(JSON.stringify({ skipped: true, reason: 'not_yen_issue' }));
      return;
    }
    if ((event.comment?.user?.login || '') === 'github-actions[bot]') {
      console.log(JSON.stringify({ skipped: true, reason: 'actions-bot' }));
      return;
    }
    const parsed = parseYenComment(event.comment?.body || '');
    if (parsed.skipped) {
      console.log(JSON.stringify({ skipped: true, reason: parsed.reason }));
      return;
    }
    const prev = fs.existsSync(CSV_PATH) ? fs.readFileSync(CSV_PATH, 'utf-8') : `${HEADER}\n`;
    const next = applyRow(prev, parsed.row);
    fs.writeFileSync(CSV_PATH, next);
    console.log(JSON.stringify({ skipped: false, date: parsed.row.date, approved_yen: parsed.row.approved_yen }));
    return;
  }
  console.log(JSON.stringify({ skipped: true, reason: 'no_event' }));
}

module.exports = { ISSUE_TITLE, parseYenComment, applyRow };

if (require.main === module) main();
