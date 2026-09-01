'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const OUTPUT_DIR = path.join(ROOT, 'output');

function readJSON(filePath, fallback = null) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  } catch (_) {
    return fallback;
  }
}

function writeJSON(filePath, data) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`, 'utf-8');
}

function loadConfig(name, fallback = null) {
  const real = path.join(ROOT, 'config', `${name}.json`);
  const example = path.join(ROOT, 'config', `${name}.example.json`);
  return readJSON(real) ?? readJSON(example) ?? fallback;
}

function todayUTC(date = new Date()) {
  return date.toISOString().slice(0, 10);
}

function todayJST(date = new Date()) {
  const shifted = new Date(date.getTime() + 9 * 3600 * 1000);
  return shifted.toISOString().slice(0, 10);
}

function utcHour(date) {
  return date.getUTCHours();
}

function utcDay(date) {
  return date.getUTCDay();
}

function clamp(n, min, max) {
  return Math.min(max, Math.max(min, n));
}

function roundTo(n, digits) {
  const f = 10 ** digits;
  return Math.round(n * f) / f;
}

function pipSize(symbol) {
  const base = String(symbol || '').replace(/[^A-Z]/gi, '').toUpperCase();
  if (base.includes('XAU') || base.includes('GOLD')) return 0.01;
  return base.endsWith('JPY') ? 0.01 : 0.0001;
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

module.exports = {
  ROOT,
  OUTPUT_DIR,
  readJSON,
  writeJSON,
  loadConfig,
  todayUTC,
  todayJST,
  utcHour,
  utcDay,
  clamp,
  roundTo,
  pipSize,
  assert
};
