'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');

process.env.CW_WORK_DIR = fs.mkdtempSync(path.join(os.tmpdir(), 'cw-engine-test-'));
delete process.env.ANTHROPIC_API_KEY;
delete process.env.CLAUDE_API_KEY;
delete process.env.CW_FACTS_JSON;
delete process.env.GITHUB_TOKEN;

const { ROOT, loadCapability, loadFacts, sanitizeFacts, workPath, readText, dateJst } = require('./util');
const intake = require('./intake');
const { REASONS, WARNINGS, qualify } = require('./qualify');
const queueMod = require('./queue');
const { checkDraft, checkDeliverable } = require('./compliance');
const { buildApplyDraft, draftApplication, AI_LINE } = require('./apply-draft');
const { classify, draftReply, INTENTS, replyFor } = require('./reply-draft');
const { buildBrief } = require('./brief');
const { makeDeliverable } = require('./make');
const { buildDeliveryDoc } = require('./deliver');
const { buildProfileDraft } = require('./profile-draft');
const ledger = require('./ledger');
const { funnel } = require('./funnel');
const { parseCommand, isNotifyComment, COMMAND_TYPES, ISSUE_TITLE, defaultCommander } = require('./commander');
const { deskLines } = require('./desk');
const { renderMarkdown } = require('./report');
const { handleComment, CHEAT_SHEET } = require('./apply-commander-comment');

function assert(cond, label) {
  if (!cond) throw new Error(label);
}

const WRITING_JOB = `【継続あり】ペット用品の紹介記事（ブログ記事）ライティング｜1記事2000〜3000文字
在宅でできるライティングのお仕事です。未経験OK。
資料とキーワードはこちらで支給します。構成案もお渡しします。
AIツールを使う場合は事前に申告してください。
納期は契約から5日以内。
応募時に以下を記載してください。
・簡単な自己紹介
・1日に確保できる作業時間
・使用できるツール
・過去の実績やポートフォリオ（あれば）
応募期限 2026-09-20
応募した人 4 人
契約した人 0 人
募集人数 3 人
報酬 1記事 2,000円（税込）`;

const CAMERA_JOB = `TikTok に出演していただける方募集！顔出し必須。
撮影はご自身のスマホで行い、動画編集も行ってください。
ポートフォリオ必須。経験者のみ。
応募期限 2026-09-15`;

const REVIEW_JOB = `Google マップに口コミを投稿していただくお仕事です。1件 100円。
指定の店舗に星5の口コミを書き込みしてください。`;

const AI_NG_JOB = `コラム記事の執筆をお願いします。3000文字。
ChatGPT などの AI ツールの使用は禁止です。手書きで丁寧に。`;

