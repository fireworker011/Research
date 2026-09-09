#!/usr/bin/env node
'use strict';

/**
 * アフィ動画の定期判定。改善とは「ゲートを見て、やってはいけないことを止める」こと。
 *
 * やること:
 * - video_cash_log.csv だけを見て、再生→クリック→成果を切り分ける
 * - スマホで読める判定を output/video/ と（任意で）GitHub Issue に書く
 * - 実験中は次の癒し3本を再掲する
 * - video-poster.js が読む自動投稿ゲート（posting）を latest.json に書く。
 *   ゲートが閉じている日は poster は何も投稿しない
 *
 * やらないこと:
 * - 投稿（投稿は video-poster.js。判定は投稿を許可するだけで実行しない）
 * - 数字の発明
 * - insight.js / Claude でのジャンル転換
 * - 媒体の追加判断（TikTok / Instagram は config/video_accounts.json の
 *   platform_unlock に人間が日付を書いたものだけをゲートに載せる）
 *
 * CSV の platform 列は任意。空なら youtube。tiktok / instagram は別行で記録する。
 *
 *   node src/video-judge.js
 *   node src/video-judge.js --self-test
 *   VIDEO_JUDGE_TODAY=2026-08-30 node src/video-judge.js
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { ROOT, OUTPUT_DIR, parseCSV, todayJST, loadConfig } = require('./util');
const { PROFILE_CTA } = require('./youtube-cta');

const GATES = {
  experimentStart: '2026-08-22',
  experimentDays: 14,
  weeklyClickMin: 15,
  weeklyClick1M: 50,
  weeklyClick1MStreak: 3,
  cumulativeOfferJudge: 50,
  weeklyVideoCap: 3
};

const PLATFORMS = ['youtube', 'tiktok', 'instagram'];
const DEFAULT_PLATFORM = 'youtube';
// 実験（14日）の間は YouTube だけ。他媒体は実験後にゲートが開いてから
const EXPERIMENT_PLATFORMS = ['youtube'];

const LOG_PATH = process.env.VIDEO_CASH_LOG || path.join(ROOT, 'data', 'video_cash_log.csv');
const OUT_DIR = process.env.VIDEO_JUDGE_OUT || path.join(OUTPUT_DIR, 'video');
const TRACKING_ISSUE_TITLE = '動画キャッシュループ — 今日の判定';
const FORBIDDEN = [
  'video-poster.js 以外で投稿を自動化するな。ゲートが閉じた日は poster も投稿しない',
  'TikTok / Instagram は platform_unlock に人間が日付を書くまで足すな。同時に2媒体を開けるな',
  'ジャンル転換するな。参考チャンネルの動画をコピーするな',
  'insight.js を動画に使うな',
  'Shorts / Reels / TikTok の説明欄・コメントにアフィURLを置くな。押せる場所はプロフィール',
  '既存32本を編集するな',
  '数字が無いのに量産するな'
];

function addDays(yyyyMmDd, n) {
  const [y, m, d] = yyyyMmDd.split('-').map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  dt.setUTCDate(dt.getUTCDate() + n);
  return dt.toISOString().slice(0, 10);
}

function daysBetween(start, end) {
  const [sy, sm, sd] = start.split('-').map(Number);
  const [ey, em, ed] = end.split('-').map(Number);
  return Math.round((Date.UTC(ey, em - 1, ed) - Date.UTC(sy, sm - 1, sd)) / 86400000);
}

function toInt(value) {
  const n = Number.parseInt(String(value ?? '').trim(), 10);
  return Number.isFinite(n) ? n : 0;
}

function isLiveRow(row) {
  if (!row || !/^\d{4}-\d{2}-\d{2}$/.test(row.date || '')) return false;
  if (/\bexample\b/i.test(row.note || '')) return false;
  return true;
}

function normalizePlatform(value) {
  const p = String(value ?? '').trim().toLowerCase();
  return PLATFORMS.includes(p) ? p : DEFAULT_PLATFORM;
}

function normalizeRow(row) {
  return {
    date: row.date,
    platform: normalizePlatform(row.platform),
    videos_published: toInt(row.videos_published),
    views: toInt(row.views),
    a8_clicks: toInt(row.a8_clicks),
    conversions: toInt(row.conversions),
    note: String(row.note || '').trim()
  };
}

function parseLog(text) {
  return parseCSV(text || '')
    .filter(isLiveRow)
    .map(normalizeRow);
}

function sumField(rows, field) {
  return rows.reduce((acc, row) => acc + (row[field] || 0), 0);
}

function inRange(rows, start, end) {
  return rows.filter((row) => row.date >= start && row.date <= end);
}

function summarize(rows, today) {
  const live = rows.filter((row) => row.date <= today);
  const last7 = inRange(live, addDays(today, -6), today);
  const prev7 = inRange(live, addDays(today, -13), addDays(today, -7));
  const experimentRows = inRange(live, GATES.experimentStart, today);
  const weekClicks = [];
  for (let i = 0; i < GATES.weeklyClick1MStreak; i++) {
    const end = addDays(today, -7 * i);
    const start = addDays(end, -6);
    weekClicks.push({ start, end, clicks: sumField(inRange(live, start, end), 'a8_clicks') });
  }

  const byPlatform = {};
  for (const platform of PLATFORMS) {
    const rows7 = last7.filter((row) => row.platform === platform);
    const rowsAll = live.filter((row) => row.platform === platform);
    if (rowsAll.length === 0) continue;
    byPlatform[platform] = {
      rows: rowsAll.length,
      last7: {
        videos: sumField(rows7, 'videos_published'),
        views: sumField(rows7, 'views'),
        clicks: sumField(rows7, 'a8_clicks'),
        conversions: sumField(rows7, 'conversions')
      },
      cumulative: {
        videos: sumField(rowsAll, 'videos_published'),
        views: sumField(rowsAll, 'views'),
        clicks: sumField(rowsAll, 'a8_clicks'),
        conversions: sumField(rowsAll, 'conversions')
      }
    };
  }

  return {
    today,
    rowCount: live.length,
    lastDate: live.length ? live[live.length - 1].date : null,
    byPlatform,
    last7: {
      start: addDays(today, -6),
      end: today,
      videos: sumField(last7, 'videos_published'),
      views: sumField(last7, 'views'),
      clicks: sumField(last7, 'a8_clicks'),
      conversions: sumField(last7, 'conversions')
    },
    prev7Clicks: sumField(prev7, 'a8_clicks'),
    cumulative: {
      videos: sumField(live, 'videos_published'),
      views: sumField(live, 'views'),
      clicks: sumField(live, 'a8_clicks'),
      conversions: sumField(live, 'conversions')
    },
    experiment: {
      start: GATES.experimentStart,
      day: daysBetween(GATES.experimentStart, today) + 1,
      videos: sumField(experimentRows, 'videos_published'),
      clicks: sumField(experimentRows, 'a8_clicks'),
      conversions: sumField(experimentRows, 'conversions')
    },
    weekClicks
  };
}

function decide(summary) {
  const inExperiment =
    summary.experiment.day >= 1 && summary.experiment.day <= GATES.experimentDays;
  const canTalk1M = summary.weekClicks.every((w) => w.clicks >= GATES.weeklyClick1M);

  if (summary.rowCount === 0) {
    return {
      code: 'RECORD_MISSING',
      title: '記録が無い。改善できない',
      improve: 'CSVに数字を書け。記録が無い改善は妄想',
      action: inExperiment
        ? `A8とYouTubeスタジオの数字をCSVに1行書け。未投稿なら癒し3本。末尾は「${PROFILE_CTA}」。URLは置かない`
        : 'A8とYouTubeスタジオを見て、affiliate-engine/data/video_cash_log.csv に1行追記する',
      includeNext3: inExperiment,
      canTalk1M: false,
      inExperiment
    };
  }

  if (inExperiment) {
    const posted = summary.experiment.videos;
    const remain = Math.max(0, GATES.weeklyVideoCap - posted);
    return {
      code: 'CONTINUE_EXPERIMENT',
      title: `実験 ${summary.experiment.day}/${GATES.experimentDays}日目。型は変えない`,
      improve: 'なし。実験中に型を変えないことが改善',
      action:
        remain > 0
          ? `癒しShortsを残り${remain}本出す。末尾は「${PROFILE_CTA}」。URLは置かない`
          : '3本は出した。触るな。今日のクリックと成果だけCSVに書け',
      includeNext3: remain > 0,
      canTalk1M,
      inExperiment
    };
  }

  if (summary.cumulative.conversions >= 1) {
    return {
      code: 'OFFER_ALIVE',
      title: '案件は生きている',
      improve: '成果が付いた型だけ複製する。媒体は足さない',
      action: '成果が付いた動画の型だけ、週3本まで。新しいジャンルは開かない',
      includeNext3: false,
      canTalk1M,
      inExperiment
    };
  }

  if (
    summary.last7.clicks >= GATES.weeklyClickMin &&
    summary.cumulative.clicks >= GATES.cumulativeOfferJudge
  ) {
    return {
      code: 'SUSPECT_OFFER',
      title: '導線は動いたが、案件か着地を疑う',
      improve: '同じカメラ動画を増やすな。安い/申込型を1本だけ人間が選ぶ',
      action: 'カメラ以外を1本だけ試す。量産禁止。人間が案件を選ぶ',
      includeNext3: false,
      canTalk1M,
      inExperiment
    };
  }

  if (summary.last7.clicks >= GATES.weeklyClickMin) {
    return {
      code: 'FUNNEL_ALIVE',
      title: '導線は生きている',
      improve: '同じ癒し型を週3本まで。媒体は足さない',
      action: `同じ型で週${GATES.weeklyVideoCap}本まで出す。末尾は「${PROFILE_CTA}」`,
      includeNext3: true,
      canTalk1M,
      inExperiment
    };
  }

  return {
    code: 'FUNNEL_WEAK',
    title: '導線では足りない',
    improve: '量産禁止。案件を安い/申込型にするか、長尺1本で比較する。どちらも人間が決める',
    action: '量産するな。ジャンル転換するな。次の一手は人間が1つだけ選ぶ',
    includeNext3: false,
    canTalk1M,
    inExperiment
  };
}

/** platform_unlock（人間が書いた日付）のうち、today 時点で有効な媒体 */
function unlockedPlatforms(unlock, today) {
  const out = [];
  for (const platform of PLATFORMS) {
    const date = unlock && unlock[platform];
    if (typeof date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(date) && date <= today) {
      out.push(platform);
    }
  }
  return out;
}

