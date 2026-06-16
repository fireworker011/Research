# SNS運用 15系統 マスタールール

このリポジトリは **3 SNS × 5ジャンル = 15系統** のSNS運用を、
**1系統 = 1会話 = 1つの `SYSTEM.md`** で回すための仕組みです。

## 全会話に共通する絶対ルール

1. **会話を開いたら、必ず対象系統の `SYSTEM.md` を最初に読む。** 読まずに作業を始めない。
2. **スマホ系(phone)では `Bash` / ターミナルを一切使わない。** 成果物はすべて
   「そのままコピペできるブロック」で出す(投稿文・キャプション・ハッシュタグ・台本)。
3. **PC系(pc)はノートブック実行・ファイル生成を行ってよい。**
   (`Lora_Trainer_XL.ipynb`, `wan22_i2v_lightx2v_colab.ipynb` を活用)
4. **作業の終わりに、得た知見を必ずその系統の `SYSTEM.md` の「改善ログ」に追記して commit する。**
   会話は使い捨てだが、mdに書けばノウハウは永続する。
5. 系統をまたいだ作業はしない。1会話=1系統に集中する。

## 起動方法(スマホ)

新規会話を開いたら、対象系統の「起動コマンド」1行を貼るだけ。
各起動コマンドは下の索引、または各 `SYSTEM.md` の冒頭に書いてある。

## 15系統 索引

### Threads
- `threads/phone/01_投稿文/SYSTEM.md` … スマホ / 投稿文・スレッド構成
- `threads/phone/02_ネタ収集/SYSTEM.md` … スマホ / ネタ収集・リプ戦略
- `threads/pc/03_画像生成/SYSTEM.md` … PC / 添付画像生成
- `threads/pc/04_LoRA素材/SYSTEM.md` … PC / LoRA素材作成
- `threads/pc/05_バッチ整形/SYSTEM.md` … PC / 画像バッチ整形

### YouTube Shorts
- `shorts/phone/01_台本/SYSTEM.md` … スマホ / 台本・キャプション
- `shorts/phone/02_フック/SYSTEM.md` … スマホ / フック・サムネ文言
- `shorts/pc/03_動画生成/SYSTEM.md` … PC / 動画生成(WAN i2v)
- `shorts/pc/04_LoRA学習/SYSTEM.md` … PC / LoRA学習・差し替え
- `shorts/pc/05_書き出し/SYSTEM.md` … PC / バッチ書き出し

### TikTok
- `tiktok/phone/01_台本/SYSTEM.md` … スマホ / 台本・キャプション
- `tiktok/phone/02_トレンド/SYSTEM.md` … スマホ / フック・トレンド合わせ
- `tiktok/pc/03_動画生成/SYSTEM.md` … PC / 動画生成(WAN i2v)
- `tiktok/pc/04_編集素材/SYSTEM.md` … PC / 編集用素材バッチ
- `tiktok/pc/05_書き出し/SYSTEM.md` … PC / バッチ書き出し

> ジャンル名・フォルダ名は仮。実ジャンルに合わせて自由にリネームしてよい。
