#!/usr/bin/env node
'use strict';

/**
 * Video Poster（YouTube Shorts / TikTok / Instagram Reels 多アカウント・ステートレス）
 *
 * threads-poster.js の設計をそのまま動画に移した:
 * - 常駐しない。起動時に「期日が来ている未投稿分」だけ投稿して終了する
 * - 状態は output/state/video_posted.json（済みキー + 直近の内容ハッシュ）
 * - 投稿前に compliance.js を通す。URL はどの媒体でも本文に置かない（押せる場所はプロフィール）
 *
 * threads-poster に無い関門（動画特有）:
 * 1. video-judge.js のゲート: output/video/latest.json の posting.allowed が false の日、
 *    または platforms に無い媒体には投稿しない。判定が2日以上古ければ全部止める
 * 2. ライブゲート: config/video_accounts.json の live_enabled=true と
 *    環境変数 VIDEO_POST_LIVE_CONFIRM=I_UNDERSTAND_THE_RISK の両方が無ければ常にドライラン
 * 3. 週次上限: ゲートの weekly_cap を state の直近7日成功数で守る
 *
 * アカウントは人間が手動で開設し、video-oauth.js で OAuth 登録したトークンを Secrets に置く。
 * アカウントの自動作成は行わない（各媒体の規約違反）。
 *
 * 使用方法:
 *   node src/video-poster.js [--dry-run]
 *   node src/video-poster.js --self-test
 *   node src/video-poster.js --refresh-tokens
 *   node src/video-poster.js --enqueue --account pet_youtube --video <path|https URL> \
 *        --title "..." --desc "..." [--date YYYY-MM-DD] [--time HH:MM] [--template-id ID]
 *
 * キュー（output/video_queue.jsonl、1行1件）:
 *   {"date":"2026-09-10","time":"07:00","account":"pet_youtube","video_path":"affiliate-engine/assets/video/a.mp4",
 *    "video_url":"","title":"...","description":"...","template_id":"pet_012"}
 *
 * 環境変数:
 *   CATCHUP_HOURS            何時間前までの未投稿分を拾うか（既定 6）
 *   VIDEO_POST_LIVE_CONFIRM  I_UNDERSTAND_THE_RISK で実投稿を許可（live_enabled と両方必要）
 *   JITTER=0                 投稿間隔の分散を切る
 *   VIDEO_QUEUE / VIDEO_JUDGE_OUT / VIDEO_STATE  パス上書き（テスト用）
 *   GH_SECRETS_PAT           トークン回転時の Secrets 自動書き戻し（任意）
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { checkContent, DISCLOSURE_PATTERN } = require('./compliance');
const { PROFILE_CTA, applyProfileCta } = require('./youtube-cta');
const { OUTPUT_DIR, readJSON, writeJSON, loadConfig, todayJST, scheduleEpoch } = require('./util');
const { getAdapter } = require('./video-platforms');
const { resolveVideoPath, sleep } = require('./video-platforms/common');
const { updateSecret } = require('./refresh-tokens');

const CATCHUP_HOURS = parseFloat(process.env.CATCHUP_HOURS || '6');
const LIVE_CONFIRM = 'I_UNDERSTAND_THE_RISK';
const JUDGE_MAX_AGE_DAYS = 2;
const RECENT_DEFAULT_DAYS = 30;

const QUEUE_PATH = process.env.VIDEO_QUEUE || path.join(OUTPUT_DIR, 'video_queue.jsonl');
const STATE_PATH = process.env.VIDEO_STATE || path.join(OUTPUT_DIR, 'state', 'video_posted.json');
const JUDGE_LATEST = path.join(process.env.VIDEO_JUDGE_OUT || path.join(OUTPUT_DIR, 'video'), 'latest.json');

const argv = process.argv.slice(2);
const isDryRunFlag = argv.includes('--dry-run');

function argValue(name) {
  const i = argv.indexOf(name);
  return i !== -1 ? argv[i + 1] : undefined;
}

// ---------------------------------------------------------------------------
// 純粋関数（self-test 対象）
// ---------------------------------------------------------------------------

function itemKey(item) {
  return item.id || `${item.date}_${item.time}_${item.account}`;
}

function contentHash(item) {
  const src = `${item.video_path || ''}|${item.video_url || ''}|${item.description || ''}`;
  return crypto.createHash('sha1').update(src).digest('hex').slice(0, 16);
}

function parseQueue(text) {
  const items = [];
  const errors = [];
  String(text || '')
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean)
    .forEach((line, idx) => {
      try {
        const item = JSON.parse(line);
        if (!item.date || !item.time || !item.account) {
          errors.push(`line ${idx + 1}: date / time / account が必要`);
          return;
        }
        items.push(item);
      } catch (err) {
        errors.push(`line ${idx + 1}: ${err.message}`);
      }
    });
  return { items, errors };
}

function dueItems(items, state, now, catchupHours = CATCHUP_HOURS) {
  const windowStart = now - catchupHours * 3600 * 1000;
  return items.filter((item) => {
    const t = scheduleEpoch(item.date, item.time);
    return t <= now && t >= windowStart && !state.posted[itemKey(item)];
  });
}

/**
 * video-judge の latest.json からゲートを読む。
 * 無い・古い・旧形式は全部「閉」。投稿側で判定を発明しない。
 */