/**
 * video-poster.js が読む自動投稿ゲート。
 * 判定コードから「今日は投稿してよいか・週何本まで・どの媒体か」だけを機械可読で出す。
 * 媒体は人間の platform_unlock と判定の積集合。判定が閉じていれば全媒体が閉じる。
 */
function postingGate(summary, verdict, unlock) {
  const unlocked = unlockedPlatforms(unlock, summary.today);
  const closed = (reason) => ({ allowed: false, weekly_cap: 0, platforms: [], reason });

  let cap = 0;
  let platforms = [];
  let reason = '';

  switch (verdict.code) {
    case 'RECORD_MISSING':
      return closed('記録が無い。判定できない日は投稿しない');
    case 'CONTINUE_EXPERIMENT': {
      const remain = Math.max(0, GATES.weeklyVideoCap - summary.experiment.videos);
      if (remain === 0) return closed('実験の3本は出した。触らない');
      cap = remain;
      platforms = unlocked.filter((p) => EXPERIMENT_PLATFORMS.includes(p));
      reason = `実験中。癒し型を残り${remain}本、YouTube だけ`;
      break;
    }
    case 'FUNNEL_ALIVE':
      cap = GATES.weeklyVideoCap;
      platforms = unlocked;
      reason = `導線は生きている。同じ型を週${cap}本まで`;
      break;
    case 'OFFER_ALIVE':
      cap = GATES.weeklyVideoCap;
      platforms = unlocked;
      reason = `案件は生きている。成果が付いた型だけ週${cap}本まで`;
      break;
    case 'SUSPECT_OFFER':
      return closed('案件か着地を疑う。人間が1本選ぶまで自動投稿しない');
    case 'FUNNEL_WEAK':
      return closed('導線では足りない。量産しない。次の一手は人間が選ぶ');
    default:
      return closed(`未知の判定 ${verdict.code}`);
  }

  if (platforms.length === 0) {
    return closed(`${reason}。ただし platform_unlock に有効な媒体が無い`);
  }
  return { allowed: true, weekly_cap: cap, platforms, reason };
}