function testIntakeAndQualify(capability, facts) {
  const job = intake.parseJobText('13500001', WRITING_JOB, capability);
  assert(job.category === 'writing_article', `category ${job.category}`);
  assert(job.flags.materials_provided, 'materials flag');
  assert(job.flags.unexperienced_ok, 'unexperienced flag');
  assert(job.flags.continuous, 'continuous flag');
  assert(job.flags.ai_disclose_required && !job.flags.ai_forbidden, 'ai disclose not forbidden');
  assert(!job.flags.needs_portfolio, 'portfolio optional');
  assert(job.asks.length === 4, `asks ${job.asks.length}`);
  assert(job.deadline === '2026-09-20', `deadline ${job.deadline}`);
  assert(job.applicants === 4 && job.contracted === 0 && job.openings === 3, 'counts');
  assert(job.public_price_yen === 2000, `price ${job.public_price_yen}`);
  assert(job.char_spec && job.char_spec[0] === 2000 && job.char_spec[1] === 3000, 'char spec');
  const v = qualify(job, { capability, facts, commander: defaultCommander(), queue: queueMod.defaultQueue() });
  assert(v.ok, `qualify ok ${v.reasons}`);
  assert(v.warnings.includes(WARNINGS.AI_DISCLOSE), 'warn disclose');
  assert(v.priority > 90, `priority ${v.priority}`);

  const cam = intake.parseJobText('13500002', CAMERA_JOB, capability);
  const vc = qualify(cam, { capability, facts, commander: defaultCommander(), queue: queueMod.defaultQueue() });
  assert(!vc.ok && vc.reasons.includes(REASONS.ON_CAMERA), 'camera deny');
  assert(vc.reasons.includes(REASONS.PORTFOLIO_REQUIRED), 'portfolio deny');

  const rev = intake.parseJobText('13500003', REVIEW_JOB, capability);
  const vr = qualify(rev, { capability, facts, commander: defaultCommander(), queue: queueMod.defaultQueue() });
  assert(vr.reasons.includes(REASONS.REVIEW_POSTING), 'review deny');
  assert(vr.reasons.includes(REASONS.CATEGORY_UNKNOWN), 'category unknown');

  const aing = intake.parseJobText('13500004', AI_NG_JOB, capability);
  const va = qualify(aing, { capability, facts, commander: defaultCommander(), queue: queueMod.defaultQueue() });
  assert(!va.ok && va.reasons.includes(REASONS.AI_FORBIDDEN), 'ai forbidden deny');

  const halted = qualify(job, { capability, facts, commander: { command: 'HALT' }, queue: queueMod.defaultQueue() });
  assert(halted.reasons.includes(REASONS.HALTED), 'halt deny');

  const busy = { jobs: [{ id: '1', status: 'contracted' }, { id: '2', status: 'making' }, { id: '3', status: 'ready' }] };
  const cap = qualify(job, { capability, facts, commander: defaultCommander(), queue: busy });
  assert(cap.reasons.includes(REASONS.CAPACITY), 'capacity deny');

  const applied = intake.parseJobText('13500005', `${WRITING_JOB}\n応募者 fireworker12`, capability);
  assert(applied.flags.already_applied, 'already applied detection');
  const video = intake.parseJobText('13500006', '素材支給の短尺 TikTok 動画編集。テロップとカット。未経験OK', capability);
  const vv = qualify(video, { capability, facts, commander: defaultCommander(), queue: queueMod.defaultQueue() });
  assert(vv.ok && vv.warnings.includes(WARNINGS.HUMAN_TOOL), 'video needs human tool');
  const videoNoMat = intake.parseJobText('13500007', '短尺 TikTok 動画編集。テロップとカット。', capability);
  const vn = qualify(videoNoMat, { capability, facts, commander: defaultCommander(), queue: queueMod.defaultQueue() });
  assert(vn.reasons.includes(REASONS.NOT_AI_COMPLETE), 'video without materials denied');
  return job;
}

function testQueue(job, facts, capability) {
  const v = qualify(job, { capability, facts, commander: defaultCommander(), queue: queueMod.defaultQueue() });
  const now = new Date('2026-09-12T00:00:00Z');
  let rec = queueMod.newJobRecord(job, v, now);
  assert(rec.status === 'qualified' && rec.confirmed_yen === null, 'new record');
  const bad = queueMod.transition(rec, 'PAID', now);
  assert(!bad.ok && /bad_state/.test(bad.reason), 'bad transition');
  for (const ev of ['DRAFTED', 'SENT', 'CONTRACT', 'MAKE', 'QA_FAIL', 'MAKE', 'QA_PASS', 'DELIVERED', 'PAID']) {
    const t = queueMod.transition(rec, ev, now);
    assert(t.ok, `transition ${ev}: ${t.reason}`);
    rec = t.job;
  }
  assert(rec.status === 'paid' && rec.revisions === 1 && rec.drafts === 1, 'final state');
  const q = queueMod.upsertJob(queueMod.defaultQueue(), rec, now);
  assert(queueMod.counts(q).paid === 1, 'counts paid');
  assert(queueMod.transition({ status: 'nope' }, 'BOGUS', now).ok === false, 'unknown event');
}

