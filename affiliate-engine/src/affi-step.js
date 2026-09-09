#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const DUMP = 'affiliate-engine/docs/grok-bots/dump';
const START = 'sns_next';
const WORDS = new Set([
  '未提携',
  'Threadsあり',
  'YouTubeあり',
  '項目なし',
  '媒体なし',
  '開設済み',
  '未開設',
  '置済み',
  '完了'
]);

const FILES = {
  sns_next: `${DUMP}/G_hq_sns_next.txt`,
  a8_partner: `${DUMP}/G_hq_a8_partner.txt`,
  yt_only: `${DUMP}/G_hq_yt_only.txt`,
  threads_exist: `${DUMP}/G_hq_threads_exist.txt`,
  a8_site_neo: `${DUMP}/G_hq_a8_site.txt`,
  secret_neo: `${DUMP}/G_hq_secret_neo.txt`,
  profile_neo: `${DUMP}/G_hq_threads_profile.txt`,
  sns_nko: `${DUMP}/G_hq_sns_nko.txt`,
  a8_partner_nko: `${DUMP}/G_hq_a8_partner_nko.txt`,
  yt_only_nko: `${DUMP}/G_hq_yt_only_nko.txt`,
  edu_exist_nko: `${DUMP}/G_hq_edu_exist.txt`,
  a8_site_edu_nko: `${DUMP}/G_hq_a8_site_edu.txt`,
  secret_nko: `${DUMP}/G_hq_secret_nko.txt`,
  profile_edu_nko: `${DUMP}/G_hq_threads_profile_edu.txt`,
  sns_eyes: `${DUMP}/G_hq_sns_eyes.txt`,
  a8_partner_eyes: `${DUMP}/G_hq_a8_partner_eyes.txt`,
  yt_only_eyes: `${DUMP}/G_hq_yt_only_eyes.txt`,
  edu_exist_eyes: `${DUMP}/G_hq_edu_exist.txt`,
  a8_site_edu_eyes: `${DUMP}/G_hq_a8_site_edu.txt`,
  secret_eyes: `${DUMP}/G_hq_secret_eyes.txt`,
  profile_edu_eyes: `${DUMP}/G_hq_threads_profile_eyes.txt`,
  tenshoku_exist: `${DUMP}/G_hq_tenshoku_exist.txt`,
  sns_ticket: `${DUMP}/G_hq_sns_ticket.txt`,
  a8_partner_ticket: `${DUMP}/G_hq_a8_partner_ticket.txt`,
  yt_only_ticket: `${DUMP}/G_hq_yt_only_ticket.txt`,
  a8_site_ticket: `${DUMP}/G_hq_a8_site.txt`,
  secret_ticket: `${DUMP}/G_hq_secret_ticket.txt`,
  profile_ticket: `${DUMP}/G_hq_threads_profile_ticket.txt`,
  a8_csv: `${DUMP}/G_hq_a8_csv.txt`
};

