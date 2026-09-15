'use strict';

const { categoryById, addDays, dateJst } = require('./util');
const { NEEDS_CHECK } = require('./compliance');
const llm = require('./llm');

function charSpecFor(job, category) {
  if (Array.isArray(job.char_spec) && job.char_spec[1] > 0) return job.char_spec;
  if (category && Array.isArray(category.default_chars) && category.default_chars[1] > 0) return category.default_chars;
  return null;
}

function materialsRequest(missing) {
  if (!missing.length) return null;
  return [
    'お世話になっております。着手前に次をご共有ください。',
    ...missing.map((m) => `・${m}`),
    '揃い次第、初稿を目安どおりお送りします。'
  ].join('\n');
}

function buildBrief(job, { capability, contractNotes = '', materials = '', now } = {}) {
  const category = categoryById(capability, job.category);
  const spec = charSpecFor(job, category);
  const contractDate = dateJst(now);
  const due = addDays(contractDate, category ? category.turnaround_days : 2);
  const hasMaterials = String(materials || '').trim().length > 0;
  const missing = [];
  if (!hasMaterials) missing.push('元になる素材（テーマ・資料・原稿・参考URL など、募集文に書かれたもの）');
  if (!spec) missing.push('分量（文字数・本数）');
  if (!/(トーン|口調|文体|敬語|カジュアル|ターゲット|読者|想定)/.test(`${job.text_excerpt || ''}${contractNotes}${materials}`)) missing.push('トーン・想定読者（無ければ「一般向け・丁寧」で作ります）');
  const lines = [];
  lines.push(`# BRIEF — ${job.id} ${job.title || ''}`.trim());
  lines.push('');
  lines.push(`- カテゴリ: ${category ? category.label : NEEDS_CHECK}`);
  lines.push(`- 契約日（JST）: ${contractDate}`);
  lines.push(`- 初稿の目安: ${due}${job.deadline ? `（募集の期限: ${job.deadline}）` : ''}`);
  lines.push(`- 公開の報酬表示: ${job.public_price_yen != null ? `${job.public_price_yen} 円（カタログ。確定ではない。台帳に足すな）` : '無し'}`);
  lines.push('');
  lines.push('## 成果物の定義');
  lines.push(`- 形式: ${category && category.id === 'data_structuring' ? 'CSV（UTF-8・ヘッダ行あり）+ 補足メモ' : 'テキスト（.md と .txt）。ご指定があればその形式'}`);
  lines.push(`- 分量: ${spec ? `${spec[0]}〜${spec[1]} 文字` : NEEDS_CHECK}`);
  lines.push(`- 本数: ${/(\d+)\s*本/.test(job.text_excerpt || '') ? (job.text_excerpt.match(/(\d+)\s*本/) || [])[1] + ' 本' : `1 ${category ? category.unit : '本'}（募集文に本数があれば従う）`}`);
  lines.push('- トーン・読者: 募集文とクライアント指示に従う。無ければ一般向け・丁寧');
  lines.push('');
  lines.push('## 受入条件（納品前に全部 yes）');
  lines.push('- 募集文・契約メッセージの指示をすべて反映している');
  lines.push('- 事実・数字・固有名詞は素材にあるものだけ。無いものは書かない');
  lines.push('- コピペ・無断転載が無い。引用は出典明記で最小限');
  lines.push('- 断定表現（治る・必ず・No.1）と個人情報が無い');
  lines.push('- 分量・形式・本数がこの BRIEF と一致');
  lines.push('- AI利用の開示条件（募集文・契約）に従っている');
  lines.push('');
  lines.push('## 手順');
  lines.push('1. 素材と指示を読み、不足を依頼する（下の依頼文）');
  lines.push('2. 構成（見出し・流れ）を作る');
  lines.push('3. 本文を作る → QA（自動）→ 人間が最終確認');
  lines.push('4. 納品メッセージと一緒に納品ボタン（人間）');
  lines.push('5. 修正依頼は `CW: REVISE <id>` で反映版を作る（無償1回）');
  lines.push('');
  lines.push('## 禁止');
  lines.push('- 仮払い前の着手。直接取引への移動。実績の発明。他者コンテンツのコピー');
  lines.push('- クライアント素材をこの作業以外に使う・外部へ出す');
  lines.push('');
  lines.push('## 不足している素材');
  if (missing.length) {
    for (const m of missing) lines.push(`- ${NEEDS_CHECK} ${m}`);
    lines.push('');
    lines.push('### 素材依頼文（そのまま貼れる）');
    lines.push('```');
    lines.push(materialsRequest(missing));
    lines.push('```');
  } else {
    lines.push('- 無し（着手できる）');
  }
  if (String(contractNotes || '').trim()) {
    lines.push('');
    lines.push('## 契約時のメモ（人間が貼った文）');
    lines.push(String(contractNotes).trim());
  }
  return { text: lines.join('\n'), spec, due, missing, ready: missing.length === 0 || (hasMaterials && spec !== null) };
}

async function enrichBrief(brief, job, { materials = '' } = {}) {
  if (!llm.llmAvailable() || !String(materials || '').trim()) return brief;
  const prompt = [
    `募集文（公開）:\n${job.text_excerpt || job.title}`,
    `素材・指示:\n${String(materials).slice(0, 6000)}`,
    '上の情報から「構成案」を見出しの箇条書きで 5〜10 行だけ書いてください。素材に無い事実・数字・固有名詞は書かず、不足は【要確認】と書いてください。前置きは不要です。'
  ].join('\n\n');
  try {
    const outline = llm.stripFences(await llm.ask(prompt, { maxTokens: 800 }));
    if (!outline) return brief;
    return { ...brief, text: `${brief.text}\n\n## 構成案（機械。人間が確認）\n${outline}` };
  } catch (_) {
    return brief;
  }
}

module.exports = { buildBrief, enrichBrief, charSpecFor, materialsRequest };