function next3Markdown() {
  const result = spawnSync(process.execPath, [path.join(__dirname, 'youtube-next3.js')], {
    encoding: 'utf-8'
  });
  if (result.status !== 0) {
    return `次の3本を出せなかった: ${(result.stderr || result.stdout || '').trim()}`;
  }
  return (result.stdout || '').trim();
}

function renderMarkdown(summary, verdict, next3, posting) {
  const lines = [
    `# ${TRACKING_ISSUE_TITLE}`,
    '',
    `日付: ${summary.today}（JST）`,
    `判定: **${verdict.code}** — ${verdict.title}`,
    `今日の改善: ${verdict.improve}`,
    `今日の作業: ${verdict.action}`,
    ''
  ];

  if (posting) {
    lines.push('## 自動投稿ゲート（video-poster.js が読む）');
    lines.push('');
    if (posting.allowed) {
      lines.push(`- 開: 週${posting.weekly_cap}本まで / 媒体: ${posting.platforms.join(', ')}`);
    } else {
      lines.push('- 閉: 今日は自動投稿しない');
    }
    lines.push(`- 理由: ${posting.reason}`);
    lines.push('- 媒体を足すのは人間。config/video_accounts.json の platform_unlock に日付を書く');
    lines.push('');
  }

  if (!verdict.canTalk1M) {
    lines.push(`月100万はまだ語らない。週${GATES.weeklyClick1M}クリックが${GATES.weeklyClick1MStreak}週続くまで待つ。`);
    lines.push('');
  } else {
    lines.push(`週${GATES.weeklyClick1M}クリックが${GATES.weeklyClick1MStreak}週続いた。月100万の話を始めてよい。まだ媒体は足さない。`);
    lines.push('');
  }

  lines.push('## 数字（CSVにある分だけ）');
  lines.push('');
  if (summary.rowCount === 0) {
    lines.push('記録0行。数字は発明していない。');
  } else {
    lines.push(`- 記録行: ${summary.rowCount}（最終 ${summary.lastDate}）`);
    lines.push(
      `- 直近7日 (${summary.last7.start}〜${summary.last7.end}): 投稿${summary.last7.videos} / 再生${summary.last7.views} / クリック${summary.last7.clicks} / 成果${summary.last7.conversions}`
    );
    lines.push(
      `- 累計: 投稿${summary.cumulative.videos} / 再生${summary.cumulative.views} / クリック${summary.cumulative.clicks} / 成果${summary.cumulative.conversions}`
    );
    lines.push(
      `- 実験 ${summary.experiment.day}日目: 投稿${summary.experiment.videos} / クリック${summary.experiment.clicks} / 成果${summary.experiment.conversions}`
    );
    lines.push(
      `- 週次クリック: ${summary.weekClicks.map((w) => `${w.start}〜${w.end}=${w.clicks}`).join(' / ')}`
    );
    const platforms = Object.keys(summary.byPlatform || {});
    if (platforms.length > 1) {
      for (const p of platforms) {
        const s = summary.byPlatform[p];
        lines.push(
          `- ${p}: 直近7日 投稿${s.last7.videos} / 再生${s.last7.views} / クリック${s.last7.clicks} / 成果${s.last7.conversions}（累計 投稿${s.cumulative.videos} / クリック${s.cumulative.clicks} / 成果${s.cumulative.conversions}）`
        );
      }
    }
  }
  lines.push('');
  lines.push('ゲート: 週15で導線、累計50+成果0で案件疑い、週50が3週で月100万の会話解禁。');
  lines.push('');
  lines.push('## やるな');
  lines.push('');
  for (const item of FORBIDDEN) lines.push(`- ${item}`);
  lines.push('');

  if (verdict.includeNext3 && next3) {
    lines.push('## 次の3本（再掲。新しい創作ではない）');
    lines.push('');
    lines.push(next3);
    lines.push('');
  }

  lines.push('記録の書き方: `affiliate-engine/data/video_cash_log.csv` に1行。GitHubアプリでよい。');
  lines.push('');
  return `${lines.join('\n')}\n`;
}

