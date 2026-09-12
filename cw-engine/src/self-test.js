'use strict';

const fs = require('fs');
const path = require('path');
const { ROOT, loadCapability, loadProfile } = require('./util');
const {
  ISSUE_TITLE,
  COMMANDS,
  defaultCommander,
  parseCommandText,
  parseQueueEvent,
  isDeskComment,
  applyCommand
} = require('./commander');
const { qualify, REASONS } = require('./qualify');
const {
  defaultQueue,
  addJob,
  applyEvent,
  counts,
  waitingHumanOverflow,
  catalogYenBlocked
} = require('./queue');
const { applyComment } = require('./apply-commander-comment');
const { deskLines } = require('./desk');
const { renderMarkdown } = require('./report');

function assert(cond, label) {
  if (!cond) throw new Error(label);
}

function sampleJob(over = {}) {
  return {
    id: '10000001',
    title: '素材支給の縦型ショート',
    category: 'video_edit_short',
    duration_sec: 30,
    materials_provided: true,
    on_camera: false,
    ai_forbidden: false,
    needs_portfolio: false,
    closed: false,
    already_applied: false,
    catalog_yen: 2000,
    public_apply_yen: null,
    ...over
  };
}

function selfTest() {
  const capability = loadCapability();
  const profile = loadProfile();
  assert(capability.account === 'fireworker12', 'capability account');
  assert(capability.max_concurrent_contracts === 1, 'max concurrent');
  assert(profile.has_completed_delivery === false, 'no invented delivery');

  const ok = qualify(sampleJob(), { capability, profile, commander: defaultCommander(), queue: defaultQueue() });
  assert(ok.ok, `qualify ok ${ok.reasons}`);
  assert(ok.catalog_yen_ignored, 'catalog ignored');

  const closed = qualify(sampleJob({ closed: true }), { capability, profile, commander: defaultCommander(), queue: defaultQueue() });
  assert(!closed.ok && closed.reasons.includes(REASONS.CLOSED), 'closed');

  const applied = qualify(sampleJob({ already_applied: true }), { capability, profile, commander: defaultCommander(), queue: defaultQueue() });
  assert(!applied.ok && applied.reasons.includes(REASONS.ALREADY_APPLIED), 'already');

  const cam = qualify(sampleJob({ on_camera: true }), { capability, profile, commander: defaultCommander(), queue: defaultQueue() });
  assert(!cam.ok && cam.reasons.includes(REASONS.ON_CAMERA), 'camera');

  const port = qualify(sampleJob({ needs_portfolio: true }), { capability, profile, commander: defaultCommander(), queue: defaultQueue() });
  assert(!port.ok && port.reasons.includes(REASONS.PORTFOLIO_REQUIRED), 'portfolio');

  const long = qualify(sampleJob({ duration_sec: 180 }), { capability, profile, commander: defaultCommander(), queue: defaultQueue() });
  assert(!long.ok && long.reasons.includes(REASONS.DURATION), 'duration');

  const halt = qualify(sampleJob(), {
    capability,
    profile,
    commander: { command: 'HALT' },
    queue: defaultQueue()
  });
  assert(!halt.ok && halt.reasons.includes(REASONS.HALTED), 'halt');

  const added = addJob(defaultQueue(), sampleJob(), {
    capability,
    profile,
    commander: defaultCommander(),
    now: new Date('2026-09-12T00:00:00.000Z')
  });
  assert(!added.skipped && added.job.status === 'qualified', 'add qualified');
  assert(added.job.approved_yen === null, 'no approved from catalog');
  assert(catalogYenBlocked(added.job), 'catalog blocked');

  const dup = addJob(added.queue, sampleJob(), { capability, profile, commander: defaultCommander() });
  assert(dup.skipped && dup.reason === 'duplicate', 'dup');

  const sent = applyEvent(added.queue, { type: 'SENT', id: '10000001' }, new Date('2026-09-12T01:00:00.000Z'));
  assert(!sent.skipped && sent.job.status === 'sent', 'sent');
  const contracted = applyEvent(sent.queue, { type: 'CONTRACT', id: '10000001' }, new Date('2026-09-12T02:00:00.000Z'));
  assert(contracted.job.status === 'contracted', 'contract');
  const overCap = qualify(sampleJob({ id: '10000002' }), {
    capability,
    profile,
    commander: defaultCommander(),
    queue: contracted.queue
  });
  assert(!overCap.ok && overCap.reasons.includes(REASONS.CAPACITY), 'capacity');

  const n = counts(added.queue);
  assert(n.qualified === 1 && n.waiting_human === 0, 'counts');

  const draftedQueue = {
    jobs: [
      { id: '1', status: 'drafted' },
      { id: '2', status: 'drafted' },
      { id: '3', status: 'drafted' }
    ]
  };
  assert(waitingHumanOverflow(draftedQueue, capability), 'overflow');

  assert(parseCommandText('CW: HALT') === 'HALT', 'parse halt');
  assert(parseCommandText('CW: RESUME') === null, 'no resume');
  assert(parseCommandText('KILL_SWITCH: HALT') === null, 'no xm cmd');
  assert(COMMANDS.includes('HALT') && COMMANDS.includes('PAPER_ONLY'), 'commands');
  assert(!COMMANDS.includes('RESUME'), 'no live apply resume');
  assert(parseQueueEvent('CW: SENT 10000001').type === 'SENT', 'sent event');
  assert(isDeskComment('cw-desk: paper\ncommand: PAPER_ONLY'), 'desk');
  assert(!isDeskComment('CW: HALT'), 'halt not desk');

  const halted = applyCommand(defaultCommander(), {
    command: 'HALT',
    source: 'test',
    reason: 'stop',
    now: new Date('2026-09-12T00:00:00.000Z')
  });
  assert(halted.command === 'HALT' && halted.previous === 'PAPER_ONLY', 'apply halt');

  const skipDesk = applyComment({
    body: 'cw-desk: paper',
    login: 'n',
    persist: false,
    current: defaultCommander(),
    queue: defaultQueue()
  });
  assert(skipDesk.skipped && skipDesk.reason === 'notify-comment', 'skip desk');

  const skipBot = applyComment({
    body: 'CW: HALT',
    login: 'github-actions[bot]',
    persist: false,
    current: defaultCommander(),
    queue: defaultQueue()
  });
  assert(skipBot.skipped && skipBot.reason === 'actions-bot', 'skip bot');

  const appliedCmd = applyComment({
    body: 'CW: HALT',
    login: 'naomichi',
    persist: false,
    current: defaultCommander(),
    queue: defaultQueue(),
    now: new Date('2026-09-12T00:00:00.000Z')
  });
  assert(!appliedCmd.skipped && appliedCmd.command === 'HALT', 'apply comment halt');

  const desk = deskLines({
    commander: defaultCommander(),
    queue: defaultQueue(),
    capability,
    now: new Date('2026-09-12T00:00:00.000Z')
  });
  assert(desk[0] === 'cw-desk: paper', 'desk head');
  assert(desk.some((l) => l === 'remain_n10: parked'), 'parked line');
  assert(desk.some((l) => l.startsWith('command: PAPER_ONLY')), 'desk command');

  const md = renderMarkdown({
    commander: defaultCommander(),
    queue: defaultQueue(),
    capability,
    now: new Date('2026-09-12T00:00:00.000Z')
  });
  assert(/司令塔ステータス/.test(md), 'md status');
  assert(/remain \/ n10/.test(md), 'md parked');
  assert(!/13406725/.test(md), 'no leftover job id');
  assert(!/approved_yen: 2000/.test(md), 'no catalog as approved');

  const dump = fs.readFileSync(path.join(ROOT, 'docs/grok-bots/G_cw.txt'), 'utf8');
  assert(/remain \/ n10/.test(dump), 'dump mentions parked');
  assert(!/G_hq_cw_remain/.test(dump), 'dump does not open remain');
  assert(!/G_hq_cw_n10/.test(dump), 'dump does not open n10');
  assert(!/パスワード/.test(dump) || /パスワードを聞くな/.test(dump), 'no secret prompt');
  assert(/ジャンルbot/.test(dump), 'no genre bots');
  assert(/CW: HALT/.test(dump), 'halt cmd');
  assert(!/CW: RESUME/.test(dump) || /RESUME` は出すな/.test(dump), 'resume forbidden');
  assert(!/crowdworks\.jp\/public\/jobs\/\d+/.test(dump), 'no live apply urls');

  const boot = fs.readFileSync(path.join(ROOT, '../affiliate-engine/docs/grok-bots/dump/G_hq_boot.txt'), 'utf8');
  assert(/CW: GO/.test(boot), 'boot has CW GO');
  assert(/G_hq_cw_remain/.test(boot) && /開けるな/.test(boot), 'remain still parked');

  const machine = fs.readFileSync(path.join(ROOT, '../affiliate-engine/docs/grok-bots/MACHINE.md'), 'utf8');
  assert(/CW: GO/.test(machine), 'machine has CW');
  assert(/G_hq_cw_remain/.test(machine), 'machine keeps remain parked');

  const yml = fs.readFileSync(path.join(ROOT, '../.github/workflows/cw_engine_ci.yml'), 'utf8');
  assert(!/^\s*schedule:/m.test(yml), 'ci has no cron');
  const cmdYml = fs.readFileSync(path.join(ROOT, '../.github/workflows/cw_engine_commander.yml'), 'utf8');
  assert(!/^\s*schedule:/m.test(cmdYml), 'commander has no cron');
  assert(cmdYml.includes(ISSUE_TITLE), 'commander issue title');

  const agents = fs.readFileSync(path.join(ROOT, 'docs/AGENTS.md'), 'utf8');
  assert(/Grok Bot.*1/.test(agents), 'one grok bot');
  assert(/常時稼働.*0/.test(agents), 'zero always-on agents');

  process.stdout.write('cw-engine self-test ok\n');
}

if (require.main === module) {
  selfTest();
}

module.exports = { selfTest };
