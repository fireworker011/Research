// サービスアカウント JSON から OAuth2 アクセストークンを取る（依存ライブラリなし・RS256 自前署名）
import crypto from 'node:crypto';
import fs from 'node:fs';

const b64url = (input) =>
  Buffer.from(input).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

export async function accessTokenFromServiceAccount(credentialsPath, scope) {
  const sa = JSON.parse(fs.readFileSync(credentialsPath, 'utf8'));
  if (!sa.client_email || !sa.private_key) {
    throw new Error(`${credentialsPath}: client_email / private_key がありません`);
  }

  const now = Math.floor(Date.now() / 1000);
  const header = b64url(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
  const claim = b64url(
    JSON.stringify({
      iss: sa.client_email,
      scope,
      aud: 'https://oauth2.googleapis.com/token',
      iat: now,
      exp: now + 3600,
    })
  );

  const signer = crypto.createSign('RSA-SHA256');
  signer.update(`${header}.${claim}`);
  const signature = b64url(signer.sign(sa.private_key));
  const jwt = `${header}.${claim}.${signature}`;

  const res = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
      assertion: jwt,
    }),
  });

  if (!res.ok) throw new Error(`トークン取得に失敗 (${res.status}): ${await res.text()}`);
  return (await res.json()).access_token;
}
