#!/usr/bin/env node
'use strict';

/**
 * FANZA/DMMアダアフィの定期判定。投稿しない。数字を発明しない。
 * ペット動画（video-judge.js）とは別事業。混ぜない。
 *
 *   node src/adult-judge.js
 *   node src/adult-judge.js --self-test
 *   ADULT_JUDGE_TODAY=2026-09-10 node src/adult-judge.js
 */

const fs = require('fs');
const path = require('path');
const { ROOT, OUTPUT_DIR, parseCSV, todayJST } = require('./util');

const GATES = {
  experimentDays: 14,
  weeklyClickMin: 15,
  weeklyClick1M: 50,
  weeklyClick1MStreak: 3,
  cumulativeOfferJudge: 50,
  weeklyPostCap: 7,
  payoutMinJpy: 5000
};

const ALLOWED_CHANNELS = new Set(['x', 'landing']);
const FORBIDDEN_CHANNELS = new Set([
  'youtube',
  'tiktok',
  'instagram',
  'threads',
  'pet',
  'shorts',
  'reels'
]);

const LOG_PATH = process.env.ADULT_CASH_LOG || path.join(ROOT, 'data', 'adult_cash_log.csv');
const OUT_DIR = process.env.ADULT_JUDGE_OUT || path.join(OUTPUT_DIR, 'adult');
const TRACKING_ISSUE_TITLE = 'アダアフィキャッシュループ — 今日の判定';
const FORBIDDEN = [
  'ペットチャンネルをアダに転用するな',
  'YouTube / TikTok / Instagram / Threads にアダを出すな',
  '投稿を自動化するな。X bot・Playwright で投稿するな',
  'insight.js をアダに使うな',
  'アフィリンクをコミットするな',
  '体験談を捏造するな。#PR / 広告 なしでリンクするな',
  '数字が無いのに量産するな',
  '週50クリックが3週続く前に月100万を語るな'
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

function normalizeChannel(value) {
  return String(value || '')
    .trim()
    .toLowerCase();
}

function isLiveRow(row) {
  if (!row || !/^\d{4}-\d{2}-\d{2}$/.test(row.date || '')) return false;
  if (/\bexample\b/i.test(row.note || '')) return false;
  return true;
}

function normalizeRow(row) {
  return {
    date: row.date,
    channel: normalizeChannel(row.channel),
    posts: toInt(row.posts),
    impressions: toInt(row.impressions),
    clicks: toInt(row.clicks),
    conversions: toInt(row.conversions),
    reward_jpy: toInt(row.reward_jpy),
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

function uniqueChannels(rows) {
  return [...new Set(rows.map((row) => row.channel).filter(Boolean))];
}

function hasWrongChannel(rows) {
  return rows.some((row) => !row.channel || FORBIDDEN_CHANNELS.has(row.channel) || !ALLOWED_CHANNELS.has(row.channel));
}

function experimentStartOf(rows, today) {
  return rows.length ? rows[0].date : today;
}

function summarize(rows, today) {
  const live = rows.filter((row) => row.date <= today).sort((a, b) => a.date.localeCompare(b.date));
  const start = experimentStartOf(live, today);
  const last7 = inRange(live, addDays(today, -6), today);
  const prev7 = inRange(live, addDays(today, -13), addDays(today, -7));
  const experimentRows = inRange(live, start, addDays(start, GATES.experimentDays - 1));
  const weekClicks = [];
  for (let i = 0; i < GATES.weeklyClick1MStreak; i++) {
    const end = addDays(today, -7 * i);
    const weekStart = addDays(end, -6);
    weekClicks.push({ start: weekStart, end, clicks: sumField(inRange(live, weekStart, end), 'clicks') });
  }

  return {
    today,
    rowCount: live.length,
    lastDate: live.length ? live[live.length - 1].date : null,
    channels: uniqueChannels(live),
    wrongChannel: hasWrongChannel(live),
    last7: {
      start: addDays(today, -6),
      end: today,
      posts: sumField(last7, 'posts'),
      impressions: sumField(last7, 'impressions'),
      clicks: sumField(last7, 'clicks'),
      conversions: sumField(last7, 'conversions'),
      reward_jpy: sumField(last7, 'reward_jpy')
    },
    prev7Clicks: sumField(prev7, 'clicks'),
    cumulative: {
      posts: sumField(live, 'posts'),
      impressions: sumField(live, 'impressions'),
      clicks: sumField(live, 'clicks'),
      conversions: sumField(live, 'conversions'),
      reward_jpy: sumField(live, 'reward_jpy')
    },
    experiment: {
      start,
      day: live.length ? daysBetween(start, today) + 1 : 0,
      posts: sumField(experimentRows, 'posts'),
      clicks: sumField(experimentRows, 'clicks'),
      conversions: sumField(experimentRows, 'conversions')
    },
    weekClicks
  };
}

function decide(summary) {
  const inExperiment =
    summary.rowCount > 0 &&
    summary.experiment.day >= 1 &&
    summary.experiment.day <= GATES.experimentDays;
  const canTalk1M = summary.weekClicks.every((w) => w.clicks >= GATES.weeklyClick1M);
  const payoutReady = summary.cumulative.reward_jpy >= GATES.payoutMinJpy;

  if (summary.wrongChannel) {
    return {
      code: 'WRONG_CHANNEL',
      title: '禁止媒体に出している。止める',
      improve: 'YouTube / TikTok / Instagram / Threads / ペットをアダに使うな',
      action: 'その媒体のアダ投稿を止めろ。許可は x と landing だけ。ペットは元の実験に戻せ',
      canTalk1M: false,
      inExperiment: false,
      payoutReady
    };
  }

  if (summary.rowCount === 0) {
    return {
      code: 'RECORD_MISSING',
      title: '記録が無い。改善できない',
      improve: 'CSVに数字を書け。記録が無い改善は妄想',
      action:
        '人間だけ: DMMアフィ登録 → 新規Xを審査に出す → 投稿1本（#PR必須）→ adult_cash_log.csv に1行。リンクはコミットするな',
      canTalk1M: false,
      inExperiment: false,
      payoutReady: false
    };
  }

  if (inExperiment) {
    const remain = Math.max(0, GATES.weeklyPostCap - summary.last7.posts);
    return {
      code: 'CONTINUE_EXPERIMENT',
      title: `実験 ${summary.experiment.day}/${GATES.experimentDays}日目。媒体は変えない`,
      improve: 'なし。実験中にYouTubeへ逃げることが失敗',
      action:
        remain > 0
          ? `Xに直近7日の残り${remain}本。1日1本。#PR必須。公式ツールバーのリンク。体験は書くな`
          : '直近7日の7本は出した。触るな。今日のクリックと成果だけCSVに書け',
      canTalk1M,
      inExperiment,
      payoutReady
    };
  }

  if (summary.cumulative.conversions >= 1) {
    return {
      code: 'OFFER_ALIVE',
      title: '案件は生きている',
      improve: '成果が付いた型だけ複製する。媒体は足さない',
      action: '成果が付いたXの型だけ、週7本まで。YouTubeは開かない',
      canTalk1M,
      inExperiment: false,
      payoutReady
    };
  }

  if (
    summary.last7.clicks >= GATES.weeklyClickMin &&
    summary.cumulative.clicks >= GATES.cumulativeOfferJudge
  ) {
    return {
      code: 'SUSPECT_OFFER',
      title: '導線は動いたが、案件か着地を疑う',
      improve: '同じ紹介を増やすな。人間が着地を1つだけ変える',
      action: '着地を1つだけ変える。量産禁止。媒体追加禁止',
      canTalk1M,
      inExperiment: false,
      payoutReady
    };
  }

  if (summary.last7.clicks >= GATES.weeklyClickMin) {
    return {
      code: 'FUNNEL_ALIVE',
      title: '導線は生きている',
      improve: '同じXの型を週7本まで。媒体は足さない',
      action: `同じ型で週${GATES.weeklyPostCap}本まで。#PR必須`,
      canTalk1M,
      inExperiment: false,
      payoutReady
    };
  }

  return {
    code: 'FUNNEL_WEAK',
    title: '導線では足りない',
    improve: '量産禁止。YouTubeへ逃げるな。次の一手は人間が1つだけ選ぶ',
    action: '量産するな。媒体を足すな。着地か投稿頻度かを人間が1つだけ選ぶ',
    canTalk1M,
    inExperiment: false,
    payoutReady
  };
}

function renderMarkdown(summary, verdict) {
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
    lines.push(
      `月100万はまだ語らない。週${GATES.weeklyClick1M}クリックが${GATES.weeklyClick1MStreak}週続くまで待つ。最初の現金ゲートは累計報酬¥${GATES.payoutMinJpy}。`
    );
  } else {
    lines.push(
      `週${GATES.weeklyClick1M}クリックが${GATES.weeklyClick1MStreak}週続いた。月100万の話を始めてよい。まだYouTubeは足さない。`
    );
  }
  lines.push('');

  if (verdict.payoutReady) {
    lines.push(`支払下限 ¥${GATES.payoutMinJpy} を超えた記録がある。口座が無ければ登録だけ人間がやる。`);
    lines.push('');
  }

  lines.push('## 数字（CSVにある分だけ）');
  lines.push('');
  if (summary.rowCount === 0) {
    lines.push('記録0行。数字は発明していない。');
  } else {
    lines.push(`- 記録行: ${summary.rowCount}（最終 ${summary.lastDate}）`);
    lines.push(`- 媒体: ${summary.channels.join(', ') || 'なし'}`);
    lines.push(
      `- 直近7日 (${summary.last7.start}〜${summary.last7.end}): 投稿${summary.last7.posts} / 表示${summary.last7.impressions} / クリック${summary.last7.clicks} / 成果${summary.last7.conversions} / 報酬¥${summary.last7.reward_jpy}`
    );
    lines.push(
      `- 累計: 投稿${summary.cumulative.posts} / 表示${summary.cumulative.impressions} / クリック${summary.cumulative.clicks} / 成果${summary.cumulative.conversions} / 報酬¥${summary.cumulative.reward_jpy}`
    );
    if (summary.experiment.day > 0) {
      lines.push(
        `- 実験 ${summary.experiment.day}日目: 投稿${summary.experiment.posts} / クリック${summary.experiment.clicks} / 成果${summary.experiment.conversions}`
      );
    }
    lines.push(
      `- 週次クリック: ${summary.weekClicks.map((w) => `${w.start}〜${w.end}=${w.clicks}`).join(' / ')}`
    );
  }
  lines.push('');
  lines.push(
    `ゲート: 週${GATES.weeklyClickMin}で導線、累計${GATES.cumulativeOfferJudge}+成果0で案件疑い、週${GATES.weeklyClick1M}が${GATES.weeklyClick1MStreak}週で月100万の会話解禁。現金は¥${GATES.payoutMinJpy}。`
  );
  lines.push('');
  lines.push('## やるな');
  lines.push('');
  for (const item of FORBIDDEN) lines.push(`- ${item}`);
  lines.push('');
  lines.push('記録の書き方: `affiliate-engine/data/adult_cash_log.csv` に1行。GitHubアプリでよい。リンクは書くな。');
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
        labels: ['adult-fanza-loop'],
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

function header() {
  return 'date,channel,posts,impressions,clicks,conversions,reward_jpy,note';
}

function runSelfTest() {
  const missing = decide(summarize([], '2026-08-22'));
  assertEqual(missing.code, 'RECORD_MISSING', 'empty log');
  assertEqual(missing.canTalk1M, false, 'empty cannot talk 1M');

  const exampleOnly = decide(
    summarize(
      parseLog(`${header()}\n2026-08-22,x,1,100,1,0,0,example. copy\n`),
      '2026-08-22'
    )
  );
  assertEqual(exampleOnly.code, 'RECORD_MISSING', 'example row skipped');

  const youtube = decide(
    summarize(
      parseLog(`${header()}\n2026-08-22,youtube,1,1000,10,0,0,shorts\n`),
      '2026-08-22'
    )
  );
  assertEqual(youtube.code, 'WRONG_CHANNEL', 'youtube blocked');

  const pet = decide(
    summarize(parseLog(`${header()}\n2026-08-22,pet,1,100,1,0,0,\n`), '2026-08-22')
  );
  assertEqual(pet.code, 'WRONG_CHANNEL', 'pet blocked');

  const emptyChannel = decide(
    summarize(parseLog(`${header()}\n2026-08-22,,1,100,1,0,0,\n`), '2026-08-22')
  );
  assertEqual(emptyChannel.code, 'WRONG_CHANNEL', 'blank channel blocked');

  const day3 = decide(
    summarize(
      parseLog(
        [
          header(),
          '2026-08-22,x,1,200,1,0,0,',
          '2026-08-23,x,1,180,1,0,0,',
          '2026-08-24,x,0,90,0,0,0,'
        ].join('\n')
      ),
      '2026-08-24'
    )
  );
  assertEqual(day3.code, 'CONTINUE_EXPERIMENT', 'in experiment');
  if (!/残り/.test(day3.action)) throw new Error('day3 should ask remaining posts');

  const posted7 = decide(
    summarize(
      parseLog(
        [
          header(),
          '2026-08-22,x,1,10,1,0,0,',
          '2026-08-23,x,1,10,1,0,0,',
          '2026-08-24,x,1,10,1,0,0,',
          '2026-08-25,x,1,10,1,0,0,',
          '2026-08-26,x,1,10,1,0,0,',
          '2026-08-27,x,1,10,1,0,0,',
          '2026-08-28,x,1,10,1,0,0,'
        ].join('\n')
      ),
      '2026-08-28'
    )
  );
  assertEqual(posted7.code, 'CONTINUE_EXPERIMENT', 'still in 14 days');
  if (!/触るな/.test(posted7.action)) throw new Error('posted7 action');

  const funnel = decide(
    summarize(
      parseLog(
        [
          header(),
          '2026-08-25,x,1,100,1,0,0,',
          '2026-09-10,x,1,1000,5,0,0,',
          '2026-09-11,x,1,1000,5,0,0,',
          '2026-09-12,x,1,1000,6,0,0,'
        ].join('\n')
      ),
      '2026-09-16'
    )
  );
  assertEqual(funnel.code, 'FUNNEL_ALIVE', 'weekly 16 clicks after experiment');

  const suspect = decide(
    summarize(
      parseLog(
        [
          header(),
          '2026-08-25,x,1,200,20,0,0,',
          '2026-09-10,x,1,200,20,0,0,',
          '2026-09-12,x,1,200,20,0,0,'
        ].join('\n')
      ),
      '2026-09-16'
    )
  );
  assertEqual(suspect.code, 'SUSPECT_OFFER', 'weekly 40 and cumulative 60');

  const alive = decide(
    summarize(
      parseLog(`${header()}\n2026-09-05,x,1,900,4,1,1200,first\n`),
      '2026-09-20'
    )
  );
  assertEqual(alive.code, 'OFFER_ALIVE', 'one conversion wins');
  assertEqual(alive.payoutReady, false, '1200 is below payout min');

  const payout = decide(
    summarize(
      parseLog(`${header()}\n2026-09-05,x,1,900,4,3,5200,paid\n`),
      '2026-09-20'
    )
  );
  assertEqual(payout.payoutReady, true, '5200 unlocks payout note');

  const weak = decide(
    summarize(
      parseLog(`${header()}\n2026-09-05,x,1,900,2,0,0,\n`),
      '2026-09-20'
    )
  );
  assertEqual(weak.code, 'FUNNEL_WEAK', 'few clicks after experiment');

  const talk = decide(
    summarize(
      parseLog(
        [
          header(),
          '2026-08-28,x,1,100,50,0,0,',
          '2026-09-04,x,1,100,50,0,0,',
          '2026-09-11,x,1,100,50,1,1050,'
        ].join('\n')
      ),
      '2026-09-16'
    )
  );
  assertEqual(talk.code, 'OFFER_ALIVE', 'conversion still wins over 1M talk');
  assertEqual(talk.canTalk1M, true, '3 weeks of 50');

  const landing = decide(
    summarize(parseLog(`${header()}\n2026-08-22,landing,1,50,2,0,0,\n`), '2026-08-22')
  );
  assertEqual(landing.code, 'CONTINUE_EXPERIMENT', 'landing allowed');

  console.log('self-test ok');
}

async function main() {
  const today = process.env.ADULT_JUDGE_TODAY || todayJST();
  console.log(`アダ判定 ${today}`);

  const rows = loadRows();
  const summary = summarize(rows, today);
  const verdict = decide(summary);
  const markdown = renderMarkdown(summary, verdict);
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
  ALLOWED_CHANNELS,
  FORBIDDEN_CHANNELS,
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
      console.error(`adult-judge failed: ${err.message}`);
      process.exit(1);
    });
  }
}
