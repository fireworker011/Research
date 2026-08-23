#!/usr/bin/env node
'use strict';

const { loadSprint, findPacket, composeStillPrompt, composeVideoPrompt, parseArgs } = require('./lib');

const args = parseArgs(process.argv);
const packet = findPacket(loadSprint(), args);
if (!packet) {
  console.error('packet not found');
  process.exit(1);
}

console.log(`# ${packet.id}  ${packet.date}  ${packet.type}  ${packet.wardrobe}`);
console.log(`# models: ${packet.image_model} → ${packet.video_model}`);
console.log(`# ${packet.aspect_ratio}  ${packet.duration_sec}s  ${packet.resolution}`);
console.log('');
console.log('===== STILL (image mode, 9:16, 2k) =====');
console.log(composeStillPrompt(packet));
console.log('');
console.log(`===== VIDEO (image-to-video, ${packet.duration_sec}s, 9:16, 720p) =====`);
console.log(composeVideoPrompt(packet));
console.log('');
console.log('===== CAPTION (paste into Instagram, do not edit) =====');
console.log(packet.caption);
console.log('');
console.log(`===== SAVE AS =====`);
console.log(`output/${packet.id}/still.jpg`);
console.log(`output/${packet.id}/reel.mp4`);
console.log(`output/${packet.id}/caption.txt`);
