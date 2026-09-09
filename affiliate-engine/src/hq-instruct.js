#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { ISSUE_TITLE: YEN_ISSUE_TITLE } = require('./apply-a8-yen');
const { overlayStatusText } = require('./overlay-keys');
const { resolveAffi, START, fileFor, repliesFor } = require('./affi-step');
const { parseCSV } = require('./util');

const ISSUE_TITLE = 'Grok Bot — 指示';
const RAW_PREFIX =
  'https://raw.githubusercontent.com/fireworker011/Research/claude/setup-colab-comfyui-Eb9Lh/';
const XM_POINTER = 'xm-trade-engine/docs/grok-bots/G_xm_trade.txt';
const AFFI_POINTER = fileFor(START);
const POINTER = XM_POINTER;
const RAW = `${RAW_PREFIX}${XM_POINTER}`;
const INSTRUCT_BODY =
  '指示役が毎日 `hq-instruct:` を書く。高単価を進めるならコメントを `AFFI: GO` だけの行にする。止めるなら `AFFI: STOP`。分岐の返事は1語だけ。申請・副サイト・プロフィール・Secret が終わったら `完了`。Grok Bot は最新コメントの1ファイルだけ開け。人間は外部サイトだけ。';
const YEN_BODY =
  'A8 を自分で開いた日だけ1行。`A8_YEN: YYYY-MM-DD,A8,all,clicks,cv,yen,note`。URL・カンマ数字・カタログ円は拒否。開いていない日は書くな。';

function targetFor(go, state) {
  return go ? fileFor(state || START) : XM_POINTER;
}

function neoFlag(neo) {
  return neo === 'placed' ? 'placed' : 'no';
}

function instructBody(go = false, state = START, neo = 'no') {
  const pointer = targetFor(go, state);
  const extra = go
    ? '人間の1語（または完了）で次ファイルへ進め。ENTRY は出すな。'
    : 'ENTRY は出すな。';
  const lines = [
    `hq-instruct: ${pointer}`,
    `${RAW_PREFIX}${pointer}`,
    `この1ファイルだけ開け。結合するな。remain / n10 は開けるな。Cursor を起こすな。Threads cron は戻すな。${extra} boot に戻ってループするな。`
  ];
  if (go) {
    const st = state || START;
    lines.push(`hq-affi-state: ${st}`);
    lines.push(`hq-affi-neo: ${neoFlag(neo)}`);
    lines.push(`hq-affi-reply: ${repliesFor(st).join(' / ') || '(none)'}`);
  }
  return lines.join('\n');
}

function samePointer(body, go = false, state = START) {
  return String(body || '').includes(`hq-instruct: ${targetFor(go, state)}`);
}

function commentBody(go = false, state = START, neo = 'no') {
  return `${instructBody(go, state, neo)}\n${overlayStatusText().text.trim()}\n${yenStatusText()}`;
}

function approvedYenSum(csvText) {
  const rows = parseCSV(String(csvText || ''));
  let sum = 0;
  for (const r of rows) {
    const d = String(r.date || '');
    if (d.startsWith('#')) continue;
    if (/カタログ/.test(String(r.note || '')) && parseInt(r.approved_yen || '0', 10) > 0) continue;
    const n = parseInt(r.approved_yen, 10);
    if (!Number.isFinite(n)) continue;
    sum += n;
  }
  return sum;
}

function yenStatusText() {
  const csvPath = path.join(__dirname, '../data/conversions.csv');
  const n = approvedYenSum(fs.readFileSync(csvPath, 'utf8'));
  return `approved-yen: ${n}`;
}

function affiGo(comments) {
  let go = false;
  for (const c of comments || []) {
    if ((c.user?.login || '') === 'github-actions[bot]') continue;
    for (const line of String(c.body || '').split(/\r?\n/)) {
      if (/^\s*AFFI:\s*STOP\b/i.test(line)) go = false;
      else if (/^\s*AFFI:\s*GO\b/i.test(line)) go = true;
    }
  }
  return go;
}

function isTodayUtc(iso) {
  return String(iso || '').slice(0, 10) === new Date().toISOString().slice(0, 10);
}

