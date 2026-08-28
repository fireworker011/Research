# 指令塔に貼る順（参謀が用意）

司令部のチャットへ、**1回に1ファイル**。結合するな。

| 順 | ファイル | 仕事 |
|---|---|---|
| 今夜 | `dump/G_hq_cw_n10.txt` | CW 既応募6は再応募せず、新規4で N=10。貼るな |
| そのあと | `dump/G_hq_note_place.txt` | SKU1 を note 下書きに置く。公開するな |
| そのあと | `dump/G_hq_sns_next.txt` | neo `s00000018427001` を開け。返しは 未提携 / Threadsあり / YouTubeあり / 項目なし / 媒体なし。UZUZ は開くな |
| 未提携のあと | `dump/G_hq_a8_partner.txt` | neo だけ提携申請。UZUZ に申請するな。承認前に貼るな。承認後は sns_next を再貼り |
| Threadsありのあと | `dump/G_hq_threads_exist.txt` | 転職 Threads は 開設済み / 未開設。未開設なら新造するな。ハンドルはチャットに書くな |
| 開設済みのあと | `dump/G_hq_a8_site.txt` | その Threads を副サイト登録。未開設では使うな。転職YouTubeは始めるな |
| そのあと | `dump/G_hq_secret_neo.txt` | 掲載サイトにその Threads を選んで発行した URL を Secret の `転職_neo` だけ。links.json は空。cron は戻すな。自動投稿は checkout ブランチに重ねが無いと空のまま（`CHECKOUT.md`）。プロフィールは待たない |
| そのあと | `dump/G_hq_threads_profile.txt` | 開設済み転職 Threads のプロフィールリンク欄だけ。本文は貼るな。cron は戻すな。次は N高（教育アカは別。neo を教育に置くな） |
| YouTubeありのあと | `dump/G_hq_yt_only.txt` | Threads が欄に無い。プロフィールに置くな。転職YouTubeは始めるな。ペットに neo を置くな。次は N高 |
| neo の掲載を見たあと（置いた／置けなかった両方） | `dump/G_hq_sns_nko.txt` | N高 `s00000027548001` だけ開け。教育アカに置く。転職アカに N高を置くな。教育アカに neo を置くな。UZUZ は開くな |
| N高が 未提携 のあと | `dump/G_hq_a8_partner_nko.txt` | N高だけ提携申請。UZUZ に出すな。承認後は sns_nko を再貼り |
| N高が Threadsあり のあと | `dump/G_hq_edu_exist.txt` | 教育 Threads は 開設済み / 未開設。未開設なら新造するな。ハンドルはチャットに書くな |
| 教育が 開設済み のあと | `dump/G_hq_a8_site_edu.txt` | その教育 Threads を副サイト。転職アカに N高を載せるな。教育YouTubeは始めるな |
| そのあと | `dump/G_hq_secret_nko.txt` | Secret の `教育_N高` だけ。links.json は空。cron は戻すな |
| そのあと | `dump/G_hq_threads_profile_edu.txt` | 教育 Threads のプロフィールリンク欄だけ。本文は貼るな。次は転職アカが空ならチケット。neo を既に置いたならバナー（出品するな） |
| 教育が 未開設 のあと | `dump/G_hq_tenshoku_exist.txt` | アイズも置けない。新造するな。教育アカを今日開くな。未開設ならバナー（出品するな） |
| N高が YouTubeあり のあと | `dump/G_hq_yt_only_nko.txt` | 教育 Threads に置くな。教育YouTubeは始めるな。次はアイズ |
| N高が 項目なし / 媒体なし / YouTubeあり のあと | `dump/G_hq_sns_eyes.txt` | チャイルド・アイズ `s00000027572003` だけ開け。N高が Threadsあり かつ 教育 開設済み なら使うな。UZUZ は開くな |
| アイズが 未提携 のあと | `dump/G_hq_a8_partner_eyes.txt` | アイズだけ提携申請。承認後は sns_eyes を再貼り |
| アイズが Threadsあり のあと | `dump/G_hq_edu_exist.txt` | 教育 Threads は 開設済み / 未開設。未開設なら新造するな |
| 教育が 開設済み のあと | `dump/G_hq_a8_site_edu.txt` | その教育 Threads を副サイト。転職アカにアイズを載せるな |
| そのあと | `dump/G_hq_secret_eyes.txt` | Secret の `教育_アイズ` だけ。links.json は空。cron は戻すな |
| そのあと | `dump/G_hq_threads_profile_eyes.txt` | 教育 Threads のプロフィールリンク欄だけ。本文は貼るな。次は転職アカが空ならチケット |
| アイズが YouTubeあり のあと | `dump/G_hq_yt_only_eyes.txt` | 教育 Threads に置くな。教育YouTubeは始めるな。次は転職アカの有無 |
| アイズが 項目なし / 媒体なし / YouTubeあり のあと | `dump/G_hq_tenshoku_exist.txt` | 転職 Threads は 開設済み / 未開設。未開設なら新造するな。neo を既に置いたなら使うな（同じ欄）。次はバナー |
| 教育プロフィールのあと（neo を既に置いた） | `dump/G_hq_banner_10.txt` | チケットで上書きするな。出品するな |
| neo が Threadsあり かつ 未開設のまま アイズまで落ちたあと | `dump/G_hq_banner_10.txt` | tenshoku_exist は既知なので聞かず。チケットは置けない。出品するな |
| 開設済みのあと（neo 未置き） | `dump/G_hq_sns_ticket.txt` | キャリアチケット `s00000011866027` だけ開け。UZUZ は開くな。パーソル（ドライバー）は開くな |
| チケットが 未提携 のあと | `dump/G_hq_a8_partner_ticket.txt` | チケットだけ提携申請。承認後は sns_ticket を再貼り |
| チケットが Threadsあり のあと | `dump/G_hq_a8_site.txt` | 開設済み転職 Threads を副サイト。教育アカにチケットを載せるな |
| そのあと | `dump/G_hq_secret_ticket.txt` | Secret の `転職_チケット` だけ。links.json は空。cron は戻すな |
| そのあと | `dump/G_hq_threads_profile_ticket.txt` | 転職 Threads のプロフィールリンク欄だけ。本文は貼るな。次はバナー |
| チケットが YouTubeあり のあと | `dump/G_hq_yt_only_ticket.txt` | プロフィールに置くな。転職YouTubeは始めるな。次はバナー |
| チケットが 項目なし / 媒体なし のあと | `dump/G_hq_banner_10.txt` | チケットは置くな。出品するな |
| 転職 未開設 のあと | `dump/G_hq_banner_10.txt` | チケットは置けない。新造するな。出品するな |
| そのあと | `dump/G_hq_banner_10.txt` | 秋バナーは製作済。出品するな |
| そのあと | `dump/G_hq_a8_csv.txt` | A8 で見た数字だけ conversions に1行。開いていないなら足すな |
| 自動投稿を出す前 | `dump/G_hq_merge_overlay.txt` | PR 77 と 78 をマージ。schedule は戻すな。プロフィールは待たない |
| 旧 | `dump/G_hq_20260828.txt` | 使わない。今夜の1手は上 |

ジャンル9体の貼り文は `cursor/video-channel-playbook-e013` の `PHONE.md` が正。
