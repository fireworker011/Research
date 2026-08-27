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
| clicks | 画面のクリック数 | 再生数を代入 |
| cv | 画面の成果件数 | カタログの想定 CV |
| approved_yen | 画面の **確定金額** | 未確定・掲載単価・EPC |
| note | 期間のメモ（URLなし） | 売上予想 |

古い例 `date,genre,amount_jpy,status` は使わない。

## 手順

1. A8 管理画面を開く。開いていないなら **行を足すな**（0 を invent するな）。
2. 見えた clicks / cv / 確定金額だけを1行にする。見えない列は空にしない。見えた 0 は 0 と書く。
3. 同じ日・同じ source・同じ program の行が既にあれば、上書きするか新しい行にするかを画面の数字に合わせる。数字を足して倍にしない。
4. `node src/sprint-1m.js --self-test && node src/sprint-1m.js` で TODAY.md の実測円が CSV と一致することを見る。
5. アフィURL・トークンを Git / チャット / ログに書くな。

## 円にしないもの

- CW 公開ページの報酬表示・契約人数
- note 価格欄 980・未公開
- 秋バナーの枚数
- `video_cash_log.csv` の再生・A8 累計クリック
- sns.php のカタログ報酬

ペット実験の当日数字は `data/video_cash_log.csv` に1行。円の合計には使わない。無い日は空のまま。
