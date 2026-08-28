# 本番 checkout（参謀・2026-08-28 実測）

`CLAUDE.md` の「作業ブランチへ push した時点で本番反映」は、次のワークフローでは成り立たない。ジョブが別 ref を checkout するため。

円は足していない。cron は戻していない。

## ジョブが読むブランチ

| workflow | checkout `ref` | この sprint へ push した JS は動くか |
|---|---|---|
| `affiliate_engine_post.yml` | `claude/monthly-revenue-system-gvi02u` | 動かない |
| `affiliate_engine_insight.yml` | 同上 | 動かない |
| `affiliate_engine_report.yml` | 同上 | 動かない |
| `refresh_threads_token.yml` | 同上 | 動かない |
| `affiliate_engine_video_judge.yml` | デフォルト `claude/setup-colab-comfyui-Eb9Lh` | 動かない |
| `affiliate_engine_overlay_status.yml` | `claude/monthly-revenue-system-gvi02u` | 動かない（鍵名だけ。投稿しない） |

GitHub の schedule / デフォルトからの dispatch が使う **YAML** はデフォルトブランチ。`AFFILIATE_LINKS_JSON` を env に書く変更は、dispatch するブランチ（再開後の schedule ならデフォルト）の YAML が要る。schedule 自体は指令塔が出すまで戻すな。

## Secret 重ねは入った。cron は止まっている

2026-08-28 15:59 JST に `origin/claude/monthly-revenue-system-gvi02u` を読んだ結果（HEAD `37044d1`）:

- `util.js` に `loadLinks()` がある（PR #77、マージ `5ae52e2`、2026-08-28T05:27:22Z）
- PR #84 入済み（`37044d1`、2026-08-28T06:58:44Z）。`申込_auひかり` は Secret / ファイルのどちらからもも載せない
- `config/links.json` に `転職_neo` / `教育_N高` / `教育_アイズ` / `転職_チケット` / `申込_auひかり` がある。**値は全部空**
- seed に `career_20260828_neo_01/02` / `education_20260828_nko_01` / `education_20260828_eyes_01` / `career_20260828_ticket_01` がある
- 空リンクのスキップは `posted.json` に書かない（PR #80、マージ `307a858`、2026-08-28T05:24:20Z）

デフォルト YAML（`origin/claude/setup-colab-comfyui-Eb9Lh`、HANDOVER は dump raw を指す）:

- post / insight に `AFFILIATE_LINKS_JSON` がある（PR #78、マージ `2cd4499`、2026-08-28T05:26:53Z）
- `AMPLIFY_ENABLED` も `AFFILIATE_BODY_LINKS` も YAML に足していない
- schedule は post / insight / report とも **無い**（`workflow_dispatch` のみ）
- 2026-08-28 15:07 JST に `origin/claude/setup-colab-comfyui-Eb9Lh` を再読しても、post / insight / report / overlay_status に `cron:` は無い。`AMPLIFY_ENABLED` も `AFFILIATE_BODY_LINKS` も YAML に無い。戻すな

GitHub Secret の**値**はファイルに無い。`gh secret list` は 403。空の Secret なら本文は今までどおりスキップする（キーは残さない）。auひかりは Secret に入れるな。cron は戻すな。再マージするな。

Secret を入れたあと、投稿せず鍵名だけ見るジョブ: デフォルトの `affiliate_engine_overlay_status.yml`（PR #81 が 2026-08-28 14:53 JST に入った。`workflow_dispatch` のみ。schedule は無い。今夜の1手ではない）。この参謀ランから dispatch は 403。人間が https://github.com/fireworker011/Research/actions/workflows/affiliate_engine_overlay_status.yml で Run workflow（ref デフォルト。投稿しない）。2026-08-28 15:35 JST `gh run list` は空。ページは **0 workflow runs**。環境変数に `AFFILIATE_LINKS_JSON` / A8 系は無い（値は書いていない）。

重ね PR の状態（再マージするな）:

- https://github.com/fireworker011/Research/pull/77 MERGED
- https://github.com/fireworker011/Research/pull/78 MERGED
- https://github.com/fireworker011/Research/pull/80 MERGED
- https://github.com/fireworker011/Research/pull/81 MERGED（鍵名 dispatch。投稿しない）
- https://github.com/fireworker011/Research/pull/84 MERGED（auひかりを loadLinks から除外。投稿しない）
- 旧マージ指示 dump: `dump/G_hq_merge_overlay.txt`（入済み。今夜の1手ではない）

## 今夜の円の置き場（重ねを待たない）

指令塔が `Threadsあり` と返したあとの手動導線:

1. 開設済みか（`EXIST.md`）。未開設なら新造するな。neo は貼るな。次は教育 Threads × N高
2. 開設済み転職 Threads を副サイト登録（`SITE.md`）
3. 掲載サイトにその Threads を選んで発行した URL を Secret の `転職_neo` だけ（`SECRET.md`）
4. 同じ URL を転職 Threads の **プロフィールリンク欄**（`PROFILE.md`）

プロフィール欄は GitHub Actions を通らない。overlay 入済みでも置ける。本文に貼るな。cron は戻すな。ドライランと投稿ログは URL を出さない（`redactAffiliateUrls`）。amplify のリプ増幅は `AMPLIFY_ENABLED=1` が無いと動かない。本文の `{{AFFILIATE_LINK}}` は `AFFILIATE_BODY_LINKS=1` が無いと載せない。YAML に足すな。

neo が `項目なし` / `媒体なし` / `YouTubeあり` / 転職 `未開設` なら、同じ手動導線を教育 Threads × N高で行う（`EXIST_EDU.md` → `SITE_EDU.md` → `dump/G_hq_secret_nko.txt` → `dump/G_hq_threads_profile_edu.txt`）。neo を転職プロフィールに置いたあとも教育アカで N高へ進む。教育 YouTube は始めない。N高を転職アカに置くな。教育アカに neo を置くな。チケットが置けなければバナー出品するな。

## やらないこと

- post / insight / report の schedule を戻す
- URL を Git / チャット / このファイルに書く
- sprint ブランチへの push を本番反映と書く
- 転職 YouTube を始める
- カタログ 15000 円を `approved_yen` に足す
