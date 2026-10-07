# アフィ縦動画

開くノートは1つです。表も、話のジョブも、自分の文の I2V も、その mp4 も、このページです。

https://colab.research.google.com/github/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/affi.ipynb

## 使い方

ランタイムは最初から GPU にする。途中で変えない。

1. **読み込み**
2. **選ぶ** で、やりたいことを1つ選んで実行
3. **実行**
4. **焼く**（ready のあと。焼くにチェックを入れて押す。最初は1本だけ）

上の「すべてのセルを実行」は押さない。焼くはオフなので、全部実行しても動画は始まらない。コードは読まない。

見た目は初期値のまま進めていい。変えるときだけ、2と3のあいだに、話の名前が同じ見た目のセルを1つ実行する。

## 選び方

- **表を見る** … 美容、ドッグフード、見守りカメラ、婚活の作り方。ジョブは書かない。日付は 2026-10-07。初めてなら変えない。
- **話でジョブを書く** … 話を1つ。ドッグフードだけインタビュー・咀嚼・ダンス・会話。中身は「テンプレ」「オマージュ」「元の型のまま」。テーマと台詞は入っている。元の顔、元の台詞、曲名は入らない。静止画は空でよい。空なら文章から焼く。ファイルを書くと、その画像が最初のコマになる。
- **自分の文で1本** … プロンプトを自分で書く。静止画が空なら T2V。ファイルがあれば I2V。「実行」が ready なら、一番下の「焼く」で1本焼く。

Checkpoint は MiniMax-H3。LoRA は FL2VA の Turbo と Motion Repair V2。話のジョブも I2V も同じです。

表の「冒頭」は最初の3秒、「主役」は画面の中心。強い＝両方10件以上、弱い＝件数が少ない、比較不能＝片方が3件未満。ドッグフードと見守りは、表の次の「オマージュ」を先に使う。表は mp4 を焼かない。数字は `accounts.csv` にあるものだけ。

表の「冒頭」は最初の3秒、「主役」は画面の中心。強い＝両方10件以上、弱い＝件数が少ない、比較不能＝片方が3件未満。ドッグフードと見守りは、表の次の「オマージュ」を先に使う。表のセルは mp4 を焼かない。

## データを差し替える

1. 新しい CSV を `research/affi-templates/data/<日付>/accounts.csv` に置く。`videos.csv` はあれば一緒に置く（集計には使わない。行数だけ記録する）。
2. ノートブックの `DATE` をそのフォルダ名にする。ローカルなら次でも同じ。

