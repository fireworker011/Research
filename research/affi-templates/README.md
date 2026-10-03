# アフィ縦動画のジャンル別テンプレート

美容スキンケア、ドッグフード、見守りカメラ、婚活について、伸びてるアカウントの型を1枚にまとめる。投稿も動画生成もしない。台本の文は作らない。数字は `accounts.csv` にあるものだけ。

## Colabで開く

https://colab.research.google.com/github/fireworker011/Research/blob/cursor/affi-genre-templates-6dc5/research/affi-templates/affi_genre_templates.ipynb

上から順に実行する。リポジトリを開いているときはその場の CSV を読む。Colab だけ開いたときは、同じブランチの raw URL から CSV とモジュールを取る。

## データを差し替える

1. 新しい CSV を `research/affi-templates/data/<日付>/accounts.csv` に置く。`videos.csv` はあれば一緒に置く（集計には使わない。行数だけ記録する）。
2. ノートブックの `DATE` をそのフォルダ名にする。ローカルなら次でも同じ。

```bash
python3 research/affi-templates/affi_genre_templates.py \
  --data research/affi-templates/data/2026-10-03 \
  --out research/affi-templates/templates
```

しきい値は `--strong-min` `--compare-min` `--thin-below` `--min-gap-pt`。既定は 10 / 3 / 10 / 10。

- 両群の判定件数が 10 以上: 信頼度「強い」
- 両群が 3 以上で、どちらかが 10 未満: 「弱い」
- どちらかが 3 未満: 「比較不能」
- 伸び悩みのアカウント数が `thin_below` 未満: 既定値は伸びてる群の最頻値とし、「比較ではなく伸びてる群の傾向」と書く

「不明」「空」「その他/不明」は分母に入れない。`product_display` は `;` で分け、知っている語だけ数える。`notes` が「ユーザー参考アカウント」で始まる行は集計に入れない。

## テンプレートの読み方

`templates/compare.md` が4ジャンルの横並び。`templates/<ジャンル>.md` が人用の1枚。`templates/<ジャンル>.json` が台本係用。

各ジャンルの「このジャンルで作るとき」は、伸びてる群の最頻値。件数と信頼度が同じ行にある。

- 伸びてる側に寄っている: 伸びてる群の割合の方が 10pt 以上高いもの
- やらないこと: 伸び悩み群の割合の方が 10pt 以上高いもの。伸びてる群で 50% 以上の最頻値は、ここから外す
- 最初の3秒の参考例: 再生中央値が高い伸びてるアカウントの引用。コピーしない
- 参考アカウント: 指定の4件。集計の外で、テンプレと同じか違うかだけ書く

投稿頻度の差は、伸び悩みの定義が「直近30日に4本以上」なので、3本以下との差は定義の影響を受ける。

## bot用スキーマ `affi-genre-template/v1`

`templates/<ジャンル>.json` の主な枠。

| キー | 意味 |
|---|---|
| `basis` | `比較` または `伸びてる群の傾向` |
| `account_confidence` | アカウント数での信頼度。強い / 弱い / 比較不能 |
| `script_brief.first_3_seconds.opening_type` | 最初の3秒の型。具体文は入っていない |
| `script_brief.first_3_seconds.examples` | 参考引用。`platform` `handle` `evidence` `first_frame_text` |
| `script_brief.first_3_seconds.homage` | ペット2ジャンルだけ。YouTube @cat-yu-chan の型。集計外。再生数は無い。映像・すず丸・タイトル文は使わない |
| `script_brief.middle_pattern` | 真ん中で、伸びてる側に寄っている商品の見せ方。無ければ `["データ不足"]` |
| `script_brief.on_screen` | `main_subject` と `face_shown` |
| `script_brief.duration_band` | 尺の帯。同数なら `同数（…）` |
| `script_brief.duration_median_sec` | 伸びてる群の尺の中央値。無ければ null |
| `script_brief.audio` | 音 |
| `production` | ハッシュタグの帯、PR、投稿頻度、テンプレ固定 |
| `avoid` / `favor` | 差が 10pt 以上の項目。`growing` / `struggling` は `m` `n` `pct` |
| `reference` | 参考アカウント。`same` と `different` |

`templates/all.json` は4ジャンルをまとめたもの。

## 限界

- 冒頭・顔出し・音・商品の見せ方の多くは `feature_source=推定（説明文）`。動画は見ていない。
- 伸び悩みは件数が少ない。3件未満と比べない。見守りカメラとドッグフードは薄い。
- 同じ handle がプラットフォーム違いで2行ある。参考から外すのは notes が「ユーザー参考アカウント」で始まる行だけ。婚活の `@yako.shiawasekon` は TikTok 行が参考、Instagram 行は伸びてる群に残っている。
- `videos.csv` はアカウント集計に混ぜない。プラットフォーム名が accounts と揃っておらず、ある分だけの動画だから。
- ドッグフードと見守りカメラには、YouTube @cat-yu-chan（すず丸と暮らしてます）の型をオマージュとして足してある。集計の266件には入っていない。再生数は書いていない。借りるのは「同じ子、最初の不一致、商品は後、シリーズ」だけ。ドッグフードを作るときは、集計の「商品名から入る・手元」よりこの型を先に使う。
- 前回の `opening-types.md`（美容・ペットをプラットフォーム別に見た別調査）では、美容の伸びてる側は冒頭Bが多め、という書き方だった。今回の `accounts.csv` では美容の伸びてる最頻は「その他」（132件中73件、55%）。Bは伸び悩みの方が割合が高い（30件中12件、40% 対 132件中33件、25%）。テンプレートは今回の CSV に従う。

## テスト

```bash
python3 -m pytest research/affi-templates/test_affi_genre_templates.py -q
```
