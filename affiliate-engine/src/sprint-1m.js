#!/usr/bin/env node
'use strict';

/**
 * 9/30 まで ¥1,000,000（確定円）のスコアボード。
 * 24時間スプリントの毎時ティックでも使う。数字は invent しない。
 *
 *   node src/sprint-1m.js
 *   node src/sprint-1m.js --self-test
 *   SPRINT_TODAY=2026-08-27 node src/sprint-1m.js
 *
 * 円の正本: data/conversions.csv の approved_yen。カタログ単価は足さない。
 * リンクの実 URL はログに出さない。
 */

const fs = require('fs');
const path = require('path');
const {
  ROOT,
  OUTPUT_DIR,
  parseCSV,
  readJSON,
  writeJSON,
  loadLinks,
  countFilledLinks,
  filledLinkKeys,
  todayJST
} = require('./util');

const TARGET_YEN = 1_000_000;
const DEADLINE = '2026-09-30';
const SPRINT_HOURS = 24;
const CONVERSIONS_PATH = process.env.CONVERSIONS_CSV || path.join(ROOT, 'data', 'conversions.csv');
const STATE_PATH = path.join(OUTPUT_DIR, 'sprint', 'state.json');
const TODAY_PATH = path.join(OUTPUT_DIR, 'sprint', 'TODAY.md');
const HUMAN_PATH = path.join(OUTPUT_DIR, 'sprint', 'HUMAN.md');

function daysInclusive(start, end) {
  const [sy, sm, sd] = start.split('-').map(Number);
  const [ey, em, ed] = end.split('-').map(Number);
  const diff = Math.round((Date.UTC(ey, em - 1, ed) - Date.UTC(sy, sm - 1, sd)) / 86400000);
  if (diff < 0) return 0;
  return diff + 1;
}

function toInt(value) {
  const n = Number.parseInt(String(value ?? '').trim(), 10);
  return Number.isFinite(n) ? n : 0;
}

function isLiveConversionRow(row) {
  if (!row || !/^\d{4}-\d{2}-\d{2}$/.test(row.date || '')) return false;
  return true;
}

function lastLiveConversionDate(csvText) {
  const rows = parseCSV(csvText).filter(isLiveConversionRow);
  let last = null;
  for (const row of rows) {
    if (!last || row.date > last) last = row.date;
  }
  return last;
}

function sumConversions(csvText) {
  const rows = parseCSV(csvText).filter(isLiveConversionRow);
  let clicks = 0;
  let cv = 0;
  let approvedYen = 0;
  for (const row of rows) {
    clicks += toInt(row.clicks);
    cv += toInt(row.cv);
    approvedYen += toInt(row.approved_yen);
  }
  return { rows: rows.length, clicks, cv, approvedYen, lastDate: lastLiveConversionDate(csvText) };
}

function hoursElapsed(startedAtIso, nowMs = Date.now()) {
  if (!startedAtIso) return 0;
  const started = Date.parse(startedAtIso);
  if (!Number.isFinite(started)) return 0;
  return Math.max(0, Math.floor((nowMs - started) / 3600000));
}