```bash
python3 research/affi-templates/affi_genre_templates.py \
  --data research/affi-templates/data/2026-10-07 \
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
- ドッグフードと見守りカメラには、YouTube @cat-yu-chan（すず丸と暮らしてます）の型をオマージュとして足してある。集計の277件には入っていない。再生数は書いていない。借りるのは「同じ子、最初の不一致、商品は後、シリーズ」だけ。2026-10-07 のドッグフードは、伸びてる群の最頻が冒頭「その他」、主役「動物」。
- 前回の `opening-types.md`（美容・ペットをプラットフォーム別に見た別調査）では、美容の伸びてる側は冒頭Bが多め、という書き方だった。2026-10-07 の `accounts.csv` では美容の伸びてる最頻は「その他」（134件中73件、54%）。Bは伸び悩みの方が割合が高い（30件中12件、40% 対 134件中34件、25%）。テンプレートはこの CSV に従う。

## 参考4アカウントの再現（2026-10-04）

設計書は `reference-accounts/source/`。機械が読む型は `reference-accounts/templates/`。元の台詞とキャラはコピーしない。仕様の「推定」「不明」はそのまま。

制作シート:

```bash
python3 research/affi-templates/affi_reference.py feasibility
python3 research/affi-templates/affi_reference.py ab --id H1-1 --theme 髪の悩み
python3 research/affi-templates/affi_reference.py judge
```

使う Colab は上の1ページです。

投稿後の数字は `reference-accounts/results.csv` に手で入れる。空欄は0にしない。72時間後の値。1回に変える要素は1つ。

見た目は `reference-accounts/looks.yaml` の選択肢か、同じ形のYAML（例: `look.example.yaml`）。Colabでは話ごとに日本語の欄がある。迷ったら初期値のまま。選んだ話のセルだけがプロンプトに入る。
一覧に無い見た目は、その欄に短い文を直接書く。その文は全カットのプロンプトに入る。初期値は元アカウントの見た目ではない。
秒数・カット・字幕は型のまま。A/Bの見た目は両版で同じ。人物は成人のみ。実在の人や元アカウントに似せる指定は止まる。静止画は「選ぶ」の1欄。空なら T2V で、文章から絵を作る。ファイルがあるときは、その画像が FL2VA または I2V の最初のコマになる。

焼くジョブは「選ぶ」で「話でジョブを書く」にして「実行」するか、次で書く。話は「美容：材料のキャラ（the.care.logic）」「ドッグフード：犬（nuts0629）」「見守り：猫2匹の言い合い（junjun_ranran）」「婚活：男女の会話（yako.shiawasekon）」の1件。ドッグフードだけインタビュー・咀嚼・ダンス・会話を選ぶ。中身は「テンプレ」「オマージュ」「元の型のまま」の3つ。テーマと台詞は入っている。元の顔、元の台詞、曲名は入れない。静止画が空なら T2V で ready になる。書いた場所にファイルが無いときだけ `blocked`。「実行」と、下のコマンドは mp4 を焼かない。ノートの「焼く」が焼きます。投稿しない。15秒を超えるカットだけ生成を 5〜15 秒に分け、つなぎの長さは型の秒に戻す。5秒未満のカットは、生成を 5 秒にしてから型の秒で切る。中身を渡さない呼び出しで、台詞が「台詞は入力」のまま、テーマが「テーマは入力」のままのときも `blocked`。表の尺の帯では秒を変えない。表を見る、ではジョブを書かない。

ジョブに入るのは次の5つ。どれも型に書いてある事実だけ。元動画との一致率は測っていない。

1. 動作。型の絵とカメラを、H3 の英文にする。静止画が空のときは絵の位置を書かない。せりふ以外の日本語はプロンプトに入れない。テーマは `job["theme"]` に残し、声にはしない。
2. 声。型の声。せりふの日本語は、渡した1文だけを `<d>[Japanese] ...</d>` に入れる。
3. 口。その1文だけを口が言う。長いカットを分けた後半では、同じ文を繰り返さない。
4. 字幕。声と同じ文を `captions.json` に書く。型が字幕を焼かない話では焼かない。長いカットを分けたときは、声が出る最初の部分の秒に合わせる。
5. BGM。婚活のピアノだけ。曲名はコピーしない。曲なし・不明・トレンド・曲名は入力のまま、は足さない。

LoRA は FL2VA の Turbo（強さ 1.0、steps 9）と Motion Repair V2（強さ 0.6）。Larry と Combat は使わない。int8 の経路では LoRA は外れる。

「選ぶ」で「自分の文で1本」にすると、「実行」が自分で書いたプロンプトからコマンドを書きます。静止画が空なら `--task t2va` です。ファイルがあれば `--task i2va` で、その画像が最初のコマです。最後のコマは渡しません。mp4 は同じノートの一番下「焼く」で焼きます。別のノートは開きません。焼くはオフが初期値です。最初の1本だけがオンです。重みはマイドライブの `h3-weights`（fireworker06@gmail.com）です。無いときだけ「重みが無いとき落とす」を入れます。プレビューは 144.1GB です。オフなら落としません。投稿しません。

```bash
python3 research/affi-templates/affi_bake.py genre \
  --genre ドッグフード --theme 夕方の散歩 --out /tmp/affi-bake/dog
python3 research/affi-templates/affi_bake.py reference \
  --handle nuts0629 --mode dance --theme 夕方の散歩 \
  --image still.jpg --out /tmp/affi-bake/dance
```

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
python3 -m pytest research/affi-templates/test_affi_genre_templates.py research/affi-templates/test_affi_reference.py research/affi-templates/test_affi_bake.py -q
```
