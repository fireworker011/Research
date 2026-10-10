'use strict';

const HUMAN_PLACEHOLDER = '（人間が書く）';
const NEEDS_CHECK = '【要確認】';

const META_AI_RE = /(私はAI|AIとして|AIです|As an AI|言語モデル|アシスタントとして)/;
const INVENTED_RE = /(実績(多数|豊富)|多くの(案件|実績|お客様)|経験\s*\d+\s*年|\d+\s*件以上の(実績|納品)|プロとして|専門家として|得意分野は|受賞)/;
const HYPE_RE = /(絶対に|必ず(成果|結果|伸び|売れ)|100%|保証します|誰でも稼げる)/;
const CLAIM_RE = /(治る|完治|必ず痩せ|痩せる|若返る|シワが消え|No\.?\s*1|日本一|最安)/;
const URL_RE = /https?:\/\/[^\s)）」』]+/g;
const CATALOG_YEN_RE = /(報酬|単価|金額)[^。\n]{0,10}[\d,]+\s*円/;
const BROKEN_RE = /(undefined|null|NaN|\[object Object\]|\$\{)/;
const CONTACT_RE = /(\b0\d{1,4}-\d{1,4}-\d{3,4}\b|[\w.+-]+@[\w-]+\.[\w.]+)/;

function urlsIn(text) {
  return String(text || '').match(URL_RE) || [];
}

function checkDraft(text, { facts, kind = 'apply', maxChars = 1500, allowUrls = [] } = {}) {
  const t = String(text || '');
  const issues = [];
  const deliveries = Number(facts?.public_profile_facts?.deliveries_completed || 0);
  const allowed = new Set([...(allowUrls || []), facts?.public_profile_facts?.portfolio_url].filter(Boolean));
  for (const u of urlsIn(t)) {
    if (!allowed.has(u)) issues.push(`url_not_allowed:${u.slice(0, 40)}`);
  }
  if (META_AI_RE.test(t)) issues.push('meta_ai_phrase');
  if (INVENTED_RE.test(t) && deliveries === 0) issues.push('invented_achievement');
  if (HYPE_RE.test(t)) issues.push('hype_phrase');
  if (BROKEN_RE.test(t)) issues.push('broken_template');
  if (kind === 'apply' || kind === 'profile') {
    if (facts?.ai_policy?.disclose !== false && !/AI/.test(t)) issues.push('ai_disclosure_missing');
    if (CATALOG_YEN_RE.test(t)) issues.push('catalog_yen_in_text');
    if (deliveries === 0 && /実績(が)?あり|納品実績(が)?あります/.test(t)) issues.push('invented_achievement');
  }
  if (kind === 'reply' && CONTACT_RE.test(t)) issues.push('contact_in_reply');
  const chars = t.replace(/\s/g, '').length;
  if (chars > maxChars) issues.push(`too_long:${chars}>${maxChars}`);
  if (chars < 40) issues.push('too_short');
  const needsHuman = (t.match(new RegExp(HUMAN_PLACEHOLDER.replace(/[()（）]/g, '\\$&'), 'g')) || []).length;
  return { ok: issues.length === 0, issues, needs_human: needsHuman, chars };
}

function checkDeliverable(text, { materials = '', charSpec = null, category = null } = {}) {
  const t = String(text || '');
  const issues = [];
  const warnings = [];
  const mat = String(materials || '');
  const chars = t.replace(/\s/g, '').length;
  if (META_AI_RE.test(t)) issues.push('meta_ai_phrase');
  if (BROKEN_RE.test(t)) issues.push('broken_template');
  if (/```/.test(t)) issues.push('code_fence_left');
  const unresolved = (t.match(/【要確認】/g) || []).length;
  if (unresolved) issues.push(`needs_check_left:${unresolved}`);
  for (const u of urlsIn(t)) {
    if (!mat.includes(u)) issues.push(`url_not_in_materials:${u.slice(0, 40)}`);
  }
  const claim = t.match(CLAIM_RE);
  if (claim && !mat.includes(claim[0])) issues.push(`claim_not_in_materials:${claim[0]}`);
  if (HYPE_RE.test(t)) issues.push('hype_phrase');
  const contact = t.match(CONTACT_RE);
  if (contact && !mat.includes(contact[0])) issues.push('contact_not_in_materials');
  if (Array.isArray(charSpec) && charSpec[1] > 0 && category !== 'data_structuring') {
    const [lo, hi] = charSpec;
    if (chars < Math.floor(lo * 0.9)) issues.push(`too_short:${chars}<${lo}`);
    if (chars > Math.ceil(hi * 1.15)) issues.push(`too_long:${chars}>${hi}`);
  }
  const paras = t.split(/\n\s*\n/).map((p) => p.trim()).filter((p) => p.length > 40);
  const dup = paras.length - new Set(paras).size;
  if (dup > 0) warnings.push(`duplicate_paragraphs:${dup}`);
  if (chars < 20) issues.push('empty_deliverable');
  return { ok: issues.length === 0, issues, warnings, chars };
}

module.exports = { HUMAN_PLACEHOLDER, NEEDS_CHECK, checkDraft, checkDeliverable, urlsIn };
