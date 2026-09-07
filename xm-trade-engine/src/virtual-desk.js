'use strict';

const fs = require('fs');
const path = require('path');
const { OUTPUT_DIR, writeJSON, roundTo } = require('./util');
const { runTick } = require('./tick');
const { postIssueMarker, virtualDeskCommentLines } = require('./issue-notify');

const VIRTUAL_MD = path.join(OUTPUT_DIR, 'reports', 'VIRTUAL.md');
const VIRTUAL_JSON = path.join(OUTPUT_DIR, 'reports', 'virtual.json');

function fmt(n, d = 2) {
  return Number.isFinite(n) ? roundTo(n, d) : '—';
}

function tvLine(row) {
  if (!row) return '取得失敗';
  return `close ${fmt(row.close, 5)}  high ${fmt(row.high, 5)}  low ${fmt(row.low, 5)}  RSI ${fmt(row.RSI, 1)}  ATR(D) ${fmt(row.ATR, 4)}  ATR(H1) ${fmt(row['ATR|60'], 4)}  SMA20 ${fmt(row.SMA20, 5)}  SMA50 ${fmt(row.SMA50, 5)}`;
}

function renderVirtualMarkdown(result) {
  const { now, book, gold, tv, intents, prices, commander, live_gate: liveGate, data_errors: errors } = result;
  const pending = (book.pending || []).filter((p) => p.status === 'working');
  const lines = [];
  lines.push('# 仮想トレード机 — TradingView + ルール（XMではない）');
  lines.push('');
  lines.push(`生成: ${now}`);
  lines.push('');
  lines.push('> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。');
  lines.push('> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。');
  lines.push('');
  lines.push('## データ源');
  lines.push('');
  lines.push('- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）');
  lines.push('- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors');
  lines.push('- Majors 足: Yahoo Finance H1');
  lines.push('- Yahoo `XAUUSD=X` は 404 のため使わない');
  lines.push('');
  if (errors && Object.keys(errors).length) {
    lines.push('### 取得エラー');
    lines.push('');
    for (const [k, v] of Object.entries(errors)) lines.push(`- ${k}: ${v}`);
    lines.push('');
  }
  lines.push('## TradingView スナップショット');
  lines.push('');
  if (tv) {
    lines.push(`- GOLD ${tvLine(tv.gold)}`);
    lines.push(`- EURUSD ${tvLine(tv.EURUSD)}`);
    lines.push(`- GBPUSD ${tvLine(tv.GBPUSD)}`);
    lines.push(`- USDJPY ${tvLine(tv.USDJPY)}`);
  } else {
    lines.push('- TradingView 未取得');
  }
  lines.push('');
  lines.push('## Gold 仮想 OCO（損切り・利確）');
  lines.push('');
  if (!gold || !gold.status) {
    lines.push('- セットアップなし');
  } else {
    lines.push(`- status: \`${gold.status}\` / reason: ${gold.reason || '—'}`);
    lines.push(`- last: ${fmt(prices?.GOLD, 2)}`);
    if (gold.asia_high != null) {
      lines.push(`- アジア: ${gold.asia_low} – ${gold.asia_high} close ${gold.asia_close}（range ${gold.range}, ATR日次比 ${gold.range_atr_frac}）`);
      lines.push(`- H1 ATR: ${gold.h1_atr}（${gold.h1_atr_source || 'rules'} / OKX H1 ${gold.okx_h1_atr ?? '—'}） / SL距離 ${gold.sl_distance}（1.2×ATR） / TP距離 ${gold.tp_distance}（1.8R）`);
      lines.push(`- chart suggested_side: ${gold.suggested_side}（参考。執行は OCO 両方）`);
      lines.push(`- BuyStop ${gold.buy_stop} → 損切り ${gold.buy_sl} / 利確 ${gold.buy_tp}`);
      lines.push(`- SellStop ${gold.sell_stop} → 損切り ${gold.sell_sl} / 利確 ${gold.sell_tp}`);
      if (gold.lot) lines.push(`- lot: ${gold.lot}（リスク 0.5%、上限 0.10。固定lotではない）`);
    }
    if (gold.status === 'forming') {
      lines.push('- アジア未確定。ロンドン開始まで高安は更新され得る。OCO は仮置き。');
    }
    if (gold.status === 'awaiting_arm' || gold.status === 'armed') {
      lines.push('- ロンドン枠で両方の pending が有効。先に触れた側だけ約定。反対は取消。');
    }
  }
  lines.push('');
  lines.push('## ペーパー帳簿（仮想資金）');
  lines.push('');
  lines.push(`- equity: ${book.equity} / balance: ${book.balance} / 本日実現: ${book.daily?.realized_pnl}`);
  lines.push(`- commander: \`${commander.command}\``);
  lines.push(`- live_gate: ${(liveGate || []).join('; ') || 'none'}`);
  lines.push('');
  if (pending.length) {
    lines.push('### 未約定 pending');
    lines.push('');
    for (const p of pending) {
      lines.push(`- ${p.type} ${p.symbol} lot=${p.lot} status=${p.setup_status || p.status}`);
      lines.push(`  - BUY ${p.buy_stop} SL ${p.buy_sl} TP ${p.buy_tp}`);
      lines.push(`  - SELL ${p.sell_stop} SL ${p.sell_sl} TP ${p.sell_tp}`);
    }
    lines.push('');
  }
  const open = book.positions || [];
  if (open.length) {
    lines.push('### 建玉');
    lines.push('');
    for (const p of open) {
      lines.push(`- ${p.side} ${p.symbol} lot=${p.lot} entry=${p.entry} SL=${p.sl} TP=${p.tp} uPnL=${p.unrealized ?? '—'}`);
    }
    lines.push('');
  } else {
    lines.push('- 建玉なし（約定待ち、またはルール未点火）');
    lines.push('');
  }
  lines.push('## Majors（EMAルール。LLMは選ばない）');
  lines.push('');
  for (const intent of intents || []) {
    lines.push(`- ${intent.symbol}: ${intent.action} (${intent.reason})${intent.lot ? ` lot=${intent.lot} SL=${intent.sl} TP=${intent.tp}` : ''}`);
  }
  lines.push('');
  lines.push('## やらない');
  lines.push('');
  lines.push('- ゴールドの方向を文章で予想しない');
  lines.push('- majors を LLM が買わせない');
  lines.push('- マーチンゲール・ナンピン・グリッド');
  lines.push('- リスク上限を上げる');
  lines.push('- この数字を XM 残高として読む');
  lines.push('');
  return `${lines.join('\n')}\n`;
}

