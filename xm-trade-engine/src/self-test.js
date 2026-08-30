#!/usr/bin/env node
'use strict';

const { emaSeries, rsiSeries, atrSeries } = require('./indicators');
const { decide, inSession, shouldFlattenFriday, validateStrategy } = require('./strategy');
const {
  lotFromRisk,
  liveGateReasons,
  canSendLiveOrder,
  forbidMartingale,
  dailyLossExceeded,
  LIVE_CONFIRM_PHRASE
} = require('./risk');
const { parseCommandText, applyCommand, latestCommandFromComments, defaultCommander, parseGoldArmText } = require('./commander');
const { applyComment } = require('./apply-commander-comment');
const { parseYahooChart, dropIncompleteLastBar } = require('./market-data');
const { tradeBody, isSuccess } = require('./adapters/metaapi');
const { runTick } = require('./tick');
const { replay } = require('./backtest');
const { renderMarkdown } = require('./report');
const { loadConfig, pipSize } = require('./util');
const { proposeSetup, applyArm, detectFill, isFirstFriday, suggestedSide, asianRange, inLondonWindow, brokerHourStart, goldWindows } = require('./gold-breakout');

function assertEqual(actual, expected, label) {
  if (actual !== expected) {
    throw new Error(`${label}: expected ${JSON.stringify(expected)} got ${JSON.stringify(actual)}`);
  }
}

function assert(cond, label) {
  if (!cond) throw new Error(label);
}

function makeBars({ n = 80, start = 1.08, drift = 0.00008, startTime = Date.parse('2024-03-04T08:00:00Z') } = {}) {
  const bars = [];
  let price = start;
  let t = startTime;
  for (let i = 0; i < n; i++) {
    const d = new Date(t);
    if (d.getUTCDay() === 0 || d.getUTCDay() === 6) {
      t += 3600000;
      i -= 1;
      continue;
    }
    const open = price;
    const noise = ((i * 13) % 5 - 2) * 0.00003;
    const close = price + drift + noise;
    bars.push({
      time: t,
      open,
      high: Math.max(open, close) + 0.0002,
      low: Math.min(open, close) - 0.0002,
      close,
      volume: 100
    });
    price = close;
    t += 3600000;
  }
  return bars;
}

function goldAsiaBars() {
  const bars = [];
  const day = Date.parse('2024-03-05T00:00:00Z');
  for (let h = 0; h < 8; h++) {
    const t = day + h * 3600000;
    const mid = 2400;
    bars.push({
      time: t,
      open: mid,
      high: mid + 4,
      low: mid - 4,
      close: mid,
      volume: 1
    });
  }
  return bars;
}

/** XM +2: ブローカー 0-7 = UTC 前日 22:00–当日 05:00 */
function goldAsiaBarsXm() {
  const bars = [];
  const start = Date.parse('2024-03-04T22:00:00Z');
  for (let h = 0; h < 7; h++) {
    const t = start + h * 3600000;
    const mid = 2400;
    bars.push({
      time: t,
      open: mid,
      high: mid + 4,
      low: mid - 4,
      close: mid,
      volume: 1
    });
  }
  return bars;
}

