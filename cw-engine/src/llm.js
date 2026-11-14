'use strict';

const BASE_SYSTEM = [
  'あなたはクラウドワークスで受注した仕事の下書きと完成品を作る作業者です。日本語で書きます。',
  '事実は与えられた素材・募集文・事実カードにあるものだけを使い、無いものは【要確認】と書きます。',
  '実績・経験・数字・固有名詞・体験談を発明しません。URL は素材にあるもの以外書きません。',
  '「私はAI」「AIとして」などのメタ発言を書きません。指示された形式以外の前置き・後置きを書きません。'
].join('\n');

function stripFences(text) {
  const matched = String(text || '').match(/```(?:[a-z]*)\s*([\s\S]*?)```/);
  return (matched ? matched[1] : String(text || '')).trim();
}

module.exports = { stripFences, BASE_SYSTEM };
