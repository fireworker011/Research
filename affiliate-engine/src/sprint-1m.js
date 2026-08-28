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

function conversionShapeErrors(csvText, today) {
  const errors = [];
  const rows = parseCSV(csvText).filter(isLiveConversionRow);
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const label = `row ${i + 1} ${row.date}`;
    const fields = [row.date, row.source, row.program, row.clicks, row.cv, row.approved_yen, row.note];
    if (fields.some((v) => /https?:\/\//i.test(String(v || '')))) {
      errors.push(`${label}: URL を書くな`);
    }
    for (const col of ['clicks', 'cv', 'approved_yen']) {
      const raw = String(row[col] ?? '').trim();
      if (!/^-?\d+$/.test(raw)) {
        errors.push(`${label}: ${col} は整数`);
        continue;
      }
      if (Number.parseInt(raw, 10) < 0) errors.push(`${label}: ${col} は 0 以上`);
    }
    const yen = toInt(row.approved_yen);
    if (yen > 0 && /カタログ/.test(String(row.note || ''))) {
      errors.push(`${label}: カタログ円を approved_yen に足すな`);
    }
    if (today && row.date > today) {
      errors.push(`${label}: 未来日`);
    }
  }
  const bySource = new Map();
  for (const row of rows) {
    const src = String(row.source || '').trim();
    const prog = String(row.program || '').trim();
    if (!bySource.has(src)) bySource.set(src, new Set());
    bySource.get(src).add(prog);
  }
  for (const [src, progs] of bySource) {
    if (progs.has('all') && progs.size > 1) {
      errors.push(`${src}: program=all と案件別を混ぜるな（円が倍になる）`);
    }
  }
  return errors;
}

function lastLiveConversionDate(csvText) {
  const rows = parseCSV(csvText).filter(isLiveConversionRow);
  let last = null;
  for (const row of rows) {
    if (!last || row.date > last) last = row.date;
  }
  return last;
}

function sourceProgramKey(row) {
  return `${String(row.source || '').trim()}\t${String(row.program || '').trim()}`;
}

/** 同じ source+program は最新日だけ。月次スナップの再掲を足して倍にしない */
function latestBySourceProgram(rows) {
  const map = new Map();
  for (const row of rows) {
    const key = sourceProgramKey(row);
    const prev = map.get(key);
    if (!prev || row.date > prev.date) map.set(key, row);
  }
  return [...map.values()];
}