async function testDrafts(job, facts, capability) {
  const text = buildApplyDraft(job, { facts, capability, sample: null });
  assert(text.includes(AI_LINE), 'ai line');
  assert(text.includes('完成納品はまだありません'), 'honest deliveries');
  assert(text.includes('（人間が書く）'), 'placeholder for facts');
  assert(!/実績多数|経験\d+年/.test(text), 'no invented');
  const check = checkDraft(text, { facts, kind: 'apply' });
  assert(check.ok, `apply check ${check.issues}`);
  const d = await draftApplication(job, { facts, capability });
  assert(d.check.ok && !d.sample_used, 'draft without llm');
  const bad = checkDraft('実績多数です。https://example.com 必ず成果が出ます。私はAIです。', { facts, kind: 'apply' });
  assert(!bad.ok && bad.issues.includes('invented_achievement') && bad.issues.includes('hype_phrase') && bad.issues.includes('meta_ai_phrase'), `bad draft ${bad.issues}`);
  assert(bad.issues.some((i) => i.startsWith('url_not_allowed')), 'url flagged');

  const richFacts = sanitizeFacts({
    public_profile_facts: { occupation: '会社員', hours_per_day: 2, reply_hours: '平日20-23時', tools: ['Google ドキュメント'], deliveries_completed: 3, portfolio_url: 'https://example.com/p', age: 40, name: 'x' }
  });
  assert(richFacts.public_profile_facts.age === undefined && richFacts.public_profile_facts.name === undefined, 'facts sanitized');
  const rich = buildApplyDraft(job, { facts: richFacts, capability, sample: null });
  assert(rich.includes('完成納品は 3 件'), 'deliveries count');
  assert(rich.includes('1日 2 時間'), 'hours from facts');
  assert(checkDraft(rich, { facts: richFacts, kind: 'apply' }).ok, 'rich check ok');
}

function testReplies(job, facts, capability) {
  const now = new Date('2026-09-12T00:00:00Z');
  assert(classify('LINE でやり取りしませんか') === 'external_contact', 'intent external');
  assert(classify('まず1本作っていただいてから契約します') === 'prepay_request', 'intent prepay');
  assert(classify('ここを修正してください') === 'revision', 'intent revision');
  assert(classify('納期はいつまでですか') === 'deadline', 'intent deadline');
  assert(classify('AIは使いますか') === 'ask_ai', 'intent ai');
  assert(classify('実績を教えてください') === 'ask_experience', 'intent experience');
  assert(classify('ぜひ契約をお願いしたいです') === 'contract_offer', 'intent contract');
  assert(classify('天気がいいですね') === 'unknown', 'intent unknown');
  for (const intent of INTENTS) {
    const text = replyFor(intent, { job, facts, capability, now });
    const c = checkDraft(text, { facts, kind: 'reply', maxChars: 800 });
    assert(c.ok, `reply ${intent}: ${c.issues}`);
  }
  const r = draftReply('LINE でやり取りしませんか', { job, facts, capability, now });
  assert(/クラウドワークスのメッセージ内/.test(r.text), 'decline external');
  const p = draftReply('先に作業してもらえますか', { job, facts, capability, now });
  assert(/仮払い/.test(p.text), 'decline prepay');
  const both = draftReply('LINEでやり取りしませんか？先に1本テストで書いてもらえますか', { job, facts, capability, now });
  assert(both.intent === 'external_contact' && both.intents.includes('prepay_request') && /仮払い/.test(both.text) && /メッセージ内/.test(both.text), 'combined reply');
  assert(both.check.ok, `combined reply check ${both.check.issues}`);
}

