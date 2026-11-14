# kanzen-saigen

参考動画の「型」（カットの切れ目、各カットの尺、構図の山）を数値にして、AI で作ったカットをその尺どおりにつなぐ。生成 API は呼ばない。Linux 上の ffmpeg と Python 3 だけで動く。

入口は 3 本。

| スクリプト | 役割 |
| --- | --- |
| `split_ref.py` | 参考動画をカットに分け、`timeline.json` と Start / Peak / End の PNG を書く |
| `finish.py` | `genNN.mp4` から先頭 0.25 秒を外し、元のカット尺だけを 1080x1920 でつなぐ |
| `qc.py` | 尺、切れ目、黒フレーム、LUFS を判定して `QC.md` と `contact.png` を書く |

## 必要なもの

- Linux
- ffmpeg / ffprobe（このリポジトリの確認環境は ffmpeg 6.1）
- Python 3
- PySceneDetect、OpenCV、NumPy

```bash
cd tools/kanzen-saigen
python3 -m pip install -r requirements.txt
```

`scenedetect` は `opencv-python` も依存に持つ。ヘッドレス環境では、依存を分けて入れる。

```bash
python3 -m pip install numpy 'opencv-python-headless>=4.9' click platformdirs tqdm
python3 -m pip install 'scenedetect>=0.6.4,<0.8' --no-deps
```

## 1. 参考動画を割る

```bash
python3 split_ref.py ref.mp4 outdir
```

PySceneDetect の ContentDetector、threshold 27（ライブラリ既定の最短 15 フレーム）でシーンを切る。各カットはフレーム境界で切り出して `cut01.mp4`、`cut02.mp4` … になる。

`outdir/timeline.json` には、動画全体と各カットの開始・終了・秒・フレーム数を書く。

- `start_sec` / `end_sec` は参考動画の先頭からの秒
- `duration_sec` はそのカットの秒
- `frame_count` はフレーム数（`end_frame` は終端を含まない）
- `peak_frame` / `peak_sec` は、そのカットの中で直前フレームとの差分が最大のフレーム。差分は OpenCV の絶対差の平均。同点なら早いフレーム。`peak_sec` はカット先頭からの秒
- `cutNN_start.png` / `cutNN_peak.png` / `cutNN_end.png` がその 3 枚

15 フレームより短いカットは、PySceneDetect の既定で隣に吸収されることがある。

## 2. 生成カットを尺に合わせる

生成側は `gen_dir/gen01.mp4` のように、timeline の `index` と同じ 2 桁の番号で置く。想定の長さは 5〜6 秒。先頭 0.25 秒は捨て、その時刻以降の最初のフレームから、元カットの尺だけを使う。30fps では 0.25 秒がフレームの途中にあるので、開始は 0 始まりのフレーム 8（時刻 8/30 秒）になる。

```bash
python3 finish.py outdir/timeline.json gen_dir out.mp4 --audio voice.wav
```

出力は 1080x1920、H.264、`yuv420p`。`--fps` は `24` か `30`。省略したときは timeline が 24 か 30 ならそれに合わせ、それ以外なら指定が必要。

| オプション | 動き |
| --- | --- |
| `--speed 2` | 生成側を 2 倍速で読む。出力の尺は元カットのまま（読む長さが 2 倍になる） |
| `--peak-align` | 生成側の動きの山（先頭 0.25 秒より後）を、元カットの `peak_sec` に合わせる。窓がはみ出すときは、先頭 0.25 秒より前には出さず、尺が収まる位置まで戻す |
| `--xfade 0.1` | カットの境を 0.1 秒のクロスフェードにする。省略時、または `0` のときは突き合わせのカット。重なった秒 ×（カット数 − 1）だけ全体が短くなる |
| `--grain` | 細いフィルムグレイン |
| `--vignette` | 四隅を少し落とす |
| `--shake` | 105% に拡大したうえで、数ピクセルの手ブレ |
| `--audio voice.wav` | 映像の長さに切り（短ければループし）、integrated loudness を -14 LUFS にそろえて AAC で載せる |

## 3. 判定する

```bash
python3 qc.py outdir/timeline.json out.mp4
```

`out.mp4` と同じフォルダに `QC.md` と `contact.png` を書く。`QC.md` の 1 行目が `PASS` か `FAIL`、2 行目がその根拠。終了コードは PASS が 0、FAIL が 1。

判定は次の 4 つ。全部満たしたときだけ PASS。

- 全体尺が timeline の `duration_sec` と ±0.2 秒以内
- 各カットの切れ目が、timeline から決まるフレーム位置と ±2 フレーム以内（境目の前後でフレーム差分の山があること）
- `blackdetect` で黒フレームがない（画面の 98% 以上が黒のフレーム）
- 音声の integrated loudness が -15〜-13 LUFS

`contact.png` は各カットの中央フレームを横に並べたもの（4 枚を超えると折り返す）。

`--xfade` を使うと全体が短くなるので、尺の判定は通らない。QC は突き合わせのカットを前提にしている。

## テスト

`tests/ref_3cut.mp4` は ffmpeg の `testsrc` を赤・緑・青の地に重ねた 3 カット（2.0 秒、1.5 秒、2.0 秒、30fps、1080x1920）をつないだもの。`tests/gen/gen01.mp4` から `gen03.mp4` は各 6 秒で、先頭 8 フレームだけ別色。`tests/audio.wav` は 440Hz のサイン波。

```bash
python3 tests/make_fixtures.py
python3 tests/test_pipeline.py
```

`test_pipeline.py` はフィクスチャを作り直し、split → finish → qc を通して `PASS` を確認する。加えて、peak 合わせ、グレイン／ビネット／手ブレ、2 倍速、24fps でも QC が通ること、`--xfade 0.1` だと全体が 0.2 秒短くなることを見る。
