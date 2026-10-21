# 実写再現（live_remake）

元動画の秒、ショット順、カメラを固定して、人物を実写に置き換える仕組み。H3 Studio のジョブ `live_remake`。Comfy だけで動く。生成ボタンと公開は人間。

使えるのは、元動画、キャラクター、音の権利を持っている素材だけ。役は `S1`、`S2` と静止画のパスで指す。キャラクターの名前と姿の文は、このリポジトリとシートの骨組みに入れない。

## 課題と解決

| 課題 | 解決 | どこ |
|---|---|---|
| カットの秒が無い。光や衝撃のコマでシーン検出が誤って切る | ffmpeg のシーン検出（既定 0.35）を取り、0.5秒より短いショットは前とまとめる。シートの `cuts` は人が目で直せる | `h3_live_remake.measure`、`merge_cuts` |
| H3 の1本は 124〜345 フレーム（5.167〜14.375秒）。長い元動画は1本にできない | 測ったカットで範囲に詰める。1つのショットが範囲より長いときは等分する。既定の範囲の上限は 8秒 | `plan_spans` |
| 元動画の fps と大きさが H3 と違う | 範囲ごとに 24fps、768P の画面に整形し、最後のコマで要求の長さまで伸ばす。つなぎで測ったフレームに切り戻す | `conform_argv`、`join_argv` |
| 途中で姿が変わる役、場所、小道具の静止画が要る | シートで役ごとに `stills` を形（form）別に持ち、範囲ごとに使う形を指す。場所は `place_still`、小道具は `P1` など。足りないと止まる | `cast`、`place_still`、`props` |
| 範囲ごとの動きとカメラの文 | Grok Build の `video-to-h3-prompt`（MIT）が書く。ここは英語か、ラベルが静止画と合うか、`<Video 1>` 以外が無いかだけを見る | `.cursor/skills/video-to-h3-prompt/` |
| 元の絵の線が実写に残る | 動画は秒、位置、カメラだけ。静止画が顔と衣装。文に実写の固定文を前置きし、見た目は書かない。本体は FastH3 Omni の 8 step INT8。LoRA は anime2real 1.0 を単独で載せる | `_prompt`、`OMNI_FILE` |
| 公式の Ref2VA は遅い | 公開の速度比較は FastH3 V2 の文だけ（640x640）。Omni の画質はここで測っていない。live_remake は 8 step の Omni を使う | `model` |
| anime2real の取得元 | 未登録。Civitai の検索では H3 用が見つからなかった。マイドライブの `h3-weights/loras` に置く | `WEIGHT_NOTE` |
| 静止画が複数 | h3-runner の `--image` は1枚。Comfy の `MiniMaxH3ReferenceToVideo` は `ref_images.ref_image_N` に複数を取る。だから Comfy だけ。`runtime=api` は止める | `_gate` |
| 15秒を超える連続ショット | 等分すると、つなぎ目で動きが段になることがある。連続を取るなら `longform_chunk`（H3 Continuum）。参照画像の当て方は `write-h3-v39-reference-prompts`（MIT） | `.cursor/skills/write-h3-v39-reference-prompts/` |
| 音 | `audio=source` は元動画の音を測った長さで載せる。`generated` は各範囲の音を切ってつなぐ | `join_argv` |
| 出力の fps | 24fps。元が 60fps でも補間はしない | `notes` |

## 残る限界

- 顔、動き、口の動きの完全一致は保証されない。
- 範囲の長さと静止画の数で VRAM が変わる。焼くときは `colab/h3_r2v_core.py` の上限に合わせる。
- 効果線、割り画面、光などの実写への訳は、範囲の文の書き方しだい。
- `colab/_write_studio_nb.py` の `BRANCH` は `cursor/h3-sfw-colab-6dc5`。このコードがそのブランチに入るまで、Colab は古い helper を取る。

## 手順

1. Studio ノートの一番下のセル（元動画を測る）に元動画のパスを書いて実行する。マイドライブの `minimax-h3-comfyui/studio/remake-sheet.json` に骨組みができる。
2. Grok Build の `video-to-h3-prompt` に同じ動画を回す。
3. シートの `cast` に役ごとの静止画、`place_still` と `props` に場所と小道具の静止画を入れる。
4. 各範囲の `cast` に出る役と形、`place`、`props`、`description` を入れる。`description` は手順 2 の出力から、その範囲の動きとカメラだけを貼る。
5. 上のセルで `JOB=live_remake`、`RUNTIME=comfy`、`REMAKE_SHEET` にシートのパスを書いて実行する。`ready` なら、範囲ごとの整形コマンド、静止画、プロンプトが出る。
6. Comfy の Ref2VA で範囲ごとに焼く（人間）。
7. `join_argv` で1本につなぐ。

## シートの形

```json
{
  "schema": "h3-live-remake/v1",
  "source": {"path": "source.mp4", "duration_s": 12.0, "width": 1920, "height": 1080, "fps": 24.0, "has_audio": true},
  "cuts": [4.0],
  "cuts_from": "ffmpeg scene>0.35。0.5秒より短いショットは前とまとめた。目で直してよい。",
  "max_span_s": 8.0,
  "audio": "source",
  "cast": {
    "S1": {"stills": {"default": "s1.png", "armored": "s1-armored.png"}},
    "S2": {"stills": {"default": "s2.png"}}
  },
  "place_still": "street.png",
  "props": {"P1": {"still": "prop.png"}},
  "spans": [
    {"index": 1, "start_s": 0.0, "end_s": 4.0, "cast": {"S1": "default", "S2": "default"}, "place": true, "props": [], "description": "入力", "soundscape": "", "music": "N/A"}
  ]
}
```

確認:

```bash
python3 -m pytest colab/test_h3_live_remake.py colab/test_h3_studio.py -q
```
