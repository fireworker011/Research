"use strict";

const { assertSellable } = require("./compliance");

/**
 * イベントコードは公式の「イベントコード→クリップボードへコピー」形式。
 * 一次例: YADOT サンプル「宿屋の人」
 *   [101] 文章 / [102] 選択肢 / [401] 分岐頭 / [0] 分岐内終端 / [499] 分岐終了
 * [102] の数値 50 は同例のコピー。公式ドキュメント上の意味は未確認。
 * 貼り付け後、Editor で選択肢コマンドを開いて動作を目視すること。
 */

function escapeWolfString(text) {
  return String(text)
    .replace(/\r\n/g, "\n")
    .replace(/\n/g, "<\\n>")
    .replace(/"/g, "”");
}

function line(code, indent, nums, strs) {
  const head = `[${code}][${nums.length},${strs.length}]<${indent}>`;
  const numPart = nums.length ? `(${nums.join(",")})` : "()";
  const strPart = strs.length
    ? `(${strs.map((s) => `"${escapeWolfString(s)}"`).join(",")})`
    : "()";
  return `${head}${numPart}${strPart}`;
}

function speakerOf(spec, id) {
  const ch = (spec.characters || []).find((c) => c.id === id);
  return ch ? ch.name : "";
}

function nodeById(spec, id) {
  const n = (spec.nodes || []).find((x) => x.id === id);
  if (!n) throw new Error(`node not found: ${id}`);
  return n;
}

function messageText(spec, node) {
  const who = speakerOf(spec, node.speaker);
  const body = node.text || "";
  if (node.type === "hscene") {
    const prefix = "【Hシーン】成人・合意";
    return who ? `${prefix}<\\n>【${who}】<\\n>${body}` : `${prefix}<\\n>${body}`;
  }
  return who ? `【${who}】<\\n>${body}` : body;
}

function compileNode(spec, nodeId, indent, stack) {
  if (stack.includes(nodeId)) {
    return [line(103, indent, [], [`循環参照 ${nodeId}。ここで止めた`])];
  }
  const node = nodeById(spec, nodeId);
  const nextStack = stack.concat(nodeId);
  const out = [];

  if (node.type === "say" || node.type === "hscene" || node.type === "end") {
    out.push(line(101, indent, [], [messageText(spec, node)]));
    if (node.type !== "end" && node.goto) {
      out.push(...compileNode(spec, node.goto, indent, nextStack));
    }
    return out;
  }

  if (node.type === "choice") {
    const opts = node.options || [];
    if (opts.length < 2 || opts.length > 10) {
      throw new Error(`${node.id}: 選択肢は 2〜10`);
    }
    out.push(line(102, indent, [50], opts.map((o) => o.label)));
    opts.forEach((o, i) => {
      out.push(line(401, indent, [i + 2], []));
      out.push(...compileNode(spec, o.goto, indent + 1, nextStack));
      out.push(line(0, indent + 1, [], []));
    });
    out.push(line(499, indent, [], []));
    return out;
  }

  throw new Error(`${node.id}: 未対応 type ${node.type}`);
}

function emitEventCode(spec) {
  assertSellable(spec);
  const body = compileNode(spec, spec.start, 0, []);
  return ["WoditorEvCOMMAND_START", ...body, "WoditorEvCOMMAND_END"].join("\n") + "\n";
}

module.exports = { emitEventCode, escapeWolfString, line };
