#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');

function loadSprint() {
  return JSON.parse(fs.readFileSync(path.join(ROOT, 'packets', 'sprint-01.json'), 'utf8'));
}

function loadLock() {
  return fs.readFileSync(path.join(ROOT, 'data', 'character-lock.txt'), 'utf8').trim();
}

function loadNegatives() {
  return fs.readFileSync(path.join(ROOT, 'data', 'negatives.txt'), 'utf8').trim();
}

function todayJst() {
  return new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Tokyo' });
}

function findPacket(sprint, { date, id, next }) {
  if (id) return sprint.packets.find((p) => p.id === id) || null;
  if (date) return sprint.packets.find((p) => p.date === date) || null;
  if (next) {
    const t = date || todayJst();
    return sprint.packets.find((p) => p.date >= t) || sprint.packets[sprint.packets.length - 1];
  }
  return null;
}

function composeStillPrompt(packet) {
  return [loadLock(), packet.still.prompt, loadNegatives()].join('\n\n');
}

function composeVideoPrompt(packet) {
  return [
    'Animate this exact woman. Do not change her face.',
    packet.video.prompt,
    'Vertical 9:16. Photorealistic. No garbled text. No second person.',
    loadNegatives()
  ].join('\n\n');
}

function parseArgs(argv) {
  const out = { next: false };
  for (let i = 2; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === '--next') out.next = true;
    else if (a === '--date') out.date = argv[++i];
    else if (a === '--id') out.id = argv[++i];
  }
  if (!out.date && !out.id) out.next = true;
  return out;
}

module.exports = {
  ROOT,
  loadSprint,
  loadLock,
  loadNegatives,
  todayJst,
  findPacket,
  composeStillPrompt,
  composeVideoPrompt,
  parseArgs
};