function evaluateGate(latest, today, maxAgeDays = JUDGE_MAX_AGE_DAYS) {
  if (!latest || !latest.summary || !latest.summary.today) {
    return { allowed: false, weekly_cap: 0, platforms: [], reason: 'judge_missing: video-judge.js を先に回す' };
  }
  const judgeDay = latest.summary.today;
  if (judgeDay < shiftDate(today, -maxAgeDays)) {
    return { allowed: false, weekly_cap: 0, platforms: [], reason: `judge_stale: 判定が ${judgeDay} で止まっている` };
  }
  if (!latest.posting) {
    return { allowed: false, weekly_cap: 0, platforms: [], reason: 'judge_no_gate: 旧形式の判定。video-judge.js を更新して回す' };
  }
  const p = latest.posting;
  return {
    allowed: Boolean(p.allowed),
    weekly_cap: Number(p.weekly_cap) || 0,
    platforms: Array.isArray(p.platforms) ? p.platforms : [],
    reason: p.reason || '',
    verdict: latest.verdict && latest.verdict.code
  };
}

function shiftDate(yyyyMmDd, days) {
  const [y, m, d] = yyyyMmDd.split('-').map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  dt.setUTCDate(dt.getUTCDate() + days);
  return dt.toISOString().slice(0, 10);
}

/** 直近 days 日の成功投稿数（アカウント別） */
function countRecentSuccess(state, account, today, days) {
  const cutoff = shiftDate(today, -(days - 1));
  let n = 0;
  for (const entry of Object.values(state.posted || {})) {
    if (entry.status !== 'success' || entry.account !== account) continue;
    if ((entry.date || '') >= cutoff) n++;
  }
  return n;
}

