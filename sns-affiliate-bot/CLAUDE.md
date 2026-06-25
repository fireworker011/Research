# ペット×見守りカメラ YouTube Shorts アフィリエイトプロジェクト

## チャンネル情報
- チャンネル名: ペットと暮らす小さな物語
- チャンネルID: UC65pP_901i2ERosuStSAIVw
- ジャンル: 保護猫×ペットカメラ ショートドラマ
- ターゲット: 猫を飼う日本人女性 20〜40代

## アフィリエイト
- ASP: A8.net
- リンク: https://px.a8.net/svt/ejp?a8mat=4B5UWA+GC8AGI+3SUY+5Z6WY
- 商品: ペット見守りカメラ
- CTAコピー: 「コメント欄のリンクへ」

## 投稿済み動画一覧
| # | タイトル | 投稿日 | 再生数(目安) |
|---|---------|--------|------------|
| 1 | 僕がいないと、ご飯を食べない保護猫 | 2026/06/13 | 1,492 |
| 2 | 通知を見て、言葉を失った | 2026/06/16 | 1,781 |
| 3 | 帰れない夜だった | 2026/06/18 | 1,936 |
| 4 | 泣いてたの、バレてた | 2026/06/20 | 1,298 |
| 5 | 玄関で、目が合った | 2026/06/22 | ~375 |
| 6 | 心配で、泣いてしまった | 2026/06/23 | 投稿済 |

## 制作パイプライン（毎回この順番）
1. `python generate_images_petX.py` → gpt-image-1で7枚生成
2. Grok Agentに7枚アップ → 5秒動画×7本生成
3. Voicevox起動 → `python make_audio_petX.py` → 音声生成
4. `assemble_petX.py` → FFmpegで動画+音声+テロップ合成
5. `youtube_publisher.py --post` → YouTube Shortsアップロード
6. YouTube Studioでコメント欄にアフィリンクをピン固定
7. `python monitor_and_research.py` → 競合リサーチ

## キャラクター設定（画像プロンプト共通）
```
WOMAN = "Japanese woman in her early 30s, black shoulder-length straight hair
slightly tucked behind one ear, oval face, natural makeup,
wearing a light beige turtleneck sweater and dark navy trousers"
```

## 技術スタック
- 画像生成: gpt-image-1（size=1024x1536, quality=high, b64_json）
- 動画生成: Grok Agent（5秒, 縦型9:16）
- 音声: Voicevox 波音リツ（SPEAKER_ID=9, SPEED=0.88, PITCH=-0.03, INTONATION=1.4）
- 動画編集: FFmpeg（trim/resize/concat/ASS字幕焼き込み）
- 投稿: YouTube Data API v3（OAuth2.0, token.pickle）

## フックパターン（実績あり）
- 感情直球: 「泣いてたの、バレてた」「心配で、泣いてしまった」
- 状況描写: 「帰れない夜だった」「玄関で、目が合った」
- 不安×数字: 「一人で8時間、何してるんだろう」
- 共感: 「仕事中、何度スマホを見たかわからない」

## 競合TOP動画（リサーチ済）
1. ふわまるん「一人でいるにゃんこが心配でホームカメラを見て泣いてしまった飼い主」26,030,246再生
2. イチニコ「ペットカメラに写っていた母の奇行」22,028,616再生

## ピン固定コメントテンプレート
```
▼ 動画で紹介したペットカメラはこちら👇
https://px.a8.net/svt/ejp?a8mat=4B5UWA+GC8AGI+3SUY+5Z6WY

✅ 留守番中に声をかけられる
✅ スマホで24時間確認できる
✅ 夜間撮影・双方向通話対応

気になる方はお気軽にコメントください🐾
#PR #ペットカメラ #見守りカメラ
```

## 重要メモ
- description欄リンクはShortsでタップ不可（2023年8月〜）→ コメント欄ピン固定が必須
- 投稿間隔: 2〜3日が理想（毎日投稿はアルゴリズムに不利）
- scene7のテロップ: `留守番中の子に、声が届くカメラ。\Nコメント欄のリンクへ【PR】`
- FFmpegのASSフィルタはWindowsパスのコロン問題 → cwd=ass.parent で回避済み
- git pull前に未完了マージがある場合: `git commit --no-edit` してから pull

## 作業ディレクトリ
```
C:\Users\ys734\Desktop\Research\sns-affiliate-bot
```