async function api(url, { method = 'GET', body } = {}) {
  const token = process.env.GITHUB_TOKEN;
  if (!token) throw new Error('missing GITHUB_TOKEN');
  const res = await fetch(url, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'hq-instruct'
    },
    body: body ? JSON.stringify(body) : undefined
  });
  const text = await res.text();
  let json = null;
  try {
    json = text ? JSON.parse(text) : null;
  } catch {
    json = { raw: text };
  }
  if (!res.ok) {
    const err = new Error(`github ${res.status} ${url}`);
    err.status = res.status;
    throw err;
  }
  return json;
}

function repoApi(path) {
  const repo = process.env.GITHUB_REPOSITORY;
  if (!repo) throw new Error('missing GITHUB_REPOSITORY');
  return `https://api.github.com/repos/${repo}${path}`;
}

async function findIssueByTitle(title) {
  for (let page = 1; page <= 10; page++) {
    const issues = await api(repoApi(`/issues?state=all&per_page=100&page=${page}`));
    if (!Array.isArray(issues) || !issues.length) return null;
    const hit = issues.find((i) => i.title === title && !i.pull_request);
    if (hit) return hit;
    if (issues.length < 100) return null;
  }
  return null;
}

async function ensureIssue(title, body) {
  const hit = await findIssueByTitle(title);
  if (hit) {
    if (hit.state === 'closed') {
      await api(repoApi(`/issues/${hit.number}`), { method: 'PATCH', body: { state: 'open' } });
      hit.state = 'open';
    }
    return { issue: hit, created: false };
  }
  const issue = await api(repoApi('/issues'), {
    method: 'POST',
    body: { title, body }
  });
  return { issue, created: true };
}

async function listComments(issueNumber) {
  const out = [];
  for (let page = 1; page <= 10; page++) {
    const batch = await api(repoApi(`/issues/${issueNumber}/comments?per_page=100&page=${page}`));
    if (!Array.isArray(batch) || !batch.length) break;
    out.push(...batch);
    if (batch.length < 100) break;
  }
  return out;
}

async function run() {
  const yen = await ensureIssue(YEN_ISSUE_TITLE, YEN_BODY);
  const { issue } = await ensureIssue(ISSUE_TITLE, INSTRUCT_BODY);
  const comments = await listComments(issue.number);
  const go = affiGo(comments);
  const affi = go ? resolveAffi(comments) : { state: START, pointer: XM_POINTER, word: null, neo: 'no' };
  const pointer = go ? affi.pointer : XM_POINTER;
  const state = go ? affi.state : START;
  const neo = go ? affi.neo || 'no' : 'no';
  const body = commentBody(go, state, neo);
  const last = comments.length ? comments[comments.length - 1] : null;
  if (last && String(last.body || '').trim() === body.trim() && isTodayUtc(last.created_at)) {
    process.stdout.write(
      `${JSON.stringify({
        skipped: true,
        reason: 'already_today',
        number: issue.number,
        yen_number: yen.issue.number,
        yen_created: yen.created,
        overlay_filled: overlayStatusText().names.length,
        approved_yen: approvedYenSum(fs.readFileSync(path.join(__dirname, '../data/conversions.csv'), 'utf8')),
        pointer,
        affi: go,
        state,
        neo
      })}\n`
    );
    return;
  }
  await api(repoApi(`/issues/${issue.number}/comments`), {
    method: 'POST',
    body: { body }
  });
  process.stdout.write(
    `${JSON.stringify({
      skipped: false,
      number: issue.number,
      pointer,
      affi: go,
      state,
      word: affi.word || null,
      neo,
      yen_number: yen.issue.number,
      yen_created: yen.created,
      overlay_filled: overlayStatusText().names.length
    })}\n`
  );
}

