'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const WORK_DIR = process.env.CW_WORK_DIR ? path.resolve(process.env.CW_WORK_DIR) : path.join(ROOT, 'output');

function workPath(...parts) {
  return path.join(WORK_DIR, ...parts);
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

function readJSON(filePath, fallback) {
  try {
    if (!fs.existsSync(filePath)) return fallback;
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (_) {
    return fallback;
  }
}

function writeJSON(filePath, data) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`);
  return data;
}

function readText(filePath, fallback = '') {
  try {
    if (!fs.existsSync(filePath)) return fallback;
    return fs.readFileSync(filePath, 'utf8');
  } catch (_) {
    return fallback;
  }
}

function writeText(filePath, text) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, text.endsWith('\n') ? text : `${text}\n`);
  return filePath;
}

function loadCapability() {
  return readJSON(path.join(ROOT, 'config', 'capability.json'), null);
}

function categoryById(capability, id) {
  return (capability?.categories || []).find((c) => c.id === id) || null;
}

const FACTS_FORBIDDEN_KEYS = ['name', 'full_name', 'age', 'address', 'phone', 'family', '氏名', '年齢', '住所', '電話', '家族構成'];

function sanitizeFacts(raw) {
  const facts = raw && typeof raw === 'object' ? JSON.parse(JSON.stringify(raw)) : {};
  const pub = facts.public_profile_facts && typeof facts.public_profile_facts === 'object' ? facts.public_profile_facts : {};
  for (const k of FACTS_FORBIDDEN_KEYS) {
    delete pub[k];
    delete facts[k];
  }
  return {
    handle: typeof facts.handle === 'string' && facts.handle ? facts.handle : 'fireworker12',
    public_profile_facts: {
      occupation: typeof pub.occupation === 'string' && pub.occupation ? pub.occupation : null,
      hours_per_day: Number.isFinite(Number(pub.hours_per_day)) && pub.hours_per_day !== null ? Number(pub.hours_per_day) : null,
      reply_hours: typeof pub.reply_hours === 'string' && pub.reply_hours ? pub.reply_hours : null,
      tools: Array.isArray(pub.tools) ? pub.tools.filter((t) => typeof t === 'string' && t) : [],
      deliveries_completed: Number.isFinite(Number(pub.deliveries_completed)) ? Math.max(0, Math.floor(Number(pub.deliveries_completed))) : 0,
      portfolio_url: typeof pub.portfolio_url === 'string' && /^https?:\/\//.test(pub.portfolio_url) ? pub.portfolio_url : null
    },
    ai_policy: {
      use_ai: facts.ai_policy?.use_ai !== false,
      disclose: facts.ai_policy?.disclose !== false,
      final_check_by_human: facts.ai_policy?.final_check_by_human !== false
    }
  };
}

function loadFacts() {
  const env = process.env.CW_FACTS_JSON;
  if (env) {
    try {
      return sanitizeFacts(JSON.parse(env));
    } catch (_) {
      return sanitizeFacts({});
    }
  }
  const live = path.join(ROOT, 'config', 'facts.json');
  const example = path.join(ROOT, 'config', 'facts.example.json');
  return sanitizeFacts(readJSON(live, readJSON(example, {})));
}

function nowIso(now) {
  return (now instanceof Date ? now : new Date()).toISOString();
}

function dateJst(now) {
  const d = now instanceof Date ? now : new Date();
  return new Date(d.getTime() + 9 * 3600 * 1000).toISOString().slice(0, 10);
}

function addDays(dateStr, days) {
  const d = new Date(`${dateStr}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

function parseYenInt(raw) {
  const s = String(raw || '').trim();
  if (!/^\d+$/.test(s)) return null;
  return Number(s);
}

function stripHtml(html) {
  return String(html || '')
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/(p|div|li|tr|h\d|section|article)>/gi, '\n')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/[ \t]+/g, ' ')
    .replace(/\n\s*\n\s*\n+/g, '\n\n')
    .trim();
}

function countChars(text) {
  return String(text || '').replace(/\s/g, '').length;
}

module.exports = {
  ROOT,
  WORK_DIR,
  workPath,
  ensureDir,
  readJSON,
  writeJSON,
  readText,
  writeText,
  loadCapability,
  categoryById,
  loadFacts,
  sanitizeFacts,
  nowIso,
  dateJst,
  addDays,
  parseYenInt,
  stripHtml,
  countChars
};
