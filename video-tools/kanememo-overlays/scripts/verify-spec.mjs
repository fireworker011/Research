import { readFileSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const inputRoot = process.argv[2] || "/tmp/inputs";

const slugs = [
  ["kougaku-hayamihyo", "2026-10-28-金メモ-kougaku-hayamihyo"],
  ["shussan-ichijikin", "2026-10-29-金メモ-shussan-ichijikin"],
  ["shobyo-teate", "2026-10-29-金メモ-shobyo-teate"],
  ["nenkin-kurisage", "2026-10-29-金メモ-nenkin-kurisage"],
];

const banned = ["70,608", "237,279", "844,900", "約9.3万", "42万円", "8.4%"];
const affiliateNeedles = [
  ["a8", "net"].join("."),
  ["a8", "mat"].join(""),
  ["px", "a8"].join("."),
];
let failed = 0;

const fail = (message) => {
  failed += 1;
  console.error(`FAIL ${message}`);
};

const stringsOf = (value, key, out) => {
  if (typeof value === "string") {
    if (key !== "slug" && key !== "pos") {
      out.push(value);
    }
    return;
  }
  if (Array.isArray(value)) {
    for (const item of value) stringsOf(item, key, out);
    return;
  }
  if (value && typeof value === "object") {
    for (const [childKey, child] of Object.entries(value)) {
      stringsOf(child, childKey, out);
    }
  }
};

for (const [slug, stem] of slugs) {
  const spec = JSON.parse(
    readFileSync(path.join(root, "data", `${slug}.json`), "utf8"),
  );
  const scriptPath = path.join(inputRoot, "video/scripts", `${stem}.md`);
  const srtPath = path.join(inputRoot, "video/subs", `${stem}.srt`);
  if (!existsSync(scriptPath) || !existsSync(srtPath)) {
    fail(`${slug} の台本かSRTが無い: ${scriptPath}`);
    continue;
  }
  const corpus = `${readFileSync(scriptPath, "utf8")}\n${readFileSync(srtPath, "utf8")}`;
  const texts = [];
  stringsOf(spec, "", texts);
  const blob = texts.join("\n");
  const packed = `${blob}\n${JSON.stringify(spec)}`.toLowerCase();
  if (affiliateNeedles.some((needle) => packed.includes(needle))) {
    fail(`${slug} にアフィリエイトURLがある`);
  }
  for (const word of banned) {
    if (blob.includes(word)) fail(`${slug} に出さない数字がある: ${word}`);
  }
  for (const text of texts) {
    const pieces = text.split("\n");
    for (const piece of pieces) {
      if (piece.length === 0) continue;
      if (!corpus.includes(piece)) {
        fail(`${slug} 台本に無い文字: ${piece}`);
      }
    }
  }
  const callout = spec.callout.lines.join("");
  if (!corpus.includes(callout)) {
    fail(`${slug} 大きな金額の連結が台本に無い: ${callout}`);
  }
  const bottom = spec.subtitles
    .filter((cue) => cue.pos === "bottom")
    .slice()
    .sort((a, b) => a.fromSec - b.fromSec);
  let maxGap = 0;
  for (let i = 1; i < bottom.length; i += 1) {
    const gap = Number((bottom[i].fromSec - bottom[i - 1].toSec).toFixed(3));
    maxGap = Math.max(maxGap, gap);
    if (gap > 1.5) fail(`${slug} 字幕の間が1.5秒超: ${gap}`);
    if (gap < 0) fail(`${slug} 字幕が重なる: ${gap}`);
  }
  if (spec.durationSec !== 15 || spec.fps !== 24) {
    fail(`${slug} 尺かfpsが台本と違う`);
  }
  console.log(`${slug} 字幕の最大の間=${maxGap}秒 文字数=${texts.length}`);
}

if (failed > 0) {
  console.error(`verify FAIL ${failed}`);
  process.exit(1);
}
console.log("verify PASS");
