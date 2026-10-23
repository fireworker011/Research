'use strict';

const { workPath, readJSON, writeJSON, nowIso } = require('./util');

const COMMANDER_PATH = workPath('state', 'commander.json');
const ISSUE_TITLE = 'CW — 司令塔';
const KILL_COMMANDS = Object.freeze(['HALT', 'PAPER_ONLY']);
const COMMAND_TYPES = Object.freeze([
  'HALT',
  'PAPER_ONLY',
  'JOB',
  'SKIP',
  'SENT',
  'MSG',
  'CONTRACT',
  'MATERIAL',
  'MAKE',
  'DRAFT',
  'REVISE',
  'DELIVERED',
  'PAID',
  'REJECT',
  'PROFILE',
  'DESK'
]);
const WITH_ID = new Set(['JOB', 'SKIP', 'SENT', 'MSG', 'CONTRACT', 'MATERIAL', 'MAKE', 'DRAFT', 'REVISE', 'DELIVERED', 'PAID', 'REJECT']);
const WITH_PAYLOAD = new Set(['JOB', 'MSG', 'CONTRACT', 'MATERIAL', 'MAKE', 'DRAFT', 'REVISE']);
const NOTIFY_RE = /^\s*cw-(desk|apply|reply|brief|make|deliver|qa|profile|note):/m;
const FIRST_LINE_RE = /^\s*CW:\s*([A-Z_]+)\b(.*)$/i;

function defaultCommander() {
  return {
    command: 'PAPER_ONLY',
    source: 'init',
    reason: 'no official apply API; sending stays human',
    updated_at: '2026-09-12T00:00:00.000Z',
    previous: null,
    issue_number: ''
  };
}

function loadCommander() {
  return readJSON(COMMANDER_PATH, defaultCommander());
}

function saveCommander(data) {
  return writeJSON(COMMANDER_PATH, data);
}

function isNotifyComment(body) {
  return NOTIFY_RE.test(String(body || ''));
}

function parseCommand(body) {
  const lines = String(body || '').replace(/\r/g, '').split('\n');
  const idx = lines.findIndex((l) => FIRST_LINE_RE.test(l));
  if (idx === -1) return null;
  const m = lines[idx].match(FIRST_LINE_RE);
  const type = m[1].toUpperCase();
  if (!COMMAND_TYPES.includes(type)) return null;
  const rest = m[2].trim();
  const tokens = rest ? rest.split(/\s+/) : [];
  let id = null;
  const opts = {};
  const extra = [];
  for (const tok of tokens) {
    if (!id && /^\d{4,12}$/.test(tok) && WITH_ID.has(type)) id = tok;
    else if (/^[a-z_]+=\S+$/i.test(tok)) {
      const [k, v] = tok.split('=');
      opts[k.toLowerCase()] = v;
    } else extra.push(tok);
  }
  if (WITH_ID.has(type) && !id) return { type, id: null, opts, extra, payload: '', error: 'missing_id' };
  const payload = WITH_PAYLOAD.has(type) ? lines.slice(idx + 1).join('\n').trim() : '';
  return { type, id, opts, extra, payload, error: null };
}

function applyKill(current, { command, source, reason, now }) {
  if (!KILL_COMMANDS.includes(command)) throw new Error(`unknown command: ${command}`);
  return {
    command,
    source,
    reason: reason || '',
    updated_at: nowIso(now),
    previous: current?.command || null,
    issue_number: current?.issue_number || ''
  };
}

module.exports = {
  COMMANDER_PATH,
  ISSUE_TITLE,
  KILL_COMMANDS,
  COMMAND_TYPES,
  WITH_ID,
  WITH_PAYLOAD,
  defaultCommander,
  loadCommander,
  saveCommander,
  isNotifyComment,
  parseCommand,
  applyKill
};