function buildSnapshot(opts = {}) {
  const today = opts.today || process.env.SPRINT_TODAY || todayJST();
  const csvText = opts.csvText != null ? opts.csvText : fs.readFileSync(CONVERSIONS_PATH, 'utf-8');
  const conversions = sumConversions(csvText);
  const remainingDays = daysInclusive(today, DEADLINE);
  const remainingYen = Math.max(0, TARGET_YEN - conversions.approvedYen);
  const paceYenPerDay = remainingDays > 0 ? Math.ceil(remainingYen / remainingDays) : remainingYen;
  const links = opts.links || loadLinks();
  const filled = countFilledLinks(links);
  const filledKeys = filledLinkKeys(links);
  const prev = opts.prevState || readJSON(STATE_PATH, {}) || {};
  const startedAt = opts.startedAt || prev.sprint_started_at || new Date().toISOString();
  const elapsed = hoursElapsed(startedAt, opts.nowMs);
  const hoursLeft = Math.max(0, SPRINT_HOURS - elapsed);

  const blockers = [];
  blockers.push({
    id: 'hq_do_not_paste',
    owner: '指令塔→人間',
    action: 'auひかりは SNS 掲載項目なし。貼るな。Secret に URL を入れるな'
  });
  blockers.push({
    id: 'run_cw_note_banner',
    owner: '指令塔→人間',
    action: 'KEEP_CUT の run: CWは既応募6へ再応募せず新規4でN=10 / note下書き / 秋バナー製作。出品と公開は指令塔がまだ出していない'
  });
  const lastDate = conversions.lastDate;
  const csvStale = !lastDate || lastDate < today;
  blockers.push({
    id: csvStale ? 'csv_stale' : 'a8_csv',
    owner: '指令塔→人間',
    action: csvStale
      ? `conversions 最終実測行は ${lastDate || '無し'}。今日 ${today} の行はファイルに無い。管理画面を見てから1行。開いていないなら足すな。invent するな`
      : 'A8 管理画面で見た clicks / cv / approved_yen だけ conversions.csv に1行。カタログ円は書かない'
  });
  blockers.push({
    id: 'video_csv',
    owner: '指令塔→人間',
    action: 'ペット実験の当日数字を video_cash_log.csv に1行。無い日は空のまま'
  });
  if (filled > 0) {
    blockers.unshift({
      id: 'links_present',
      owner: '指令塔',
      action: `値が入っている link_key が ${filled}。貼る可否は HQ_APPLY を見て指令塔が決める。Cursor は再開しない`
    });
  }

  return {
    commander: 'Grok Bot 指令塔',
    staff: 'Cursor',
    today,
    deadline: DEADLINE,
    target_yen: TARGET_YEN,
    measured_yen: conversions.approvedYen,
    remaining_yen: remainingYen,
    remaining_days: remainingDays,
    pace_yen_per_day: paceYenPerDay,
    conversion_rows: conversions.rows,
    conversion_last_date: conversions.lastDate,
    csv_stale: csvStale,
    clicks: conversions.clicks,
    cv: conversions.cv,
    filled_link_keys: filled,
    filled_link_key_names: filledKeys,
    threads_cron: 'stopped',
    sprint_started_at: startedAt,
    sprint_hours: SPRINT_HOURS,
    hours_elapsed: elapsed,
    hours_left: hoursLeft,
    blockers,
    notes: [
      '確定円だけが売上。再生・カタログ単価・EPC は売上ではない',
      '司令塔は Grok Bot。Cursor は参謀。指示を出すのも動くのも BOT',
      'Threads 自動投稿の cron は指令塔が再開を出すまで戻さない',
      'いいね / フォロー / DM / 体験談の捏造 / #PR なしリンクはやらない'
    ]
  };
}

