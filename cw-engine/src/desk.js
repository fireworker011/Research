'use strict';

const { counts, waitingHumanOverflow } = require('./queue');

function nextHumanAction(queue, capability, commander) {
  const jobs = queue?.jobs || [];
  if (commander?.command === 'HALT') return 'HALT 中。再開は CW: PAPER_ONLY。契約・外部案内・納品以外は触るな';
  const ready = jobs.filter((j) => j.status === 'ready');
  if (ready.length) {
    return `納品 ${ready.length} 件（${ready.map((j) => j.id).join(', ')}）。外部サイトで納品ボタン → CW: DELIVERED <id>。案内・誘導も人間`;
  }
  const sent = jobs.filter((j) => j.status === 'sent');
  if (sent.length) {
    return `契約待ち ${sent.length} 件（${sent.map((j) => j.id).join(', ')}）。受けるなら CW: CONTRACT <id>、断るなら CW: REJECT <id>。外部サイトへの案内・誘導は人間。応募・下書きは Grok`;
  }
  return 'なし。人間は案件の契約・外部サイトの案内誘導・納品だけ';
}

function nextGrokAction(queue, capability, commander) {
  const jobs = queue?.jobs || [];
  if (commander?.command === 'HALT') return 'HALT。新規 JOB と応募をするな';
  const qaFailed = jobs.filter((j) => j.status === 'qa_failed');
  if (qaFailed.length) {
    return `QA 不合格 ${qaFailed.length} 件（${qaFailed.map((j) => j.id).join(', ')}）。直して CW: DRAFT <id>`;
  }
  const making = jobs.filter((j) => j.status === 'making');
  if (making.length) {
    return `完成品 ${making.length} 件（${making.map((j) => j.id).join(', ')}）。本文を書いて CW: DRAFT <id>`;
  }
  const contracted = jobs.filter((j) => j.status === 'contracted');
  if (contracted.length) {
    return `素材待ち ${contracted.length} 件（${contracted.map((j) => j.id).join(', ')}）。CW内の素材を CW: MAKE <id>。契約ボタン・納品ボタン・外部誘導はするな`;
  }
  const drafted = jobs.filter((j) => j.status === 'drafted');
  if (drafted.length) {
    const full = waitingHumanOverflow(queue, capability);
    return `下書き ${drafted.length} 件（${drafted.map((j) => j.id).join(', ')}）。CWで応募して CW: SENT <id>。落ちたら SKIP${full ? '。下書き満杯。新しい JOB は増やすな' : ''}`;
  }
  const sent = jobs.filter((j) => j.status === 'sent');
  if (sent.length) {
    return `返事待ち ${sent.length} 件。CW内の相手文を CW: MSG <id>。返信下書きをCW内に貼る。契約・外部誘導・納品はするな`;
  }
  return 'キュー空。公開の文章系を1件 CW: JOB <id> + 公開文';
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
    `next_grok: ${nextGrokAction(queue, capability, commander)}`,
    'auto_send: grok（応募は Grok。契約・外部案内誘導・納品は人間）'
  ];
}

module.exports = { deskLines, nextHumanAction, nextGrokAction };
