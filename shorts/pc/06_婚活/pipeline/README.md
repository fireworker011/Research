# 婚活Shorts 完全自動パイプライン

CapCutの手作業を置き換える。台本JSONを渡すと以下を全自動実行:

```
台本JSON → ①Grok画像生成 → ②Grok動画化 → ③TTSナレーション
        → ④FFmpeg合成(尺自動調整) → ⑤YouTube自動投稿
```

**手動なのは「台本を選ぶ」と「投稿前の1回確認」だけ**(確認スキップも可)。

## 初回セットアップ(Windows)

```cmd
cd shorts\pc\06_婚活\pipeline
pip install -r requirements.txt
copy .env.example .env
```

1. **FFmpeg**: https://ffmpeg.org からDLしてPATHを通す(`ffmpeg -version`で確認)
2. **xAI APIキー**: https://console.x.ai で発行 → `.env` の `XAI_API_KEY=` に貼る
   - 料金目安: 画像$0.02/枚 × 7 + 動画$0.05/秒 × 70秒 ≒ **1本あたり約$3.6(550円)**
3. **YouTube認証**(初回のみ):
   - Google Cloud Console → YouTube Data API v3 有効化 → OAuthクライアント(デスクトップ)作成 → JSONをDL
   - `python upload.py auth client_secrets.json` → ブラウザで「みくこんかつ」のGoogleアカウントでログイン

## 使い方

```cmd
# ① 動画生成のみ(推奨: 投稿前に1回目視確認)
python run.py scripts_json/003_ng5sen.json

# ② 確認OKなら投稿
python run.py scripts_json/003_ng5sen.json --upload-only

# ③ 確認もスキップして全自動(品質が安定してきたら)
python run.py scripts_json/003_ng5sen.json --upload
```

生成物は `output/<project_id>/` に残る。画像・動画は再実行時にキャッシュ利用
(気に入らないシーンだけファイル削除して再実行すればそのシーンだけ再生成)。

## 台本JSONの作り方

`scripts_json/003_ng5sen.json` がテンプレ。毎週のPDCAレビュー時に
Claude Codeに「次の台本JSONを作って」と言えば市場リサーチ込みで生成される。

## 品質を落とさないための運用ルール

- `--upload` は最初の3本では使わない。①→目視→②の2段階で
- キャラ一貫性: `character` フィールドが全シーンのプロンプトに自動前置される
- シーンの動画が音声より短い場合は自動スロー再生で尺を合わせる(破綻したら
  そのシーンの `duration` を増やして再生成)
- Grok APIのエンドポイント/モデル名が変わったら `.env` で上書き

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| `XAI_API_KEY が未設定` | `.env` にキーを設定 |
| FFmpeg失敗 | `ffmpeg -version` でPATH確認 |
| 404/モデル名エラー | docs.x.ai で最新モデル名を確認し `.env` で上書き |
| YouTube 401 | `python upload.py auth client_secrets.json` で再認証 |
