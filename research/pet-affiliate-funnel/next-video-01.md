# 次の作り置き 1本（見守りカメラの留守番）

日付: 2026-10-14
id: `pet_camera_01`
状態: 採用済みの第1弾（2026-10-15）。Imagine にはまだ投げない。投稿しない。アフィリエイトURLは書かない。
許可: ナオミチが、この1本を「見守りカメラで留守番中を隠し撮りしたら〇〇だった」型で作ると書き、2026-10-15 に第1弾として採用した。
基準（02以降はこの4つを繰り返さない）: 最初の絵は棚へ上がる後輩の前足。最初のナレは「留守番のカメラを、あとから開いた。」尺は12.0秒。光は昼の左窓。サムネになりやすいフレームは、棚と上がった前足。

## 型

借りるのは型だけ。参考動画の絵、せりふ、タイトルは使わない。

- 依頼の参考: 「監視カメラで撮ったらおもしろ過ぎた」 https://youtube.com/shorts/iH3SR9h4tKI （依頼の再生目安 約18.8万）
- 依頼の参考: 「最新ペットカメラで隠し撮り」 https://youtube.com/shorts/qNW-3a1Nl9c （依頼の再生目安 約17.9万）
- 依頼の所見: 商品紹介型は数百回で止まる
- 2026-10-14 に両URLを開いたが、再生数はページから取れなかった。上の回数は依頼の数字であり、こちらで測り直していない

この1本の「〇〇」: 先輩が後輩の前足を一回止めて、戻った部屋は何事もなかったことになっていた。

商品名、価格、機能比較では開けない。最初の絵は、角から見た子猫の前足。見守りカメラは、その絵を残した視点である。

## ルール（2026-10-09 の pet.md）

- 字幕、テロップ、CTA、画面の文字は無し。声でもプロフィールを案内しない
- 猫だけ。人は出さない。犬は出さない
- 先輩は大人の猫、後輩は子猫。柄と顔は参照画像で固定し、この3ショットで変えない
- 実写。カメラは見守りカメラの高い角だけ。猫の目線と混ぜない
- Imagine は1生成1ショット、2〜5秒、動きは1つ、カメラは固定。光と質感を書く。ロゴ、ブランド、パッケージ、画面、時刻は禁止
- 同じプロンプトを使い回さない。最後のショットをループして尺を埋めない
- 合計 12.0秒（4.0 + 4.0 + 4.0）。10〜15秒の範囲

生成前の確認（全部はい、になるまで投げない）:

1. 1ショットだけか
2. 動きは1つか
3. カメラは固定の高角か
4. 参照画像から始め、柄を変えていないか
5. カメラ、光、質感が書いてあるか
6. 実写か
7. 文字、字幕、ロゴの禁止が入っているか
8. 前のショットと同じ文ではないか

## 1. タイトル案

画面には出さない。投稿時のタイトル。

1. 見守りカメラで留守番中を隠し撮りしたら、先輩が止めていた
2. 見守りカメラで留守番を開いたら、何事もなかったことになっていた
3. 見守りカメラの角から見たら、後輩の前足を先輩が止めていた

本採用は1。2と3は、同じ12秒に付け替えられる予備。

## 2. ショット表

場所は3ショットとも同じ。昼の和室寄りのリビング。窓は画面左。低い棚が画面右。床は木目。カメラは天井近くの角に固定し、斜め下を見る。筐体のロゴは映さない。アプリ画面は映さない。

口は3ショットとも閉じたまま。日記の声は飼い主で、猫の口パクには合わせない。尺は、そのショットの1つの動きが終わる長さに合わせる。

| # | 秒 | 狙い | 開始状態 | 動き（1つ） |
|---|---|---|---|---|
| 1 | 0.0–4.0 | 角のカメラの席に座らせる。商品名は出さない | 先輩は座って止まっている。後輩は棚の前にいる | 後輩の前足が、棚の無地の箱へ一回上がり、上がったまま止まる |
| 2 | 4.0–8.0 | 人がいない部屋で、先輩が止めた、という事実 | 後輩の前足はすでに上がっている。先輩の前足はまだ床にある | 先輩の前足が一回だけ降りて、後輩の前足の上で止まる |
| 3 | 8.0–12.0 | 戻った部屋は何事もない。記録が無いと分からない | 2匹は棚の下に座っている。箱は棚に残っている | 先輩が、棚から部屋のほうへ顔を一回だけそらす。後輩は動かない |