async function upsertIssue(body) {
  const token = process.env.GITHUB_TOKEN || '';
  const repo = process.env.GITHUB_REPOSITORY || '';
  if (!token || !repo) {
    console.log('  Issue投稿はスキップ（GITHUB_TOKEN / GITHUB_REPOSITORY なし）');
    return null;
  }

  const headers = {
    Authorization: `token ${token}`,
    Accept: 'application/vnd.github.v3+json',
    'content-type': 'application/json'
  };
  const base = `https://api.github.com/repos/${repo}`;
  const searchRes = await fetch(`${base}/issues?state=open&per_page=100`, { headers });
  const existing = await searchRes.json().catch(() => []);
  const found = Array.isArray(existing) ? existing.find((i) => i.title === TRACKING_ISSUE_TITLE) : null;

  if (!found) {
    const createRes = await fetch(`${base}/issues`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        title: TRACKING_ISSUE_TITLE,
        labels: ['video-cash-loop'],
        body
      })
    });
    if (!createRes.ok) {
      console.warn(`  追跡Issueの作成に失敗: ${createRes.status}`);
      return null;
    }
    const created = await createRes.json();
    console.log(`  追跡Issueを作成: #${created.number}`);
    return created.number;
  }

  const patchRes = await fetch(`${base}/issues/${found.number}`, {
    method: 'PATCH',
    headers,
    body: JSON.stringify({ body })
  });
  if (!patchRes.ok) {
    console.warn(`  追跡Issueの更新に失敗: ${patchRes.status}`);
    return found.number;
  }
  console.log(`  追跡Issueを更新: #${found.number}`);
  return found.number;
}

