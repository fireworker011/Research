# 計測回転（参謀・invent するな）

円の正本は `data/conversions.csv` の `approved_yen`。カタログ単価・CW報酬表示・note 価格欄 980・再生は円ではない。

日次レポートの cron は停止のまま。このファイルは **行の書き方** だけ。再開は指令塔が出す。

## 列（この順。増やさない）

```
date,source,program,clicks,cv,approved_yen,note
```

| 列 | 書く | 書くな |
|---|---|---|
| date | 管理画面を開いた日（JST `YYYY-MM-DD`） | 推測した日 |
| source | 見た画面の名前（例: `A8`） | URL |
| program | 画面のプログラム名。全部なら `all` | アフィURL |
| clicks | 画面のクリック数。カンマも円も外した整数 | 再生数を代入。`1,000`（引用符なし） |
| cv | 画面の成果件数。整数 | カタログの想定 CV |
| approved_yen | 画面の **確定金額**。`15000` のように整数。引用符付き `"1,000"` は読める | 未確定・掲載単価・EPC。引用符なしの `1,000`（列が壊れ 1 円になる） |
| note | 期間のメモ（URLなし） | 売上予想 |

古い例 `date,genre,amount_jpy,status` は使わない。

## 手順

人間は A8 画面を見る。CSV を手で編集しなくてよい。見た数字を Issue タイトル **`Affiliate — 確定円`** に1行:

```
A8_YEN: 2026-09-09,A8,all,33,0,0,screen monthly
```

Grok Bot がこの1行を Issue に書いてよい。Cursor は日常で起こすな。Actions が `conversions.csv` に書き、指示役コメントの `approved-yen:` が合計を出す。ファイルが無いときは `unknown`（0 を invent しない）。

1. A8 管理画面を開く。開いていないなら **行を足すな**（0 を invent するな）。
2. 見えた clicks / cv / 確定金額だけを上の1行にする。カンマと円記号は外す（`15000`）。引用符なしの `1,000` は書くな。見えた 0 は 0 と書く。note に「カタログ」と書いて yen を足すな。
3. 同じ source・同じ program は **最新日の行だけ** が円。同じ日の同じ program は上書き。
4. `program=all` と案件別を同じ source に並べるな。
5. URL を書くな。report の cron は回すな。

Secret の埋まっている鍵名は指示役 Issue の `overlay-filled:` / `overlay-keys:`（毎日。URL は出さない）。`affiliate_engine_overlay_status.yml` の Run は不要。`申込_auひかり` は載せない。開いていない A8 の円は足すな。

## 円にしないもの

- CW 公開ページの報酬表示・契約人数・応募画面の 455円 / 100円。source を `CW` にして足してもスコアボードは拒否する
- note 価格欄 980・未公開
- 秋バナーの枚数
- `video_cash_log.csv` の再生・A8 累計クリック
- sns.php のカタログ報酬

ペット実験の当日数字は `data/video_cash_log.csv` に1行。円の合計には使わない。無い日は空のまま。
