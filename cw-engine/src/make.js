'use strict';

const { categoryById } = require('./util');
const { checkDeliverable } = require('./compliance');
const llm = require('./llm');

const MAKER_SYSTEM = {
  writing_article: '記事本文だけを Markdown で書く。見出し（##）を使い、導入・本文・まとめの順。事実は素材にあるものだけ。',
  writing_sns: '投稿文だけを書く。1本ごとに「---」で区切る。ハッシュタグは素材か指示にあるものだけ。',
  writing_script: '台本だけを書く。「ナレーション:」「テロップ:」の行で構成する。秒数は指示があるときだけ。',
  writing_copy: '商品説明・コピーだけを書く。効果・効能の断定と最上級表現は使わない。',
  text_cleanup: '与えられた文字起こしを整文・要約する。内容の追加や改変はしない。話者表記は元に従う。',
  translation: '与えられた原文を翻訳する。訳注は【訳注】で最小限。原文に無い情報を足さない。',
  data_structuring: 'CSV だけを出力する。1行目はヘッダ。値のカンマは二重引用符で囲む。素材に無い値は空欄。',
  video_edit_short: '編集計画だけを書く。「カット表（開始-終了 / 内容 / テロップ文）」と「テロップ原稿一覧」の2節。動画そのものは作れないと明記する。'
};

function buildPrompt(job, { category, brief, materials, revisionRequest }) {
  const parts = [];
  parts.push(`募集文（公開）:\n${job.text_excerpt || job.title}`);
  parts.push(`BRIEF（成果物の定義・受入条件）:\n${String(brief || '').slice(0, 4000)}`);
  parts.push(`素材・クライアント指示:\n${String(materials || '').slice(0, 12000)}`);
  if (revisionRequest) parts.push(`修正依頼（クライアント）:\n${String(revisionRequest).slice(0, 3000)}\n上の修正依頼を反映した反映版を作る。`);
  const spec = Array.isArray(brief?.spec) ? brief.spec : null;
  parts.push(
    [
      `成果物: ${category ? category.label : '募集文どおり'}。`,
      spec ? `分量: ${spec[0]}〜${spec[1]} 文字。` : '',
      '素材に無い事実・数字・固有名詞・体験談・URL は書かない。不明は【要確認】と書く。',
      '前置き・後置き・説明文・コードフェンスは書かない。成果物本体だけを出力する。'
    ]
      .filter(Boolean)
      .join('\n')
  );
  return parts.join('\n\n');
}

function extension(category) {
  return category && category.id === 'data_structuring' ? 'csv' : 'md';
}

function makerSystem(category) {
  return MAKER_SYSTEM[category ? category.id : ''] || '成果物本体だけを書く。';
}

function grokPacket(job, { capability, brief, briefText, materials, revisionRequest = null }) {
  const category = categoryById(capability, job.category);
  const prompt = buildPrompt(job, { category, brief: briefText, materials, revisionRequest });
  const system = `${llm.BASE_SYSTEM}\n\n${makerSystem(category)}`;
  return { jobId: job.id, category, ext: extension(category), system, prompt };
}

function formatGrokPrompt(packet) {
  return [
    '# Grok への完成品依頼（Anthropic API は使わない）',
    '',
    'HQ clone には貼るな。この非公開 Issue の仕事だけ。素材に無い事実は書くな。',
    '',
    '## 守ること',
    packet.system,
    '',
    '## 依頼',
    packet.prompt,
    '',
    '## 書けたら Issue にこれだけ',
    '',
    '```',
    `CW: DRAFT ${packet.jobId}`,
    '<成果物本体だけ。このフェンスの説明文は貼らない>',
    '```'
  ].join('\n');
}

function qaDeliverableText(job, { capability, brief, materials, text }) {
  const category = categoryById(capability, job.category);
  const cleaned = llm.stripFences(text);
  const qa = checkDeliverable(cleaned, {
    materials: `${materials || ''}\n${job.text_excerpt || ''}`,
    charSpec: brief && Array.isArray(brief.spec) ? brief.spec : null,
    category: category ? category.id : null
  });
  return {
    ok: qa.ok,
    blocked: null,
    text: cleaned,
    qa,
    category,
    ext: extension(category),
    human_tool_required: Boolean(category && category.ai_complete === false)
  };
}

async function makeDeliverable(job, { capability, brief, briefText, materials, revisionRequest = null }) {
  const packet = grokPacket(job, { capability, brief, briefText, materials, revisionRequest });
  if (!llm.llmAvailable()) {
    return {
      ok: false,
      blocked: 'await_grok',
      text: null,
      category: packet.category,
      ext: packet.ext,
      grokPrompt: formatGrokPrompt(packet)
    };
  }
  let raw;
  try {
    raw = await llm.ask(packet.prompt, { system: makerSystem(packet.category), maxTokens: 8000 });
  } catch (err) {
    return { ok: false, blocked: `llm_error:${String(err.message || err).slice(0, 80)}`, text: null, category: packet.category, ext: packet.ext };
  }
  return qaDeliverableText(job, { capability, brief, materials, text: raw });
}

module.exports = {
  MAKER_SYSTEM,
  buildPrompt,
  makeDeliverable,
  extension,
  grokPacket,
  formatGrokPrompt,
  qaDeliverableText
};
