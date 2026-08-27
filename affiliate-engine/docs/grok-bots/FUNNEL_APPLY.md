# 申込型導線（参謀・貼るな）

公開ページだけ。カタログ円は確定円に足さない。URL は書かない。指令塔が掲載媒体を確認するまで投稿しない。

出典:
- 高額報酬ランキング（最終更新 2026.8.10）: https://support.a8.net/as/HintOfProgram/ranking/highprice.php
- SNS投稿おすすめ（2026-08-28 開封）: https://support.a8.net/as/HintOfProgram/sns.php
- SNS掲載のFAQ: https://support.a8.net/a8/as/faq/2022/post_1955.html

## 次に確認する1件（auひかりではない）

公開実測: `docs/grok-bots/FUNNEL_LIVE.md`（2026-08-28 07:51 JST 再々読。sns.php に neo / N高は載っている。neo の公開ID `s00000018427001`）。

| 公開名 | ページ | 公開プログラムID | 公開の成果地点（カタログ） | 既存アカ |
|---|---|---|---|---|
| 第二/既卒/フリーター/中退/高卒の就職・転職支援【第二新卒エージェントneo】 | sns.php「売れてる案件」 | `s00000018427001` | 新規カウンセリング15000円（足すな） | 転職 |
| N高等学校 | sns.php「注目案件」 | `s00000027548001` | 新規資料請求15000円（足すな） | 教育 |
| チャイルド・アイズ | sns.php「注目案件」 | `s00000027572003` | 新規無料体験予約6767円（足すな） | 教育 |

sns.php は「前月 SNS 経由で成果が出た」と書いてある。プログラム詳細の掲載媒体（YouTube の有無）はログイン後。**確認前に貼るな。** 同じページの UZUZ第二新卒（`s00000014490001`）は neo の代わりにしない。

人間の返し: `未提携` / `Threadsあり` / `YouTubeあり` / `項目なし` / `媒体なし`。未提携＝申請は `dump/G_hq_a8_partner.txt`。項目なし・媒体なし＝neo は貼らない。次は N高 `dump/G_hq_sns_nko.txt`。YouTubeあり（Threads 無し）＝プロフィールに置くな（`dump/G_hq_yt_only.txt`）。そのあと N高。

見ないもの: auひかり（項目なし）。オリコで乗ーるをオリコカードに代入するな。Pappy 等のマッチングは Meta の出会い系リスクで使わない。

## 貼る位置（確認後・指令塔が再開を出したとき）

| 媒体 | 位置 | 足すな |
|---|---|---|
| YouTube | 指令塔が指定した既存動画の詳細欄 + PR表記 + 有料プロモーション | 動画内URL。ShortsコメントのアフィURL。転職ジャンルの新規チャンネル（台帳 `make: never`） |
| Threads | プロフィールのリンク欄 | スレッド本文の広告リンク（A8 FAQ: iOS遷移不良のため本文は控える）。cron 独断再開 |

テンプレは seed に `転職_neo` / `教育_N高`。値は空。本文は「調べた／整理した」。体験の捏造なし。#PR 付き。

空キーのまま投稿すると `skipped_no_link`。Secret `AFFILIATE_LINKS_JSON` は指令塔が `Threadsあり` と返し、転職 Threads が `開設済み`（`EXIST.md` / `dump/G_hq_threads_exist.txt`）のあと、副サイト登録（`SITE.md` / `dump/G_hq_a8_site.txt`）を経て人間が入れる。手順: `docs/grok-bots/SECRET.md`。dump: `dump/G_hq_secret_neo.txt`（YouTubeあり／項目なし／媒体なし／未開設では使わない）。その次はプロフィールリンク欄: `docs/grok-bots/PROFILE.md` / `dump/G_hq_threads_profile.txt`。

neo が `項目なし` / `媒体なし` / `YouTubeあり` のときは N高へ。N高も同じなら チャイルド・アイズへ（`dump/G_hq_sns_eyes.txt`）。教育 Threads が `開設済み`（`EXIST_EDU.md`）なら副サイト `dump/G_hq_a8_site_edu.txt` → Secret `教育_N高` または `教育_アイズ` → 教育プロフィール。教育 YouTube は始めない。