### ショット1の Imagine プロンプト（4秒）

```
Photorealistic natural home video, as if recorded by a pet camera. Vertical 9:16, 1080x1920. One continuous 4-second shot, no cuts. Camera: locked off, mounted high in a room corner, looking down across a wooden floor toward a low shelf. Lighting: soft afternoon daylight from a window on the left, gentle floor shadows, no spotlight. Texture: visible wood grain, matte plaster wall, a plain unlabeled cardboard box on the shelf. Cats only. Start from the locked reference images of the same adult cat and the same kitten. Keep their coats, faces, and size relationship unchanged. No humans, no dogs. No text, no captions, no subtitles, no watermark, no logos, no brand names, no packaging print, no screen, no app UI, no timestamp.

Start state: the adult cat is already sitting still on the floor. The kitten is already standing at the low shelf. Mouths stay closed. The only motion is the kitten's one forepaw rising once toward the plain box and remaining raised. The adult cat does not move.
```

### ショット2の Imagine プロンプト（4秒）

```
Photorealistic natural home video, continuing a corner pet-camera recording. Vertical 9:16, 1080x1920. One continuous 4-second shot, no cuts. Camera: locked off in the same high corner, angled down at the low shelf and the wooden floor. Lighting: the same soft afternoon window light from the left, with the shelf edge casting a short shadow. Texture: wood grain under the paws, matte wall, the same plain unlabeled box still on the shelf. Cats only. Start from the locked reference images of the same adult cat and the same kitten. Do not redesign either cat. No humans, no dogs. No text, no captions, no logos, no brand marks, no readable print, no phone, no UI, no clock.

Start state: the kitten's one forepaw is already raised against the box. The adult cat is seated beside the kitten, with both forepaws still on the floor. Mouths stay closed. The only motion is the adult cat's one forepaw coming down once onto the kitten's raised paw and staying there. The kitten does not add another movement.
```

### ショット3の Imagine プロンプト（4秒）

```
Photorealistic natural home video from the same high corner pet camera. Vertical 9:16, 1080x1920. One continuous 4-second shot, no cuts. Camera: locked off, high corner, looking down. Lighting: quiet afternoon side light, slightly dimmer on the far wall, no lamp flare. Texture: wooden floor, soft shadow under the two cats, the plain box still sitting on the low shelf. Cats only. Start from the locked reference images. The adult cat and the kitten keep the same coats and faces as the previous shots. No humans, no dogs. No text, no subtitles, no logos, no brand, no screen, no timestamp, no watermark.

Start state: both cats are already seated under the shelf, looking toward the box, mouths closed. The only motion is the adult cat turning its head once away from the shelf, toward the empty room. The kitten stays still.
```

編集は、この3本を順につなぐ。クロスフェードは0.2秒以内。黒味で埋めない。4秒のクリップをループしない。

## 3. ナレーション

あとから音声合成で足す。声は落ち着いた大人の女性。日記を読む速さ。画面には出さない。プロフィール、リンク、商品名、価格は読まない。

句点でショットを切る。各文は、その4秒の動きが終わるまでに読み終わる長さ。目安は、落ち着いた読みで1秒あたり4モーラ前後。

| 秒 | 読む文 | モーラの目安 | 絵 |
|---|---|---|---|
| 0.0–4.0 | 留守番のカメラを、あとから開いた。 | 17 | 後輩の前足が上がる |
| 4.0–8.0 | 後輩が手を出して、先輩が止めた。 | 18 | 先輩の前足が降りる |
| 8.0–12.0 | 戻った部屋は、何事もなかった。 | 16 | 先輩が顔をそらす |

通し:

```
留守番のカメラを、あとから開いた。後輩が手を出して、先輩が止めた。戻った部屋は、何事もなかった。
```

合成が4秒に収まらない文は、語を足さず、間を詰める。別の説明を足さない。

## 4. 概要欄

URLは置かない。先頭が広告表記。誘導先はチャンネルのリンク1本。

```
広告
見守りカメラで留守番中を隠し撮りしたら、先輩が止めていた。
戻った部屋は、何事もなかった。

見る点は、チャンネルのリンクに置いてあります。
#PR
```

## 5. 固定コメント

URLは置かない。

```
広告。見る点はチャンネルのリンクにあります。
```

## 6. カメラが欲しくなる一文

戻った部屋は何事もないままなので、先輩が止めた前足は、角の見守りカメラを開かないと残らない。
