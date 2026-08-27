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
| `sprint_1m.yml` | デフォルト | 動かない |

GitHub の schedule / デフォルトからの dispatch が使う **YAML** はデフォルトブランチ。`AFFILIATE_LINKS_JSON` を env に書く変更は、dispatch するブランチ（再開後の schedule ならデフォルト）の YAML が要る。schedule 自体は指令塔が出すまで戻すな。

## Secret だけでは自動投稿は空のまま

2026-08-28 に `origin/claude/monthly-revenue-system-gvi02u` を読んだ結果:

- `util.js` に `loadLinks()` が無い
- poster / amplify / insight / strategy-engine は `loadConfig('links')` のファイルだけを見る
- `config/links.json` に `転職_neo` / `教育_N高` / `申込_auひかり` が無い
- post / insight の YAML に `AFFILIATE_LINKS_JSON` が無い
- seed に `career_20260828_neo_01/02` が無い（重ね PR 77 が足す。N高 `education_20260828_nko_01` とアイズ `education_20260828_eyes_01` も重ねに足す）

GitHub Secret を入れても、checkout ブランチがファイルの空キーしか見ない。`skipped_no_link` になる。sprint ブランチの重ねは本番ジョブでは使われない。

重ねコードの置き場:

- checkout ブランチ（JS + 空キー + neo テンプレ + YAML env）: https://github.com/fireworker011/Research/pull/77 （`cursor/prod-neo-secret-overlay-a971` → `claude/monthly-revenue-system-gvi02u`）。2026-08-27 23:25 UTC 時点 MERGEABLE。schedule は戻していない
- デフォルト YAML の env だけ（schedule は戻していない）: https://github.com/fireworker011/Research/pull/78
- マージ指示 dump: `dump/G_hq_merge_overlay.txt`（自動投稿を出す前。プロフィールは待たない）

## 今夜の円の置き場（重ねを待たない）

指令塔が `Threadsあり` と返したあとの手動導線:

1. 開設済みか（`EXIST.md`）。未開設なら新造せず止まれ
2. 開設済み転職 Threads を副サイト登録（`SITE.md`）
3. 掲載サイトにその Threads を選んで発行した URL を Secret の `転職_neo` だけ（`SECRET.md`）
4. 同じ URL を転職 Threads の **プロフィールリンク欄**（`PROFILE.md`）

プロフィール欄は GitHub Actions を通らない。overlay 未マージでも置ける。本文に貼るな。cron は戻すな。

neo が `項目なし` / `媒体なし` / `YouTubeあり` なら、同じ手動導線を教育 Threads × N高で行う（`EXIST_EDU.md` → `SITE_EDU.md` → `dump/G_hq_secret_nko.txt` → `dump/G_hq_threads_profile_edu.txt`）。教育 YouTube は始めない。N高を転職アカに置くな。

## やらないこと

- post / insight / report の schedule を戻す
- URL を Git / チャット / このファイルに書く
- sprint ブランチへの push を本番反映と書く
- 転職 YouTube を始める
- カタログ 15000 円を `approved_yen` に足す
