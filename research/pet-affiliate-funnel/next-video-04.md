# 次の作り置き 4本目（夜の隣）

日付: 2026-10-15
id: `pet_camera_04`
状態: 設計のみ。Imagine に投げない。投稿しない。アフィリエイトURLは書かない。
前の3本: `pet_camera_01` は棚の前足で12秒の昼。`pet_camera_02` は毛布で9秒の朝。`pet_camera_03` は水で13秒の夕方。この本は夜。

## 型

1. 飼い主の留守中に、知らない一瞬が起きる。
2. その一瞬は、カメラがあったから知れた。
3. 見た人が「うちの子も外から見たい」と思う。

動画の中では宣伝しない。導線の文言は説明欄だけ。声はあみたろ（落ち着いた大人の女性、日記）。画面に文字は出さない。

この本の「〇〇」: 夜中に寝ていたのは後輩だけで、先輩は途中から隣に丸まった。朝の二人は、ずっと寝ていた顔だった。

01〜03との差: 最初の絵は、暗い床の下のほうで小さく丸まる後輩。最初のナレは「夜中、寝ていたのは後輩だけだった。」尺は 15.0秒。光は夜の赤外線風（緑がかった灰色、画面表示は焼かない）。サムネは下三分の一に寝姿、上は暗い床。

## ルール（2026-10-09 の pet.md）

- 字幕、テロップ、CTA、画面の文字は無し。赤外線の見た目だけを使い、`REC` や時刻や電池の印は出さない
- 声でもリンクを案内しない
- 猫だけ。人は出さない。犬は出さない
- 同じ2匹。参照画像の柄と顔を、夜の色の中でも変えない
- 実写。高い角の固定カメラだけ。猫の目線と混ぜない
- 1生成1ショット、2〜5秒、動きは1つ。光と質感を書く。ロゴ禁止
- 同じプロンプトを使い回さない
- 合計 15.0秒（5.0 + 5.0 + 5.0）

## 1. タイトル案

画面には出さない。本採用は1。

1. 夜の見守りカメラを見たら、先輩が途中から隣に来ていた
2. 見守りカメラの夜の映像では、寝ていたのは後輩だけだった
3. 朝まで寝ていたと思ったら、夜の見守りカメラでは先輩が来ていた

## 2. ショット表

場所は同じ部屋の床の丸い寝床。高い角から見下ろす。照明は消えている。絵はペットカメラの夜モードのように、緑がかった灰色で、粒子が少しある。目が開いたときだけ、弱い眼底反射があってよい。文字のオーバーレイは無い。器も毛布の山も棚も出さない。

| # | 秒 | 狙い | 開始状態 | 動き（1つ） |
|---|---|---|---|---|
| 1 | 0.0–5.0 | その時刻に寝ていたのは後輩だけ、と分かる | 後輩は寝床で目を閉じて丸まっている。先輩は画角にいない。床の上側は空いている | 後輩の耳が、一回だけ動いてまた寝る |
| 2 | 5.0–10.0 | 先輩は初めから隣にいたわけではない | 後輩は寝たまま。寝床の外側、画面上に先輩が座っている | 先輩が寝床へ一回降り、後輩の背に沿って丸まって止まる |
| 3 | 10.0–15.0 | 朝に見ると、二人とも最初から寝ていたように見える | 2匹はすでに寝床で目を閉じている。体は触れている | 先輩の耳が、一回だけ動く。後輩は動かない |

ショット2の「降りる、沿う、止まる」は、一連の就寝として1動作。途中で別の仕草を足さない。前足で相手の前足を止める動きにはしない。

### ショット1の Imagine プロンプト（5秒）

```
Photorealistic night footage from a high corner pet camera, with a night-vision look and no on-screen graphics. Vertical 9:16, 1080x1920. One continuous 5-second shot, no cuts. Camera: locked off, high, looking down at a round pet bed on the floor. Lighting: no sunlight, no orange lamp. The image is desaturated green-gray, slightly grainy, like infrared night mode. The upper two-thirds of the floor stays dark and empty. Texture: soft round bed, short carpet, matte wall lost in dark. Cats only. The kitten is the locked reference kitten, asleep, coat still recognizable in the green-gray. Eyes closed, so no eyeshine. No adult cat in frame. No humans, no dogs. No text, no REC mark, no clock, no battery icon, no logo, no HUD, no watermark.

Start state: the kitten is already curled small in the lower third, asleep. The only motion is one ear twitching once and settling. The body does not travel.
```

### ショット2の Imagine プロンプト（5秒）

