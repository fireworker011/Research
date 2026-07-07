# スマホだけで運用するためのセットアップ&運用ガイド(完全無料版)

## 毎回の運用フロー(スマホのみ・PC不要)

```
① Claude(このチャット)に「次の動画のプロンプト作って」と言う
     → 私が市場リサーチ→台本作成→Grokアプリ用プロンプトMarkdownを作成
② あなたがGrokアプリ(無料枠)で画像→動画をシーンごとに生成
③ できた動画ファイルをこのチャットに送る(私がリポジトリに配置)
④ 「合成して投稿して」と言う → 私がActionsを起動
⑤ 10分後、YouTube Studioアプリに「非公開動画」として届く
⑥ スマホで動画を確認 → 問題なければアプリで「公開」に切り替え
```

課金が発生する箇所は**ありません**(Grokアプリの無料枠・Edge TTS・FFmpeg・
YouTube API・GitHub Actionsはすべて無料)。

---

## 初回セットアップ(スマホブラウザで15分・1回だけ)

xAI APIキーの取得は不要になりました。YouTube投稿の認証だけ行います。

### 手順1: Google OAuth クライアント作成
1. スマホブラウザで https://console.cloud.google.com を開く(PC表示推奨)
2. 新規プロジェクト作成 → 「APIとサービス」→「ライブラリ」→ YouTube Data API v3 を有効化
3. 「OAuth同意画面」→ 外部 → アプリ名など入力 → テストユーザーに自分のGmailを追加
4. 「認証情報」→「認証情報を作成」→「OAuthクライアントID」→ 種類は「ウェブアプリケーション」
   - 承認済みリダイレクトURIに `https://developers.google.com/oauthplayground` を追加
5. **クライアントID** と **クライアントシークレット** をコピー

### 手順2: リフレッシュトークン取得(OAuth Playground)
1. スマホブラウザで https://developers.google.com/oauthplayground を開く
2. 右上の⚙ → 「Use your own OAuth credentials」にチェック → 手順1のID/シークレットを入力
3. 左のリストで `https://www.googleapis.com/auth/youtube.upload` を入力して Authorize
4. 「みくこんかつ」のGoogleアカウントでログイン → 許可
5. 「Exchange authorization code for tokens」→ **Refresh token** をコピー

### 手順3: GitHub Secrets 登録
1. スマホブラウザで https://github.com/fireworker011/Research/settings/secrets/actions を開く
2. 「New repository secret」で以下3つを登録:

| Name | 値 |
|------|-----|
| `YT_CLIENT_ID` | 手順1のクライアントID |
| `YT_CLIENT_SECRET` | 手順1のシークレット |
| `YT_REFRESH_TOKEN` | 手順2のリフレッシュトークン |

### 手順4: 動作テスト
Grokで1シーン分だけ動画を作ってこのチャットに送り、
「テスト実行して」と言ってください。私がActionsを起動して結果を報告します。

---

## トラブル時

- 生成失敗 → Claudeに「Actionsのログ見て」と言えば私が原因を調べて直します
- 完成動画はActionsのアーティファクトにも7日間保存(投稿失敗時の救済用)
- コスト: **完全無料**(Grokアプリの無料枠を使う分だけ、生成回数に上限がある場合あり)
