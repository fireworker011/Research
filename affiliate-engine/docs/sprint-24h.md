# Cursor 24h スプリント手順

ナオミチ指令（2026-08-27）: 今日から 2026-09-30 までに確定 ¥1,000,000。このエージェントは **24時間、毎時1ティック** で動く。Grok Bot の指令よりナオミチのこのスレッドを優先する。

毎時の起き方:

1. `affiliate-engine/output/sprint/state.json` と `TODAY.md` と `HUMAN.md` を読む
2. `cd affiliate-engine && node src/sprint-1m.js --self-test && node src/sprint-1m.js`
3. `conversions.csv` を先に見る。円は `approved_yen` だけ。無いものは「ファイルに無い」
4. **次の未完了タスクを1つだけ** やる（下の表）。数字を発明しない。アフィURLをコミットしない
5. 変更があれば commit → push → PR を更新する
6. `hours_left` が 0 なら 24h の総括を `output/sprint/TODAY.md` に書き、タイマーを止める

## やらないこと（毎ティック）

- Threads / YouTube の実投稿、予約投稿、固定コメント
- いいね・フォロー・自動DM
- 体験談の捏造、#PR なしリンク
- `links.json` に URL を書く
- 停止中の post / insight cron を、リンク Secret 無しで戻す
- TikTok / Instagram / 新チャンネル / ジャンル転換
- Grok Bot の dump を待って止まる

## 24時間のタスク順（1時間に1つ）

| 時 | やること |
|---|---|
| 0 | スコアボード・Secretリンク読み込み・この手順をデフォルトラインに載せる（本ティック） |
| 1 | `threads-poster.js --dry-run` で、価値提供投稿 vs `skipped_no_link` の内訳を state に残す |
| 2 | post / amplify ワークフローに `AFFILIATE_LINKS_JSON` が渡るか確認。足りなければ足す |
| 3 | 高単価キー（`申込_auひかり` 等）がテンプレ検品で落ちないことを `strategy-engine.js --from-file` で確認 |
| 4 | 人間ブロッカー（HUMAN.md）を1枚に保ち、A8 SNS可否が未確認なら貼るなと繰り返す |
| 5 | video-judge を回し、記録不足なら CSV 追記だけ頼む。新しい台本は創らない |
| 6 | 残日数×必要ペースを funnel-calc 1,000,000 と突き合わせ、カタログ円は足さない |
| 7 | トークン未設定アカウント（setsuyaku / tenshoku / pet / sleep）を state に列挙するだけ。発行は人間 |
| 8 | エンゲージ下書きの生成可否をコード面だけ確認。送信はしない |
| 9 | 重複ガードと日付決定論が壊れていないことを再確認 |
| 10 | conversions.csv の行が増えていないか見る。増えていなければ実測円 0 のまま |
| 11 | 24h 中間: 埋まっていないブロッカーを HUMAN.md の1手に圧縮する |
| 12–22 | 同じ読み順。新しい媒体を足さず、ブロッカーが解消されたら Secret 連携の配線だけ進める |
| 23 | 24h 総括。残日数と不足円。Threads cron を戻したかどうか（戻していないのが正） |

## 人間がやること（エージェント代替不可）

`output/sprint/HUMAN.md` の1手。いまは:

1. A8 管理画面で SNS 掲載可否を見た案件だけ選ぶ
2. その URL を GitHub Secret `AFFILIATE_LINKS_JSON` に入れる
3. 見た数字を `conversions.csv` に1行
