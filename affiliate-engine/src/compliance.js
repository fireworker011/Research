'use strict';

/**
 * コンプライアンスチェック
 *
 * アカウント凍結・法令違反は収益ゼロに直結するため、
 * 投稿前に全コンテンツをここに通す。
 *
 * 根拠:
 * - 景品表示法 ステマ規制（2023年10月施行）: 広告であることの明示が必要
 * - Meta コミュニティ規定: アダルト・出会い系の性的訴求は禁止
 * - 薬機法・景表法: 効果効能の断定表現は不可
 */

const DISCLOSURE_PATTERN = /#(PR|pr|広告|プロモーション|アフィリエイト)/;

// Meta ポリシー違反・法令違反リスクの高い表現（投稿ブロック対象）
const BLOCKED_PATTERNS = [
  // 誇大・断定（景表法/薬機法）
  /(絶対|必ず|100%)(稼げ|痩せ|儲か|治る|モテる)/,
  /誰でも(簡単に)?月\d+万/,
  /(シミ|シワ|ニキビ)が(消える|治る)/,
  /(肌|顔|見た目)が若返(る|り|った)/,
  // アダルト直接訴求（Meta ポリシー）
  /(出会い系|セフレ|パパ活|アダルト動画|エロ)/,
  // 投資・副業詐欺類似表現
  /(元本保証|確実に増え|放置で稼げ)/
];

/**
 * 投稿本文をチェックする。
 * @returns {{ ok: boolean, text: string, reasons: string[] }}
 *   ok=false ならブロック。ok=true でも text は修正済み（#PR 自動付与など）の場合がある。
 */
function checkContent(text) {
  const reasons = [];

  for (const pattern of BLOCKED_PATTERNS) {
    const match = text.match(pattern);
    if (match) {
      reasons.push(`禁止表現に該当: 「${match[0]}」`);
    }
  }
  if (reasons.length > 0) {
    return { ok: false, text, reasons };
  }

  // リンクを含む投稿（=アフィリエイト誘導）は広告表記必須
  const hasLink = /https?:\/\//.test(text);
  if (hasLink && !DISCLOSURE_PATTERN.test(text)) {
    text = `${text}\n#PR`;
    reasons.push('広告表記 #PR を自動付与');
  }

  return { ok: true, text, reasons };
}

module.exports = { checkContent, DISCLOSURE_PATTERN };