function renderTodayMd(s) {
  const blockerLines = s.blockers.map((b) => `- **${b.owner}**: ${b.action}`).join('\n');
  const keyNames = s.filled_link_key_names.length ? s.filled_link_key_names.join(', ') : 'なし（値は出さない）';
  return `# 9/30 ¥100万 — 今日のスコアボード

日付: ${s.today}（JST）
司令塔: **${s.commander}**
参謀: **${s.staff}**（企画・運用・指示書・仕組み。指示は出さない）
参謀ループ: 経過 ${s.hours_elapsed} / ${s.sprint_hours} 時間（残り ${s.hours_left}）

## 円

| 項目 | 値 |
|---|---|
| 期限 | ${s.deadline} |
| 目標 | ¥${s.target_yen.toLocaleString()}（確定円） |
| 実測円 | ¥${s.measured_yen.toLocaleString()} |
| 不足円 | ¥${s.remaining_yen.toLocaleString()} |
| 残日数（今日含む） | ${s.remaining_days} |
| 必要ペース | ¥${s.pace_yen_per_day.toLocaleString()} / 日 |
| conversions 行 | ${s.conversion_rows} |
| 最終実測行 | ${s.conversion_last_date || '無し'} |
| 今日の行 | ${s.csv_stale ? 'ファイルに無い' : 'ある'} |
| clicks（ファイルにある分） | ${s.clicks} |
| cv（ファイルにある分） | ${s.cv} |

カタログ単価は足していない。

## 導線

- 値が入っている link_key 数: ${s.filled_link_keys}
- キー名: ${keyNames}
- Threads cron: **${s.threads_cron}**（再開は指令塔が出す。参謀は出さない）

## 司令部が人間へ出す手（参謀は代替しない）

${blockerLines}

## やらないこと

- 数字を発明する
- アフィURLを Git / チャット / ログに書く
- いいね・フォロー・自動DM
- YouTube 投稿の自動化
- 体験談の捏造、#PR なしのリンク
`;
}

function renderHumanMd(s) {
  return `# 司令部が人間へ出す1手（参謀下書き）

指令塔がこの文を採否する。Cursor は送らない。今夜の dump は \`G_hq_cw_n10.txt\` が正。

目標 ${s.deadline} 確定 ¥${s.target_yen.toLocaleString()}。実測円 ¥${s.measured_yen.toLocaleString()}。

1. CW fireworker12 で、既応募6件には再応募せず、CW_LIVE.md の新規4件へ CW_APPLY.md の文で応募して N=10 にせよ。無い実績は書くな。プロフィールは直すな。
2. auひかりは貼るな。note は公開するな。バナーは出品するな。

CSV の1行は dump \`G_hq_a8_csv.txt\` の仕事。今夜の dump と結合するな。

次の指示は指令塔が出す。
`;
}

function writeOutputs(snapshot) {
  const prev = readJSON(STATE_PATH, {}) || {};
  const ticks = Array.isArray(prev.ticks) ? prev.ticks.slice() : [];
  ticks.push({
    at: new Date().toISOString(),
    today: snapshot.today,
    measured_yen: snapshot.measured_yen,
    filled_link_keys: snapshot.filled_link_keys,
    hours_elapsed: snapshot.hours_elapsed
  });
  const keep = {};
  for (const key of ['completed_hours', 'next_hour_task', 'last_dry_run', 'video_judge', 'funnel', 'note_sku1', 'cw_live', 'banner_10', 'measure']) {
    if (prev[key] !== undefined) keep[key] = prev[key];
  }
  const state = {
    ...keep,
    ...snapshot,
    ticks: ticks.slice(-48)
  };
  writeJSON(STATE_PATH, state);
  fs.mkdirSync(path.dirname(TODAY_PATH), { recursive: true });
  fs.writeFileSync(TODAY_PATH, renderTodayMd(snapshot), 'utf-8');
  fs.writeFileSync(HUMAN_PATH, renderHumanMd(snapshot), 'utf-8');
  return state;
}

