'use strict';

const API_URL = 'https://api.anthropic.com/v1/messages';
const DEFAULT_MODEL = process.env.CW_LLM_MODEL || process.env.CLAUDE_MODEL || 'claude-sonnet-5';

const BASE_SYSTEM = [
  'あなたはクラウドワークスで受注した仕事の下書きと完成品を作る作業者です。日本語で書きます。',
  '事実は与えられた素材・募集文・事実カードにあるものだけを使い、無いものは【要確認】と書きます。',
  '実績・経験・数字・固有名詞・体験談を発明しません。URL は素材にあるもの以外書きません。',
  '「私はAI」「AIとして」などのメタ発言を書きません。指示された形式以外の前置き・後置きを書きません。'
].join('\n');

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function llmAvailable() {
  return Boolean(process.env.ANTHROPIC_API_KEY || process.env.CLAUDE_API_KEY);
}

async function ask(prompt, { system = '', maxTokens = 4096, model = DEFAULT_MODEL } = {}) {
  const apiKey = process.env.ANTHROPIC_API_KEY || process.env.CLAUDE_API_KEY;
  if (!apiKey) throw new Error('llm_missing');
  const body = {
    model,
    max_tokens: maxTokens,
    system: system ? `${BASE_SYSTEM}\n\n${system}` : BASE_SYSTEM,
    messages: [{ role: 'user', content: prompt }]
  };
  let lastError = null;
  for (let attempt = 1; attempt <= 3; attempt++) {
    let res;
    try {
      res = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01'
        },
        body: JSON.stringify(body)
      });
    } catch (err) {
      lastError = err;
      await sleep(1500 * attempt);
      continue;
    }
    if (res.status === 429 || res.status >= 500) {
      lastError = new Error(`llm ${res.status}`);
      await sleep(1500 * attempt);
      continue;
    }
    if (!res.ok) throw new Error(`llm ${res.status}: ${(await res.text()).slice(0, 200)}`);
    const data = await res.json();
    return (data.content || [])
      .filter((b) => b.type === 'text')
      .map((b) => b.text)
      .join('')
      .trim();
  }
  throw new Error(`llm retry exhausted: ${lastError && lastError.message}`);
}

function stripFences(text) {
  const m = String(text || '').match(/```(?:[a-z]*)\s*([\s\S]*?)```/);
  return (m ? m[1] : String(text || '')).trim();
}

module.exports = { llmAvailable, ask, stripFences, BASE_SYSTEM, DEFAULT_MODEL };
