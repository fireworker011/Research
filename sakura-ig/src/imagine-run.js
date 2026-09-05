#!/usr/bin/env node
'use strict';

/**
 * 使わない。本番は Grok bot → Grok Imagine（APIキー不要）。
 * このファイルは xAI HTTP API 用の残骸。投稿しない。
 */

const fs = require('fs');
const path = require('path');
const {
  ROOT,
  loadSprint,
  findPacket,
  composeStillPrompt,
  composeVideoPrompt,
  parseArgs,
  resolveReferenceStill
} = require('./lib');

function fileToDataUri(filePath) {
  const buf = fs.readFileSync(filePath);
  const ext = path.extname(filePath).toLowerCase();
  const mime = ext === '.png' ? 'image/png' : 'image/jpeg';
  return `data:${mime};base64,${buf.toString('base64')}`;
}

const API = 'https://api.x.ai/v1';

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function api(pathname, { method = 'GET', body, raw = false } = {}) {
  const res = await fetch(`${API}${pathname}`, {
    method,
    headers: {
      Authorization: `Bearer ${process.env.XAI_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: body ? JSON.stringify(body) : undefined
  });
  if (raw) return res;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(`${method} ${pathname} ${res.status}: ${JSON.stringify(data)}`);
  }
  return data;
}

async function download(url, dest) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`download ${url} ${res.status}`);
  fs.writeFileSync(dest, Buffer.from(await res.arrayBuffer()));
}

async function generateStill(packet) {
  const data = await api('/images/generations', {
    method: 'POST',
    body: {
      model: packet.image_model,
      prompt: composeStillPrompt(packet),
      aspect_ratio: '9:16',
      resolution: '2k',
      n: 1
    }
  });
  const url = data.data && data.data[0] && (data.data[0].url || data.data[0].image_url);
  if (!url) throw new Error(`no still url: ${JSON.stringify(data)}`);
  return url;
}

async function generateVideo(packet, stillUrl) {
  const started = await api('/videos/generations', {
    method: 'POST',
    body: {
      model: packet.video_model,
      prompt: composeVideoPrompt(packet),
      image: { url: stillUrl },
      duration: packet.duration_sec,
      aspect_ratio: '9:16',
      resolution: packet.resolution
    }
  });
  const requestId = started.request_id;
  if (!requestId) throw new Error(`no request_id: ${JSON.stringify(started)}`);

  for (let i = 0; i < 60; i += 1) {
    await sleep(5000);
    const poll = await api(`/videos/${requestId}`);
    if (poll.status === 'done' && poll.video && poll.video.url) return poll.video.url;
    if (poll.status === 'failed' || poll.status === 'expired') {
      throw new Error(`video ${poll.status}: ${JSON.stringify(poll)}`);
    }
  }
  throw new Error('video poll timeout');
}

async function main() {
  const packet = findPacket(loadSprint(), parseArgs(process.argv));
  if (!packet) {
    console.error('packet not found');
    process.exit(1);
  }

  if (packet.use_reference_still) {
    try {
      resolveReferenceStill(packet);
    } catch (err) {
      console.error(err.message);
      process.exit(1);
    }
  }

  if (!process.env.XAI_API_KEY) {
    console.error('XAI_API_KEY が無い。下を Imagine UI に貼るか、キーを入れて再実行。投稿はするな。');
    require('child_process').execFileSync(process.execPath, [
      path.join(__dirname, 'print-packet.js'),
      '--id',
      packet.id
    ], { stdio: 'inherit' });
    process.exit(2);
  }

  const dir = path.join(ROOT, 'output', packet.id);
  fs.mkdirSync(dir, { recursive: true });

  const stillPath = path.join(dir, 'still.jpg');
  let stillUrl;
  if (packet.use_reference_still) {
    const ref = resolveReferenceStill(packet);
    fs.copyFileSync(ref, stillPath);
    stillUrl = fileToDataUri(ref);
    console.log(`still ${packet.id}: reference ${path.relative(ROOT, ref)}`);
  } else {
    console.log(`still ${packet.id}...`);
    stillUrl = await generateStill(packet);
    await download(stillUrl, stillPath);
  }

  console.log(`video ${packet.id} (${packet.duration_sec}s)...`);
  const videoUrl = await generateVideo(packet, stillUrl);
  const reelPath = path.join(dir, 'reel.mp4');
  await download(videoUrl, reelPath);

  fs.writeFileSync(path.join(dir, 'caption.txt'), `${packet.caption}\n`);
  const manifest = {
    id: packet.id,
    date: packet.date,
    type: packet.type,
    wardrobe: packet.wardrobe,
    cta: packet.cta,
    still: stillPath,
    reel: reelPath,
    posted: false,
    created_at: new Date().toISOString()
  };
  fs.writeFileSync(path.join(dir, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
  console.log(`OK ${dir}`);
  console.log('投稿しない。人間が reel.mp4 と caption.txt を使う。');
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
