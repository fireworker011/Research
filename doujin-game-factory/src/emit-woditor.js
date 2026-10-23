"use strict";

const fs = require("fs");
const path = require("path");
const { assertSellable } = require("./compliance");
const { emitEventCode } = require("./emit-event-code");

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
  } else if (node.type === "end") {
    lines.push("■文章の表示");
    lines.push(escapeCmd(node.text || "END"));
    lines.push("");
  }
  return lines.join("\n");
}

function emitWoditor(spec) {
  assertSellable(spec);
  const chars = spec.characters || [];
  const parts = [];
  parts.push("人間可読のコマンド文。Editor には貼れない。");
  parts.push("貼るのは event-code.txt（WoditorEvCOMMAND_START ... END）。");
  parts.push("");
  parts.push(`タイトル: ${spec.title}`);
  parts.push(`開始: ${spec.start}`);
  parts.push("");
  for (const n of spec.nodes) {
    parts.push(nodeToCommands(n, chars));
  }
  return parts.join("\n");
}

function pcPipelineMarkdown() {
  return `# PCパイプライン（ウディタ本線）

前提: Windows PC で公式 WOLF RPGエディターを使う。
このリポジトリの Linux Cloud Agent は Editor.exe を実行できない。生成物を PC に持っていく。

## 1. 一度だけ

1. https://silversecond.com/WolfRPGEditor/ から最新版を入れる（解凍するだけ）
2. Node.js LTS を入れる
3. 環境変数 \`WOLF_DIR\` を \`Editor.exe\` があるフォルダにする
4. \`scripts\\windows\\01_check.bat\` を実行し、Editor.exe が見えることを確認する

## 2. 毎回（作品ごと）

1. \`node src/cli.js generate --seed data/seeds/sample-adult-adv.json\`
2. \`node src/cli.js woditor --in output/ir/game.json\`
3. Editor.exe を起動し、サンプルゲームを複製した空プロジェクトを開く
4. タイトルマップにイベントを1つ置き、起動条件を「自動実行」
5. \`output/woditor/event-code.txt\` を全選択コピー
6. イベントコマンド欄で右クリック → 「クリップボード→コード貼り付け」（Eキー）。Vキーでは貼れない
7. Ctrl+T または F9 でテストプレイ。両分岐を最後まで通す
8. 絵・音は Data 配下に入れてから、必要ならコマンドを手で足す
9. \`scripts\\windows\\04_gamedata.bat\` または Editor のゲームデータ作成。Editor.exe は配布フォルダに入れない
10. 出力フォルダを zip して DLsite/FANZA に出す。AI申告を偽らない

## 3. 公式テキスト入出力（任意）

共同作業・バックアップ用。ゲーム中には読めない。

\`\`\`
Editor.exe -txtoutput -txt_folder Data_AutoTXT -target ALL -wait
Editor.exe -txtinput  -txt_folder Data_AutoTXT -target ALL -wait
Editor.exe -gamedata -crypt NO
\`\`\`

\`scripts\\windows\\03_txtoutput.bat\` が同じことをする。
複数保存(TXT)のコモン一括形式は、公式サンプル無しでは捏造しない。貼り付け経路を正とする。

## 4. まだ自動化しないこと

- マップタイルの配置
- 戦闘・データベース一式
- 審査提出そのもの
- 週4本（DLsite AI生成の申請月3と衝突）
`;
}

function writeWoditor(spec, outDir) {
  fs.mkdirSync(outDir, { recursive: true });
  const commandsFile = path.join(outDir, "commands.txt");
  const eventCodeFile = path.join(outDir, "event-code.txt");
  const readme = path.join(outDir, "PC_PIPELINE.md");
  fs.writeFileSync(commandsFile, emitWoditor(spec) + "\n");
  fs.writeFileSync(eventCodeFile, emitEventCode(spec));
  const canonical = path.join(__dirname, "..", "docs", "PC_PIPELINE.md");
  const guide = fs.existsSync(canonical) ? fs.readFileSync(canonical, "utf8") : pcPipelineMarkdown();
  fs.writeFileSync(readme, guide);
  return { file: commandsFile, eventCodeFile, readme };
}

module.exports = { emitWoditor, writeWoditor, pcPipelineMarkdown };
