# サクラIG（`sakura_ai_beauty`）

ゴールはフォロワー増ではない。**リールが届き、プロフィールの Fanvue が週15回押され、課金が判定できる**こと。  
判定は 再生 → クリック → 成果。数字は台帳の行だけ。発明しない。

## 仕組み（API 不要。cron 不要。人間の毎日ゼロ）

```
Cursor マネージャー（この体・1体）
  prompts/ と src/build-keys.js で keys/<date>.md を100日分書く。Imagine を呼ばない。投稿しない

Grok Bot A サクラ専属自動投稿     05:00 JST  keys/<今日>.md を raw URL で読む → B に IMAGINE_THROW ＋参照画像2枚
Grok Bot B サクラImagine          STEP 1 静止画（髪型・場面・構図だけ変える）→ STEP 2 動画 → mp4 を A に返す
Grok Bot A                        06:00 JST  リール投稿。キャプションそのまま
Grok Bot A                        日曜 07:00 JST  Insights の数字を data/reel_log.csv に足す
GitHub Actions                    CSV が push されたら src/judge.js が Issue「サクラ判定」に切り分けを書く
```

- 受け渡し口は **`keys/<YYYY-MM-DD>.md` の raw URL 一本**。Issue「サクラ起動キー」は起動文と初日の掲示板（鏡）
- 顔・紅い和服・両肩の露出は固定。**髪型だけ**日で変わる。他の着は無い
- 型は曜日で決まる: 月 question / 火 turn / 水 micro / 木 push-pull（CTA）/ 金 detail / 土 season / 日 loop
- キーは日付だけから決まる。作り直しても同じ日は同じキー（`node src/build-keys.js --from ... --days ...`）

## 場所

| もの | パス |
|---|---|
| 役割表・起動文 | `bots/ROSTER.md` |
| A のカード | `bots/A-サクラ専属自動投稿.md` |
| B のカード | `bots/B-サクラImagine.md` |
| IG 初回設定 | `ig/first-run.md` |
| 起動キー銀行 | `keys/<date>.md` / `keys/INDEX.md` |
| 参照顔 | `refs/sakura-face.jpg`（正本）`refs/sakura-face-2.jpg` |
| プロンプト部品 | `prompts/lock.txt` `prompts/kimono.txt` `prompts/bank.json` `prompts/negatives.txt` |
| 設定 | `config/account.json` `config/links.json` |
| 台帳 | `data/reel_log.csv` |
| 判定 | `src/judge.js` → Issue「サクラ判定」 |
| 監査 | `CHECK.md` |

## コマンド

```bash
cd sakura-ig
node src/build-keys.js --from 2026-09-13 --days 100   # 銀行を作る／延ばす
node src/validate-keys.js                             # 検品（重複・ロック語・木曜CTA・時刻）
node src/judge.js --self-test && node src/judge.js    # 台帳の切り分け
node src/handoff.js --local                           # Issue 掲示文の確認
```

## 人間の席（これだけ）

1. `config/links.json` に Fanvue の URL を1本入れる（A がバイオに置く）
2. Grok Bot 2体にカードを貼る（`bots/ROSTER.md`）。A は IG と GitHub にログインした状態にする
3. あとは A の `席: …` が出た時だけ

## しないこと

いいね／フォロー自動、人間を装う DM、非公式 API、他の着、新しい顔、画面内の日本語、歌詞、X/TikTok の同時追加、Threads cron の復帰、PR #122 のマージ、4体目の Bot。
