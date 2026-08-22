"use strict";

const fs = require("fs");
const path = require("path");
const { assertSellable } = require("./compliance");

function escapeCmd(text) {
  return String(text).replace(/\r\n/g, "\n");
}

function nodeToCommands(node, characters) {
  const lines = [];
  const speaker = (id) => {
    if (!id) return "";
    const ch = characters.find((c) => c.id === id);
    return ch ? ch.name : id;
  };
  lines.push(`# node ${node.id} type=${node.type}`);
  if (node.type === "say") {
    lines.push("■文章の表示");
    if (node.speaker) lines.push(`【${speaker(node.speaker)}】`);
    lines.push(escapeCmd(node.text));
    lines.push("");
  } else if (node.type === "hscene") {
    lines.push("■文章の表示");
    lines.push("【Hシーン】成人同士・合意済み。画像は別アセット。");
    lines.push(escapeCmd(node.text));
    lines.push("");
  } else if (node.type === "choice") {
    lines.push("■選択肢");
    for (const o of node.options) {
      lines.push(`- ${o.label} => ${o.goto}`);
    }
    lines.push("");
    lines.push("※ウディタの分岐はコモン側の条件分岐に手で結ぶ。このテキストは設計図であり、-txtinput 可能な完全バイナリではない。");
    lines.push("");
  } else if (node.type === "end") {
    lines.push("■文章の表示");
    lines.push(escapeCmd(node.text || "END"));
    lines.push("■ゲーム終了");
    lines.push("");
  }
  return lines.join("\n");
}

function emitWoditor(spec) {
  assertSellable(spec);
  const chars = spec.characters || [];
  const parts = [];
  parts.push("WOLF RPG Editor コマンド文エクスポート（人間がEditorに貼る用）");
  parts.push("公式: Editor.exe -txtoutput / -txtinput は Windows の Editor.exe が必要。");
  parts.push("このファイルを Linux/Cloud Agent から .mps に直接は書けない。");
  parts.push("");
  parts.push(`タイトル: ${spec.title}`);
  parts.push(`開始: ${spec.start}`);
  parts.push("");
  for (const n of spec.nodes) {
    parts.push(nodeToCommands(n, chars));
  }
  return parts.join("\n");
}

function writeWoditor(spec, outDir) {
  fs.mkdirSync(outDir, { recursive: true });
  const file = path.join(outDir, "commands.txt");
  fs.writeFileSync(file, emitWoditor(spec) + "\n");
  const readme = path.join(outDir, "WINDOWS_LAST_MILE.md");
  fs.writeFileSync(
    readme,
    [
      "# Windows last mile",
      "",
      "Cloud / Linux / スマホだけでは Game.exe は作れない。",
      "必要手順:",
      "1. Windows（自宅PC、クラウドVM、誰かへの依頼）で公式ウディタを入れる",
      "2. 空プロジェクトを作る",
      "3. `commands.txt` をイベントに貼る、または将来 `-txtinput` 用テキストへ変換する",
      "4. `Editor.exe -gamedata` で配布用フォルダを出す",
      "5. Editor.exe 自体は配布しない（公式の配布物ルール）",
      "",
      "自動化の境界: ここまでが人間または Windows ランナー。IR 生成までは Cloud Agent。",
      "",
    ].join("\n")
  );
  return { file, readme };
}

module.exports = { emitWoditor, writeWoditor };
