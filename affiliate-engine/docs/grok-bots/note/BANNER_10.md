# SKU2 製作ブリーフ — 秋の告知バナー10枚（出品するな）

出典: ACCOUNT_NOTE.md（2本目=秋の告知バナー10枚・価格欄980・未完成なら出さない） / IMAGE_PLAYBOOK.md（顔なし・商標なし・note 最終 1280×670）。
今夜は **製作のみ**。note に出さない。BOOTH に出さない。手順書と1記事同梱しない。980・月収は画像に書かない。

経路: APIキーがファイルに無い間は [Web Imagine](https://grok.com/imagine)。Canva 自作でも同じ落とし3項。

## 共通（10枚とも）

| 項 | 値 |
|---|---|
| 最終サイズ | **1280×670**（note 見出しの公式推奨。16:9で通すな） |
| 顔 | 目・鼻・口が見えたら通すな。人物を新造するな。参照画像を載せるな |
| 商標 | 読めるブランド名・ロゴ・®・™・既存キャラ名が1つでもあれば落とし |
| 文字 | 下の指定文字列と画像上の文字が1字も違わない。指定以外の文字は落とし |
| 価格・月収 | 画像に書くな。980は後の価格欄だけ |
| 円 | 無い |
| 出品 | するな |

Imagine の比リストに 1280×670 / 1.91:1 は無い。出力を測れなければ INSUFFICIENT。勝手に16:9へクロップして通すな。

貼るプロンプトの骨格（文字列だけ差し替える）:

```
Still image. Wooden desk, closed notebook, ceramic mug, natural window light from the left. Autumn indoor still life. No people. No human faces. No celebrity. No named character.
Exact Japanese text on the image, spelled exactly:
「（各枚の指定文字列）」
No extra letters. No logos. No brand names. No trademarks. No product packaging with readable marks. No UI. No existing characters.
```

机以外の小物を足す文は、各枚の「小物」列だけ。顔・商標・指定外の文字を足すな。「高品質に」を足すな。

## 10枚

| # | 指定文字列（一字も変えるな） | 小物（任意・文字なし） |
|---|---|---|
| 01 | 秋の告知 | 落ち葉が1枚、机の端 |
| 02 | 顔も声も出さない | 閉じたノートだけ |
| 03 | 毎日1本出す | 短い鉛筆 |
| 04 | 短尺のまま | 砂時計（ロゴなし） |
| 05 | 手順は別記事 | 付箋は無地 |
| 06 | 同じアカウント | 同じ色の2冊のノート |
| 07 | 未完成なら出さない | 蓋をした缶 |
| 08 | 続報 | 封をした封筒（宛名なし） |
| 09 | 準備中 | 空のフレーム |
| 10 | 公開は別判断 | 閉じた扉の取っ手だけ（顔なし） |

## 1枚ごとの記録（通すまで次へ進むな）

```
日付:
経路: Web Imagine（APIキー無し） / Canva
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
保存ファイル名: banner_01.png … banner_10.png（Git に画像を置くな。ローカルだけ）
```

完成枚数が 10 になるまで出品するな。完成は rest 条件ではない。公開URLは未出品のため INSUFFICIENT。

参謀記録: `BANNER_LOG.md`（2026-08-28・通す 10 / 出品していない）。PNG は Git に置くな。
