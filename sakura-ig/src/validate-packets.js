#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const sprint = JSON.parse(fs.readFileSync(path.join(ROOT, 'packets', 'sprint-01.json'), 'utf8'));
const lock = fs.readFileSync(path.join(ROOT, 'data', 'character-lock.txt'), 'utf8').trim();
const negatives = fs.readFileSync(path.join(ROOT, 'data', 'negatives.txt'), 'utf8').trim();

const TYPES = new Set(['question', 'which-one', 'micro-motion', 'researcher', 'push-pull', 'season', 'loop']);
const REQUIRED = [
  'id', 'date', 'weekday', 'type', 'signature_kimono', 'wardrobe',
  'duration_sec', 'aspect_ratio', 'resolution', 'image_model', 'video_model',
  'still', 'video', 'overlay', 'cta', 'caption'
];

const errors = [];
const ids = new Set();
const dates = new Set();
let signatureCount = 0;

if (!lock) errors.push('character-lock.txt is empty');
if (!negatives) errors.push('negatives.txt is empty');
if (!Array.isArray(sprint.packets) || sprint.packets.length !== 14) {
  errors.push(`expected 14 packets, got ${sprint.packets ? sprint.packets.length : 0}`);
}

for (const p of sprint.packets || []) {
  for (const key of REQUIRED) {
    if (p[key] === undefined || p[key] === null) errors.push(`${p.id || '?'}: missing ${key}`);
  }
  if (ids.has(p.id)) errors.push(`duplicate id ${p.id}`);
  ids.add(p.id);
  if (dates.has(p.date)) errors.push(`duplicate date ${p.date}`);
  dates.add(p.date);
  if (!TYPES.has(p.type)) errors.push(`${p.id}: bad type ${p.type}`);
  if (p.aspect_ratio !== '9:16') errors.push(`${p.id}: aspect_ratio must be 9:16`);
  if (p.resolution !== '720p') errors.push(`${p.id}: resolution must be 720p`);
  if (p.image_model !== 'grok-imagine-image-2.0') errors.push(`${p.id}: unexpected image model`);
  if (p.video_model !== 'grok-imagine-video-1.5') errors.push(`${p.id}: unexpected video model`);
  if (p.duration_sec < 5 || p.duration_sec > 8) errors.push(`${p.id}: duration ${p.duration_sec} out of 5-8`);
  if (!p.still || !p.still.prompt || p.still.prompt.length < 40) errors.push(`${p.id}: still.prompt too short`);
  if (!p.video || !p.video.prompt || p.video.prompt.length < 40) errors.push(`${p.id}: video.prompt too short`);
  if (!p.caption || !p.caption.includes('AI')) errors.push(`${p.id}: caption must disclose AI`);
  if (p.overlay && p.overlay.burn && /[ぁ-んァ-ン一-龯]/.test(p.overlay.text || '')) {
    errors.push(`${p.id}: overlay must not burn Japanese`);
  }
  if (p.signature_kimono) signatureCount += 1;
}

if (signatureCount > 7) errors.push(`too many signature red kimonos: ${signatureCount}`);
if (sprint.packets && sprint.packets.filter((p) => p.cta).length !== 2) {
  errors.push('cta must appear on exactly 2 packets (Thursdays)');
}

if (errors.length) {
  console.error('validate-packets: FAIL');
  for (const e of errors) console.error(' -', e);
  process.exit(1);
}

console.log(`validate-packets: OK (${sprint.packets.length} packets, red-signature ${signatureCount})`);
