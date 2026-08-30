'use strict';

const fs = require('fs');
const path = require('path');
const { OUTPUT_DIR, todayJST, writeJSON } = require('./util');
const commanderMod = require('./commander');
const paper = require('./paper-broker');
const { loadAllConfig } = require('./tick');
const { liveGateReasons, dailyLossExceeded } = require('./risk');
const goldMod = require('./gold-breakout');
const { todayUTC } = require('./util');

const TRACKING_ISSUE_TITLE = commanderMod.ISSUE_TITLE;
const FORBIDDEN = [
  'LLM / Grok に majors のエントリーを選ばせるな。Gold は suggested_side 以外で方向を決めるな',
  'マーチンゲール・ナンピン・グリッドを足すな',
  'リスク上限を上げるな',
  'XM_LIVE_CONFIRM なしで実口座発注するな',
  'GitHub cron を実時間の発注クロックにするな（遅延する）',
  'ペーパー損益をXM口座の損益として語るな',
  '数字が無いのに「勝っている」と書くな',
  '巷の Gold EA のグリッド／ナンピンをコピーするな'
];

function renderMarkdown({ today, book, commander, runtime, liveGate, now, goldState }) {
  const open = book.positions || [];
  const closedToday = (book.closed || []).filter((c) => (c.closed_at || '').slice(0, 10) === todayUTC(now));
  const lines = [];
  lines.push(`# XM Trade 日次 — ${today}`);
  lines.push('');
  lines.push(`生成: ${now.toISOString()}`);
  lines.push('');
  lines.push('> ペーパー帳簿は仮想資金。XMの残高・損益は MetaApi 未接続なら **未確認**。発明しない。');
  lines.push('');
  lines.push('## 司令塔ステータス');
  lines.push('');
  lines.push(`- command: \`${commander.command}\``);
  lines.push(`- source: ${commander.source}`);
  lines.push(`- reason: ${commander.reason || '—'}`);
  lines.push(`- updated_at: ${commander.updated_at}`);
  lines.push(`- gold_arm: \`${commander.gold_arm || 'IDLE'}\` (${commander.gold_arm_date || '—'})`);
  lines.push('');
  lines.push('## ペーパー帳簿（XMではない）');
  lines.push('');
  lines.push(`- equity: ${book.equity}`);
  lines.push(`- balance: ${book.balance}`);
  lines.push(`- daily start_equity: ${book.daily?.start_equity} (${book.daily?.date})`);
  lines.push(`- daily realized: ${book.daily?.realized_pnl}`);
  lines.push(`- open: ${open.length}`);
  lines.push(`- closed today: ${closedToday.length}`);
  lines.push('');
  if (open.length) {
    lines.push('### 建玉');
    lines.push('');
    for (const p of open) {
      lines.push(`- ${p.side} ${p.symbol} lot=${p.lot} entry=${p.entry} sl=${p.sl} tp=${p.tp} uPnL=${p.unrealized ?? '—'}`);
    }
    lines.push('');
  }
  if (closedToday.length) {
    lines.push('### 本日決済');
    lines.push('');
    for (const p of closedToday) {
      lines.push(`- ${p.side} ${p.symbol} pnl=${p.pnl} reason=${p.close_reason}`);
    }
    lines.push('');
  }
  lines.push('## Gold 半自動（アジアレンジ → ロンドン OCO）');
  lines.push('');
  if (goldState && goldState.status && goldState.status !== 'idle') {
    lines.push(`- status: \`${goldState.status}\``);
    lines.push(`- reason: ${goldState.reason || '—'}`);
    if (goldState.asia_high != null) {
      lines.push(`- asia: ${goldState.asia_low} – ${goldState.asia_high} close ${goldState.asia_close ?? '—'} (range ${goldState.range}, frac ${goldState.range_atr_frac})`);
      lines.push(`- suggested_side: ${goldState.suggested_side || 'NONE'}`);
      lines.push(`- levels: BuyStop ${goldState.buy_stop} / SellStop ${goldState.sell_stop}`);
    }
    if (goldState.status === 'awaiting_arm') {
      lines.push('- Grok は suggested_side に従え。BUY→`ENTRY: GOLD BUY` / SELL→`ENTRY: GOLD SELL` / NONE→`SKIP: GOLD`');
      lines.push('- この suggested_side は Yahoo H1（ペーパー）。MT5 の chart_side と違うなら SKIP');
    }
  } else {
    lines.push(`- ${goldState?.reason || 'waiting_asia / no state'}`);
  }
  lines.push('');
  lines.push('## 実口座ゲート');
  lines.push('');
  lines.push(`- adapter: ${runtime.adapter}`);
  lines.push(`- live_enabled: ${runtime.live_enabled}`);
  if (liveGate.length) {
    for (const r of liveGate) lines.push(`- blocked: ${r}`);
  } else {
    lines.push('- live gates passed（実発注が走り得る。意図したか確認）');
  }
  lines.push('');
  lines.push('## 人間 / Grok Bot の1手');
  lines.push('');
  lines.push('デモEAが未設置なら、今日の1手は **MT5デモに EA を載せる**。実口座はまだ開くな。');
  lines.push('停止するときは Issue に次の1行だけ:');
  lines.push('');
  lines.push('```');
  lines.push('KILL_SWITCH: HALT');
  lines.push('```');
  lines.push('');
  lines.push('再開（ペーパー）: `KILL_SWITCH: PAPER_ONLY` / リスク半減: `KILL_SWITCH: REDUCE_RISK`');
  lines.push('`RESUME` はライブゲートを全部満たさない限り実発注しない。');
  lines.push('Gold 半自動: Grok は `ENTRY: GOLD BUY` / `ENTRY: GOLD SELL` / `SKIP: GOLD`。suggested_side 以外で方向を決めるな。');
  lines.push('');
  lines.push('## やるな');
  lines.push('');
  for (const item of FORBIDDEN) lines.push(`- ${item}`);
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
        body: JSON.stringify({ title: TRACKING_ISSUE_TITLE, body })
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

async function runReport({ now = new Date(), skipIssue = false } = {}) {
  const { risk, runtime } = loadAllConfig();
  const commander = commanderMod.loadCommander();
  const book = paper.loadBook(risk);
  const goldState = goldMod.loadGoldState();
  const liveGate = liveGateReasons({ runtime, commander, env: process.env });
  const today = todayJST(now);
  const markdown = renderMarkdown({ today, book, commander, runtime, liveGate, now, goldState });
  const outDir = path.join(OUTPUT_DIR, 'reports');
  fs.mkdirSync(outDir, { recursive: true });
  const dated = path.join(outDir, `report_${today}.md`);
  const latest = path.join(outDir, 'TODAY.md');
  fs.writeFileSync(dated, markdown, 'utf-8');
  fs.writeFileSync(latest, markdown, 'utf-8');
  writeJSON(path.join(outDir, 'latest.json'), {
    generated_at: now.toISOString(),
    commander,
    paper_equity: book.equity,
    paper_balance: book.balance,
    live_gate: liveGate,
    gold: goldState && { status: goldState.status, reason: goldState.reason },
    daily_loss_exceeded: dailyLossExceeded(book, risk, todayUTC(now))
  });
  if (!skipIssue) await upsertIssue(markdown);
  return { markdown, dated, latest };
}

module.exports = { renderMarkdown, runReport, FORBIDDEN };

if (require.main === module) {
  runReport().catch((err) => {
    console.error(`report failed: ${err.message}`);
    process.exit(1);
  });
}
