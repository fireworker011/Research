'use strict';

const { categoryById } = require('./util');
const { HUMAN_PLACEHOLDER, checkDraft } = require('./compliance');
const { loadSharedRules } = require('./shared-rules');

const AI_LINE = '生成AIは補助に使います。最後の確認と直しは自分でやります。条件があれば合わせます。';

function deliveriesLine(facts) {
  const n = Number(facts?.public_profile_facts?.deliveries_completed || 0);
  if (n > 0) return `クラウドワークスでの完成納品は ${n} 件です。`;
  return 'クラウドワークスでの完成納品はまだありません。無い実績は書きません。';
}

function aiLine(facts) {
  if (facts?.ai_policy?.disclose === false) return null;
  if (facts?.ai_policy?.use_ai === false) return '生成AIは使いません。';
  return AI_LINE;
}

function answerAsk(ask, { facts, placeholder = HUMAN_PLACEHOLDER }) {
  const pub = facts?.public_profile_facts || {};
  const a = String(ask);
  if (/(氏名|お名前|名前|年齢|年代|ご年代|家族|住所|電話|生年月日|性別)/.test(a)) return placeholder;
  if (/(稼働|作業時間|対応可能な時間|作業できる|週に)/.test(a)) {
    if (!pub.hours_per_day) return placeholder;
    return pub.reply_hours ? `1日 ${pub.hours_per_day} 時間程度（${pub.reply_hours}）` : `1日 ${pub.hours_per_day} 時間程度`;
  }
  if (/(連絡|返信|レスポンス)/.test(a)) return pub.reply_hours || placeholder;
  if (/(ソフト|ツール|環境|使用)/.test(a)) return pub.tools?.length ? pub.tools.join('、') : placeholder;
  if (/(職業|ご職業|お仕事|現在の状況|ご状況|経歴)/.test(a)) return pub.occupation || placeholder;
  if (/(ポートフォリオ|実績|作品|制作物|サンプル)/.test(a)) {
    const n = Number(pub.deliveries_completed || 0);
    if (n > 0) return `クラウドワークスでの完成納品は ${n} 件です。リンクは${placeholder}`;
    return `クラウドワークスでの完成納品はまだありません。無い実績は書きません。リンクは${placeholder}`;
  }
  if (/(経験|スキル|得意)/.test(a)) {
    const n = Number(pub.deliveries_completed || 0);
    if (n > 0) return `クラウドワークスでの完成納品は ${n} 件です。無い経験は書きません。`;
    return '同種の納品はまだありません。無い経験は書きません。';
  }
  if (/(自己紹介|志望|理由|動機|意気込み)/.test(a)) {
    return pub.occupation ? `${pub.occupation}です。` : placeholder;
  }
  if (/(AI|ＡＩ)/.test(a)) return facts?.ai_policy?.use_ai === false ? '使いません' : '補助に使います。最後の確認は自分でやります。条件があれば合わせます';
  return placeholder;
}

function buildApplyDraft(job, { facts, capability, rules }) {
  if (!rules?.ok || !rules.displayName) throw new Error('rules_required');
  const category = categoryById(capability, job.category);
  const pub = facts?.public_profile_facts || {};
  const placeholder = rules.placeholder || HUMAN_PLACEHOLDER;
  const asks = job.asks || [];
  const lines = [];
  lines.push(`${rules.displayName}です。`);
  const title = String(job.title || '募集').replace(/\s+/g, ' ').trim();
  const label = category ? category.label : '募集文の仕事';
  lines.push(`「${title}」を読みました。${label}として応募します。`);
  lines.push('募集の範囲で書きます。確認と直しは自分でします。');
  if (asks.length) {
    lines.push('');
    for (const ask of asks) lines.push(`${ask}: ${answerAsk(ask, { facts, placeholder })}`);
  }
  const askedHours = asks.some((ask) => /(稼働|作業時間|対応可能な時間|作業できる|週に)/.test(ask));
  const askedRecord = asks.some((ask) => /(ポートフォリオ|実績|作品|制作物|サンプル|経験)/.test(ask));
  lines.push('');
  if (!askedHours) {
    lines.push(pub.hours_per_day ? `稼働は1日 ${pub.hours_per_day} 時間程度です。` : `稼働: ${placeholder}`);
  }
  const spec = Array.isArray(job.char_spec) ? job.char_spec : null;
  const titleText = String(job.title || '');
  const titleHasSpec = spec && titleText.includes(String(spec[0])) && titleText.includes(String(spec[1]));
  if (spec && !titleHasSpec) lines.push(`文字数は募集の ${spec[0]}〜${spec[1]}文字 に合わせます。`);
  const disclosed = aiLine(facts);
  if (disclosed) lines.push(disclosed);
  if (!askedRecord) lines.push(deliveriesLine(facts));
  lines.push('納期と連絡は守ります。よろしくお願いします。');
  return lines.join('\n').replace(/\n{3,}/g, '\n\n');
}

function draftApplication(job, { facts, capability, rules = null } = {}) {
  const loaded = rules || loadSharedRules();
  if (!loaded.ok) {
    return {
      text: '',
      check: { ok: false, issues: ['rules_missing'], needs_human: 0, chars: 0 },
      sample_used: false,
      rules: loaded
    };
  }
  const text = buildApplyDraft(job, { facts, capability, rules: loaded });
  const check = checkDraft(text, { facts, kind: 'apply', maxChars: 1500 });
  for (const phrase of loaded.banned || []) {
    if (phrase && text.includes(phrase)) check.issues.push(`banned_phrase:${phrase}`);
  }
  if (/(LINE|ライン|アフィリエイト|友達追加|メールでご連絡|こちらから登録)/.test(text)) check.issues.push('external_redirect');
  if (/\bfireworker12\b/.test(text)) check.issues.push('legacy_handle');
  check.ok = check.issues.length === 0;
  return { text, check, sample_used: false, rules: loaded };
}

module.exports = { AI_LINE, answerAsk, buildApplyDraft, draftApplication, deliveriesLine, aiLine };