const NEXT = {
  'sns_next|未提携': 'a8_partner',
  'sns_next|Threadsあり': 'threads_exist',
  'sns_next|YouTubeあり': 'yt_only',
  'sns_next|項目なし': 'sns_nko',
  'sns_next|媒体なし': 'sns_nko',
  'a8_partner|完了': 'sns_next',
  'yt_only|完了': 'sns_nko',
  'threads_exist|開設済み': 'a8_site_neo',
  'threads_exist|未開設': 'sns_nko',
  'a8_site_neo|完了': 'profile_neo',
  'profile_neo|完了': 'secret_neo',
  'secret_neo|完了': 'sns_nko',
  'sns_nko|未提携': 'a8_partner_nko',
  'sns_nko|Threadsあり': 'edu_exist_nko',
  'sns_nko|YouTubeあり': 'yt_only_nko',
  'sns_nko|項目なし': 'sns_eyes',
  'sns_nko|媒体なし': 'sns_eyes',
  'a8_partner_nko|完了': 'sns_nko',
  'yt_only_nko|完了': 'sns_eyes',
  'edu_exist_nko|開設済み': 'a8_site_edu_nko',
  'edu_exist_nko|未開設': 'tenshoku_exist',
  'a8_site_edu_nko|完了': 'profile_edu_nko',
  'profile_edu_nko|完了': 'secret_nko',
  'secret_nko|完了': 'tenshoku_exist',
  'sns_eyes|未提携': 'a8_partner_eyes',
  'sns_eyes|Threadsあり': 'edu_exist_eyes',
  'sns_eyes|YouTubeあり': 'yt_only_eyes',
  'sns_eyes|項目なし': 'tenshoku_exist',
  'sns_eyes|媒体なし': 'tenshoku_exist',
  'a8_partner_eyes|完了': 'sns_eyes',
  'yt_only_eyes|完了': 'tenshoku_exist',
  'edu_exist_eyes|開設済み': 'a8_site_edu_eyes',
  'edu_exist_eyes|未開設': 'tenshoku_exist',
  'a8_site_edu_eyes|完了': 'profile_edu_eyes',
  'profile_edu_eyes|完了': 'secret_eyes',
  'secret_eyes|完了': 'tenshoku_exist',
  'tenshoku_exist|開設済み': 'sns_ticket',
  'tenshoku_exist|未開設': 'a8_csv',
  'tenshoku_exist|置済み': 'a8_csv',
  'sns_ticket|未提携': 'a8_partner_ticket',
  'sns_ticket|Threadsあり': 'a8_site_ticket',
  'sns_ticket|YouTubeあり': 'yt_only_ticket',
  'sns_ticket|項目なし': 'a8_csv',
  'sns_ticket|媒体なし': 'a8_csv',
  'a8_partner_ticket|完了': 'sns_ticket',
  'yt_only_ticket|完了': 'a8_csv',
  'a8_site_ticket|完了': 'profile_ticket',
  'profile_ticket|完了': 'secret_ticket',
  'secret_ticket|完了': 'a8_csv'
};

function fileFor(state) {
  return FILES[state] || FILES[START];
}

function repliesFor(state) {
  const cur = FILES[state] ? state : START;
  const prefix = `${cur}|`;
  return Object.keys(NEXT)
    .filter((k) => k.startsWith(prefix))
    .map((k) => k.slice(prefix.length));
}

function parseWord(body) {
  let found = null;
  for (const line of String(body || '').split(/\r?\n/)) {
    const t = line.trim();
    if (WORDS.has(t)) found = t;
  }
  return found;
}

function parseState(body) {
  const m = String(body || '').match(/^\s*hq-affi-state:\s*([a-z0-9_]+)\s*$/im);
  if (!m) return null;
  return FILES[m[1]] ? m[1] : null;
}

function parseNeo(body) {
  const m = String(body || '').match(/^\s*hq-affi-neo:\s*(placed|no)\s*$/im);
  return m ? m[1] : null;
}

function neoAfter(state, word, neo) {
  if (neo === 'placed') return 'placed';
  if (state === 'profile_neo' && word === '完了') return 'placed';
  if (state === 'tenshoku_exist' && word === '置済み') return 'placed';
  return neo === 'placed' ? 'placed' : 'no';
}

function arrive(next, neo) {
  if (neo === 'placed' && (next === 'tenshoku_exist' || next === 'sns_ticket')) return 'a8_csv';
  return next;
}

function step(state, word, neo) {
  const cur = FILES[state] ? state : START;
  const flag = neoAfter(cur, word, neo);
  if (!WORDS.has(word)) return cur;
  const next = NEXT[`${cur}|${word}`];
  if (!next) return cur;
  if (!FILES[next]) return cur;
  if (/remain|n10|cw_/i.test(FILES[next])) return cur;
  return arrive(next, flag);
}

function isBot(comment) {
  return (comment?.user?.login || '') === 'github-actions[bot]';
}

