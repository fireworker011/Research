# SNS Affiliate Bot - スキルマニュアル

このファイルはClaude Codeへの業務マニュアルです。
「〇〇スキル使って」と指示するだけで、以下の処理が自動実行されます。

---

## 利用可能なスキル一覧

| スキル名 | コマンド | 説明 |
|----------|----------|------|
| Threads投稿 | `python main.py post threads career` | 転職ジャンルをThreadsに投稿 |
| YouTube生成 | `python main.py post youtube career` | 動画生成→YouTube Shortsアップロード |
| コンテンツ一括生成 | `python main.py generate threads career 7` | 7日分のThreadsコンテンツを生成 |
| 台本一括生成 | `python main.py generate youtube career 7` | 7本分のYouTube台本を生成 |
| スケジューラ起動 | `python main.py run career` | 完全自動化モード（常時実行） |
| 環境チェック | `python main.py check` | API接続・設定の確認 |

---

## セットアップ手順

### ステップ1: 依存パッケージのインストール

```bash
cd sns-affiliate-bot
pip install -r requirements.txt
```

### ステップ2: .env ファイルを作成

```bash
cp .env.example .env
```

---

## Threads API セットアップ

### 必要なもの
- Facebookアカウント（新規作成でOK）
- Facebookページ
- Instagramプロアカウント（設定済み）
- Meta for Developers アプリ

### 手順

**①Facebookアカウントを作成**
https://www.facebook.com/r.php で新規登録

**②Facebookページを作成**
https://www.facebook.com/pages/create

**③Meta for Developers でアプリを作成**
1. https://developers.facebook.com にアクセス
2. 「マイアプリ」→「アプリを作成」
3. タイプ: 「ビジネス」を選択
4. アプリ名: 任意（例: sns-affiliate-bot）

**④Threads APIを製品として追加**
1. アプリダッシュボード → 「ユースケースを追加」
2. 「Threads API」を選択して「設定」

**⑤アクセストークンの取得**
1. 「ツール」→「Graph APIエクスプローラー」
2. 右上でアプリを選択
3. 権限を追加: `threads_basic`, `threads_content_publish`
4. 「ユーザーアクセストークンを生成」をクリック
5. コピーして .env の `THREADS_CAREER_ACCESS_TOKEN` に貼り付け

**⑥Threads User IDの取得**
Graph APIエクスプローラーで以下を実行:
```
GET me?fields=id,username
```
表示された `id` を .env の `THREADS_CAREER_USER_ID` に設定

---

## YouTube Data API セットアップ

### 手順

**①Google Cloud Console でプロジェクトを作成**
1. https://console.cloud.google.com にアクセス
2. 「プロジェクトを作成」→ 名前: sns-affiliate-bot

**②YouTube Data API v3 を有効化**
1. 「APIとサービス」→「APIとサービスを有効化」
2. 「YouTube Data API v3」を検索して有効化

**③OAuth 2.0 認証情報を作成**
1. 「認証情報」→「認証情報を作成」→「OAuthクライアントID」
2. アプリの種類: 「デスクトップアプリ」
3. 名前: sns-affiliate-bot
4. 「作成」→「JSONをダウンロード」
5. ダウンロードしたファイルを以下に配置:
   `config/credentials/youtube_career.json`

**④初回認証（ブラウザが自動で開きます）**
```bash
python main.py post youtube career
```
ブラウザでGoogleアカウントにログインして許可→以降は自動

---

## Pexels API セットアップ（5分で完了・無料）

1. https://www.pexels.com/api/ にアクセス
2. 無料登録して「Your API Key」をコピー
3. .env の `PEXELS_API_KEY` に貼り付け

---

## A8.net アフィリエイト設定

1. https://www.a8.net に登録
2. 提携したい案件を承認申請（例: プログラミングスクール）
3. 承認後、各案件のアフィリエイトリンクをコピー
4. `config/niches/career.json` の `products` セクションに追加:
   ```json
   {
     "id": "your_product_id",
     "name": "商品名",
     "url_template": "https://px.a8.net/...",
     "cta": "無料体験はプロフのリンクから"
   }
   ```

---

## VOICEVOX インストール（Windows/Mac）

1. https://voicevox.hiroshiba.jp/ からダウンロード
2. インストールしてアプリを起動
3. バックグラウンドで起動中（localhost:50021）
4. `python main.py check` で確認

---

## 新しいジャンルの追加方法（5ジャンルへの拡張）

1. `config/niches/beauty.json` を `career.json` を参考に編集
2. Threads/YouTube アカウントを作成してAPIキーを取得
3. `.env` に以下を追加:
   ```
   THREADS_BEAUTY_USER_ID=...
   THREADS_BEAUTY_ACCESS_TOKEN=...
   YOUTUBE_BEAUTY_CHANNEL_ID=...
   ```
4. `config/credentials/youtube_beauty.json` を配置
5. `python main.py post threads beauty` でテスト

---

## AI プロバイダーの切り替え（Grok / OpenAI Codex）

現在は追加コストゼロの `template` モードで動作しています。
高品質なコンテンツ生成に切り替えたい場合:

**Grok に切り替える場合:**
```env
AI_PROVIDER=grok
XAI_API_KEY=your_xai_api_key_here
```

**OpenAI に切り替える場合:**
```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
```

**Claude API に切り替える場合:**
```env
AI_PROVIDER=claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

コードの変更は不要です。`.env` の値を変えるだけで自動的に切り替わります。

---

## Instagram 自動投稿（将来追加）

Threads + YouTube が安定した後に追加予定。
`platforms/instagram/` ディレクトリに実装を追加します。
Meta Graph API を使用（Threadsと同じアクセストークンで対応可能）。
