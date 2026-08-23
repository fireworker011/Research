#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const PROMPTS = path.join(ROOT, 'prompts');

function readPrompt(rel) {
  return fs.readFileSync(path.join(PROMPTS, rel), 'utf8').trim();
}

function loadSprint() {
  return JSON.parse(fs.readFileSync(path.join(ROOT, 'packets', 'sprint-01.json'), 'utf8'));
}

function loadLock() {
  return readPrompt('lock.txt');
}

function loadNegatives() {
  return readPrompt('negatives.txt');
}

function loadAnimate() {
  return readPrompt('animate.txt');
}

function wardrobeIds(packet) {
  return String(packet.wardrobe || '')
    .split('+')
    .map((s) => s.trim())
    .filter(Boolean);
}

function loadWardrobe(packet) {
  return wardrobeIds(packet)
    .map((id) => readPrompt(path.join('wardrobe', `${id}.txt`)))
    .join('\n\n');
}

function loadTypeBlock(type, section) {
  const raw = readPrompt(path.join('types', `${type}.txt`));
  const key = `${section}:`;
  const lines = raw.split(/\r?\n/);
  const hit = lines.find((line) => line.startsWith(key));
  if (!hit) throw new Error(`type ${type} missing ${section}`);
  return hit.slice(key.length).trim();
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
  return [
    loadLock(),
    loadWardrobe(packet),
    loadTypeBlock(packet.type, 'STILL'),
    packet.still.prompt,
    loadNegatives()
  ].join('\n\n');
}

function composeVideoPrompt(packet) {
  return [
    loadAnimate(),
    loadWardrobe(packet),
    loadTypeBlock(packet.type, 'VIDEO'),
    packet.video.prompt,
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
  PROMPTS,
  loadSprint,
  loadLock,
  loadNegatives,
  loadAnimate,
  wardrobeIds,
  loadWardrobe,
  loadTypeBlock,
  todayJst,
  findPacket,
  composeStillPrompt,
  composeVideoPrompt,
  parseArgs
};
