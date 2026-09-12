'use strict';

const { workPath, writeText, loadCapability, categoryById } = require('./util');
const { loadCommander } = require('./commander');
const { loadQueue } = require('./queue');
const { ledgerTotal } = require('./ledger');
const { funnel } = require('./funnel');
const { deskLines } = require('./desk');

const STATUS_ORDER = ['ready', 'qa_failed', 'making', 'contracted', 'drafted', 'qualified', 'sent', 'delivered', 'paid', 'skipped', 'lost', 'rejected'];

function renderMarkdown({ commander, queue, capability, ledgerYen = 0, now }) {
  const f = funnel(queue, { ledgerYen, capability });
  const day = (now || new Date()).toISOString().slice(0, 10);
  const lines = [];
  lines.push(`# CW 司令塔 — ${day}`);
  lines.push('');
  lines.push(`生成: ${(now || new Date()).toISOString()}`);
  lines.push('');
  lines.push('> 公開の報酬表示は確定ではない。確定は `CW: PAID` で人間が画面を見た日だけ。人間は契約・外部案内誘導・納品。応募は Grok。エンジンは応募 POST しない。');
  lines.push('');
  lines.push('## 司令塔ステータス');
  lines.push('');
  lines.push(`- command: \`${commander.command}\``);
  lines.push(`- source: ${commander.source || 'init'}`);
  lines.push(`- updated_at: ${commander.updated_at}`);
  lines.push('');
  lines.push('## ファネル');
  lines.push('');
  lines.push(`- 取込 ${f.counts.total} / 資格OK ${f.counts.qualified} / 下書き ${f.counts.drafted} / 送信中 ${f.counts.sent}`);
  lines.push(`- 契約中 ${f.counts.contracted} / 納品済 ${f.counts.delivered} / 確定 ${f.counts.paid}`);
  lines.push(`- 累計: 送信 ${f.ever.sent} / 契約 ${f.ever.contracted} / 納品 ${f.ever.delivered} / 確定 ${f.ever.paid}`);
  lines.push(`- 確定報酬合計: ${ledgerYen} 円（台帳。カタログではない）`);
  lines.push(`- ゲート: ${f.gate}`);
  for (const a of f.advice) lines.push(`- 改善: ${a}`);
  lines.push('');
  lines.push('## 案件（公開情報だけ）');
  lines.push('');
  const jobs = [...(queue.jobs || [])].sort((a, b) => STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status) || (b.priority || 0) - (a.priority || 0));
  if (!jobs.length) lines.push('- キュー空。応募を連発するな。');
  for (const j of jobs) {
    const cat = categoryById(capability, j.category);
    const extra = j.status === 'rejected' ? ` 理由: ${(j.reasons || []).join(', ')}` : '';
    const warn = (j.warnings || []).length ? ` 注意: ${j.warnings.join(', ')}` : '';
    lines.push(`- ${j.id} [${j.status}] ${j.title || ''} — ${cat ? cat.label : j.category}${j.deadline ? ` 期限 ${j.deadline}` : ''}${extra}${warn}`);
  }
  lines.push('');
  lines.push('## デスク行（Bot は写すだけ）');
  lines.push('');
  lines.push('```');
  lines.push(...deskLines({ commander, queue, capability, funnel: f, ledgerYen, now }));
  lines.push('```');
  lines.push('');
  lines.push('## やらない');
  lines.push('');
  lines.push('- エンジンへのログイン自動化・非公式 API での応募送信。契約ボタン・納品ボタン・外部誘導');
  lines.push('- 実績捏造。カタログ円を確定に足す');
  lines.push('- 仮払い前の着手。直接取引。クライアント素材の外部流用');
  lines.push('- Grok clone やジャンルbot の増設。本線（100万）の dump に CW を差す');
  return `${lines.join('\n')}\n`;
}

function writeToday(now) {
  const commander = loadCommander();
  const queue = loadQueue();
  const capability = loadCapability();
  const ledgerYen = ledgerTotal();
  const md = renderMarkdown({ commander, queue, capability, ledgerYen, now });
  const out = workPath('reports', 'TODAY.md');
  writeText(out, md);
  return { out, md };
}

module.exports = { renderMarkdown, writeToday };

if (require.main === module) {
  try {
    process.stdout.write(`${writeToday().out}\n`);
  } catch (err) {
    console.error(err.message || err);
    process.exit(1);
  }
}
