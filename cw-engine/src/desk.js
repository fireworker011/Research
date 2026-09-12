'use strict';

const { counts, waitingHumanOverflow } = require('./queue');

function nextHumanAction(queue, capability, commander) {
  const jobs = queue?.jobs || [];
  if (commander?.command === 'HALT') return 'HALT 中。新規 JOB は資格判定で落ちる。再開は CW: PAPER_ONLY';
  const ready = jobs.filter((j) => j.status === 'ready');
  if (ready.length) return `納品待ち ${ready.length} 件（${ready.map((j) => j.id).join(', ')}）。DELIVERY.md を見て納品ボタン → CW: DELIVERED <id>`;
  const qaFailed = jobs.filter((j) => j.status === 'qa_failed');
  if (qaFailed.length) {
    return `QA 不合格 ${qaFailed.length} 件（${qaFailed.map((j) => j.id).join(', ')}）。直した本文を CW: DRAFT <id>、または素材を足して CW: MAKE <id>`;
  }
  const making = jobs.filter((j) => j.status === 'making');
  if (making.length) {
    return `完成品待ち ${making.length} 件（${making.map((j) => j.id).join(', ')}）。Grok が本文を書き CW: DRAFT <id>（Anthropic 不要）`;
  }
  const contracted = jobs.filter((j) => j.status === 'contracted');
  if (contracted.length) return `契約済み ${contracted.length} 件（${contracted.map((j) => j.id).join(', ')}）。素材を貼って CW: MAKE <id>`;
  const drafted = jobs.filter((j) => j.status === 'drafted');
  if (drafted.length) {
    const full = waitingHumanOverflow(queue, capability);
    return `下書き ${drafted.length} 件（${drafted.map((j) => j.id).join(', ')}）。貼って送るなら CW: SENT <id>、見送りは CW: SKIP <id>${full ? '。下書きは満杯。新しい JOB は増やすな' : ''}`;
  }
  const sent = jobs.filter((j) => j.status === 'sent');
  if (sent.length) return `返事待ち ${sent.length} 件。契約したら CW: CONTRACT <id>、断られたら CW: REJECT <id>。新しい JOB を足してよい`;
  return 'キュー空。公開ページの仕事 ID を CW: JOB <id> で入れる（本文を貼れば確実）';
}

function deskLines({ commander, queue, capability, funnel, ledgerYen = 0, now }) {
  const n = counts(queue);
  const stamp = (now || new Date()).toISOString();
  return [
    'cw-desk: paper',
    `generated: ${stamp}`,
    `command: ${commander?.command || 'PAPER_ONLY'}`,
    `queue_total: ${n.total}`,
    `qualified: ${n.qualified} / drafted: ${n.drafted} / sent: ${n.sent}`,
    `contracted: ${n.contracted} (making ${n.making}, qa_failed ${n.qa_failed}, ready ${n.ready})`,
    `delivered: ${n.delivered} / paid: ${n.paid}`,
    `confirmed_yen_total: ${ledgerYen}（画面で見た確定だけ。カタログではない）`,
    `gate: ${funnel ? funnel.gate : 'intake'}`,
    `next_human: ${nextHumanAction(queue, capability, commander)}`,
    'auto_send: never（応募送信・契約・納品ボタンは人間が許可すれば送ることは🉑）'
  ];
}

module.exports = { deskLines, nextHumanAction };
