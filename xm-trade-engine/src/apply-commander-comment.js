#!/usr/bin/env node
'use strict';

const fs = require('fs');
const {
  ISSUE_TITLE,
  loadCommander,
  saveCommander,
  parseCommandText,
  parseGoldArmText,
  applyCommand
} = require('./commander');

function readEvent() {
  const p = process.env.GITHUB_EVENT_PATH;
  if (p && fs.existsSync(p)) {
    return JSON.parse(fs.readFileSync(p, 'utf-8'));
  }
  return null;
}

function isNotifyComment(body) {
  return /(?:gold-notice|xm-fill|xm-close|gold-fill|gold-close):/.test(body || '');
}

function applyComment({ body, login, now, current, persist = false }) {
  if (isNotifyComment(body)) {
    return { skipped: true, reason: 'notify-comment' };
  }
  if (login === 'github-actions[bot]') {
    return { skipped: true, reason: 'actions-bot' };
  }
  const kill = parseCommandText(body);
  const gold = parseGoldArmText(body);
  if (!kill && !gold) return { skipped: true, reason: 'no_command' };

  let commander = current || loadCommander();
  if (kill) {
    commander = applyCommand(commander, {
      command: kill,
      source: 'grok-bot-issue',
      reason: 'issue_comment',
      now
    });
  }
  if (gold) {
    commander = {
      ...commander,
      gold_arm: gold,
      gold_arm_date: now.toISOString().slice(0, 10)
    };
  }
  if (persist) saveCommander(commander);
  return {
    skipped: false,
    command: commander.command,
    gold_arm: commander.gold_arm,
    gold_arm_date: commander.gold_arm_date,
    commander
  };
}

function main() {
  const event = readEvent();
  if (event) {
    if (event.issue?.title !== ISSUE_TITLE) {
      console.log(JSON.stringify({ skipped: true, reason: 'not_xm_issue' }));
      return;
    }
    const result = applyComment({
      body: event.comment?.body || '',
      login: event.comment?.user?.login || '',
      now: new Date(event.comment?.updated_at || Date.now()),
      persist: true
    });
    console.log(JSON.stringify({
      skipped: result.skipped,
      reason: result.reason,
      command: result.command,
      gold_arm: result.gold_arm,
      gold_arm_date: result.gold_arm_date
    }));
    return;
  }
  console.log(JSON.stringify({ skipped: true, reason: 'no_event' }));
}

module.exports = { applyComment, isNotifyComment };

if (require.main === module) {
  try {
    main();
  } catch (err) {
    console.error(`apply-commander-comment failed: ${err.message}`);
    process.exit(1);
  }
}
