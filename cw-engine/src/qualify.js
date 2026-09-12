'use strict';

const REASONS = {
  CLOSED: 'closed',
  ALREADY_APPLIED: 'already_applied',
  ON_CAMERA: 'on_camera',
  NO_MATERIALS: 'no_materials',
  AI_FORBIDDEN: 'ai_forbidden',
  PORTFOLIO_REQUIRED: 'portfolio_required_without_delivery',
  CATEGORY: 'category_not_allowed',
  DURATION: 'duration_too_long',
  CAPACITY: 'over_concurrent_capacity',
  MISSING_ID: 'missing_id',
  HALTED: 'commander_halt'
};

const ALLOWED_CATEGORIES = new Set(['video_edit_short']);

function reasonList() {
  return Object.freeze({ ...REASONS });
}

function qualify(job, { capability, profile, commander, queue } = {}) {
  const reasons = [];
  const id = String(job?.id || '').trim();
  if (!id) reasons.push(REASONS.MISSING_ID);
  if (job?.closed) reasons.push(REASONS.CLOSED);
  if (job?.already_applied) reasons.push(REASONS.ALREADY_APPLIED);
  if (job?.on_camera) reasons.push(REASONS.ON_CAMERA);
  if (job?.ai_forbidden) reasons.push(REASONS.AI_FORBIDDEN);
  if (job?.materials_provided !== true) reasons.push(REASONS.NO_MATERIALS);
  if (job?.category && !ALLOWED_CATEGORIES.has(job.category)) reasons.push(REASONS.CATEGORY);
  const allow = (capability?.allow || []).find((a) => a.category === job?.category);
  if (!allow) reasons.push(REASONS.CATEGORY);
  const maxSec = allow?.duration_sec_max || 60;
  if (Number.isFinite(job?.duration_sec) && job.duration_sec > maxSec) reasons.push(REASONS.DURATION);
  const hasDelivery = Boolean(profile?.has_completed_delivery) || Number(profile?.completed_deliveries) > 0;
  if (job?.needs_portfolio && !hasDelivery) reasons.push(REASONS.PORTFOLIO_REQUIRED);
  const maxConcurrent = Number(capability?.max_concurrent_contracts || 1);
  const contracted = (queue?.jobs || []).filter((j) => j.status === 'contracted' || j.status === 'delivering').length;
  if (contracted >= maxConcurrent) reasons.push(REASONS.CAPACITY);
  if (commander?.command === 'HALT') reasons.push(REASONS.HALTED);

  const unique = [...new Set(reasons)];
  return {
    ok: unique.length === 0,
    reasons: unique,
    catalog_yen_ignored: true
  };
}

function assertKnownReason(code) {
  const known = new Set(Object.values(REASONS));
  if (!known.has(code)) throw new Error(`unknown reason: ${code}`);
  return code;
}

module.exports = {
  REASONS,
  ALLOWED_CATEGORIES,
  reasonList,
  qualify,
  assertKnownReason
};
