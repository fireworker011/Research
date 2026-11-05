# 検査: 完成動画の長さ判定を置き換える（2026-11-05）

PCにはまだ置かない。投稿しない。公開しない。本編をレンダーしない。音声を足さない。既存の未完成PRはマージしない。

このファイルは、人間がPCの古い `check_video.sh` を正規版に差し替えるときの手順。クラウド側では実行していない。

## 正規版

PCへ渡す正規版は `tools/check_video.sh`。

- 続きのブランチ: `cursor/final-check-8-10-5-18fe`
- 元のチェッカー: draft PR #261（`cursor/script-lint-20261028-c032`）の `tools/check_video.sh`
- 下書きも `--final` も、ペットと金メモは 8.0〜10.5秒（端を含む）
- `--final` は音声だけが追加で厳しい。音声が無い、aac でない、mean_volume が -45dB 以下、は不合格のまま
- 10.500±0.050 の等値判定は使わない

配布のスナップショット:

| 場所 | 長さ |
|---|---|
| draft PR #301 `animatics/20261104-night/check_video.sh` | 通常の M5 はすでに `lo=8.0` `hi=10.5`。`--final` は長さを上書きしない。M13 と M14 は無い |
| `animatics/20261102-night` と `20261103-night` | ペット 8〜50秒、金メモ 8〜60秒。完成の範囲ではない |
| PC `C:\Users\hp\Documents\grokbuild\out\v1104-pr300-shorts\check_video.sh` | 古い。通常はレーン別の広い範囲、`--final` だけ `abs(duration-10.5)<=0.05` |
| PC `C:\Users\hp\Documents\grokbuild\out\v1104-pr301-shorts\check_video.sh` | 通常判定は `lo=8.0` `hi=10.5` が既にある。`--final` は下記で確認する |

PCにコピーするのは、このブランチの `tools/check_video.sh` だけ。上のスナップショットはコピー元にしない。

## PCでやること

1. 古いファイルを残す。`check_video.sh` を `check_video.sh.bak-10.5eq` にコピーする。上書きしない。
2. このブランチの `tools/check_video.sh` を、次の場所の `check_video.sh` として置く。
   - `C:\Users\hp\Documents\grokbuild\out\v1104-pr300-shorts\check_video.sh`
3. `v1104-pr301-shorts\check_video.sh` を開く。`--final` の長さがまだ `abs(duration-10.5)<=0.05` なら、同じ正規版に差し替える。すでに 8.0〜10.5秒なら、そのファイルは触らない。
4. 差し替え後のファイルに、コメント以外の `abs(...10.5...)` が残っていないことを見る。

## 動作確認

リポジトリ側の確認は `bash tools/check_video_duration_test.sh`。合成の単色mp4を一時ディレクトリに作り、終わったら消す。

PCでも同じことを見る。bash、ffmpeg、ffprobe、python3 がある場所で、差し替え後の `check_video.sh` に対して行う。本編のmp4は使わない。

長さは 24fps のフレーム数で作る。色は青（`0x2244aa`）。完成の確認には 440Hz の正弦波を aac で入れる。これは判定用で、ナレーションではない。

| フレーム | ffprobe | モード | レーン | M5 |
|---:|---:|---|---|---|
| 192 | 8.000000 | `--final` | pet | PASS |
| 216 | 9.000000 | `--final` | pet と kane | PASS（古い等値判定では FAIL） |
| 252 | 10.500000 | `--final` | kane | PASS |
| 253 | 10.541667 | `--final` | pet | FAIL（古い等値判定では PASS） |
| 191 | 7.958333 | `--final` | pet | FAIL |
| 264 | 11.000000 | `--final` | kane | FAIL |
| 216 | 9.000000 | 下書き | pet | PASS。音声なしでも M6 と M8 は PASS |
| 216 | 9.000000 | `--final` | pet | 長さは PASS。音声が無ければ M6 と M8 は FAIL |

M1〜M14 の行は、どれも出力から消えない。M12 は文字の帯が無ければ SKIP。

合格の表示は `8.0〜10.5秒（完成）`。`10.500±0.050` とは出さない。