function writeOutputs(today, markdown, payload) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const dated = path.join(OUT_DIR, `judge_${today}.md`);
  const latest = path.join(OUT_DIR, 'TODAY.md');
  const jsonPath = path.join(OUT_DIR, 'latest.json');
  fs.writeFileSync(dated, markdown, 'utf-8');
  fs.writeFileSync(latest, markdown, 'utf-8');
  fs.writeFileSync(jsonPath, JSON.stringify(payload, null, 2), 'utf-8');
  return { dated, latest, jsonPath };
}

function loadRows() {
  if (!fs.existsSync(LOG_PATH)) return [];
  return parseLog(fs.readFileSync(LOG_PATH, 'utf-8'));
}

function assertEqual(actual, expected, label) {
  if (actual !== expected) {
    throw new Error(`${label}: expected ${expected}, got ${actual}`);
  }
}

function runSelfTest() {
  const today = '2026-08-30';

  const missingDuring = decide(summarize([], today));
  assertEqual(missingDuring.code, 'RECORD_MISSING', 'empty log in experiment');
  assertEqual(missingDuring.includeNext3, true, 'experiment missing still needs scripts');

  const missingAfter = decide(summarize([], '2026-09-10'));
  assertEqual(missingAfter.code, 'RECORD_MISSING', 'empty log after experiment');
  assertEqual(missingAfter.includeNext3, false, 'after experiment missing has no scripts');

  const exampleOnly = decide(
    summarize(parseLog('date,videos_published,views,a8_clicks,conversions,note\n2026-08-22,0,0,0,0,example. copy\n'), today)
  );
  assertEqual(exampleOnly.code, 'RECORD_MISSING', 'example row skipped');

  const day3 = decide(
    summarize(
      parseLog(
        [
          'date,videos_published,views,a8_clicks,conversions,note',
          '2026-08-22,1,800,1,0,healing',
          '2026-08-23,1,500,1,0,',
          '2026-08-24,0,400,0,0,'
        ].join('\n')
      ),
      '2026-08-24'
    )
  );
  assertEqual(day3.code, 'CONTINUE_EXPERIMENT', 'in experiment');
  assertEqual(day3.includeNext3, true, 'experiment still needs posts');

  const posted3 = decide(
    summarize(
      parseLog(
        [
          'date,videos_published,views,a8_clicks,conversions,note',
          '2026-08-22,1,100,1,0,',
          '2026-08-23,1,100,1,0,',
          '2026-08-24,1,100,1,0,'
        ].join('\n')
      ),
      '2026-08-24'
    )
  );
  assertEqual(posted3.includeNext3, false, '3 already posted');
  if (!/触るな/.test(posted3.action)) throw new Error('posted3 action');

  const funnel = decide(
    summarize(
      parseLog(
        [
          'date,videos_published,views,a8_clicks,conversions,note',
          '2026-09-01,1,1000,5,0,',
          '2026-09-02,1,1000,5,0,',
          '2026-09-03,1,1000,6,0,'
        ].join('\n')
      ),
      '2026-09-07'
    )
  );
  assertEqual(funnel.code, 'FUNNEL_ALIVE', 'weekly 16 clicks after experiment');
  assertEqual(funnel.includeNext3, true, 'funnel reprints scripts');

  const suspect = decide(
    summarize(
      parseLog(
        [
          'date,videos_published,views,a8_clicks,conversions,note',
          '2026-08-25,1,200,20,0,',
          '2026-09-01,1,200,20,0,',
          '2026-09-03,1,200,20,0,'
        ].join('\n')
      ),
      '2026-09-07'
    )
  );
  assertEqual(suspect.code, 'SUSPECT_OFFER', 'weekly 40 and cumulative 60');

  const alive = decide(
    summarize(
      parseLog('date,videos_published,views,a8_clicks,conversions,note\n2026-09-05,1,900,4,1,first\n'),
      '2026-09-07'
    )
  );
  assertEqual(alive.code, 'OFFER_ALIVE', 'one conversion wins');

  const weak = decide(
    summarize(
      parseLog('date,videos_published,views,a8_clicks,conversions,note\n2026-09-05,1,900,2,0,\n'),
      '2026-09-07'
    )
  );
  assertEqual(weak.code, 'FUNNEL_WEAK', 'few clicks after experiment');

  const talk = decide(
    summarize(
      parseLog(
        [
          'date,videos_published,views,a8_clicks,conversions,note',
          '2026-08-18,1,100,50,0,',
          '2026-08-25,1,100,50,0,',
          '2026-09-01,1,100,50,1,'
        ].join('\n')
      ),
      '2026-09-07'
    )
  );
  assertEqual(talk.code, 'OFFER_ALIVE', 'conversion still wins over 1M talk');
  assertEqual(talk.canTalk1M, true, '3 weeks of 50');

  // --- 自動投稿ゲート ---
  const unlockYt = { youtube: '2026-06-20', tiktok: null, instagram: null };
  const unlockAll = { youtube: '2026-06-20', tiktok: '2026-09-01', instagram: '2026-09-01' };
  const unlockFuture = { youtube: '2026-06-20', tiktok: '2027-01-01', instagram: null };

  assertEqual(unlockedPlatforms(unlockFuture, '2026-09-07').join(','), 'youtube', 'future unlock date is not yet open');
  assertEqual(unlockedPlatforms(unlockAll, '2026-09-07').join(','), 'youtube,tiktok,instagram', 'all unlocked');
  assertEqual(unlockedPlatforms({ youtube: 'yes' }, '2026-09-07').length, 0, 'non-date unlock ignored');

  const gMissing = postingGate(summarize([], today), missingDuring, unlockAll);
  assertEqual(gMissing.allowed, false, 'record missing closes gate');

  const day3Summary = summarize(
    parseLog(
      [
        'date,videos_published,views,a8_clicks,conversions,note',
        '2026-08-22,1,800,1,0,healing',
        '2026-08-23,1,500,1,0,'
      ].join('\n')
    ),
    '2026-08-24'
  );
  const gExp = postingGate(day3Summary, decide(day3Summary), unlockAll);
  assertEqual(gExp.allowed, true, 'experiment with remaining opens gate');
  assertEqual(gExp.weekly_cap, 1, 'experiment cap is remaining count');
  assertEqual(gExp.platforms.join(','), 'youtube', 'experiment is youtube only even if others unlocked');

  const posted3Summary = summarize(
    parseLog(
      [
        'date,videos_published,views,a8_clicks,conversions,note',
        '2026-08-22,1,100,1,0,',
        '2026-08-23,1,100,1,0,',
        '2026-08-24,1,100,1,0,'
      ].join('\n')
    ),
    '2026-08-24'
  );
  assertEqual(postingGate(posted3Summary, decide(posted3Summary), unlockAll).allowed, false, '3 posted closes gate');

  const funnelSummary = summarize(
    parseLog(
      [
        'date,videos_published,views,a8_clicks,conversions,note',
        '2026-09-01,1,1000,5,0,',
        '2026-09-02,1,1000,5,0,',
        '2026-09-03,1,1000,6,0,'
      ].join('\n')
    ),
    '2026-09-07'
  );
  const gFunnelYt = postingGate(funnelSummary, decide(funnelSummary), unlockYt);
  assertEqual(gFunnelYt.allowed, true, 'funnel alive opens gate');
  assertEqual(gFunnelYt.weekly_cap, GATES.weeklyVideoCap, 'funnel cap is weekly cap');
  assertEqual(gFunnelYt.platforms.join(','), 'youtube', 'only unlocked platforms');
  const gFunnelAll = postingGate(funnelSummary, decide(funnelSummary), unlockAll);
  assertEqual(gFunnelAll.platforms.join(','), 'youtube,tiktok,instagram', 'human unlock adds platforms');
  assertEqual(postingGate(funnelSummary, decide(funnelSummary), {}).allowed, false, 'no unlock closes gate');

  const weakSummary = summarize(
    parseLog('date,videos_published,views,a8_clicks,conversions,note\n2026-09-05,1,900,2,0,\n'),
    '2026-09-07'
  );
  assertEqual(postingGate(weakSummary, decide(weakSummary), unlockAll).allowed, false, 'weak funnel closes gate');

  const suspectSummary = summarize(
    parseLog(
      [
        'date,videos_published,views,a8_clicks,conversions,note',
        '2026-08-25,1,200,20,0,',
        '2026-09-01,1,200,20,0,',
        '2026-09-03,1,200,20,0,'
      ].join('\n')
    ),
    '2026-09-07'
  );
  assertEqual(postingGate(suspectSummary, decide(suspectSummary), unlockAll).allowed, false, 'suspect offer closes gate');

  // --- platform 列 ---
  const multi = summarize(
    parseLog(
      [
        'date,platform,videos_published,views,a8_clicks,conversions,note',
        '2026-09-05,youtube,1,900,10,0,',
        '2026-09-05,tiktok,1,300,2,0,',
        '2026-09-06,,1,500,6,1,blank platform = youtube',
        '2026-09-06,Instagram,1,100,0,0,case insensitive'
      ].join('\n')
    ),
    '2026-09-07'
  );
  assertEqual(multi.cumulative.clicks, 18, 'platform rows sum into total');
  assertEqual(multi.byPlatform.youtube.cumulative.videos, 2, 'blank platform counts as youtube');
  assertEqual(multi.byPlatform.tiktok.cumulative.clicks, 2, 'tiktok rows split out');
  assertEqual(multi.byPlatform.instagram.rows, 1, 'platform is case insensitive');
  assertEqual(decide(multi).code, 'OFFER_ALIVE', 'conversion on any platform keeps offer alive');

  const md = renderMarkdown(multi, decide(multi), '', postingGate(multi, decide(multi), unlockAll));
  if (!/自動投稿ゲート/.test(md) || !/tiktok:/.test(md)) throw new Error('markdown lacks gate or platform lines');

  console.log('self-test ok');
}