function countHashtags(text) {
  return (String(text || '').match(/(^|\s)#[^\s#]+/g) || []).length;
}

/**
 * 媒体別のキャプションを組み立てる。全媒体共通のルール:
 * - {{AFFILIATE_LINK}} は消し、プロフィールCTAを1回だけ足す
 * - #PR を必ず含める（アフィ導線がプロフィールにあるため）
 * - URL は置かない（Shorts / Reels / TikTok いずれもクリック不可。スパム判定の元）
 * - 長さ・ハッシュタグ数は媒体上限内
 */
function buildCaption(item, adapter) {
  const reasons = [];
  let body = applyProfileCta(item.description || '');
  if (!DISCLOSURE_PATTERN.test(body)) {
    body = `${body}\n#PR`;
    reasons.push('#PR を自動付与');
  }
  if (/https?:\/\//.test(body)) {
    return { ok: false, reasons: ['本文に URL がある。押せる場所はプロフィールだけ'] };
  }
  if (/\{\{.+?\}\}/.test(body)) {
    return { ok: false, reasons: ['未解決プレースホルダーが残っている'] };
  }
  const { titleMax, captionMax, hashtagMax } = adapter.LIMITS;
  if (body.length > captionMax) {
    return { ok: false, reasons: [`本文 ${body.length} 字（${adapter.platform} 上限 ${captionMax}）`] };
  }
  if (hashtagMax && countHashtags(body) > hashtagMax) {
    return { ok: false, reasons: [`ハッシュタグ ${countHashtags(body)} 個（${adapter.platform} 上限 ${hashtagMax}）`] };
  }

  let title = '';
  if (titleMax > 0) {
    const raw = String(item.title || body.split('\n').find((l) => l.trim() && !/^#/.test(l.trim())) || '').trim();
    title = raw.replace(/https?:\/\/\S+/g, '').trim();
    if (!title) return { ok: false, reasons: ['タイトルが空'] };
    if (title.length > titleMax) {
      title = title.slice(0, titleMax - 1).trimEnd() + '…';
      reasons.push(`タイトルを ${titleMax} 字に切った`);
    }
  }

  const compliance = checkContent(body);
  if (!compliance.ok) return { ok: false, reasons: compliance.reasons };
  const titleCheck = title ? checkContent(title) : { ok: true, reasons: [] };
  if (!titleCheck.ok) return { ok: false, reasons: titleCheck.reasons.map((r) => `タイトル: ${r}`) };

  return { ok: true, title, body: compliance.text, reasons };
}

/** ライブ判定。片方だけではドライラン */
function resolveMode(config, envConfirm, dryRunFlag) {
  if (dryRunFlag) return { live: false, why: '--dry-run' };
  const gates = [];
  if (config.live_enabled !== true) gates.push('config/video_accounts.json の live_enabled が true でない');
  if (envConfirm !== LIVE_CONFIRM) gates.push(`環境変数 VIDEO_POST_LIVE_CONFIRM が ${LIVE_CONFIRM} でない`);
  if (gates.length) return { live: false, why: gates.join(' / ') };
  return { live: true, why: 'live_enabled + VIDEO_POST_LIVE_CONFIRM' };
}

// ---------------------------------------------------------------------------
// I/O
// ---------------------------------------------------------------------------

function loadAccounts(config) {
  const defaults = config.defaults || {};
  return Object.fromEntries(
    (config.accounts || [])
      .filter((a) => a.enabled !== false)
      .map((a) => [
        a.key,
        {
          ...a,
          platform: String(a.platform || '').toLowerCase(),
          daily_cap: a.daily_cap ?? defaults.daily_cap ?? 1,
          privacy: a.privacy || defaults.privacy || 'public'
        }
      ])
  );
}

function logPosting(entry) {
  const logDir = path.join(OUTPUT_DIR, 'posting_logs');
  fs.mkdirSync(logDir, { recursive: true });
  fs.appendFileSync(path.join(logDir, `video_posting_${todayJST()}.jsonl`), JSON.stringify(entry) + '\n', 'utf-8');
}

function applySecretUpdates(updates, label) {
  const results = [];
  for (const u of updates || []) {
    if (!u.env || !u.value) continue;
    const r = updateSecret(u.env, u.value);
    if (r.ok) console.log(`   🔐 ${label}: ${u.env} を Secrets に書き戻した`);
    else console.log(`   ⚠️ ${label}: ${u.env} の書き戻し不可（${r.reason}）。Step Summary か video-oauth.js で手動更新`);
    results.push({ ...u, ok: r.ok, reason: r.reason });
  }
  return results;
}

// ---------------------------------------------------------------------------
// 投稿本体
// ---------------------------------------------------------------------------

async function runPost() {
  const config = loadConfig('video_accounts', { accounts: [] }) || { accounts: [] };
  const mode = resolveMode(config, process.env.VIDEO_POST_LIVE_CONFIRM, isDryRunFlag);
  const live = mode.live;
  console.log(`🎬 Video Poster ${live ? '' : '（ドライラン: ' + mode.why + '）'}\n`);

  if (!fs.existsSync(QUEUE_PATH)) {
    console.log(`📭 キューがありません: ${QUEUE_PATH}`);
    console.log('   node src/video-poster.js --enqueue ... で追加してください');
    return;
  }

  const accounts = loadAccounts(config);
  const { items, errors } = parseQueue(fs.readFileSync(QUEUE_PATH, 'utf-8'));
  for (const e of errors) console.log(`⚠️ キュー行を無視: ${e}`);
  const state = readJSON(STATE_PATH, { posted: {}, recent: {} });
  state.posted = state.posted || {};
  state.recent = state.recent || {};

  const today = todayJST();
  const now = Date.now();
  const gate = evaluateGate(readJSON(JUDGE_LATEST, null), today);
  console.log(
    `🚦 判定ゲート: ${gate.allowed ? `開（週${gate.weekly_cap}本 / ${gate.platforms.join(',')}）` : '閉'} — ${gate.reason}${gate.verdict ? ` [${gate.verdict}]` : ''}`
  );

  const due = dueItems(items, state, now);
  console.log(`📋 キュー ${items.length} 件中、期日到来 ${due.length} 件\n`);

  const useJitter = live && process.env.JITTER !== '0';
  if (useJitter && due.length > 1) {
    for (let i = due.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [due[i], due[j]] = [due[j], due[i]];
    }
  }
  if (useJitter && due.length > 0) {
    const initialDelay = Math.floor(15000 + Math.random() * 120000);
    console.log(`⏲  開始ディレイ ${Math.round(initialDelay / 1000)} 秒\n`);
    await sleep(initialDelay);
  }

  const postedToday = {};
  for (const entry of Object.values(state.posted)) {
    if (entry.status === 'success' && entry.date === today) {
      postedToday[entry.account] = (postedToday[entry.account] || 0) + 1;
    }
  }

  let success = 0;
  let failed = 0;
  let skipped = 0;
  const mark = (key, status, extra = {}) => {
    if (live) state.posted[key] = { status, at: new Date().toISOString(), ...extra };
  };

  for (const item of due) {
    const key = itemKey(item);
    const account = accounts[item.account];
    const label = `${item.date} ${item.time} @${item.account}`;

    if (!account) {
      console.log(`⏭  ${label}: アカウント未定義（または enabled=false）のためスキップ`);
      skipped++;
      continue;
    }
    const adapter = getAdapter(account.platform);
    if (!adapter) {
      console.log(`⏭  ${label}: 未対応 platform "${account.platform}"`);
      skipped++;
      continue;
    }

    if (!gate.allowed) {
      console.log(`⏭  ${label}: 判定ゲート閉のためスキップ（${gate.reason}）`);
      mark(key, 'skipped_judge', { account: item.account, date: item.date, reason: gate.reason });
      skipped++;
      continue;
    }
    if (!gate.platforms.includes(account.platform)) {
      console.log(`⏭  ${label}: ${account.platform} はゲート対象外（platform_unlock か実験中）`);
      mark(key, 'skipped_platform_gate', { account: item.account, date: item.date, platform: account.platform });
      skipped++;
      continue;
    }
    const weekly = countRecentSuccess(state, item.account, today, 7);
    if (weekly >= gate.weekly_cap) {
      console.log(`⏭  ${label}: 週次上限 ${gate.weekly_cap} 本に到達（直近7日 ${weekly}）`);
      skipped++;
      continue;
    }
    if ((postedToday[item.account] || 0) >= account.daily_cap) {
      console.log(`⏭  ${label}: デイリー上限 ${account.daily_cap} 本に到達`);
      skipped++;
      continue;
    }

    // 重複ガード: 同じ動画/本文を同一アカウントに30日以内に出さない
    const hash = contentHash(item);
    const recentDays = (config.defaults && config.defaults.duplicate_window_days) || RECENT_DEFAULT_DAYS;
    const recentCutoff = todayJST(-recentDays);
    const accountRecent = (state.recent[item.account] = state.recent[item.account] || {});
    for (const [h, d] of Object.entries(accountRecent)) {
      if (d < recentCutoff) delete accountRecent[h];
    }
    if (accountRecent[hash]) {
      console.log(`⏭  ${label}: ${recentDays}日以内に同一動画/本文を投稿済みのためスキップ`);
      mark(key, 'skipped_duplicate', { account: item.account, date: item.date });
      skipped++;
      continue;
    }

    const caption = buildCaption(item, adapter);
    if (!caption.ok) {
      console.log(`🚫 ${label}: ブロック（${caption.reasons.join(', ')}）`);
      mark(key, 'blocked', { account: item.account, date: item.date, reasons: caption.reasons });
      if (live) logPosting({ key, status: 'blocked', reasons: caption.reasons });
      skipped++;
      continue;
    }

    const localPath = resolveVideoPath(item.video_path);
    const hasLocal = localPath && fs.existsSync(localPath);
    if (!hasLocal && !item.video_url) {
      console.log(`⏭  ${label}: 動画が無い（${item.video_path || 'video_path 未指定'} / video_url 未指定）`);
      skipped++;
      continue;
    }

    if (!live) {
      console.log(`📝 ${label} → ${account.platform}${account.handle ? ` ${account.handle}` : ''}`);
      if (caption.title) console.log(`   ┃ title: ${caption.title}`);
      console.log(caption.body.split('\n').map((l) => `   │ ${l}`).join('\n'));
      console.log(`   ┃ video: ${hasLocal ? localPath : item.video_url}`);
      if (caption.reasons.length) console.log(`   ┃ note: ${caption.reasons.join(', ')}`);
      console.log('');
      continue;
    }

    const { values: creds, missing } = adapter.credentials(account);
    if (missing.length) {
      console.log(`⏭  ${label}: Secrets 未設定 ${missing.join(', ')}`);
      skipped++;
      continue;
    }

    try {
      const result = await adapter.publish(account, creds, item, caption, (msg) => console.log(`   ℹ️ ${msg}`));
      console.log(`✅ ${label}: ${account.platform} 投稿成功 (${result.id})${result.url ? ` ${result.url}` : ''}`);
      accountRecent[hash] = item.date;
      state.posted[key] = {
        status: 'success',
        platform: account.platform,
        account: item.account,
        date: item.date,
        post_id: result.id,
        url: result.url || null,
        template_id: item.template_id || null,
        at: new Date().toISOString()
      };
      logPosting({ key, status: 'success', platform: account.platform, account: item.account, post_id: result.id, url: result.url || null });
      postedToday[item.account] = (postedToday[item.account] || 0) + 1;
      success++;
      if (result.rotated_refresh_token && account.refresh_token_env) {
        applySecretUpdates([{ env: account.refresh_token_env, value: result.rotated_refresh_token }], item.account);
      }
      await sleep(useJitter ? Math.floor(60000 + Math.random() * 120000) : 3000);
    } catch (err) {
      console.log(`❌ ${label}: ${err.message}`);
      state.posted[key] = {
        status: err.code === 'no_public_url' ? 'skipped_no_public_url' : 'failed',
        platform: account.platform,
        account: item.account,
        date: item.date,
        error: err.message,
        at: new Date().toISOString()
      };
      logPosting({ key, status: 'failed', platform: account.platform, account: item.account, error: err.message });
      failed++;
    }
  }

  if (live) {
    writeJSON(STATE_PATH, state);
    console.log(`\n📊 結果: 成功 ${success} / 失敗 ${failed} / スキップ ${skipped}`);
    console.log(`   状態ファイル: ${STATE_PATH}`);
  } else {
    console.log(`（ドライラン: ${due.length} 件が期日到来。実投稿・状態更新は行っていません）`);
  }
}

// ---------------------------------------------------------------------------
// --refresh-tokens
// ---------------------------------------------------------------------------

async function runRefreshTokens() {
  console.log('🔄 動画アカウントのトークン延命\n');
  const config = loadConfig('video_accounts', { accounts: [] }) || { accounts: [] };
  const accounts = loadAccounts(config);
  const summary = [];
  for (const account of Object.values(accounts)) {
    const adapter = getAdapter(account.platform);
    if (!adapter || typeof adapter.refreshTokens !== 'function') {
      console.log(`⏭  ${account.key}: ${account.platform} は延命不要（refresh_token は失効しない）`);
      continue;
    }
    const { values: creds, missing } = adapter.credentials(account);
    if (missing.length) {
      console.log(`⏭  ${account.key}: Secrets 未設定 ${missing.join(', ')}`);
      continue;
    }
    try {
      const r = await adapter.refreshTokens(account, creds);
      console.log(`✅ ${account.key}: ${r.note}`);
      const written = applySecretUpdates(r.updates, account.key);
      summary.push({ key: account.key, ok: true, note: r.note, written });
    } catch (err) {
      console.log(`❌ ${account.key}: ${err.message}`);
      summary.push({ key: account.key, ok: false, error: err.message });
    }
  }

  const stepSummary = process.env.GITHUB_STEP_SUMMARY;
  if (stepSummary) {
    const lines = ['## 動画アカウント トークン延命', ''];
    for (const s of summary) {
      if (!s.ok) {
        lines.push(`- ❌ ${s.key}: ${s.error}`);
        continue;
      }
      lines.push(`- ✅ ${s.key}: ${s.note}`);
      // 自動書き戻しできなかった分だけ Summary で人間に渡す（Threads の refresh-tokens.js と同じ運用）
      for (const u of (s.written || []).filter((w) => !w.ok)) {
        lines.push(`  - ⚠️ \`${u.env}\` を手動更新（自動書き戻し不可: ${u.reason}）:`);
        lines.push('    ```');
        lines.push(`    ${u.value}`);
        lines.push('    ```');
      }
    }
    fs.appendFileSync(stepSummary, lines.join('\n') + '\n', 'utf-8');
  }
}

// ---------------------------------------------------------------------------
// --enqueue
// ---------------------------------------------------------------------------

function runEnqueue() {
  const config = loadConfig('video_accounts', { accounts: [] }) || { accounts: [] };
  const accounts = loadAccounts(config);
  const accountKey = argValue('--account');
  const video = argValue('--video');
  const account = accounts[accountKey];
  if (!account) {
    console.error(`❌ --account が不正: ${accountKey}（有効: ${Object.keys(accounts).join(', ') || 'なし'}）`);
    process.exit(1);
  }
  if (!video) {
    console.error('❌ --video <path|https URL> が必要');
    process.exit(1);
  }
  const nowJst = new Date(Date.now() + 9 * 3600 * 1000);
  const item = {
    date: argValue('--date') || todayJST(),
    time: argValue('--time') || nowJst.toISOString().slice(11, 16),
    account: accountKey,
    video_path: /^https?:\/\//.test(video) ? '' : video,
    video_url: /^https?:\/\//.test(video) ? video : '',
    title: argValue('--title') || '',
    description: (argValue('--desc') || '').replace(/\\n/g, '\n'),
    template_id: argValue('--template-id') || null
  };
  const adapter = getAdapter(account.platform);
  const caption = buildCaption(item, adapter);
  if (!caption.ok) {
    console.error(`❌ 検品で落ちた: ${caption.reasons.join(', ')}`);
    process.exit(1);
  }
  // 同じ 日付_時刻_アカウント が既にあれば id を分けて state キーの衝突を避ける
  const existing = fs.existsSync(QUEUE_PATH) ? parseQueue(fs.readFileSync(QUEUE_PATH, 'utf-8')).items : [];
  const usedKeys = new Set(existing.map(itemKey));
  const baseKey = itemKey(item);
  if (usedKeys.has(baseKey)) {
    let n = 2;
    while (usedKeys.has(`${baseKey}_${n}`)) n++;
    item.id = `${baseKey}_${n}`;
  }
  fs.mkdirSync(path.dirname(QUEUE_PATH), { recursive: true });
  fs.appendFileSync(QUEUE_PATH, JSON.stringify(item) + '\n', 'utf-8');
  console.log(`✅ キューに追加: ${itemKey(item)} → ${QUEUE_PATH}`);
  if (caption.title) console.log(`   title: ${caption.title}`);
  console.log(caption.body.split('\n').map((l) => `   │ ${l}`).join('\n'));
  if (caption.reasons.length) console.log(`   note: ${caption.reasons.join(', ')}`);
}

// ---------------------------------------------------------------------------
// --self-test
// ---------------------------------------------------------------------------

function assertEqual(actual, expected, label) {
  if (actual !== expected) throw new Error(`${label}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
}

function runSelfTest() {
  const yt = getAdapter('youtube');
  const tt = getAdapter('tiktok');
  const ig = getAdapter('instagram');

  // caption: CTA + #PR、URL 拒否、タイトル切り詰め
  const base = { description: '猫が夜中に走る理由\n3つの説がある {{AFFILIATE_LINK}}' };
  const c1 = buildCaption(base, yt);
  assertEqual(c1.ok, true, 'basic caption ok');
  if (!c1.body.includes(PROFILE_CTA)) throw new Error('profile CTA missing');
  if (!/#PR/.test(c1.body)) throw new Error('#PR missing');
  if (/\{\{/.test(c1.body)) throw new Error('placeholder leaked');
  assertEqual(c1.title, '猫が夜中に走る理由', 'title from first line');

  const c2 = buildCaption({ description: 'ここから買える https://example.com/a #PR' }, yt);
  assertEqual(c2.ok, false, 'url rejected');

  const c3 = buildCaption({ title: 'あ'.repeat(120), description: '本文' }, yt);
  assertEqual(c3.ok, true, 'long title ok');
  assertEqual(c3.title.length, yt.LIMITS.titleMax, 'title cut to 100');

  const c4 = buildCaption({ description: '誰でも簡単に月30万 稼げる話' }, tt);
  assertEqual(c4.ok, false, 'compliance block on caption');

  const c5 = buildCaption({ description: '本文 ' + Array.from({ length: 31 }, (_, i) => `#t${i}`).join(' ') }, ig);
  assertEqual(c5.ok, false, 'hashtag cap on instagram');
  assertEqual(buildCaption({ description: '本文だけ' }, ig).title, '', 'instagram has no title');
  assertEqual(buildCaption({ description: '本文だけ' }, tt).title, '本文だけ', 'tiktok title from body');

  // mode
  assertEqual(resolveMode({ live_enabled: true }, LIVE_CONFIRM, false).live, true, 'live when both gates');
  assertEqual(resolveMode({ live_enabled: true }, '', false).live, false, 'no env confirm → dry');
  assertEqual(resolveMode({ live_enabled: false }, LIVE_CONFIRM, false).live, false, 'config off → dry');
  assertEqual(resolveMode({ live_enabled: true }, LIVE_CONFIRM, true).live, false, '--dry-run wins');

  // gate
  const today = '2026-09-10';
  assertEqual(evaluateGate(null, today).allowed, false, 'missing judge closes');
  assertEqual(
    evaluateGate({ summary: { today: '2026-09-01' }, posting: { allowed: true, weekly_cap: 3, platforms: ['youtube'] } }, today).allowed,
    false,
    'stale judge closes'
  );
  assertEqual(evaluateGate({ summary: { today }, verdict: { code: 'FUNNEL_ALIVE' } }, today).allowed, false, 'old format closes');
  const open = evaluateGate({ summary: { today }, posting: { allowed: true, weekly_cap: 3, platforms: ['youtube'], reason: 'x' } }, today);
  assertEqual(open.allowed, true, 'fresh open gate');
  assertEqual(open.weekly_cap, 3, 'cap passthrough');
  const yesterday = evaluateGate(
    { summary: { today: shiftDate(today, -1) }, posting: { allowed: true, weekly_cap: 1, platforms: ['tiktok'] } },
    today
  );
  assertEqual(yesterday.allowed, true, 'yesterday judge still fresh');

  // due / state
  const state = {
    posted: {
      a: { status: 'success', account: 'pet_youtube', date: shiftDate(today, -2) },
      b: { status: 'success', account: 'pet_youtube', date: shiftDate(today, -8) },
      c: { status: 'failed', account: 'pet_youtube', date: today },
      d: { status: 'success', account: 'pet_tiktok', date: today },
      '2026-09-10_07:00_pet_youtube': { status: 'success', account: 'pet_youtube', date: today }
    },
    recent: {}
  };
  assertEqual(countRecentSuccess(state, 'pet_youtube', today, 7), 2, 'weekly count ignores old/failed/other');
  const now = scheduleEpoch(today, '09:00');
  const items = [
    { date: today, time: '07:00', account: 'pet_youtube' },
    { date: today, time: '08:00', account: 'pet_youtube' },
    { date: today, time: '10:00', account: 'pet_youtube' },
    { date: shiftDate(today, -1), time: '08:00', account: 'pet_youtube' }
  ];
  const due = dueItems(items, state, now, 6);
  assertEqual(due.length, 1, 'only unposted, due, in-window items');
  assertEqual(due[0].time, '08:00', 'due item');

  const q = parseQueue('{"date":"2026-09-10","time":"07:00","account":"a"}\nnot json\n{"date":"x"}\n');
  assertEqual(q.items.length, 1, 'queue parse keeps valid');
  assertEqual(q.errors.length, 2, 'queue parse reports invalid');

  assertEqual(contentHash({ video_path: 'a.mp4', description: 'x' }), contentHash({ video_path: 'a.mp4', description: 'x', title: 'y' }), 'hash ignores title');
  if (contentHash({ video_path: 'a.mp4' }) === contentHash({ video_path: 'b.mp4' })) throw new Error('hash must differ by video');

  // tiktok helpers
  assertEqual(tt.chooseChunking(3 * 1024 * 1024).total_chunk_count, 1, 'small file single chunk');
  assertEqual(tt.chooseChunking(60 * 1024 * 1024).total_chunk_count, 1, '60MB single chunk');
  const big = tt.chooseChunking(105 * 1024 * 1024);
  assertEqual(big.total_chunk_count, 10, '105MB → 10 chunks of 10MB, last absorbs 5MB');
  assertEqual(tt.resolvePrivacy({ privacy: 'public' }, { privacy_level_options: ['SELF_ONLY'] }), 'SELF_ONLY', 'unaudited app falls back to SELF_ONLY');
  assertEqual(
    tt.resolvePrivacy({ privacy: 'public' }, { privacy_level_options: ['PUBLIC_TO_EVERYONE', 'SELF_ONLY'] }),
    'PUBLIC_TO_EVERYONE',
    'public when allowed'
  );

  console.log('self-test ok');
}

// ---------------------------------------------------------------------------

module.exports = {
  itemKey,
  contentHash,
  parseQueue,
  dueItems,
  evaluateGate,
  countRecentSuccess,
  buildCaption,
  resolveMode,
  LIVE_CONFIRM
};

if (require.main === module) {
  let task;
  if (argv.includes('--self-test')) {
    try {
      runSelfTest();
    } catch (err) {
      console.error(`self-test failed: ${err.message}`);
      process.exit(1);
    }
  } else if (argv.includes('--refresh-tokens')) {
    task = runRefreshTokens();
  } else if (argv.includes('--enqueue')) {
    runEnqueue();
  } else {
    task = runPost();
  }
  if (task) {
    task.catch((err) => {
      console.error('\n🔴 致命的エラー:', err.message);
      process.exit(1);
    });
  }
}
