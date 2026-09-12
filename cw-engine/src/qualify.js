'use strict';

const { categoryById } = require('./util');

const REASONS = Object.freeze({
  MISSING_ID: 'missing_id',
  CLOSED: 'closed',
  ALREADY_APPLIED: 'already_applied',
  ON_CAMERA: 'on_camera',
  AI_FORBIDDEN: 'ai_forbidden',
  REVIEW_POSTING: 'tos_review_posting',
  SEO_MANIPULATION: 'tos_seo_manipulation',
  RANKING: 'tos_ranking_manipulation',
  AFFILIATE_REG: 'tos_affiliate_registration',
  ACCOUNT_WORK: 'tos_account_work',
  MLM: 'tos_mlm',
  ACADEMIC: 'academic_ghostwriting',
  ADULT: 'adult',
  PERSONAL_DATA: 'personal_data_handling',
  PORTFOLIO_REQUIRED: 'portfolio_required_without_delivery',
  CATEGORY_UNKNOWN: 'category_unknown',
  NOT_AI_COMPLETE: 'not_ai_complete_without_materials',
  CAPACITY: 'over_concurrent_capacity',
  HALTED: 'commander_halt'
});

const WARNINGS = Object.freeze({
  EXTERNAL_CONTACT: 'external_contact_first',
  PREPAY: 'prepay_risk',
  AI_DISCLOSE: 'ai_disclose_required',
  SCHOOL: 'school_excluded',
  HUMAN_TOOL: 'human_tool_required',
  CROWDED: 'crowded'
});

const DENY_FLAG_TO_REASON = Object.freeze({
  closed: REASONS.CLOSED,
  already_applied: REASONS.ALREADY_APPLIED,
  on_camera: REASONS.ON_CAMERA,
  ai_forbidden: REASONS.AI_FORBIDDEN,
  review_posting: REASONS.REVIEW_POSTING,
  seo_manipulation: REASONS.SEO_MANIPULATION,
  ranking_manipulation: REASONS.RANKING,
  affiliate_registration: REASONS.AFFILIATE_REG,
  account_work: REASONS.ACCOUNT_WORK,
  mlm: REASONS.MLM,
  academic: REASONS.ACADEMIC,
  adult: REASONS.ADULT,
  personal_data: REASONS.PERSONAL_DATA
});

function activeContracts(queue) {
  return (queue?.jobs || []).filter((j) => ['contracted', 'making', 'qa_failed', 'ready'].includes(j.status)).length;
}

function priorityOf(job, category) {
  let p = category ? Number(category.priority || 0) : 0;
  const f = job.flags || {};
  if (f.unexperienced_ok) p += 10;
  if (f.continuous) p += 10;
  if (Number.isFinite(job.openings) && Number.isFinite(job.applicants) && job.openings > job.applicants) p += 10;
  if ((job.asks || []).length <= 3) p += 5;
  if (category && category.ai_complete === false) p -= 40;
  return p;
}

function qualify(job, { capability, facts, commander, queue } = {}) {
  const reasons = [];
  const warnings = [];
  const flags = job?.flags || {};
  if (!String(job?.id || '').trim()) reasons.push(REASONS.MISSING_ID);
  for (const [flag, reason] of Object.entries(DENY_FLAG_TO_REASON)) {
    if (flags[flag]) reasons.push(reason);
  }
  const category = categoryById(capability, job?.category);
  if (!category) reasons.push(REASONS.CATEGORY_UNKNOWN);
  const deliveries = Number(facts?.public_profile_facts?.deliveries_completed || 0);
  if (flags.needs_portfolio && deliveries === 0 && !facts?.public_profile_facts?.portfolio_url) {
    reasons.push(REASONS.PORTFOLIO_REQUIRED);
  }
  if (category && category.ai_complete === false) {
    if (!flags.materials_provided) reasons.push(REASONS.NOT_AI_COMPLETE);
    else warnings.push(WARNINGS.HUMAN_TOOL);
  }
  const maxConcurrent = Number(capability?.max_concurrent_contracts || 1);
  if (activeContracts(queue) >= maxConcurrent) reasons.push(REASONS.CAPACITY);
  if (commander?.command === 'HALT') reasons.push(REASONS.HALTED);

  if (flags.external_contact_first) warnings.push(WARNINGS.EXTERNAL_CONTACT);
  if (flags.prepay_risk) warnings.push(WARNINGS.PREPAY);
  if (flags.ai_disclose_required) warnings.push(WARNINGS.AI_DISCLOSE);
  if (flags.school_excluded) warnings.push(WARNINGS.SCHOOL);
  if (Number.isFinite(job?.applicants) && Number.isFinite(job?.openings) && job.openings > 0 && job.applicants / job.openings >= 10) {
    warnings.push(WARNINGS.CROWDED);
  }

  const unique = [...new Set(reasons)];
  return {
    ok: unique.length === 0,
    reasons: unique,
    warnings: [...new Set(warnings)],
    priority: priorityOf(job || {}, category),
    catalog_yen_ignored: true
  };
}

module.exports = { REASONS, WARNINGS, DENY_FLAG_TO_REASON, qualify, activeContracts, priorityOf };
