'use strict';

const { categoryById } = require('./util');

function deliveryMessage(job, { capability, files, revision = 0 }) {
  const category = categoryById(capability, job.category);
  const lines = [];
  lines.push('お世話になっております。');
  lines.push(`${revision > 0 ? `修正依頼を反映した反映版（${revision}回目）` : `ご依頼の${category ? category.label : '成果物'}`}を納品します。`);
  lines.push('');
  lines.push('添付ファイル:');
  for (const f of files) lines.push(`・${f}`);
  lines.push('');
  lines.push('確認のお願い:');
  lines.push('・募集文とご指示の反映漏れがあればお知らせください（修正1回まで無償）');
  lines.push('・事実・数字・固有名詞はご提供の素材に基づいています。素材に無い箇所は【要確認】としています（残っていれば教えてください）');
  lines.push('');
  lines.push('問題なければ検収をお願いいたします。ありがとうございました。');
  return lines.join('\n');
}

function humanChecklist(job, { qa, humanToolRequired }) {
  const items = [
    '仮払いが完了している（未完了なら納品しない）',
    '成果物を開いて最終確認した（機械のQAは補助）',
    '募集文・契約メッセージの指示と一致している',
    'ファイルを添付して納品ボタン（クラウドワークス内）',
    '納品したら Issue に `CW: DELIVERED <id>`'
  ];
  if (qa && qa.warnings && qa.warnings.length) items.unshift(`QA の注意: ${qa.warnings.join(' / ')}`);
  if (humanToolRequired) items.unshift('このカテゴリは機械が編集計画までしか作れない。動画そのものは人間のツールで仕上げる');
  return items;
}

function buildDeliveryDoc(job, { capability, files, qa, revision = 0, humanToolRequired = false }) {
  const lines = [];
  lines.push(`# DELIVERY — ${job.id} ${job.title || ''}`.trim());
  lines.push('');
  lines.push('## 納品メッセージ（そのまま貼れる）');
  lines.push('```');
  lines.push(deliveryMessage(job, { capability, files, revision }));
  lines.push('```');
  lines.push('');
  lines.push('## 人間のチェック（納品ボタンの前）');
  for (const item of humanChecklist(job, { qa, humanToolRequired })) lines.push(`- [ ] ${item}`);
  lines.push('');
  lines.push('## QA（機械）');
  lines.push(`- 結果: ${qa && qa.ok ? 'pass' : 'fail'}`);
  lines.push(`- 文字数（空白除く）: ${qa ? qa.chars : '未確認'}`);
  if (qa && qa.issues && qa.issues.length) lines.push(`- 問題: ${qa.issues.join(' / ')}`);
  if (qa && qa.warnings && qa.warnings.length) lines.push(`- 注意: ${qa.warnings.join(' / ')}`);
  return lines.join('\n');
}

module.exports = { deliveryMessage, humanChecklist, buildDeliveryDoc };
