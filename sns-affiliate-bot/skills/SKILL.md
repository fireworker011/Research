# SNS Affiliate Bot - スキルマニュアル

このファイルはClaude Codeへの業務マニュアルです。
「〇〇スキル使って」と指示するだけで、以下の処理が自動実行されます。

---

## 利用可能なスキル一覧

| スキル名 | コマンド | 説明 |
|----------|----------|------|
| Threads投稿 | `python main.py post threads career` | 転職ジャンルをThreadsに1投稿（確認あり） |
| YouTube生成 | `python main.py post youtube career` | 動画生成→YouTube Shortsアップロード（確認あり） |
| コンテンツ一括生成 | `python main.py generate threads career 7` | 7日分のThreadsコンテンツをキューに保存 |
| 台本一括生成 | `python main.py generate youtube career 7` | 7本分のYouTube台本をキューに保存 |
| スケジューラ起動 | `python main.py run career` | 完全自動化モード（常時実行・手動停止はCtrl+C） |
| 環境チェック | `python main.py check` | API接続・設定の確認 |

---

## ゼロから動かすまでの全手順（Windows）

### ステップ0: リポジトリをローカルに取得

```bash
git clone https://github.com/fireworker011/research.git
cd research/sns-affiliate-bot
pip install -r requirements.txt
cp .env.example .env
```

---

### ステップ1: Threads API セットアップ

#### 1-1. Meta for Developers でアプリを準備

1. https://developers.facebook.com → 「sns-affiliate-bot」アプリを開く
2. 左メニュー「アプリの役割」→「役割」→「テスター」タブ
   → 「テスターを追加」→ 自分のInstagramユーザー名を入力して追加
3. **Instagramアプリ**で通知を確認 → テスター招待を「承認」
4. アプリダッシュボードに戻る → 「ユースケースを追加」
   → 「Threads APIへのアクセス」→「設定」
   → permissions で以下を有効化:
   - `threads_basic` ✅
   - `threads_content_publish` ✅

#### 1-2. アクセストークンを取得

1. 「ツール」→「Graph APIエクスプローラー」を開く
2. 右上のアプリ選択で「**sns-affiliate-bot**」を選択
3. 「ユーザーまたはページ」で自分のアカウントを選択
4. permissions に `threads_basic`, `threads_content_publish` を追加
5. 「アクセストークンを生成」をクリック → コピー

#### 1-3. スクリプトでトークンを保存

```bash
python setup/threads_token.py setup
# → コピーしたトークンを貼り付けると自動で長期トークン（60日）に変換して .env に保存
```

#### 1-4. トークン自動確認（毎週）

Windowsタスクスケジューラに登録後（ステップ4参照）、
毎週月曜に残り日数を自動確認します。

手動確認:
```bash
python setup/threads_token.py check
```

トークン更新（期限が近くなったら）:
```bash
python setup/threads_token.py refresh
```

---

### ステップ2: YouTube Data API セットアップ

#### 2-1. Google Cloud Console での作業

1. https://console.cloud.google.com にアクセス
2. 上部「プロジェクトを選択」→「新しいプロジェクト」
   - プロジェクト名: `sns-affiliate-bot` → 作成
3. 「APIとサービス」→「ライブラリ」→「YouTube Data API v3」を検索 → 有効にする
4. 「APIとサービス」→「OAuth同意画面」
   - ユーザーの種類: **外部** → 作成
   - アプリ名: `sns-affiliate-bot`
   - サポートメール: 自分のGmailアドレス
   - 「スコープを追加」→ `YouTube Data API v3` の `youtube.upload` を追加
   - テストユーザー → 自分のGoogleアカウントを追加
   → 保存して次へ（全項目完了まで）
5. 「認証情報」→「認証情報を作成」→「OAuthクライアントID」
   - アプリの種類: **デスクトップアプリ**
   - 名前: `sns-affiliate-bot-desktop` → 作成
6. 「JSONをダウンロード」ボタンをクリック

#### 2-2. ファイルを配置

ダウンロードしたJSONファイルを以下にコピー（リネームして配置）:
```
sns-affiliate-bot/config/credentials/youtube_career.json
```

