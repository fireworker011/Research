'use strict';

const commanderMod = require('./commander');

async function findTrackingIssue(headers, repo) {
  const base = `https://api.github.com/repos/${repo}`;
  const searchRes = await fetch(`${base}/issues?state=open&per_page=100`, { headers });
  const existing = await searchRes.json().catch(() => []);
  if (!Array.isArray(existing)) return null;
  return existing.find((i) => i.title === commanderMod.ISSUE_TITLE) || null;
}

/**
 * Issue「XM Trade — 日次レポート」へ告知コメント。指令ではない。
 * marker が既存コメントにあれば送らない。
 */
async function postIssueMarker({ marker, lines, env = process.env } = {}) {
  const token = env.GITHUB_TOKEN || '';
  const repo = env.GITHUB_REPOSITORY || '';
  if (!token || !repo || !marker) return { posted: false, reason: 'no_token_or_marker' };
  const headers = {
    Authorization: `token ${token}`,
    Accept: 'application/vnd.github.v3+json',
    'content-type': 'application/json'
  };
  const found = await findTrackingIssue(headers, repo);
  if (!found) return { posted: false, reason: 'no_issue' };
  const base = `https://api.github.com/repos/${repo}`;
  const commentsRes = await fetch(`${base}/issues/${found.number}/comments?per_page=100`, { headers });
  const comments = await commentsRes.json().catch(() => []);
  if (Array.isArray(comments) && comments.some((c) => String(c.body || '').includes(marker))) {
    return { posted: false, reason: 'already', issue: found.number };
  }
  const body = [marker, '', ...(lines || [])].join('\n');
  const res = await fetch(`${base}/issues/${found.number}/comments`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ body })
  });
  if (!res.ok) return { posted: false, reason: `http_${res.status}`, issue: found.number };
  return { posted: true, issue: found.number, marker };
}

function virtualDeskCommentLines(gold, book) {
  const pending = (book?.pending || []).find((p) => p.symbol === 'GOLD' && p.status === 'working');
  const lot = gold?.lot ?? pending?.lot ?? '—';
  return [
    'ペーパー仮想トレード（XM残高ではない）。指令ではない。Grok は ENTRY を出すな。',
    `status ${gold?.status || '—'} / reason ${gold?.reason || '—'} / lot ${lot}`,
    gold?.asia_high != null
      ? `asia ${gold.asia_low} – ${gold.asia_high} close ${gold.asia_close} range ${gold.range}`
      : 'asia —',
    `BuyStop ${gold?.buy_stop ?? '—'} 損切り ${gold?.buy_sl ?? '—'} 利確 ${gold?.buy_tp ?? '—'}`,
    `SellStop ${gold?.sell_stop ?? '—'} 損切り ${gold?.sell_sl ?? '—'} 利確 ${gold?.sell_tp ?? '—'}`,
    `H1 ATR ${gold?.h1_atr ?? '—'} SL距離 ${gold?.sl_distance ?? '—'} TP距離 ${gold?.tp_distance ?? '—'} (${gold?.h1_atr_source || 'rules'})`,
    `chart suggested_side: ${gold?.suggested_side || 'NONE'}（参考。執行は OCO 両方）`,
    '',
    '人間へは上の表を写せ。無い数字は未確認。方向を予想するな。',
    '止めるなら `KILL_SWITCH: HALT` または `SKIP: GOLD`。'
  ];
}

module.exports = {
  findTrackingIssue,
  postIssueMarker,
  virtualDeskCommentLines
};
