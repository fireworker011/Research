# SNS アフィリエイトBot — 共通設定

## プロジェクト概要
YouTube Shorts でアフィリエイト収益を自動化するシステム。
ジャンルごとにショートドラマ動画を制作・投稿する。

## 作業ディレクトリ（PC）
```
C:\Users\ys734\Desktop\Research\sns-affiliate-bot
```

## ジャンル一覧
| ジャンル | フォルダ | ステータス |
|---------|---------|----------|
| ペット×見守りカメラ | genres/pet/ | 稼働中（動画6本投稿済） |
| 美容×コスメ | genres/beauty/ | 未着手 |
| 節約×クレカ | genres/finance/ | 未着手 |
| ダイエット×サプリ | genres/diet/ | 未着手 |
| 婚活×マッチングアプリ | genres/marriage/ | 未着手 |
| 副業×スキル | genres/side_job/ | 未着手 |
| 育児×便利グッズ | genres/parenting/ | 未着手 |
| 旅行×予約サイト | genres/travel/ | 未着手 |
| 転職×エージェント | genres/career/ | 未着手 |
| 食×デリバリー | genres/food/ | 未着手 |

ジャンルの詳細は各フォルダの CLAUDE.md を参照。

## 共通技術スタック
- 画像生成: gpt-image-1（size=1024x1536, quality=high, b64_json）
- 動画生成: Grok Agent（デフォルト6秒, 縦型9:16）※尺指定不要、assemble_grok.pyが自動フィット
- 音声: Voicevox 波音リツ（SPEAKER_ID=9, SPEED=0.88, PITCH=-0.03, INTONATION=1.4）
- 動画編集: FFmpeg（trim/resize/concat/ASS字幕焼き込み）
- 投稿: YouTube Data API v3（OAuth2.0, token.pickle）
- 競合リサーチ: monitor_and_research.py

## 共通制作パイプライン
1. `python generate_images_[genre][num].py` → 画像7枚生成
2. Grok Agentで動画化（デフォルト6秒×7本、尺指定不要）
3. Voicevox起動 → `python make_audio_[genre][num].py`
4. `assemble_[genre][num].py` → 動画完成
5. YouTube Shortsアップロード
6. コメント欄にアフィリンクをピン固定
7. `python monitor_and_research.py` → 競合リサーチ

## 共通Gitメモ
- ブランチ: `claude/wizardly-mendel-nCgBE`
- マージ未完了エラーが出たら: `git commit --no-edit` → `git pull`
- Vimが開いたら: `:wq` でEnter

## 環境ファイル
- `.env`: OPENAI_API_KEY
- `client_secret.json`: Google OAuth（Downloadsからコピー済）
- `token.pickle`: YouTube認証トークン（自動生成）
