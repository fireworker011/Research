# 再確認（2026-09-12）

これまでに挙げた 問題・未決・要望 を1件ずつ。証拠は今のリポジトリと実行結果だけ。人間の席が残るものは「席」と書く。

## 問題

| # | 問題 | 解決 | 証拠 |
|---|---|---|---|
| 1 | 投稿ボットがいない | Grok 2体（`4efdf8ca…`=A 投稿、`913a8b14…`=B Imagine）に役割カードと起動文を用意 | `bots/ROSTER.md` `bots/A-サクラ専属自動投稿.md` `bots/B-サクラImagine.md`。raw URL 200 |
| 2 | 参照顔がリポジトリに無い | 自アカの公開リール表紙（08-09, 07-27）を `refs/sakura-face.jpg` `refs/sakura-face-2.jpg` に置き、gitignore を外した | `refs/README.md`。raw で 184132B / 46308B の JPEG が落ちる（`src/dry-run.js`） |
| 3 | バイオに有料リンクが見えない | `config/links.json` の `fanvue` を A が初回設定でバイオに置く。URL は空 | `ig/first-run.md` §2。**席: Fanvue URL を1本入れる** |
| 4 | cron がデフォルトブランチ依存 | 時計を Grok Bot A のルーチンに移した。Actions は push トリガだけ（ブランチで動く） | `schedule.md`。`sakura_ig_handoff.yml` `sakura_ig_judge.yml` に `schedule:` なし。両方 push で success（run 34699742101 / 34699742129） |
| 5 | IG ログイン未確認 | A が 06:00 前にログインを確認。切れていれば止まり `席: IGログイン` を1行 | `bots/A-…md` ルーチン2 / 止まる条件 |
| 6 | 台帳が空 | 列を定義し、A が日曜に Insights を7行足す。push で `judge.js` が切り分けを Issue に書く | `data/reel_log.csv` ヘッダ。`node src/judge.js --self-test` 7分岐 OK。Issue #126「サクラ判定」が Actions から生成 |
| 7 | 8/9 以降 投稿停止 | 2026-09-13 06:00 JST から毎日1本のキーが200日分ある | `keys/INDEX.md` 2026-09-13〜2027-03-31。`validate-keys.js` OK |
| 8 | マネージャー→ボットに直接メンション不可 | 受け渡しを `keys/<date>.md` の raw URL 一本にした。Issue #54 は起動文の掲示板 | `dry-run.js` が明日分を raw で取得し IMAGINE_THROW / CAPTION を切り出せる |

## 未決

| # | 未決 | 決めたこと |
|---|---|---|
| 1 | 2 ID の役割 | 先に書かれた `4efdf8ca…` を A、`913a8b14…` を B と仮置き。逆ならカードを入れ替えて貼るだけ（`bots/ROSTER.md`） |
| 2 | 受け渡し口 | `keys/<YYYY-MM-DD>.md` 一本。Issue は鏡 |
| 3 | 投稿ボットの IG 接続 | 仕組み側からは確認できない。A の自己チェックと `席: IGログイン` で止める |

## 要望

| 要望 | 解決 | 証拠 |
|---|---|---|
| 保存済み返信4本・非表示ワード・AI 自動返信 OFF | A が初回設定で公式画面から設定。リプは自分の投稿へのコメントだけ、週20件、4定型 | `ig/first-run.md` §3–5。`bots/A-…md` リプ節 |
| API は不要 | xAI HTTP API・`imagine-run.js` を削除。カード・README・skills に「API キー不要」 | `rg XAI_API sakura-ig` → 検品の禁止語のみ |
| 顔・紅い和服・肩露出は固定、髪型だけ可変 | `lock.txt` `kimono.txt` に固定。他の着5種を削除。髪型8種を日付で回す | `prompts/`。全キーに `vermillion-red` `off both shoulders` `No nudity` `Do not invent a new face` を検品 |
| プロンプトを作り込む | 参照URL → 顔ロック → 和服 → STEP1（髪・場面・構図だけ変更）→ STEP2（冒頭0.5秒・動き・カメラ・音）→ CHECK → Avoid。約3,600字 | `keys/2026-09-17.md` など |
| 新しいエージェント・司令塔を増やさない | Cursor 1体 ＋ Grok 2体。4体目なし | `bots/ROSTER.md` 共通ルール |
| 介入を極限まで減らす | 毎日ゼロ。人間は「Fanvue URL」「2体にカードを貼る・ログイン」「席: が出た時」だけ | `README.md` 人間の席 |

## 仕組みの穴確認

| 確認 | 結果 |
|---|---|
| `node --check src/*.js` | 5本 OK |
| `validate-keys.js`（200日・重複・連日の髪型/場面・ロック語・木曜CTA・06:00 JST） | OK。土曜の季節場面が金曜と重なる日を1回検出→前後日から計算して回避（状態なし） |
| 同じ日は同じキーか（`--from` を変えて再生成） | md5 一致 |
| ワークフロー YAML | 2本 parse OK。push で success |
| raw URL 取得（キー・INDEX・参照2枚・カード3枚・初回設定・links.json） | すべて 200。銀行の翌日は 404（A は何もしない、が仕様） |
| 模擬1日（`dry-run.js` 09-13 / 10-17 / 銀行外） | OK / OK / 404 正常 |
| 古い参照（launch-keys, imagine-run, wardrobe, post-gate 等） | 本文から消えた。残りは検品の禁止語だけ |
| Issue 掲示 | #54 に銀行案内（起動文A/B・場所・初日キー）。#126 サクラ判定 stage 0 |

## 残る席（仕組みでは埋まらない）

1. `config/links.json` に Fanvue URL を1本（A がバイオに置く）
2. Grok Bot 2体に `bots/ROSTER.md` の起動文を貼る。A は IG と GitHub にログイン済みにする
3. A が `席: …` を1行書いた時だけ動く

## 触っていないもの

Threads の post/insight/report cron、draft PR #122、`affiliate-engine/`、`hq-instruct.js`、デフォルトブランチ。
