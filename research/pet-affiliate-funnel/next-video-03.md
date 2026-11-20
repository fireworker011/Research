# 次の作り置き 3本目（夕方の水）

日付: 2026-10-15
id: `pet_camera_03`
状態: 設計のみ。Imagine に投げない。投稿しない。アフィリエイトURLは書かない。
第1弾: `pet_camera_01`（棚の前足、12秒、昼）。2本目: `pet_camera_02`（毛布、9秒、朝）。この本はどちらでもない。

## 型

1. 飼い主の留守中に、知らない一瞬が起きる。
2. その一瞬は、カメラがあったから知れた。
3. 見た人が「うちの子も外から見たい」と思う。

動画の中では宣伝しない。導線の文言は説明欄だけ。声はあみたろ（落ち着いた大人の女性、日記）。画面に文字は出さない。

この本の「〇〇」: 後輩が先に水へ顔を下ろし、先輩があとから飲んで、水面が落ちた。

01・02との差: 最初の絵は円い器と、降りてくる顔。最初のナレは「夕方、水に顔を下ろした。」尺は 13.0秒。光は右からの橙色。サムネは器を円で大きく置く。

## ルール（2026-10-09 の pet.md）

- 字幕、テロップ、CTA、画面の文字は無し。声でもリンクを案内しない
- 猫だけ。人は出さない。犬は出さない
- 同じ2匹。参照画像で柄と顔を固定する
- 実写。高い角の固定カメラだけ
- 1生成1ショット、2〜5秒、動きは1つ。光と質感を書く。ロゴ、文字、時刻、水面の反射文字は禁止
- 同じプロンプトを使い回さない
- 合計 13.0秒（4.0 + 4.0 + 5.0）

## 1. タイトル案

画面には出さない。本採用は1。

1. 見守りカメラの夕方を見たら、水が減った順番が残っていた
2. 夕方の見守りカメラでは、後輩が先に水へ顔を下ろしていた
3. 見守りカメラで留守の夕方を見たら、水面だけが落ちていた

## 2. ショット表

場所は同じ部屋の床。高い角から、床の白い陶器の器を見下ろす。取っ手も文字も絵付けも無い。水は透明。光は画面右の低い夕方で、器の右縁が橙色、左縁が長い影。毛布も棚も出さない。口を開けるのは、ショット3で先輩が水面に口をつけるその一回だけ。それ以外の口は閉じている。

| # | 秒 | 狙い | 開始状態 | 動き（1つ） |
|---|---|---|---|---|
| 1 | 0.0–4.0 | 先に飲もうとしたのが後輩だと分かる | 器は満水。後輩の顔は器の上にある。先輩は画角の外 | 後輩の顔が、水面の手前まで一回下りて止まる。水はまだ減らない |
| 2 | 4.0–8.0 | 先輩はあとから来た、と分かる | 後輩は器の左で座って止まっている。先輩の体はまだ右端の外 | 先輩が右から歩いて入り、器の右で止まって座る |
| 3 | 8.0–13.0 | 減った理由が、先輩のその一回だと分かる | 先輩は座っている。水面はまだ高い。後輩は動かない | 先輩が口を水面へ一回つけ、顔を戻す。水面がその分だけ下がる |

### ショット1の Imagine プロンプト（4秒）

```
Photorealistic pet-camera footage from a high corner. Vertical 9:16, 1080x1920. One continuous 4-second shot, no cuts. Camera: locked off, high, looking down so a round white ceramic bowl fills the lower center. Lighting: low evening sun from the right, warm orange on the right rim, a long cool shadow to the left of the bowl, no morning white, no night vision. Texture: glossy water surface, matte ceramic with no pattern and no letters, wood floor. Cats only. The kitten is the locked reference kitten, coat and face unchanged. The adult cat is not in this shot. No humans, no dogs. No text, no logos, no reflection of writing, no UI, no clock, no blanket, no shelf.

Start state: the bowl is full. The kitten's face is already above the bowl, mouth closed. The only motion is the kitten lowering its face once until it stops just short of the water. The waterline does not drop.
```

### ショット2の Imagine プロンプト（4秒）

