#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { ISSUE_TITLE: YEN_ISSUE_TITLE } = require('./apply-a8-yen');
const { overlayStatusText } = require('./overlay-keys');
const { START, fileFor } = require('./affi-step');
const { parseCSV, loadLinks } = require('./util');
const { pickDump, SITTING_POINTER, CSV_POINTER, XM_POINTER, GOAL_YEN } = require('./hq-earn');

const ISSUE_TITLE = 'Grok Bot — 指示';
const RAW_PREFIX =
  'https://raw.githubusercontent.com/fireworker011/Research/claude/setup-colab-comfyui-Eb9Lh/';
const AFFI_POINTER = fileFor(START);
const POINTER = SITTING_POINTER;
const RAW = `${RAW_PREFIX}${SITTING_POINTER}`;
const INSTRUCT_BODY =
  '指示役が毎日 `hq-instruct:` を書く。9/30まで高単価は overlay と確定円で dump を選ぶ。止めるなら `AFFI: STOP`。席が終わったら `完了`。1語分岐は返すな。Grok Bot は最新コメントの1ファイルだけ開け。人間は外部サイトだけ。';
const YEN_BODY =
  'A8 を自分で開いた日だけ1行。`A8_YEN: YYYY-MM-DD,A8,all,clicks,cv,yen,note`。URL・カンマ数字・カタログ円は拒否。開いていない日は書くな。';

function extraFor(picked) {
  if (picked.mode === 'sitting') {
    return '1語分岐で次ファイルへ進むな。席が終わったら人間は `完了` だけ。overlay が空なら次に進まない。ENTRY は出すな。';
  }
  if (picked.mode === 'measure' || picked.mode === 'done') {
    return '人間の仕事は A8 を開いた日の A8_YEN だけ。プロフィールのリンクを外すな。ENTRY は出すな。';
  }
  return 'ENTRY は出すな。';
}

function instructBody(picked) {
  const pointer = picked.pointer;
  const lines = [
    `hq-instruct: ${pointer}`,
    `${RAW_PREFIX}${pointer}`,
    `この1ファイルだけ開け。結合するな。remain / n10 は開けるな。Cursor を起こすな。Threads cron は戻すな。${extraFor(picked)} boot に戻ってループするな。`,
    `hq-gate: ${picked.gate}`
  ];
  if (picked.reply && picked.reply !== '(none)') {
    lines.push(`hq-affi-reply: ${picked.reply}`);
  }
  return lines.join('\n');
}

function samePointer(body, pointer) {
  return String(body || '').includes(`hq-instruct: ${pointer}`);
}

function overlayNow() {
  return overlayStatusText(loadLinks());
}

function pickNow(stop = false, overlay = overlayNow(), yen = yenStatus()) {
  return pickDump({
    stop: !!stop,
    overlayCount: overlay.names.length,
    approvedYen: yen.approved_yen
  });
}

