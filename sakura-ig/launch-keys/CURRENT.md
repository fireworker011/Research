# 起動キー — テスト

宛先: **サクラ専属自動投稿**  
渡し元: マネージャー  
渡した時刻: 2026-08-23 12:06 JST（テスト。本番の 05:00 受け渡しではない）

このファイルを開いたら即実行。文を足すな。

1. 下の `IMAGINE_THROW` を **Grok Imagine agent** にそのまま投げる
2. 参照は `sakura-ig/refs/sakura-face.jpg`。新しい顔を作らせない
3. 動画を `sakura-ig/output/reel-test-ref/reel.mp4` に置く
4. **投稿するな。** これはテスト。06:00 投稿は本番だけ

---

## 本番の時計（このテストでは使わない）

| JST | 誰 | 仕事 |
|---|---|---|
| 05:00 | マネージャー | この起動キーをボットに渡す |
| 05:00〜06:00 | ボット | Imagine に投げて動画完成 |
| 06:00 | ボット | 投稿 |

---

## メタ

| 項目 | 値 |
|---|---|
| id | reel-test-ref |
| run | test |
| post | false |
| duration | 5 |
| aspect | 9:16 |
| resolution | 720p |
| model | grok-imagine-video-1.5 |
| mode | image-to-video |
| reference | sakura-ig/refs/sakura-face.jpg |

---

## IMAGINE_THROW

```
Image-to-video from the attached reference sakura-ig/refs/sakura-face.jpg only. Do not generate a new woman.

This is SAKURA, this exact face and body. Adult Japanese woman, mid-20s. Slender oval face, porcelain-fair skin, large dark almond eyes, thin natural eyebrows, small straight nose, soft reddish-pink lips with a slight closed-mouth smile. Long voluminous wavy dark-brown hair, wispy see-through bangs, gold floral kanzashi on the side. Slender hourglass figure, defined waist, full chest, graceful shoulders. Deep vermillion-red kimono with large white-and-gold cherry-blossom embroidery, worn off both shoulders, loosely draped on the upper arms. Elegant and sensual. No nudity. No sexual act.

Output: 9:16, 5 seconds, 720p, grok-imagine-video-1.5.

First half-second is her eyes and hair, not the garden. She blinks once. Wispy bangs move. A few pink petals drift. The red sleeve shifts one centimeter. Slow 5 percent push-in on the face. Keep the same smile, same eyes, same kimono, same body.

Soft garden air only. No lyrics. No song title. No on-screen text. No second person. No face morph.
```

---

## CAPTION（テスト。投稿しない）

```
テスト。投稿しない。
AI生成の成人モデルです。
Test. Do not post.
```
