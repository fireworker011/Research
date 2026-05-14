const fetch = require('node-fetch');

async function callCodex(prompt) {
  const response = await fetch('https://api.openai.com/v1/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`
    },
    body: JSON.stringify({
      model: 'code-davinci-002', // または code-davinci-003
      prompt: prompt,
      max_tokens: 500,
      temperature: 0.5
    })
  });

  const data = await response.json();
  return data.choices[0].text;
}

// RPGツクール向けのプロンプト例
const prompt = `
// RPGツクール MZ プラグイン
// ユーザーが入力値を受け取るウィンドウを作成してください
window.MY_PLUGIN = {};
`;

callCodex(prompt).then(code => {
  console.log('=== Codex が生成したコード ===');
  console.log(code);
});
