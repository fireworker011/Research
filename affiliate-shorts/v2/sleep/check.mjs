import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const root = new URL(".", import.meta.url).pathname;
const ids = ["01", "02", "03", "04", "05"];
const files = ["script.md", "narration.txt", "subs.srt", "pr_last2s.txt", "description.txt"];
const disclaimer = "医療的な助言ではありません";
const pr = "詳しくはプロフィールのリンク（PR）";
const cta = ["プロフィール", "リンク", "フォロー", "チャンネル登録", "コメント", "保存して", "概要欄"];
let failed = 0;

const fail = (message) => {
  failed += 1;
  console.error(message);
};

const chars = (value) => [...value].length;

for (const id of ids) {
  const dir = join(root, id);
  for (const file of files) {
    const path = join(dir, file);
    if (!existsSync(path)) {
      fail(`${id}/${file} がない`);
      continue;
    }
    const text = readFileSync(path, "utf8");
    if (!text.includes(disclaimer) && file !== "pr_last2s.txt") {
      fail(`${id}/${file} に免責がない`);
    }
    if (file !== "pr_last2s.txt" && !text.includes("http")) {
      if (file === "description.txt" || file === "script.md") {
        fail(`${id}/${file} に出典URLがない`);
      }
    }
  }

  const prText = readFileSync(join(dir, "pr_last2s.txt"), "utf8").trim();
  if (prText !== pr) {
    fail(`${id}/pr_last2s.txt が指定のPR文ではない`);
  }

  const narration = readFileSync(join(dir, "narration.txt"), "utf8");
  const prAt = narration.lastIndexOf("プロフィール");
  const body = narration.slice(0, prAt);
  for (const word of cta) {
    if (body.includes(word)) {
      fail(`${id}/narration.txt の本編に「${word}」がある`);
    }
  }
  if (!narration.trim().endsWith("PR。")) {
    fail(`${id}/narration.txt の末尾がPRではない`);
  }

  const srt = readFileSync(join(dir, "subs.srt"), "utf8").trim();
  const cues = srt.split(/\n\n+/);
  let lastStart = 0;
  let lastEnd = 0;
  cues.forEach((cue, index) => {
    const lines = cue.split("\n");
    const timing = lines[1] ?? "";
    const match = timing.match(
      /(\d\d):(\d\d):(\d\d),(\d\d\d) --> (\d\d):(\d\d):(\d\d),(\d\d\d)/,
    );
    if (!match) {
      fail(`${id}/subs.srt cue ${index + 1} の時刻が読めない`);
      return;
    }
    const toSec = (h, m, s, ms) =>
      Number(h) * 3600 + Number(m) * 60 + Number(s) + Number(ms) / 1000;
    const start = toSec(match[1], match[2], match[3], match[4]);
    const end = toSec(match[5], match[6], match[7], match[8]);
    lastStart = start;
    lastEnd = end;
    const textLines = lines.slice(2).filter((line) => line.length > 0);
    textLines.forEach((line) => {
      if (chars(line) > 16) {
        fail(`${id}/subs.srt ${chars(line)}文字: ${line}`);
      }
    });
    const isLast = index === cues.length - 1;
    const joined = textLines.join("");
    if (!isLast) {
      for (const word of ["プロフィール", "リンク", "フォロー", "コメント"]) {
        if (joined.includes(word)) {
          fail(`${id}/subs.srt の本編に「${word}」がある`);
        }
      }
    }
  });
  if (Math.abs(lastEnd - lastStart - 2) > 0.001) {
    fail(`${id}/subs.srt の最後が2秒ではない (${lastEnd - lastStart})`);
  }
  if (!srt.includes(disclaimer)) {
    fail(`${id}/subs.srt に免責がない`);
  }
}

if (failed > 0) {
  console.error(`失敗 ${failed}`);
  process.exit(1);
}
console.log("台本チェックOK");