async function testWork(job, facts, capability) {
  const now = new Date('2026-09-12T00:00:00Z');
  const brief = buildBrief(job, { capability, contractNotes: '', materials: '', now });
  assert(brief.missing.length >= 1 && /素材依頼文/.test(brief.text), 'brief asks materials');
  assert(brief.spec && brief.spec[0] === 2000, 'brief spec from job');
  assert(brief.due === '2026-09-14', `brief due ${brief.due}`);
  assert(/カタログ/.test(brief.text), 'brief marks catalog');
  const withMat = buildBrief(job, { capability, materials: 'キーワード: 犬 おもちゃ。読者: 初めて犬を飼う人。トーン: やさしく', now });
  assert(withMat.missing.length === 0 && withMat.ready, 'brief ready with materials');
  const made = await makeDeliverable(job, { capability, brief, briefText: brief.text, materials: '' });
  assert(!made.ok && made.blocked === 'await_grok' && /CW: DRAFT/.test(made.grokPrompt), 'make waits for grok');
  const qaBad = checkDeliverable('これは【要確認】です。https://evil.example 必ず治る。私はAIです。```x```', { materials: '', charSpec: [2000, 3000] });
  assert(!qaBad.ok, 'qa fails');
  assert(qaBad.issues.some((i) => i.startsWith('needs_check_left')), 'qa needs check');
  assert(qaBad.issues.some((i) => i.startsWith('url_not_in_materials')), 'qa url');
  assert(qaBad.issues.some((i) => i.startsWith('claim_not_in_materials')), 'qa claim');
  assert(qaBad.issues.includes('meta_ai_phrase') && qaBad.issues.includes('code_fence_left'), 'qa meta/fence');
  const good = checkDeliverable(`## 見出し\n${'犬のおもちゃを選ぶときは安全性を見ます。'.repeat(120)}`, { materials: '犬のおもちゃ', charSpec: [2000, 3000] });
  assert(good.ok, `qa good ${good.issues}`);
  const doc = buildDeliveryDoc(job, { capability, files: ['jobs/1/deliverables/v1/deliverable.md'], qa: good });
  assert(/納品ボタン/.test(doc) && /仮払い/.test(doc), 'delivery doc');
  const prof = buildProfileDraft({ facts, capability });
  assert(prof.check.ok, `profile ${prof.check.issues}`);
  assert(/お受けしていないもの/.test(prof.text) && /口コミ/.test(prof.text), 'profile denies');
}

function testLedgerAndFunnel(capability) {
  const bad = ledger.validatePaid({ date: '2026-09-12', jobId: '13500001', yenRaw: '1,000', note: '' });
  assert(!bad.ok && bad.reason === 'comma_number', 'ledger comma');
  const cat = ledger.validatePaid({ date: '2026-09-12', jobId: '13500001', yenRaw: '2000', note: 'カタログ' });
  assert(!cat.ok && cat.reason === 'catalog_yen', 'ledger catalog');
  const ok = ledger.validatePaid({ date: '2026-09-12', jobId: '13500001', yenRaw: '2000', note: '画面 確定' });
  assert(ok.ok, 'ledger ok');
  let csv = ledger.appendRow('', ok.row);
  csv = ledger.appendRow(csv, { ...ok.row, yen: 2500 });
  assert(ledger.total(csv) === 2500, `ledger dedupe total ${ledger.total(csv)}`);
  const hist = (events) => ({ history: events.map((e) => ({ event: e })) });
  const q1 = { jobs: Array.from({ length: 8 }, (_, i) => ({ id: String(i), status: 'sent', ...hist(['DRAFTED', 'SENT']) })) };
  assert(funnel(q1, { capability }).gate === 'improve_profile', 'funnel improve profile');
  const q2 = { jobs: [{ id: '1', status: 'contracted', ...hist(['SENT', 'CONTRACT']) }] };
  assert(funnel(q2, { capability }).gate === 'deliver_first', 'funnel deliver first');
  const q3 = { jobs: [{ id: '1', status: 'paid', ...hist(['PAID']) }, { id: '2', status: 'paid', ...hist(['PAID']) }] };
  assert(funnel(q3, { capability }).gate === 'scale', 'funnel scale');
}

function testCommander() {
  const c = parseCommand('CW: JOB 13500001 category=writing_article\n本文です\n続き');
  assert(c && c.type === 'JOB' && c.id === '13500001' && c.opts.category === 'writing_article' && c.payload === '本文です\n続き', 'parse job');
  const d = parseCommand('CW: DRAFT 13500001\n本文');
  assert(d.type === 'DRAFT' && d.payload === '本文', 'parse draft');
  const p = parseCommand('cw: paid 13500001 2000 画面で確定');
  assert(p.type === 'PAID' && p.id === '13500001' && p.extra[0] === '2000', 'parse paid');
  const noId = parseCommand('CW: SENT');
  assert(noId && noId.error === 'missing_id', 'missing id');
  assert(parseCommand('KILL_SWITCH: HALT') === null, 'xm command ignored');
  assert(parseCommand('CW: RESUME') === null, 'no resume');
  assert(parseCommand('CW: GO') === null, 'no lane switch in engine');
  assert(!COMMAND_TYPES.includes('RESUME') && !COMMAND_TYPES.includes('GO'), 'no live gate');
  assert(isNotifyComment('cw-apply: 1\n...') && isNotifyComment('cw-desk: paper') && isNotifyComment('cw-make: 1') && !isNotifyComment('CW: HALT'), 'notify detect');
  assert(ISSUE_TITLE === 'CW — 司令塔', 'issue title');
}

