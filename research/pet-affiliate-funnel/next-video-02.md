# 次の作り置き 2本目（朝の毛布）

日付: 2026-10-15
id: `pet_camera_02`
状態: 設計のみ。Imagine に投げない。投稿しない。アフィリエイトURLは書かない。
第1弾: `next-video-01.md`（`pet_camera_01`）は採用済み。この本はそれに続けない出来事。

## 型

1. 飼い主の留守中に、知らない一瞬が起きる。
2. その一瞬は、カメラがあったから知れた。
3. 見た人が「うちの子も外から見たい」と思う。

動画の中では宣伝しない。導線の文言は説明欄だけ。声はあみたろ（落ち着いた大人の女性、日記）。画面に文字は出さない。

この本の「〇〇」: 毛布の山が動いて、後輩が端を引いたら先輩が出てきた。戻ったときには、ただ並んでいた。

01との差: 最初の絵は毛布の山（前足でも棚でもない）。最初のナレは「朝、毛布が動いた。」尺は 9.0秒。光は朝の上からの白い光。サムネは山を横長に置く。

## ルール（2026-10-09 の pet.md）

- 字幕、テロップ、CTA、画面の文字は無し。声でもリンクを案内しない
- 猫だけ。人は出さない。犬は出さない
- 先輩は大人の猫、後輩は子猫。柄と顔は参照画像で固定する
- 実写。カメラは見守りカメラの高い角だけ。固定。猫の目線と混ぜない
- 1生成1ショット、2〜5秒、動きは1つ。光と質感を書く。ロゴ、ブランド、画面、時刻は禁止
- 同じプロンプトを使い回さない
- 合計 9.0秒（3.0 + 4.0 + 2.0）

## 1. タイトル案

画面には出さない。本採用は1。

1. 見守りカメラで朝の留守番を見たら、毛布の中に先輩がいた
2. 朝の見守りカメラを開いたら、動いたのは毛布だけだった
3. 見守りカメラの朝の映像では、後輩が毛布の端を引いていた

## 2. ショット表

場所は同じ朝のリビング。高い角から床を見下ろす。窓は頭上側で、光は上から床へ落ちる。色は白い朝。毛布は薄い生成りの無地。文字も縫い取りも無い。棚も箱も出さない。口は閉じたまま。

| # | 秒 | 狙い | 開始状態 | 動き（1つ） |
|---|---|---|---|---|
| 1 | 0.0–3.0 | 留守の部屋に、動く山だけがある | 毛布が床の中央で盛られている。後輩は画面左端で止まっている。先輩の体は見えない | 盛りの頂点が、一回だけ持ち上がって止まる |
| 2 | 3.0–7.0 | 引いたのが後輩で、中身が先輩だったと分かる | 盛りはそのまま。後輩の前足はまだ毛布に触れていない | 後輩の前足が端を一回引き、引いた先から先輩の顔が出て止まる |
| 3 | 7.0–9.0 | 戻ったあとでは、並んでいるだけに見える | 毛布は開いている。2匹はすでにその上で座っている | 2匹とも動かない。先輩がまぶたを一回だけ下ろす |

ショット3のまばたきが「動き1つ」。体の移動は無い。2.0秒なので、まばたきは後半の0.4秒だけ。

### ショット1の Imagine プロンプト（3秒）

```
Photorealistic natural home video from a high corner pet camera. Vertical 9:16, 1080x1920. One continuous 3-second shot, no cuts. Camera: locked off, high in the corner, looking steeply down at the floor. Lighting: early morning, cool white light falling from above, pale blue-gray shadows, no warm sunset, no lamp. Texture: light wood floor, a plain cream blanket heaped in the center, soft cotton folds, matte wall. Cats only. Start from the locked reference images. The kitten keeps the same coat and face. The adult cat is hidden inside the blanket and must not be redesigned when later revealed. No humans, no dogs. No text, no captions, no logos, no brand marks, no screen, no timestamp, no shelf, no box.

Start state: the blanket is already heaped. The kitten sits still at the left edge of the frame. Mouths closed. The only motion is the top of the heap lifting once and stopping. The kitten does not move.
```

