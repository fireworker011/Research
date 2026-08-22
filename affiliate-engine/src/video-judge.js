#!/usr/bin/env node
'use strict';

/**
 * アフィ動画の定期判定。改善とは「ゲートを見て、やってはいけないことを止める」こと。
 *
 * やること:
 * - video_cash_log.csv だけを見て、再生→クリック→成果を切り分ける
 * - スマホで読める判定を output/video/ と（任意で）GitHub Issue に書く
 * - 実験中は次の癒し3本を再掲する
 *
 * やらないこと:
 * - 投稿
 * - 数字の発明
 * - insight.js / Claude でのジャンル転換
 * - TikTok / Instagram / 量産 / 新しいエージェント
 *
 *   node src/video-judge.js
 *   node src/video-judge.js --self-test
 *   VIDEO_JUDGE_TODAY=2026-08-30 node src/video-judge.js
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { ROOT, OUTPUT_DIR, parseCSV, todayJST } = require('./util');
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

const LOG_PATH = process.env.VIDEO_CASH_LOG || path.join(ROOT, 'data', 'video_cash_log.csv');
const OUT_DIR = process.env.VIDEO_JUDGE_OUT || path.join(OUTPUT_DIR, 'video');
const TRACKING_ISSUE_TITLE = '動画キャッシュループ — 今日の判定';
const FORBIDDEN = [
  '投稿を自動化するな',
  'TikTok / Instagram を足すな',
  'ジャンル転換するな。参考チャンネルの動画をコピーするな',
  'insight.js を動画に使うな',
  'Shorts の説明欄・コメントにアフィURLを置くな',
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

function normalizeRow(row) {
  return {
    date: row.date,
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

  return {
    today,
    rowCount: live.length,
    lastDate: live.length ? live[live.length - 1].date : null,
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

function next3Markdown() {
  const result = spawnSync(process.execPath, [path.join(__dirname, 'youtube-next3.js')], {
    encoding: 'utf-8'
  });
  if (result.status !== 0) {
    return `次の3本を出せなかった: ${(result.stderr || result.stdout || '').trim()}`;
  }
  return (result.stdout || '').trim();
}

function renderMarkdown(summary, verdict, next3) {
  const lines = [
    `# ${TRACKING_ISSUE_TITLE}`,
    '',
    `日付: ${summary.today}（JST）`,
    `判定: **${verdict.code}** — ${verdict.title}`,
    `今日の改善: ${verdict.improve}`,
    `今日の作業: ${verdict.action}`,
    ''
  ];

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

  console.log('self-test ok');
}

async function main() {
  const today = process.env.VIDEO_JUDGE_TODAY || todayJST();
  console.log(`動画判定 ${today}`);

  const rows = loadRows();
  const summary = summarize(rows, today);
  const verdict = decide(summary);
  const next3 = verdict.includeNext3 ? next3Markdown() : '';
  const markdown = renderMarkdown(summary, verdict, next3);
  const payload = { generated_at: new Date().toISOString(), summary, verdict };
  const paths = writeOutputs(today, markdown, payload);

  console.log(`  ${verdict.code}: ${verdict.title}`);
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
  parseLog,
  summarize,
  decide,
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