async function main() {
  const today = process.env.VIDEO_JUDGE_TODAY || todayJST();
  console.log(`動画判定 ${today}`);

  const rows = loadRows();
  const summary = summarize(rows, today);
  const verdict = decide(summary);
  const unlock = (loadConfig('video_accounts', {}) || {}).platform_unlock || {};
  const posting = postingGate(summary, verdict, unlock);
  const next3 = verdict.includeNext3 ? next3Markdown() : '';
  const markdown = renderMarkdown(summary, verdict, next3, posting);
  const payload = { generated_at: new Date().toISOString(), summary, verdict, posting };
  const paths = writeOutputs(today, markdown, payload);

  console.log(`  ${verdict.code}: ${verdict.title}`);
  console.log(`  ゲート: ${posting.allowed ? `開（週${posting.weekly_cap}本 / ${posting.platforms.join(',')}）` : '閉'} — ${posting.reason}`);
  console.log(`  ${paths.latest}`);

  if (process.argv.includes('--json')) {
    process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`);
  } else {
    process.stdout.write(markdown);
  }

  await upsertIssue(markdown);
}

module.exports = {
  GATES,
  PLATFORMS,
  parseLog,
  summarize,
  decide,
  postingGate,
  unlockedPlatforms,
  renderMarkdown,
  addDays
};

if (require.main === module) {
  if (process.argv.includes('--self-test')) {
    try {
      runSelfTest();
    } catch (err) {
      console.error(`self-test failed: ${err.message}`);
      process.exit(1);
    }
  } else {
    main().catch((err) => {
      console.error(`video-judge failed: ${err.message}`);
      process.exit(1);
    });
  }
}
