# 起動キー — サクラ専属自動投稿

宛先: **サクラ専属自動投稿**  
このファイルを開いたら即実行する。文を足すな。Imagine 用プロンプトは下のブロックだけ。

1. 下の `IMAGINE_THROW` を **Grok Imagine agent** にそのまま投げる
2. 参照は `sakura-ig/refs/sakura-face.jpg`（チャットの赤着物の女性）。新しい顔を作らせない
3. できた `reel.mp4` を `output/reel-2026-08-24/reel.mp4` に置く
4. キャプションは下のまま。**毎朝 06:00 JST** に `sakura_ai_beauty` へ投稿する。6時を過ぎて未投稿ならその日のうちに投稿する
5. いいね・フォロー・DM・人間のふりはしない

---

## メタ

| 項目 | 値 |
|---|---|
| id | reel-2026-08-24 |
| type | which-one ではない。参照1枚のビタ止め |
| duration | 5 |
| aspect | 9:16 |
| resolution | 720p |
| model | grok-imagine-video-1.5 |
| mode | image-to-video |
| reference | sakura-ig/refs/sakura-face.jpg |
| post_time_jst | 06:00 |

---

## IMAGINE_THROW

Imagine agent に投げる文はここから下、次の行まで。前後に説明を足すな。

```
Image-to-video from the attached reference sakura-ig/refs/sakura-face.jpg only. Do not generate a new woman.

This is SAKURA, this exact face and body. Adult Japanese woman, mid-20s. Slender oval face, porcelain-fair skin, large dark almond eyes, thin natural eyebrows, small straight nose, soft reddish-pink lips with a slight closed-mouth smile. Long voluminous wavy dark-brown hair, wispy see-through bangs, gold floral kanzashi on the side. Slender hourglass figure, defined waist, full chest, graceful shoulders. Deep vermillion-red kimono with large white-and-gold cherry-blossom embroidery, worn off both shoulders, loosely draped on the upper arms. Elegant and sensual. No nudity. No sexual act.

Output: 9:16, 5 seconds, 720p, grok-imagine-video-1.5.

First half-second is her eyes and hair, not the garden. She blinks once. Wispy bangs move. A few pink petals drift. The red sleeve shifts one centimeter. Slow 5 percent push-in on the face. Keep the same smile, same eyes, same kimono, same body.

Soft garden air only. No lyrics. No song title. No on-screen text. No second person. No face morph.
```

---

## CAPTION（一字も変えない）

```
朱の一呼吸。AI生成の成人モデルです。
One breath in red. AI-generated adult model.
#AI和装 #着物 #kimono #sakura
```