#### 2-3. 初回認証（ブラウザが自動で開きます）

```bash
python setup/youtube_oauth.py setup career
# → ブラウザが開く → Googleアカウントでログイン → 許可
# → チャンネルIDが自動で .env に保存される
```

---

### ステップ3: その他の設定

#### Pexels API（無料・動画生成に必要）

1. https://www.pexels.com/api/ → 無料登録
2. 「Your API Key」をコピー
3. `.env` の `PEXELS_API_KEY=` に貼り付け

#### VOICEVOX（動画のナレーション生成に必要）

1. https://voicevox.hiroshiba.jp/ からダウンロード・インストール
2. VOICEVOXアプリを起動（バックグラウンドで動く）
3. `python main.py check` で「VOICEVOX サーバー: 起動中」を確認

#### A8.net アフィリエイトリンク設定

1. https://www.a8.net に登録
2. 転職・スキルアップ系の案件に提携申請（例: プログラミングスクール、転職エージェント）
3. 承認後、アフィリエイトリンクをコピー
4. `config/niches/career.json` の `products` にリンクを追記:
```json
{
  "id": "your_product_id",
  "name": "商品名",
  "url_template": "https://px.a8.net/svt/ejp?a8mat=XXXXXX",
  "cta": "無料登録はプロフのリンクから"
}
```

---

### ステップ4: 動作確認

```bash
# 全設定チェック
python main.py check

# Threads にテスト投稿（確認プロンプトあり）
python main.py post threads career

# YouTube Shorts テスト（VOICEVOXを先に起動しておく）
python main.py post youtube career
```

---

### ステップ5: Windowsタスクスケジューラに登録（完全自動化）

管理者権限でコマンドプロンプトを開いて実行:
```bash
python scheduler/windows_task.py install
```

登録後:
- 毎日 08:00 にスケジューラが自動起動
- 毎週月曜 09:00 にThreadsトークンの残日数を確認

登録状態の確認:
```bash
python scheduler/windows_task.py status
```

タスクを削除する場合:
```bash
python scheduler/windows_task.py uninstall
```

---

## AI プロバイダーの切り替え（コンテンツ品質UP）

現在は追加コストゼロの `template` モードで動作しています。
高品質なコンテンツ生成に切り替えたい場合は `.env` を編集するだけです。

**Claude API（高品質・日本語に強い）:**
```env
AI_PROVIDER=claude
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

**Grok（X/Threadsのトレンドに強い）:**
```env
AI_PROVIDER=grok
XAI_API_KEY=your_xai_api_key_here
```

コードの変更は不要。`.env` の値を変えるだけで自動的に切り替わります。

---

## 新しいジャンルの追加方法

1. Threads・YouTubeアカウントを別途作成してAPIキーを取得
2. `.env` に追加:
   ```
   THREADS_BEAUTY_USER_ID=...
   THREADS_BEAUTY_ACCESS_TOKEN=...
   ```
3. YouTube認証:
   ```bash
   python setup/youtube_oauth.py setup beauty
   ```
4. テスト:
   ```bash
   python main.py post threads beauty
   ```

---

## Instagram 自動投稿（将来追加）

Threads + YouTube が安定した後に追加予定。
`platforms/instagram/` ディレクトリに実装を追加します。
Threadsと同じMeta Graph APIを使用するため、アクセストークンの共有が可能。

---

## トラブルシューティング

| エラー | 原因 | 対処 |
|--------|------|------|
| `THREADS_CAREER_ACCESS_TOKEN が設定されていません` | .env 未設定 | `python setup/threads_token.py setup` を実行 |
| `トークン交換失敗` | META_APP_SECRET が間違い | Meta for Developers → 基本設定 で確認 |
| `コンテナ処理エラー` | 動画URLが無効 | 公開アクセス可能なURLを使用 |
| `VOICEVOX が起動していません` | アプリ未起動 | VOICEVOXアプリを起動してから再実行 |
| `youtube_career.json が見つからない` | ファイル未配置 | `setup/youtube_oauth.py setup career` の手順2-2を確認 |
