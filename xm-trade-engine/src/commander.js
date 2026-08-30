'use strict';

const { COMMANDS } = require('./risk');
const { readJSON, writeJSON, OUTPUT_DIR } = require('./util');
const path = require('path');

const COMMANDER_PATH = path.join(OUTPUT_DIR, 'state', 'commander.json');
const ISSUE_TITLE = 'XM Trade — 日次レポート';
const COMMAND_RE = /(?:KILL_SWITCH|COMMAND)\s*:\s*(HALT|PAPER_ONLY|RESUME|REDUCE_RISK)\b/i;

function defaultCommander() {
  return {
    command: 'PAPER_ONLY',
    source: 'init',
    reason: 'live is gated until a human enables it',
    risk_multiplier: 1,
    updated_at: '2026-08-30T00:00:00.000Z'
  };
}

function loadCommander() {
  return readJSON(COMMANDER_PATH, defaultCommander());
}

function saveCommander(data) {
  writeJSON(COMMANDER_PATH, data);
  return data;
}

function parseCommandText(text) {
  const m = String(text || '').match(COMMAND_RE);
  if (!m) return null;
  const command = m[1].toUpperCase();
  if (!COMMANDS.includes(command)) return null;
  return command;
}

function applyCommand(current, { command, source, reason, now }) {
  if (!COMMANDS.includes(command)) throw new Error(`unknown command: ${command}`);
  return {
    command,
    source,
    reason: reason || '',
    risk_multiplier: command === 'REDUCE_RISK' ? 0.5 : 1,
    updated_at: (now || new Date()).toISOString(),
    previous: current?.command || null
  };
}

async function fetchIssueComments({ token, repo, title }) {
  const headers = {
    Authorization: `token ${token}`,
    Accept: 'application/vnd.github.v3+json'
  };
  const base = `https://api.github.com/repos/${repo}`;
  const searchRes = await fetch(`${base}/issues?state=open&per_page=100`, { headers });
  const existing = await searchRes.json().catch(() => []);
  const found = Array.isArray(existing) ? existing.find((i) => i.title === title) : null;
  if (!found) return { issue: null, comments: [] };
  const commentsRes = await fetch(`${base}/issues/${found.number}/comments?per_page=100`, { headers });
  const comments = await commentsRes.json().catch(() => []);
  return { issue: found, comments: Array.isArray(comments) ? comments : [] };
}

function latestCommandFromComments(comments) {
  let best = null;
  for (const c of comments) {
    const command = parseCommandText(c.body);
    if (!command) continue;
    const ts = Date.parse(c.updated_at || c.created_at || 0);
    if (!best || ts >= best.ts) {
      best = {
        command,
        source: 'grok-bot-issue',
        reason: `issue comment ${c.id}`,
        ts,
        updated_at: c.updated_at || c.created_at
      };
    }
  }
  return best;
}

async function syncFromGitHubIssue({ token, repo, now }) {
  const current = loadCommander();
  if (!token || !repo) return { commander: current, synced: false, reason: 'no_github' };
  const { comments } = await fetchIssueComments({ token, repo, title: ISSUE_TITLE });
  const latest = latestCommandFromComments(comments);
  if (!latest) return { commander: current, synced: false, reason: 'no_command_comment' };
  const currentTs = Date.parse(current.updated_at || 0);
  if (latest.ts < currentTs && current.source === 'risk-guard') {
    return { commander: current, synced: false, reason: 'risk-guard_newer' };
  }
  if (latest.command === current.command && current.source === 'grok-bot-issue') {
    return { commander: current, synced: false, reason: 'unchanged' };
  }
  const next = applyCommand(current, {
    command: latest.command,
    source: 'grok-bot-issue',
    reason: latest.reason,
    now: now || new Date(latest.updated_at)
  });
  saveCommander(next);
  return { commander: next, synced: true };
}

function haltFromRisk(current, reason, now) {
  const next = applyCommand(current, {
    command: 'HALT',
    source: 'risk-guard',
    reason,
    now
  });
  saveCommander(next);
  return next;
}

module.exports = {
  COMMANDER_PATH,
  ISSUE_TITLE,
  defaultCommander,
  loadCommander,
  saveCommander,
  parseCommandText,
  applyCommand,
  latestCommandFromComments,
  syncFromGitHubIssue,
  haltFromRisk
};
