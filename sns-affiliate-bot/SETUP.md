# SNS Affiliate Bot — ローカルPC セットアップガイド

## 前提条件

| 必須 | バージョン |
|------|-----------|
| Python | 3.11 以上 |
| pip | 24.0 以上 |
| Git | 任意 |
| ネットワーク | 制限なし（VPN 未接続推奨）|

---

## 1. リポジトリのクローンと依存インストール

```bash
git clone <リポジトリURL>
cd sns-affiliate-bot

pip install -r requirements.txt
```

---

## 2. .env ファイルの設定

```bash
cp .env.example .env
```

`.env` をエディタで開き、以下を設定します：

```env
ANTHROPIC_API_KEY=sk-ant-api03-...    # 必須
OPENAI_API_KEY=sk-proj-...            # 必須（DALL-E 3 画像生成）
```

### API キーの取得先

| キー | 取得元 | 無料枠 |
|------|--------|--------|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com/settings/keys | あり（$5）|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys | なし（プリペイド）|

---

## 3. OpenAI キーの確認（IP 制限のチェック）

> **重要:** このエラーが出た場合 → `PermissionDeniedError: Host not in allowlist`

OpenAI のキーに IP 制限が設定されているか確認してください：

1. https://platform.openai.com/api-keys を開く
2. 使用するキーをクリック
3. **Restrictions** タブ → **IP restrictions** を確認
4. 制限がある場合 → `No restriction` に変更して保存

> ほとんどの場合、新規作成したキーには制限なし。問題が出た場合のみ確認。

---

## 4. 動作確認テスト

```bash
python scripts/test_full_pipeline.py
```

### 期待される出力（全項目 PASS の場合）

```
[STEP 0] 環境チェック
  ✅ Python 3.11.x
  ✅ .env 読み込み完了
  ✅ ANTHROPIC_API_KEY: sk-ant-api0...
  ✅ OPENAI_API_KEY: sk-proj-L-O...
  ✅ anthropic インポートOK
  ✅ openai インポートOK
  ✅ edge_tts インポートOK
  ✅ imageio_ffmpeg インポートOK
  ✅ PIL インポートOK
  ✅ requests インポートOK
  ✅ NotoSansJP-Bold.otf (4547 KB)
  ✅ FFmpeg: /path/to/ffmpeg

[STEP 1] 台本生成テスト (Claude Haiku)
  ✅ 台本生成成功 (3.2秒)
  project_id  : beauty_tiktok_20260607_XXXXXX
  フック型    : shock_fact
  シーン数    : 6
  ...

[STEP 2] DALL-E 3 画像生成テスト
  ✅ DALL-E 3 成功 (8.1秒) — 1024×1024px

[STEP 3] Edge TTS 音声合成テスト
  ✅ Edge TTS 成功 (2.3秒) — 62,304 bytes
  音声長さ: 00:00:05.76

[STEP 4] テロップ焼き付けテスト
  ✅ テロップ焼き付け成功

[STEP 5] Ken Burns + 音声合成テスト
  ✅ Ken Burns シーン生成成功 (4.5秒)

[STEP 6] フルパイプライン — 2シーン完全動画生成
  ✅ 動画生成成功 (45.2秒)
  ファイル   : output/videos/test/full_pipeline_test.mp4
  サイズ     : 3,840 KB (3.7 MB)
  Duration: 00:00:12.xx  Video: h264, 1080x1920, 25fps

[STEP 7] 6ジャンル × 台本生成バッチテスト
  ✅ beauty      [tiktok ] 3.1s | フック: スキンケアで90%の人がやってる間...
  ✅ gadget      [reels  ] 2.8s | フック: このガジェット知らないのは損して...
  ...

============================================================
  テスト結果サマリー
============================================================
  ✅ PASS  環境チェック
  ✅ PASS  台本生成 (Claude Haiku)
  ✅ PASS  DALL-E 3 画像生成
  ✅ PASS  Edge TTS 音声合成
  ✅ PASS  Pillow テロップ
  ✅ PASS  FFmpeg Ken Burns
  ✅ PASS  フルパイプライン
  ✅ PASS  6ジャンルバッチ
```

---

## 5. 基本的な使い方

### 台本を1本生成する

```bash
# 美容ジャンル × TikTok
python main.py script beauty tiktok

# ガジェット × YouTube Shorts × 高品質モード
python main.py script gadget shorts 1 high

# 婚活 × Instagram Reels × 7本一括
python main.py script marriage reels 7
```

### 台本 JSON から動画を生成する

```bash
python main.py generate video output/scripts/beauty/tiktok/beauty_tiktok_XXXXXXX.json
```

### デモ動画を生成する（台本不要）

```bash
python main.py generate video --demo
```

---

## 6. 生成ジャンル一覧

| ジャンル ID | 表示名 | 推奨プラットフォーム |
|------------|--------|---------------------|
| `beauty` | 美容・コスメ | `reels`, `tiktok` |
| `gadget` | ガジェット・テック | `tiktok`, `shorts` |
| `lifehack` | ライフハック・節約 | `tiktok`, `shorts`, `reels` |
| `marriage` | 婚活・恋愛 | `tiktok`, `reels` |
| `sidehustle` | 副業・マネー | `tiktok`, `shorts` |
| `diet` | ダイエット・健康 | `reels`, `tiktok` |

---

## 7. 出力ファイル構造

```
sns-affiliate-bot/
├── output/
│   ├── scripts/          # 生成済み台本 JSON
│   │   └── {genre}/{platform}/{project_id}.json
│   └── videos/           # 生成済み MP4
│       └── {project_id}.mp4
```

---

## 8. よくあるエラーと対処法

### `PermissionDeniedError: Host not in allowlist`
→ OpenAI キーの IP 制限。「3. OpenAI キーの確認」を参照。  
→ または VPN/プロキシ環境での実行。VPN を OFF にして再試行。

### `SSLCertVerificationError: certificate verify failed`
→ 企業プロキシが SSL を傍受している。Edge TTS は利用不可。  
→ 対処: VPN OFF、または社内ネットワーク外で実行。

### `OSError: unknown file format` (フォント)
→ `assets/fonts/NotoSansJP-Bold.otf` が壊れている。  
→ 以下で再ダウンロード:
```bash
python -c "
import urllib.request
urllib.request.urlretrieve(
    'https://github.com/googlefonts/noto-cjk/raw/main/Sans/SubsetOTF/JP/NotoSansJP-Bold.otf',
    'assets/fonts/NotoSansJP-Bold.otf'
)
print('ダウンロード完了')
"
```

### `ModuleNotFoundError`
→ `pip install -r requirements.txt` を再実行。

---

## 9. コスト目安（1動画あたり）

| コンポーネント | モデル | 推定コスト |
|--------------|--------|-----------|
| 台本生成（fast） | Claude Haiku | ~$0.002 |
| 台本生成（high） | Claude Sonnet | ~$0.015 |
| 画像生成（6シーン）| DALL-E 3 standard | ~$0.24 |
| 音声合成（Edge TTS）| 無料 | $0 |
| **合計（fast モード）** | — | **~$0.24/本** |

> DALL-E 3 は `1024×1792`（縦型）×シーン数で課金。  
> 1シーン = $0.04 (standard) / $0.08 (HD)
