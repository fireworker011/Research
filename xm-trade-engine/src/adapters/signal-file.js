'use strict';

const path = require('path');
const { writeJSON, OUTPUT_DIR } = require('../util');

const SIGNAL_PATH = path.join(OUTPUT_DIR, 'state', 'signals.json');

function emptySignals(now) {
  return {
    kind: 'shadow_signals',
    disclaimer: 'GitHub cron は1〜4時間遅延する。XMの実時間発注には使わず、EAのローカル戦略を正とする。',
    updated_at: now.toISOString(),
    intents: []
  };
}

function writeSignals(intents, now) {
  const payload = {
    kind: 'shadow_signals',
    disclaimer: 'GitHub cron は1〜4時間遅延する。XMの実時間発注には使わず、EAのローカル戦略を正とする。',
    updated_at: now.toISOString(),
    intents
  };
  writeJSON(SIGNAL_PATH, payload);
  return payload;
}

module.exports = { SIGNAL_PATH, emptySignals, writeSignals };
