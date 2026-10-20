# もしも検証：大切な人のためなら、何日一人でいられますか

テキストのみ。動画も画像も生成していない。

- 出典スキル: [kaomei/stickman-video-director](https://github.com/kaomei/stickman-video-director) の `skills/directing-stickman-videos`
- 日付: 2026-10-20
- 画面: 縦 9:16
- 尺: 60秒（指定帯 30–60秒のうち、スキルの既定である10秒倍数）
- 音声: 日本語ナレーション。画面下字幕はナレーションと同一文。生成画像には文字を入れない
- 生成順: キャラクターシート → 参照スティル → カット静止画 → その静止画を始点にした image-to-video。text-to-video は使わない

## 制作ヘッダ

**英語タイトル:** How Many Days Could You Stay Alone for Someone You Love?

**日本語タイトル:** 大切な人のためなら、何日一人でいられますか

**核心:** 迎えはいつでも来る。食料も水も安全もある。本当に高いのは孤独そのものではなく、相手のメッセージを一通読むたびに、相手のために貯まる二日分が消えること。フードくんは最後まで、どちらのボタンも押さない。

**つかみ:** 無人島なのに、脱出ボタンは最初から手の届く場所にある。

**画面と尺と画風:** 縦 9:16、60秒。土台はスキルの Style 4（Cozy Storytelling／フルカラーの2Dアニメ背景、物語ごとのキャスト固定）。赤いニット帽の Style 2 にはしない。ユーザー指定の白いフードと、白い髪に緑の葉の女の子を、この話専用のキャストとして固定する。背景は砂浜、木の小屋、室内に限る。

**ナレーター（全編固定）:** 成人男性。標準的な日本語で、方言なし。中低音、澄んでいて、息漏れもしゃがれもない。胸に軽く響く。もしも検証の語りで、高さの揺れは小さめ、速度は一定、急がない。近い距離の乾いたスタジオ音。感情の起伏は画面と音楽が担い、声色はカットごとに変えない。登場人物のセリフにはしない。島や小屋の残響は環境音だけに置く。

英語の凍結ブロック（ナレーション収録用。画像プロンプトには声を入れない）:

```text
One off-screen adult male narrator throughout. Standard Japanese with no regional dialect, warm clean medium-low voice, gentle chest resonance, no raspiness or breathiness. Calm emotional documentary delivery, restrained pitch variation, steady speaking pace, and close, dry studio sound. Keep the same vocal timbre, register, accent, pace, and recording quality throughout. Emotional progression belongs to the visuals and music; do not change the narrator's voice or switch to character dialogue.
```

**色の役割（色コードは使わない）:**

- 琥珀: 帰還ボタン。いつでも出ていける自由
- 澄んだ青: メッセージのボタン。一通読むことの代価
- 葉の緑: 大切な人の印と、積立の瓶

背景は淡い砂色、明るい木、薄い青緑の海。彩度は背景を抑え、三つの印だけをはっきりさせる。

**BGM:** 同じ静かなピアノと、薄いパッド。テンポはゆったりで一定。最初のカットでモチーフを出し、以降は楽器もテンポも変えない。楽観的なサビには盛らない。積立が見えるところで音が一段だけ明るく触れ、最後は同じモチーフのまま細くする。効果音は波、コイン、ボタンの柔らかい光、布の擦れ。声を前に出す。

**感情の弧:** 問い → 安全だと分かって拍子抜け → 隠れたルール → 一通の代価に気づく → 押さないまま残る余韻。

**五段階:**

1. 黄金のつかみ（0:00.0–0:11.2）: 問いと、いつでも帰れる無人島
2. 前提を壊す（0:11.2–0:24.4）: サバイバルではない。食料、水、安全はある。つらいのは危険ではなく、誰も来ないこと
3. 内幕（0:24.4–0:39.0）: 本人は知らない。一日五万円。青いボタンは一通十万円、二日分
4. 真相（0:39.0–0:51.0）: 声が聞きたい。でもその一通は、相手の二日である
5. 余韻と問い（0:51.0–1:00.0）: どちらのボタンも押さない。視聴者に同じ問いを返す

**原典にある数字:** 一日残るごとに五万円。メッセージ一通は十万円で、二日分。これ以外の金額と、滞在した合計日数は置かない。「翌日」は「日を追う」を一回見せる演出で、何日目まで残ったかの記録ではない。

**葉の女の子の呼び方:** 制作上の識別名は Leaf-girl。ナレーションでは名前を付けず、「大切な人」「相手」だけを使う。島のカットには出さない。出てくるのは、積立を見せるカットアウェイだけ。

---

## 1. キャラクターシート

二人とも、全カットでこの見た目を一字も変えない。ポーズ、場所、カメラだけを変える。頭の形、線の太さ、フードの白、葉の位置をカットごとに描き直さない。

手足は常に二本ずつ。今のポーズだけを描き、動かす前の腕や足を残さない。関節はつながる。指は作り込まない。小さな丸い手にする。口は開けて話さない。ナレーションは画面外。

### フードくん

白いフードをかぶった、シンプルな棒人間。島に一人でいる主人公。

- 頭: 大きい白い円。フードの開口から顔だけ見える。フードの外に髪は出ない
- 顔: 小さい暗い楕円の目が二つ、短い直線の眉、小さな曲がった口。鼻、耳、歯、リアルな肌は無い
- 服: 無地の白いパーカー。フードは必ず上がっている。白い縁と、短い白い紐が二本。ロゴ、文字、模様、バッジは無い
- 胴: 白いパーカーの形。中は白く塗り、輪郭は暗い一色
- 腕: 暗い一本線がちょうど二本。袖口から出て、先は小さい暗い丸い手。線の太さは一定
- 足: 同じ太さの暗い一本線がちょうど二本。先は短い暗い足
- 比率: 頭が大きく、胴は短く、手足は細い。全身は頭四つ分くらい。この比率を全カットで揃える

凍結用の英語アンカー（フードくんが出る静止画プロンプトには、このブロックをそのまま繰り返す）:

```text
Hood-kun, identical in every image: a simple flat 2D anime stick-figure with a large round white head, a plain white hoodie with the hood fully up, a soft white hood rim around the face, and two short white drawstrings with no logos. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no hair outside the hood, no realistic skin. The torso is a simple white hoodie with solid white fill and a clean dark outline, no patterns, no text, no badges. Exactly two arms and exactly two legs. The arms are dark single-line strokes of constant medium weight, ending in small dark rounded hands. The legs are dark single-line strokes of the same weight, ending in short dark rounded feet. A moving limb replaces its previous pose and never leaves a second arm or leg behind. Proportions stay fixed: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.
```

### 葉の女の子

白い髪に、緑の葉が一つの女の子。棒人間系。大切な人。島にはいない。

- 頭: 大きい白い円。フードくんと同じ比率
- 髪: 真っ白で、肩までの直線、毛先は揃っている。色は白だけ
- 葉: シンプルな緑の葉が一つだけ。正面を向いたとき、画面左側の髪につける。斜めのときも、彼女自身の左側
- 顔: フードくんと同じく、小さい暗い楕円の目、短い眉、小さな口。鼻、耳、歯、リアルな肌は無い
- 服: 無地の白いノースリーブのワンピース。裾は膝の上。模様も文字も無い
- 手足: 暗い一本線。腕二本、足二本。小さい丸い手、短い足。線の太さはフードくんと同じ

凍結用の英語アンカー:

```text
Leaf-girl, identical in every image: a simple flat 2D anime stick-figure with a large round white head and straight white hair cut in a blunt shoulder-length shape. One single simple green leaf is tucked on the viewer's left side of her hair when she faces the camera, and on her own left side in three-quarter view. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no realistic skin, no second leaf, no hair color other than white. She wears a simple sleeveless white dress with solid white fill and a clean dark outline, hem above the knee, no patterns and no text. Exactly two arms and exactly two legs, dark single-line strokes of constant medium weight, small dark rounded hands, short dark rounded feet. A moving limb replaces its previous pose and never leaves a second limb behind. Proportions match Hood-kun: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.
```

### 小道具（見た目は固定、位置と状態だけが変わる）

- 帰還ボタン: 大きい丸い琥珀のボタン。柔らかい光。木の柱の上。文字も記号も数字も無い。島の砂浜にあり、最後まで押されない
- 青いボタン: 大きい丸い、澄んだ青のボタン。柔らかい光。低い木の台の上。文字も記号も数字も無い。小屋の卓上にあり、最後まで押されない
- 積立の瓶: 透明なガラス瓶。正面に緑の葉の印が一つ。文字は無い。中のコインは無地の金色の円盤で、数字は無い。小屋の中にあり、日が変わるにつれて増える。メッセージの代価を説明しても、この瓶からは減らさない
- 一通: 無地のクリーム色の封筒が一つ。宛名も切手の文字も無い
- 代価のコイン: 青いボタンの横に出る説明用の二列。押した支払いではなく、「一回で二日分が消える」ルールの図。光が抜けて輪郭だけになる。瓶のコインは残る

### 場所

- 砂浜: 淡い砂、薄い青緑の海、明るい空、木の小屋が一つ。船も、他の人の足跡も、動物も無い
- 小屋の室内: 明るい木の壁、簡単な卓、食料の入った木箱、透明な水の瓶、海の見える窓。ポスターも、文字のあるパッケージも無い
- 女の子の室内: 島とは別の、明るい木の床の部屋。無地の窓。低い棚。ポスターも、題名の見える本も、スマホも無い。C09 だけで使う

---

## 2. 参照スティル用プロンプト

物語のカットより先に、この四枚だけを作る。背景は無地。小道具は置かない。全身が切れずに入る。生成後、頭の大きさ、フードの白、葉の位置、線の太さが揃っているかを見てから、カットの静止画へ進む。

共通の禁止:

```text
Vertical 9:16 character reference still on a plain warm off-white background. Even soft light, full body visible including head and feet, centered, generous empty space around the figure. Flat clean 2D anime, no scenery, no props, no ground texture, no text, no letters, no watermark. No photorealistic skin, no extra limbs, no missing limbs, no disconnected joints.
```

### R1 フードくん正面

```text
Vertical 9:16 character reference still on a plain warm off-white background. Even soft light, full body visible including head and feet, centered, generous empty space around the figure. Flat clean 2D anime, no scenery, no props, no ground texture, no text, no letters, no watermark. No photorealistic skin, no extra limbs, no missing limbs, no disconnected joints.

Hood-kun, identical in every image: a simple flat 2D anime stick-figure with a large round white head, a plain white hoodie with the hood fully up, a soft white hood rim around the face, and two short white drawstrings with no logos. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no hair outside the hood, no realistic skin. The torso is a simple white hoodie with solid white fill and a clean dark outline, no patterns, no text, no badges. Exactly two arms and exactly two legs. The arms are dark single-line strokes of constant medium weight, ending in small dark rounded hands. The legs are dark single-line strokes of the same weight, ending in short dark rounded feet. A moving limb replaces its previous pose and never leaves a second arm or leg behind. Proportions stay fixed: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.

Pose: standing front view, facing the camera, both arms relaxed at his sides, both feet together, neutral tiny mouth. This is an identity reference, not a story frame.
```

### R2 フードくん斜め

```text
Vertical 9:16 character reference still on a plain warm off-white background. Even soft light, full body visible including head and feet, centered, generous empty space around the figure. Flat clean 2D anime, no scenery, no props, no ground texture, no text, no letters, no watermark. No photorealistic skin, no extra limbs, no missing limbs, no disconnected joints.

Hood-kun, identical in every image: a simple flat 2D anime stick-figure with a large round white head, a plain white hoodie with the hood fully up, a soft white hood rim around the face, and two short white drawstrings with no logos. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no hair outside the hood, no realistic skin. The torso is a simple white hoodie with solid white fill and a clean dark outline, no patterns, no text, no badges. Exactly two arms and exactly two legs. The arms are dark single-line strokes of constant medium weight, ending in small dark rounded hands. The legs are dark single-line strokes of the same weight, ending in short dark rounded feet. A moving limb replaces its previous pose and never leaves a second arm or leg behind. Proportions stay fixed: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.

Pose: three-quarter view turned toward the viewer's right, standing, both arms at his sides, both feet visible. The white hood, drawstrings, face marks, and proportions match the front reference exactly. This is an identity reference, not a story frame.
```

### R3 葉の女の子正面

```text
Vertical 9:16 character reference still on a plain warm off-white background. Even soft light, full body visible including head and feet, centered, generous empty space around the figure. Flat clean 2D anime, no scenery, no props, no ground texture, no text, no letters, no watermark. No photorealistic skin, no extra limbs, no missing limbs, no disconnected joints.

Leaf-girl, identical in every image: a simple flat 2D anime stick-figure with a large round white head and straight white hair cut in a blunt shoulder-length shape. One single simple green leaf is tucked on the viewer's left side of her hair when she faces the camera, and on her own left side in three-quarter view. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no realistic skin, no second leaf, no hair color other than white. She wears a simple sleeveless white dress with solid white fill and a clean dark outline, hem above the knee, no patterns and no text. Exactly two arms and exactly two legs, dark single-line strokes of constant medium weight, small dark rounded hands, short dark rounded feet. A moving limb replaces its previous pose and never leaves a second limb behind. Proportions match Hood-kun: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.

Pose: standing front view, facing the camera, both arms relaxed at her sides, both feet together, neutral tiny mouth. The single green leaf is on the viewer's left. This is an identity reference, not a story frame.
```

### R4 葉の女の子斜め

```text
Vertical 9:16 character reference still on a plain warm off-white background. Even soft light, full body visible including head and feet, centered, generous empty space around the figure. Flat clean 2D anime, no scenery, no props, no ground texture, no text, no letters, no watermark. No photorealistic skin, no extra limbs, no missing limbs, no disconnected joints.

Leaf-girl, identical in every image: a simple flat 2D anime stick-figure with a large round white head and straight white hair cut in a blunt shoulder-length shape. One single simple green leaf is tucked on the viewer's left side of her hair when she faces the camera, and on her own left side in three-quarter view. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no realistic skin, no second leaf, no hair color other than white. She wears a simple sleeveless white dress with solid white fill and a clean dark outline, hem above the knee, no patterns and no text. Exactly two arms and exactly two legs, dark single-line strokes of constant medium weight, small dark rounded hands, short dark rounded feet. A moving limb replaces its previous pose and never leaves a second limb behind. Proportions match Hood-kun: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.

Pose: three-quarter view turned toward the viewer's left, standing, both arms at her sides, both feet visible. The single green leaf stays on her own left side. Hair, dress, face marks, and proportions match the front reference exactly. This is an identity reference, not a story frame.
```

---

## 3. 台本

日本語が収録する本文。字幕は各行と同一で、画面下の安全域に置く。生成画像には字幕を描かない。行と行の空きはすべて 1.5秒以内。最後の行のあと、1:00.0 までは同じ字幕を残して絵を止める。これは行間の空きではなく、最後の余韻。

読みの速さは、もしも検証の語りで急がない程度（おおよそ一秒に七から八モーラ）。行の長さはその範囲に合わせてある。

| 行 | タイムコード | 行間 | ナレーション（字幕も同じ） | 英語参考訳（収録しない） |
|---|---|---|---|---|
| L1 | 0:00.0–0:03.4 | — | 大切な人のためなら、何日、一人でいられますか。 | For someone you love, how many days could you stay alone? |
| L2 | 0:04.0–0:07.0 | 0.6秒 | 無人島に、フードくんが一人で残っています。 | Hood-kun has been left alone on a deserted island. |
| L3 | 0:07.6–0:10.6 | 0.6秒 | 帰還ボタンを押せば、いつでも迎えが来ます。 | If he presses the return button, a rescue comes whenever he wants. |
| L4 | 0:11.2–0:14.4 | 0.6秒 | 小屋には食料と水があり、安全も確認済みです。 | The hut has food and water, and it has already been checked as safe. |
| L5 | 0:15.0–0:17.6 | 0.6秒 | スマホも、娯楽も、ありません。 | There is no phone, and nothing to entertain him. |
| L6 | 0:18.2–0:20.6 | 0.6秒 | これは、我慢くらべじゃありません。 | This is not a contest of endurance. |
| L7 | 0:21.2–0:23.8 | 0.6秒 | 危険は無い。ただ、誰も来ないだけです。 | There is no danger. It is only that nobody comes. |
| L8 | 0:24.4–0:27.4 | 0.6秒 | 本人はまだ知りません。一日残るごとに、 | He does not know this yet. For every day he stays, |
| L9 | 0:27.8–0:30.8 | 0.4秒 | 大切な人へ、五万円が積み立てられます。 | Fifty thousand yen is set aside for the person he loves. |
| L10 | 0:31.4–0:34.8 | 0.6秒 | 青いボタンで、相手のメッセージが一通読めます。 | The blue button lets him read one message from that person. |
| L11 | 0:35.4–0:38.4 | 0.6秒 | ただし一回、十万円。二日分が消えます。 | But one press costs one hundred thousand yen. Two days disappear. |
| L12 | 0:39.0–0:42.6 | 0.6秒 | 翌日。フードくんは青いボタンに指を伸ばし、止めます。 | The next day, Hood-kun reaches for the blue button and stops. |
| L13 | 0:43.2–0:46.4 | 0.6秒 | 声が聞きたい。でもその一通は、相手の二日です。 | He wants to hear their voice. But that one message is two days of theirs. |
| L14 | 0:47.0–0:50.4 | 0.6秒 | 日が暮れ、また明けても、積立だけが増えていきます。 | The sun sets and rises again, and only the savings keep growing. |
| L15 | 0:51.0–0:54.2 | 0.6秒 | フードくんは、どちらのボタンも押しません。 | Hood-kun presses neither button. |
| L16 | 0:55.0–0:58.2 | 0.8秒 | あなたなら、何日目で、青を押しますか。 | On which day would you press the blue one? |
| 余韻 | 0:58.2–1:00.0 | 最終行の保持 | （L16 の字幕を残す。新しい行は入れない） | Hold the last line. |

字幕: 白文字、細い暗い縁、画面下から約8%上げた位置、中央揃え、一行。ボタンや手や顔を字幕帯に置かない。

---

## 4. ショットリスト

一行につき一カット。その行が言っているものだけを画面に置く。秒は、その行の開始から次の行の開始まで。最後のカットだけ 1:00.0 まで。

| カット | 秒 | 段階 | 場所 | 画面にあるもの | 行 |
|---|---|---|---|---|---|
| C01 | 0:00.0–0:04.0（4.0秒） | つかみ | 砂浜 | 無人の砂浜、奥に木の小屋、フードくんが一人、手前に未押下の琥珀の帰還ボタン | L1 |
| C02 | 0:04.0–0:07.6（3.6秒） | つかみ | 砂浜 | フードくんの全身。周囲の砂浜に誰もいない | L2 |
| C03 | 0:07.6–0:11.2（3.6秒） | つかみ | 砂浜 | 琥珀の帰還ボタンの寄り。フードくんの手が届く直前で止まっている。押していない | L3 |
| C04 | 0:11.2–0:15.0（3.8秒） | 前提を壊す | 小屋 | 食料の木箱と水の瓶。窓の外は穏やかな海。フードくんがそれを見ている | L4 |
| C05 | 0:15.0–0:18.2（3.2秒） | 前提を壊す | 小屋 | 何も乗っていない棚。スマホも本もゲームも無い。フードくんが見ている | L5 |
| C06 | 0:18.2–0:21.2（3.0秒） | 前提を壊す | 小屋 | フードくんが床に座っている。汗も鎖も重りも無い。苦しむ絵にはしない | L6 |
| C07 | 0:21.2–0:24.4（3.2秒） | 前提を壊す | 小屋の窓 | 穏やかな海。嵐も獣も無い。フードくんは窓辺に立っている | L7 |
| C08 | 0:24.4–0:27.8（3.4秒） | 内幕 | 小屋 | フードくんは窓を見たまま。背後の木箱の陰に、葉印のコイン瓶が少し見える。視線は瓶に向いていない | L8 |
| C09 | 0:27.8–0:31.4（3.6秒） | 内幕 | 女の子の室内／小屋 | 画面を上下に分ける。上は葉の女の子が自分の部屋の窓辺にいる。下は小屋の瓶にコインが積まれる。島に二人はいない | L9 |
| C10 | 0:31.4–0:35.4（4.0秒） | 内幕 | 小屋 | 卓上の青いボタンと、文字の無い封筒が一通。手はボタンに触れていない | L10 |
| C11 | 0:35.4–0:39.0（3.6秒） | 内幕 | 小屋 | 青いボタンの横で、説明用のコイン二列が輪郭だけになる。奥の瓶のコインは減らない | L11 |
| C12 | 0:39.0–0:43.2（4.2秒） | 真相 | 小屋・朝 | 朝の光。フードくんの片手が青いボタンへ伸び、触れる前に止まる | L12 |
| C13 | 0:43.2–0:47.0（3.8秒） | 真相 | 小屋 | 手は体側に戻っている。顔の寄り。奥に封筒一通と、消えた二列の輪郭が残る | L13 |
| C14 | 0:47.0–0:51.0（4.0秒） | 真相 | 小屋の窓 | 窓の光が夕方から朝へ移る。瓶のコインだけが増える。ボタンは押されない | L14 |
| C15 | 0:51.0–0:55.0（4.0秒） | 余韻 | 砂浜と小屋口 | 手前に琥珀の帰還ボタン、戸口の奥に青いボタン。フードくんは間に立ち、両手を下ろしている | L15 |
| C16 | 0:55.0–1:00.0（5.0秒） | 余韻 | 青いボタン | 青いボタンへの縦の寄り。手は下で止まったまま、触れていない | L16 |

### 10秒単位の絵コンテ

スキルの五行と、約10秒のまとまり。カットの境はセリフの空きに合わせたので、秒数は 8秒から12秒の幅がある。

| 時間 | 叙事 | 画面の流れ | 動きとつなぎ | 日本語ナレーション | BGM / 効果音 |
|---|---|---|---|---|---|
| 0:00.0–0:11.2 | つかみ。脱出できる無人島 | C01 引きの砂浜 → C02 一人の全身 → C03 琥珀ボタン | 空からボタンまで降りる。手はボタンの手前で止まる。次は、彼がその手を小屋の入口へ向ける | L1–L3 | ピアノのモチーフ開始。波。ボタンの柔らかい光 |
| 0:11.2–0:24.4 | 前提を壊す。生存の試練ではない | C04 食料と水 → C05 空の棚 → C06 ただ座る → C07 穏やかな海 | 同じ室内を横に見渡し、床へ降り、窓へ戻る。苦行の記号は出さない。次は、彼の背後を見せる | L4–L7 | 同じピアノとパッド。棚に何も置かれない静けさ |
| 0:24.4–0:39.0 | 内幕。五万円と、一通の代価 | C08 知らないまま窓 → C09 女の子と瓶 → C10 青いボタンと封筒 → C11 二列が消える図 | 瓶を本人の視線の外に出す。女の子は別の部屋。支払いはまだ起きない。次は朝の光で同じ卓 | L8–L11 | 同じテンポ。コインの音。瓶は減らさない |
| 0:39.0–0:51.0 | 真相。一通は相手の二日 | C12 手が伸びて止まる → C13 手が戻る → C14 夕日から朝、瓶だけ増える | 時間のジャンプは C12 の朝と C14 の光の移動だけ。ボタンの状態は未押下のまま次の戸口へ | L12–L14 | 同じモチーフ。布の擦れ。朝の光に合わせて一段だけ明るい |
| 0:51.0–1:00.0 | 余韻。押さない、と問い返す | C15 二つのボタンの間 → C16 青いボタンの寄り | 両手は下がったまま。最後は青へ寄るが、手は触れない。字幕の問いを残して 1:00.0 で終わる | L15–L16 | 同じモチーフのまま細くする。波だけ残る |

### カットのつながり

- C01 の砂浜、小屋、琥珀ボタン、フードくんの白フード → C02 は同じ砂浜を本人へ寄る。ボタンは端に残す
- C02 の本人 → C03 は同じ琥珀ボタンへ寄る。手は押さずに止まる
- C03 の止まっている手 → C04 は小屋の入口を通って室内の食料と水へ。時間は同じ日
- C04 の室内 → C05 は同じ部屋の空の棚へパン
- C05 の空の棚 → C06 は同じ棚を背景に、床へ座る
- C06 の室内 → C07 は同じ窓の穏やかな海。始まりの静止画はすでに窓辺
- C07 の後ろ姿 → C08 はカメラだけが背後へ回り、隠れた瓶を見せる。本人は振り向かない
- C08 の瓶 → C09 は上下二分割。下は同じ瓶、上は別の部屋の女の子。場所のカットアウェイで、島に彼女を出さない
- C09 の瓶 → C10 は小屋の卓へ戻る。瓶は奥に残し、青いボタンと封筒を出す
- C10 の青いボタンと封筒 → C11 は同じ卓。説明用の二列だけが消え、瓶は減らない
- C11 の未押下の青 → C12 は朝への時間ジャンプ。同じ卓、同じボタン
- C12 の伸びた手 → C13 はその手が体側へ戻った顔の寄り。封筒と二列の輪郭は残す
- C13 の未押下 → C14 は同じ窓で夕方から朝へ。瓶だけが増える
- C14 の増えた瓶と未押下の青 → C15 は外へ出て、琥珀ボタンと戸口の青の間に立つ
- C15 の青 → C16 はその青いボタンへ縦に寄る。手は触れたままにしない

---

## 5. カット別プロンプト

静止画が先、その画像を一枚目にした image-to-video が後。text-to-video は使わない。モデル名は書かない。

各静止画の共通条件:

```text
Vertical 9:16 story still. Clean flat 2D anime background, soft daylight, simple shapes, gentle shadows. Match the approved character reference stills exactly. Leave the bottom fifth of the frame empty of faces, hands, and important props. No text, no letters, no numbers, no logos, no watermarks, no speech bubbles, no captions, no subtitles. No photorealistic humans, no 3D skin, no extra limbs, no missing limbs, no disconnected joints, no duplicate bodies, no melted hands. No other people unless this cut names Leaf-girl.
```

image-to-video の共通条件:

```text
Image-to-video only. Use the approved still of this cut as the first frame. Do not redesign the character, the hoodie, the leaf, the line weight, or the proportions. Do not switch to text-to-video. Do not add speech, lip sync, captions, subtitles, letters, or numbers. Exactly two arms and two legs; a moving limb replaces its old pose. No extra fingers, no broken joints, no morphing of the body into another shape. Ambient motion and camera only, plus the one action named below.
```

ナレーションと BGM は編集で載せる。動画プロンプトの中では話させない。

### C01 砂浜の問い（4.0秒）

画面: 無人島の引き。フードくん一人。琥珀の帰還ボタンは未押下。

静止画:

```text
Vertical 9:16 story still. Clean flat 2D anime background, soft daylight, simple shapes, gentle shadows. Match the approved character reference stills exactly. Leave the bottom fifth of the frame empty of faces, hands, and important props. No text, no letters, no numbers, no logos, no watermarks, no speech bubbles, no captions, no subtitles. No photorealistic humans, no 3D skin, no extra limbs, no missing limbs, no disconnected joints, no duplicate bodies, no melted hands. No other people unless this cut names Leaf-girl.

Hood-kun, identical in every image: a simple flat 2D anime stick-figure with a large round white head, a plain white hoodie with the hood fully up, a soft white hood rim around the face, and two short white drawstrings with no logos. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no hair outside the hood, no realistic skin. The torso is a simple white hoodie with solid white fill and a clean dark outline, no patterns, no text, no badges. Exactly two arms and exactly two legs. The arms are dark single-line strokes of constant medium weight, ending in small dark rounded hands. The legs are dark single-line strokes of the same weight, ending in short dark rounded feet. A moving limb replaces its previous pose and never leaves a second arm or leg behind. Proportions stay fixed: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.

Setting: a clean anime beach, pale sand, soft turquoise water, bright clear sky, one small wooden hut, no boats, no other footprints, no animals. A large round amber button with a soft warm glow sits on a plain wooden post in the lower midground, above the empty subtitle area, with no letters and no symbols. Hood-kun stands alone in the midground, small in the wide vertical frame, facing the sea, both arms at his sides. The hut is behind him. He is the only person.
```

i2v:

```text
Image-to-video only. Use the approved still of this cut as the first frame. Do not redesign the character, the hoodie, the leaf, the line weight, or the proportions. Do not switch to text-to-video. Do not add speech, lip sync, captions, subtitles, letters, or numbers. Exactly two arms and two legs; a moving limb replaces its old pose. No extra fingers, no broken joints, no morphing of the body into another shape. Ambient motion and camera only, plus the one action named below.

Duration 4.0 seconds. The camera slowly lowers from the sky to Hood-kun and then to the amber return button. Hood-kun takes one small step toward the sea and stops, arms staying at his sides. The button is not pressed. End with the glowing amber button still unpressed in the lower midground, and Hood-kun still alone.
```

### C02 一人である（3.6秒）

画面: 同じ砂浜で、フードくんの全身。誰もいない。

静止画:

```text
Vertical 9:16 story still. Clean flat 2D anime background, soft daylight, simple shapes, gentle shadows. Match the approved character reference stills exactly. Leave the bottom fifth of the frame empty of faces, hands, and important props. No text, no letters, no numbers, no logos, no watermarks, no speech bubbles, no captions, no subtitles. No photorealistic humans, no 3D skin, no extra limbs, no missing limbs, no disconnected joints, no duplicate bodies, no melted hands. No other people unless this cut names Leaf-girl.

Hood-kun, identical in every image: a simple flat 2D anime stick-figure with a large round white head, a plain white hoodie with the hood fully up, a soft white hood rim around the face, and two short white drawstrings with no logos. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no hair outside the hood, no realistic skin. The torso is a simple white hoodie with solid white fill and a clean dark outline, no patterns, no text, no badges. Exactly two arms and exactly two legs. The arms are dark single-line strokes of constant medium weight, ending in small dark rounded hands. The legs are dark single-line strokes of the same weight, ending in short dark rounded feet. A moving limb replaces its previous pose and never leaves a second arm or leg behind. Proportions stay fixed: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.

Setting: the same clean anime beach and the same wooden hut. Full-body Hood-kun centered, standing, looking slightly to one side at the empty sand. The amber return button remains partly visible at the frame edge, unpressed. No second person anywhere on the beach.
```

i2v:

```text
Image-to-video only. Use the approved still of this cut as the first frame. Do not redesign the character, the hoodie, the leaf, the line weight, or the proportions. Do not switch to text-to-video. Do not add speech, lip sync, captions, subtitles, letters, or numbers. Exactly two arms and two legs; a moving limb replaces its old pose. No extra fingers, no broken joints, no morphing of the body into another shape. Ambient motion and camera only, plus the one action named below.

Duration 3.6 seconds. Hood-kun turns his head from left to right, looking across the empty beach. The camera eases slightly closer. Nobody enters. End on his full body, still alone, with the hut and the unpressed amber button still in frame.
```

### C03 帰還ボタン（3.6秒）

画面: 琥珀のボタン。手は触れる前で止まる。

静止画:

```text
Vertical 9:16 story still. Clean flat 2D anime background, soft daylight, simple shapes, gentle shadows. Match the approved character reference stills exactly. Leave the bottom fifth of the frame empty of faces, hands, and important props. No text, no letters, no numbers, no logos, no watermarks, no speech bubbles, no captions, no subtitles. No photorealistic humans, no 3D skin, no extra limbs, no missing limbs, no disconnected joints, no duplicate bodies, no melted hands. No other people unless this cut names Leaf-girl.

Hood-kun, identical in every image: a simple flat 2D anime stick-figure with a large round white head, a plain white hoodie with the hood fully up, a soft white hood rim around the face, and two short white drawstrings with no logos. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no hair outside the hood, no realistic skin. The torso is a simple white hoodie with solid white fill and a clean dark outline, no patterns, no text, no badges. Exactly two arms and exactly two legs. The arms are dark single-line strokes of constant medium weight, ending in small dark rounded hands. The legs are dark single-line strokes of the same weight, ending in short dark rounded feet. A moving limb replaces its previous pose and never leaves a second arm or leg behind. Proportions stay fixed: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.

Close vertical framing on the large round amber return button on its wooden post, soft warm glow, no letters and no symbols. Hood-kun's right hand hovers a short distance above the button and does not touch it. His other arm stays down. Part of his same white hood and face is visible at the top of the frame. The button is unpressed.
```

i2v:

```text
Image-to-video only. Use the approved still of this cut as the first frame. Do not redesign the character, the hoodie, the leaf, the line weight, or the proportions. Do not switch to text-to-video. Do not add speech, lip sync, captions, subtitles, letters, or numbers. Exactly two arms and two legs; a moving limb replaces its old pose. No extra fingers, no broken joints, no morphing of the body into another shape. Ambient motion and camera only, plus the one action named below.

Duration 3.6 seconds. Hood-kun's right hand moves a little closer to the amber button, then stops short of contact. The other arm does not rise. The button's glow pulses once. He does not press it. End on the unpressed button and the stopped hand.
```

### C04 食料と水と安全（3.8秒）

画面: 小屋の中。食料、水、穏やかな海。

静止画:

```text
Vertical 9:16 story still. Clean flat 2D anime background, soft daylight, simple shapes, gentle shadows. Match the approved character reference stills exactly. Leave the bottom fifth of the frame empty of faces, hands, and important props. No text, no letters, no numbers, no logos, no watermarks, no speech bubbles, no captions, no subtitles. No photorealistic humans, no 3D skin, no extra limbs, no missing limbs, no disconnected joints, no duplicate bodies, no melted hands. No other people unless this cut names Leaf-girl.

Hood-kun, identical in every image: a simple flat 2D anime stick-figure with a large round white head, a plain white hoodie with the hood fully up, a soft white hood rim around the face, and two short white drawstrings with no logos. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no hair outside the hood, no realistic skin. The torso is a simple white hoodie with solid white fill and a clean dark outline, no patterns, no text, no badges. Exactly two arms and exactly two legs. The arms are dark single-line strokes of constant medium weight, ending in small dark rounded hands. The legs are dark single-line strokes of the same weight, ending in short dark rounded feet. A moving limb replaces its previous pose and never leaves a second arm or leg behind. Proportions stay fixed: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.

Interior of a small clean wooden hut, light wood walls, one window onto a calm beach. A wooden crate holds plain bread and simple fruit with no labels. A clear water jug sits beside it, no label. Hood-kun stands looking at the crate and the jug, both arms relaxed, both feet on the floor. The room is tidy and brightly lit, with no damage and no storm outside.
```

i2v:

```text
Image-to-video only. Use the approved still of this cut as the first frame. Do not redesign the character, the hoodie, the leaf, the line weight, or the proportions. Do not switch to text-to-video. Do not add speech, lip sync, captions, subtitles, letters, or numbers. Exactly two arms and two legs; a moving limb replaces its old pose. No extra fingers, no broken joints, no morphing of the body into another shape. Ambient motion and camera only, plus the one action named below.

Duration 3.8 seconds. The camera drifts from the food crate to the water jug. Hood-kun nods once while looking at them. Both arms stay relaxed. The sea outside the window stays calm. End with both the food and the water still visible, and Hood-kun still inside the safe hut.
```

### C05 何も無い棚（3.2秒）

画面: 空の棚。スマホも娯楽も無い。

静止画:

```text
Vertical 9:16 story still. Clean flat 2D anime background, soft daylight, simple shapes, gentle shadows. Match the approved character reference stills exactly. Leave the bottom fifth of the frame empty of faces, hands, and important props. No text, no letters, no numbers, no logos, no watermarks, no speech bubbles, no captions, no subtitles. No photorealistic humans, no 3D skin, no extra limbs, no missing limbs, no disconnected joints, no duplicate bodies, no melted hands. No other people unless this cut names Leaf-girl.

Hood-kun, identical in every image: a simple flat 2D anime stick-figure with a large round white head, a plain white hoodie with the hood fully up, a soft white hood rim around the face, and two short white drawstrings with no logos. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no hair outside the hood, no realistic skin. The torso is a simple white hoodie with solid white fill and a clean dark outline, no patterns, no text, no badges. Exactly two arms and exactly two legs. The arms are dark single-line strokes of constant medium weight, ending in small dark rounded hands. The legs are dark single-line strokes of the same weight, ending in short dark rounded feet. A moving limb replaces its previous pose and never leaves a second arm or leg behind. Proportions stay fixed: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.

Same hut interior. A bare wooden shelf fills the upper midground. The shelf is empty: no phone, no books, no games, no screen. Hood-kun stands looking at the empty shelf, calm, both arms at his sides. The food crate remains small in the background so this is the same room.
```

i2v:

```text
Image-to-video only. Use the approved still of this cut as the first frame. Do not redesign the character, the hoodie, the leaf, the line weight, or the proportions. Do not switch to text-to-video. Do not add speech, lip sync, captions, subtitles, letters, or numbers. Exactly two arms and two legs; a moving limb replaces its old pose. No extra fingers, no broken joints, no morphing of the body into another shape. Ambient motion and camera only, plus the one action named below.

Duration 3.2 seconds. The camera slides from the food crate onto the bare shelf. Hood-kun's gaze follows the empty shelf from one end to the other. Nothing appears on the shelf. End with the shelf still empty and Hood-kun still looking at it.
```

### C06 我慢くらべではない（3.0秒）

画面: 座っているだけ。苦しむ記号は出さない。

静止画:

```text
Vertical 9:16 story still. Clean flat 2D anime background, soft daylight, simple shapes, gentle shadows. Match the approved character reference stills exactly. Leave the bottom fifth of the frame empty of faces, hands, and important props. No text, no letters, no numbers, no logos, no watermarks, no speech bubbles, no captions, no subtitles. No photorealistic humans, no 3D skin, no extra limbs, no missing limbs, no disconnected joints, no duplicate bodies, no melted hands. No other people unless this cut names Leaf-girl.

Hood-kun, identical in every image: a simple flat 2D anime stick-figure with a large round white head, a plain white hoodie with the hood fully up, a soft white hood rim around the face, and two short white drawstrings with no logos. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no hair outside the hood, no realistic skin. The torso is a simple white hoodie with solid white fill and a clean dark outline, no patterns, no text, no badges. Exactly two arms and exactly two legs. The arms are dark single-line strokes of constant medium weight, ending in small dark rounded hands. The legs are dark single-line strokes of the same weight, ending in short dark rounded feet. A moving limb replaces its previous pose and never leaves a second arm or leg behind. Proportions stay fixed: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.

Same hut. Hood-kun sits on the wooden floor in a simple seated pose, two legs bent and both visible, both hands resting on his knees. He is not sweating, not straining, not tied, and there are no chains, weights, clocks, or struggle symbols. The empty shelf remains in the background. The mood is quiet and almost blank.
```

i2v:

```text
Image-to-video only. Use the approved still of this cut as the first frame. Do not redesign the character, the hoodie, the leaf, the line weight, or the proportions. Do not switch to text-to-video. Do not add speech, lip sync, captions, subtitles, letters, or numbers. Exactly two arms and two legs; a moving limb replaces its old pose. No extra fingers, no broken joints, no morphing of the body into another shape. Ambient motion and camera only, plus the one action named below.

Duration 3.0 seconds. Hood-kun is already seated. He blinks once and stays seated, hands remaining on his knees. The camera holds with a very small downward settle. Do not add struggle props. End with him still calmly seated and the shelf still empty.
```

### C07 危険は無い（3.2秒）

画面: 窓の外の穏やかな海。誰も来ない。

静止画:

```text
Vertical 9:16 story still. Clean flat 2D anime background, soft daylight, simple shapes, gentle shadows. Match the approved character reference stills exactly. Leave the bottom fifth of the frame empty of faces, hands, and important props. No text, no letters, no numbers, no logos, no watermarks, no speech bubbles, no captions, no subtitles. No photorealistic humans, no 3D skin, no extra limbs, no missing limbs, no disconnected joints, no duplicate bodies, no melted hands. No other people unless this cut names Leaf-girl.

Hood-kun, identical in every image: a simple flat 2D anime stick-figure with a large round white head, a plain white hoodie with the hood fully up, a soft white hood rim around the face, and two short white drawstrings with no logos. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no hair outside the hood, no realistic skin. The torso is a simple white hoodie with solid white fill and a clean dark outline, no patterns, no text, no badges. Exactly two arms and exactly two legs. The arms are dark single-line strokes of constant medium weight, ending in small dark rounded hands. The legs are dark single-line strokes of the same weight, ending in short dark rounded feet. A moving limb replaces its previous pose and never leaves a second arm or leg behind. Proportions stay fixed: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.

Hood-kun stands at the hut window, both feet on the floor, looking out. Outside is only a calm bright sea and clear sky. No storm, no rocks falling, no animals, no boat, no second person. His arms hang at his sides.
```

i2v:

```text
Image-to-video only. Use the approved still of this cut as the first frame. Do not redesign the character, the hoodie, the leaf, the line weight, or the proportions. Do not switch to text-to-video. Do not add speech, lip sync, captions, subtitles, letters, or numbers. Exactly two arms and two legs; a moving limb replaces its old pose. No extra fingers, no broken joints, no morphing of the body into another shape. Ambient motion and camera only, plus the one action named below.

Duration 3.2 seconds. Hood-kun is already at the window. He takes one small breath and keeps looking out. Gentle waves move on the calm sea. Nobody arrives. End with him still at the window and the sea still empty.
```

### C08 まだ知らない（3.4秒）

画面: 本人は窓を見ている。瓶は背後に隠れたまま。

静止画:

```text
Vertical 9:16 story still. Clean flat 2D anime background, soft daylight, simple shapes, gentle shadows. Match the approved character reference stills exactly. Leave the bottom fifth of the frame empty of faces, hands, and important props. No text, no letters, no numbers, no logos, no watermarks, no speech bubbles, no captions, no subtitles. No photorealistic humans, no 3D skin, no extra limbs, no missing limbs, no disconnected joints, no duplicate bodies, no melted hands. No other people unless this cut names Leaf-girl.

Hood-kun, identical in every image: a simple flat 2D anime stick-figure with a large round white head, a plain white hoodie with the hood fully up, a soft white hood rim around the face, and two short white drawstrings with no logos. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no hair outside the hood, no realistic skin. The torso is a simple white hoodie with solid white fill and a clean dark outline, no patterns, no text, no badges. Exactly two arms and exactly two legs. The arms are dark single-line strokes of constant medium weight, ending in small dark rounded hands. The legs are dark single-line strokes of the same weight, ending in short dark rounded feet. A moving limb replaces its previous pose and never leaves a second arm or leg behind. Proportions stay fixed: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.

Camera behind Hood-kun. He faces the window and does not look back. A simple clear glass jar with one small green leaf icon and no writing sits on the floor, partly hidden by the food crate. A few plain gold coins with no numerals are inside. His eyes point toward the sea, not toward the jar.
```

i2v:

```text
Image-to-video only. Use the approved still of this cut as the first frame. Do not redesign the character, the hoodie, the leaf, the line weight, or the proportions. Do not switch to text-to-video. Do not add speech, lip sync, captions, subtitles, letters, or numbers. Exactly two arms and two legs; a moving limb replaces its old pose. No extra fingers, no broken joints, no morphing of the body into another shape. Ambient motion and camera only, plus the one action named below.

Duration 3.4 seconds. The camera slides from beside Hood-kun's face to a view behind him, revealing more of the hidden jar. He does not turn around. The coins do not jump out. End with him still facing the window and the jar still behind him, only partly in view.
```

### C09 五万円が積まれる（3.6秒）

画面: 上に大切な人、下に増える瓶。島には二人で立たない。

静止画:

```text
Vertical 9:16 story still. Clean flat 2D anime background, soft daylight, simple shapes, gentle shadows. Match the approved character reference stills exactly. Leave the bottom fifth of the frame empty of faces, hands, and important props. No text, no letters, no numbers, no logos, no watermarks, no speech bubbles, no captions, no subtitles. No photorealistic humans, no 3D skin, no extra limbs, no missing limbs, no disconnected joints, no duplicate bodies, no melted hands. No other people unless this cut names Leaf-girl.

A clean horizontal split with a thin soft divider. No morph between the halves.

Top half, a different room, not the island: Leaf-girl, identical in every image: a simple flat 2D anime stick-figure with a large round white head and straight white hair cut in a blunt shoulder-length shape. One single simple green leaf is tucked on the viewer's left side of her hair when she faces the camera, and on her own left side in three-quarter view. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no realistic skin, no second leaf, no hair color other than white. She wears a simple sleeveless white dress with solid white fill and a clean dark outline, hem above the knee, no patterns and no text. Exactly two arms and exactly two legs, dark single-line strokes of constant medium weight, small dark rounded hands, short dark rounded feet. A moving limb replaces its previous pose and never leaves a second limb behind. Proportions match Hood-kun: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight. She stands at a plain window in a bright wooden room with no posters, no titled books, and no phone, arms at her sides, looking outside. She is not on the beach and Hood-kun is not in this half.

Bottom half, above the empty subtitle band: the same hut jar, clear glass, one green leaf icon, no writing, with plain gold coins stacked inside. Hood-kun's back is at the edge of this half, still facing away from the jar. Hood-kun, identical in every image: a simple flat 2D anime stick-figure with a large round white head, a plain white hoodie with the hood fully up, a soft white hood rim around the face, and two short white drawstrings with no logos. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no hair outside the hood, no realistic skin. The torso is a simple white hoodie with solid white fill and a clean dark outline, no patterns, no text, no badges. Exactly two arms and exactly two legs. The arms are dark single-line strokes of constant medium weight, ending in small dark rounded hands. The legs are dark single-line strokes of the same weight, ending in short dark rounded feet. A moving limb replaces its previous pose and never leaves a second arm or leg behind. Proportions stay fixed: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.
```

i2v:

```text
Image-to-video only. Use the approved still of this cut as the first frame. Do not redesign the character, the hoodie, the leaf, the line weight, or the proportions. Do not switch to text-to-video. Do not add speech, lip sync, captions, subtitles, letters, or numbers. Exactly two arms and two legs; a moving limb replaces its old pose. No extra fingers, no broken joints, no morphing of the body into another shape. Ambient motion and camera only, plus the one action named below.

Duration 3.6 seconds. Keep the split. In the top half, Leaf-girl turns her gaze a little toward the window and does not speak. In the bottom half, three plain coins drop one by one into the jar. Do not morph one half into the other. Do not place Leaf-girl on the island. End with a slightly fuller jar and Leaf-girl still in her own room.
```

### C10 青いボタンで一通（4.0秒）

画面: 青いボタンと、文字の無い封筒が一通。まだ押さない。

静止画:

```text
Vertical 9:16 story still. Clean flat 2D anime background, soft daylight, simple shapes, gentle shadows. Match the approved character reference stills exactly. Leave the bottom fifth of the frame empty of faces, hands, and important props. No text, no letters, no numbers, no logos, no watermarks, no speech bubbles, no captions, no subtitles. No photorealistic humans, no 3D skin, no extra limbs, no missing limbs, no disconnected joints, no duplicate bodies, no melted hands. No other people unless this cut names Leaf-girl.

Hood-kun, identical in every image: a simple flat 2D anime stick-figure with a large round white head, a plain white hoodie with the hood fully up, a soft white hood rim around the face, and two short white drawstrings with no logos. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no hair outside the hood, no realistic skin. The torso is a simple white hoodie with solid white fill and a clean dark outline, no patterns, no text, no badges. Exactly two arms and exactly two legs. The arms are dark single-line strokes of constant medium weight, ending in small dark rounded hands. The legs are dark single-line strokes of the same weight, ending in short dark rounded feet. A moving limb replaces its previous pose and never leaves a second arm or leg behind. Proportions stay fixed: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.

Hut interior, back at the low wooden table. A large round clear-blue button with a soft cool glow sits on a plain wooden stand, no letters and no symbols. One plain cream envelope with no writing hovers just above the button. Hood-kun stands behind the table, both hands at his sides, not touching the button. The savings jar remains in the background, still full, with its green leaf icon.
```

i2v:

```text
Image-to-video only. Use the approved still of this cut as the first frame. Do not redesign the character, the hoodie, the leaf, the line weight, or the proportions. Do not switch to text-to-video. Do not add speech, lip sync, captions, subtitles, letters, or numbers. Exactly two arms and two legs; a moving limb replaces its old pose. No extra fingers, no broken joints, no morphing of the body into another shape. Ambient motion and camera only, plus the one action named below.

Duration 4.0 seconds. The plain envelope drifts down toward the blue button and hovers above it. Hood-kun's hand twitches once and returns to his side. He does not touch the button. Only one envelope is visible. End with the envelope still hovering and the button unpressed.
```

### C11 一回十万円、二日分（3.6秒）

画面: 代価の二列だけが消える。瓶は減らない。まだ払っていない。

静止画:

```text
Vertical 9:16 story still. Clean flat 2D anime background, soft daylight, simple shapes, gentle shadows. Match the approved character reference stills exactly. Leave the bottom fifth of the frame empty of faces, hands, and important props. No text, no letters, no numbers, no logos, no watermarks, no speech bubbles, no captions, no subtitles. No photorealistic humans, no 3D skin, no extra limbs, no missing limbs, no disconnected joints, no duplicate bodies, no melted hands. No other people unless this cut names Leaf-girl.

Hood-kun, identical in every image: a simple flat 2D anime stick-figure with a large round white head, a plain white hoodie with the hood fully up, a soft white hood rim around the face, and two short white drawstrings with no logos. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no hair outside the hood, no realistic skin. The torso is a simple white hoodie with solid white fill and a clean dark outline, no patterns, no text, no badges. Exactly two arms and exactly two legs. The arms are dark single-line strokes of constant medium weight, ending in small dark rounded hands. The legs are dark single-line strokes of the same weight, ending in short dark rounded feet. A moving limb replaces its previous pose and never leaves a second arm or leg behind. Proportions stay fixed: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.

Same table and the same unpressed blue button. Beside the button, two columns of plain gold coins are shown as a price diagram, with no numerals. The savings jar in the background still holds its own coins and does not lose any. The one plain envelope remains above the button. Hood-kun watches, both hands down. He is not paying.
```

i2v:

```text
Image-to-video only. Use the approved still of this cut as the first frame. Do not redesign the character, the hoodie, the leaf, the line weight, or the proportions. Do not switch to text-to-video. Do not add speech, lip sync, captions, subtitles, letters, or numbers. Exactly two arms and two legs; a moving limb replaces its old pose. No extra fingers, no broken joints, no morphing of the body into another shape. Ambient motion and camera only, plus the one action named below.

Duration 3.6 seconds. The two price columns beside the blue button fade from solid coins into empty outlines. The savings jar in the background stays at the same level. Hood-kun does not reach and does not press. End with the empty outlines, the full jar, the envelope, and the unpressed blue button.
```

### C12 翌日、伸ばして止める（4.2秒）

画面: 朝。片手が青に伸び、触れる前に止まる。

静止画:

```text
Vertical 9:16 story still. Clean flat 2D anime background, soft daylight, simple shapes, gentle shadows. Match the approved character reference stills exactly. Leave the bottom fifth of the frame empty of faces, hands, and important props. No text, no letters, no numbers, no logos, no watermarks, no speech bubbles, no captions, no subtitles. No photorealistic humans, no 3D skin, no extra limbs, no missing limbs, no disconnected joints, no duplicate bodies, no melted hands. No other people unless this cut names Leaf-girl.

Hood-kun, identical in every image: a simple flat 2D anime stick-figure with a large round white head, a plain white hoodie with the hood fully up, a soft white hood rim around the face, and two short white drawstrings with no logos. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no hair outside the hood, no realistic skin. The torso is a simple white hoodie with solid white fill and a clean dark outline, no patterns, no text, no badges. Exactly two arms and exactly two legs. The arms are dark single-line strokes of constant medium weight, ending in small dark rounded hands. The legs are dark single-line strokes of the same weight, ending in short dark rounded feet. A moving limb replaces its previous pose and never leaves a second arm or leg behind. Proportions stay fixed: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.

Same hut table in cooler, brighter morning light. This is a new morning, not a new room. Hood-kun's right arm is extended toward the blue button, the rounded hand stopped short of contact. His left arm stays down. There is no second right arm. The blue button is unpressed. The envelope and the jar remain.
```

i2v:

```text
Image-to-video only. Use the approved still of this cut as the first frame. Do not redesign the character, the hoodie, the leaf, the line weight, or the proportions. Do not switch to text-to-video. Do not add speech, lip sync, captions, subtitles, letters, or numbers. Exactly two arms and two legs; a moving limb replaces its old pose. No extra fingers, no broken joints, no morphing of the body into another shape. Ambient motion and camera only, plus the one action named below.

Duration 4.2 seconds. Morning light brightens a little. Hood-kun's right hand travels toward the blue button and stops before touching it. His left arm stays at his side the whole time. Do not leave the lowered arm in place while the reaching arm appears. He does not press. End on the stopped hand just short of the button.
```

### C13 一通は相手の二日（3.8秒）

画面: 手は戻っている。封筒一通と、消えた二列の輪郭。

静止画:

```text
Vertical 9:16 story still. Clean flat 2D anime background, soft daylight, simple shapes, gentle shadows. Match the approved character reference stills exactly. Leave the bottom fifth of the frame empty of faces, hands, and important props. No text, no letters, no numbers, no logos, no watermarks, no speech bubbles, no captions, no subtitles. No photorealistic humans, no 3D skin, no extra limbs, no missing limbs, no disconnected joints, no duplicate bodies, no melted hands. No other people unless this cut names Leaf-girl.

Hood-kun, identical in every image: a simple flat 2D anime stick-figure with a large round white head, a plain white hoodie with the hood fully up, a soft white hood rim around the face, and two short white drawstrings with no logos. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no hair outside the hood, no realistic skin. The torso is a simple white hoodie with solid white fill and a clean dark outline, no patterns, no text, no badges. Exactly two arms and exactly two legs. The arms are dark single-line strokes of constant medium weight, ending in small dark rounded hands. The legs are dark single-line strokes of the same weight, ending in short dark rounded feet. A moving limb replaces its previous pose and never leaves a second arm or leg behind. Proportions stay fixed: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.

Closer framing on Hood-kun's face and chest, same hood and same face marks. Both hands are back at his sides, not reaching. His mouth is closed. In the lower midground, above the empty subtitle band, the one plain envelope and the two faded coin-column outlines remain beside the unpressed blue button. Leaf-girl is not in this room.
```

i2v:

```text
Image-to-video only. Use the approved still of this cut as the first frame. Do not redesign the character, the hoodie, the leaf, the line weight, or the proportions. Do not switch to text-to-video. Do not add speech, lip sync, captions, subtitles, letters, or numbers. Exactly two arms and two legs; a moving limb replaces its old pose. No extra fingers, no broken joints, no morphing of the body into another shape. Ambient motion and camera only, plus the one action named below.

Duration 3.8 seconds. The right hand, already returning, settles at his side. Hood-kun blinks once and keeps looking at the envelope. He does not speak and does not press the button. End with both hands down, one envelope, and the two empty coin outlines still visible.
```

### C14 積立だけが増える（4.0秒）

画面: 夕方の光が朝へ移る。増えるのは瓶だけ。

静止画:

```text
Vertical 9:16 story still. Clean flat 2D anime background, soft daylight, simple shapes, gentle shadows. Match the approved character reference stills exactly. Leave the bottom fifth of the frame empty of faces, hands, and important props. No text, no letters, no numbers, no logos, no watermarks, no speech bubbles, no captions, no subtitles. No photorealistic humans, no 3D skin, no extra limbs, no missing limbs, no disconnected joints, no duplicate bodies, no melted hands. No other people unless this cut names Leaf-girl.

Hood-kun, identical in every image: a simple flat 2D anime stick-figure with a large round white head, a plain white hoodie with the hood fully up, a soft white hood rim around the face, and two short white drawstrings with no logos. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no hair outside the hood, no realistic skin. The torso is a simple white hoodie with solid white fill and a clean dark outline, no patterns, no text, no badges. Exactly two arms and exactly two legs. The arms are dark single-line strokes of constant medium weight, ending in small dark rounded hands. The legs are dark single-line strokes of the same weight, ending in short dark rounded feet. A moving limb replaces its previous pose and never leaves a second arm or leg behind. Proportions stay fixed: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.

Same hut window. The window light is divided cleanly: warm sunset on the left of the glass, pale morning on the right, as a light change and not a change to his body. Hood-kun stands watching the window, arms down. The savings jar beside him is fuller than when it was hidden behind the crate. The blue button is visible on the table and is unpressed. No days are written anywhere.
```

i2v:

```text
Image-to-video only. Use the approved still of this cut as the first frame. Do not redesign the character, the hoodie, the leaf, the line weight, or the proportions. Do not switch to text-to-video. Do not add speech, lip sync, captions, subtitles, letters, or numbers. Exactly two arms and two legs; a moving limb replaces its old pose. No extra fingers, no broken joints, no morphing of the body into another shape. Ambient motion and camera only, plus the one action named below.

Duration 4.0 seconds. The window light travels from warm sunset to pale morning. Three more plain coins drop into the jar. Hood-kun stays standing and does not touch the blue button. Do not morph his body. End in morning light, with a fuller jar and the button still unpressed.
```

### C15 どちらも押さない（4.0秒）

画面: 琥珀と青の間に立ち、両手を下ろしている。

静止画:

```text
Vertical 9:16 story still. Clean flat 2D anime background, soft daylight, simple shapes, gentle shadows. Match the approved character reference stills exactly. Leave the bottom fifth of the frame empty of faces, hands, and important props. No text, no letters, no numbers, no logos, no watermarks, no speech bubbles, no captions, no subtitles. No photorealistic humans, no 3D skin, no extra limbs, no missing limbs, no disconnected joints, no duplicate bodies, no melted hands. No other people unless this cut names Leaf-girl.

Hood-kun, identical in every image: a simple flat 2D anime stick-figure with a large round white head, a plain white hoodie with the hood fully up, a soft white hood rim around the face, and two short white drawstrings with no logos. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no hair outside the hood, no realistic skin. The torso is a simple white hoodie with solid white fill and a clean dark outline, no patterns, no text, no badges. Exactly two arms and exactly two legs. The arms are dark single-line strokes of constant medium weight, ending in small dark rounded hands. The legs are dark single-line strokes of the same weight, ending in short dark rounded feet. A moving limb replaces its previous pose and never leaves a second arm or leg behind. Proportions stay fixed: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.

Exterior on the same beach. Hood-kun stands full body in the center, both arms down, both hands away from every button. The amber return button on its wooden post is in the foreground, unpressed. Through the hut doorway behind him, the blue button is visible on the table, also unpressed. The sea is behind the hut. He is alone.
```

i2v:

```text
Image-to-video only. Use the approved still of this cut as the first frame. Do not redesign the character, the hoodie, the leaf, the line weight, or the proportions. Do not switch to text-to-video. Do not add speech, lip sync, captions, subtitles, letters, or numbers. Exactly two arms and two legs; a moving limb replaces its old pose. No extra fingers, no broken joints, no morphing of the body into another shape. Ambient motion and camera only, plus the one action named below.

Duration 4.0 seconds. Hood-kun looks toward the amber return button, then toward the blue button in the doorway, then lowers his eyes. Both arms stay down the whole time. He presses neither button. End with him standing between the two unpressed buttons.
```

### C16 青を押しますか（5.0秒）

画面: 青いボタンの寄り。手は触れていない。問いの余韻。

静止画:

```text
Vertical 9:16 story still. Clean flat 2D anime background, soft daylight, simple shapes, gentle shadows. Match the approved character reference stills exactly. Leave the bottom fifth of the frame empty of faces, hands, and important props. No text, no letters, no numbers, no logos, no watermarks, no speech bubbles, no captions, no subtitles. No photorealistic humans, no 3D skin, no extra limbs, no missing limbs, no disconnected joints, no duplicate bodies, no melted hands. No other people unless this cut names Leaf-girl.

Hood-kun, identical in every image: a simple flat 2D anime stick-figure with a large round white head, a plain white hoodie with the hood fully up, a soft white hood rim around the face, and two short white drawstrings with no logos. The face has only two small dark oval eyes, short straight dark eyebrows, and a tiny curved mouth. No nose, no ears, no teeth, no hair outside the hood, no realistic skin. The torso is a simple white hoodie with solid white fill and a clean dark outline, no patterns, no text, no badges. Exactly two arms and exactly two legs. The arms are dark single-line strokes of constant medium weight, ending in small dark rounded hands. The legs are dark single-line strokes of the same weight, ending in short dark rounded feet. A moving limb replaces its previous pose and never leaves a second arm or leg behind. Proportions stay fixed: large round head, short torso, thin limbs, full body about four heads tall. Clean uniform line weight.

Tight vertical close-up of the same clear-blue button, soft cool glow, no letters and no symbols. Hood-kun's hand is low in the frame, above the empty subtitle band, stopped short of the button. A small part of the same white sleeve is visible. The beach and the hut are a soft background. The button is unpressed.
```

i2v:

```text
Image-to-video only. Use the approved still of this cut as the first frame. Do not redesign the character, the hoodie, the leaf, the line weight, or the proportions. Do not switch to text-to-video. Do not add speech, lip sync, captions, subtitles, letters, or numbers. Exactly two arms and two legs; a moving limb replaces its old pose. No extra fingers, no broken joints, no morphing of the body into another shape. Ambient motion and camera only, plus the one action named below.

Duration 5.0 seconds. The camera pushes in very slowly on the blue button. Hood-kun's hand stays stopped below it and never completes the press. The glow pulses slowly twice. Do not fade to black and do not add a second person. End on the unpressed blue button, still glowing, with the hand still short of contact.
```

### 編集で載せること

- 日本語ナレーションは、上の凍結した声で、台本のタイムコードどおりに別収録する
- 字幕はナレーションと同じ文を、画面下の空いている帯に置く。画像の中には焼かない
- BGM は最初のカットのピアノとパッドを最後まで継続する。途中で曲種を変えない
- 金額の数字は字幕と声だけ。絵のコインに数字を足さない

---

## 6. スキルの使い方と、合わなかった箇所

読んだファイル:

- `skills/directing-stickman-videos/SKILL.md`
- `references/storyboard-template.md`
- `references/style-catalog.md`
- `references/voice-continuity.md`
- `references/cozy-storytelling.md`
- `references/omni-flash-prompt-contract.md`
- `references/examples.md` は手順と詳細さの確認にだけ使い、題材と文面は流用していない

### そのまま使ったところ

- 設定は依頼に揃っていたので、比率と画風の質問では止めていない。縦 9:16。尺は 30–60秒の帯なので、スキルの既定である 60秒（10秒の倍数）にした
- 叙事は五段階（つかみ、前提を壊す、内幕、真相、最後の問い）に乗せた。最後の行はコメントが割れる問い
- キャラは Style 4 のやり方で、話専用のアンカーを凍結し、出るカットの静止画プロンプトへ全文を繰り返した。「同じキャラ」だけの省略はしていない
- 手足は二本、今のポーズだけ、線の太さは一定、という崩れ防止を全プロンプトに入れた
- 小道具は「見た目」と「最初の位置」と「動きの結果」を分けた。代価の二列が消えても、積立の瓶は減らさない
- 場所の変化と時間のジャンプ（女の子の部屋、翌日の朝、夕日から朝）は絵コンテに名前を書いた
- 声は動画単位で一つに固定し、カットごとに声色を変えない。感情は画面と音楽へ置いた
- 色は日常語だけにした。色コードは書いていない
- 生成画像の中に文字、字幕、吹き出しを置かない。字幕は編集用に分離した
- 縦画面は奥行きと上下の分割（C09）と、ボタンへの縦の寄り（C16）で組んだ
- 事実として足した金額は無い。五万円と十万円（二日分）は依頼のルールそのまま

### 依頼とスキルが違って、依頼を優先したところ

- スキルは演出プランのあとで承認を待ち、承認前にモデル用プロンプトを書かない。今回の依頼は、キャラクターシートから i2v までを一つの文書にまとめる指定だった。承認待ちでは止めていない
- スキルの本編音声は英語で、ユーザーの言語は参考訳。今回の収録本文は日本語。英語は参考訳の列だけ
- スキルの Phase B は、約10秒の text-to-video を六本、音声込みで書く契約（Gemini Omni Flash を想定）。今回は text-to-video を禁止され、参照スティル、カット静止画、その画像を始点にした image-to-video、という順を指定された。プロンプトにモデル名は入れていない
- スキルは生成クリップの中の字幕を禁止する。画面下字幕は編集工程として台本に書いた。静止画プロンプトは下五分の一を空け、文字を描かせない
- スキルの Style 4 は、10秒ごとに別の場所を基本にする。依頼の背景は砂浜、木の小屋、室内だけなので、その三つに収めた。女の子の部屋は「大切な人は島にいない」ことを見せる一回だけのカットアウェイ
- Style 4 の見本アンカーは髪も服も無い。依頼の白いフードと、白い髪と緑の葉が優先なので、見本アンカーは使わず、この話のシートを凍結した
- Style 2 の赤いニット帽と黄色いシャツは、このキャラクターと違うので使っていない
- スキルの BGM 文面には「楽観的な勢い」がある。この話の余韻には合わないので、楽器とテンポの固定だけを残し、気分は抑えたピアノに変えた
- 一行と画面を一致させ、行間を 1.5秒以内にするため、生成単位は 10秒六本ではなく、セリフ十六行に対応する十六カットにした。五段階のまとまりは約10秒で絵コンテに残している
- ナレーションを動画プロンプトの中で話させると、モデルが字幕や英語を描くので、声は別収録にした。声の凍結ブロックは収録仕様としてヘッダに残した

### 生成していないもの

参照スティル、物語の静止画、image-to-video、ナレーション音声、字幕入りの完成動画は、この文書では作っていない。