async function runSelfTest() {
  const strategy = loadConfig('strategy');
  const risk = loadConfig('risk');
  validateStrategy(strategy);

  const ema = emaSeries([1, 2, 3, 4], 3);
  assertEqual(ema[2], 2, 'ema seed sma');
  assertEqual(ema[3], 3, 'ema k=0.5');

  const rsi = rsiSeries([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], 14);
  assert(rsi[14] === 100, `rsi all-up should be 100 got ${rsi[14]}`);

  const atrBars = [
    { high: 2, low: 1, close: 1.5 },
    { high: 2.2, low: 1.1, close: 2 },
    { high: 2.3, low: 1.8, close: 2.1 },
    { high: 2.4, low: 2.0, close: 2.2 }
  ];
  const atr = atrSeries(atrBars, 2);
  assert(atr[2] != null && atr[2] > 0, 'atr seed');
  assert(atr[3] != null, 'atr wilder');

  assertEqual(inSession(new Date('2024-03-04T10:00:00Z'), strategy.session), true, 'london session');
  assertEqual(inSession(new Date('2024-03-04T03:00:00Z'), strategy.session), false, 'night');
  assertEqual(shouldFlattenFriday(new Date('2024-03-08T19:00:00Z'), strategy.session), true, 'friday flat');

  const up = makeBars({ n: 90, drift: 0.00015 });
  const buy = decide(up, new Date(up[up.length - 1].time), null, strategy);
  assert(['BUY', 'FLAT', 'HOLD'].includes(buy.action), `got ${buy.action}`);
  if (buy.action === 'BUY') {
    assert(buy.sl < buy.close, 'buy sl below');
    assert(buy.tp > buy.close, 'buy tp above');
  }

  const down = makeBars({ n: 90, start: 1.12, drift: -0.00015 });
  const sell = decide(down, new Date(down[down.length - 1].time), null, strategy);
  if (sell.action === 'SELL') {
    assert(sell.sl > sell.close, 'sell sl above');
    assert(sell.tp < sell.close, 'sell tp below');
  }

  const hold = decide(up, new Date(up[up.length - 1].time), { side: 'BUY' }, strategy);
  assert(hold.action === 'HOLD' || hold.action === 'CLOSE', `in-position ${hold.action}`);

  const mini = {
    ...strategy,
    ema_fast: 3,
    ema_slow: 5,
    rsi_period: 3,
    atr_period: 3,
    rsi_overbought: 99,
    rsi_oversold: 1,
    atr_filter: null
  };
  const flatThenUp = makeBars({ n: 10, start: 1.1, drift: -0.0004, startTime: Date.parse('2024-03-04T08:00:00Z') });
  const prev = flatThenUp[flatThenUp.length - 1];
  flatThenUp.push({
    time: prev.time + 3600000,
    open: prev.close,
    high: prev.close + 0.012,
    low: prev.close,
    close: prev.close + 0.01,
    volume: 100
  });
  const forcedBuy = decide(flatThenUp, new Date(flatThenUp[flatThenUp.length - 1].time), null, mini);
  assertEqual(forcedBuy.action, 'BUY', `forced buy got ${forcedBuy.action} ${forcedBuy.reason}`);

  const sized = lotFromRisk({
    symbol: 'EURUSD',
    price: 1.08,
    slPrice: 1.08 - 0.0015,
    equity: 10000,
    riskPct: 0.5,
    maxLot: 0.1,
    minLot: 0.01,
    lotStep: 0.01,
    contractSize: 100000
  });
  assert(sized.lot > 0 && sized.lot <= 0.1, `lot ${sized.lot}`);
  assertEqual(forbidMartingale(0.02, 0.04, -12), true, 'martingale blocked');
  assertEqual(forbidMartingale(0.02, 0.02, -12), false, 'same lot ok');
  assertEqual(forbidMartingale(0.02, 0.04, 12), false, 'after win ok');

  const lossBook = {
    equity: 9700,
    daily: { date: '2026-08-30', start_equity: 10000, realized_pnl: -300 }
  };
  assertEqual(dailyLossExceeded(lossBook, { max_daily_loss_pct: 2 }, '2026-08-30'), true, 'daily loss');
  assertEqual(dailyLossExceeded(lossBook, { max_daily_loss_pct: 2 }, '2026-08-31'), false, 'other day');

  const runtime = { live_enabled: false, adapter: 'paper' };
  const commander = defaultCommander();
  const gates = liveGateReasons({ runtime, commander, env: {} });
  assert(gates.length >= 2, 'live blocked');
  assertEqual(canSendLiveOrder({ runtime, commander, env: {} }), false, 'no live');
  assertEqual(
    canSendLiveOrder({
      runtime: { live_enabled: true, adapter: 'paper' },
      commander: { command: 'RESUME' },
      env: { XM_LIVE_CONFIRM: LIVE_CONFIRM_PHRASE }
    }),
    true,
    'paper resume with confirm'
  );
  assertEqual(
    canSendLiveOrder({
      runtime: { live_enabled: true, adapter: 'metaapi' },
      commander: { command: 'RESUME' },
      env: { XM_LIVE_CONFIRM: LIVE_CONFIRM_PHRASE }
    }),
    false,
    'metaapi needs secrets'
  );

  assertEqual(parseCommandText('KILL_SWITCH: HALT'), 'HALT', 'parse halt');
  assertEqual(parseCommandText('command: paper_only'), 'PAPER_ONLY', 'parse paper');
  assertEqual(parseCommandText('hello'), null, 'parse none');
  applyCommand(commander, {
    command: 'HALT',
    source: 'test',
    reason: 'x',
    now: new Date('2026-08-30T00:00:00Z')
  });
  const fromComments = latestCommandFromComments([
    { id: 1, body: 'KILL_SWITCH: RESUME', updated_at: '2026-08-30T01:00:00Z' },
    { id: 2, body: 'KILL_SWITCH: HALT', updated_at: '2026-08-30T02:00:00Z' }
  ]);
  assertEqual(fromComments.command, 'HALT', 'latest comment wins');

  const yahoo = parseYahooChart({
    chart: {
      result: [{
        timestamp: [1, 2, 3],
        indicators: {
          quote: [{
            open: [1, 1.1, 1.2],
            high: [1.05, 1.15, 1.25],
            low: [0.9, 1.0, 1.1],
            close: [1, 1.1, 1.2],
            volume: [1, 1, 1]
          }]
        }
      }]
    }
  });
  assertEqual(yahoo.length, 2, 'drop last bar');
  assertEqual(dropIncompleteLastBar([{ t: 1 }, { t: 2 }]).length, 1, 'drop helper');

  const body = tradeBody({ action: 'BUY', symbol: 'EURUSD', lot: 0.02, sl: 1.07, tp: 1.09 });
  assertEqual(body.actionType, 'ORDER_TYPE_BUY', 'metaapi buy');
  assertEqual(isSuccess({ stringCode: 'TRADE_RETCODE_DONE', numericCode: 10009 }), true, 'mt success');
  assertEqual(isSuccess({ stringCode: 'TRADE_RETCODE_REJECT', numericCode: 10006 }), false, 'mt reject');

  const fixture = makeBars({ n: 100, drift: 0.0001 });
  const jpy = makeBars({ n: 100, start: 150, drift: 0.02 });
  const fixtures = { EURUSD: fixture, GBPUSD: fixture, USDJPY: jpy, GOLD: goldAsiaBars() };
  const now = new Date(fixture[fixture.length - 1].time);
  const tick = await runTick({ now, dryRun: true, env: {}, fixtureBySymbol: fixtures });
  assert(Array.isArray(tick.intents), 'tick intents');
  assertEqual(tick.dryRun, true, 'dry run');
  assert(tick.live_gate.length > 0, 'live still gated');
  assert(tick.gold != null, 'gold state');
  const second = await runTick({ now, dryRun: true, env: {}, fixtureBySymbol: fixtures });
  assertEqual(
    JSON.stringify(tick.intents.map((i) => `${i.symbol}:${i.action}`)),
    JSON.stringify(second.intents.map((i) => `${i.symbol}:${i.action}`)),
    'deterministic intents'
  );

  const stats = replay(up, { ...strategy, symbols: ['EURUSD'] }, risk, commander);
  assert(stats.trades >= 0, 'replay runs');
  assert(stats.end_equity != null, 'equity exists');

  const md = renderMarkdown({
    today: '2026-08-30',
    book: {
      equity: 10000,
      balance: 10000,
      positions: [],
      closed: [],
      daily: { date: '2026-08-30', start_equity: 10000, realized_pnl: 0 }
    },
    commander,
    runtime,
    liveGate: gates,
    now: new Date('2026-08-30T05:00:00Z')
  });
  assert(/ペーパー/.test(md), 'report labels paper');
  assert(/KILL_SWITCH/.test(md), 'report has kill switch');
  assert(!/必ず稼げる/.test(md), 'no guarantee copy');
  assert(/Gold 半自動/.test(md), 'report has gold section');

  const goldCfg = loadConfig('gold');
  const goldTestCfg = { ...goldCfg, atr_period: 3, broker_utc_offset_hours: 0 };
  const goldXmCfg = { ...goldCfg, atr_period: 3, broker_utc_offset_hours: 2 };
  assertEqual(goldWindows(goldCfg).offset, 2, 'gold.json default XM +2');
  assertEqual(goldWindows(goldCfg).asiaEnd, 7, 'asia end is broker hour 7');
  assertEqual(pipSize('GOLD'), 0.01, 'gold pip');
  assertEqual(parseGoldArmText('ARM: GOLD'), 'ARM', 'arm parse');
  assertEqual(parseGoldArmText('SKIP: GOLD'), 'SKIP', 'skip parse');
  assertEqual(parseGoldArmText('ENTRY: GOLD BUY'), 'BUY', 'entry buy');
  assertEqual(parseGoldArmText('ENTRY: GOLD SELL'), 'SELL', 'entry sell');
  assertEqual(parseGoldArmText('KILL_SWITCH: HALT'), null, 'kill is not arm');
  assertEqual(isFirstFriday(new Date('2026-09-04T08:00:00Z')), true, 'first friday');
  assertEqual(isFirstFriday(new Date('2026-09-11T08:00:00Z')), false, 'second friday');

  const lockNow = new Date('2024-03-05T08:00:00Z');
  const proposed = proposeSetup({ bars: goldAsiaBars(), now: lockNow, cfg: goldTestCfg, dailyAtrOverride: 20 });
  assertEqual(proposed.status, 'awaiting_arm', `gold propose ${proposed.status} ${proposed.reason}`);
  assert(proposed.buy_stop > proposed.asia_high, 'buy stop above asia');
  assertEqual(proposed.suggested_side, 'NONE', 'mid asia close is none');

  const buyBars = goldAsiaBars();
  const lastAsia = buyBars.findLast
    ? buyBars.filter((b) => b.time < Date.parse('2024-03-05T07:00:00Z')).slice(-1)[0]
    : null;
  const idx = buyBars.indexOf(lastAsia);
  buyBars[idx].close = 2403.2;
  buyBars[idx].high = Math.max(buyBars[idx].high, 2403.2);
  const buySetup = proposeSetup({ bars: buyBars, now: lockNow, cfg: goldTestCfg, dailyAtrOverride: 20 });
  assertEqual(buySetup.suggested_side, 'BUY', 'upper third suggests buy');
  assertEqual(suggestedSide({ high: 100, low: 0, close: 80 }), 'BUY', 'suggested buy');
  assertEqual(suggestedSide({ high: 100, low: 0, close: 20 }), 'SELL', 'suggested sell');

  const grokBuy = applyArm(buySetup, { goldArm: 'BUY', goldArmDate: '2024-03-05', halted: false, now: lockNow });
  assertEqual(grokBuy.entry_side, 'BUY', 'grok entry side');
  const grokFilled = detectFill(
    grokBuy,
    [{
      time: Date.parse('2024-03-05T08:00:00Z'),
      high: grokBuy.buy_stop + 1,
      low: grokBuy.sell_stop - 1,
      open: 2400,
      close: grokBuy.buy_stop + 0.4,
      volume: 1
    }],
    new Date('2024-03-05T08:30:00Z'),
    goldTestCfg
  );
  assertEqual(grokFilled.status, 'filled', 'grok buy fills');
  assertEqual(grokFilled.fill_side, 'BUY', 'buy-only ignores sell stop');

  const applied = applyComment({
    body: 'ENTRY: GOLD SELL',
    login: 'grok-bot',
    now: lockNow,
    current: defaultCommander(),
    persist: false
  });
  assertEqual(applied.gold_arm, 'SELL', 'comment writes sell');
  const ignored = applyComment({
    body: 'gold-notice:2024-03-05\nENTRY: GOLD BUY',
    login: 'human',
    now: lockNow,
    persist: false
  });
  assertEqual(ignored.skipped, true, 'gold-notice is not a command');

  const unarmedFill = detectFill(
    proposed,
    [{ time: Date.parse('2024-03-05T08:00:00Z'), high: 2500, low: 2390, open: 2400, close: 2490, volume: 1 }],
    lockNow,
    goldTestCfg
  );
  assertEqual(unarmedFill.status, 'awaiting_arm', 'no fill without ARM');

  const armed = applyArm(proposed, { goldArm: 'ARM', goldArmDate: '2024-03-05', halted: false, now: lockNow });
  assertEqual(armed.status, 'armed', 'armed');
  const filled = detectFill(
    armed,
    [{ time: Date.parse('2024-03-05T08:00:00Z'), high: armed.buy_stop + 1, low: armed.asia_low + 1, open: 2400, close: armed.buy_stop + 0.4, volume: 1 }],
    new Date('2024-03-05T08:30:00Z'),
    goldTestCfg
  );
  assertEqual(filled.status, 'filled', `fill ${filled.reason}`);
  assertEqual(filled.fill_side, 'BUY', 'oco buy only');

  const skipped = applyArm(proposed, { goldArm: 'SKIP', goldArmDate: '2024-03-05', halted: false, now: lockNow });
  assertEqual(skipped.status, 'skipped', 'skip command');

  const tiny = proposeSetup({ bars: goldAsiaBars(), now: lockNow, cfg: goldTestCfg, dailyAtrOverride: 200 });
  assertEqual(tiny.status, 'skipped', 'range too small vs daily atr');

  const nfp = proposeSetup({ bars: goldAsiaBars(), now: new Date('2026-09-04T08:00:00Z'), cfg: goldCfg, dailyAtrOverride: 20 });
  assertEqual(nfp.reason, 'skip_first_friday', 'first friday sit out');

  const xmNow = new Date('2024-03-05T06:00:00Z');
  assertEqual(inLondonWindow(xmNow, goldXmCfg), true, 'broker 08 is london');
  assertEqual(inLondonWindow(new Date('2024-03-05T04:00:00Z'), goldXmCfg), false, 'broker 06 is still asia');
  assertEqual(
    brokerHourStart(xmNow, 0, goldXmCfg),
    Date.parse('2024-03-04T22:00:00Z'),
    'asia start broker 0 = UTC prev 22:00'
  );
  assertEqual(
    brokerHourStart(xmNow, 7, goldXmCfg),
    Date.parse('2024-03-05T05:00:00Z'),
    'asia end broker 7 = UTC 05:00'
  );
  const waitingXm = proposeSetup({
    bars: goldAsiaBarsXm(),
    now: new Date('2024-03-05T04:00:00Z'),
    cfg: goldXmCfg,
    dailyAtrOverride: 20
  });
  assertEqual(waitingXm.reason, 'waiting_asia', 'XM +2 still in asia at 04:00 UTC');
  const xmRange = asianRange(goldAsiaBarsXm(), xmNow, goldXmCfg);
  assert(xmRange && xmRange.bars === 7, `xm asia bars ${xmRange && xmRange.bars}`);
  const xmProposed = proposeSetup({ bars: goldAsiaBarsXm(), now: xmNow, cfg: goldXmCfg, dailyAtrOverride: 20 });
  assertEqual(xmProposed.status, 'awaiting_arm', `xm propose ${xmProposed.status} ${xmProposed.reason}`);
  assertEqual(xmProposed.broker_utc_offset_hours, 2, 'setup records offset');
  const utcFridayEarly = proposeSetup({
    bars: goldAsiaBarsXm(),
    now: new Date('2026-09-03T23:00:00Z'),
    cfg: { ...goldXmCfg, skip_first_friday: true },
    dailyAtrOverride: 20
  });
  assertEqual(utcFridayEarly.reason, 'skip_first_friday', 'broker Friday after UTC Thursday');
  const utcFriNight = proposeSetup({
    bars: goldAsiaBarsXm(),
    now: new Date('2024-03-08T22:00:00Z'),
    cfg: goldXmCfg,
    dailyAtrOverride: 20
  });
  assertEqual(utcFriNight.reason, 'weekend', 'broker Saturday after UTC Friday 22:00');
  const xmArmed = applyArm(xmProposed, { goldArm: 'BUY', goldArmDate: '2024-03-05', halted: false, now: xmNow });
  const xmExpired = detectFill(xmArmed, goldAsiaBarsXm(), new Date('2024-03-05T09:00:00Z'), goldXmCfg);
  assertEqual(xmExpired.status, 'expired', 'london end at broker 11 = 09:00 UTC');

  console.log('self-test ok');
}

module.exports = { runSelfTest, makeBars };

if (require.main === module) {
  runSelfTest().catch((err) => {
    console.error(`self-test failed: ${err.message}`);
    process.exit(1);
  });
}