function selfTest() {
  const remaining = daysInclusive('2026-08-27', '2026-09-30');
  if (remaining !== 35) throw new Error(`remaining days want 35, got ${remaining}`);
  if (daysInclusive('2026-09-30', '2026-09-30') !== 1) throw new Error('deadline day should be 1');
  if (daysInclusive('2026-10-01', '2026-09-30') !== 0) throw new Error('past deadline should be 0');

  const csv = [
    'date,source,program,clicks,cv,approved_yen,note',
    '#,,,,,,comment',
    '2026-08-27,A8,all,33,0,0,period monthly'
  ].join('\n');
  const sums = sumConversions(csv);
  if (sums.rows !== 1) throw new Error(`rows want 1, got ${sums.rows}`);
  if (sums.clicks !== 33) throw new Error(`clicks want 33, got ${sums.clicks}`);
  if (sums.approvedYen !== 0) throw new Error(`yen want 0, got ${sums.approvedYen}`);

  const prev = process.env.AFFILIATE_LINKS_JSON;
  process.env.AFFILIATE_LINKS_JSON = JSON.stringify({ 申込_auひかり: 'https://example.invalid/secret' });
  const links = loadLinks();
  if (countFilledLinks(links) < 1) throw new Error('env overlay should fill at least 1 key');
  if (filledLinkKeys(links).includes('申込_auひかり') !== true) throw new Error('key name missing');
  const dumped = JSON.stringify(buildSnapshot({
    today: '2026-08-27',
    csvText: csv,
    links,
    startedAt: '2026-08-27T00:00:00.000Z',
    nowMs: Date.parse('2026-08-27T03:00:00.000Z')
  }));
  if (dumped.includes('example.invalid')) throw new Error('snapshot leaked a link URL');
  if (prev === undefined) delete process.env.AFFILIATE_LINKS_JSON;
  else process.env.AFFILIATE_LINKS_JSON = prev;

  const snap = buildSnapshot({
    today: '2026-08-27',
    csvText: csv,
    links: { 婚活: '', 申込_auひかり: '' },
    startedAt: '2026-08-27T00:00:00.000Z',
    nowMs: Date.parse('2026-08-27T03:00:00.000Z')
  });
  if (snap.remaining_days !== 35) throw new Error('snapshot remaining_days');
  if (snap.measured_yen !== 0) throw new Error('snapshot measured_yen');
  if (snap.pace_yen_per_day !== Math.ceil(1_000_000 / 35)) throw new Error('pace');
  if (snap.hours_elapsed !== 3) throw new Error('hours_elapsed');
  if (snap.hours_left !== 21) throw new Error('hours_left');
  if (snap.commander !== 'Grok Bot 指令塔') throw new Error('commander');
  if (snap.staff !== 'Cursor') throw new Error('staff');
  if (lastLiveConversionDate(csv) !== '2026-08-27') throw new Error('lastLiveConversionDate');
  if (snap.csv_stale !== false) throw new Error('same-day csv should not be stale');
  const staleSnap = buildSnapshot({
    today: '2026-08-28',
    csvText: csv,
    links: { 婚活: '' },
    startedAt: '2026-08-27T00:00:00.000Z',
    nowMs: Date.parse('2026-08-27T03:00:00.000Z')
  });
  if (staleSnap.csv_stale !== true) throw new Error('next-day csv should be stale');
  if (!staleSnap.blockers.some((b) => b.id === 'csv_stale')) throw new Error('csv_stale blocker missing');
  console.log('self-test ok');
}

function main() {
  if (process.argv.includes('--self-test')) {
    selfTest();
    return;
  }
  const snapshot = buildSnapshot();
  writeOutputs(snapshot);
  console.log(`🎯 ${snapshot.deadline} まで ¥${snapshot.target_yen.toLocaleString()}`);
  console.log(`   実測円 ¥${snapshot.measured_yen.toLocaleString()} / 不足 ¥${snapshot.remaining_yen.toLocaleString()}`);
  console.log(`   残日数 ${snapshot.remaining_days}（今日含む）/ 必要ペース ¥${snapshot.pace_yen_per_day.toLocaleString()}/日`);
  console.log(`   リンク値が入っているキー ${snapshot.filled_link_keys} 個（URLは出さない）`);
  console.log(`   24hスプリント 残り ${snapshot.hours_left} 時間`);
  console.log(`   書き出し: ${TODAY_PATH}`);
}

module.exports = {
  TARGET_YEN,
  DEADLINE,
  daysInclusive,
  sumConversions,
  lastLiveConversionDate,
  buildSnapshot
};

if (require.main === module) {
  try {
    main();
  } catch (err) {
    console.error(`sprint-1m failed: ${err.message}`);
    process.exit(1);
  }
}
