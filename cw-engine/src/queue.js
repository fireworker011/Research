'use strict';

const { workPath, readJSON, writeJSON, nowIso } = require('./util');

const QUEUE_PATH = workPath('state', 'queue.json');

const STATUSES = Object.freeze([
  'scouted',
  'rejected',
  'qualified',
  'drafted',
  'sent',
  'skipped',
  'lost',
  'contracted',
  'making',
  'qa_failed',
  'ready',
  'delivered',
  'paid'
]);

const EVENTS = Object.freeze([
  'QUALIFY_OK',
  'QUALIFY_NG',
  'DRAFTED',
  'SENT',
  'SKIP',
  'REJECT',
  'CONTRACT',
  'MAKE',
  'QA_FAIL',
  'QA_PASS',
  'DELIVERED',
  'PAID'
]);

const TRANSITIONS = Object.freeze({
  QUALIFY_OK: { from: ['scouted', 'rejected'], to: 'qualified' },
  QUALIFY_NG: { from: ['scouted', 'qualified'], to: 'rejected' },
  DRAFTED: { from: ['qualified', 'drafted'], to: 'drafted' },
  SENT: { from: ['qualified', 'drafted', 'sent'], to: 'sent' },
  SKIP: { from: ['scouted', 'rejected', 'qualified', 'drafted', 'sent'], to: 'skipped' },
  REJECT: { from: ['sent', 'contracted', 'making', 'qa_failed', 'ready', 'delivered', 'drafted', 'qualified'], to: 'lost' },
  CONTRACT: { from: ['sent', 'drafted', 'qualified', 'skipped'], to: 'contracted' },
  MAKE: { from: ['contracted', 'making', 'qa_failed', 'ready', 'delivered'], to: 'making' },
  QA_FAIL: { from: ['making'], to: 'qa_failed' },
  QA_PASS: { from: ['making'], to: 'ready' },
  DELIVERED: { from: ['ready', 'making', 'qa_failed', 'contracted', 'delivered'], to: 'delivered' },
  PAID: { from: ['delivered', 'ready', 'paid'], to: 'paid' }
});

function defaultQueue() {
  return { jobs: [], updated_at: '2026-09-12T00:00:00.000Z' };
}

function loadQueue() {
  const q = readJSON(QUEUE_PATH, defaultQueue());
  if (!Array.isArray(q.jobs)) q.jobs = [];
  return q;
}

function saveQueue(data) {
  return writeJSON(QUEUE_PATH, data);
}

function findJob(queue, id) {
  return (queue?.jobs || []).find((j) => String(j.id) === String(id)) || null;
}

function upsertJob(queue, job, now) {
  const jobs = (queue.jobs || []).filter((j) => String(j.id) !== String(job.id));
  jobs.push(job);
  jobs.sort((a, b) => String(a.id).localeCompare(String(b.id)));
  return { jobs, updated_at: nowIso(now) };
}

function newJobRecord(parsed, verdict, now) {
  return {
    id: parsed.id,
    title: parsed.title || '',
    category: parsed.category || 'unknown',
    status: verdict.ok ? 'qualified' : 'rejected',
    reasons: verdict.ok ? [] : verdict.reasons,
    warnings: verdict.warnings || [],
    priority: verdict.priority || 0,
    flags: parsed.flags || {},
    asks: parsed.asks || [],
    deadline: parsed.deadline || null,
    applicants: parsed.applicants,
    contracted: parsed.contracted,
    openings: parsed.openings,
    public_price_yen: parsed.public_price_yen == null ? null : parsed.public_price_yen,
    char_spec: parsed.char_spec || null,
    confirmed_yen: null,
    drafts: 0,
    messages: 0,
    revisions: 0,
    created_at: nowIso(now),
    updated_at: nowIso(now),
    history: [{ at: nowIso(now), event: verdict.ok ? 'QUALIFY_OK' : 'QUALIFY_NG' }]
  };
}

function transition(job, event, now) {
  const rule = TRANSITIONS[event];
  if (!rule) return { ok: false, reason: `unknown_event:${event}`, job };
  if (!rule.from.includes(job.status)) return { ok: false, reason: `bad_state:${job.status}->${event}`, job };
  const next = { ...job, status: rule.to, updated_at: nowIso(now), history: [...(job.history || []), { at: nowIso(now), event }] };
  switch (event) {
    case 'DRAFTED':
      next.drafts = Number(job.drafts || 0) + 1;
      break;
    case 'MAKE':
      if (job.status !== 'contracted') next.revisions = Number(job.revisions || 0) + 1;
      break;
    case 'QUALIFY_OK':
    case 'QUALIFY_NG':
    case 'SENT':
    case 'SKIP':
    case 'REJECT':
    case 'CONTRACT':
    case 'QA_FAIL':
    case 'QA_PASS':
    case 'DELIVERED':
    case 'PAID':
      break;
    default: {
      const _never = event;
      return { ok: false, reason: `unhandled_event:${_never}`, job };
    }
  }
  return { ok: true, job: next };
}

function counts(queue) {
  const jobs = queue?.jobs || [];
  const n = (...statuses) => jobs.filter((j) => statuses.includes(j.status)).length;
  return {
    total: jobs.length,
    rejected: n('rejected'),
    qualified: n('qualified'),
    drafted: n('drafted'),
    sent: n('sent'),
    skipped: n('skipped'),
    lost: n('lost'),
    contracted: n('contracted', 'making', 'qa_failed', 'ready'),
    making: n('making'),
    qa_failed: n('qa_failed'),
    ready: n('ready'),
    delivered: n('delivered'),
    paid: n('paid'),
    waiting_human: n('drafted', 'ready')
  };
}

function waitingHumanOverflow(queue, capability) {
  const max = Number(capability?.max_drafts_waiting_human || 3);
  return counts(queue).drafted >= max;
}

function catalogYenBlocked(job) {
  return job?.public_price_yen != null && job?.confirmed_yen == null;
}

module.exports = {
  QUEUE_PATH,
  STATUSES,
  EVENTS,
  TRANSITIONS,
  defaultQueue,
  loadQueue,
  saveQueue,
  findJob,
  upsertJob,
  newJobRecord,
  transition,
  counts,
  waitingHumanOverflow,
  catalogYenBlocked
};
