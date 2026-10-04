#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { workPath, readText, writeText, loadCapability, loadFacts, nowIso, dateJst, categoryById } = require('./util');
const { ISSUE_TITLE, loadCommander, saveCommander, isNotifyComment, parseCommand, applyKill } = require('./commander');
const { loadQueue, saveQueue, findJob, upsertJob, newJobRecord, transition } = require('./queue');
const { parseJobText, fetchPublicJob } = require('./intake');
const { qualify } = require('./qualify');
const { draftApplication } = require('./apply-draft');
const { draftReply } = require('./reply-draft');
const { buildBrief, enrichBrief } = require('./brief');
const { makeDeliverable, qaDeliverableText } = require('./make');
const { buildDeliveryDoc } = require('./deliver');
const { buildProfileDraft } = require('./profile-draft');
const { recordPaid, ledgerTotal } = require('./ledger');
const { funnel } = require('./funnel');
const { deskLines } = require('./desk');
const { writeToday } = require('./report');
const github = require('./github');

const CHEAT_SHEET = [
  'CW 司令塔。人間は契約・外部案内誘導・納品だけ。ほかは Grok（応募・下書き・完成品）。コメント1行目 `CW: <コマンド> <仕事ID>`。',
  '',
  '| 行 | 意味 |',
  '|---|---|',
  '| `CW: JOB <id>` + 公開文 | 取込 → 資格判定 → 応募稿（本文が無ければ公開ページを1回読む） |',
  '| `CW: SENT <id>` | 応募稿を貼って送った（受注可否は人間） |',
  '| `CW: SKIP <id>` | 見送り |',
  '| `CW: MSG <id>` + 相手の文 | 定型返信の下書き |',
  '| `CW: CONTRACT <id>` + メモ | 契約した → BRIEF（業務の把握・素材依頼文） |',
  '| `CW: MATERIAL <id>` + 素材 | 素材を足す |',
  '| `CW: MAKE <id>` (+素材) | Grok 用プロンプト（完成品は `CW: DRAFT`。Anthropic 不要） |',
  '| `CW: DRAFT <id>` + 完成品本文 | Grok / 人間が本文を貼る → QA → 納品パッケージ |',
  '| `CW: REVISE <id>` + 修正依頼 | 反映版のプロンプト → また `CW: DRAFT` |',
  '| `CW: DELIVERED <id>` | 納品ボタンを押した |',
  '| `CW: PAID <id> <円>` | 画面で確定を見た日だけ |',
  '| `CW: REJECT <id>` | 不採用・失注 |',
  '| `CW: PROFILE` | 自己PR の下書き |',
  '| `CW: HALT` / `CW: PAPER_ONLY` | 止める / 既定 |',
  '',
  '`cw-*:` で始まるコメントは機械の告知。数字は発明しない。カタログ円は確定ではない。'
].join('\n');

function jobDir(id) {
  return workPath('jobs', String(id));
}

function listMaterials(id) {
  const dir = path.join(jobDir(id), 'materials');
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith('.md'))
    .sort()
    .map((f) => readText(path.join(dir, f), ''));
}

function appendMaterial(id, text, now) {
  const dir = path.join(jobDir(id), 'materials');
  const n = listMaterials(id).length + 1;
  writeText(path.join(dir, `${String(n).padStart(2, '0')}.md`), `<!-- ${nowIso(now)} -->\n${text}`);
  return n;
}