function selfTest() {
  const body = commentBody(false);
  if (!body.startsWith(`hq-instruct: ${XM_POINTER}`)) throw new Error('pointer');
  if (!body.includes(RAW)) throw new Error('raw');
  if (!samePointer(body, false)) throw new Error('same true');
  if (samePointer('nope', false)) throw new Error('same false');
  const affi = instructBody(true, START);
  if (!affi.includes(AFFI_POINTER)) throw new Error('affi pointer');
  if (!affi.includes('hq-affi-state: sns_next')) throw new Error('affi state');
  if (!affi.includes('hq-affi-neo: no')) throw new Error('affi neo');
  if (!affi.includes('hq-affi-reply:')) throw new Error('affi reply');
  if (!affi.includes('未提携')) throw new Error('affi word');
  const ticketExist = instructBody(true, 'tenshoku_exist', 'no');
  if (!ticketExist.includes('置済み')) throw new Error('placed reply');
  const afterNeo = instructBody(true, 'a8_csv', 'placed');
  if (!afterNeo.includes('hq-affi-neo: placed')) throw new Error('neo placed line');
  if (!afterNeo.includes('G_hq_a8_csv.txt')) throw new Error('csv after neo');
  if (afterNeo.includes('G_hq_sns_ticket.txt') || afterNeo.includes('banner_10')) throw new Error('ticket overwrite');
  if (/\na8\.net/i.test(affi) || /crowdworks|AFFILIATE_LINKS/i.test(affi)) throw new Error('affi leak');
  if (/^\s*AFFI:\s*GO\b/m.test(affi) || /^\s*AFFI:\s*GO\b/m.test(INSTRUCT_BODY)) throw new Error('go loop');
  if (affiGo([])) throw new Error('go empty');
  if (!affiGo([{ user: { login: 'n' }, body: 'AFFI: GO' }])) throw new Error('go on');
  if (affiGo([
    { user: { login: 'n' }, body: 'AFFI: GO' },
    { user: { login: 'n' }, body: 'AFFI: STOP' }
  ])) throw new Error('go stop');
  if (affiGo([{ user: { login: 'github-actions[bot]' }, body: 'AFFI: GO' }])) throw new Error('bot go');
  if (/crowdworks|a8\.net|AFFILIATE_LINKS/i.test(body)) throw new Error('leak');
  if (/https?:\/\/example/i.test(body)) throw new Error('example url');
  if (!body.includes('overlay-filled:')) throw new Error('overlay line');
  if (!body.includes('approved-yen: 0')) throw new Error('yen line');
  if (approvedYenSum('date,source,program,clicks,cv,approved_yen,note\n2026-09-09,A8,all,1,0,15000,カタログ\n') !== 0) {
    throw new Error('catalog yen');
  }
  if (approvedYenSum('date,source,program,clicks,cv,approved_yen,note\n2026-08-27,A8,all,33,0,0,x\n') !== 0) {
    throw new Error('zero row');
  }
  if (YEN_ISSUE_TITLE !== 'Affiliate — 確定円') throw new Error('yen title');
  const instructYml = fs.readFileSync(path.join(__dirname, '../../.github/workflows/grok_bot_instruct.yml'), 'utf8');
  if (!instructYml.includes(`github.event.issue.title == '${ISSUE_TITLE}'`)) {
    throw new Error('instruct yml title');
  }
  const yenYml = fs.readFileSync(path.join(__dirname, '../../.github/workflows/affiliate_engine_a8_yen.yml'), 'utf8');
  if (!yenYml.includes(`github.event.issue.title == '${YEN_ISSUE_TITLE}'`)) {
    throw new Error('yen yml title');
  }
  if (/https?:\/\//i.test(YEN_BODY) || /https?:\/\//i.test(INSTRUCT_BODY)) throw new Error('issue url');
  if (!YEN_BODY.includes('A8_YEN:')) throw new Error('yen cmd');
  process.stdout.write('hq-instruct self-test ok\n');
}

if (process.argv.includes('--self-test')) {
  selfTest();
} else if (require.main === module) {
  run().catch((e) => {
    console.error(e.message || e);
    process.exit(1);
  });
}

module.exports = {
  ISSUE_TITLE,
  YEN_ISSUE_TITLE,
  POINTER,
  XM_POINTER,
  AFFI_POINTER,
  instructBody,
  commentBody,
  samePointer,
  affiGo,
  approvedYenSum,
  targetFor,
  findIssueByTitle,
  ensureIssue
};
