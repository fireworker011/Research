#!/usr/bin/env node
'use strict';

/**
 * 台帳 data/reel_log.csv から 再生 → クリック → 成果 を切り分ける。数字を発明しない。
 *   node src/judge.js              # output/JUDGE.md を書いて表示
 *   node src/judge.js --self-test  # 固定データで分岐を確認
 *   node src/judge.js --issue      # GITHUB_TOKEN があれば Issue「サクラ判定」にコメント
 *
 * CSV 列: date,id,type,posted,views,followers,profile_visits,link_taps,fanvue_subs,notes
 */

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const ROOT = path.join(__dirname, '..');
const account = JSON.parse(fs.readFileSync(path.join(ROOT, 'config', 'account.json'), 'utf8'));
const G = account.gates;

const COLUMNS = ['date', 'id', 'type', 'posted', 'views', 'followers', 'profile_visits', 'link_taps', 'fanvue_subs', 'notes'];

function parseCsv(text) {
  const rows = [];
  let field = '';
  let row = [];
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i += 1; }
      else if (c === '"') quoted = false;
      else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ',') { row.push(field); field = ''; }
    else if (c === '\n') { row.push(field); rows.push(row); row = []; field = ''; }
    else if (c !== '\r') field += c;
  }
  if (field.length || row.length) { row.push(field); rows.push(row); }
  return rows.filter((r) => r.some((v) => v.trim() !== ''));
}

