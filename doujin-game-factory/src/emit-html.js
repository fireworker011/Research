"use strict";

const fs = require("fs");
const path = require("path");
const { assertSellable } = require("./compliance");

function htmlEscape(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function emitHtml(spec) {
  assertSellable(spec);
  const payload = JSON.stringify(spec).replace(/</g, "\\u003c");
  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${htmlEscape(spec.title)} (18+ preview)</title>
  <style>
    body { font-family: sans-serif; background:#140b12; color:#f3e6ee; margin:0; }
    main { max-width: 42rem; margin: 0 auto; padding: 1rem 1rem 4rem; }
    .gate, .box { background:#24141e; border:1px solid #5a3048; border-radius:12px; padding:1rem; }
    button { font-size:1rem; padding:.6rem 1rem; margin:.3rem .3rem 0 0; border-radius:8px; border:0; background:#c45c8a; color:#fff; }
    button.secondary { background:#3a2432; }
    #text { min-height: 6rem; white-space: pre-wrap; line-height:1.6; }
    .meta { opacity:.7; font-size:.85rem; }
  </style>
</head>
<body>
<main>
  <p class="meta">HTML preview / 販売物ではない / ${htmlEscape(spec.pipeline || "")}</p>
  <div id="gate" class="gate">
    <h1>18歳以上ですか</h1>
    <p>成人向けフィクション。実在人物ではない。未成年の描写は仕様で拒否済み。</p>
    <button id="yes">18歳以上である</button>
    <button class="secondary" id="no">閉じる</button>
  </div>
  <div id="play" class="box" hidden>
    <h1>${htmlEscape(spec.title)}</h1>
    <p class="meta" id="who"></p>
    <div id="text"></div>
    <div id="choices"></div>
  </div>
</main>
<script>
const SPEC = ${payload};
let nodeId = SPEC.start;
const $ = (id) => document.getElementById(id);
$("no").onclick = () => { document.body.innerHTML = "<p style='padding:2rem'>遮断しました。</p>"; };
$("yes").onclick = () => { $("gate").hidden = true; $("play").hidden = false; render(); };
function charName(id) {
  const c = (SPEC.characters || []).find(x => x.id === id);
  return c ? c.name : "";
}
function render() {
  const n = SPEC.nodes.find(x => x.id === nodeId);
  if (!n) { $("text").textContent = "node missing"; return; }
  $("who").textContent = n.speaker ? charName(n.speaker) : (n.type === "hscene" ? "Hシーン" : "");
  $("text").textContent = n.text || "";
  const box = $("choices");
  box.innerHTML = "";
  if (n.type === "end") {
    const b = document.createElement("button");
    b.textContent = "最初から";
    b.onclick = () => { nodeId = SPEC.start; render(); };
    box.appendChild(b);
    return;
  }
  if (n.type === "choice") {
    n.options.forEach(o => {
      const b = document.createElement("button");
      b.textContent = o.label;
      b.onclick = () => { nodeId = o.goto; render(); };
      box.appendChild(b);
    });
    return;
  }
  const b = document.createElement("button");
  b.textContent = "次へ";
  b.onclick = () => { nodeId = n.goto; render(); };
  box.appendChild(b);
}
</script>
</body>
</html>
`;
}

function writeHtml(spec, outDir) {
  fs.mkdirSync(outDir, { recursive: true });
  const file = path.join(outDir, "index.html");
  fs.writeFileSync(file, emitHtml(spec));
  return file;
}

module.exports = { emitHtml, writeHtml };
