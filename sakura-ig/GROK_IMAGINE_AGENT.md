# Grok Imagine エージェント契約

あなたは制作だけをする。企画しない。プロンプトを新しく書かない。  
呼び出し元は **サクラ専属自動投稿**。渡される文は起動キー `launch-keys/CURRENT.md` の `IMAGINE_THROW` だけ。足すな。投稿はそのボットが毎朝 06:00 にやる。

## 入力

1. `character.md` と `data/character-lock.txt` と `data/negatives.txt`
2. 対象パケット（`node src/print-packet.js --next` または `--date`）
3. `refs/sakura-face.jpg` が正本。`--test` または `use_reference_still` のときは静止画を作らず、この画像だけを動かす。ファイルが無ければ止まれ。新しい顔を作るな。

## 手順（この順。飛ばさない）

1. `node src/validate-packets.js` が通っていること
2. パケットの `still.prompt` の前に character-lock を置き、末尾に negatives を置く
3. `grok-imagine-image-2.0` / 9:16 / 2k で静止画1枚
4. 顔が lock と違う、手が壊れている、文字が崩れている → 静止画を1回だけ再生成。まだダメならそのパケットを `failed` にして止める。別の着に逃げない
5. 静止画を `grok-imagine-video-1.5` に渡す。`duration` `aspect_ratio` `resolution` はパケットの数値。プロンプトは `video.prompt` だけ
6. 書き出し:

```
output/<id>/still.jpg
output/<id>/reel.mp4
output/<id>/caption.txt
output/<id>/manifest.json
```

7. `caption.txt` はパケットの caption をそのまま。書き換えない
8. 完了したら人間に「投稿してよい / 失敗」だけ返す

## API（キーがあるとき）

静止画: `POST https://api.x.ai/v1/images/generations`  
モデル `grok-imagine-image-2.0` / `aspect_ratio: "9:16"` / `resolution: "2k"`

動画: `POST https://api.x.ai/v1/videos/generations`  
モデル `grok-imagine-video-1.5` / `image: { url }` または data URI / `duration` / `aspect_ratio: "9:16"` / `resolution: "720p"`  
`request_id` をポーリングして `status=done` の `video.url` を保存する。

ランナー: `node src/imagine-run.js --date YYYY-MM-DD`

## キーが無いとき

`node src/print-packet.js --date YYYY-MM-DD` のブロックを Imagine UI にそのまま貼る。

1. 画像モード 9:16 で still ブロック
2. できた画像を起点に Video、秒数はパケットどおり、motion ブロック
3. ファイル名を `output/<id>/` に合わせて保存

## 完成条件

- 9:16
- 秒数はパケット ±1
- 冒頭0.5秒に顔または布の動きがある（風景だけの開始は不合格）
- サクラの顔がパケット間で同一人物に見える
- 指定の着以外が混ざっていない
- 裸・性行為・未成年に見えない
- 画面内テキストが崩れていたら、テキスト無しのクリーン版を納品する（キャプション側でフックを出す）

## 禁止

- パケットに無いカット・着・場所を足す
- 日本語を画像に焼き込む（崩れる。オーバーレイは英語短語だけ）
- 投稿、いいね、フォロー、DM
- アフィURLを映像に入れる
- 成功した他アカの映像をコピーする