async function runVirtualDesk({ now = new Date(), dryRun = false } = {}) {
  const result = await runTick({ now, dryRun, allowForming: true });
  const md = renderVirtualMarkdown(result);
  const payload = {
    kind: 'virtual_desk',
    disclaimer: result.book?.disclaimer,
    now: result.now,
    gold: result.gold,
    tv: result.tv,
    intents: result.intents,
    prices: result.prices,
    pending: (result.book.pending || []).filter((p) => p.status === 'working'),
    positions: result.book.positions,
    equity: result.book.equity,
    data_errors: result.data_errors
  };
  if (!dryRun) {
    fs.mkdirSync(path.dirname(VIRTUAL_MD), { recursive: true });
    fs.writeFileSync(VIRTUAL_MD, md, 'utf-8');
    writeJSON(VIRTUAL_JSON, payload);
    const gold = result.gold;
    if (gold && gold.date && gold.buy_stop != null) {
      const marker = `virtual-desk:${gold.date}:${gold.status}`;
      await postIssueMarker({
        marker,
        lines: virtualDeskCommentLines(gold, result.book)
      });
    }
  }
  return { ...result, markdown: md };
}

module.exports = {
  VIRTUAL_MD,
  renderVirtualMarkdown,
  runVirtualDesk
};

if (require.main === module) {
  const dryRun = process.argv.includes('--dry-run');
  runVirtualDesk({ dryRun }).then((result) => {
    process.stdout.write(result.markdown);
    const summary = {
      gold: result.gold
        ? {
          status: result.gold.status,
          reason: result.gold.reason,
          buy_stop: result.gold.buy_stop,
          buy_sl: result.gold.buy_sl,
          buy_tp: result.gold.buy_tp,
          sell_stop: result.gold.sell_stop,
          sell_sl: result.gold.sell_sl,
          sell_tp: result.gold.sell_tp,
          lot: result.gold.lot
        }
        : null,
      intents: (result.intents || []).map((i) => ({ symbol: i.symbol, action: i.action, reason: i.reason })),
      paper_equity: result.book.equity,
      dryRun: result.dryRun
    };
    console.error(JSON.stringify(summary, null, 2));
  }).catch((err) => {
    console.error(`virtual-desk failed: ${err.message}`);
    process.exit(1);
  });
}
