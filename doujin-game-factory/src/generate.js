"use strict";

const fs = require("fs");
const path = require("path");
const { assertSellable } = require("./compliance");

function loadJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function stampMeta(spec) {
  return {
    ...spec,
    generated_at: new Date().toISOString(),
    pipeline: "doujin-game-factory/0.1",
    compile_targets: ["html_preview", "woditor_command_text"],
  };
}

function generateFromSeed(seedPath) {
  const spec = loadJson(seedPath);
  assertSellable(spec);
  return stampMeta(spec);
}

function writeIr(spec, outDir) {
  fs.mkdirSync(outDir, { recursive: true });
  const outFile = path.join(outDir, "game.json");
  fs.writeFileSync(outFile, JSON.stringify(spec, null, 2) + "\n");
  return outFile;
}

module.exports = { generateFromSeed, writeIr, loadJson };
