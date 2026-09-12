'use strict';

const path = require('path');
const { OUTPUT_DIR, readJSON, writeJSON } = require('./util');

const COMMANDER_PATH = path.join(OUTPUT_DIR, 'state', 'commander.json');
const ISSUE_TITLE = 'CW — 司令塔';
const COMMANDS = ['HALT', 'PAPER_ONLY'];
const COMMAND_RE = /^\s*CW:\s*(HALT|PAPER_ONLY)\b/im;
const EVENT_RE = /^\s*CW:\s*(SENT|CONTRACT|REJECT)\s+(\d+)\b/im;
const DESK_RE = /^\s*cw-desk:/m;

function defaultCommander() {
  return {
    command: 'PAPER_ONLY',
    source: 'init',
    reason: 'no official apply API; live send stays human',
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

function parseCommandText(text) {
  const m = String(text || '').match(COMMAND_RE);
  if (!m) return null;
  const command = m[1].toUpperCase();
  if (!COMMANDS.includes(command)) return null;
  return command;
}

function parseQueueEvent(text) {
  const m = String(text || '').match(EVENT_RE);
  if (!m) return null;
  return { type: m[1].toUpperCase(), id: m[2] };
}

function isDeskComment(body) {
  return DESK_RE.test(String(body || ''));
}

function applyCommand(current, { command, source, reason, now }) {
  if (!COMMANDS.includes(command)) throw new Error(`unknown command: ${command}`);
  return {
    command,
    source,
    reason: reason || '',
    updated_at: (now || new Date()).toISOString(),
    previous: current?.command || null,
    issue_number: current?.issue_number || ''
  };
}

module.exports = {
  ISSUE_TITLE,
  COMMANDS,
  COMMANDER_PATH,
  defaultCommander,
  loadCommander,
  saveCommander,
  parseCommandText,
  parseQueueEvent,
  isDeskComment,
  applyCommand
};
