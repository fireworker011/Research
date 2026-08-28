# IMAGE_PLAYBOOK — Web Imagine（APIキーが無い間）

sprint dump 用コピー（元 `cursor/video-channel-playbook-e013`）。秋バナー10枚は BANNER_LOG どおり製作済。Imagine で作り直すな。出品するな。

手足はこのファイルを上から実行する。市場リサーチの公開事実と、下の実測だけ。推論するな。品質を推論するな。売上予想を書くな。`agents/` 本文は直すな。

先に [BOX_MEMORY.md](BOX_MEMORY.md) を実行する。

判定は `通す` / `落とし` / `INSUFFICIENT` だけ。

円は全行 **無い**。ドルを円に換算するな。

---

## 0. 契約

| やる | やるな |
|---|---|
| 公開URLと実測だけを根拠にする | 公式に無いレシピを発明する |
| APIキーが無い間は **Web Imagine**（https://grok.com/imagine） | API を叩く（キーの手順は本ファイルに無い） |
| noteサムネの最終は **1280×670**（公式推奨を優先） | ナオミチの16:9指定で公式推奨を上書きする |
| 落とし3項（比率違い / 文字崩れ / 商標） | 「きれいさ」で落とす |

`research/` はこのブランチに無い。公開URLは本ファイルに置く。

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
| noteサムネ | **1280×670**（公式推奨を優先） |
| ナオミチ16:9 | **材料**。公式推奨を上書きしない |
| `agents/` 本文 | 直すな |
| 円 | 全行 **無い** |

---

## 2. 円

| 行 | 円 |
|---|---|
| grok-imagine-image-2.0 | **無い** |
| grok-imagine-image-quality（Quality Mode） | **無い** |
| Web Imagine の利用 | **無い** |
| note / YouTube の売上 | **無い** |
| 週次 usage pool の円換算 | **無い** |

公式のドルは §3。円列に足すな。

---

## 3. API（公開事実）

2つは別モデル。同一と書くな。

| 項目 | grok-imagine-image-2.0 | grok-imagine-image-quality（Quality Mode） |
|---|---|---|
| モデル名 | `grok-imagine-image-2.0` | `grok-imagine-image-quality`（別名 `grok-imagine-image-pro` 等） |
| Output | $0.04 / 枚 | $0.05 / 枚 |
| 円 | 無い | 無い |
| `quality` | `low` / `medium`。省略時 `medium`。**このパラメータは 2.0 のみ** | 公式モデルページに `quality=low/medium` は無い |
| 解像度 | `1k` / `2k`（生成ドキュメント。省略時 `1k`） | モデルページに 1k/2k の表は無い |
| n | 1–10（生成ドキュメント） | モデルページに n の表は無い |
| RPS | 6 | 6 |
| 公式が書く文言 | （生成ドキュメント） | Stronger text rendering / multilingual（ニュース） |
| 出典 | https://docs.x.ai/developers/models/grok-imagine-image-2.0 ／ https://docs.x.ai/developers/model-capabilities/images/generation | https://docs.x.ai/developers/models/grok-imagine-image-quality ／ https://x.ai/news/grok-imagine-quality-mode （May 6, 2026） |

APIキーが無い間は上を **叩かない**。Web Imagine を使う。

### 比率（生成ドキュメント。省略時 `auto`）

`16:9` `9:16` `1:1` `4:3` `3:4` `3:2` `2:3` `2:1` `1:2` `19.5:9` `9:19.5` `20:9` `9:20` `21:9` `5:2` `auto`

出典: https://docs.x.ai/developers/model-capabilities/images/generation

このリストに **1280×670** も **1.91:1** も無い。

### 回数

週次の共有 usage pool。Imagine 単独の枚数表は **無い**。

出典: https://docs.x.ai/grok/faq

### 落ちる条件（公式にあるもの）

