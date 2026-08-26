# IMAGE_PLAYBOOK — Imagine クオリティーモード2.0

手足はこのファイルを上から実行する。品質を推論するな。売上予想を書くな。`agents/` 本文は直すな。

先に [BOX_MEMORY.md](BOX_MEMORY.md) を実行する。ブラウザが2つある状態で Imagine を開くな。

判定は `通す` / `落とし` / `INSUFFICIENT` だけ。きれい・微妙・プロ級・低品質は書くな。

---

## 0. このファイルの契約

| やる | やるな |
|---|---|
| 下の手順どおり開く・選ぶ・投げる・測る・照合する | 手順に無い回避を発明する |
| 公開URLと今夜の実測だけを根拠にする | モデルの賢さで品質を語る |
| 落とし3項（比率違い / 文字崩れ / 商標）で捨てる | ナオミチ意見「品質が低い」を落とし条件にする |
| 顔が出たら落とす（新しい顔を作ったことになる） | 他人の顔・既存キャラ・サクラ参照・新しい顔を通す |
| 測った幅×高さを記録する | 数字が無い行を埋める |

`research/` ディレクトリはこのブランチに無い。公開事実のURLは本ファイルに置く。

---

## 1. 確定制約（司令部）

| 項目 | 値 |
|---|---|
| 法律 | 守る |
| 他人の顔 | 使わない |
| 商標 | 使わない |
| 既存キャラ | 使わない |
| 新しい顔 | 作るな |
| サクラの顔参照 | ここに使わない（`sakura-ig/refs/sakura-face.jpg` を開くな。アップロードするな） |
| note 今夜の比 | **16:9**（ナオミチ訂正。9:16ではない） |
| `agents/` 本文 | 直すな |
| 売上予想 | 書くな |

映像ショートの「文字なし・9:16」は `COMMON.md` の行。今夜の note 静止画は **本ファイルが上**。COMMON.md を直すな。agents を直すな。

---

## 2. 実測（2026-08-26）

推論ではない。今夜測った値だけ。

| 項目 | 値 |
|---|---|
| 生成ピクセル | **1536×1024** |
| 比 | 1536÷1024 = 3:2（横） |
| 指定 | 9:16 を指定しても横で出た |
| 今夜の note 向け処理 | 中央クロップで **16:9** |
| 3:2→16:9 の計算（幅を残す） | 目標高さ = 1536 × 9 ÷ 16 = **864**。上下カット = (1024 − 864) ÷ 2 = **80px ずつ**。結果 **1536×864**（1536×9 = 864×16） |
| 9:16原画を16:9にする手順 | **今夜の実測に無い → INSUFFICIENT** |

箱の同時障害は [BOX_MEMORY.md](BOX_MEMORY.md) の実測表。

---

## 3. 公開事実（URL）

取れなかった項は INSUFFICIENT。第三者ブログの「Qualityの方がきれい」は使わない。

