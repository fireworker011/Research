#!/usr/bin/env node
// STEP3: ナレーション生成。
//   1) Google TTS Chirp3-HD (ja-JP-Chirp3-HD-Orus)   … GOOGLE_TTS_API_KEY / GOOGLE_APPLICATION_CREDENTIALS
//   2) Qwen3-TTS (DashScope)                          … DASHSCOPE_API_KEY
//   3) モック（無音・尺だけ本番相当）                  … キーなしでも全STEPを通せる
// どれで生成しても public/audio/voice-manifest.json の形は同じなので、
// 後からキーを入れて再実行するだけで本番音声に差し替わる。
import fs from 'node:fs';
import path from 'node:path';
import { AUDIO_DIR, ROOT, ensureDir, loadScript, readJson, sceneId, writeJson } from './lib/paths.mjs';
import { writeWav, audioDurationSeconds } from './lib/wav.mjs';
import { accessTokenFromServiceAccount } from './lib/gauth.mjs';

const VOICE_NAME = process.env.TTS_VOICE || 'ja-JP-Chirp3-HD-Orus';
const LANGUAGE_CODE = 'ja-JP';
const SAMPLE_RATE = 24000;
const SPEAKING_RATE = Number(process.env.TTS_SPEAKING_RATE || 1.12);
const TARGET_MAX_SECONDS = 5.0; // STEP3: 1文あたり約5秒以内

const script = loadScript();
const pron = readJson(path.join(ROOT, 'pronunciation.json'));

ensureDir(AUDIO_DIR);

const engine = await pickEngine();
console.log(`=== STEP3 ナレーション生成 ===`);
console.log(`エンジン : ${engine.label}`);
console.log(`ボイス   : ${engine.kind === 'mock' ? '(モック無音)' : VOICE_NAME}`);
console.log('');

const entries = [];
for (const [i, scene] of script.sentences.entries()) {
  const id = sceneId(i);
  const text = applyReadings(scene.narration);
  const file = path.join(AUDIO_DIR, `voice-${id}.wav`);

  const seconds = await engine.synth(text, file);
  const overLimit = seconds > TARGET_MAX_SECONDS;

  entries.push({
    index: i,
    role: scene.role,
    src: `audio/${path.basename(file)}`,
    seconds: Number(seconds.toFixed(3)),
    text,
    original: scene.narration,
    overLimit,
  });

  console.log(
    `  ${id}  ${seconds.toFixed(2)}s ${overLimit ? '[warn 5秒超]' : '        '} ${text.slice(0, 28)}`
  );
}

const manifest = {
  engine: engine.kind,
  voice: engine.kind === 'mock' ? null : VOICE_NAME,
  sampleRate: SAMPLE_RATE,
  mock: engine.kind === 'mock',
  generatedAt: new Date().toISOString(),
  totalSeconds: Number(entries.reduce((a, e) => a + e.seconds, 0).toFixed(3)),
  entries,
};
writeJson(path.join(AUDIO_DIR, 'voice-manifest.json'), manifest);

console.log('');
console.log(`合計 ${manifest.totalSeconds.toFixed(1)} 秒 / ${entries.length} 本`);
const over = entries.filter((e) => e.overLimit);
if (over.length) {
  console.log(`[warn] 5秒を超えたシーン: ${over.map((e) => sceneId(e.index)).join(', ')}（読点で分割を検討）`);
}
if (engine.kind === 'mock') {
  console.log('');
  console.log('モック音声です（無音・尺のみ本番相当）。キーを設定して再実行すると本番音声に置き換わります:');
  console.log('  export GOOGLE_TTS_API_KEY=xxx   # または GOOGLE_APPLICATION_CREDENTIALS=/path/sa.json');
}

// ---------------------------------------------------------------- エンジン選択

async function pickEngine() {
  if (process.env.FORCE_MOCK_TTS === '1') return mockEngine();

  if (process.env.GOOGLE_TTS_API_KEY) {
    return googleEngine({ apiKey: process.env.GOOGLE_TTS_API_KEY, label: 'Google TTS (API キー)' });
  }
  if (process.env.GOOGLE_APPLICATION_CREDENTIALS) {
    const token = await accessTokenFromServiceAccount(
      process.env.GOOGLE_APPLICATION_CREDENTIALS,
      'https://www.googleapis.com/auth/cloud-platform'
    );
    return googleEngine({ token, label: 'Google TTS (サービスアカウント)' });
  }
  if (process.env.DASHSCOPE_API_KEY) return qwenEngine();

  return mockEngine();
}

