'use strict';

const { checkDraft } = require('./compliance');
const { AI_LINE, deliveriesLine } = require('./apply-draft');

function buildProfileDraft({ facts, capability, funnel = null }) {
  const pub = facts?.public_profile_facts || {};
  const cats = (capability?.categories || []).filter((c) => c.ai_complete !== false);
  const lines = [];
  lines.push('【できること】');
  for (const c of cats) lines.push(`・${c.label}（初稿の目安 ${c.turnaround_days} 日）`);
  lines.push('');
  lines.push('【進め方】');
  lines.push('・契約と仮払いの確定後に着手 → 初稿 → 修正1回 → 納品。やり取りはクラウドワークス内で行います。');
  lines.push(`・${AI_LINE}`);
  lines.push('・事実・数字・固有名詞はご提供の素材に基づいて書き、無いものは書きません。');
  lines.push('');
  lines.push('【実績】');
  lines.push(`・${deliveriesLine(facts)}`);
  if (pub.portfolio_url) lines.push(`・サンプル: ${pub.portfolio_url}`);
  lines.push('');
  lines.push('【稼働・連絡】');
  lines.push(`・稼働: ${pub.hours_per_day ? `1日 ${pub.hours_per_day} 時間程度` : '（人間が書く）'}`);
  lines.push(`・連絡: ${pub.reply_hours || '（人間が書く）'}`);
  if (pub.tools && pub.tools.length) lines.push(`・使用ツール: ${pub.tools.join('、')}`);
  lines.push('');
  lines.push('【お受けしていないもの】');
  lines.push('・顔出し・出演・撮影、口コミやレビューの投稿、外部サービスのアカウント作成、仮払い前の作業、クラウドワークス外でのやり取り');
  if (funnel && funnel.advice && funnel.advice.length) {
    lines.push('');
    lines.push('（改善メモ・貼らない）');
    for (const a of funnel.advice) lines.push(`・${a}`);
  }
  const text = lines.join('\n');
  const check = checkDraft(text.split('（改善メモ・貼らない）')[0], { facts, kind: 'profile', maxChars: 2000 });
  return { text, check };
}

module.exports = { buildProfileDraft };
