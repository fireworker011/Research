'use strict';

const fs = require('fs');
const path = require('path');

const HUMAN_PLACEHOLDER = '（人間が書く）';

const RULES_FILE = path.join('rules', 'CW_RULES.md');
const CLIENT_SKILL = path.join('skills', 'cw-ai-client-work', 'SKILL.md');
const HUMAN_SKILL = path.join('skills', 'skill-1789872612155', 'SKILL.md');

const DROP_FLAGS = Object.freeze([
  ['顔出し', 'on_camera'],
  ['声出し', 'voice_required'],
  ['口コミ投稿', 'review_posting'],
  ['アカウント作成', 'account_work'],
  ['AI禁止', 'ai_forbidden'],
  ['面談必須', 'interview_required'],
  ['LINE誘導', 'line_redirect'],
  ['物販や体験が必要なもの', 'goods_or_experience'],
  ['アダルト', 'adult'],
  ['募集終了', 'closed']
]);

function defaultRoot() {
  if (process.env.CW_RULES_DIR) return path.resolve(process.env.CW_RULES_DIR);
  if (process.env.CW_WORK_DIR) return path.resolve(process.env.CW_WORK_DIR);
  return null;
}

function readRequired(root, rel) {
  const file = path.join(root, rel);
  if (!fs.existsSync(file)) return null;
  const text = fs.readFileSync(file, 'utf8');
  if (!String(text).trim()) return null;
  return text;
}

function dropLabels(text) {
  const line = String(text || '')
    .split(/\n/)
    .find((l) => l.includes('外すもの'));
  if (!line) return [];
  const after = line.split('外すもの').slice(1).join('外すもの');
  return after
    .split(/[、,]/)
    .map((s) => s.replace(/^[:：\s]+/, '').replace(/[。.\s]+$/g, '').trim())
    .filter(Boolean);
}

function bannedPhrases(skill) {
  const section = (String(skill || '').split('## やらない')[1] || '').split(/\n## /)[0];
  const out = [];
  for (const match of section.matchAll(/「([^」]+)」/g)) {
    const phrase = match[1].replace(/〜/g, '').trim();
    if (phrase && !out.includes(phrase)) out.push(phrase);
  }
  return out;
}

function loadSharedRules(root = defaultRoot()) {
  const missing = [];
  if (!root) {
    return { ok: false, missing: ['rules_root'], root: null };
  }
  const rulesText = readRequired(root, RULES_FILE);
  const clientSkill = readRequired(root, CLIENT_SKILL);
  const humanSkill = readRequired(root, HUMAN_SKILL);
  if (!rulesText) missing.push(RULES_FILE);
  if (!clientSkill) missing.push(CLIENT_SKILL);
  if (!humanSkill) missing.push(HUMAN_SKILL);
  if (missing.length) return { ok: false, missing, root };

  const nameMatch = rulesText.match(/名乗りは「([^」]+)」/);
  const displayName = nameMatch ? nameMatch[1].trim() : '';
  if (!displayName) missing.push('display_name');
  if (!rulesText.includes(HUMAN_PLACEHOLDER)) missing.push('placeholder');
  const labels = dropLabels(rulesText);
  const unmapped = labels.filter((label) => !DROP_FLAGS.some(([name]) => name === label));
  for (const [name] of DROP_FLAGS) {
    if (!labels.includes(name)) missing.push(`drop:${name}`);
  }
  for (const label of unmapped) missing.push(`unmapped_drop:${label}`);
  const waiting = rulesText.match(/下書きが\s*(\d+)\s*件/);
  const maxWaitingDrafts = waiting ? Number(waiting[1]) : 0;
  if (!maxWaitingDrafts) missing.push('max_waiting_drafts');
  if (!/提案文/.test(clientSkill) || !/6要素/.test(clientSkill)) missing.push('client_skill_markers');
  const banned = bannedPhrases(humanSkill);
  if (!banned.includes('一方で') || !banned.includes('と言えるだろう') || !banned.includes('押さえておきたい')) {
    missing.push('human_skill_banned');
  }
  if (missing.length) return { ok: false, missing, root };

  return {
    ok: true,
    missing: [],
    root,
    displayName,
    placeholder: HUMAN_PLACEHOLDER,
    dropLabels: labels,
    maxWaitingDrafts,
    banned,
    files: [RULES_FILE, CLIENT_SKILL, HUMAN_SKILL]
  };
}

function publicTextMissing(text) {
  const raw = String(text || '').trim();
  if (!raw || raw === HUMAN_PLACEHOLDER) return true;
  const marked = raw.match(/【公開文】\s*([\s\S]*?)(?:\n## |\n# |$)/);
  if (marked && marked[1].trim() === HUMAN_PLACEHOLDER) return true;
  return false;
}

module.exports = {
  HUMAN_PLACEHOLDER,
  DROP_FLAGS,
  RULES_FILE,
  CLIENT_SKILL,
  HUMAN_SKILL,
  defaultRoot,
  dropLabels,
  bannedPhrases,
  loadSharedRules,
  publicTextMissing
};
