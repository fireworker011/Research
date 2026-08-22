#!/usr/bin/env node
'use strict';

/**
 * 14日実験用。癒し型ペット投稿を3本だけ抜き、プロフィールCTAを付けて出す。
 * URLは出さない。投稿は人間がYouTubeアプリで行う。
 */

const path = require('path');
const { readJSON } = require('./util');
const { isHealingPet, applyProfileCta, youtubeDescription, PROFILE_CTA } = require('./youtube-cta');

const seed = readJSON(path.join(__dirname, '..', 'data', 'seed_templates.json'));
const templates = (seed && seed.posting_templates) || [];

const picked = templates
  .filter((t) => isHealingPet(t))
  .sort((a, b) => String(a.content || '').length - String(b.content || '').length)
  .slice(0, 3);

if (picked.length < 3) {
  console.error(`癒し型が${picked.length}本しか無い`);
  process.exit(1);
}

console.log('# 次の癒しShorts 3本（プロフィールCTA）\n');
console.log('映像の型は変えない。最後に1回だけ言う／出す:');
console.log(`\`${PROFILE_CTA}\`\n`);
console.log('固定コメントにURLは置かない。既存32本は触らない。\n');

picked.forEach((t, i) => {
  const spoken = applyProfileCta(t.content);
  const desc = youtubeDescription(t.content);
  console.log(`## ${i + 1}. ${t.id}`);
  console.log('');
  console.log('テロップ／読み上げ:');
  console.log('```');
  console.log(spoken);
  console.log('```');
  console.log('');
  console.log('YouTube説明文（URLなし）:');
  console.log('```');
  console.log(desc);
  console.log('```');
  console.log('');
});
