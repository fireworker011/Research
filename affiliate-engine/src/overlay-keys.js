#!/usr/bin/env node
'use strict';

const { loadLinks } = require('./util');

function filledNames(links) {
  return Object.entries(links || {})
    .filter(([k, v]) => !String(k).startsWith('_') && String(v || '').trim())
    .map(([k]) => k)
    .filter((k) => k !== '申込_auひかり')
    .sort();
}

function assertNoUrl(text, names) {
  const line = String(text || '');
  const list = names || [];
  if (/https?:\/\//i.test(line) || list.some((n) => /https?:/i.test(String(n)))) {
    throw new Error('url leak');
  }
}

function resolveLinks(links) {
  return links === undefined ? loadLinks() : links;
}

function overlaySecretState(raw = process.env.AFFILIATE_LINKS_JSON) {
  const s = String(raw || '').trim();
  if (!s) return 'empty';
  try {
    const parsed = JSON.parse(s);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return 'bad';
    return 'set';
  } catch (_) {
    return 'bad';
  }
}

function overlayStatusText(links) {
  const names = filledNames(resolveLinks(links));
  const secret = overlaySecretState();
  const text =
    `overlay-filled: ${names.length}\noverlay-keys: ${names.join(',') || '(none)'}\noverlay-secret: ${secret}\n`;
  assertNoUrl(text, names);
  return { names, secret, text };
}

function overlayLogText(links) {
  const names = filledNames(resolveLinks(links));
  const secret = overlaySecretState();
  const text = `filled ${names.length}\nkeys ${names.join(',') || '(none)'}\nsecret ${secret}\n`;
  assertNoUrl(text, names);
  return { names, secret, text };
}

function selfTest() {
  const prev = process.env.AFFILIATE_LINKS_JSON;
  delete process.env.AFFILIATE_LINKS_JSON;
  const empty = overlayStatusText({ 転職_neo: '', 教育_N高: '' });
  if (empty.names.length !== 0) throw new Error('empty filled');
  if (!empty.text.includes('overlay-filled: 0')) throw new Error('empty line');
  if (!empty.text.includes('overlay-secret: empty')) throw new Error('empty secret');
  if (overlaySecretState('') !== 'empty') throw new Error('state empty');
  if (overlaySecretState('[]') !== 'bad') throw new Error('state bad array');
  if (overlaySecretState('{') !== 'bad') throw new Error('state bad json');
  process.env.AFFILIATE_LINKS_JSON = JSON.stringify({
    転職_neo: 'https://example.invalid/neo',
    申込_auひかり: 'https://example.invalid/au',
    教育_N高: 'https://example.invalid/nko'
  });
  const loaded = loadLinks();
  if (!loaded['転職_neo']) throw new Error('neo secret');
  if (loaded['申込_auひかり']) throw new Error('au stripped');
  const status = overlayStatusText(loaded);
  if (status.names.join(',') !== '教育_N高,転職_neo') throw new Error('names');
  if (/https?:\/\//i.test(status.text)) throw new Error('status url');
  const implicit = overlayStatusText();
  if (implicit.names.join(',') !== '教育_N高,転職_neo') throw new Error('implicit load');
  if (!implicit.text.includes('overlay-filled: 2')) throw new Error('implicit filled');
  const log = overlayLogText(loaded);
  if (!log.text.startsWith('filled 2\n')) throw new Error('log filled');
  if (!log.text.includes('secret set')) throw new Error('log secret');
  if (status.secret !== 'set') throw new Error('status secret set');
  if (/https?:\/\//i.test(log.text)) throw new Error('log url');
  if (prev === undefined) delete process.env.AFFILIATE_LINKS_JSON;
  else process.env.AFFILIATE_LINKS_JSON = prev;
  process.stdout.write('overlay-keys self-test ok\n');
}

function main() {
  if (process.argv.includes('--self-test')) {
    selfTest();
    return;
  }
  process.stdout.write(overlayLogText(loadLinks()).text);
}

module.exports = { filledNames, overlaySecretState, overlayStatusText, overlayLogText };

if (require.main === module) main();