```
Photorealistic pet-camera night vision, same high locked corner, no graphics. Vertical 9:16, 1080x1920. One continuous 5-second shot, no cuts. Camera: locked off, looking down at the same round bed. Lighting: green-gray infrared tone, dim, light grain, no daylight and no warm sunset. Texture: the bed's rim, carpet, the adult cat's fur still matching the reference coat under the night tint. Cats only. Locked reference images for the adult cat and the kitten. Do not invent a new coat. No humans, no dogs. No text, no logos, no timestamp, no frame counter, no brand.

Start state: the kitten is already asleep in the bed, eyes closed. The adult cat is already sitting on the open floor above the bed, eyes open with a faint natural eyeshine. The only motion is the adult cat stepping down into the bed once and curling along the kitten's back until it stops. The kitten does not wake or move. This is not a paw blocking another paw.
```

### ショット3の Imagine プロンプト（5秒）

```
Photorealistic high-corner pet camera at night, infrared green-gray, no overlay. Vertical 9:16, 1080x1920. One continuous 5-second shot, no cuts. Camera: locked off, same downward angle, the round bed now nearer the center because both cats fill it. Lighting: still dark night-vision, a little brighter on the two bodies than on the empty floor, no morning window. Texture: shared bed, touching fur, carpet edge. Cats only. Same locked reference adult cat and kitten, coats consistent with the earlier night shots. Both have eyes closed. No humans, no dogs. No text, no subtitles, no logos, no HUD, no clock.

Start state: both cats are already asleep, curled together, mouths closed, eyes closed. The only motion is the adult cat's ear flicking once. The kitten stays motionless. They look as if they had been asleep together the whole time.
```

編集は 5秒を3本、順につなぐ。最後のショットをループして朝の明るさまで延ばさない。朝の見た目はナレーションが言い、絵は夜のままにする。朝日のカットを足すと、夜の赤外線風が混ざる。

## 3. ナレーション

あみたろ。5秒の文は19〜21モーラ。ショットの終わりより前に読み終わる。

| 秒 | 読む文 | モーラ | 絵 |
|---|---|---|---|
| 0.0–5.0 | 夜中、寝ていたのは後輩だけだった。 | 19 | 後輩だけが丸まって眠り、耳が一回動く |
| 5.0–10.0 | 先輩が降りてきて、隣に丸まった。 | 19 | 先輩が寝床へ降り、背に沿って止まる |
| 10.0–15.0 | 朝の二人は、ずっと寝ていた顔だった。 | 21 | 2匹は目を閉じたまま。先輩の耳が一回動く |

通し:

```
夜中、寝ていたのは後輩だけだった。先輩が降りてきて、隣に丸まった。朝の二人は、ずっと寝ていた顔だった。
```

「朝の二人」は、朝に見た顔の話。絵を朝の色に切り替えない。

## 4. 概要欄

URLは置かない。導線はここだけ。

```
広告
夜の見守りカメラを見たら、先輩が途中から隣に来ていた。
朝の二人は、ずっと寝ていた顔だった。

見る点は、チャンネルのリンクに置いてあります。
#PR
```

## 5. 固定コメント

リンク案内は書かない。

```
朝に見ると、二人とも寝ていた。
```

## 6. カメラが欲しくなる一文

朝の寝床は二匹が最初から一緒に寝ていた顔なので、夜中は後輩だけで、先輩が途中から隣へ降りたことは、夜の角のカメラが無いと残らない。

## サムネ案

採用フレーム: ショット1の 2.0秒。耳が動く前。後輩だけが寝ている。

構図: 後輩の丸まりを、画面の下から三分の一に小さく置く。上の三分の二は暗い空の床。顔のアップにしない。器の円も、毛布の横長の山も使わない。先輩は入れない。

色: 緑がかった灰色。橙色も、朝の白もない。文字の枠は焼かない。

## 一致の自己チェック

| 秒 | ナレ | 絵 | 一致 |
|---|---|---|---|
| 0.0–5.0 | 夜中、寝ていたのは後輩だけだった。 | 夜の赤外線風。後輩だけが目を閉じて丸まり、耳が一回動く。先輩はいない | はい。寝ているのは後輩だけ |
| 5.0–10.0 | 先輩が降りてきて、隣に丸まった。 | 先輩が寝床へ一回降り、後輩の背に沿って丸まって止まる。後輩は起きない | はい。前足で止める動作ではない |
| 10.0–15.0 | 朝の二人は、ずっと寝ていた顔だった。 | 2匹は目を閉じたまま寄り添っている。先輩の耳が一回動く。色は夜のまま | はい。顔は寝た顔。朝の明るさには切り替えない |

棚の前足止め、毛布の山、水の器は、この3ショットに無い。
