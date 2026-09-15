'use strict';

const fs = require('fs');
const { workPath, ensureDir, readText, parseYenInt } = require('./util');
const path = require('path');

const LEDGER_PATH = workPath('data', 'cw_ledger.csv');
const HEADER = 'date,job_id,event,yen,note';

function parseLedger(csvText) {
  const rows = [];
  for (const line of String(csvText || '').split(/\r?\n/)) {
    if (!line.trim() || line.startsWith('#') || line.startsWith('date,')) continue;
    const [date, job_id, event, yen, ...rest] = line.split(',');
    rows.push({ date, job_id, event, yen: Number(yen), note: rest.join(',') });
  }
  return rows;
}

function validatePaid({ date, jobId, yenRaw, note }) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(date || ''))) return { ok: false, reason: 'bad_date' };
  if (!/^\d+$/.test(String(jobId || ''))) return { ok: false, reason: 'bad_job_id' };
  if (/,/.test(String(yenRaw || ''))) return { ok: false, reason: 'comma_number' };
  const yen = parseYenInt(yenRaw);
  if (yen === null) return { ok: false, reason: 'bad_yen' };
  if (/カタログ|公開表示|予定|見込/.test(String(note || ''))) return { ok: false, reason: 'catalog_yen' };
  if (/https?:\/\//i.test(String(note || ''))) return { ok: false, reason: 'url' };
  return { ok: true, row: { date, job_id: String(jobId), event: 'PAID', yen, note: String(note || '').replace(/,/g, ' ').trim() } };
}

function appendRow(csvText, row) {
  const lines = String(csvText || '').split(/\r?\n/).filter((l) => l.trim());
  const out = lines.length && lines[0].startsWith('date,') ? lines : [HEADER, ...lines];
  const filtered = out.filter((l) => {
    if (l.startsWith('date,')) return true;
    const cols = l.split(',');
    return !(cols[1] === row.job_id && cols[2] === row.event);
  });
  filtered.push([row.date, row.job_id, row.event, row.yen, row.note].join(','));
  return `${filtered.join('\n')}\n`;
}

function total(csvText) {
  return parseLedger(csvText).filter((r) => r.event === 'PAID' && Number.isFinite(r.yen)).reduce((s, r) => s + r.yen, 0);
}

function recordPaid({ date, jobId, yenRaw, note }) {
  const v = validatePaid({ date, jobId, yenRaw, note });
  if (!v.ok) return v;
  ensureDir(path.dirname(LEDGER_PATH));
  const prev = readText(LEDGER_PATH, `${HEADER}\n`);
  fs.writeFileSync(LEDGER_PATH, appendRow(prev, v.row));
  return { ok: true, row: v.row, total: total(readText(LEDGER_PATH, '')) };
}

function ledgerTotal() {
  return total(readText(LEDGER_PATH, ''));
}

module.exports = { LEDGER_PATH, HEADER, parseLedger, validatePaid, appendRow, total, recordPaid, ledgerTotal };
