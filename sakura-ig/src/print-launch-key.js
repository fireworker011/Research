#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const key = JSON.parse(
  fs.readFileSync(path.join(__dirname, '..', 'launch-keys', 'CURRENT.json'), 'utf8')
);

console.log(`# 起動キー ${key.id}  →  ${key.to}`);
console.log(`# throw_to: ${key.throw_to}`);
console.log(`# ${key.mode}  ${key.duration_sec}s  ${key.aspect_ratio}  ${key.resolution}`);
console.log(`# reference: ${key.reference_still}`);
console.log(`# post: ${key.post_time_jst} JST`);
console.log('');
console.log('===== IMAGINE_THROW =====');
console.log(key.imagine_prompt);
console.log('');
console.log('===== CAPTION =====');
console.log(key.caption);
console.log('');
console.log(`===== OUTPUT =====`);
console.log(key.output);
