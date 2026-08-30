'use strict';

const SUCCESS = new Set([
  'ERR_NO_ERROR',
  'TRADE_RETCODE_PLACED',
  'TRADE_RETCODE_DONE',
  'TRADE_RETCODE_DONE_PARTIAL',
  'TRADE_RETCODE_NO_CHANGES'
]);

function baseUrl(env) {
  return env.METAAPI_DOMAIN
    || 'https://mt-client-api-v1.new-york.agiliumtrade.ai';
}

function headers(token) {
  return {
    'auth-token': token,
    'content-type': 'application/json',
    accept: 'application/json'
  };
}

async function metaapiFetch(env, pathname, { method = 'GET', body } = {}) {
  const token = env.METAAPI_TOKEN;
  const accountId = env.METAAPI_ACCOUNT_ID;
  if (!token || !accountId) throw new Error('MetaApi secrets missing');
  const url = `${baseUrl(env)}/users/current/accounts/${accountId}${pathname}`;
  const res = await fetch(url, {
    method,
    headers: headers(token),
    body: body ? JSON.stringify(body) : undefined
  });
  const text = await res.text();
  let json = null;
  try { json = JSON.parse(text); } catch (_) { json = { raw: text }; }
  if (!res.ok) {
    throw new Error(`MetaApi HTTP ${res.status}: ${json.message || text.slice(0, 200)}`);
  }
  return json;
}

async function getAccount(env) {
  return metaapiFetch(env, '/account-information');
}

async function getPositions(env) {
  return metaapiFetch(env, '/positions');
}

function tradeBody(intent) {
  if (intent.action === 'CLOSE') {
    return {
      actionType: 'POSITIONS_CLOSE_SYMBOL',
      symbol: intent.symbol
    };
  }
  if (intent.action === 'BUY' || intent.action === 'SELL') {
    return {
      actionType: intent.action === 'BUY' ? 'ORDER_TYPE_BUY' : 'ORDER_TYPE_SELL',
      symbol: intent.symbol,
      volume: intent.lot,
      stopLoss: intent.sl,
      takeProfit: intent.tp,
      clientId: intent.clientId || `xmge_${intent.symbol}`
    };
  }
  return null;
}

function isSuccess(response) {
  const code = response?.stringCode || '';
  const numeric = response?.numericCode;
  return SUCCESS.has(code) || numeric === 0 || (numeric >= 10008 && numeric <= 10010) || numeric === 10025;
}

async function submitTrade(env, intent) {
  const body = tradeBody(intent);
  if (!body) return { skipped: true, reason: 'not_an_order' };
  const response = await metaapiFetch(env, '/trade', { method: 'POST', body });
  return { ok: isSuccess(response), response };
}

module.exports = {
  getAccount,
  getPositions,
  submitTrade,
  tradeBody,
  isSuccess
};
