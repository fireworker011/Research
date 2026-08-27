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
| 8 | エンゲージ下書きの生成可否をコード面だけ。送信しない |
| 9 | 重複ガードと日付決定論 |
| 10 | conversions.csv。増えていなければ実測円 0 |
| 11 | HQ_ORDERS を1手に圧縮。dump が古ければ差し替え |
| 12–22 | 指令塔の新しい dump / 要望があればそれを1件。無ければ盤面更新のみ |
| 23 | 総括。指令塔へ返す材料だけ書く |

## 指令塔が人間へ出す手

参謀下書きは `output/sprint/HUMAN.md`。採否は指令塔。