### ショット2の Imagine プロンプト（4秒）

```
Photorealistic morning pet-camera footage, same high corner. Vertical 9:16, 1080x1920. One continuous 4-second shot, no cuts. Camera: locked off, high angle looking down. Lighting: cool overhead morning light, bright on the blanket crown, soft gray-blue shadow under the fold. Texture: rumpled cream cotton, visible wood grain around the heap. Cats only. Use the locked reference images for both the kitten and the adult cat. Do not change their coats or faces. No humans, no dogs. No text, no logos, no watermark, no UI, no clock, no furniture labels.

Start state: the heap is still. The kitten's forepaw has not yet touched the cloth. Mouths closed. The only motion is the kitten pulling the blanket edge once toward the left. As that single pull opens the fold, the adult cat's face comes out and stays. No second action from either cat.
```

### ショット3の Imagine プロンプト（2秒）

```
Photorealistic high-corner pet camera, morning. Vertical 9:16, 1080x1920. One continuous 2-second shot, no cuts. Camera: locked off, same steep downward angle. Lighting: cool white morning fill, even and quiet, no orange hour. Texture: the cream blanket now spread flat, wood floor at the edges, two cats sitting on the cloth. Cats only. Locked reference images, same adult cat and same kitten, coats unchanged. No humans, no dogs. No text, no subtitles, no logos, no brand, no screen.

Start state: both cats are already seated side by side on the opened blanket, facing slightly different ways, mouths closed. The only motion is the adult cat blinking once, slowly, near the end of the shot. The kitten stays still.
```

編集は 3本を順につなぐ。ループで尺を足さない。

## 3. ナレーション

あみたろ。日記の速さ。各文は、そのショットが終わるまでに読み終わる。目安は1秒あたり4モーラ前後。収まらないときは語を足さず、話速だけを合わせる。

| 秒 | 読む文 | モーラ | 絵 |
|---|---|---|---|
| 0.0–3.0 | 朝、毛布が動いた。 | 10 | 盛りの頂点が上がる |
| 3.0–7.0 | 後輩が端を引いて、先輩が出た。 | 18 | 端を一回引き、顔が出る |
| 7.0–9.0 | ただ、並んでいた。 | 8 | 開いた毛布の上で、まばたき一回 |

通し:

```
朝、毛布が動いた。後輩が端を引いて、先輩が出た。ただ、並んでいた。
```

## 4. 概要欄

URLは置かない。導線はここだけ。

```
広告
見守りカメラで朝の留守番を見たら、毛布の中に先輩がいた。
戻ったときには、ただ並んでいた。

見る点は、チャンネルのリンクに置いてあります。
#PR
```

## 5. 固定コメント

リンク案内は書かない。

```
朝の毛布は、戻ると普通だった。
```

## 6. カメラが欲しくなる一文

戻った部屋の毛布は開いて並んでいるだけなので、中に先輩がいて後輩が端を引いたことは、朝の角のカメラを開かないと残らない。

## サムネ案

採用フレーム: ショット1の 1.2秒。盛りが一番高い瞬間。

構図: 9:16のまま。生成りの山を画面の下半分に横長の楕円で置く。後輩は左端に小さく、体の一部だけ。先輩の顔はまだ出さない。上半分は明るい朝の床。前足のアップにしない。円い器も、暗い余白も使わない。

色: 白に近い朝。影は青灰色。

## 一致の自己チェック

| 秒 | ナレ | 絵 | 一致 |
|---|---|---|---|
| 0.0–3.0 | 朝、毛布が動いた。 | 朝の上光。盛りの頂点が一回上がる。後輩は動かない | はい。動くのは毛布だけ |
| 3.0–7.0 | 後輩が端を引いて、先輩が出た。 | 後輩の前足が端を一回引き、その結果として先輩の顔が出る | はい。引きと出現は一つの動作の結果 |
| 7.0–9.0 | ただ、並んでいた。 | 開いた毛布の上に2匹が座っている。まばたき以外は動かない | はい。見た目は並んでいるだけ |

棚の前で前足を止める絵は、この3ショットに無い。