async function testDispatcher() {
  const now = new Date('2026-09-12T01:00:00Z');
  const run = (body) => handleComment({ body, login: 'naomichi', now, persist: true });
  assert((await run('cw-desk: paper')).reason === 'notify-comment', 'skip notify');
  assert((await handleComment({ body: 'CW: HALT', login: 'github-actions[bot]', now })).reason === 'actions-bot', 'skip bot');
  assert((await run('hello')).reason === 'no_command', 'skip no command');

  const job = await run(`CW: JOB 13500001\n${WRITING_JOB}`);
  assert(!job.skipped && job.result.kind === 'apply', `job kind ${job.result.kind}`);
  assert(job.comment.startsWith('cw-apply: 13500001'), 'apply comment head');
  assert(/cw-desk: paper/.test(job.comment) && /next_human:/.test(job.comment), 'desk footer');
  assert(fs.existsSync(workPath('jobs', '13500001', 'APPLY.md')) && fs.existsSync(workPath('jobs', '13500001', 'JOB.md')), 'files written');
  assert(fs.existsSync(workPath('reports', 'TODAY.md')), 'today written');

  const dup = await run(`CW: JOB 13500001\n${WRITING_JOB}`);
  assert(dup.result.kind === 'apply', 'redraft allowed while drafted');
  const rejected = await run(`CW: JOB 13500003\n${REVIEW_JOB}`);
  assert(rejected.result.kind === 'desk' && /tos_review_posting/.test(rejected.result.body), 'rejected job');

  const sent = await run('CW: SENT 13500001');
  assert(/送信済み/.test(sent.result.body), 'sent');
  const msg = await run('CW: MSG 13500001\nぜひ契約をお願いしたいです。納期はいつまでですか');
  assert(msg.result.kind === 'reply' && /契約と仮払い|初稿/.test(msg.result.body), 'reply drafted');
  const contract = await run('CW: CONTRACT 13500001\n記事のテーマは犬のおもちゃ。3本。');
  assert(contract.result.kind === 'brief' && fs.existsSync(workPath('jobs', '13500001', 'BRIEF.md')), 'brief');
  const mat = await run('CW: MATERIAL 13500001\nキーワード: 犬 おもちゃ 安全');
  assert(/素材 2 件目/.test(mat.result.body), `material ${mat.result.body}`);
  const make = await run('CW: MAKE 13500001');
  assert(make.result.kind === 'make' && /CW: DRAFT/.test(make.result.body) && !/ANTHROPIC_API_KEY/.test(make.result.body), 'make waits for grok');
  assert(make.comment.startsWith('cw-make: 13500001'), 'make comment head');
  assert(fs.existsSync(workPath('jobs', '13500001', 'GROK_PROMPT.md')), 'grok prompt file');
  let q = queueMod.loadQueue();
  assert(queueMod.findJob(q, '13500001').status === 'making', 'status making');
  const emptyDraft = await run('CW: DRAFT 13500001');
  assert(/2行目以降/.test(emptyDraft.result.body), 'draft needs body');
  const badDraft = await run('CW: DRAFT 13500001\nこれは【要確認】です。');
  assert(badDraft.result.kind === 'qa', 'qa fail on invented check');
  const article = `## 導入\n${'犬のおもちゃを選ぶときは安全性を見ます。'.repeat(80)}\n\n## 本文\n${'キーワードに沿って初心者向けに書きます。'.repeat(80)}\n\n## まとめ\n安全性を優先します。`;
  const draft = await run(`CW: DRAFT 13500001\n${article}`);
  assert(draft.result.kind === 'deliver' && /QA 合格/.test(draft.result.body), `draft qa ${draft.result.body}`);
  q = queueMod.loadQueue();
  assert(queueMod.findJob(q, '13500001').status === 'ready', 'status ready after draft');
  const delivered = await run('CW: DELIVERED 13500001');
  assert(/納品済み/.test(delivered.result.body), 'delivered');
  const paidBad = await run('CW: PAID 13500001 2,000');
  assert(/拒否/.test(paidBad.result.body), 'paid comma rejected');
  const paid = await run('CW: PAID 13500001 2000 画面で確定');
  assert(/確定 2000 円/.test(paid.result.body), `paid ${paid.result.body}`);
  assert(ledger.ledgerTotal() === 2000, 'ledger total after paid');
  const prof = await run('CW: PROFILE');
  assert(prof.result.kind === 'profile' && fs.existsSync(workPath('profile', 'PROFILE.md')), 'profile file');
  const halt = await run('CW: HALT');
  assert(/HALT/.test(halt.comment), 'halt');
  const blocked = await run(`CW: JOB 13500009\n${WRITING_JOB}`);
  assert(/commander_halt/.test(blocked.result.body), 'job blocked by halt');
  await run('CW: PAPER_ONLY');
  const noIdOut = await run('CW: SENT');
  assert(/仕事 ID が要る/.test(noIdOut.result.body), 'missing id note');
  const today = readText(workPath('reports', 'TODAY.md'));
  assert(/司令塔ステータス/.test(today) && /13500001/.test(today) && /確定報酬合計: 2000/.test(today), 'today content');
  assert(!/https?:\/\/crowdworks/.test(today), 'today has no job urls');
  const md = renderMarkdown({ commander: defaultCommander(), queue: queueMod.defaultQueue(), capability: loadCapability(), ledgerYen: 0, now });
  assert(/キュー空/.test(md), 'empty queue text');
  const desk = deskLines({ commander: defaultCommander(), queue: queueMod.defaultQueue(), capability: loadCapability(), funnel: funnel(queueMod.defaultQueue(), {}), now });
  assert(desk[0] === 'cw-desk: paper' && desk.some((l) => l.startsWith('auto_send: grok')), 'desk lines');
  assert(desk.some((l) => l.startsWith('next_grok:')), 'desk next_grok');
  assert(/CW: JOB/.test(CHEAT_SHEET) && !/RESUME/.test(CHEAT_SHEET), 'cheat sheet');
}

