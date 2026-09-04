#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const { generateFromSeed, writeIr, loadJson } = require("./generate");
const { validateSpec } = require("./compliance");
const { writeHtml } = require("./emit-html");
const { writeWoditor } = require("./emit-woditor");
const { projectMonth, defaultScenarios, PLATFORM_CAPS } = require("./finance");

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  if (i === -1) return fallback;
  return process.argv[i + 1];
}

function cmd() {
  return process.argv[2] || "help";
}

function print(obj) {
  process.stdout.write(JSON.stringify(obj, null, 2) + "\n");
}

function help() {
  process.stdout.write(`doujin-game-factory
  generate  --seed <json>     検品して IR を output/ir/game.json へ
  validate  --in <json>
  preview   --in <json>       グラフ確認用 HTML（Editorの代用ではない）
  woditor   --in <json>       PCのEditorへ貼る event-code.txt
  finance   --price --copies --works [--cap]
  gate      同上。今決めることだけ出す
  scenarios --price
`);
}

function main() {
  const c = cmd();
  if (c === "help" || c === "-h") return help();

  if (c === "generate") {
    const seed = arg("--seed");
    if (!seed) throw new Error("--seed required");
    const spec = generateFromSeed(seed);
    const file = writeIr(spec, path.join(__dirname, "..", "output", "ir"));
    print({ ok: true, file, title: spec.title, nodes: spec.nodes.length });
    return;
  }
  if (c === "validate") {
    const spec = loadJson(arg("--in"));
    print(validateSpec(spec));
    if (!validateSpec(spec).ok) process.exitCode = 1;
    return;
  }
  if (c === "preview") {
    const spec = loadJson(arg("--in"));
    const file = writeHtml(spec, path.join(__dirname, "..", "output", "preview"));
    print({ ok: true, file, hint: "グラフ確認用。本番テストは PC の Editor F9" });
    return;
  }
  if (c === "woditor") {
    const spec = loadJson(arg("--in"));
    const out = writeWoditor(spec, path.join(__dirname, "..", "output", "woditor"));
    print({
      ok: true,
      ...out,
      next: "PC で scripts/windows/01_check.bat → event-code.txt を自動実行イベントへ貼る → F9",
      warning: "このコマンドは Game.exe をビルドしない。Editor.exe -gamedata がビルド",
    });
    return;
  }
  if (c === "finance" || c === "gate" || c === "scenarios") {
    const price = Number(arg("--price", "2200"));
    if (c === "scenarios") return print(defaultScenarios(price));
    const copies = Number(arg("--copies", "0"));
    const works = Number(arg("--works", "0"));
    const cap = Number(arg("--cap", String(PLATFORM_CAPS.dlsite_ai_generated.worksPerMonth)));
    const result = projectMonth({
      priceYen: price,
      copiesPerWork: copies,
      worksPerMonth: works,
      platformCap: cap,
    });
    if (c === "gate") {
      print({
        now_decide: [
          "エンジンはウディタ。最初の作品は戦闘なしの短い成人ADV（自動実行イベント）",
          "フルAIで週1を捨てる（DLsite AI生成は申請月3本）。PCがあっても販売枠は増えない",
          "月200万を『初月から』語らない。初作30本ゲートを先に置く",
        ],
        later: [
          "RPG戦闘を足すか",
          "価格",
          "サークル名・世界観の量産",
        ],
        irreversible: [
          "虚偽のAI非申告（アカウント死）",
          "未成年に見えるキャラ（法とPF停止）",
          "複数サークルで月次上限回避（公式が明示的に不可）",
        ],
        reversible: [
          "エンジン（IRが残る限り HTML↔ウディタ貼り付けはやり直せる）",
          "価格",
          "本数ペース",
        ],
        finance: result,
        caps: PLATFORM_CAPS,
      });
      return;
    }
    print(result);
    return;
  }
  help();
  process.exitCode = 1;
}

try {
  main();
} catch (e) {
  print({ ok: false, error: e.message, errors: e.errors || undefined });
  process.exitCode = 1;
}