function resolveAffi(comments) {
  const list = comments || [];
  let lastBot = -1;
  let state = START;
  let neo = 'no';
  list.forEach((c, i) => {
    if (!isBot(c)) return;
    const parsed = parseState(c.body);
    if (!parsed) return;
    lastBot = i;
    state = parsed;
    const flag = parseNeo(c.body);
    if (flag) neo = flag;
  });
  let word = null;
  for (let i = lastBot + 1; i < list.length; i++) {
    if (isBot(list[i])) continue;
    const w = parseWord(list[i].body);
    if (w) word = w;
  }
  if (word) {
    neo = neoAfter(state, word, neo);
    state = step(state, word, neo);
  }
  if (neo === 'placed' && (state === 'tenshoku_exist' || state === 'sns_ticket')) {
    state = 'a8_csv';
  }
  return { state, pointer: fileFor(state), word, neo };
}

function selfTest() {
  if (step('sns_next', '未提携') !== 'a8_partner') throw new Error('partner');
  if (step('sns_next', '項目なし') !== 'sns_nko') throw new Error('nko');
  if (step('threads_exist', '未開設') !== 'sns_nko') throw new Error('skip neo');
  if (step('sns_nko', 'Threadsあり') !== 'edu_exist_nko') throw new Error('edu');
  if (step('a8_csv', '完了') !== 'a8_csv') throw new Error('csv stay');
  if (step('a8_site_neo', '完了') !== 'profile_neo') throw new Error('site then profile');
  if (step('profile_neo', '完了') !== 'secret_neo') throw new Error('profile then secret');
  if (step('secret_neo', '完了') !== 'sns_nko') throw new Error('after neo secret');
  if (neoAfter('profile_neo', '完了', 'no') !== 'placed') throw new Error('neo placed');
  if (step('tenshoku_exist', '開設済み', 'no') !== 'sns_ticket') throw new Error('ticket when empty');
  if (step('tenshoku_exist', '開設済み', 'placed') !== 'a8_csv') throw new Error('no overwrite');
  if (step('tenshoku_exist', '置済み', 'no') !== 'a8_csv') throw new Error('placed word');
  if (step('edu_exist_eyes', '未開設', 'placed') !== 'a8_csv') throw new Error('skip ticket node');
  if (!repliesFor('sns_next').includes('未提携')) throw new Error('reply next');
  if (repliesFor('a8_csv').length !== 0) throw new Error('reply csv');
  if (!repliesFor('a8_partner').includes('完了')) throw new Error('reply partner');
  if (!repliesFor('tenshoku_exist').includes('置済み')) throw new Error('reply placed');
  for (const node of Object.keys(FILES)) {
    if (node === 'a8_csv') continue;
    if (!repliesFor(node).length) throw new Error(`no reply ${node}`);
  }
  if (step('sns_next', 'nonsense') !== 'sns_next') throw new Error('stay');
  if (parseWord('未提携') !== '未提携') throw new Error('word');
  if (parseWord('ね、未提携かも') !== null) throw new Error('loose');
  const r = resolveAffi([
    { user: { login: 'github-actions[bot]' }, body: 'hq-instruct: x\nhq-affi-state: sns_next\n' },
    { user: { login: 'n' }, body: '項目なし' }
  ]);
  if (r.state !== 'sns_nko') throw new Error('resolve');
  const placed = resolveAffi([
    { user: { login: 'github-actions[bot]' }, body: 'hq-affi-state: tenshoku_exist\nhq-affi-neo: placed\n' },
    { user: { login: 'n' }, body: '開設済み' }
  ]);
  if (placed.state !== 'a8_csv') throw new Error('resolve no overwrite');
  if (placed.neo !== 'placed') throw new Error('resolve neo');
  const root = path.join(__dirname, '../..');
  for (const rel of Object.values(FILES)) {
    if (/remain|n10|G_hq_cw_/i.test(rel)) throw new Error(`parked ${rel}`);
    if (!fs.existsSync(path.join(root, rel))) throw new Error(`missing ${rel}`);
    const dump = fs.readFileSync(path.join(root, rel), 'utf8');
    if (dump.includes('G_hq_banner_10.txt')) throw new Error(`banner ${rel}`);
  }
  process.stdout.write('affi-step self-test ok\n');
}

module.exports = {
  START,
  WORDS,
  FILES,
  fileFor,
  repliesFor,
  parseWord,
  parseState,
  parseNeo,
  neoAfter,
  step,
  resolveAffi
};

if (require.main === module) {
  if (process.argv.includes('--self-test')) selfTest();
}