function sumConversions(csvText) {
  const rows = parseCSV(csvText).filter(isLiveConversionRow);
  const latest = latestBySourceProgram(rows);
  let clicks = 0;
  let cv = 0;
  let approvedYen = 0;
  for (const row of latest) {
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
  blockers.push({
    id: 'high_ticket_nko',
    owner: '指令塔→人間',
    action: 'neo s00000018427001 の掲載媒体はログイン後。置けるなら転職プロフィール。そのあと教育アカで N高 s00000027548001（別アカ。neo を教育に置くな。N高を転職に置くな）。N高が置けなければ チャイルド・アイズ s00000027572003。教育未開設ならアイズも置けない。転職アカが空なら キャリアチケット s00000011866027。未開設・項目なし・媒体なし・YouTubeありならバナー出品するな。新造するな。教育YouTubeは始めるな'
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

## 指令塔へ返す材料

\`output/sprint/WRAP.md\`。参謀は発出しない。採否は指令塔。
`;
}

function renderHumanMd(s) {
  return `# 司令部が人間へ出す1手（参謀下書き）

指令塔がこの文を採否する。Cursor は送らない。今夜の dump は \`G_hq_cw_n10.txt\` が正。

目標 ${s.deadline} 確定 ¥${s.target_yen.toLocaleString()}。実測円 ¥${s.measured_yen.toLocaleString()}。

1. CW fireworker12 で、既応募6件には再応募せず、https://crowdworks.jp/public/jobs/13405300 と https://crowdworks.jp/public/jobs/13405200 と https://crowdworks.jp/public/jobs/13405801 と https://crowdworks.jp/public/jobs/13406725 へ CW_APPLY.md の文で応募して N=10 にせよ。4が合わなければ https://crowdworks.jp/public/jobs/13408073 。それも合わなければ https://crowdworks.jp/public/jobs/13408021 。無い実績は書くな。プロフィールは直すな。
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
  for (const key of ['completed_hours', 'next_hour_task', 'last_dry_run', 'video_judge', 'funnel', 'note_sku1', 'cw_live', 'banner_10', 'measure', 'wrap']) {
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
  const { spawnSync } = require('child_process');
  const verify = spawnSync(process.execPath, [path.join(__dirname, '..', 'scripts', 'verify-secret-overlay.js')], { encoding: 'utf-8' });
  if (verify.status !== 0) throw new Error(`verify-secret-overlay: ${verify.stderr || verify.stdout}`);
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

  const shapeOk = conversionShapeErrors(csv, '2026-08-27');
  if (shapeOk.length) throw new Error(`shape want empty, got ${shapeOk.join('; ')}`);
  const urlBad = conversionShapeErrors(
    'date,source,program,clicks,cv,approved_yen,note\n2026-08-27,A8,all,1,0,0,see https://example.invalid\n',
    '2026-08-27'
  );
  if (!urlBad.some((e) => /URL/.test(e))) throw new Error('URL in note should fail');
  const catalogBad = conversionShapeErrors(
    'date,source,program,clicks,cv,approved_yen,note\n2026-08-27,A8,neo,0,1,15000,sns.php カタログ\n',
    '2026-08-27'
  );
  if (!catalogBad.some((e) => /カタログ/.test(e))) throw new Error('catalog yen should fail');

  const twoDays = [
    'date,source,program,clicks,cv,approved_yen,note',
    '2026-08-27,A8,all,33,0,0,monthly',
    '2026-08-28,A8,all,40,1,15000,monthly'
  ].join('\n');
  const latestSum = sumConversions(twoDays);
  if (latestSum.approvedYen !== 15000) throw new Error(`latest yen want 15000, got ${latestSum.approvedYen}`);
  if (latestSum.clicks !== 40) throw new Error(`latest clicks want 40, got ${latestSum.clicks}`);
  if (latestSum.cv !== 1) throw new Error(`latest cv want 1, got ${latestSum.cv}`);
  if (latestSum.rows !== 2) throw new Error(`rows want 2, got ${latestSum.rows}`);

  const twoPrograms = [
    'date,source,program,clicks,cv,approved_yen,note',
    '2026-08-28,A8,neo,10,1,15000,screen',
    '2026-08-28,A8,nko,2,1,8000,screen'
  ].join('\n');
  const progSum = sumConversions(twoPrograms);
  if (progSum.approvedYen !== 23000) throw new Error(`program yen want 23000, got ${progSum.approvedYen}`);

  const mixed = conversionShapeErrors(
    'date,source,program,clicks,cv,approved_yen,note\n2026-08-27,A8,all,33,0,0,monthly\n2026-08-28,A8,neo,1,1,15000,screen\n',
    '2026-08-28'
  );
  if (!mixed.some((e) => /混ぜるな/.test(e))) throw new Error('all+program mix should fail');

  const dumpDir = path.join(__dirname, '..', 'docs', 'grok-bots', 'dump');
  const readDump = (name) => fs.readFileSync(path.join(dumpDir, name), 'utf8');
  const ticketSns = readDump('G_hq_sns_ticket.txt');
  if (!ticketSns.includes('G_hq_banner_10.txt')) throw new Error('ticket 項目なし should name banner dump');
  const ticketYt = readDump('G_hq_yt_only_ticket.txt');
  if (!ticketYt.includes('G_hq_banner_10.txt')) throw new Error('ticket YouTubeあり should name banner dump');
  const tenshokuExist = readDump('G_hq_tenshoku_exist.txt');
  if (tenshokuExist.includes('ここで止まれ')) throw new Error('tenshoku 未開設 must not stop the chain');
  if (!tenshokuExist.includes('G_hq_banner_10.txt')) throw new Error('tenshoku 未開設 should name banner dump');
  if (!tenshokuExist.includes('EXIST_TICKET.md')) throw new Error('ticket exist dump must not reuse EXIST.md');
  const neoExist = fs.readFileSync(path.join(__dirname, '..', 'docs', 'grok-bots', 'EXIST.md'), 'utf8');
  if (!neoExist.includes('G_hq_sns_nko.txt')) throw new Error('neo 未開設 should still fall to N高');
  const neoProfile = readDump('G_hq_threads_profile.txt');
  if (!neoProfile.includes('G_hq_sns_nko.txt')) throw new Error('neo profile should continue to N高');
  const nkoSns = readDump('G_hq_sns_nko.txt');
  if (!nkoSns.includes('置いたあとでも使え')) throw new Error('N高 dump should run after neo placed');
  if (!nkoSns.includes('G_hq_yt_only_nko.txt')) throw new Error('N高 YouTubeあり should name yt_only_nko');
  if (!nkoSns.includes('G_hq_edu_exist.txt')) throw new Error('N高 Threadsあり should name edu_exist');
  if (!nkoSns.includes('G_hq_a8_partner_nko.txt')) throw new Error('N高 未提携 should name partner_nko');
  const eyesSns = readDump('G_hq_sns_eyes.txt');
  if (!eyesSns.includes('G_hq_yt_only_eyes.txt')) throw new Error('アイズ YouTubeあり should name yt_only_eyes');
  if (!eyesSns.includes('G_hq_edu_exist.txt')) throw new Error('アイズ Threadsあり should name edu_exist');
  const snsNext = readDump('G_hq_sns_next.txt');
  if (!snsNext.includes('G_hq_a8_partner.txt')) throw new Error('neo 未提携 should name partner dump');
  if (!snsNext.includes('G_hq_threads_exist.txt')) throw new Error('neo Threadsあり should name exist dump');
  const threadsExist = readDump('G_hq_threads_exist.txt');
  if (!threadsExist.includes('G_hq_a8_site.txt')) throw new Error('転職 開設済み should name site dump');
  const eduExist = readDump('G_hq_edu_exist.txt');
  if (!eduExist.includes('G_hq_a8_site_edu.txt')) throw new Error('教育 開設済み should name site_edu dump');
  if (!eduExist.includes('アイズ')) throw new Error('edu_exist should also run after アイズ Threadsあり');
  const secretNko = readDump('G_hq_secret_nko.txt');
  if (secretNko.includes('neo が Threadsあり ならこの dump は使うな')) throw new Error('N高 Secret must still run after neo placed');
  if (!secretNko.includes('G_hq_threads_profile_edu.txt')) throw new Error('N高 Secret should name edu profile dump');
  if (!secretNko.includes('SECRET_EDU.md')) throw new Error('N高 Secret should open SECRET_EDU not neo SECRET');
  if (/docs\/grok-bots\/SECRET\.md/.test(secretNko)) throw new Error('N高 Secret must not open neo SECRET.md');
  const secretEyes = readDump('G_hq_secret_eyes.txt');
  if (!secretEyes.includes('SECRET_EDU.md')) throw new Error('アイズ Secret should open SECRET_EDU');
  if (/docs\/grok-bots\/SECRET\.md/.test(secretEyes)) throw new Error('アイズ Secret must not open neo SECRET.md');
  const secretTicket = readDump('G_hq_secret_ticket.txt');
  if (!secretTicket.includes('SECRET_TICKET.md')) throw new Error('ticket Secret should open SECRET_TICKET');
  if (/docs\/grok-bots\/SECRET\.md/.test(secretTicket)) throw new Error('ticket Secret must not open neo SECRET.md');
  const secretNeo = readDump('G_hq_secret_neo.txt');
  if (!secretNeo.includes('G_hq_threads_profile.txt')) throw new Error('neo Secret should name profile dump');
  if (!secretNeo.includes('SECRET.md')) throw new Error('neo Secret should still open SECRET.md');
  const eduProfile = readDump('G_hq_threads_profile_edu.txt');
  if (!eduProfile.includes('PROFILE_EDU.md')) throw new Error('edu profile dump should open PROFILE_EDU not tenshoku PROFILE');
  if (/docs\/grok-bots\/PROFILE\.md/.test(eduProfile)) throw new Error('edu profile dump must not open tenshoku PROFILE.md');
  const eyesProfile = readDump('G_hq_threads_profile_eyes.txt');
  if (!eyesProfile.includes('PROFILE_EDU.md')) throw new Error('eyes profile dump should open PROFILE_EDU');
  if (/docs\/grok-bots\/PROFILE\.md/.test(eyesProfile)) throw new Error('eyes profile dump must not open tenshoku PROFILE.md');
  const ticketProfile = readDump('G_hq_threads_profile_ticket.txt');
  if (!ticketProfile.includes('PROFILE_TICKET.md')) throw new Error('ticket profile dump should open PROFILE_TICKET');
  if (!ticketProfile.includes('EXIST_TICKET.md')) throw new Error('ticket profile dump must open EXIST_TICKET.md');
  if (/docs\/grok-bots\/EXIST\.md/.test(ticketProfile)) throw new Error('ticket profile dump must not open neo EXIST.md');
  const partnerEyes = readDump('G_hq_a8_partner_eyes.txt');
  if (!partnerEyes.includes('PARTNER_EYES.md')) throw new Error('アイズ partner dump should open PARTNER_EYES');
  if (partnerEyes.includes('FUNNEL_LIVE.md')) throw new Error('アイズ partner dump must not open neo-first FUNNEL_LIVE');
  const partnerTicket = readDump('G_hq_a8_partner_ticket.txt');
  if (!partnerTicket.includes('PARTNER_TICKET.md')) throw new Error('ticket partner dump should open PARTNER_TICKET');
  if (partnerTicket.includes('FUNNEL_LIVE.md')) throw new Error('ticket partner dump must not open neo-first FUNNEL_LIVE');
  const nkoSnsApply = readDump('G_hq_sns_nko.txt');
  if (nkoSnsApply.includes('FUNNEL_APPLY.md')) throw new Error('N高 sns dump must not open FUNNEL_APPLY (未提携→neo partner)');
  if (!nkoSnsApply.includes('FUNNEL_NKO.md')) throw new Error('N高 sns dump should open FUNNEL_NKO');
  if (nkoSnsApply.includes('FUNNEL_LIVE.md')) throw new Error('N高 sns dump must not open neo-first FUNNEL_LIVE');
  const eyesSnsApply = readDump('G_hq_sns_eyes.txt');
  if (eyesSnsApply.includes('FUNNEL_APPLY.md')) throw new Error('アイズ sns dump must not open FUNNEL_APPLY (未提携→neo partner)');
  if (!eyesSnsApply.includes('FUNNEL_EYES.md')) throw new Error('アイズ sns dump should open FUNNEL_EYES');
  if (eyesSnsApply.includes('FUNNEL_LIVE.md')) throw new Error('アイズ sns dump must not open neo-first FUNNEL_LIVE');
  if (!ticketSns.includes('FUNNEL_TICKET.md')) throw new Error('ticket sns dump should open FUNNEL_TICKET');
  if (ticketSns.includes('FUNNEL_LIVE.md')) throw new Error('ticket sns dump must not open neo-first FUNNEL_LIVE');
  const ytNko = readDump('G_hq_yt_only_nko.txt');
  if (!ytNko.includes('FUNNEL_NKO.md')) throw new Error('N高 yt_only dump should open FUNNEL_NKO');
  if (ytNko.includes('FUNNEL_LIVE.md')) throw new Error('N高 yt_only dump must not open neo-first FUNNEL_LIVE');
  const ytEyes = readDump('G_hq_yt_only_eyes.txt');
  if (!ytEyes.includes('FUNNEL_EYES.md')) throw new Error('アイズ yt_only dump should open FUNNEL_EYES');
  if (ytEyes.includes('FUNNEL_LIVE.md')) throw new Error('アイズ yt_only dump must not open neo-first FUNNEL_LIVE');
  const ytTicket = readDump('G_hq_yt_only_ticket.txt');
  if (!ytTicket.includes('FUNNEL_TICKET.md')) throw new Error('ticket yt_only dump should open FUNNEL_TICKET');
  if (ytTicket.includes('FUNNEL_LIVE.md')) throw new Error('ticket yt_only dump must not open neo-first FUNNEL_LIVE');
  const ytNeo = readDump('G_hq_yt_only.txt');
  if (!ytNeo.includes('FUNNEL_LIVE.md')) throw new Error('neo yt_only dump should still open FUNNEL_LIVE');
  const partnerNko = readDump('G_hq_a8_partner_nko.txt');
  if (!partnerNko.includes('PARTNER_NKO.md')) throw new Error('N高 partner dump should open PARTNER_NKO');
  if (partnerNko.includes('FUNNEL_LIVE.md')) throw new Error('N高 partner dump must not open neo-first FUNNEL_LIVE');
  if (/docs\/grok-bots\/PARTNER\.md/.test(partnerNko)) throw new Error('N高 partner dump must not open neo PARTNER.md');
  if (threadsExist.includes('SITE.md')) throw new Error('転職 exist dump must not open SITE.md before 開設済み');
  if (eduExist.includes('SITE_EDU.md')) throw new Error('教育 exist dump must not open SITE_EDU.md before 開設済み');
  if (ticketSns.includes('FUNNEL_APPLY.md')) throw new Error('ticket sns dump must not open FUNNEL_APPLY (未提携→neo partner)');
  const mergeOv = readDump('G_hq_merge_overlay.txt');
  if (!mergeOv.includes('次は無い')) throw new Error('merge overlay is the last dump before cron');
  const existEdu = fs.readFileSync(path.join(__dirname, '..', 'docs', 'grok-bots', 'EXIST_EDU.md'), 'utf8');
  if (!existEdu.includes('アイズ')) throw new Error('EXIST_EDU should cover アイズ Threadsあり');
  const cwDump = readDump('G_hq_cw_n10.txt');
  if (!cwDump.includes('13406725')) throw new Error('CW dump should name same-type primary 13406725');
  if (!cwDump.includes('sprint-1m-24h-a971/affiliate-engine/docs/grok-bots/KEEP_CUT.md')) {
    throw new Error('CW dump KEEP_CUT must live on the sprint branch');
  }
  const noteDump = readDump('G_hq_note_place.txt');
  if (!noteDump.includes('sprint-1m-24h-a971/affiliate-engine/docs/grok-bots/ACCOUNT_NOTE.md')) {
    throw new Error('note dump ACCOUNT_NOTE must live on the sprint branch');
  }
  const quoted = cwDump.split('人間へ出す指示は1つ:')[1] || '';
  if (!quoted.includes('13406725')) throw new Error('CW human 1手 should use 13406725 as one of the four');
  if (quoted.includes('13405803')) throw new Error('CW human 1手 should not send 13405803 as a primary URL');
  if (!quoted.includes('13408073')) throw new Error('CW human 1手 same-type alt should be 13408073');
  if (quoted.includes('13407700')) throw new Error('CW human 1手 should not send 通常尺 13407700 as the alt');
  const ht = staleSnap.blockers.find((b) => b.id === 'high_ticket_nko');
  if (!ht || !/バナー/.test(ht.action)) throw new Error('high_ticket blocker should mention banner fallthrough');

  const { validateTemplate, checkContent } = require('./compliance');
  const seed = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', 'seed_templates.json'), 'utf8'));
  const linkKeys = Object.keys(require('../config/links.json')).filter((k) => !k.startsWith('_'));
  const yenIds = [
    'career_20260828_neo_01',
    'career_20260828_neo_02',
    'education_20260828_nko_01',
    'education_20260828_eyes_01',
    'career_20260828_ticket_01'
  ];
  const yenGenres = new Set(['転職', '教育']);
  for (const id of yenIds) {
    const t = (seed.posting_templates || []).find((x) => x.id === id);
    if (!t) throw new Error(`missing yen template ${id}`);
    const structural = validateTemplate(t, { genres: yenGenres, linkKeys });
    if (!structural.ok) throw new Error(`${id} validateTemplate: ${structural.reasons.join(', ')}`);
    const dummy = String(structural.template.content || '').replaceAll('{{AFFILIATE_LINK}}', 'https://example.invalid/x');
    const content = checkContent(dummy);
    if (!content.ok) throw new Error(`${id} checkContent: ${content.reasons.join(', ')}`);
  }
  const funnelLive = fs.readFileSync(path.join(__dirname, '..', 'docs', 'grok-bots', 'FUNNEL_LIVE.md'), 'utf8');
  if (!funnelLive.includes('s00000018427001')) throw new Error('FUNNEL_LIVE should keep neo id');
  const funnelNko = fs.readFileSync(path.join(__dirname, '..', 'docs', 'grok-bots', 'FUNNEL_NKO.md'), 'utf8');
  if (!funnelNko.includes('s00000027548001')) throw new Error('FUNNEL_NKO should name N高 id');
  const funnelEyes = fs.readFileSync(path.join(__dirname, '..', 'docs', 'grok-bots', 'FUNNEL_EYES.md'), 'utf8');
  if (!funnelEyes.includes('s00000027572003')) throw new Error('FUNNEL_EYES should name アイズ id');
  const funnelTicket = fs.readFileSync(path.join(__dirname, '..', 'docs', 'grok-bots', 'FUNNEL_TICKET.md'), 'utf8');
  if (!funnelTicket.includes('s00000011866027')) throw new Error('FUNNEL_TICKET should name ticket id');

  console.log('self-test ok');
}

function main() {
  if (process.argv.includes('--self-test')) {
    selfTest();
    return;
  }
  const csvText = fs.readFileSync(CONVERSIONS_PATH, 'utf-8');
  const today = process.env.SPRINT_TODAY || todayJST();
  const shape = conversionShapeErrors(csvText, today);
  if (shape.length) {
    throw new Error(`conversions.csv が正本として読めない: ${shape.join('; ')}`);
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
  conversionShapeErrors,
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
