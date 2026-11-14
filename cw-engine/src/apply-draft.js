'use strict';

const { categoryById } = require('./util');
const { HUMAN_PLACEHOLDER, checkDraft } = require('./compliance');
const llm = require('./llm');

const AI_LINE = '作業には生成AIを補助的に使い、最終確認と修正は私自身が行います。AI利用に条件があればお知らせください。';

function deliveriesLine(facts) {
  const n = Number(facts?.public_profile_facts?.deliveries_completed || 0);
  if (n > 0) return `クラウドワークスでの完成納品は ${n} 件です。`;
  return 'クラウドワークスでの完成納品はまだありません。無い実績は書きません。';
}

function answerAsk(ask, { facts, category, job }) {
  const pub = facts?.public_profile_facts || {};
  const a = String(ask);
  if (/(氏名|お名前|名前|年齢|年代|ご年代|家族|住所|電話|生年月日|性別)/.test(a)) return HUMAN_PLACEHOLDER;
  if (/(稼働|作業時間|対応可能な時間|作業できる|週に)/.test(a)) {
    return pub.hours_per_day ? `1日 ${pub.hours_per_day} 時間程度（${pub.reply_hours || '連絡時間は' + HUMAN_PLACEHOLDER}）` : HUMAN_PLACEHOLDER;
  }
  if (/(連絡|返信|レスポンス)/.test(a)) return pub.reply_hours || HUMAN_PLACEHOLDER;
  if (/(ソフト|ツール|環境|使用)/.test(a)) return pub.tools?.length ? pub.tools.join('、') : HUMAN_PLACEHOLDER;
  if (/(職業|ご職業|お仕事|現在の状況|ご状況|経歴)/.test(a)) return pub.occupation || HUMAN_PLACEHOLDER;
  if (/(ポートフォリオ|実績|作品|制作物|サンプル)/.test(a)) {
    if (pub.portfolio_url) return pub.portfolio_url;
    return Number(pub.deliveries_completed || 0) > 0 ? `クラウドワークスでの完成納品 ${pub.deliveries_completed} 件（詳細はお伝えできる範囲で）` : '無し（完成納品はまだありません。借り物は載せません）';
  }
  if (/(経験|スキル|得意)/.test(a)) {
    return Number(pub.deliveries_completed || 0) > 0
      ? `${category?.label || '同種'}の完成納品 ${pub.deliveries_completed} 件。無い経験は書きません`
      : `${category?.label || '同種'}の実務納品はまだありません。生成AIを補助に使い、最終確認は自分で行います`;
  }
  if (/(志望|理由|動機|意気込み|自己紹介)/.test(a)) {
    return `公開の募集文を読み、${category?.label || '記載の業務'}として、納期と連絡を守って納品するために応募します。`;
  }
  if (/(AI|ＡＩ)/.test(a)) return facts?.ai_policy?.use_ai === false ? '使用しません' : '補助的に使用します（最終確認は自分で行います）。条件があれば従います';
  return HUMAN_PLACEHOLDER;
}

function buildApplyDraft(job, { facts, capability, sample = null }) {
  const category = categoryById(capability, job.category);
  const handle = facts?.handle || 'fireworker12';
  const pub = facts?.public_profile_facts || {};
  const lines = [];
  for (const ask of job.asks || []) {
    lines.push(`${ask}: ${answerAsk(ask, { facts, category, job })}`);
  }
  if (lines.length) lines.push('');
  lines.push(`はじめまして。クラウドワークスの ${handle} です。`);
  lines.push(`公開の募集文を読み、${category ? category.label : '記載の業務'}として応募します。`);
  const spec = job.char_spec ? `${job.char_spec[0]}〜${job.char_spec[1]}文字` : null;
  lines.push(`納品物: 募集文のとおり${spec ? `（1${category ? category.unit : '本'}あたり ${spec}）` : ''}。形式はご指定に合わせます。`);
  lines.push(`進め方: 着手 → 初稿 → 修正1回 → 納品（初稿の目安 ${category ? category.turnaround_days : 2} 日）。${pub.reply_hours ? `連絡は ${pub.reply_hours} に返します。` : ''}`.trim());
  if (facts?.ai_policy?.disclose !== false) lines.push(AI_LINE);
  lines.push(deliveriesLine(facts));
  if (sample) {
    lines.push('');
    lines.push('募集文のテーマに沿った短いサンプルです（この応募のために作成）:');
    lines.push(sample.trim());
    lines.push('');
  }
  lines.push('納期と連絡は守ります。よろしくお願いいたします。');
  return lines.join('\n');
}

async function makeSample(job, category) {
  if (!llm.llmAvailable() || !category || category.ai_complete === false) return null;
  const prompt = [
    `募集文（公開）:\n${job.text_excerpt || job.title}`,
    `この募集の${category.label}として、テーマに沿った 100〜150 字のサンプル文を1つだけ書いてください。`,
    '固有名詞・数字・体験談は募集文にあるものだけ。無ければ一般的な表現にする。前置き・見出し・URL は書かない。'
  ].join('\n\n');
  try {
    const out = llm.stripFences(await llm.ask(prompt, { maxTokens: 400 }));
    return out.length >= 40 && out.length <= 260 ? out : null;
  } catch (_) {
    return null;
  }
}

async function draftApplication(job, { facts, capability }) {
  const category = categoryById(capability, job.category);
  const sample = await makeSample(job, category);
  let text = buildApplyDraft(job, { facts, capability, sample });
  let check = checkDraft(text, { facts, kind: 'apply', maxChars: 1500 });
  if (!check.ok) {
    text = buildApplyDraft(job, { facts, capability, sample: null });
    check = checkDraft(text, { facts, kind: 'apply', maxChars: 1500 });
  }
  return { text, check, sample_used: Boolean(sample) && check.ok };
}

module.exports = { AI_LINE, answerAsk, buildApplyDraft, draftApplication, deliveriesLine };
