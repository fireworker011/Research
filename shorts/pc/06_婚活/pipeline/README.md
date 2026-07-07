# 婚活Shorts 自動パイプライン(完全無料版)

課金が発生する箇所(Grok Imagine API)を廃止。画像・動画生成は
**Grokアプリ/Web版を手動操作(無料枠)**で行い、それ以外(音声・合成・投稿)を自動化する。

```
①台本JSON → プロンプト書き出し(無料・自動)
②あなたがGrokアプリで画像→動画生成(無料枠・手動)
③生成動画を input/ フォルダに配置
④TTSナレーション → FFmpeg合成 → YouTube投稿(すべて無料・自動)
```

**課金が発生するのは今のところゼロ**(FFmpeg・Edge TTS・YouTube API・GitHub Actionsは無料)。

## 使い方

### ① Grok用プロンプトを書き出す
```cmd
cd shorts\pc\06_婚活\pipeline
python make_prompts.py scripts_json/003_ng5sen.json
```
→ `prompts/003_ng5sen_grok_prompts.md` ができる。これをスマホで開く。

### ② Grokアプリで生成
Markdown内の「①画像プロンプト」をGrokアプリに貼って画像生成 →
気に入った画像を選んで「動画化」→「②動画プロンプト」を貼って生成。
シーン1〜7を順番に。

### ③ 生成した動画を配置
`pipeline/input/konkatsu_003_ng5sen/scene_01.mp4` 〜 `scene_07.mp4` に保存。
スマホから直接置けない場合は、**Claudeとのチャットに動画ファイルを送ってください**。
私が受け取ってこのフォルダに配置し、続きを実行します。

### ④ 合成 → 確認 → 投稿
```cmd
# 合成のみ(まず目視確認)
python run.py scripts_json/003_ng5sen.json

# 確認OKなら非公開でYouTubeに投稿
python run.py scripts_json/003_ng5sen.json --upload-only

# 即公開したい場合
python run.py scripts_json/003_ng5sen.json --upload-only --public
```

## 初回セットアップ(Windows / 無料のみ)

```cmd
cd shorts\pc\06_婚活\pipeline
pip install -r requirements.txt
```

1. **FFmpeg**(無料): https://ffmpeg.org からDLしてPATHを通す
2. **YouTube認証**(無料・初回のみ): `SETUP_MOBILE.md` の「手順2・3・4」参照
   (xAI APIキーの手順は不要になったのでスキップ)

## スマホ運用(Claude経由・推奨)

PCを開かず、Claudeとのチャットだけで完結させたい場合:

1. 「次の動画のプロンプト作って」→ 台本+プロンプトMarkdownを私が作成
2. あなたがGrokアプリで画像→動画を生成
3. できた動画ファイルをこのチャットに送る
4. 「合成して投稿して」と言えば、私がGitHub Actions経由で
   音声生成・合成・YouTube非公開投稿まで実行
5. スマホのYouTube Studioアプリで確認→公開

## 品質を落とさないための運用ルール

- キャラ一貫性: プロンプト冒頭の `character` 設定は毎回同じ文言をGrokに貼る
- シーン動画が音声より短い/長い場合は `assemble.py` が自動で尺を合わせる
- 気に入らないシーンだけ `input/<project_id>/scene_XX.mp4` を差し替えて再実行すればOK

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| `シーン動画が見つかりません` | `input/<project_id>/scene_XX.mp4` の配置を確認 |
| FFmpeg失敗 | `ffmpeg -version` でPATH確認 |
| YouTube 401 | `python upload.py auth client_secrets.json` で再認証 |