function googleEngine({ apiKey, token, label }) {
  const url =
    'https://texttospeech.googleapis.com/v1/text:synthesize' + (apiKey ? `?key=${apiKey}` : '');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;

  return {
    kind: 'google-chirp3hd',
    label,
    async synth(text, file) {
      const res = await fetch(url, {
        method: 'POST',
        headers,
        // Chirp3-HD は SSML 非対応。プレーンテキストで渡す。
        body: JSON.stringify({
          input: { text },
          voice: { languageCode: LANGUAGE_CODE, name: VOICE_NAME },
          audioConfig: {
            audioEncoding: 'LINEAR16',
            sampleRateHertz: SAMPLE_RATE,
            speakingRate: SPEAKING_RATE,
          },
        }),
      });
      if (!res.ok) throw new Error(`Google TTS 失敗 (${res.status}): ${await res.text()}`);
      const { audioContent } = await res.json();
      fs.writeFileSync(file, Buffer.from(audioContent, 'base64'));
      return audioDurationSeconds(file);
    },
  };
}

function qwenEngine() {
  const endpoint =
    process.env.DASHSCOPE_ENDPOINT ||
    'https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation';

  return {
    kind: 'qwen3-tts',
    label: 'Qwen3-TTS (DashScope)',
    async synth(text, file) {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${process.env.DASHSCOPE_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: process.env.QWEN_TTS_MODEL || 'qwen3-tts-flash',
          input: { text, voice: process.env.QWEN_TTS_VOICE || 'Cherry', language_type: 'Japanese' },
        }),
      });
      if (!res.ok) throw new Error(`Qwen3-TTS 失敗 (${res.status}): ${await res.text()}`);
      const json = await res.json();
      const audioUrl = json?.output?.audio?.url;
      if (!audioUrl) throw new Error(`Qwen3-TTS: 音声URLが返りません: ${JSON.stringify(json)}`);

      const wav = file.replace(/\.wav$/, path.extname(new URL(audioUrl).pathname) || '.wav');
      const bin = Buffer.from(await (await fetch(audioUrl)).arrayBuffer());
      fs.writeFileSync(wav, bin);
      return audioDurationSeconds(wav);
    },
  };
}

function mockEngine() {
  return {
    kind: 'mock',
    label: 'モック（無音・尺だけ本番相当）',
    async synth(text, file) {
      const seconds = estimateSeconds(text);
      const samples = new Float32Array(Math.round(seconds * SAMPLE_RATE)); // 全ゼロ = 無音
      writeWav(file, samples, SAMPLE_RATE);
      return seconds;
    },
  };
}

// ---------------------------------------------------------------- 補助

function applyReadings(text) {
  return pron.replacements.reduce((acc, r) => acc.split(r.from).join(r.to), text);
}

// モーラ数から日本語ナレーションの尺を見積もる（本番TTSと±10%程度で一致する）
function estimateSeconds(text) {
  const MORA_PER_SEC = 7.5 * SPEAKING_RATE;
  let mora = 0;
  let pause = 0.35; // 文末の間

  for (const ch of text) {
    if ('ゃゅょャュョぁぃぅぇぉァィゥェォ'.includes(ch)) continue; // 拗音は独立モーラでない
    if ('、，'.includes(ch)) { pause += 0.22; continue; }
    if ('。．！？!?'.includes(ch)) { pause += 0.32; continue; }
    if ('「」『』（）()・…'.includes(ch)) continue;
    if (/[ぁ-んァ-ヴーっッ]/.test(ch)) { mora += 1; continue; }
    if (/[一-龠々]/.test(ch)) { mora += 1.8; continue; } // 漢字は音読み2モーラ弱
    if (/[0-9０-９]/.test(ch)) { mora += 2; continue; }
    if (/[A-Za-z]/.test(ch)) { mora += 1.6; continue; }
    mora += 1;
  }
  return Math.max(0.8, mora / MORA_PER_SEC + pause);
}
