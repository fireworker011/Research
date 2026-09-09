#!/usr/bin/env node
'use strict';

const ISSUE_TITLE = 'Grok Bot — 指示';
const POINTER = 'xm-trade-engine/docs/grok-bots/G_xm_trade.txt';
const RAW =
  'https://raw.githubusercontent.com/fireworker011/Research/claude/setup-colab-comfyui-Eb9Lh/xm-trade-engine/docs/grok-bots/G_xm_trade.txt';

function instructBody() {
  return [
    `hq-instruct: ${POINTER}`,
    RAW,
    'この1ファイルだけ開け。結合するな。remain / n10 は開けるな。Cursor を起こすな。Threads cron は戻すな。ENTRY は出すな。boot に戻ってループするな。'
  ].join('\n');
}

function samePointer(body) {
  return String(body || '').includes(`hq-instruct: ${POINTER}`);
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

async function ensureIssue() {
  const repo = process.env.GITHUB_REPOSITORY;
  const q = encodeURIComponent(`repo:${repo} is:issue in:title "${ISSUE_TITLE}"`);
  const search = await api(`https://api.github.com/search/issues?q=${q}&per_page=10`);
  const hit = (search.items || []).find((i) => i.title === ISSUE_TITLE);
  if (hit) return hit;
  return api(repoApi('/issues'), {
    method: 'POST',
    body: {
      title: ISSUE_TITLE,
      body: '指示役が毎日 `hq-instruct:` を書く。Grok Bot は最新コメントの1ファイルだけ開け。人間は外部サイトだけ。'
    }
  });
}

async function latestComment(issueNumber) {
  const comments = await api(repoApi(`/issues/${issueNumber}/comments?per_page=100`));
  if (!Array.isArray(comments) || !comments.length) return null;
  return comments[comments.length - 1];
}

async function run() {
  const issue = await ensureIssue();
  const last = await latestComment(issue.number);
  if (last && samePointer(last.body) && isTodayUtc(last.created_at)) {
    process.stdout.write(`${JSON.stringify({ skipped: true, reason: 'already_today', number: issue.number })}\n`);
    return;
  }
  await api(repoApi(`/issues/${issue.number}/comments`), {
    method: 'POST',
    body: { body: instructBody() }
  });
  process.stdout.write(`${JSON.stringify({ skipped: false, number: issue.number, pointer: POINTER })}\n`);
}

function selfTest() {
  const body = instructBody();
  if (!body.startsWith(`hq-instruct: ${POINTER}`)) throw new Error('pointer');
  if (!body.includes(RAW)) throw new Error('raw');
  if (!samePointer(body)) throw new Error('same true');
  if (samePointer('nope')) throw new Error('same false');
  if (/crowdworks|a8\.net|AFFILIATE_LINKS/i.test(body)) throw new Error('leak');
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

module.exports = { ISSUE_TITLE, POINTER, instructBody, samePointer };