| 条件 | 公式 | 出典 |
|---|---|---|
| モデレーションでフィルタ | ある | 生成ドキュメント `respect_moderation` ／ FAQ（NSFWを付けても moderation は残る。個別ルールは非公開） |
| 透かし | 付く。外す設定は無い。除去・改変・隠匿は AUP 禁止 | https://docs.x.ai/grok/faq ／ https://x.ai/legal/acceptable-use-policy |
| 720p 動画 | 上限後は 480p に落ちる | https://docs.x.ai/grok/faq 「Why did my 720p video come out at 480p?」 |
| Imagine のメモリ落ち条件 | **公式に無い** | |

### 日本語の文字

日本語 16:9 / 9:16 の Imagine **公式実物は無い**。ニュースの作例プロンプトは英語（例: "La Belle Vie"）。日本語サムネの公式見本URLは **INSUFFICIENT**。

Quality Mode ニュースは "Stronger text rendering" / "Clean, multilingual text capabilities" と書く。日本語 16:9/9:16 の実物ではない。

### 顔

「新しい顔を作るな」の **公式レシピは無い**。

公式にあるのは:

- 既存画像の **edit**（https://docs.x.ai/developers/model-capabilities/images/editing）
- 参照画像 **最大3枚**（https://docs.x.ai/developers/model-capabilities/images/multi-image-editing）

他人の顔・サクラ参照は確定制約で使わない。載せる既存画像が依頼に無いなら、参照なしで顔を新造するな。

---

## 4. 媒体の公式サイズ

| 媒体 | 公式 | 円 | 出典 |
|---|---|---|---|
| note 記事の見出し（サムネ） | **1280×670 px**。推奨と違うとトリミング。容量 10MB 以下 | 無い | https://www.help-note.com/hc/ja/articles/360000231642-%E7%99%BB%E9%8C%B2%E7%94%BB%E5%83%8F%E3%81%AE%E6%8E%A8%E5%A5%A8%E3%82%B5%E3%82%A4%E3%82%BA%E4%B8%80%E8%A6%A7 |
| note 見出しの比 | 1280÷670 = 1.91:1。**16:9ではない**（1280×9=11520、670×16=10720） | 無い | 上のピクセルから計算 |
| note クリエイター/マガジンヘッダーの推奨比率 | 1.91:1。基本 1280×670、より綺麗なら 1920×1006 | 無い | 同じヘルプ |
| YouTube 動画サムネ | 3840×2160、比 16:9。最小幅 640 | 無い | https://support.google.com/youtube/answer/72431 |
| YouTube Shorts サムネ | 2160×3840、比 9:16。最小高さ 640 | 無い | 同上 |
| YouTube サムネ容量（PC） | 50MB（video / Shorts / podcast） | 無い | 同上 |

note の仕事では 1280×670 を通す。16:9（ナオミチ）は材料。YouTube の 3840×2160 を note に使うな。

---

## 5. 実測（2026-08-26）

推論ではない。今夜測った値。note公式推奨の代わりにしない。

| 項目 | 値 |
|---|---|
| 生成ピクセル | 1536×1024 |
| 比 | 3:2（横） |
| 指定 | 9:16 を指定しても横で出た |
| その夜の処理 | 中央クロップで 16:9（1536×864 = 上下80px） |
| note公式との関係 | 1536×864 も 1536×1024 も **1280×670ではない** |

箱の同時障害は [BOX_MEMORY.md](BOX_MEMORY.md)。

---

## 6. 実行手順 — APIキーが無い間は Web Imagine

1. [BOX_MEMORY.md](BOX_MEMORY.md) の「開く前」を完了する。
2. ブラウザ1つで https://grok.com/imagine を開く。
3. **Image** を選ぶ（動画を頼まれていないなら Video にしない）。
4. 画面の表記（Speed / Quality (v2.0) 等）を記録する。この表記が `grok-imagine-image-quality` と同一である公式一文は **無い**。同一と書くな。APIキーが無いので Quality Mode API は使わない。
5. 比のドロップダウンを記録する。noteサムネの公式 1.91:1 はこのリストに無い。ドロップダウンを 16:9 にして公式推奨を捨てるな（16:9は材料）。
6. 参照画像: 依頼に既存画像が無いなら載せない。最大3は公式。サクラ・他人の顔は載せない。Headshot / Profile Picture / Character Sprite / Mascot Maker は顔・キャラ型なので押すな。
7. §8 のプロンプトを投げる。文を足すな。「高品質に」を足すな。
8. 保存する。公式: 生成URLは一時的。
9. 幅と高さを測る。測れなければ **INSUFFICIENT**。
10. §7 の順で見る。
11. Imagine を閉じてから次のサイトを1つ開く。