```
Photorealistic evening pet camera, same high locked corner. Vertical 9:16, 1080x1920. One continuous 4-second shot, no cuts. Camera: locked off, looking down at the same plain white bowl. Lighting: orange sunset from frame-right, rim light on the right edge of the bowl, long shadow to the left. Texture: still high water, unprinted ceramic, wood grain. Cats only. Both cats use the locked reference images, coats unchanged. No humans, no dogs. No text, no logos, no watermark, no screen, no timestamp.

Start state: the kitten is already seated to the left of the bowl, still, mouth closed. The adult cat is not yet in frame. The only motion is the adult cat walking in from the right and sitting down once beside the bowl. The kitten does not move. The waterline stays high.
```

### ショット3の Imagine プロンプト（5秒）

```
Photorealistic high-corner pet camera at evening. Vertical 9:16, 1080x1920. One continuous 5-second shot, no cuts. Camera: locked off, steep look down at the round bowl. Lighting: deeper orange from the right, the left side of the bowl now in soft shadow, no infrared tint. Texture: clear water, plain ceramic, wood floor. Cats only. Locked reference adult cat and kitten, same coats and faces. No humans, no dogs. No text, no logos, no brand, no HUD, no clock.

Start state: the adult cat is already seated at the right of the full bowl. The kitten sits still at the left, mouth closed. The only motion is the adult cat dipping its mouth to the water once and lifting its head back. The waterline falls by that one drink. The kitten does not move.
```

編集は 3本を順につなぐ。水の量は、ショット1と2は満水、ショット3の終わりだけ下がる。

## 3. ナレーション

あみたろ。各文はそのショットの秒数で読み終わる。目安は1秒あたり4モーラ前後。

| 秒 | 読む文 | モーラ | 絵 |
|---|---|---|---|
| 0.0–4.0 | 夕方、水に顔を下ろした。 | 14 | 後輩の顔が一回下り、水面の手前で止まる |
| 4.0–8.0 | 先輩が横から入ってきた。 | 15 | 先輩が右から歩いて入り、座って止まる |
| 8.0–13.0 | そのあと先輩が飲んで、水面が落ちた。 | 20 | 口を一回つけ、水面が下がる |

通し:

```
夕方、水に顔を下ろした。先輩が横から入ってきた。そのあと先輩が飲んで、水面が落ちた。
```

ショット1の文は、後輩とは言わない。画角にいる猫は後輩だけなので、顔を下ろした主体は絵で分かる。

## 4. 概要欄

URLは置かない。導線はここだけ。

```
広告
見守りカメラの夕方を見たら、水が減った順番が残っていた。
後輩が先で、先輩があとだった。

見る点は、チャンネルのリンクに置いてあります。
#PR
```

## 5. 固定コメント

リンク案内は書かない。

```
夕方の水は、戻ったときには減っていた。
```

## 6. カメラが欲しくなる一文

戻った器は水位が低いだけなので、先に顔を下ろしたのが後輩で、飲んで落としたのが先輩だとは、夕方の角のカメラが無いと分からない。

## サムネ案

採用フレーム: ショット1の 2.5秒。顔が下りきる直前。

構図: 白い器を画面下側の中央に、円として大きく置く（画面の高さの約4割）。後輩の顔は器の上縁にかかる。先輩は入れない。床の左は長い影。山のような塊にも、画面いっぱいの暗い余白にもしない。

色: 右が橙色、左の影は青みの残る灰色。朝の白でも、夜の緑灰色でもない。

## 一致の自己チェック

| 秒 | ナレ | 絵 | 一致 |
|---|---|---|---|
| 0.0–4.0 | 夕方、水に顔を下ろした。 | 右からの橙色。後輩の顔だけが一回下り、満水の手前で止まる | はい。飲む前で止まるので、水面はまだ落ちない |
| 4.0–8.0 | 先輩が横から入ってきた。 | 先輩が右から歩いて入り、器の右に座って止まる。後輩は動かない | はい。動きは入場の一回 |
| 8.0–13.0 | そのあと先輩が飲んで、水面が落ちた。 | 先輩が口を一回つけ、顔を戻す。水面がその分下がる | はい。減るのはこのショットだけ |

棚の前で前足を止める絵は無い。毛布の山も無い。
