'use strict';

const fs = require('fs');
const path = require('path');
const { OUTPUT_DIR, loadCapability } = require('./util');
const { loadCommander } = require('./commander');
const { loadQueue, counts, catalogYenBlocked } = require('./queue');
const { deskLines } = require('./desk');

function renderMarkdown({ commander, queue, capability, now }) {
  const n = counts(queue);
  const day = (now || new Date()).toISOString().slice(0, 10);
  const lines = [];
  lines.push(`# CW 司令塔 — ${day}`);
  lines.push('');
  lines.push(`生成: ${(now || new Date()).toISOString()}`);
  lines.push('');
  lines.push('> 公開報酬・応募画面の円は `approved_yen` ではない。発明しない。remain / n10 は駐車。');
  lines.push('');
  lines.push('## 司令塔ステータス');
  lines.push('');
  lines.push(`- command: \`${commander.command}\``);
  lines.push(`- source: ${commander.source || 'init'}`);
  lines.push(`- reason: ${commander.reason || ''}`);
  lines.push(`- updated_at: ${commander.updated_at}`);
  lines.push('');
  lines.push('## キュー（応募は自動送信していない）');
  lines.push('');
  lines.push(`- 合計: ${n.total}`);
  lines.push(`- 資格OK: ${n.qualified}`);
  lines.push(`- 下書き（人間送信待ち）: ${n.waiting_human}`);
  lines.push(`- 送信済: ${n.sent}`);
  lines.push(`- 同時契約: ${n.contracted}`);
  if (n.total === 0) {
    lines.push('- キュー空。応募を連発するな。remain の仕事 ID を足すな。');
  }
  const blocked = (queue.jobs || []).filter(catalogYenBlocked);
  if (blocked.length) {
    lines.push(`- カタログ円を無視した件: ${blocked.length}（CSV に足していない）`);
  }
  lines.push('');
  lines.push('## デスク行（Grok は写すだけ）');
  lines.push('');
  lines.push('```');
  lines.push(...deskLines({ commander, queue, capability, now }));
  lines.push('```');
  lines.push('');
  lines.push('## やらない');
  lines.push('');
  lines.push('- remain / n10 を開けるな');
  lines.push('- ログイン自動化・非公式 API での応募送信');
  lines.push('- 実績捏造、カタログ円の conversions 加算');
  lines.push('- ジャンルbot の増設');
  lines.push('');
  return `${lines.join('\n')}\n`;
}

function writeToday(now) {
  const commander = loadCommander();
  const queue = loadQueue();
  const capability = loadCapability();
  const md = renderMarkdown({ commander, queue, capability, now });
  const out = path.join(OUTPUT_DIR, 'reports', 'TODAY.md');
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, md);
  return { out, md };
}

function main() {
  const { out } = writeToday();
  process.stdout.write(`${out}\n`);
}

module.exports = { renderMarkdown, writeToday };

if (require.main === module) {
  try {
    main();
  } catch (err) {
    console.error(err.message || err);
    process.exit(1);
  }
}
