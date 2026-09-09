#!/usr/bin/env node
'use strict';

const { ISSUE_TITLE: YEN_ISSUE_TITLE } = require('./apply-a8-yen');
const { overlayStatusText } = require('./overlay-keys');

const ISSUE_TITLE = 'Grok Bot — 指示';
const RAW_PREFIX =
  'https://raw.githubusercontent.com/fireworker011/Research/claude/setup-colab-comfyui-Eb9Lh/';
const XM_POINTER = 'xm-trade-engine/docs/grok-bots/G_xm_trade.txt';
const AFFI_POINTER = 'affiliate-engine/docs/grok-bots/dump/G_hq_sns_next.txt';
const POINTER = XM_POINTER;
const RAW = `${RAW_PREFIX}${XM_POINTER}`;
const INSTRUCT_BODY =
  '指示役が毎日 `hq-instruct:` を書く。高単価を進めるならコメントを `AFFI: GO` だけの行にする。止めるなら `AFFI: STOP`。Grok Bot は最新コメントの1ファイルだけ開け。人間は外部サイトだけ。';
const YEN_BODY =
  'A8 を自分で開いた日だけ1行。`A8_YEN: YYYY-MM-DD,A8,all,clicks,cv,yen,note`。URL・カンマ数字・カタログ円は拒否。開いていない日は書くな。';

function targetFor(go) {
  return go ? AFFI_POINTER : XM_POINTER;
}

function instructBody(go = false) {
  const pointer = targetFor(go);
  const extra = go
    ? '人間が返した1語の次ファイルへ進め。ENTRY は出すな。'
    : 'ENTRY は出すな。';
  return [
    `hq-instruct: ${pointer}`,
    `${RAW_PREFIX}${pointer}`,
    `この1ファイルだけ開け。結合するな。remain / n10 は開けるな。Cursor を起こすな。Threads cron は戻すな。${extra} boot に戻ってループするな。`
  ].join('\n');
}

function samePointer(body, go = false) {
  return String(body || '').includes(`hq-instruct: ${targetFor(go)}`);
}

function commentBody(go = false) {
  return `${instructBody(go)}\n${overlayStatusText().text.trim()}`;
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
  const pointer = targetFor(go);
  const body = commentBody(go);
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
        pointer,
        affi: go
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
  const affi = instructBody(true);
  if (!affi.includes(AFFI_POINTER)) throw new Error('affi pointer');
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
  if (YEN_ISSUE_TITLE !== 'Affiliate — 確定円') throw new Error('yen title');
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
  targetFor,
  findIssueByTitle,
  ensureIssue
};
