'use strict';

const path = require('path');
const { readJSON, writeJSON, OUTPUT_DIR, todayUTC, pipSize, roundTo } = require('./util');

const PAPER_PATH = path.join(OUTPUT_DIR, 'state', 'paper.json');

function emptyBook(risk) {
  const balance = risk.paper_start_balance;
  return {
    kind: 'paper',
    disclaimer: '仮想資金。XM口座の残高ではない。数字を実口座と混ぜて読むな。',
    currency: 'USD',
    balance,
    equity: balance,
    positions: [],
    pending: [],
    closed: [],
    daily: {
      date: todayUTC(),
      start_equity: balance,
      realized_pnl: 0
    }
  };
}

function loadBook(risk) {
  const book = readJSON(PAPER_PATH, null);
  if (!book) return emptyBook(risk);
  if (!Array.isArray(book.pending)) book.pending = [];
  return book;
}

function saveBook(book) {
  writeJSON(PAPER_PATH, book);
  return book;
}

function rolloverDaily(book, now) {
  const date = todayUTC(now);
  if (book.daily?.date === date) return book;
  book.daily = {
    date,
    start_equity: book.equity ?? book.balance,
    realized_pnl: 0
  };
  return book;
}

function markToMarket(book, prices) {
  let floating = 0;
  for (const p of book.positions) {
    const price = prices[p.symbol];
    if (!Number.isFinite(price)) continue;
    p.mark = price;
    p.unrealized = pnlOf(p, price);
    floating += p.unrealized;
  }
  book.equity = roundTo(book.balance + floating, 2);
  return book;
}

function pnlOf(position, price) {
  const pip = pipSize(position.symbol);
  const dir = position.side === 'BUY' ? 1 : -1;
  const pips = ((price - position.entry) / pip) * dir;
  return roundTo(pips * position.pip_value * position.lot, 2);
}

function openPosition(book, order) {
  const pos = {
    id: `p_${order.symbol}_${order.now.toISOString()}`,
    symbol: order.symbol,
    side: order.side,
    lot: order.lot,
    entry: order.price,
    sl: order.sl,
    tp: order.tp,
    pip_value: order.pip_value,
    opened_at: order.now.toISOString(),
    reason: order.reason,
    mark: order.price,
    unrealized: 0
  };
  book.positions.push(pos);
  if (order.commission) {
    book.balance = roundTo(book.balance - order.commission, 2);
  }
  return pos;
}

function closePosition(book, symbol, price, now, reason) {
  const idx = book.positions.findIndex((p) => p.symbol === symbol);
  if (idx < 0) return null;
  const pos = book.positions.splice(idx, 1)[0];
  const pnl = pnlOf(pos, price);
  book.balance = roundTo(book.balance + pnl, 2);
  book.daily.realized_pnl = roundTo((book.daily.realized_pnl || 0) + pnl, 2);
  const closed = {
    ...pos,
    exit: price,
    pnl,
    closed_at: now.toISOString(),
    close_reason: reason
  };
  book.closed.push(closed);
  if (book.closed.length > 500) book.closed = book.closed.slice(-500);
  return closed;
}

function upsertPending(book, order) {
  if (!Array.isArray(book.pending)) book.pending = [];
  const placed = (order.now instanceof Date ? order.now.toISOString() : order.placed_at) || new Date().toISOString();
  book.pending = book.pending.filter((p) => !(p.symbol === order.symbol && p.status === 'working'));
  const row = {
    id: order.id || `pend_${order.symbol}_${placed}`,
    symbol: order.symbol,
    type: order.type || 'OCO',
    status: 'working',
    buy_stop: order.buy_stop,
    sell_stop: order.sell_stop,
    buy_sl: order.buy_sl,
    buy_tp: order.buy_tp,
    sell_sl: order.sell_sl,
    sell_tp: order.sell_tp,
    sl_distance: order.sl_distance,
    tp_distance: order.tp_distance,
    lot: order.lot,
    reason: order.reason,
    setup_status: order.setup_status,
    placed_at: placed
  };
  book.pending.push(row);
  if (book.pending.length > 200) book.pending = book.pending.slice(-200);
  return row;
}

function cancelWorkingPending(book, symbol, reason, now) {
  if (!Array.isArray(book.pending)) book.pending = [];
  for (const p of book.pending) {
    if (p.symbol === symbol && p.status === 'working') {
      p.status = 'cancelled';
      p.cancel_reason = reason;
      p.cancelled_at = now.toISOString();
    }
  }
}

function markPendingFilled(book, symbol, side, now) {
  if (!Array.isArray(book.pending)) book.pending = [];
  for (const p of book.pending) {
    if (p.symbol === symbol && p.status === 'working') {
      p.status = 'filled';
      p.fill_side = side;
      p.filled_at = now.toISOString();
    }
  }
}

function hitStops(book, prices, now) {
  const closed = [];
  for (const p of [...book.positions]) {
    const price = prices[p.symbol];
    if (!Number.isFinite(price)) continue;
    if (p.side === 'BUY') {
      if (p.sl != null && price <= p.sl) {
        closed.push(closePosition(book, p.symbol, p.sl, now, 'sl'));
      } else if (p.tp != null && price >= p.tp) {
        closed.push(closePosition(book, p.symbol, p.tp, now, 'tp'));
      }
    } else {
      if (p.sl != null && price >= p.sl) {
        closed.push(closePosition(book, p.symbol, p.sl, now, 'sl'));
      } else if (p.tp != null && price <= p.tp) {
        closed.push(closePosition(book, p.symbol, p.tp, now, 'tp'));
      }
    }
  }
  return closed.filter(Boolean);
}

module.exports = {
  PAPER_PATH,
  emptyBook,
  loadBook,
  saveBook,
  rolloverDaily,
  markToMarket,
  pnlOf,
  openPosition,
  closePosition,
  hitStops,
  upsertPending,
  cancelWorkingPending,
  markPendingFilled
};