| 事実 | 出典 |
|---|---|
| grok.com Imagine の画面に **Image / Speed / Quality (v2.0)** と比の表示がある。取得時の比表示は **2:3** | https://grok.com/imagine （2026-08-26 取得） |
| 同じページに Professional Headshot / Profile Picture / Character Sprite / Mascot Maker がある | 同上。顔・キャラ用。今夜は押すな |
| 同じページに Smart Resize がある | 同上。今夜の実測手順は中央クロップ。Smart Resize の結果は本ファイルに無い → **使うな** |
| API モデル名 `grok-imagine-image-2.0`。`aspect_ratio` 省略時は `auto`（モデルが比を選ぶ）。列に 16:9 / 9:16 / 3:2 / 2:3 がある | https://docs.x.ai/developers/model-capabilities/images/generation （最終更新 2026-08-21） |
| `quality` は `low` または `medium`。省略時 `medium`。このパラメータは `grok-imagine-image-2.0` のみ | 同上 |
| `resolution` は `1k`（省略時）または `2k` | 同上。1536×1024 という数値は公式ページに無い |
| 価格表（1K/2K × Low/Medium） | https://docs.x.ai/developers/models/grok-imagine-image-2.0 |
| 生成画像に Grok ウォーターマークがある。外す設定は無い。除去・改変・隠匿は AUP 禁止 | https://docs.x.ai/grok/faq |
| 著作権・商標の侵害、他人の publicity / なりすましを禁ずる | https://x.ai/legal/acceptable-use-policy （Effective: 2026-08-14） |
| ウェブは grok.com を Chrome / Chromium で | https://docs.x.ai/grok/faq 「What's the correct web address」 |
| note 記事の見出し画像 推奨 1280×670 px。推奨と違うとトリミングされる。容量 10MB 以下 | https://help.note.com/hc/ja/articles/360000231642-%E7%99%BB%E9%8C%B2%E7%94%BB%E5%83%8F%E3%81%AE%E6%8E%A8%E5%A5%A8%E3%82%B5%E3%82%A4%E3%82%BA%E4%B8%80%E8%A6%A7 |
| 1280×670 は 16:9 ではない（1280×9=11520、670×16=10720） | 上の推奨サイズから計算 |
| note メンバーシップ画像の推奨は 1280×720 px（16:9） | 同じヘルプ |
| 生成AIの出力が既存著作物と類似かつ依拠なら侵害になり得る。プロンプトに既存の題号・キャラ名を入れると依拠が推認されやすい | https://www.bunka.go.jp/seisaku/chosakuken/aiandcopyright.html ／ https://www.bunka.go.jp/seisaku/bunkashingikai/chosakuken/seisaku/r06_02/pdf/94089701_05.pdf |
| 肖像はみだりに利用されない（最高裁昭和44年12月24日大法廷・刑集23巻12号1625頁、最高裁平成17年11月10日第一小法廷・民集59巻9号2428頁を引用した公開判決文） | https://www.courts.go.jp/assets/hanrei/hanrei-pdf-81957.pdf |
| 商標は商品・サービスを区別するマーク。他人の登録商標と紛らわしい使用は侵害になり得る | https://www.jpo.go.jp/faq/yokuaru/trademark/shouhyou_seido_faq.html ／ https://www.bunka.go.jp/seisaku/chosakuken/kaizoku/faq.html |

公式が「クオリティーモード2.0は文字が正しい」とは書いていない。文字の正否は §8 の1文字照合だけ。

---

## 4. 実行手順 — クオリティーモード2.0

1. [BOX_MEMORY.md](BOX_MEMORY.md) の「開く前」を完了する。Canva と CrowdWorks は閉じる。
2. ブラウザを **1つ** だけ残し、https://grok.com/imagine を開く。
3. **Image** を選ぶ（動画を頼まれていないなら Video にしない）。
4. **Quality (v2.0)** を選ぶ。**Speed** のまま生成するな。
5. 比のドロップダウンを、今夜の note なら **16:9** にする。2:3 / 3:2 / 9:16 / 1:1 のままにするな。プロンプトに比を書くだけでは足りない（実測: 9:16指定でも 3:2 で出た）。
6. 押すな: Professional Headshot / Profile Picture / Character Sprite / Mascot Maker。顔または既存キャラ型。
7. 参照画像に顔を載せるな。サクラ参照を使うな。他人の写真をアップロードするな。
8. 下のプロンプト枠を、依頼の文字列だけ差し替えて投げる。文を足すな。「もっと高品質に」を足すな。
9. 1枚出たら保存する。URLは一時的（公式）。保存せずに次を開くな。
10. 幅と高さを測る。測れなければ **INSUFFICIENT**。通すな。
11. §5 の比、§6 の文字、§7 の顔、§8 の商標をこの順で見る。
12. 3:2（例: 1536×1024）で、用途が note 16:9 なら §5 の中央クロップだけやる。Smart Resize は使うな。
13. Imagine を閉じてから、次のサイトを1つだけ開く。

API を使うな（キーの手順は本ファイルに無い）。grok.com の画面だけ。

---

## 5. 比率

### 用途と指定比