---

## 7. 落とし（この3つだけ）

| 項 | 通す | 落とし |
|---|---|---|
| 比率違い | **noteサムネ**なら最終が **1280×670**。YouTube動画サムネなら 3840×2160（16:9）。Shortsサムネなら 2160×3840（9:16） | 最終が上の公式サイズでない。測れない。noteを16:9で通す（公式推奨を捨てている） |
| 文字崩れ | 指定文字列と画像上の文字が1字も違わない | 欠・増・誤・読不能。指定が無いのに文字がある |
| 商標 | 読めるブランド名・ロゴ・®・™・商品の識別表示が無い | 1つでも読める。既存キャラ名が読める |

日本語 16:9/9:16 の公式実物は無い。照合は依頼文字列との1文字比較だけ。公式見本との見た目比較はするな。

透かしは公式どおり付く。外すな。落とし3項に入れない。

顔: 目・鼻・口が見えたら、新しい顔を作ったので通すな（確定制約）。公式の「顔なし人物レシピ」は無い。

---

## 8. 貼るプロンプト（noteサムネ）

Web Imagine に投げる。比 16:9 をプロンプトで固定するな（公式推奨は 1280×670 で、Imagine比リストに 1.91:1 は無い）。人物の公式レシピは無いので、顔を新造する文を足すな。参照画像も足すな。

文字列は依頼文があればそれを一字も変えず。無ければ note 初回SKUの題名（`ACCOUNT_NOTE.md`）だけ。980・月収は入れるな。

```
Still image. Wooden desk, closed notebook, ceramic mug, natural window light from the left. No people. No human faces. No celebrity. No named character.
Exact Japanese text on the image, spelled exactly:
「顔も声も出さない。Shortsを毎日1本出すための手順書」
No extra letters. No logos. No brand names. No trademarks. No product packaging with readable marks. No UI. No existing characters.
```

最終が 1280×670 でなければ §7 で落とす。Imagine出力を 1280×670 にする公式変換手順は **無い**（INSUFFICIENT）。勝手に16:9へクロップして通すな。

---

## 9. 返したら終わり（記録）

```
日付:
経路: Web Imagine（APIキー無し） / API（キーがファイルに無いので使うな）
画面の表記:
ドロップダウンの比:
指定文字列:
生成 W×H:
最終 W×H:
note 1280×670: はい / いいえ → いいえなら落とし（比率違い）
画像上の文字（書き写し）:
文字照合: 一致 / 落とし（文字崩れ）
目鼻口: 見えない / 見える → 見えるなら通すな
読めたブランド名・ロゴ: 無し / 有り → 落とし（商標）
円: 無い
判定: 通す / 落とし / INSUFFICIENT
```

投稿するな。出品するな。agents を直すな。

---

## 10. ナオミチ意見（材料。公式推奨と落とし条件に使わない）

「文字入れと人物が欲しい。品質が低い。mdをGitHubに置いて手足は読むだけ」  
「noteの比は16:9」（訂正）

16:9 は材料。noteサムネは公式 1280×670 を優先。  
「品質が低い」は落とし3項に変換しない。  
人物の公式レシピは無い。参照最大3の既存editだけが公式。

---

## 11. ファイルに無いもの（INSUFFICIENT）

- `research/` ディレクトリ（このブランチ）
- APIキー
- grok.com のボタンと `grok-imagine-image-quality` が同一である公式一文
- 日本語 16:9 / 9:16 の Imagine 公式実物
- 新しい顔を作らない公式レシピ
- Imagine比 1.91:1 / 1280×670
- Imagine出力を 1280×670 にする公式変換
- Imagine のメモリ落ち条件
- Imagine × タブ数（[BOX_MEMORY.md](BOX_MEMORY.md)）
- Imagine 単独の週間枚数表
- 円（全行無い）
