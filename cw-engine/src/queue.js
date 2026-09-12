'use strict';

const path = require('path');
const { OUTPUT_DIR, readJSON, writeJSON } = require('./util');
const { qualify } = require('./qualify');

const QUEUE_PATH = path.join(OUTPUT_DIR, 'state', 'queue.json');
const STATUSES = ['scouted', 'qualified', 'drafted', 'sent', 'contracted', 'delivering', 'delivered', 'rejected', 'closed'];

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

function counts(queue) {
  const jobs = queue?.jobs || [];
  const n = (status) => jobs.filter((j) => j.status === status).length;
  return {
    total: jobs.length,
    qualified: n('qualified'),
    drafted: n('drafted'),
    sent: n('sent'),
    contracted: n('contracted') + n('delivering'),
    waiting_human: n('drafted')
  };
}

function waitingHumanOverflow(queue, capability) {
  const max = Number(capability?.max_drafts_waiting_human || 3);
  return counts(queue).waiting_human >= max;
}

function addJob(queue, job, ctx) {
  const id = String(job?.id || '').trim();
  if (!id) return { skipped: true, reason: 'missing_id', queue };
  if ((queue.jobs || []).some((j) => String(j.id) === id)) {
    return { skipped: true, reason: 'duplicate', queue };
  }
  const verdict = qualify(job, ctx);
  const next = {
    id,
    title: job.title || '',
    category: job.category || '',
    status: verdict.ok ? 'qualified' : 'rejected',
    reasons: verdict.ok ? [] : verdict.reasons,
    public_apply_yen: job.public_apply_yen == null ? null : job.public_apply_yen,
    catalog_yen: job.catalog_yen == null ? null : job.catalog_yen,
    approved_yen: null,
    already_applied: Boolean(job.already_applied),
    closed: Boolean(job.closed)
  };
  const jobs = [...(queue.jobs || []), next];
  return {
    skipped: false,
    verdict,
    job: next,
    queue: { jobs, updated_at: (ctx?.now || new Date()).toISOString() }
  };
}

function applyEvent(queue, event, now) {
  if (!event) return { skipped: true, reason: 'no_event', queue };
  const id = String(event.id || '').trim();
  const jobs = (queue.jobs || []).map((j) => ({ ...j }));
  const hit = jobs.find((j) => String(j.id) === id);
  if (!hit) return { skipped: true, reason: 'unknown_id', queue };
  switch (event.type) {
    case 'SENT':
      hit.status = 'sent';
      break;
    case 'CONTRACT':
      hit.status = 'contracted';
      break;
    case 'REJECT':
      hit.status = 'rejected';
      break;
    default: {
      const _never = event.type;
      return { skipped: true, reason: `unknown_type:${_never}`, queue };
    }
  }
  return {
    skipped: false,
    job: hit,
    queue: { jobs, updated_at: (now || new Date()).toISOString() }
  };
}

function catalogYenBlocked(job) {
  return job?.catalog_yen != null && job?.approved_yen == null;
}

module.exports = {
  QUEUE_PATH,
  STATUSES,
  defaultQueue,
  loadQueue,
  saveQueue,
  counts,
  waitingHumanOverflow,
  addJob,
  applyEvent,
  catalogYenBlocked
};