| 用途 | 指定比 | 根拠 |
|---|---|---|
| note 今夜 | **16:9** | ナオミチ訂正 |
| note 公式 記事見出し | 1280×670（16:9ではない） | ヘルプ。今夜はこれに合わせるな |
| Shorts 映像 | 9:16 | COMMON.md。本ファイルの今夜の仕事ではない |
| 秋バナー | 比が本ファイルに無い | **INSUFFICIENT** |

### 測り方

幅を `W`、高さを `H` とする。

| 目標 | 通す条件 | 落とす条件 |
|---|---|---|
| 16:9 | `W × 9` と `H × 16` が等しい | 等しくない（クロップ前なら §5 の例外を見ろ） |

### クロップ（今夜の実測がある場合だけ）

原画が **3:2 横**（例: 1536×1024）で目標が **16:9** のときだけ、次を実行する。

1. 幅 `W` は変えない。
2. 目標高さ `H2 = W × 9 ÷ 16`（割り切れなければ通すな。1536 なら 864）。
3. 上下から `(H − H2) ÷ 2` を切る（1536×1024 なら 80px ずつ）。左右は切るな。
4. 結果で `W × 9 == H2 × 16` を再計算する。等しくなければ **落とし（比率違い）**。
5. 9:16 原画からの16:9化は実測が無い → **INSUFFICIENT**。切るな。
6. 1:1 原画からの16:9化は実測が無い → **INSUFFICIENT**。切るな。

プロンプトに 9:16 と書いてドロップダウンが 16:9 なら、ドロップダウンに従え（今夜の note）。

---

## 6. 文字入れ

### 文字列の出所

| 優先 | 使う文字 | 使うな |
|---|---|---|
| 1 | 依頼文に書かれた文字列を一字も変えず | 言い換え、要約、英訳 |
| 2 | 依頼に文字列が無く、仕事が note 初回SKUのときだけ `ACCOUNT_NOTE.md` の題名 **顔も声も出さない。Shortsを毎日1本出すための手順書** | 価格 980、月収、実績数字（ACCOUNT_NOTE.md 本文NG） |
| 3 | 上記が両方無い | **INSUFFICIENT**。題名を発明するな |

### プロンプトへの書き方

指定文字列を英語で説明せず、日本語を引用符のまま置く。

```
Exact Japanese text on the image, spelled exactly:
「（ここに文字列）」
No extra letters, no English translation of that sentence on the image.
```

### 検品（1文字）

1. 依頼（または上表）の文字列を書き写す。
2. 画像に読める文字を書き写す。読めない字は「読不能」と書く。
3. 一致しなければ **落とし（文字崩れ）**。
4. 1字でも欠ける・増える・濁点だけ違う・鏡文字・別漢字は崩れ。
5. 「たぶんこれ」と補完するな。読不能は崩れ。
6. 指定文字列が無いのに文字が乗っている → **落とし（文字崩れ）**。
7. Imagine の文字が崩れたあとの Canva 後載せは、本ファイルに手順が無い → **INSUFFICIENT**。推測で直すな。

---

## 7. 人物（新しい顔を作らない）

ナオミチ意見は「人物が欲しい」（材料）。通してよい人物は、顔が画面に出ないものだけ。

### 投げる前

| やる | やるな |
|---|---|
| 手元、後ろ姿、肩から下、顔はフレーム外 | 実在の人名 |
| `face out of frame` `no eyes, no nose, no mouth visible` | 既存キャラ名、作品名、マスコット名 |
| | 他人の写真・サクラ参照のアップロード |
| | Professional Headshot / Profile Picture / Character Sprite / Mascot Maker |
| | 「新しい顔を作れ」「架空の人物の顔」 |

顔が見える人物の通し方は本ファイルに無い → **INSUFFICIENT**。顔出しを通すな。

### プロンプトに必ず入れる（人物を入れる仕事のとき）

```
One person: hands and back of head only. Face out of frame. No eyes, no nose, no mouth visible. No celebrity. No named character. Do not invent a new identifiable face.
```

人物を入れない仕事なら、この3行は入れず `no people` にする。今夜の note はナオミチが人物を要求しているので入れる。

### 検品（顔）

