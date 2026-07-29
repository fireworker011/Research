// 最小限の WAV (PCM 16bit) の読み書き。ffmpeg/ffprobe に依存しないための自前実装。
import fs from 'node:fs';

export function writeWav(filePath, samples, sampleRate = 24000, channels = 1) {
  const bytesPerSample = 2;
  const dataSize = samples.length * bytesPerSample;
  const buf = Buffer.alloc(44 + dataSize);

  buf.write('RIFF', 0);
  buf.writeUInt32LE(36 + dataSize, 4);
  buf.write('WAVE', 8);
  buf.write('fmt ', 12);
  buf.writeUInt32LE(16, 16); // fmt チャンクサイズ
  buf.writeUInt16LE(1, 20); // PCM
  buf.writeUInt16LE(channels, 22);
  buf.writeUInt32LE(sampleRate, 24);
  buf.writeUInt32LE(sampleRate * channels * bytesPerSample, 28);
  buf.writeUInt16LE(channels * bytesPerSample, 32);
  buf.writeUInt16LE(16, 34);
  buf.write('data', 36);
  buf.writeUInt32LE(dataSize, 40);

  for (let i = 0; i < samples.length; i++) {
    const clamped = Math.max(-1, Math.min(1, samples[i]));
    buf.writeInt16LE(Math.round(clamped * 32767), 44 + i * bytesPerSample);
  }

  fs.writeFileSync(filePath, buf);
  return { path: filePath, seconds: samples.length / channels / sampleRate };
}

// WAV / MP3 のヘッダを読んで再生秒数を返す。タイムライン生成に使う。
export function audioDurationSeconds(filePath) {
  const buf = fs.readFileSync(filePath);
  if (buf.length > 12 && buf.toString('ascii', 0, 4) === 'RIFF') return wavDuration(buf);
  return mp3Duration(buf);
}

function wavDuration(buf) {
  let offset = 12;
  let sampleRate = 0;
  let channels = 1;
  let bitsPerSample = 16;

  while (offset + 8 <= buf.length) {
    const id = buf.toString('ascii', offset, offset + 4);
    const size = buf.readUInt32LE(offset + 4);
    if (id === 'fmt ') {
      channels = buf.readUInt16LE(offset + 10);
      sampleRate = buf.readUInt32LE(offset + 12);
      bitsPerSample = buf.readUInt16LE(offset + 22);
    } else if (id === 'data') {
      return size / (sampleRate * channels * (bitsPerSample / 8));
    }
    offset += 8 + size + (size % 2); // チャンクは偶数バイト境界
  }
  throw new Error('WAV: data チャンクが見つかりません');
}

// フレームヘッダを走査して積算する（CBR/VBR どちらでも実測できる）
function mp3Duration(buf) {
  const V1_L3 = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320];
  const V2_L3 = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160];
  const RATES = { 3: [44100, 48000, 32000], 2: [22050, 24000, 16000], 0: [11025, 12000, 8000] };

  let i = 0;
  if (buf.toString('ascii', 0, 3) === 'ID3') {
    const size =
      (buf[6] << 21) | (buf[7] << 14) | (buf[8] << 7) | buf[9]; // syncsafe int
    i = 10 + size;
  }

  let seconds = 0;
  while (i + 4 <= buf.length) {
    if (buf[i] !== 0xff || (buf[i + 1] & 0xe0) !== 0xe0) {
      i++;
      continue;
    }
    const versionBits = (buf[i + 1] >> 3) & 0x03;
    const bitrateIdx = (buf[i + 2] >> 4) & 0x0f;
    const rateIdx = (buf[i + 2] >> 2) & 0x03;
    const padding = (buf[i + 2] >> 1) & 0x01;
    const rates = RATES[versionBits];
    if (!rates || rateIdx === 3 || bitrateIdx === 0 || bitrateIdx === 15) {
      i++;
      continue;
    }
    const sampleRate = rates[rateIdx];
    const kbps = (versionBits === 3 ? V1_L3 : V2_L3)[bitrateIdx];
    const samplesPerFrame = versionBits === 3 ? 1152 : 576;
    const frameLen = Math.floor((samplesPerFrame / 8) * (kbps * 1000) / sampleRate) + padding;
    if (frameLen < 4) {
      i++;
      continue;
    }
    seconds += samplesPerFrame / sampleRate;
    i += frameLen;
  }
  if (seconds === 0) throw new Error('MP3: フレームを解析できませんでした');
  return seconds;
}
