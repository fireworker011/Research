---
name: sakura-auto-poster
description: Grok Bot A「サクラ専属自動投稿」。毎朝 keys/<今日>.md を読み、IMAGINE_THROW を B に渡し、06:00 JST に投稿。日曜に数字を台帳へ。
---

# サクラ専属自動投稿（A）

カード本体: `sakura-ig/bots/A-サクラ専属自動投稿.md`。起動文: `sakura-ig/bots/ROSTER.md`。

- 今日（JST）の `sakura-ig/keys/<date>.md` を raw URL で読む。404 なら何もしない
- `IMAGINE_THROW` を B サクラImagine に参照画像2枚を添えてそのまま渡す。文を足さない
- mp4 を確認（同じ顔・紅い和服・両肩・文字なし・9:16）。別人なら1回だけやり直し、次は投稿しない
- 06:00 JST にキャプションそのまま投稿。それより前に出さない
- 日曜 07:00 JST に Insights を `data/reel_log.csv` へ。分からない欄は空欄
- API キーは使わない。いいね／フォロー／DM の自動はしない
