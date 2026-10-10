'use strict';

const { counts } = require('./queue');

const GATES = Object.freeze({
  sentNoContract: 8,
  contractedNoDelivery: 1,
  paidToRaiseCapacity: 2
});

function funnel(queue, { ledgerYen = 0, capability } = {}) {
  const n = counts(queue);
  const jobs = queue?.jobs || [];
  const everSent = jobs.filter((j) => (j.history || []).some((h) => h.event === 'SENT')).length;
  const everContracted = jobs.filter((j) => (j.history || []).some((h) => h.event === 'CONTRACT')).length;
  const everDelivered = jobs.filter((j) => (j.history || []).some((h) => h.event === 'DELIVERED')).length;
  const everPaid = jobs.filter((j) => (j.history || []).some((h) => h.event === 'PAID')).length;
  const advice = [];
  let gate = 'intake';
  if (everSent >= GATES.sentNoContract && everContracted === 0) {
    gate = 'improve_profile';
    advice.push(`送信 ${everSent} 件で契約 0。改善は1つだけ: プロフィールを再生成して差し替える（CW: PROFILE）。カテゴリは文章系に寄せる`);
  } else if (everContracted >= GATES.contractedNoDelivery && everDelivered === 0) {
    gate = 'deliver_first';
    advice.push('契約はあるが納品 0。新規応募より納品を先に（CW: MAKE）');
  } else if (everPaid >= GATES.paidToRaiseCapacity) {
    gate = 'scale';
    advice.push(`確定 ${everPaid} 件。同時契約上限（今 ${capability?.max_concurrent_contracts || 1}）を +1 するかは人間が config で決める`);
  } else if (everSent > 0) {
    gate = 'wait_reply';
  }
  return {
    counts: n,
    ever: { sent: everSent, contracted: everContracted, delivered: everDelivered, paid: everPaid },
    ledger_yen: ledgerYen,
    gate,
    advice
  };
}

module.exports = { GATES, funnel };
