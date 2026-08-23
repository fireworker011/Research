#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const ROOT = path.join(__dirname, '..');
const ISSUE_TITLE = 'サクラ起動キー';

function loadKey() {
  return JSON.parse(fs.readFileSync(path.join(ROOT, 'launch-keys', 'CURRENT.json'), 'utf8'));
}

function main() {
  const key = loadKey();
  const todayJst = new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Tokyo' });
  const tooEarly = key.post_date && key.post_date > todayJst;
  const body = key.post === false
    ? [
      `<!-- sakura-post-gate ${key.id} -->`,
      '06:00 ゲート（テスト）',
      '投稿するな。動画ができていれば確認だけ。',
      `- output: ${key.output}`,
      ''
    ].join('\n')
    : tooEarly
      ? [
        `<!-- sakura-post-gate ${key.id} -->`,
        '06:00 ゲート（まだ早い）',
        `投稿日は ${key.post_date}。今日は作成待ち。投稿するな。`,
        `- output: ${key.output}`,
        ''
      ].join('\n')
    : [
      `<!-- sakura-post-gate ${key.id} -->`,
      '06:00 投稿ゲート',
      '宛先: サクラ専属自動投稿',
      `${key.output} を sakura_ai_beauty のリールとして投稿せよ。キャプションは下のまま。`,
      '',
      '```',
      key.caption,
      '```',
      ''
    ].join('\n');

  const out = path.join(ROOT, 'output', 'post-gate-latest.md');
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, body);
  console.log(`local ${out}`);

  if (process.argv.includes('--local') || !(process.env.GITHUB_TOKEN || process.env.GH_TOKEN)) {
    console.log('local only');
    return;
  }

  const raw = execFileSync('gh', ['issue', 'list', '--search', `${ISSUE_TITLE} in:title`, '--state', 'open', '--json', 'number,title', '--limit', '20'], { encoding: 'utf8' });
  const hits = JSON.parse(raw).filter((i) => i.title === ISSUE_TITLE);
  if (!hits[0]) {
    console.error('Issue サクラ起動キー が無い。先に handoff を回せ。');
    process.exit(2);
  }
  execFileSync('gh', ['issue', 'comment', String(hits[0].number), '--body', body], { encoding: 'utf8' });
  console.log(`commented #${hits[0].number}`);
}

main();
