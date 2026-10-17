# ジャンル_美容 の待つレシピ

正本の毎朝ファイル `agents/beauty.md` から移した。文言は移す前と同じ。status が「今の1本」ではない。

宛先: ジャンル_美容
from: manager
run: ready
post: false

条件を全部満たすまで、このレシピで動画を作るな。IMAGINE_THROW は条件クリア時だけ Grok Imagine に投げろ。文を足すな。投稿するな。

## メタ
- id: beauty_min_care_01
- status: 待つ。今は作るな
- kata: min_care（削る／1つだけ）
- genre: 美容
- link_key: 美容_オルビスユー
- phase: ready
- output: output/video/packets/beauty/beauty_min_care_01/reel.mp4
- aspect: 9:16
- duration_sec: 15.1
- duration: レシピの完成尺（下のテロップ表）
- imagine_clips: 4 × 5秒

## テロップ表（この秒で出せ）
| 秒 | 役割 | 画面の文字 |
|---|---|---|
| 0.0–0.5 | 文字なし・映像のみ | （なし） |
| 0.5–4.7 | 本文 | 疲れた夜、工程を落とす＋保湿の2 / つまで削る人がいます。感じ方には |
| 4.7–8.9 | 本文 | 個人差があります。効く／消える、 / とは言いません。続け方の組み立て |
| 8.9–13.1 | 本文 | だけプロフィールにまとめています / 。 |
| 13.1–15.1 | CTA | 詳しくはプロフィールのリンク（PR） |

完成尺: 15.1秒 / Imagineクリップ: 4本（各5秒を接続）

## IMAGINE_THROW
```
Vertical 9:16, 1080x1920, photorealistic, natural window light, no text, no captions, no subtitles, no watermark, no logos, no brand names, no product packaging, no UI, no human faces, 5 seconds, not cinematic, not commercial.

Pale beige bathroom shelf, one unbranded bottle silhouette, no skin close-ups.

One object on a shelf. No skin close-up, no before/after bodies.

A bathroom shelf at night, one unlabelled pump bottle and a towel, warm dim light. No face, no before-after, no logos.
```

## テロップ／読み上げ
```
疲れた夜、工程を落とす＋保湿の2つまで削る人がいます。感じ方には個人差があります。効く／消える、とは言いません。続け方の組み立てだけプロフィールにまとめています。

詳しくはプロフィールのリンク（PR）
```

## YouTube説明文（URLなし）
```
疲れた夜、工程を落とす＋保湿の2つまで削る人がいます。感じ方には個人差があります。効く／消える、とは言いません。続け方の組み立てだけプロフィールにまとめています。

詳しくはプロフィールのリンク（PR）
#PR
```
