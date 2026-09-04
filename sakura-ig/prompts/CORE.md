# リール根幹プロンプト

このファイルが映像の唯一の創作物。  
**サクラ専属自動投稿はここを書き換えない。** 日付の差分は `packets/` のスロットだけ。

組み立て順は常にこれ。

```
[lock.txt]
[wardrobe/<id>.txt]
[types/<type>.txt の STILL または VIDEO]
[packets の scene 1段落]
[negatives.txt]
```

動画の VIDEO ブロックの直前に `animate.txt` を足す。

モデルは動かさない。画像 `grok-imagine-image-2.0` / 9:16 / 2k。動画 `grok-imagine-video-1.5` / 9:16 / 720p / パケットの秒数。

---

## 守るルール（プロンプトを足す前に）

1. 一人。サクラ以外の顔を出さない
2. 成人。子ども・制服・「若い」を強調しない
3. 冒頭0.5秒は顔か布の動き。富士・鳥居・宇宙から始めない
4. 赤着物は記号。`signature_kimono: true` の日以外は `wardrobe/red_signature.txt` を使わない
5. 画面内テキストは英語短語だけ。日本語は焼かない
6. 音に歌詞を入れない。既存曲名を指定しない
7. 裸・性行為・水着・ベッドの性的演出は入れない
8. 他アカの映像を描写で再現しない

---

## 型の骨格（scene をはめる穴）

| type | 秒 | 冒頭0.5秒 | 動き | 終わり |
|---|---|---|---|---|
| question | 6 | 顔 | 瞬き＋視線 | 英語1語 |
| which-one | 6 | 2着の顔 | 左右が同時に呼吸 | Which? |
| micro-motion | 5 | 目か袖 | ビタ止め1つ | 余韻。文字なし可 |
| researcher | 8 | 帯か簪 | 寄りのティルト | 部位の英単語 |
| push-pull | 7 | 顔 | 引くか回る | 木曜だけ more on profile |
| season | 7 | 袖かうちわ | 季節の小道具1つ | Yukata / Formal |
| loop | 5 | 歩みか顔 | 最後が最初に戻る | 文字なし |

---

## キャプションの型

```
{日本語1文}。AI生成の成人モデルです。
{English one line}. AI-generated adult model.
{タグ 4〜6}
```

CTAがある日だけ、日本語の1文を `続きはプロフィール。` にする。リンクはバイオ。映像にURLを入れない。
