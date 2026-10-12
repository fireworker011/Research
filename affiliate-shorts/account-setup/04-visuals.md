# アイコンとバナー

絵は新規に作ります。いらすとやの素材、いらすとやのキャラクター、いらすとやの透かしは使いません。プロンプトに「いらすとや風」とは書きません。既存の絵柄を名前で指定すると、その絵が混ざることがあるためです。

文字は画像の中に描かせません。生成後に、下の「載せる文字」を中央へ載せます。日本語の文字は、生成器が崩すことが多いです。フォントは Noto Sans JP の太字で足ります。

YouTube のバナーの公式サイズは次のとおりです。出典は [チャンネルのブランディングを管理する](https://support.google.com/youtube/answer/10456525?hl=ja)。

- 推奨サイズは 2560×1440 ピクセル
- 最小アップロードサイズは 16:9 の 2048×1152 ピクセル
- 最小サイズにおける、文字とロゴの安全領域は 1235×338 ピクセル
- ファイルは 6MB 以下
- 影、枠線、フレームは足さない

アイコンの公式ピクセル数は、今回開いたバナーのヘルプにはありませんでした。正方形で作り、円に切られても顔が残るよう、モチーフは中央に置きます。

## 載せる文字

おすすめの名前を使うとき。

| 場所 | 文字 |
| --- | --- |
| アイコン | なし |
| バナー中央 | 会社員の金メモ |
| バナー中央の下 | 会社員のお金の短い話 |

他の候補を選んだときは、絵はそのまま、文字だけ次に替えます。

| 候補 | バナー中央 | 下の行 |
| --- | --- | --- |
| 明細のあと | 明細のあと | クレカと固定費の短い話 |
| 給料日の話 | 給料日の話 | 給料日のあとに残る金 |
| 固定費のメモ | 固定費のメモ | 会社員の家計の短い話 |
| ゆる金ショート | ゆる金ショート | お金の短い話 |

文字の色は `#243038`。バナーの地は `#F6F1E7`。安全領域の外には文字を置きません。

## アイコン用プロンプト

日本語:

```
正方形。オリジナルの平面イラスト。円い頭、短い黒髪、紺のスーツ、白いシャツの会社員が一人、うすい給与明細を持ち、少し驚いた顔。目は小さい点、口は短い横線。頬の赤みは一点だけ。背景は単色の生成り #F6F1E7。アクセントはくすんだ青 #3D5A80 を一点だけ。影なし、グラデーションなし、枠なし、文字なし、ロゴなし、透かしなし、署名なし。既存のフリー素材サイトのキャラクターや、有名なクリップアートの顔は使わない。顔と明細は中央60%に収める。
```

英語（生成器が英語のとき）:

```
Square image. Original flat illustration, one office worker with a round head, short black hair, navy suit, white shirt, holding a thin pay slip, slightly surprised. Dot eyes, a short straight mouth, one small blush mark. Solid warm paper background #F6F1E7, one muted blue accent #3D5A80. No shadow, no gradient, no border, no text, no logo, no watermark, no signature. Do not copy characters from any existing free-illustration library or famous clip-art face. Keep the face and the slip inside the center 60 percent.
```

## バナー用プロンプト

日本語:

```
横長 2560×1440。オリジナルの平面イラスト。左端に、アイコンと同じ会社員が小さく一人、机と薄い給与明細。中央から右は広い生成りの余白 #F6F1E7。くすんだ青 #3D5A80 は明細とネクタイだけ。影なし、グラデーションなし、枠なし、文字なし、ロゴなし、透かしなし。既存のフリー素材のキャラクターは使わない。人物は左端に寄せ、中央の横長の帯は空ける。
```

英語:

```
Wide image, 2560 by 1440. Original flat illustration. At the far left, the same office worker, small, at a desk with a thin pay slip. The center and right are a large empty warm-paper field #F6F1E7. Muted blue #3D5A80 only on the slip and the tie. No shadow, no gradient, no border, no text, no logo, no watermark. Do not copy characters from existing free-illustration libraries. Keep the person at the left edge and leave the center band empty for text added later.
```

生成後、バナーの中央の安全領域に、上の「載せる文字」を2行で載せます。アイコンには文字を載せません。
