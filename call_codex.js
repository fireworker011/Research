const fetch = require('node-fetch');

async function callCodex(prompt) {
  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`
    },
    body: JSON.stringify({
      model: 'gpt-4o-mini',
      messages: [
        {
          role: 'system',
          content: 'You are an expert JavaScript developer specialising in RPG Maker MZ plugins. Output only raw JavaScript code, no markdown fences.'
        },
        {
          role: 'user',
          content: prompt
        }
      ],
      max_tokens: 500,
      temperature: 0.5
    })
  });

  const data = await response.json();

  if (data.error) {
    throw new Error(`API error: ${data.error.message}`);
  }

  return data.choices[0].message.content;
}

// RPGツクール MZ 向けのプロンプト
const prompt = `
// RPGツクール MZ プラグイン
// ユーザーが入力値を受け取るウィンドウを作成してください
window.MY_PLUGIN = {};
`;

callCodex(prompt)
  .then(code => {
    console.log('=== Codex が生成したコード ===');
    console.log(code);
  })
  .catch(err => {
    console.error('エラー:', err.message);
    process.exit(1);
  });
