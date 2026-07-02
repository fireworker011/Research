'use strict';

/**
 * Claude API クライアント（依存ライブラリなし・fetch使用）
 */

const API_URL = 'https://api.anthropic.com/v1/messages';
const DEFAULT_MODEL = process.env.CLAUDE_MODEL || 'claude-sonnet-5';

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Claude にプロンプトを送信してテキストを返す。
 * 429 / 5xx は指数バックオフで最大3回リトライ。
 */
async function askClaude(prompt, { maxTokens = 8192, system = null, model = DEFAULT_MODEL } = {}) {
  const apiKey = process.env.ANTHROPIC_API_KEY || process.env.CLAUDE_API_KEY;
  if (!apiKey) {
    throw new Error('ANTHROPIC_API_KEY（または CLAUDE_API_KEY）が設定されていません');
  }

  const body = {
    model,
    max_tokens: maxTokens,
    messages: [{ role: 'user', content: prompt }]
  };
  if (system) body.system = system;

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
      await sleep(2000 * attempt);
      continue;
    }

    if (res.status === 429 || res.status >= 500) {
      lastError = new Error(`Claude API ${res.status}`);
      await sleep(2000 * attempt);
      continue;
    }
    if (!res.ok) {
      throw new Error(`Claude API ${res.status}: ${await res.text()}`);
    }

    const data = await res.json();
    if (data.stop_reason === 'max_tokens') {
      console.warn('⚠️  応答が max_tokens で打ち切られました。テンプレ数を減らすか maxTokens を増やしてください');
    }
    return data.content
      .filter((block) => block.type === 'text')
      .map((block) => block.text)
      .join('');
  }
  throw new Error(`Claude API: リトライ上限に達しました（${lastError && lastError.message}）`);
}

/**
 * Claude の応答から JSON を抽出してパースする。
 * コードフェンスや前置きテキストが混ざっていても対応。
 */
function extractJSON(text) {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fenced) text = fenced[1];

  const start = text.search(/[[{]/);
  if (start === -1) throw new Error('応答に JSON が見つかりません');

  // 末尾からパース可能な位置を探す（後置きテキスト対策）
  for (let end = text.length; end > start; end--) {
    const candidate = text.slice(start, end).trim();
    if (!candidate.endsWith('}') && !candidate.endsWith(']')) continue;
    try {
      return JSON.parse(candidate);
    } catch (_) {
      // 続行して短い候補を試す
    }
  }
  throw new Error('JSON のパースに失敗しました');
}

module.exports = { askClaude, extractJSON, sleep };