function testDocsAndSideline() {
  const repo = path.join(ROOT, '..');
  const dump = readText(path.join(ROOT, 'docs/grok-bots/G_cw.txt'));
  assert(dump.length > 200, 'dump exists');
  assert(!/G_hq_cw_remain|G_hq_cw_n10/.test(dump), 'dump does not open parked dumps');
  assert(!/crowdworks\.jp\/public\/jobs\/\d+/.test(dump), 'dump no live job urls');
  assert(/CW: HALT/.test(dump), 'dump halt');
  assert(/CW: DRAFT/.test(dump), 'dump draft');
  assert(/Anthropic/.test(dump), 'dump no anthropic');
  assert(!/CW: RESUME/.test(dump.replace(/`CW: RESUME` は出すな/g, '')), 'dump resume forbidden');
  assert(/HQ clone|HQ の clone|別の会話/.test(dump), 'dump separate from HQ clone');
  assert(/6416ebcd-6cd0-42bb-92c3-55e00b13828c/.test(dump), 'dump names existing bot');
  assert(/契約ボタン/.test(dump) && /納品ボタン/.test(dump) && /案内/.test(dump), 'dump human-only three');
  assert(/月100万稼ぐまで帰れま10/.test(dump) && /帰すな/.test(dump), 'dump does not report to HQ');
  const watch = readText(path.join(ROOT, 'docs/grok-bots/G_cw_watch.txt'));
  assert(/6416ebcd-6cd0-42bb-92c3-55e00b13828c/.test(watch), 'watch bot id');
  assert(!/crowdworks\.jp\/(public\/jobs|contracts|proposals)\/\d+/.test(watch), 'watch no live urls');
  assert(/HQ/.test(watch) && /帰すな/.test(watch), 'watch not to HQ');
  const roster = readText(path.join(ROOT, 'docs/grok-bots/ROSTER.md'));
  assert(/6416ebcd-6cd0-42bb-92c3-55e00b13828c/.test(roster) && /clone を足さない/.test(roster), 'roster');
  for (const f of ['README.md', 'docs/AUTO.md', 'docs/AGENTS.md', 'docs/BOTS.md', 'docs/COMMANDS.md', 'docs/CONCERNS.md', 'docs/PIPELINE.md', 'docs/TEMPLATES.md', 'docs/HUMAN_ONCE.md', 'docs/grok-bots/ROSTER.md', 'docs/grok-bots/G_cw_watch.txt', 'private-repo/cw.yml', 'private-repo/README.md']) {
    assert(fs.existsSync(path.join(ROOT, f)), `missing ${f}`);
  }
  const agents = readText(path.join(ROOT, 'docs/AGENTS.md'));
  assert(/HQ の Grok clone に足す変更\*\* \| \*\*0/.test(agents), 'agents: HQ clone untouched');
  assert(/常時稼働.*0/.test(agents), 'agents: no always-on');
  const priv = readText(path.join(ROOT, 'private-repo/cw.yml'));
  assert(/CW — 司令塔/.test(priv) && !/^\s*schedule:/m.test(priv), 'private workflow: issue title, no cron');
  assert(/fireworker011\/Research/.test(priv) && /apply-commander-comment\.js/.test(priv), 'private workflow runs engine');
  assert(/ANTHROPIC_API_KEY/.test(priv) && /CW_FACTS_JSON/.test(priv) && /CW_WORK_DIR/.test(priv), 'private workflow env');
  const ci = readText(path.join(repo, '.github/workflows/cw_engine_ci.yml'));
  assert(!/^\s*schedule:/m.test(ci) && !/issue_comment/.test(ci), 'ci: no cron, no issue trigger');
  assert(!fs.existsSync(path.join(repo, '.github/workflows/cw_engine_commander.yml')), 'no commander workflow in public repo');
  const hq = readText(path.join(repo, 'affiliate-engine/src/hq-instruct.js'));
  assert(!/cw-engine|G_cw/.test(hq), 'main-line hq-instruct untouched');
  const boot = readText(path.join(repo, 'affiliate-engine/docs/grok-bots/dump/G_hq_boot.txt'));
  assert(!/CW: GO|G_cw/.test(boot), 'main-line boot untouched');
  const machine = readText(path.join(repo, 'affiliate-engine/docs/grok-bots/MACHINE.md'));
  assert(!/G_cw/.test(machine), 'main-line machine untouched');
  const rule = readText(path.join(repo, '.cursor/rules/cw-engine.mdc'));
  assert(/cw-engine/.test(rule) && /globs/.test(rule), 'scoped rule exists');
  const gitignore = readText(path.join(ROOT, '.gitignore'));
  assert(/output\//.test(gitignore) && /facts\.json/.test(gitignore), 'gitignore hides runtime and facts');
}

async function selfTest() {
  const capability = loadCapability();
  const facts = loadFacts();
  assert(capability.account === 'fireworker12', 'capability account');
  assert(capability.categories.filter((c) => c.ai_complete).length >= 6, 'ai-complete categories');
  assert(facts.public_profile_facts.deliveries_completed === 0, 'facts example honest');
  assert(dateJst(new Date('2026-09-12T20:00:00Z')) === '2026-09-13', 'jst date');
  const job = testIntakeAndQualify(capability, facts);
  testQueue(job, facts, capability);
  await testDrafts(job, facts, capability);
  testReplies(job, facts, capability);
  await testWork(job, facts, capability);
  testLedgerAndFunnel(capability);
  testCommander();
  await testDispatcher();
  testDocsAndSideline();
  process.stdout.write('cw-engine self-test ok\n');
}

if (require.main === module) {
  selfTest().catch((err) => {
    console.error(`self-test failed: ${err.message}`);
    process.exit(1);
  });
}

module.exports = { selfTest };
