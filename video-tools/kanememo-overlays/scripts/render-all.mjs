// preview の音声は検査用の 440Hz だけ。overlay の mov には音を入れない。
// volume=-12dB のとき平均音量は約 -36dB。これより小さいと check_video.sh の M8 が落ちる。
import { spawnSync } from "node:child_process";
import { mkdirSync, rmSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const previewOnly = process.argv.includes("--preview-only");
const overlayOnly = process.argv.includes("--overlay-only");
const slugs = [
  "kougaku-hayamihyo",
  "shussan-ichijikin",
  "shobyo-teate",
  "nenkin-kurisage",
];

const run = (command, args) => {
  const result = spawnSync(command, args, { cwd: root, stdio: "inherit" });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
};

mkdirSync(path.join(root, "out", "frames"), { recursive: true });

for (const slug of slugs) {
  const silent = path.join(root, "out", `${slug}-silent.mp4`);
  const preview = path.join(root, "out", `${slug}-preview.mp4`);
  if (!overlayOnly) {
  run("npx", [
    "remotion",
    "render",
    "src/index.ts",
    `${slug}-preview`,
    silent,
    "--codec=h264",
    "--pixel-format=yuv420p",
    "--image-format=jpeg",
    "--crf=18",
    "--concurrency=2",
  ]);
  run("ffmpeg", [
    "-y",
    "-i",
    silent,
    "-f",
    "lavfi",
    "-i",
    "sine=frequency=440:sample_rate=48000:duration=15",
    "-filter_complex",
    "[1:a]volume=-12dB[a]",
    "-map",
    "0:v:0",
    "-map",
    "[a]",
    "-c:v",
    "libx264",
    "-pix_fmt",
    "yuv420p",
    "-r",
    "24",
    "-crf",
    "18",
    "-c:a",
    "aac",
    "-b:a",
    "96k",
    "-ar",
    "48000",
    "-ac",
    "2",
    "-shortest",
    "-movflags",
    "+faststart",
    preview,
  ]);
  rmSync(silent, { force: true });

  const stills = [
    ["0.0", "0"],
    ["0.5", "12"],
    ["end-1", "336"],
  ];
  for (const [name, frame] of stills) {
    run("ffmpeg", [
      "-y",
      "-i",
      preview,
      "-vf",
      `select=eq(n\\,${frame})`,
      "-frames:v",
      "1",
      "-update",
      "1",
      path.join(root, "out", "frames", `${slug}-${name}.png`),
    ]);
  }

  }
  if (previewOnly) {
    const mp4 = statSync(preview).size;
    console.log(`${slug} preview=${(mp4 / 1024 / 1024).toFixed(1)}MB`);
    continue;
  }
  run("npx", [
    "remotion",
    "render",
    "src/index.ts",
    `${slug}-overlay`,
    path.join(root, "out", `${slug}-overlay.mov`),
    "--codec=prores",
    "--prores-profile=4444",
    "--pixel-format=yuva444p10le",
    "--image-format=png",
    "--concurrency=2",
  ]);

  const mov = statSync(path.join(root, "out", `${slug}-overlay.mov`)).size;
  const mp4 = statSync(preview).size;
  console.log(
    `${slug} preview=${(mp4 / 1024 / 1024).toFixed(1)}MB overlay=${(mov / 1024 / 1024).toFixed(1)}MB`,
  );
}