function num(v) {
  if (v === undefined || v === null) return null;
  const s = String(v).replace(/,/g, '').trim();
  if (s === '') return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

function loadRows(csvText) {
  const rows = parseCsv(csvText);
  if (!rows.length) return [];
  const header = rows[0].map((h) => h.trim());
  const missing = COLUMNS.filter((c) => !header.includes(c));
  if (missing.length) throw new Error(`CSV 列が足りない: ${missing.join(',')}`);
  return rows.slice(1).map((r) => {
    const o = {};
    header.forEach((h, i) => { o[h] = (r[i] || '').trim(); });
    return o;
  }).filter((o) => /^\d{4}-\d{2}-\d{2}$/.test(o.date));
}

function daysBetween(a, b) {
  return Math.round((Date.parse(`${b}T00:00:00Z`) - Date.parse(`${a}T00:00:00Z`)) / 86400000);
}

function judge(rows) {
  const posted = rows.filter((r) => r.posted && r.posted !== 'no' && r.posted !== 'false');
  const withViews = posted.filter((r) => num(r.views) !== null);
  const anchor = posted.length ? posted.map((r) => r.date).sort().slice(-1)[0] : null;
  const week = anchor ? posted.filter((r) => daysBetween(r.date, anchor) >= 0 && daysBetween(r.date, anchor) < 7) : [];

  const followersNow = (() => {
    const known = posted.map((r) => num(r.followers)).filter((n) => n !== null);
    return known.length ? known[known.length - 1] : account.followers_baseline;
  })();

  const ratios = withViews.map((r) => ({ id: r.id, date: r.date, type: r.type, views: num(r.views), ratio: num(r.views) / (num(r.followers) || followersNow) }));
  const maxRatio = ratios.length ? Math.max(...ratios.map((x) => x.ratio)) : null;
  const best = ratios.length ? ratios.reduce((a, b) => (b.ratio > a.ratio ? b : a)) : null;

  const tapsKnown = week.map((r) => num(r.link_taps)).filter((n) => n !== null);
  const tapsWeek = tapsKnown.length ? tapsKnown.reduce((a, b) => a + b, 0) : null;
  const subsKnown = posted.map((r) => num(r.fanvue_subs)).filter((n) => n !== null);
  const subsLatest = subsKnown.length ? subsKnown[subsKnown.length - 1] : null;

  let stage;
  let verdict;
  let next;
  if (!posted.length) {
    stage = 0; verdict = '投稿記録なし'; next = 'A が投稿し、日曜に行を足す。判定はまだしない。';
  } else if (!withViews.length) {
    stage = 0; verdict = '再生が未記録'; next = 'Insights の再生数を行に入れる。数字が無い週は Fanvue を触らない。';
  } else if (maxRatio < G.views_x2) {
    stage = 1; verdict = '再生が無い（最高でもフォロワーの ' + maxRatio.toFixed(2) + ' 倍）'; next = '型の話。冒頭0.5秒・髪型・場面の差が出ているか。量産もエージェント増設もしない。';
  } else if (tapsWeek === null) {
    stage = 2; verdict = '再生はある。リンクタップが未記録'; next = 'Insights のリンクタップ（週）を行に入れる。導線の判定はそれから。';
  } else if (tapsWeek < G.link_taps_week_min) {
    stage = 2; verdict = `再生はあるがタップが週 ${tapsWeek}（最低 ${G.link_taps_week_min}）`; next = '導線の話。バイオのリンク1本と木曜CTAだけ直す。着地は触らない。';
  } else if (subsLatest === null || subsLatest === 0) {
    stage = 3; verdict = `タップ週 ${tapsWeek}。課金 ${subsLatest === null ? '未記録' : 0}`; next = tapsWeek >= G.link_taps_week_judge_offer
      ? '着地の話をしてよい。Fanvue の中身と価格を1回だけ見る。同じ動画は増やさない。'
      : `着地の兆候。週 ${G.link_taps_week_judge_offer} タップまでは Fanvue を大きく変えない。`;
  } else {
    stage = 4; verdict = `課金あり（${subsLatest}）`; next = '成果が出た型だけ複製する。媒体は増やさない。';
  }

  return { anchor, followersNow, weekCount: week.length, tapsWeek, maxRatio, best, subsLatest, stage, verdict, next, ratios, week };
}

function render(j) {
  const gate10 = j.followersNow * G.views_x10;
  const lines = [
    `# サクラ判定 ${j.anchor || ''}`,
    '',
    `フォロワー: ${j.followersNow}。10倍ゲート: ${gate10} 再生。週タップ最低: ${G.link_taps_week_min}。`,
    '',
    `**段階 ${j.stage} — ${j.verdict}**`,
    '',
    `次にやること: ${j.next}`,
    '',
    '| date | id | type | views | ×followers | link_taps |',
    '|---|---|---|---|---|---|'
  ];
  for (const r of j.week) {
    const v = num(r.views);
    const ratio = v === null ? '' : (v / (num(r.followers) || j.followersNow)).toFixed(2);
    lines.push(`| ${r.date} | ${r.id} | ${r.type} | ${v === null ? '未記録' : v} | ${ratio} | ${num(r.link_taps) === null ? '未記録' : num(r.link_taps)} |`);
  }
  if (!j.week.length) lines.push('| — | — | — | — | — | — |');
  lines.push('');
  if (j.best) lines.push(`最高: ${j.best.id} ${j.best.views} 再生（${j.best.ratio.toFixed(2)} 倍）`);
  lines.push(`週タップ合計: ${j.tapsWeek === null ? '未記録' : j.tapsWeek}。Fanvue 課金: ${j.subsLatest === null ? '未記録' : j.subsLatest}。`);
  lines.push('');
  lines.push('数字が無い欄は埋めない。この判定は台帳の行だけから出している。');
  return lines.join('\n');
}

function selfTest() {
  const header = COLUMNS.join(',');
  const cases = [
    { name: 'empty', csv: `${header}\n`, stage: 0 },
    { name: 'no views', csv: `${header}\n2026-09-13,reel-2026-09-13,loop,yes,,,,,,\n`, stage: 0 },
    { name: 'low views', csv: `${header}\n2026-09-13,reel-2026-09-13,loop,yes,800,2675,10,0,,\n`, stage: 1 },
    { name: 'views no taps', csv: `${header}\n2026-09-13,reel-2026-09-13,loop,yes,9000,2675,40,,,\n`, stage: 2 },
    { name: 'views few taps', csv: `${header}\n2026-09-13,reel-2026-09-13,loop,yes,9000,2675,40,4,0,\n2026-09-14,reel-2026-09-14,question,yes,3000,2675,20,3,0,\n`, stage: 2 },
    { name: 'taps no subs', csv: `${header}\n2026-09-13,reel-2026-09-13,loop,yes,30000,2675,300,20,0,\n`, stage: 3 },
    { name: 'subs', csv: `${header}\n2026-09-13,reel-2026-09-13,loop,yes,30000,2675,300,60,3,"good, keep"\n`, stage: 4 }
  ];
  let fail = 0;
  for (const c of cases) {
    const j = judge(loadRows(c.csv));
    const ok = j.stage === c.stage;
    if (!ok) fail += 1;
    console.log(`${ok ? 'ok ' : 'NG '} ${c.name}: stage ${j.stage} (${j.verdict})`);
  }
  if (fail) { console.error(`self-test: ${fail} failed`); process.exit(1); }
  console.log('self-test: OK');
}

function upsertIssue(body) {
  const title = account.issue_judge;
  const raw = execFileSync('gh', ['issue', 'list', '--search', `${title} in:title`, '--state', 'open', '--json', 'number,title', '--limit', '20'], { encoding: 'utf8' });
  const hit = JSON.parse(raw).find((i) => i.title === title);
  if (!hit) {
    const url = execFileSync('gh', ['issue', 'create', '--title', title, '--body', body], { encoding: 'utf8' }).trim();
    return `created ${url}`;
  }
  execFileSync('gh', ['issue', 'comment', String(hit.number), '--body', body], { encoding: 'utf8' });
  return `commented #${hit.number}`;
}

function main() {
  if (process.argv.includes('--self-test')) { selfTest(); return; }
  const csv = fs.readFileSync(path.join(ROOT, 'data', 'reel_log.csv'), 'utf8');
  const j = judge(loadRows(csv));
  const md = render(j);
  fs.mkdirSync(path.join(ROOT, 'output'), { recursive: true });
  fs.writeFileSync(path.join(ROOT, 'output', 'JUDGE.md'), `${md}\n`);
  console.log(md);
  if (process.argv.includes('--issue')) {
    if (!(process.env.GITHUB_TOKEN || process.env.GH_TOKEN)) { console.log('no token; local only'); return; }
    console.log(upsertIssue(md));
  }
}

if (require.main === module) {
  try { main(); } catch (err) { console.error(err.message); process.exit(1); }
}

module.exports = { judge, loadRows, render };
