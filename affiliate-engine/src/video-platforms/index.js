'use strict';

const youtube = require('./youtube');
const tiktok = require('./tiktok');
const instagram = require('./instagram');

/**
 * platform 名 → アダプタ。各アダプタは同じ形:
 *   LIMITS: { titleMax, captionMax, hashtagMax }
 *   credentials(account) → { values, missing }
 *   publish(account, creds, item, caption, log) → { id, url, ... }
 *   refreshTokens?(account, creds) → { updates: [{env, value}], note }
 */
const ADAPTERS = { youtube, tiktok, instagram };

function getAdapter(platform) {
  return ADAPTERS[String(platform || '').toLowerCase()] || null;
}

module.exports = { ADAPTERS, getAdapter };
