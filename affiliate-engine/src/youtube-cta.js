'use strict';

/**
 * Shorts 用の導線。URLは置かない。
 * YouTube公式: Shorts のコメント / 説明欄の URL はクリック不可。
 * https://support.google.com/youtube/answer/13748639
 */

const PROFILE_CTA = '詳しくはプロフィールのリンク（PR）';

function isHealingPet(post) {
  if (!post || post.genre !== 'ペット') return false;
  const content = String(post.content || '');
  if (content.includes('{{AFFILIATE_LINK}}')) return false;
  if (post.cta_type === 'direct') return false;
  return true;
}

function applyProfileCta(text) {
  const cleaned = String(text || '')
    .replace(/\{\{AFFILIATE_LINK\}\}/g, '')
    .replace(/[ \t]+$/gm, '')
    .trim();
  if (!cleaned) return PROFILE_CTA;
  if (/プロフィールのリンク/.test(cleaned)) return cleaned;
  return `${cleaned}\n\n${PROFILE_CTA}`;
}

function youtubeDescription(text) {
  let body = applyProfileCta(text);
  if (!/#(PR|pr|広告|プロモーション|アフィリエイト)/.test(body)) {
    body = `${body}\n#PR`;
  }
  if (/https?:\/\//.test(body)) {
    throw new Error('Shorts説明文にURLを入れない');
  }
  return body;
}

module.exports = { PROFILE_CTA, isHealingPet, applyProfileCta, youtubeDescription };
