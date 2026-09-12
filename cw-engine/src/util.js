'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const OUTPUT_DIR = path.join(ROOT, 'output');

function readJSON(filePath, fallback) {
  try {
    if (!fs.existsSync(filePath)) return fallback;
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (_) {
    return fallback;
  }
}

function writeJSON(filePath, data) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`);
  return data;
}

function loadCapability() {
  return readJSON(path.join(ROOT, 'config', 'capability.json'), null);
}

function loadProfile() {
  const live = path.join(ROOT, 'config', 'profile.json');
  const example = path.join(ROOT, 'config', 'profile.example.json');
  return readJSON(live, readJSON(example, { has_completed_delivery: false, completed_deliveries: 0 }));
}

module.exports = {
  ROOT,
  OUTPUT_DIR,
  readJSON,
  writeJSON,
  loadCapability,
  loadProfile
};