function commentBody(stop = false) {
  const overlay = overlayNow();
  const yen = yenStatus();
  const picked = pickNow(stop, overlay, yen);
  return `${instructBody(picked)}\n${overlay.text.trim()}\n${yen.text}`;
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

function yenStatus(csvPath = path.join(__dirname, '../data/conversions.csv')) {
  try {
    if (!fs.existsSync(csvPath)) return { approved_yen: null, text: 'approved-yen: unknown' };
    const n = approvedYenSum(fs.readFileSync(csvPath, 'utf8'));
    if (!Number.isFinite(n)) return { approved_yen: null, text: 'approved-yen: unknown' };
    return { approved_yen: n, text: `approved-yen: ${n}` };
  } catch (_) {
    return { approved_yen: null, text: 'approved-yen: unknown' };
  }
}

function yenStatusText() {
  return yenStatus().text;
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

function affiStop(comments) {
  let stop = false;
  for (const c of comments || []) {
    if ((c.user?.login || '') === 'github-actions[bot]') continue;
    for (const line of String(c.body || '').split(/\r?\n/)) {
      if (/^\s*AFFI:\s*STOP\b/i.test(line)) stop = true;
      else if (/^\s*AFFI:\s*GO\b/i.test(line)) stop = false;
    }
  }
  return stop;
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
  const stop = affiStop(comments);
  const overlay = overlayNow();
  const yenNow = yenStatus();
  const picked = pickNow(stop, overlay, yenNow);
  const body = commentBody(stop);
  const last = comments.length ? comments[comments.length - 1] : null;
  if (last && String(last.body || '').trim() === body.trim() && isTodayUtc(last.created_at)) {
    process.stdout.write(
      `${JSON.stringify({
        skipped: true,
        reason: 'already_today',
        number: issue.number,
        yen_number: yen.issue.number,
        yen_created: yen.created,
        overlay_filled: overlay.names.length,
        approved_yen: yenNow.approved_yen,
        pointer: picked.pointer,
        gate: picked.gate,
        mode: picked.mode,
        stop
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
      pointer: picked.pointer,
      gate: picked.gate,
      mode: picked.mode,
      stop,
      yen_number: yen.issue.number,
      yen_created: yen.created,
      overlay_filled: overlay.names.length,
      approved_yen: yenNow.approved_yen
    })}\n`
  );
}

function selfTest() {
  const body = commentBody(false);
  if (!body.startsWith(`hq-instruct: ${SITTING_POINTER}`)) throw new Error('pointer');
  if (!body.includes(RAW)) throw new Error('raw');
  if (!samePointer(body, SITTING_POINTER)) throw new Error('same true');
  if (samePointer('nope', SITTING_POINTER)) throw new Error('same false');
  if (!body.includes('hq-gate: sitting')) throw new Error('sitting gate');
  if (!body.includes('hq-affi-reply: 完了')) throw new Error('sitting reply');
  if (body.includes(`hq-instruct: ${AFFI_POINTER}`)) throw new Error('no 1word default');
  const xm = instructBody(pickDump({ stop: true }));
  if (!xm.includes(XM_POINTER)) throw new Error('stop pointer');
  if (!xm.includes('hq-gate: xm')) throw new Error('xm gate');
  const measure = instructBody(pickDump({ overlayCount: 1, approvedYen: 0 }));
  if (!measure.includes(CSV_POINTER)) throw new Error('measure pointer');
  if (!measure.includes('hq-gate: measure')) throw new Error('measure gate');
  if (measure.includes('hq-affi-reply:')) throw new Error('measure reply');
  const done = instructBody(pickDump({ overlayCount: 1, approvedYen: GOAL_YEN }));
  if (!done.includes('hq-gate: freeze')) throw new Error('done gate');
  if (/^\s*AFFI:\s*GO\b/m.test(body) || /^\s*AFFI:\s*GO\b/m.test(INSTRUCT_BODY)) throw new Error('go loop');
  if (affiGo([])) throw new Error('go empty');
  if (!affiGo([{ user: { login: 'n' }, body: 'AFFI: GO' }])) throw new Error('go on');
  if (affiStop([])) throw new Error('stop empty');
  if (!affiStop([{ user: { login: 'n' }, body: 'AFFI: STOP' }])) throw new Error('stop on');
  if (affiStop([
    { user: { login: 'n' }, body: 'AFFI: STOP' },
    { user: { login: 'n' }, body: 'AFFI: GO' }
  ])) throw new Error('go undoes stop');
  if (affiStop([{ user: { login: 'github-actions[bot]' }, body: 'AFFI: STOP' }])) throw new Error('bot stop');
  if (affiGo([
    { user: { login: 'n' }, body: 'AFFI: GO' },
    { user: { login: 'n' }, body: 'AFFI: STOP' }
  ])) throw new Error('go stop');
  if (affiGo([{ user: { login: 'github-actions[bot]' }, body: 'AFFI: GO' }])) throw new Error('bot go');
  if (/crowdworks|a8\.net|AFFILIATE_LINKS/i.test(body)) throw new Error('leak');
  if (/https?:\/\/example/i.test(body)) throw new Error('example url');
  if (!body.includes('overlay-filled:')) throw new Error('overlay line');
  if (!body.includes('approved-yen: 0')) throw new Error('yen line');
  const prevOverlay = process.env.AFFILIATE_LINKS_JSON;
  process.env.AFFILIATE_LINKS_JSON = JSON.stringify({
    転職_neo: 'https://example.invalid/neo',
    申込_auひかり: 'https://example.invalid/au'
  });
  const filled = commentBody(false);
  if (!filled.includes('overlay-filled: 1')) throw new Error('secret overlay count');
  if (!filled.includes('転職_neo')) throw new Error('secret overlay neo');
  if (!filled.includes(CSV_POINTER)) throw new Error('secret routes csv');
  if (filled.includes(SITTING_POINTER) && filled.includes(`hq-instruct: ${SITTING_POINTER}`)) {
    throw new Error('secret still sitting');
  }
  if (/申込_auひかり/.test(filled)) throw new Error('au in overlay');
  if (/https?:\/\/example/i.test(filled)) throw new Error('secret url');
  const stoppedFilled = commentBody(true);
  if (!stoppedFilled.includes(`hq-instruct: ${XM_POINTER}`)) throw new Error('stop wins overlay');
  if (prevOverlay === undefined) delete process.env.AFFILIATE_LINKS_JSON;
  else process.env.AFFILIATE_LINKS_JSON = prevOverlay;
  if (yenStatus('/no/such/conversions.csv').text !== 'approved-yen: unknown') throw new Error('yen missing');
  if (yenStatus('/no/such/conversions.csv').approved_yen !== null) throw new Error('yen missing null');
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
  if (!instructYml.includes('affiliate-engine/data/conversions.csv')) throw new Error('instruct csv path');
  if (!instructYml.includes('hq-earn.js')) throw new Error('instruct earn path');
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
  SITTING_POINTER,
  instructBody,
  commentBody,
  samePointer,
  affiGo,
  affiStop,
  approvedYenSum,
  yenStatus,
  pickNow,
  findIssueByTitle,
  ensureIssue
};
