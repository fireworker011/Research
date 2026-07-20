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

/**
 * テンプレの構造検品（モデル非依存の品質ゲート）。
 * 生成モデルの賢さに品質を依存させないため、AI が生成したテンプレは
 * 必ずここを通す。軽微な不備は自動修正し、直せないものは reject する。
 *
 * @param {object} t テンプレ（{id, genre, content, link_key, ...}）
 * @param {{genres?: Set<string>|string[], linkKeys?: Set<string>|string[]}} known
 * @returns {{ ok: boolean, template: object, reasons: string[] }}
 */
function validateTemplate(t, known = {}) {
  const reasons = [];
  const genres = new Set(known.genres || []);
  const linkKeys = new Set(known.linkKeys || []);
  const out = { ...t };
  const content = String(out.content || '');

  // ジャンル必須（欠落テンプレはスケジュールに載らず死蔵される）
  if (!out.genre || (genres.size && !genres.has(out.genre))) {
    return { ok: false, template: out, reasons: [`ジャンル不正: ${JSON.stringify(out.genre)}`] };
  }

  // 長さ: Threads 上限500字。絵文字・#PR自動付与の余白を残して480字まで
  if (content.length > 480) {
    return { ok: false, template: out, reasons: [`本文が長すぎ（${content.length}字 > 480）`] };
  }
  if (content.length < 30) {
    return { ok: false, template: out, reasons: [`本文が短すぎ（${content.length}字）`] };
  }

  // プレースホルダー整合性
  const placeholders = [...content.matchAll(/\{\{(.+?)\}\}/g)].map((m) => m[1]);
  const unknownPh = placeholders.filter((p) => p !== 'AFFILIATE_LINK');
  if (unknownPh.length) {
    return { ok: false, template: out, reasons: [`未知のプレースホルダー: ${unknownPh.join(', ')}`] };
  }
  const hasLink = placeholders.includes('AFFILIATE_LINK');

  if (hasLink) {
    if (!out.link_key) {
      return { ok: false, template: out, reasons: ['{{AFFILIATE_LINK}} があるのに link_key 未指定'] };
    }
    if (linkKeys.size && !linkKeys.has(out.link_key)) {
      return { ok: false, template: out, reasons: [`未知の link_key: ${out.link_key}`] };
    }
    if (!DISCLOSURE_PATTERN.test(content)) {
      out.content = `${content}\n#PR`;
      reasons.push('#PR を自動付与');
    }
  } else if (out.link_key) {
    // リンクなしなのに link_key が付いていると分析を汚すため落とす
    delete out.link_key;
    reasons.push('リンクなしのため link_key を除去');
  }

  return { ok: true, template: out, reasons };
}

module.exports = { checkContent, validateTemplate, DISCLOSURE_PATTERN };
