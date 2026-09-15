"use strict";

const { describe, it } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { generateFromSeed, writeIr } = require("../src/generate");
const { emitHtml, writeHtml } = require("../src/emit-html");
const { emitWoditor, writeWoditor } = require("../src/emit-woditor");

const seed = path.join(__dirname, "..", "data", "seeds", "sample-adult-adv.json");

describe("generate and emit", () => {
  it("writes ir, html, woditor from seed", () => {
    const spec = generateFromSeed(seed);
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "dgf-"));
    const ir = writeIr(spec, path.join(dir, "ir"));
    const htmlFile = writeHtml(spec, path.join(dir, "preview"));
    const w = writeWoditor(spec, path.join(dir, "woditor"));
    assert.ok(fs.existsSync(ir));
    const html = fs.readFileSync(htmlFile, "utf8");
    assert.match(html, /18歳以上/);
    assert.match(html, /終電後の事務所/);
    assert.match(html, /青山 綾/);
    const txt = fs.readFileSync(w.file, "utf8");
    assert.match(txt, /■文章の表示/);
    const code = fs.readFileSync(w.eventCodeFile, "utf8");
    assert.match(code, /WoditorEvCOMMAND_START/);
    assert.match(code, /\[102\]/);
    const guide = fs.readFileSync(w.readme, "utf8");
    assert.match(guide, /WOLF_DIR/);
    assert.equal(emitHtml(spec).includes("<script>"), true);
    assert.match(emitWoditor(spec), /h1/);
  });

  it("refuses to emit html for underage spec", () => {
    const spec = generateFromSeed(seed);
    spec.characters[0].age = 16;
    assert.throws(() => emitHtml(spec));
  });
});