function fence(text) {
  return ['```', String(text || '').replace(/```/g, "'''"), '```'].join('\n');
}

function ctxLoad() {
  return { capability: loadCapability(), facts: loadFacts(), commander: loadCommander(), queue: loadQueue() };
}

async function handleJob(cmd, ctx, now) {
  const { capability, facts, commander } = ctx;
  let queue = ctx.queue;
  const id = cmd.id;
  const existing = findJob(queue, id);
  if (existing && !['scouted', 'rejected', 'qualified', 'drafted'].includes(existing.status)) {
    return { kind: 'note', id, body: `${id} は既に \`${existing.status}\`。JOB で上書きしない。`, queue };
  }
  let text = cmd.payload;
  let fetched = null;
  if (!text) {
    if (capability?.public_fetch?.enabled === false) return { kind: 'note', id, body: `${id}: 公開文を貼って \`CW: JOB ${id}\` をもう一度。`, queue };
    fetched = await fetchPublicJob(id);
    if (!fetched.ok) return { kind: 'note', id, body: `${id}: 公開ページを読めなかった（${fetched.reason}）。公開文を貼って \`CW: JOB ${id}\` をもう一度。`, queue };
    text = fetched.text;
  }
  const parsed = parseJobText(id, text, capability, { category: cmd.opts.category, applied: cmd.opts.applied, title: fetched?.title || undefined });
  const verdict = qualify(parsed, { capability, facts, commander, queue });
  let job = newJobRecord(parsed, verdict, now);
  writeText(path.join(jobDir(id), 'JOB.md'), `# ${id} ${job.title}\n\n取込: ${nowIso(now)}${fetched ? '（公開ページ1回読み）' : '（人間が貼った公開文）'}\n\n${text}`);
  if (!verdict.ok) {
    queue = upsertJob(queue, job, now);
    const hint = verdict.reasons.includes('category_unknown')
      ? `\nカテゴリが取れない。合うなら \`CW: JOB ${id} category=<id>\` で上書き（${(capability.categories || []).map((c) => c.id).join(' / ')}）。`
      : '';
    return { kind: 'desk', id, body: `${id} は資格判定で落ちた: ${verdict.reasons.join(', ')}${verdict.warnings.length ? `（注意: ${verdict.warnings.join(', ')}）` : ''}${hint}`, queue };
  }
  const draft = await draftApplication(job, { facts, capability });
  writeText(path.join(jobDir(id), 'APPLY.md'), `# APPLY — ${id}\n\n${draft.text}`);
  const t = transition(job, 'DRAFTED', now);
  job = t.ok ? t.job : job;
  queue = upsertJob(queue, job, now);
  const cat = categoryById(capability, job.category);
  const body = [
    `${id} ${job.title} — ${cat ? cat.label : job.category}（優先度 ${job.priority}${job.deadline ? `・期限 ${job.deadline}` : ''}）`,
    job.warnings.length ? `注意: ${job.warnings.join(', ')}` : '',
    draft.check.needs_human ? `「（人間が書く）」が ${draft.check.needs_human} 箇所。氏名・年齢などは人間が埋める。` : '',
    draft.check.ok ? '' : `検品: ${draft.check.issues.join(', ')}`,
    '',
    '応募稿（貼って送る。送ったら `CW: SENT ' + id + '`、見送りは `CW: SKIP ' + id + '`）:',
    fence(draft.text)
  ]
    .filter((l) => l !== '')
    .join('\n');
  return { kind: 'apply', id, body, queue };
}

function handleTransition(cmd, ctx, now, event, okText) {
  const job = findJob(ctx.queue, cmd.id);
  if (!job) return { kind: 'note', id: cmd.id, body: `${cmd.id} はキューに無い。先に \`CW: JOB ${cmd.id}\`。`, queue: ctx.queue };
  const t = transition(job, event, now);
  if (!t.ok) return { kind: 'note', id: cmd.id, body: `${cmd.id}: ${t.reason}。今は \`${job.status}\`。`, queue: ctx.queue };
  return { kind: 'note', id: cmd.id, body: okText(t.job), queue: upsertJob(ctx.queue, t.job, now), job: t.job };
}

async function handleContract(cmd, ctx, now) {
  const r = handleTransition(cmd, ctx, now, 'CONTRACT', (j) => `${j.id} を契約済みにした。`);
  if (!r.job) return r;
  if (cmd.payload) appendMaterial(cmd.id, cmd.payload, now);
  const materials = listMaterials(cmd.id).join('\n\n');
  let brief = buildBrief(r.job, { capability: ctx.capability, contractNotes: cmd.payload, materials, now });
  brief = await enrichBrief(brief, r.job, { materials });
  writeText(path.join(jobDir(cmd.id), 'BRIEF.md'), brief.text);
  const body = [
    `${cmd.id} を契約済みにした。初稿の目安 ${brief.due}。`,
    brief.missing.length ? `不足素材 ${brief.missing.length} 件。BRIEF の依頼文を貼り、届いたら \`CW: MAKE ${cmd.id}\` に素材を貼る。` : `素材は揃っている。\`CW: MAKE ${cmd.id}\` で完成品を作る。`,
    '',
    fence(brief.text)
  ].join('\n');
  return { ...r, kind: 'brief', body };
}

function handleMsg(cmd, ctx, now) {
  const job = findJob(ctx.queue, cmd.id);
  if (!job) return { kind: 'note', id: cmd.id, body: `${cmd.id} はキューに無い。先に \`CW: JOB ${cmd.id}\`。`, queue: ctx.queue };
  if (!cmd.payload) return { kind: 'note', id: cmd.id, body: `${cmd.id}: 相手の文を2行目以降に貼る。`, queue: ctx.queue };
  const reply = draftReply(cmd.payload, { job, facts: ctx.facts, capability: ctx.capability, now });
  const n = Number(job.messages || 0) + 1;
  writeText(path.join(jobDir(cmd.id), 'messages', `${String(n).padStart(2, '0')}_in.md`), cmd.payload);
  writeText(path.join(jobDir(cmd.id), 'messages', `${String(n).padStart(2, '0')}_reply.md`), reply.text);
  const next = { ...job, messages: n, updated_at: nowIso(now) };
  const body = [
    `${cmd.id} 返信の下書き（分類: ${reply.intent}）${reply.check.needs_human ? `。「（人間が書く）」${reply.check.needs_human} 箇所は人間が判断` : ''}:`,
    fence(reply.text),
    '契約の申し出なら `CW: CONTRACT ' + cmd.id + '`。断りなら `CW: REJECT ' + cmd.id + '`。'
  ].join('\n');
  return { kind: 'reply', id: cmd.id, body, queue: upsertJob(ctx.queue, next, now) };
}

function handleMaterial(cmd, ctx, now) {
  const job = findJob(ctx.queue, cmd.id);
  if (!job) return { kind: 'note', id: cmd.id, body: `${cmd.id} はキューに無い。`, queue: ctx.queue };
  if (!cmd.payload) return { kind: 'note', id: cmd.id, body: `${cmd.id}: 素材を2行目以降に貼る。`, queue: ctx.queue };
  const n = appendMaterial(cmd.id, cmd.payload, now);
  return { kind: 'note', id: cmd.id, body: `${cmd.id}: 素材 ${n} 件目を保存した。揃ったら \`CW: MAKE ${cmd.id}\`。`, queue: ctx.queue };
}

function finalizeQa(cmd, job, ctx, now, result, { revision = false } = {}) {
  const version = Number(job.revisions || 0) + 1;
  const outDir = path.join(jobDir(cmd.id), 'deliverables', `v${version}`);
  const files = [];
  const main = path.join(outDir, `deliverable.${result.ext}`);
  writeText(main, result.text);
  files.push(path.relative(workPath(), main));
  if (result.ext === 'md') {
    const txt = path.join(outDir, 'deliverable.txt');
    writeText(txt, result.text.replace(/^#+\s*/gm, '').replace(/\*\*/g, ''));
    files.push(path.relative(workPath(), txt));
  }
  writeText(path.join(outDir, 'QA.md'), `# QA — ${cmd.id} v${version}\n\n- result: ${result.qa.ok ? 'pass' : 'fail'}\n- chars: ${result.qa.chars}\n- issues: ${result.qa.issues.join(', ') || 'none'}\n- warnings: ${result.qa.warnings.join(', ') || 'none'}`);
  if (!result.qa.ok) {
    const fail = transition(job, 'QA_FAIL', now);
    job = fail.ok ? fail.job : job;
    return {
      kind: 'qa',
      id: cmd.id,
      body: `${cmd.id} v${version}: QA 不合格 — ${result.qa.issues.join(', ')}。直した本文を \`CW: DRAFT ${cmd.id}\`、または素材を足して \`CW: MAKE ${cmd.id}\`（下書きは ${files[0]}）。`,
      queue: upsertJob(ctx.queue, job, now)
    };
  }
  const pass = transition(job, 'QA_PASS', now);
  job = pass.ok ? pass.job : job;
  const deliveryDoc = buildDeliveryDoc(job, { capability: ctx.capability, files, qa: result.qa, revision: revision ? version - 1 : 0, humanToolRequired: result.human_tool_required });
  writeText(path.join(outDir, 'DELIVERY.md'), deliveryDoc);
  const preview = result.text.slice(0, 400);
  const body = [
    `${cmd.id} v${version}: QA 合格（${result.qa.chars} 文字）。${result.human_tool_required ? '編集計画まで。動画は人間のツールで仕上げる。' : ''}`,
    `ファイル: ${files.join(' / ')}（このリポジトリ内）。納品メッセージとチェックは ${path.relative(workPath(), path.join(outDir, 'DELIVERY.md'))}。`,
    '',
    '冒頭:',
    fence(preview + (result.text.length > 400 ? '\n…' : '')),
    `納品ボタンを押したら \`CW: DELIVERED ${cmd.id}\`。修正依頼が来たら \`CW: REVISE ${cmd.id}\` + 依頼文。`
  ].join('\n');
  return { kind: 'deliver', id: cmd.id, body, queue: upsertJob(ctx.queue, job, now) };
}

async function handleMake(cmd, ctx, now, { revision = false } = {}) {
  const job0 = findJob(ctx.queue, cmd.id);
  if (!job0) return { kind: 'note', id: cmd.id, body: `${cmd.id} はキューに無い。`, queue: ctx.queue };
  if (revision && !cmd.payload) return { kind: 'note', id: cmd.id, body: `${cmd.id}: 修正依頼の文を2行目以降に貼る。`, queue: ctx.queue };
  if (!revision && cmd.payload) appendMaterial(cmd.id, cmd.payload, now);
  const start = transition(job0, 'MAKE', now);
  if (!start.ok) return { kind: 'note', id: cmd.id, body: `${cmd.id}: ${start.reason}。先に \`CW: CONTRACT ${cmd.id}\`。`, queue: ctx.queue };
  let job = start.job;
  const materials = listMaterials(cmd.id).join('\n\n');
  let briefText = readText(path.join(jobDir(cmd.id), 'BRIEF.md'), '');
  const brief = buildBrief(job, { capability: ctx.capability, materials, now });
  if (!briefText) {
    briefText = brief.text;
    writeText(path.join(jobDir(cmd.id), 'BRIEF.md'), briefText);
  }
  const result = await makeDeliverable(job, { capability: ctx.capability, brief, briefText, materials, revisionRequest: revision ? cmd.payload : null });
  if (result.blocked === 'await_grok') {
    writeText(path.join(jobDir(cmd.id), 'GROK_PROMPT.md'), result.grokPrompt);
    const shown = String(result.grokPrompt || '').slice(0, 12000);
    return {
      kind: 'make',
      id: cmd.id,
      body: [
        `${cmd.id}: Anthropic API は使わない。Grok Bot（HQ clone ではない別会話）が完成品を書く。`,
        `プロンプト全文: jobs/${cmd.id}/GROK_PROMPT.md`,
        '',
        fence(shown),
        '',
        `書けたら 1 行目 \`CW: DRAFT ${cmd.id}\`、2 行目以降に成果物本体。発明しない。`
      ].join('\n'),
      queue: upsertJob(ctx.queue, job, now)
    };
  }
  if (result.blocked) {
    const fail = transition(job, 'QA_FAIL', now);
    job = fail.ok ? { ...fail.job, last_block: result.blocked } : job;
    return { kind: 'qa', id: cmd.id, body: `${cmd.id}: 完成品を作れなかった（${result.blocked}）。Grok に \`CW: DRAFT ${cmd.id}\` で本文を貼る。`, queue: upsertJob(ctx.queue, job, now) };
  }
  return finalizeQa(cmd, job, ctx, now, result, { revision });
}

function handleDraft(cmd, ctx, now) {
  const job0 = findJob(ctx.queue, cmd.id);
  if (!job0) return { kind: 'note', id: cmd.id, body: `${cmd.id} はキューに無い。`, queue: ctx.queue };
  if (!cmd.payload) return { kind: 'note', id: cmd.id, body: `${cmd.id}: 完成品の本文を2行目以降に貼る（\`CW: DRAFT ${cmd.id}\`）。`, queue: ctx.queue };
  let job = job0;
  if (job.status !== 'making') {
    const start = transition(job, 'MAKE', now);
    if (!start.ok) return { kind: 'note', id: cmd.id, body: `${cmd.id}: ${start.reason}。先に \`CW: CONTRACT ${cmd.id}\` と \`CW: MAKE ${cmd.id}\`。`, queue: ctx.queue };
    job = start.job;
  }
  const materials = listMaterials(cmd.id).join('\n\n');
  const brief = buildBrief(job, { capability: ctx.capability, materials, now });
  const result = qaDeliverableText(job, { capability: ctx.capability, brief, materials, text: cmd.payload });
  return finalizeQa(cmd, job, ctx, now, result, { revision: Number(job.revisions || 0) > 0 });
}

function handlePaid(cmd, ctx, now) {
  const yenRaw = cmd.extra[0];
  const note = cmd.extra.slice(1).join(' ');
  const v = recordPaid({ date: dateJst(now), jobId: cmd.id, yenRaw, note });
  if (!v.ok) return { kind: 'note', id: cmd.id, body: `${cmd.id}: PAID を拒否（${v.reason}）。形は \`CW: PAID <id> <整数円> <メモ>\`。カタログ・見込み・カンマ数字は書くな。`, queue: ctx.queue };
  const r = handleTransition(cmd, ctx, now, 'PAID', (j) => `${j.id} 確定 ${v.row.yen} 円を台帳に書いた（合計 ${v.total} 円）。`);
  if (r.job) r.job.confirmed_yen = v.row.yen;
  return { ...r, queue: r.job ? upsertJob(r.queue, { ...r.job, confirmed_yen: v.row.yen }, now) : r.queue };
}

function handleProfile(ctx) {
  const f = funnel(ctx.queue, { ledgerYen: ledgerTotal(), capability: ctx.capability });
  const p = buildProfileDraft({ facts: ctx.facts, capability: ctx.capability, funnel: f });
  writeText(workPath('profile', 'PROFILE.md'), `# PROFILE 下書き\n\n${p.text}`);
  return { kind: 'profile', id: null, body: `自己PR の下書き（貼る前に「（人間が書く）」を埋める。無い実績は足すな）:\n${fence(p.text)}`, queue: ctx.queue };
}

async function dispatch(cmd, ctx, now) {
  switch (cmd.type) {
    case 'HALT':
    case 'PAPER_ONLY': {
      const commander = applyKill(ctx.commander, { command: cmd.type, source: 'issue', reason: 'issue_comment', now });
      return { kind: 'desk', id: null, body: `command を ${cmd.type} にした。`, queue: ctx.queue, commander };
    }
    case 'JOB':
      return handleJob(cmd, ctx, now);
    case 'SKIP':
      return handleTransition(cmd, ctx, now, 'SKIP', (j) => `${j.id} を見送りにした。`);
    case 'SENT':
      return handleTransition(cmd, ctx, now, 'SENT', (j) => `${j.id} を送信済みにした。返事が来たら \`CW: MSG ${j.id}\` + 相手の文。契約なら \`CW: CONTRACT ${j.id}\`。`);
    case 'MSG':
      return handleMsg(cmd, ctx, now);
    case 'CONTRACT':
      return handleContract(cmd, ctx, now);
    case 'MATERIAL':
      return handleMaterial(cmd, ctx, now);
    case 'MAKE':
      return handleMake(cmd, ctx, now);
    case 'DRAFT':
      return handleDraft(cmd, ctx, now);
    case 'REVISE':
      return handleMake(cmd, ctx, now, { revision: true });
    case 'DELIVERED':
      return handleTransition(cmd, ctx, now, 'DELIVERED', (j) => `${j.id} を納品済みにした。報酬確定を画面で見たら \`CW: PAID ${j.id} <整数円>\`。`);
    case 'PAID':
      return handlePaid(cmd, ctx, now);
    case 'REJECT':
      return handleTransition(cmd, ctx, now, 'REJECT', (j) => `${j.id} を失注にした。`);
    case 'PROFILE':
      return handleProfile(ctx);
    case 'DESK':
      return { kind: 'desk', id: null, body: 'デスクを出す。', queue: ctx.queue };
    default: {
      const _never = cmd.type;
      return { kind: 'note', id: null, body: `unknown command ${_never}`, queue: ctx.queue };
    }
  }
}

function composeComment(result, ctx, now) {
  const f = funnel(result.queue, { ledgerYen: ledgerTotal(), capability: ctx.capability });
  const desk = deskLines({ commander: result.commander || ctx.commander, queue: result.queue, capability: ctx.capability, funnel: f, ledgerYen: ledgerTotal(), now });
  const head = `cw-${result.kind}: ${result.id || '-'}`;
  return `${head}\n${result.body}\n\n---\n${desk.join('\n')}`;
}

async function handleComment({ body, login, now = new Date(), persist = true }) {
  if (isNotifyComment(body)) return { skipped: true, reason: 'notify-comment' };
  if (login === 'github-actions[bot]') return { skipped: true, reason: 'actions-bot' };
  const cmd = parseCommand(body);
  if (!cmd) return { skipped: true, reason: 'no_command' };
  const ctx = ctxLoad();
  if (cmd.error) {
    const result = { kind: 'note', id: null, body: `\`CW: ${cmd.type}\` には仕事 ID が要る。例: \`CW: ${cmd.type} 13406725\``, queue: ctx.queue };
    return { skipped: false, cmd, result, comment: composeComment(result, ctx, now) };
  }
  const result = await dispatch(cmd, ctx, now);
  if (persist) {
    saveQueue(result.queue);
    if (result.commander) saveCommander(result.commander);
    writeToday(now);
  }
  return { skipped: false, cmd, result, comment: composeComment(result, ctx, now) };
}

function readEvent() {
  const p = process.env.GITHUB_EVENT_PATH;
  if (p && fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, 'utf8'));
  return null;
}

async function bootstrap(now) {
  const ctx = ctxLoad();
  saveCommander(ctx.commander);
  saveQueue(ctx.queue);
  writeToday(now);
  if (!process.env.GITHUB_TOKEN || !process.env.GITHUB_REPOSITORY) return { skipped: true, reason: 'no_token_bootstrap' };
  const { issue, created } = await github.ensureIssue(ISSUE_TITLE, CHEAT_SHEET);
  const result = { kind: 'desk', id: null, body: created ? '司令塔 Issue を立てた。1行目 `CW: JOB <id>` から。' : 'デスク。', queue: ctx.queue };
  await github.postComment(issue.number, composeComment(result, ctx, now));
  return { skipped: false, bootstrap: true, number: issue.number, created };
}

async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes('--dry-run');
  const now = new Date();
  const argComment = args.includes('--comment') ? args[args.indexOf('--comment') + 1] : null;
  if (argComment) {
    const out = await handleComment({ body: argComment, login: 'cli', now, persist: !dryRun });
    console.log(JSON.stringify({ skipped: out.skipped, reason: out.reason, kind: out.result?.kind, id: out.result?.id }));
    if (out.comment) console.log(out.comment);
    return;
  }
  const event = readEvent();
  const eventName = process.env.GITHUB_EVENT_NAME || '';
  if (!event || eventName === 'workflow_dispatch' || eventName === 'push' || !event.comment) {
    const out = await bootstrap(now);
    console.log(JSON.stringify(out));
    return;
  }
  if (event.issue?.title !== ISSUE_TITLE) {
    console.log(JSON.stringify({ skipped: true, reason: 'not_cw_issue' }));
    return;
  }
  const out = await handleComment({ body: event.comment?.body || '', login: event.comment?.user?.login || '', now, persist: !dryRun });
  if (!out.skipped && !dryRun && process.env.GITHUB_TOKEN) {
    await github.postComment(event.issue.number, out.comment);
  }
  console.log(JSON.stringify({ skipped: out.skipped, reason: out.reason, type: out.cmd?.type, kind: out.result?.kind, id: out.result?.id }));
}

module.exports = { CHEAT_SHEET, handleComment, dispatch, composeComment, bootstrap, jobDir, listMaterials };

if (require.main === module) {
  main().catch((err) => {
    console.error(`apply-commander-comment failed: ${err.message}`);
    process.exit(1);
  });
}
