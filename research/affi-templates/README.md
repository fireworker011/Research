# アフィ縦動画のジャンル別テンプレート

美容スキンケア、ドッグフード、見守りカメラ、婚活について、伸びてるアカウントの型を1枚にまとめる。投稿も動画生成もしない。台本の文は作らない。数字は `accounts.csv` にあるものだけ。

## Colabで開く

https://colab.research.google.com/github/fireworker011/Research/blob/cursor/affi-genre-templates-6dc5/research/affi-templates/affi_genre_templates.ipynb

開いたら、上の **ランタイム → すべてのセルを実行**。許可を聞かれたらそのまま実行。下に4ジャンルの表が出る。コードは読まない。日付以外は触らない。

表の「冒頭」は最初の3秒、「主役」は画面の中心。強い＝両方10件以上、弱い＝件数が少ない、比較不能＝片方が3件未満。ドッグフードと見守りは、表の次の「オマージュ」を先に使う。動画は作らない。

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

## 参考4アカウントの再現（2026-10-04）

設計書は `reference-accounts/source/`。機械が読む型は `reference-accounts/templates/`。元の台詞とキャラはコピーしない。仕様の「推定」「不明」はそのまま。

制作シート:

```bash
python3 research/affi-templates/affi_reference.py feasibility
python3 research/affi-templates/affi_reference.py ab --id H1-1 --theme 髪の悩み
python3 research/affi-templates/affi_reference.py judge
```

判定用のColab:

https://colab.research.google.com/github/fireworker011/Research/blob/cursor/affi-genre-templates-6dc5/research/affi-templates/reference_check.ipynb

投稿後の数字は `reference-accounts/results.csv` に手で入れる。空欄は0にしない。72時間後の値。1回に変える要素は1つ。

### 最初にやること

仮説の本投稿の前に、Grok Imagineで制作可否を見る。

1. F1 日本語の口パクが1文できるか
2. F2 同じ参照画像で、場所を変えても顔が同じか
3. F3 衣装を着た同じ動物が全身で踊れるか（元はKling。できるかは未確認）

その次は H1-1（美容の表紙）、H2-1（犬がしゃべるか）、H3-1（最初の一言が対立か）。

### ジャンル別テンプレとの食い違い

- 見守りカメラの参考 @junjun_ranran は、ペットカメラ映像ではない。写実のAIで、猫2匹が口を動かして掛け合うコント。ジャンル集計の「顔なし・動物が主役」とは違う。
- ドッグフードの参考 @nuts0629 は、商品名から入る手元の型ではない。しゃべる犬のインタビューと、着ぐるみのダンス。最終投稿は2026-01-31。
- 美容の参考 @the.care.logic は、人の顔出しとナレーションの型ではない。ピクサー風の3Dキャラが10秒×3。字幕なし。台詞はミャンマー語で不明。
- 婚活の参考 @yako.shiawasekon は、説明の短編より、会話だけのドラマが伸びている。教訓とCTAを本編に入れた回は落ちている。

## テスト

```bash
python3 -m pytest research/affi-templates/test_affi_genre_templates.py research/affi-templates/test_affi_reference.py -q
```
