#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { fileFor } = require('./affi-step');

const GOAL_YEN = 1000000;
const DUMP = 'affiliate-engine/docs/grok-bots/dump';
const XM_POINTER = 'xm-trade-engine/docs/grok-bots/G_xm_trade.txt';
const SITTING_POINTER = `${DUMP}/G_hq_human_sitting.txt`;
const CSV_POINTER = fileFor('a8_csv');

function pickDump({ stop, overlayCount, approvedYen } = {}) {
  if (stop) {
    return { mode: 'xm', pointer: XM_POINTER, gate: 'xm', reply: '(none)' };
  }
  const yen = Number.isFinite(approvedYen) ? approvedYen : 0;
  const overlay = overlayCount || 0;
  if (yen >= GOAL_YEN) {
    return { mode: 'done', pointer: CSV_POINTER, gate: 'freeze', reply: '(none)' };
  }
  if (overlay >= 1) {
    return { mode: 'measure', pointer: CSV_POINTER, gate: 'measure', reply: '(none)' };
  }
  return { mode: 'sitting', pointer: SITTING_POINTER, gate: 'sitting', reply: '完了' };
}

function assertDump(rel) {
  const root = path.join(__dirname, '../..');
  const abs = path.join(root, rel);
  if (!fs.existsSync(abs)) throw new Error(`missing ${rel}`);
  const dump = fs.readFileSync(abs, 'utf8');
  if (/https?:\/\//i.test(dump)) throw new Error(`url ${rel}`);
  if (/G_hq_cw_remain|G_hq_cw_n10|banner_10/i.test(dump)) throw new Error(`parked ${rel}`);
  if (dump.includes('今すぐ次を開け')) throw new Error(`open next ${rel}`);
  return dump;
}

function selfTest() {
  const empty = pickDump({});
  if (empty.pointer !== SITTING_POINTER) throw new Error('default sitting');
  if (empty.gate !== 'sitting') throw new Error('default gate');
  if (empty.reply !== '完了') throw new Error('sitting reply');
  const stopped = pickDump({ stop: true, overlayCount: 3, approvedYen: 0 });
  if (stopped.pointer !== XM_POINTER) throw new Error('stop xm');
  const live = pickDump({ overlayCount: 1, approvedYen: 0 });
  if (live.pointer !== CSV_POINTER) throw new Error('overlay csv');
  if (live.gate !== 'measure') throw new Error('measure gate');
  const done = pickDump({ overlayCount: 2, approvedYen: GOAL_YEN });
  if (done.gate !== 'freeze') throw new Error('goal freeze');
  if (done.pointer !== CSV_POINTER) throw new Error('goal csv');
  if (pickDump({ overlayCount: 0, approvedYen: null }).pointer !== SITTING_POINTER) {
    throw new Error('null yen sitting');
  }
  if (pickDump({ stop: true }).mode !== 'xm') throw new Error('stop mode');
  const sitting = assertDump(SITTING_POINTER);
  if (!sitting.includes('s00000027548001')) throw new Error('nko id');
  if (!sitting.includes('s00000027572003')) throw new Error('eyes id');
  if (!sitting.includes('s00000018427001')) throw new Error('neo id');
  if (!sitting.includes('s00000011866027')) throw new Error('ticket id');
  if (!sitting.includes('教育_N高')) throw new Error('nko key');
  if (!sitting.includes('教育_アイズ')) throw new Error('eyes key');
  if (!sitting.includes('転職_neo')) throw new Error('neo key');
  if (!sitting.includes('はな｜小学生の習い事メモ')) throw new Error('edu name');
  if (!sitting.includes('けい｜しずかな転職準備')) throw new Error('tenshoku name');
  if (!/完了/.test(sitting)) throw new Error('done word');
  if (/^\s*AFFI:\s*GO\b/m.test(sitting)) throw new Error('sitting go');
  if (!sitting.includes('1語は返すな')) throw new Error('1word return');
  if (!sitting.includes('1語分岐の dump は開けるな')) throw new Error('no 1word dump');
  if (!sitting.includes('教育アカに neo')) throw new Error('no neo on edu');
  if (!sitting.includes('新媒体を今日開くな')) throw new Error('no new sns');
  if (!sitting.includes('auひかりは足すな')) throw new Error('no au');
  if (!sitting.includes('ペット')) throw new Error('no pet');
  const csv = assertDump(CSV_POINTER);
  if (!csv.includes('プロフィールに置いたリンクを外すな')) throw new Error('csv keep');
  const root = path.join(__dirname, '../docs/grok-bots');
  const roster = fs.readFileSync(path.join(root, 'HQ_ROSTER.md'), 'utf8');
  if (!roster.includes('#122')) throw new Error('roster 122');
  if (!roster.includes('マージするな')) throw new Error('roster no merge');
  const dumpReadme = fs.readFileSync(path.join(root, 'dump/README.md'), 'utf8');
  if (!dumpReadme.includes('G_hq_human_sitting.txt')) throw new Error('dump live sitting');
  if (/https?:\/\//i.test(dumpReadme)) throw new Error('dump readme url');
  process.stdout.write('hq-earn self-test ok\n');
}

module.exports = {
  GOAL_YEN,
  XM_POINTER,
  SITTING_POINTER,
  CSV_POINTER,
  pickDump
};

if (require.main === module) {
  if (process.argv.includes('--self-test')) selfTest();
}
