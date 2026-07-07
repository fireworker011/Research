# スマホだけで運用するためのセットアップ&運用ガイド

## 毎回の運用フロー(スマホのみ・PC不要)

```
① Claude(このチャット)に「次の動画作って」と言う
     → 私が市場リサーチ→台本JSON作成→リポジトリにプッシュ→Actionsを起動
② 10〜20分後、YouTube Studioアプリに「非公開動画」として届く
③ スマホで動画を確認 → 問題なければアプリで「公開」に切り替え
```

あなたのタップ数: **実質3タップ**(確認→公開)。

---

## 初回セットアップ(スマホブラウザで30分・1回だけ)

### 手順1: xAI APIキー
1. スマホブラウザで https://console.x.ai を開く
2. Xアカウントでログイン → API Keys → Create Key
3. キーをコピー(あとで手順4で使う)

### 手順2: Google OAuth クライアント作成
1. スマホブラウザで https://console.cloud.google.com を開く(PC表示推奨)
2. 新規プロジェクト作成 → 「APIとサービス」→「ライブラリ」→ YouTube Data API v3 を有効化
3. 「OAuth同意画面」→ 外部 → アプリ名など入力 → テストユーザーに自分のGmailを追加
4. 「認証情報」→「認証情報を作成」→「OAuthクライアントID」→ 種類は「ウェブアプリケーション」
   - 承認済みリダイレクトURIに `https://developers.google.com/oauthplayground` を追加
5. **クライアントID** と **クライアントシークレット** をコピー

### 手順3: リフレッシュトークン取得(OAuth Playground)
1. スマホブラウザで https://developers.google.com/oauthplayground を開く
2. 右上の⚙ → 「Use your own OAuth credentials」にチェック → 手順2のID/シークレットを入力
3. 左のリストで `https://www.googleapis.com/auth/youtube.upload` を入力して Authorize
4. 「みくこんかつ」のGoogleアカウントでログイン → 許可
5. 「Exchange authorization code for tokens」→ **Refresh token** をコピー

### 手順4: GitHub Secrets 登録
1. スマホブラウザで https://github.com/fireworker011/Research/settings/secrets/actions を開く
2. 「New repository secret」で以下4つを登録:

| Name | 値 |
|------|-----|
| `XAI_API_KEY` | 手順1のキー |
| `YT_CLIENT_ID` | 手順2のクライアントID |
| `YT_CLIENT_SECRET` | 手順2のシークレット |
| `YT_REFRESH_TOKEN` | 手順3のリフレッシュトークン |

### 手順5: 動作テスト
Claudeに「テスト実行して」と言う(私がActionsを起動して結果を報告します)。
またはGitHubアプリ/ブラウザから: リポジトリ → Actions → 「婚活Shorts 動画生成→YouTube投稿」→ Run workflow。

---

## トラブル時

- 生成失敗 → Claudeに「Actionsのログ見て」と言えば私が原因を調べて直します
- 完成動画はActionsのアーティファクトにも7日間保存(投稿失敗時の救済用)
- コスト目安: 1本あたり約550円(Grok API従量課金) + GitHub Actions無料枠内
