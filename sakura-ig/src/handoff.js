#!/usr/bin/env node
'use strict';

/**
 * マネージャー → サクラ専属自動投稿 の間接受け渡し。
 * CURRENT.json を Issue「サクラ起動キー」に書く。
 * ボットはその Issue の最新コメントを起動キーとして読む。
 */

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const ROOT = path.join(__dirname, '..');
const ISSUE_TITLE = 'サクラ起動キー';

function loadKey() {
  return JSON.parse(fs.readFileSync(path.join(ROOT, 'launch-keys', 'CURRENT.json'), 'utf8'));
}

function render(key) {
  return [
    `<!-- sakura-handoff ${key.id} ${key.handed_off_at || ''} -->`,
    `宛先: ${key.to}`,
    `from: ${key.from || 'manager'}`,
    `run: ${key.run}`,
    `post: ${key.post}`,
    '',
    '起動キー。IMAGINE_THROW を Grok Imagine agent にそのまま投げろ。文を足すな。',
    key.post === false ? 'テスト。投稿するな。' : `投稿は ${key.post_time_jst} JST。`,
    '',
    '## メタ',
    `- id: ${key.id}`,
    `- model: ${key.model}`,
    `- duration: ${key.duration_sec}`,
    `- output: ${key.output}`,
    `- reference: ${key.reference_still}`,
    `- post_time_jst: ${key.post_time_jst}`,
    `- manager_handoff_jst: ${key.manager_handoff_jst}`,
    '',
    '## IMAGINE_THROW',
    '```',
    key.imagine_prompt,
    '```',
    '',
    '## CAPTION',
    '```',
    key.caption,
    '```',
    ''
  ].join('\n');
}

function writeLocal(body) {
  const outDir = path.join(ROOT, 'output');
  fs.mkdirSync(outDir, { recursive: true });
  const file = path.join(outDir, 'handoff-latest.md');
  fs.writeFileSync(file, body);
  return file;
}

function gh(args) {
  return execFileSync('gh', args, { encoding: 'utf8' }).trim();
}

function upsertIssue(body) {
  const token = process.env.GITHUB_TOKEN || process.env.GH_TOKEN;
  if (!token) throw new Error('GITHUB_TOKEN が無い。ローカルファイルだけ書いた。');

  let number;
  try {
    const raw = gh(['issue', 'list', '--search', `${ISSUE_TITLE} in:title`, '--state', 'open', '--json', 'number,title', '--limit', '20']);
    const hits = JSON.parse(raw).filter((i) => i.title === ISSUE_TITLE);
    number = hits[0] && hits[0].number;
  } catch (err) {
    throw new Error(`issue list 失敗: ${err.message}`);
  }

  if (!number) {
    const created = gh(['issue', 'create', '--title', ISSUE_TITLE, '--body', body]);
    return { created: true, url: created };
  }

  gh(['issue', 'comment', String(number), '--body', body]);
  return { created: false, number };
}

function main() {
  const key = loadKey();
  const body = render(key);
  const file = writeLocal(body);
  console.log(`local ${file}`);

  if (process.argv.includes('--local')) {
    console.log('local only');
    return;
  }

  try {
    const result = upsertIssue(body);
    console.log(JSON.stringify(result));
  } catch (err) {
    console.error(err.message);
    process.exitCode = 2;
  }
}

main();
