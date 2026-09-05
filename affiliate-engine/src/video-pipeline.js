#!/usr/bin/env node
'use strict';

/**
 * 動画パイプライン（指示書の生成と 48h レビューだけ）。
 *
 * やること:
 * - 9ジャンル × 2日に1回を日付から決定論的に割る
 * - 同日の有効ジャンルを 30 分ずらして Grokbot 指示書ファイルを書く
 * - 投稿から 48 時間後の views.csv を見て keep / delete_candidate / needs_* を付ける
 *
 * やらないこと:
 * - Grokbot / Grok Imagine の API 呼び出し（仕様がリポジトリに無い）
 * - YouTube / Instagram / TikTok への投稿
 * - 動画の自動削除
 * - 視聴回数・基準値の発明
 *
 *   node src/video-pipeline.js --self-test
 *   node src/video-pipeline.js --schedule --dry-run
 *   node src/video-pipeline.js --emit --review
 *   VIDEO_PIPELINE_DATE=2026-08-26 node src/video-pipeline.js --schedule
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { spawnSync } = require('child_process');
const {
  ROOT,
  OUTPUT_DIR,
  parseCSV,
  escapeCSV,
  loadConfig,
  todayJST,
  scheduleEpoch
} = require('./util');
const { PROFILE_CTA } = require('./youtube-cta');
const { GATES, addDays } = require('./video-judge');

const CONFIG_NAME = 'video-pipeline';
const GENRES_CSV = path.join(ROOT, 'data', 'video', 'genres.csv');
const PACKETS_CSV = path.join(ROOT, 'data', 'video', 'packets.csv');
const POSTS_CSV = path.join(ROOT, 'data', 'video', 'posts.csv');
const VIEWS_CSV = path.join(ROOT, 'data', 'video', 'views.csv');
const DELETIONS_CSV = path.join(ROOT, 'data', 'video', 'deletions.csv');
const TEMPLATE_PATH = path.join(ROOT, 'prompts', 'grokbot-instruction.md');
const PIPELINE_OUT = path.join(OUTPUT_DIR, 'video', 'pipeline');
const CATCHUP_HOURS = parseFloat(process.env.VIDEO_PIPELINE_CATCHUP_HOURS || '24');
const EMIT_LIMIT = Number.parseInt(process.env.VIDEO_PIPELINE_EMIT_LIMIT || '1', 10);

const PACKET_HEADERS = [
  'id',
  'genre_key',
  'genre',
  'scheduled_date',
  'scheduled_time',
  'status',
  'packet_path',
  'note'
];
const SCHEDULE_HEADERS = [
  'date',
  'time',
  'genre_key',
  'genre',
  'video_enabled',
  'action'
];

function argvFlag(name) {
  return process.argv.includes(name);
}

function argvValue(name) {
  const idx = process.argv.indexOf(name);
  if (idx === -1) return null;
  return process.argv[idx + 1] || null;
}

function epochDay(date) {
  return Math.floor(new Date(`${date}T00:00:00+09:00`).getTime() / 86400000);
}

function addMinutesToHm(hm, minutes) {
  if (!/^\d{2}:\d{2}$/.test(hm || '')) return null;
  const [h, m] = hm.split(':').map(Number);
  const total = h * 60 + m + minutes;
  if (total < 0 || total >= 24 * 60) return null;
  return `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`;
}

function isTruthy(value) {
  return /^(true|1|yes)$/i.test(String(value || '').trim());
}

function isExampleRow(row) {
  return /\bexample\b/i.test(String(row.note || ''));
}

function toCSV(headers, rows) {
  const lines = [headers.join(',')];
  for (const row of rows) {
    lines.push(headers.map((h) => escapeCSV(row[h] ?? '')).join(','));
  }
  return `${lines.join('\n')}\n`;
}

function readCsvOrEmpty(filePath) {
  if (!fs.existsSync(filePath)) return [];
  return parseCSV(fs.readFileSync(filePath, 'utf-8'));
}

function writeCsv(filePath, headers, rows) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, toCSV(headers, rows), 'utf-8');
}

function packetId(date, time, genreKey) {
  return `vp_${date}_${String(time).replace(':', '')}_${genreKey}`;
}

function inVideoExperiment(today) {
  const start = GATES.experimentStart;
  const end = addDays(start, GATES.experimentDays - 1);
  return today >= start && today <= end;
}

function loadPipelineConfig(raw) {
  const cfg = raw || loadConfig(CONFIG_NAME, null);
  if (!cfg) throw new Error('config/video-pipeline.json が無い');

  const durationMin = Number(cfg.duration_sec_min);
  const durationMax = Number(cfg.duration_sec_max);
  const every = Number(cfg.post_every_n_days);
  const stagger = Number(cfg.stagger_minutes);
  const reviewAfter = Number(cfg.review_after_hours);
  const campaignDays = Number(cfg.campaign_days || 14);
  const slotStart = String(cfg.slot_start_jst || '');
  const thresholdRaw = cfg.view_threshold_48h;
  const threshold =
    thresholdRaw === null || thresholdRaw === undefined || thresholdRaw === ''
      ? null
      : Number(thresholdRaw);

  if (!Number.isFinite(durationMin) || !Number.isFinite(durationMax) || durationMin > durationMax) {
    throw new Error('duration_sec_min / duration_sec_max が不正');
  }
  if (!Number.isInteger(every) || every < 1) throw new Error('post_every_n_days は 1 以上の整数');
  if (!Number.isInteger(stagger) || stagger < 1) throw new Error('stagger_minutes は 1 以上の整数');
  if (!Number.isFinite(reviewAfter) || reviewAfter < 0) throw new Error('review_after_hours が不正');
  if (!Number.isInteger(campaignDays) || campaignDays < 1) throw new Error('campaign_days が不正');
  if (!/^\d{2}:\d{2}$/.test(slotStart)) throw new Error('slot_start_jst は HH:MM');
  if (threshold !== null && !Number.isFinite(threshold)) throw new Error('view_threshold_48h が不正');
  if (!Array.isArray(cfg.platforms) || cfg.platforms.length === 0) {
    throw new Error('platforms が空');
  }

  return {
    durationMin,
    durationMax,
    every,
    stagger,
    reviewAfter,
    campaignDays,
    slotStart,
    threshold,
    generationEnabled: cfg.generation_enabled === true,
    autoPost: cfg.auto_post === true,
    autoDelete: cfg.auto_delete === true,
    grokbotTransport: String(cfg.grokbot_transport || 'file'),
    platforms: cfg.platforms
  };
}

function loadGenreMaster(accountsConfig, csvText) {
  const accounts = (accountsConfig || loadConfig('accounts', { accounts: [] })).accounts || [];
  if (accounts.length === 0) throw new Error('config/accounts.json にアカウントが無い');

  const rows = parseCSV(csvText != null ? csvText : fs.readFileSync(GENRES_CSV, 'utf-8'));
  const byKey = new Map(rows.map((r) => [r.key, r]));

  for (const acc of accounts) {
    const row = byKey.get(acc.key);
    if (!row) throw new Error(`genres.csv に key=${acc.key} が無い`);
    if (row.genre !== acc.genre) {
      throw new Error(`genres.csv のジャンル不一致: ${acc.key} accounts=${acc.genre} csv=${row.genre}`);
    }
  }
  for (const row of rows) {
    if (!accounts.some((a) => a.key === row.key)) {
      throw new Error(`genres.csv の未知の key=${row.key}`);
    }
  }

  return accounts.map((acc, index) => {
    const row = byKey.get(acc.key);
    return {
      index,
      key: acc.key,
      genre: acc.genre,
      video_enabled: isTruthy(row.video_enabled),
      youtube_handle: String(row.youtube_handle || '').trim(),
      note: String(row.note || '').trim()
    };
  });
}

function enabledPlatforms(config) {
  return config.platforms.filter((p) => p.enabled === true);
}

function linkPolicyMarkdown(config, genreRow, links) {
  const lines = [];
  for (const p of config.platforms) {
    if (p.enabled === true) {
      if (p.id === 'youtube_shorts') {
        const handle = genreRow.youtube_handle || '（未記入。発明しない）';
        lines.push(
          `### ${p.label}（enabled）\n- チャンネル: ${handle}\n- URL 禁止。口頭/テロップは「${PROFILE_CTA}」1回。\n- links.json のこのジャンル枠は空でも、説明欄に URL を足すな。`
        );
      } else {
        lines.push(
          `### ${p.label}（enabled）\n- リンク設置位置は未確認。URL を発明して置くな。人間が媒体の公式ヘルプを確認するまで投稿指示を出すな。`
        );
      }
    } else {
      lines.push(`### ${p.label}（disabled）\n- ${p.blocked_reason || '有効化されていない。この媒体用の動画を作るな。'}`);
    }
  }

  const keys = Object.keys(links || {}).filter((k) => !k.startsWith('_') && k.startsWith(genreRow.genre));
  const setKeys = keys.filter((k) => String(links[k] || '').trim() !== '');
  lines.push('');
  lines.push(
    setKeys.length
      ? `links.json で値が入っているキー: ${setKeys.join(', ')}（値は指示書に書かない）`
      : `links.json の「${genreRow.genre}」枠はすべて空。リンク URL を発明するな。`
  );
  return lines.join('\n');
}

function feedbackSection(genreKey, deletions, reviews) {
  const bits = [];
  const del = (deletions || []).filter((d) => d.genre_key === genreKey && !isExampleRow(d));
  for (const d of del) {
    bits.push(
      `- 削除記録 ${d.post_id || ''} ${d.platform || ''} views=${d.views_at_delete || '（無記入）'} reason=${d.reason || ''} feedback=${d.feedback || ''}`
    );
  }
  const flagged = (reviews || []).filter(
    (r) => r.genre_key === genreKey && (r.status === 'delete_candidate' || r.status === 'needs_threshold')
  );
  for (const r of flagged) {
    bits.push(`- レビュー ${r.post_id} ${r.status}: ${r.reason}`);
  }
  if (bits.length === 0) {
    return '記録なし。数字も型の変更も発明しない。';
  }
  return bits.join('\n');
}

function fillTemplate(template, vars) {
  let out = String(template);
  for (const [key, value] of Object.entries(vars)) {
    out = out.split(`{{${key}}}`).join(String(value));
  }
  const leftover = out.match(/\{\{[A-Z0-9_]+\}\}/g);
  if (leftover) throw new Error(`テンプレ未置換: ${leftover.join(', ')}`);
  return out;
}

function experimentStatus(today) {
  if (!inVideoExperiment(today)) {
    return `実験期間外（${GATES.experimentStart} から ${GATES.experimentDays} 日）`;
  }
  const day = Math.round(
    (new Date(`${today}T00:00:00+09:00`) - new Date(`${GATES.experimentStart}T00:00:00+09:00`)) /
      86400000
  ) + 1;
  return `実験 ${day}/${GATES.experimentDays}日目。新作の型を作るな。次の癒し3本を再掲するだけ。`;
}

function buildDayPlan(date, genres, config, { generationEnabled, inExperiment } = {}) {
  const genOn = generationEnabled === true;
  const exp = inExperiment === true;
  const due = genres.filter((g) => (epochDay(date) + g.index) % config.every === 0);
  const enabledDue = due.filter((g) => g.video_enabled);
  const timesByKey = new Map();
  for (let i = 0; i < enabledDue.length; i++) {
    timesByKey.set(enabledDue[i].key, addMinutesToHm(config.slotStart, i * config.stagger));
  }

  const platformsOn = enabledPlatforms(config);
  return due.map((genre) => {
    const time = timesByKey.get(genre.key) || '';
    let action = 'emit_packet';
    if (!genre.video_enabled) action = 'skip_disabled';
    else if (platformsOn.length === 0) action = 'skip_no_platform';
    else if (!genOn) action = 'skip_generation_disabled';
    else if (exp) action = 'skip_experiment';
    else if (!time) action = 'skip_time_overflow';
    return {
      date,
      time,
      genre_key: genre.key,
      genre: genre.genre,
      video_enabled: genre.video_enabled ? 'true' : 'false',
      action,
      genreRow: genre
    };
  });
}

function buildScheduleRows(fromDate, days, genres, config, opts) {
  const rows = [];
  for (let d = 0; d < days; d++) {
    const date = addDays(fromDate, d);
    rows.push(...buildDayPlan(date, genres, config, opts));
  }
  return rows;
}

function renderPacket(slot, config, links, deletions, template, today) {
  const platforms = enabledPlatforms(config)
    .map((p) => p.label)
    .join(' / ');
  const id = packetId(slot.date, slot.time, slot.genre_key);
  const body = fillTemplate(template, {
    SCHEDULE_DATE: slot.date,
    SCHEDULE_TIME: slot.time,
    PACKET_ID: id,
    GENRE: slot.genre,
    GENRE_KEY: slot.genre_key,
    DURATION_MIN: config.durationMin,
    DURATION_MAX: config.durationMax,
    PLATFORMS: platforms || '（有効な媒体なし）',
    YOUTUBE_HANDLE: slot.genreRow.youtube_handle || '（未記入）',
    LINK_POLICY: linkPolicyMarkdown(config, slot.genreRow, links),
    PROFILE_CTA,
    FEEDBACK_SECTION: feedbackSection(slot.genre_key, deletions, []),
    GENERATION_ENABLED: String(config.generationEnabled),
    EXPERIMENT_STATUS: experimentStatus(today)
  });
  return { id, body };
}

function dueEmitSlots(planRows, nowMs, already, { catchupHours = CATCHUP_HOURS, emitLimit = EMIT_LIMIT } = {}) {
  const windowStart = nowMs - catchupHours * 3600 * 1000;
  const arrived = planRows.filter((row) => {
    if (row.action !== 'emit_packet') return false;
    if (!row.time) return false;
    const t = scheduleEpoch(row.date, row.time);
    if (t > nowMs || t < windowStart) return false;
    const id = packetId(row.date, row.time, row.genre_key);
    return !already.has(id);
  });
  arrived.sort((a, b) => scheduleEpoch(a.date, a.time) - scheduleEpoch(b.date, b.time));
  const limit = Number.isInteger(emitLimit) && emitLimit > 0 ? emitLimit : 1;
  return arrived.slice(0, limit);
}

function writePacketFiles(slot, packet, dryRun) {
  const rel = path.join('output', 'video', 'pipeline', 'packets', `${packet.id}.md`);
  const abs = path.join(ROOT, rel);
  if (!dryRun) {
    fs.mkdirSync(path.dirname(abs), { recursive: true });
    fs.writeFileSync(abs, packet.body, 'utf-8');
  }
  return rel;
}

function upsertPacketRow(rows, slot, packet, relPath, note) {
  const next = rows.filter((r) => r.id !== packet.id);
  next.push({
    id: packet.id,
    genre_key: slot.genre_key,
    genre: slot.genre,
    scheduled_date: slot.date,
    scheduled_time: slot.time,
    status: 'packet_emitted',
    packet_path: relPath,
    note: note || ''
  });
  next.sort((a, b) => String(a.id).localeCompare(String(b.id)));
  return next;
}

function reviewPost(post, viewRows, { nowMs, threshold, reviewAfterHours }) {
  if (isExampleRow(post)) {
    return { status: 'ignored_example', reason: 'example 行は見ない' };
  }
  if (!post.published_at) {
    return { status: 'awaiting_publish', reason: 'published_at が無い。投稿は人間が行う' };
  }
  const published = Date.parse(post.published_at);
  if (!Number.isFinite(published)) {
    return { status: 'invalid_published_at', reason: `published_at が日付として読めない: ${post.published_at}` };
  }
  const hours = (nowMs - published) / 3600000;
  if (hours < reviewAfterHours) {
    return {
      status: 'warming',
      reason: `公開から ${hours.toFixed(1)} 時間。${reviewAfterHours} 時間未満なので判定しない`
    };
  }
  const views = (viewRows || []).filter(
    (v) => v.post_id === post.id && !isExampleRow(v) && (v.platform || '') === (post.platform || '')
  );
  if (views.length === 0 || String(views[views.length - 1].views || '').trim() === '') {
    return { status: 'needs_views', reason: 'views.csv に数字が無い。発明しない' };
  }
  if (threshold === null) {
    return {
      status: 'needs_threshold',
      reason: 'view_threshold_48h が null。基準値が無いので削除判定しない'
    };
  }
  const n = Number.parseInt(String(views[views.length - 1].views).trim(), 10);
  if (!Number.isFinite(n)) {
    return { status: 'needs_views', reason: 'views が整数として読めない。発明しない' };
  }
  if (n < threshold) {
    return { status: 'delete_candidate', reason: `views ${n} < 基準 ${threshold}。自動削除はしない` };
  }
  return { status: 'keep', reason: `views ${n} >= 基準 ${threshold}` };
}

function renderReviewMarkdown(today, results, config) {
  const lines = [
    '# 動画パイプライン 48h レビュー',
    '',
    `日付: ${today}（JST）`,
    `基準値 view_threshold_48h: ${config.threshold === null ? 'null（未設定）' : config.threshold}`,
    `自動削除: しない`,
    ''
  ];
  if (results.length === 0) {
    lines.push('判定対象の投稿行が無い。posts.csv に published_at を人間が書く。');
    lines.push('');
    return `${lines.join('\n')}\n`;
  }
  lines.push('| post_id | genre | platform | status | reason |');
  lines.push('|---|---|---|---|---|');
  for (const r of results) {
    lines.push(
      `| ${r.post_id} | ${r.genre_key || ''} | ${r.platform || ''} | ${r.status} | ${String(r.reason).replace(/\|/g, '/')} |`
    );
  }
  lines.push('');
  return `${lines.join('\n')}\n`;
}

function assertEqual(actual, expected, label) {
  if (actual !== expected) throw new Error(`${label}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
}

function assert(cond, label) {
  if (!cond) throw new Error(label);
}

function fixtureConfig(overrides = {}) {
  const base = loadPipelineConfig({
    duration_sec_min: 30,
    duration_sec_max: 60,
    post_every_n_days: 2,
    stagger_minutes: 30,
    review_after_hours: 48,
    view_threshold_48h: null,
    slot_start_jst: '00:00',
    generation_enabled: false,
    auto_post: false,
    auto_delete: false,
    grokbot_transport: 'file',
    campaign_days: 14,
    platforms: [
      { id: 'youtube_shorts', label: 'YouTube Shorts', enabled: true },
      {
        id: 'instagram_reels',
        label: 'Instagram Reels',
        enabled: false,
        blocked_reason: 'test disabled'
      },
      { id: 'tiktok', label: 'TikTok', enabled: false, blocked_reason: 'test disabled' }
    ]
  });
  return { ...base, ...overrides };
}

function fixtureGenres(allEnabled) {
  const names = [
    ['konkatsu', '婚活'],
    ['sidejob', '副業'],
    ['beauty', '美容'],
    ['bodymake', '筋トレ'],
    ['education', '教育'],
    ['setsuyaku', '節約'],
    ['tenshoku', '転職'],
    ['pet', 'ペット'],
    ['sleep', '睡眠']
  ];
  return names.map(([key, genre], index) => ({
    index,
    key,
    genre,
    video_enabled: allEnabled ? true : key === 'pet',
    youtube_handle: key === 'pet' ? '@pet_story_select' : '',
    note: ''
  }));
}

function runSelfTest() {
  const accounts = {
    accounts: fixtureGenres(false).map((g) => ({ key: g.key, genre: g.genre, enabled: true }))
  };
  const csv = [
    'key,genre,video_enabled,youtube_handle,note',
    ...fixtureGenres(false).map(
      (g) => `${g.key},${g.genre},${g.video_enabled},${g.youtube_handle},`
    )
  ].join('\n');
  const loaded = loadGenreMaster(accounts, csv);
  assertEqual(loaded.length, 9, '9 genres');
  assertEqual(loaded.filter((g) => g.video_enabled).map((g) => g.key).join(','), 'pet', 'only pet enabled');

  const mismatchCsv = csv.replace('pet,ペット', 'pet,猫');
  let threw = false;
  try {
    loadGenreMaster(accounts, mismatchCsv);
  } catch (err) {
    threw = /ジャンル不一致/.test(err.message);
  }
  assert(threw, 'genre mismatch rejected');

  const cfg = fixtureConfig({ generationEnabled: true });
  const all = fixtureGenres(true);
  const dayA = '2026-08-26';
  const dayB = addDays(dayA, 1);
  const counts = Object.fromEntries(all.map((g) => [g.key, 0]));
  for (const date of [dayA, dayB]) {
    for (const row of buildDayPlan(date, all, cfg, { generationEnabled: true, inExperiment: false })) {
      counts[row.genre_key] += 1;
    }
  }
  for (const g of all) assertEqual(counts[g.key], 1, `${g.key} once per 2 days`);

  const evenPlan = buildDayPlan(dayA, all, cfg, { generationEnabled: true, inExperiment: false });
  const times = evenPlan.filter((r) => r.video_enabled === 'true').map((r) => r.time);
  for (let i = 1; i < times.length; i++) {
    const prev = scheduleEpoch(dayA, times[i - 1]);
    const next = scheduleEpoch(dayA, times[i]);
    assertEqual(next - prev, 30 * 60 * 1000, `stagger 30min ${times[i - 1]} -> ${times[i]}`);
  }

  const rows1 = buildScheduleRows(dayA, 14, all, cfg, { generationEnabled: true, inExperiment: false });
  const rows2 = buildScheduleRows(dayA, 14, all, cfg, { generationEnabled: true, inExperiment: false });
  const csv1 = toCSV(SCHEDULE_HEADERS, rows1.map(({ genreRow, ...rest }) => rest));
  const csv2 = toCSV(SCHEDULE_HEADERS, rows2.map(({ genreRow, ...rest }) => rest));
  assertEqual(
    crypto.createHash('md5').update(csv1).digest('hex'),
    crypto.createHash('md5').update(csv2).digest('hex'),
    'schedule md5'
  );

  const petOnly = fixtureGenres(false);

  function findPetSlot(fromDate, opts, predicate) {
    for (let d = 0; d < 4; d++) {
      const date = addDays(fromDate, d);
      const plan = buildDayPlan(date, petOnly, fixtureConfig({ generationEnabled: true }), opts);
      const hit = plan.find((r) => r.genre_key === 'pet' && predicate(r));
      if (hit) return hit;
    }
    return null;
  }

  const petDuring = findPetSlot(
    '2026-08-22',
    { generationEnabled: true, inExperiment: true },
    (r) => r.genre_key === 'pet'
  );
  assert(petDuring, 'pet due during experiment');
  assertEqual(petDuring.action, 'skip_experiment', 'experiment blocks emit');

  const petOff = findPetSlot(
    '2026-09-10',
    { generationEnabled: false, inExperiment: false },
    (r) => r.genre_key === 'pet'
  );
  assert(petOff, 'pet due after experiment');
  assertEqual(petOff.action, 'skip_generation_disabled', 'generation flag');

  const petLive = findPetSlot(
    '2026-09-10',
    { generationEnabled: true, inExperiment: false },
    (r) => r.action === 'emit_packet'
  );
  assert(petLive, 'pet emit slot after experiment');
  const template = fs.readFileSync(TEMPLATE_PATH, 'utf-8');
  const packet = renderPacket(
    petLive,
    fixtureConfig({ generationEnabled: true }),
    { ペット_Furbo: '', ペット_保険: '' },
    [],
    template,
    petLive.date
  );
  assert(packet.body.includes(PROFILE_CTA), 'profile cta');
  assert(packet.body.includes('#PR'), 'pr');
  assert(packet.body.includes('投稿しない'), 'no post');
  assert(packet.body.includes('Instagram Reels（disabled）'), 'ig disabled');
  assert(packet.body.includes('support.google.com/youtube/answer/13748639'), 'shorts url fact');
  assert(!/\{\{[A-Z0-9_]+\}\}/.test(packet.body), 'no leftover placeholders');

  const twoDue = evenPlan.filter((r) => r.action === 'emit_packet').slice(0, 2);
  assert(twoDue.length === 2, 'two emit slots on a full-enabled day');
  const noon = scheduleEpoch(twoDue[1].date, twoDue[1].time) + 60 * 1000;
  const firstOnly = dueEmitSlots(twoDue, noon, new Set(), { catchupHours: 24, emitLimit: 1 });
  assertEqual(firstOnly.length, 1, 'emit one at a time');
  assertEqual(firstOnly[0].genre_key, twoDue[0].genre_key, 'earliest slot first');

  const now = Date.parse('2026-08-26T12:00:00+09:00');
  const reviewOpts = { nowMs: now, threshold: null, reviewAfterHours: 48 };
  assertEqual(
    reviewPost({ id: 'p1', published_at: '', platform: 'youtube_shorts' }, [], reviewOpts).status,
    'awaiting_publish',
    'no published_at'
  );
  assertEqual(
    reviewPost(
      { id: 'p1', published_at: '2026-08-25T12:00:00+09:00', platform: 'youtube_shorts' },
      [],
      reviewOpts
    ).status,
    'warming',
    'under 48h'
  );
  assertEqual(
    reviewPost(
      { id: 'p1', published_at: '2026-08-24T00:00:00+09:00', platform: 'youtube_shorts' },
      [],
      reviewOpts
    ).status,
    'needs_views',
    'no views'
  );
  assertEqual(
    reviewPost(
      { id: 'p1', published_at: '2026-08-24T00:00:00+09:00', platform: 'youtube_shorts' },
      [{ post_id: 'p1', platform: 'youtube_shorts', views: '100', note: '' }],
      reviewOpts
    ).status,
    'needs_threshold',
    'null threshold'
  );
  assertEqual(
    reviewPost(
      { id: 'p1', published_at: '2026-08-24T00:00:00+09:00', platform: 'youtube_shorts' },
      [{ post_id: 'p1', platform: 'youtube_shorts', views: '10', note: '' }],
      { nowMs: now, threshold: 50, reviewAfterHours: 48 }
    ).status,
    'delete_candidate',
    'below threshold'
  );
  assertEqual(
    reviewPost(
      { id: 'p1', published_at: '2026-08-24T00:00:00+09:00', platform: 'youtube_shorts' },
      [{ post_id: 'p1', platform: 'youtube_shorts', views: '80', note: '' }],
      { nowMs: now, threshold: 50, reviewAfterHours: 48 }
    ).status,
    'keep',
    'above threshold'
  );

  assertEqual(inVideoExperiment('2026-08-22'), true, 'exp start');
  assertEqual(inVideoExperiment('2026-09-04'), true, 'exp last day');
  assertEqual(inVideoExperiment('2026-09-05'), false, 'exp over');

  const disabled = fixtureConfig({
    generationEnabled: true,
    platforms: [{ id: 'youtube_shorts', label: 'YouTube Shorts', enabled: false }]
  });
  const noPlat = buildDayPlan(petLive.date, petOnly, disabled, {
    generationEnabled: true,
    inExperiment: false
  }).find((r) => r.genre_key === 'pet');
  assert(noPlat, 'pet row when platforms off');
  assertEqual(noPlat.action, 'skip_no_platform', 'no platform');

  const denied = spawnSync(process.execPath, [__filename, '--post'], { encoding: 'utf-8' });
  assertEqual(denied.status, 2, 'post refused');
  assert(/実投稿は未実装/.test(denied.stderr || ''), 'post error text');

  const deniedDel = spawnSync(process.execPath, [__filename, '--delete'], { encoding: 'utf-8' });
  assertEqual(deniedDel.status, 2, 'delete refused');

  console.log('self-test ok');
}

function refuseWriteApis() {
  if (argvFlag('--post') || argvFlag('--upload') || argvFlag('--publish')) {
    console.error(
      '実投稿は未実装。YouTube / Instagram / TikTok の投稿 API 仕様がこのリポジトリに無い。video-cash-loop: 投稿を自動化するな。'
    );
    process.exit(2);
  }
  if (argvFlag('--delete') || argvFlag('--remove')) {
    console.error(
      '自動削除は未実装。基準値が config で null。削除は人間が行い deletions.csv に残す。'
    );
    process.exit(2);
  }
}

function loadRuntime() {
  const config = loadPipelineConfig();
  if (config.autoPost !== false) throw new Error('auto_post を true にしない。投稿 API 未確認');
  if (config.autoDelete !== false) throw new Error('auto_delete を true にしない。削除 API 未確認');
  if (config.grokbotTransport !== 'file') {
    throw new Error(`grokbot_transport=${config.grokbotTransport} は未対応。file のみ`);
  }
  const genres = loadGenreMaster();
  const links = loadConfig('links', {});
  const today = process.env.VIDEO_PIPELINE_DATE || argvValue('--date') || todayJST();
  const days = Number.parseInt(argvValue('--days') || String(config.campaignDays), 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(today)) throw new Error('date は YYYY-MM-DD');
  if (!Number.isInteger(days) || days < 1) throw new Error('days が不正');
  return { config, genres, links, today, days };
}

function runSchedule(runtime, dryRun) {
  const { config, genres, today, days } = runtime;
  const daily = [];
  for (let d = 0; d < days; d++) {
    const date = addDays(today, d);
    daily.push(
      ...buildDayPlan(date, genres, config, {
        generationEnabled: config.generationEnabled,
        inExperiment: inVideoExperiment(date)
      })
    );
  }

  const outRows = daily.map(({ genreRow, ...rest }) => rest);
  const text = toCSV(SCHEDULE_HEADERS, outRows);
  const outPath = path.join(PIPELINE_OUT, 'schedule.csv');
  if (!dryRun) {
    fs.mkdirSync(PIPELINE_OUT, { recursive: true });
    fs.writeFileSync(outPath, text, 'utf-8');
  }
  const emitCount = outRows.filter((r) => r.action === 'emit_packet').length;
  const skip = {};
  for (const r of outRows) skip[r.action] = (skip[r.action] || 0) + 1;
  console.log(`schedule ${today} +${days}d  rows=${outRows.length} emit_packet=${emitCount}`);
  console.log(`  actions: ${JSON.stringify(skip)}`);
  if (!dryRun) console.log(`  ${outPath}`);
  return { outPath, rows: daily, text };
}

function runEmit(runtime, dryRun, nowMs) {
  const { config, genres, links, today } = runtime;
  const plan = buildDayPlan(today, genres, config, {
    generationEnabled: config.generationEnabled,
    inExperiment: inVideoExperiment(today)
  });
  const existing = readCsvOrEmpty(PACKETS_CSV).filter((r) => r.id);
  const already = new Set(existing.map((r) => r.id));
  const due = dueEmitSlots(plan, nowMs, already);
  const template = fs.readFileSync(TEMPLATE_PATH, 'utf-8');
  const deletions = readCsvOrEmpty(DELETIONS_CSV);
  let packets = existing;
  const written = [];

  for (const slot of due) {
    const packet = renderPacket(slot, config, links, deletions, template, today);
    const rel = writePacketFiles(slot, packet, dryRun);
    packets = upsertPacketRow(packets, slot, packet, rel, dryRun ? 'dry-run' : '');
    written.push({ id: packet.id, path: rel, genre: slot.genre });
    console.log(`  packet ${dryRun ? '(dry-run) ' : ''}${packet.id}`);
  }

  if (!dryRun && written.length) writeCsv(PACKETS_CSV, PACKET_HEADERS, packets);
  if (due.length === 0) {
    const reasons = [...new Set(plan.map((p) => p.action))];
    console.log(`emit 0 件。today=${today} actions=${reasons.join(',')}`);
  } else {
    console.log(`emit ${written.length} 件`);
  }
  return { written, plan };
}

function runReview(runtime, dryRun, nowMs) {
  const { config, today } = runtime;
  const posts = readCsvOrEmpty(POSTS_CSV).filter((p) => p.id && !isExampleRow(p));
  const views = readCsvOrEmpty(VIEWS_CSV);
  const results = posts.map((post) => {
    const verdict = reviewPost(post, views, {
      nowMs,
      threshold: config.threshold,
      reviewAfterHours: config.reviewAfter
    });
    return {
      post_id: post.id,
      packet_id: post.packet_id,
      genre_key: post.genre_key,
      platform: post.platform,
      ...verdict
    };
  });
  const markdown = renderReviewMarkdown(today, results, config);
  const outPath = path.join(PIPELINE_OUT, `review_${today}.md`);
  const latest = path.join(PIPELINE_OUT, 'review_latest.md');
  if (!dryRun) {
    fs.mkdirSync(PIPELINE_OUT, { recursive: true });
    fs.writeFileSync(outPath, markdown, 'utf-8');
    fs.writeFileSync(latest, markdown, 'utf-8');
    fs.writeFileSync(
      path.join(PIPELINE_OUT, 'review_latest.json'),
      JSON.stringify({ generated_at: new Date().toISOString(), today, results }, null, 2),
      'utf-8'
    );
  }
  console.log(`review ${results.length} 件 → ${dryRun ? '(dry-run)' : outPath}`);
  process.stdout.write(markdown);
  return { results, markdown };
}

function main() {
  refuseWriteApis();
  const dryRun = argvFlag('--dry-run');
  const wantSchedule = argvFlag('--schedule');
  const wantEmit = argvFlag('--emit');
  const wantReview = argvFlag('--review');
  const wantJson = argvFlag('--json');
  const doAll = !wantSchedule && !wantEmit && !wantReview;

  const runtime = loadRuntime();
  const nowMs = Date.now();
  const payload = { today: runtime.today, dryRun };

  if (wantSchedule || doAll) payload.schedule = runSchedule(runtime, dryRun);
  if (wantEmit || doAll) payload.emit = runEmit(runtime, dryRun, nowMs);
  if (wantReview || doAll) payload.review = runReview(runtime, dryRun, nowMs);

  if (wantJson) {
    const slim = {
      today: payload.today,
      dryRun,
      schedule_actions: payload.schedule
        ? payload.schedule.rows.reduce((acc, r) => {
            acc[r.action] = (acc[r.action] || 0) + 1;
            return acc;
          }, {})
        : null,
      emitted: payload.emit ? payload.emit.written.map((w) => w.id) : [],
      review: payload.review ? payload.review.results : []
    };
    process.stdout.write(`${JSON.stringify(slim, null, 2)}\n`);
  }
}

module.exports = {
  epochDay,
  addMinutesToHm,
  loadPipelineConfig,
  loadGenreMaster,
  buildDayPlan,
  buildScheduleRows,
  fillTemplate,
  reviewPost,
  inVideoExperiment,
  packetId,
  dueEmitSlots
};

if (require.main === module) {
  if (argvFlag('--self-test')) {
    try {
      runSelfTest();
    } catch (err) {
      console.error(`self-test failed: ${err.message}`);
      process.exit(1);
    }
  } else {
    try {
      main();
    } catch (err) {
      console.error(`video-pipeline failed: ${err.message}`);
      process.exit(1);
    }
  }
}
