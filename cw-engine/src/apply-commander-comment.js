'use strict';

const fs = require('fs');
const { parseCommandText, parseQueueEvent, isDeskComment, applyCommand, loadCommander, saveCommander, ISSUE_TITLE } = require('./commander');
const { loadQueue, saveQueue, applyEvent } = require('./queue');

function applyComment({ body, login, now, persist = false, current, queue }) {
  if (isDeskComment(body)) return { skipped: true, reason: 'notify-comment' };
  if (login === 'github-actions[bot]') return { skipped: true, reason: 'actions-bot' };

  const kill = parseCommandText(body);
  const event = parseQueueEvent(body);
  if (!kill && !event) return { skipped: true, reason: 'no_command' };

  let commander = current || loadCommander();
  let nextQueue = queue || loadQueue();

  if (kill) {
    commander = applyCommand(commander, {
      command: kill,
      source: 'grok-bot-issue',
      reason: 'issue_comment',
      now
    });
  }
  let queueResult = { skipped: true, reason: 'no_event' };
  if (event) {
    queueResult = applyEvent(nextQueue, event, now);
    if (!queueResult.skipped) nextQueue = queueResult.queue;
  }

  if (persist) {
    saveCommander(commander);
    if (!queueResult.skipped) saveQueue(nextQueue);
  }

  return {
    skipped: false,
    command: commander.command,
    event: event || null,
    queue_skipped: queueResult.skipped,
    queue_reason: queueResult.reason || null,
    commander,
    queue: nextQueue
  };
}

function readEvent() {
  const p = process.env.GITHUB_EVENT_PATH;
  if (p && fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, 'utf8'));
  return null;
}

function main() {
  const event = readEvent();
  if (!event) {
    console.log(JSON.stringify({ skipped: true, reason: 'no_event' }));
    return;
  }
  if (event.issue?.title !== ISSUE_TITLE) {
    console.log(JSON.stringify({ skipped: true, reason: 'not_cw_issue' }));
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
    event: result.event,
    queue_skipped: result.queue_skipped
  }));
}

module.exports = { applyComment };

if (require.main === module) {
  try {
    main();
  } catch (err) {
    console.error(`apply-commander-comment failed: ${err.message}`);
    process.exit(1);
  }
}
