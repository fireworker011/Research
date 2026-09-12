'use strict';

const { counts, waitingHumanOverflow } = require('./queue');

function deskLines({ commander, queue, capability, now }) {
  const n = counts(queue);
  const overflow = waitingHumanOverflow(queue, capability);
  const stamp = (now || new Date()).toISOString();
  return [
    'cw-desk: paper',
    `generated: ${stamp}`,
    `command: ${commander?.command || 'PAPER_ONLY'}`,
    `concurrent_contracts: ${n.contracted}`,
    `queue_total: ${n.total}`,
    `qualified: ${n.qualified}`,
    `drafted_waiting_human: ${n.waiting_human}`,
    `sent: ${n.sent}`,
    overflow
      ? 'human_gate: drafts_full 新しい応募宿題を出すな'
      : 'human_gate: copy_table_only',
    'approved_yen: not_from_catalog',
    'remain_n10: parked'
  ];
}

module.exports = { deskLines };