目・鼻・口のどれかが見えたら **落とし**（新しい顔を作った）。他人の顔に似ていても落とす。後ろ姿だけなら顔項は通す。似てるかどうかの推論はするな。見えた器官だけで判定する。

---

## 8. 落とし品質（この3つだけ）

推論の「きれいさ」は見ない。ナオミチの「品質が低い」は §9。落とし条件にしない。

| 項 | 通す | 落とし |
|---|---|---|
| 比率違い | 最終ファイルが指定比（note 今夜は 16:9。`W×9 == H×16`） | 最終が指定比でない。測れない |
| 文字崩れ | 指定文字列と画像上の文字が1字も違わない | 欠・増・誤・読不能。指定が無いのに文字がある |
| 商標 | 読めるブランド名・ロゴ・®・™・商品パッケージの識別表示が無い | 1つでも読める。既存キャラの名称・特徴的外形が直接感得できる |

商標の見方（特許庁FAQ・文化庁FAQの公開事実に合わせる）: 企業のマーク、商品名、アプリの識別表示。一般名詞の「ノート」「マグカップ」は商標項で落とすな。読めない模様をロゴと推論するな。読めた文字がブランド名なら落とす。

既存キャラは文化庁チェックリストの「題号・キャラ名をプロンプトに入れるな」に合わせ、出力に既存キャラが直接感得できたら落とす。似てる気は推論。直接感得できる名称・耳とリボン等の固定特徴が同時に出たら落とす。

ウォーターマーク: 公式FAQどおり付く。外すな。落とし3項に入れない。外す回避は AUP 違反なので本ファイルは書かない。

---

## 9. 貼るプロンプト（note 今夜）

Quality (v2.0) と 16:9 を画面で選んだあと、次をそのまま投げる。括弧内だけ、依頼の文字列に差し替えてよい。足すな。

```
16:9 landscape still image. Wooden desk, closed notebook, ceramic mug, natural window light from the left. One person: hands and back of head only. Face out of frame. No eyes, no nose, no mouth visible. No celebrity. No named character. Do not invent a new identifiable face.
Exact Japanese text on the image, spelled exactly:
「顔も声も出さない。Shortsを毎日1本出すための手順書」
No extra letters. No logos. No brand names. No trademarks. No product packaging with readable marks. No UI. No existing characters.
```

---

## 10. 返したら終わり（記録）

この表だけ返す。空欄を感想で埋めるな。

```
日付:
URL: grok.com/imagine
モード: Quality (v2.0) / それ以外（それ以外なら通すな）
ドロップダウンの比:
指定文字列:
生成 W×H:
生成の W×9 と H×16:
クロップしたか: した（上下何px） / していない
最終 W×H:
最終 16:9: はい（W×9==H×16） / いいえ → 落とし（比率違い）
画像上の文字（書き写し）:
文字照合: 一致 / 落とし（文字崩れ）
目鼻口: 見えない / 見える → 落とし（新しい顔）
読めたブランド名・ロゴ: 無し / 有り（書いたもの）→ 落とし（商標）
判定: 通す / 落とし / INSUFFICIENT
```

投稿するな。出品するな。agents を直すな。

---

## 11. ナオミチ意見（材料。落とし条件に使わない）

「文字入れと人物が欲しい。品質が低い。mdをGitHubに置いて手足は読むだけ」

文字入れは §6、人物は §7 で実行する。「品質が低い」は落とし3項に変換しない。

---

## 12. ファイルに無いもの（INSUFFICIENT）

- `research/` ディレクトリ（このブランチ）
- grok.com のボタン表記と API の `quality=medium` が同一であることの公式一文
- 生成が必ず 16:9 になる保証（実測は 9:16指定でも 3:2）
- 1536×1024 を公式が「1k」と呼ぶことの公式一文
- Canva で文字を後載せする座標・フォント
- Smart Resize の結果
- 9:16 原画 → 16:9 のクロップ
- 顔が見える人物の通し方
- サクラ参照の使用
- Canva Error 9 の公式定義（[BOX_MEMORY.md](BOX_MEMORY.md)）
- どのSKUがいくらの売上になるか
