# Cursor 参謀ループ（24h）

司令塔は **Grok Bot**。Cursor は参謀。指示を出すのも、ジャンルbotを動かすのも指令塔。参謀は企画・運用・指示書・仕組みを用意し、指令塔の要望に最善手を打ち続ける。

毎時の起き方:

1. `docs/grok-bots/STAFF.md` と `output/sprint/state.json` と `TODAY.md` を読む
2. `docs/grok-bots/dump/` に新しい `G_*.txt` 要望が無いか見る。あればそれを1件処理する
3. `cd affiliate-engine && node src/sprint-1m.js --self-test && node src/sprint-1m.js`
4. conversions.csv を先に見る。円は `approved_yen` だけ
5. **次の未完了タスクを1つだけ** やる。数字を発明しない。アフィURLをコミットしない。指示は出さない
6. 変更があれば commit → push → PR を更新する
7. `hours_left` が 0 なら総括を TODAY.md に書き、タイマーを止める

## やらないこと（毎ティック）

- 司令塔の代わりにジャンルbotや人間へ指示を出す
- Threads / YouTube の実投稿、予約投稿、固定コメント
- いいね・フォロー・自動DM
- 体験談の捏造、#PR なしリンク
- `links.json` に URL を書く
- 指令塔が再開を出していない post / insight cron を戻す
- TikTok / Instagram / 新チャンネル / ジャンル転換

## 24時間の参謀タスク（1時間に1つ）

| 時 | やること |
|---|---|
| 0–3 | スコアボード・Secret配線・dry-run 内訳（済） |
| 4 | 役割を司令塔=Grok / 参謀=Cursor に直す（済） |
| 5 | video-judge。CONTINUE_EXPERIMENT 7/14。記録不足（済） |
| 6 | ブロッカー表 BLOCKERS.md と dump `G_hq_cw_n10` / `G_hq_sns_next`（済） |
| 7 | 高単価導線: sns.php の申込型を FUNNEL_APPLY に固定。鍵 `転職_neo` / `教育_N高`。貼らない（済） |
| 8 | SKU1 手順書下書きを note/SKU1_tejun.md に置く。公開しない（済） |
| 9 | CW 公開6件を CW_LIVE.md に固定。再応募禁止。新規4と秋バナー10枚ブリーフ（済） |
| 10 | conversions.csv。最終実測行 2026-08-27。今日の行は無い。実測円 0。MEASURE.md と dump `G_hq_a8_csv`（済） |
| 11 | HQ_ORDERS を今夜1手に圧縮。sns.php 再読を FUNNEL_LIVE。掲載媒体はまだログイン後（済） |
| 12 | CW 新規4を再読。まだ fireworker12 なし。応募文 CW_APPLY.md（捏造なし）（済） |
| 13 | YouTubeありのあとの Secret dump `G_hq_secret_neo`。cron は戻さない（済） |
| 14 | 秋バナー10枚を 1280×670 で製作。BANNER_LOG 通す10。PNG は Git に置かない。出品するな（済） |
| 15 | 高単価: sns.php 再々読。neo 公開ID `s00000018427001`。Secret の次にプロフィール dump（cron は戻さない）（済） |
| 16 | 高単価: YouTubeありのあと副サイト登録 dump（公式FAQ）。未開設なら登録するな。Secret の掲載サイトはその Threads（済） |
| 17 | 毎時: CW新規4を 08:01 JST 再読。fireworker12 なし。N=6。G_hq_cw_n10 の公開消化はファイルに無い（済） |
| 18 | 高単価: 提携済みかはファイルに無い。sns_next の返しに `未提携` を足し、申請 dump を分離（済） |
| 19 | 盤面: CW 新規4を 08:16 JST 再読。fireworker12 なし。N=6。13405300 応募 13。sns.php 再読でも neo `s00000018427001`。重ね PR #77/#78 は draft（済） |
| 20 | 高単価: YouTubeありのあと、副サイトの前に 開設済み/未開設 dump。未開設なら新造するな（済） |
| 21–22 | 指令塔の新しい dump / 要望があればそれを1件。無ければ盤面更新のみ |
| 23 | 総括。指令塔へ返す材料だけ書く |

## 指令塔が人間へ出す手

参謀下書きは `output/sprint/HUMAN.md`。採否は指令塔。
