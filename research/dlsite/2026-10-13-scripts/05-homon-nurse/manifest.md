# 05-homon-nurse 音声の一覧

申請も公開もしていない。数字は 2026-10-13 に測った値。

ファイルの置き場所: `/opt/cursor/artifacts/dlsite-2026-10-13/05-homon-nurse/`
WAV と MP3 と zip は git に入れていない。

WAV は 44.1kHz、16bit、ステレオ。MP3 は 320kbps。
音量の目標は -16 LUFS。表の LUFS は、そのファイルを EBU R128 の積分ラウドネスで測った値。

【】の行は読んでいない。【間：N秒】は無音。【SE】と効果音は入れていない。

成果物の置き場は、1ファイルが 100MiB 以上だと保存時に失敗する。
長いトラックは無音の位置で分け、zip も 90MiB 以下にした。どれも 300MB 未満。

体験版の長さは、台本の【間】をそのまま入れた実測。
台本上の約90秒は、読みを1秒4文字と仮定して【間】を足した秒で、収録の実測ではない。

話者: つくよみちゃん / れいせい。規約は `license.md`。

## 音声

| ファイル | 種類 | 長さ | サイズ | LUFS |
| --- | --- | --- | --- | --- |
| `05-homon-nurse_track-01.wav` | 本編WAV | 243.62秒（4:04） | 42973812 bytes | -16.2 |
| `05-homon-nurse_track-01.mp3` | 本編MP3 | 243.64秒（4:04） | 9746852 bytes | -16.2 |
| `05-homon-nurse_track-02-part-01.wav` | 本編WAV | 504.99秒（8:25） | 89079884 bytes | -15.9 |
| `05-homon-nurse_track-02-part-01.mp3` | 本編MP3 | 505.03秒（8:25） | 20202101 bytes | -15.9 |
| `05-homon-nurse_track-02-part-02.wav` | 本編WAV | 169.07秒（2:49） | 29823156 bytes | -17.9 |
| `05-homon-nurse_track-02-part-02.mp3` | 本編MP3 | 169.12秒（2:49） | 6765758 bytes | -17.9 |
| `05-homon-nurse_track-03-part-01.wav` | 本編WAV | 504.99秒（8:25） | 89079884 bytes | -16.0 |
| `05-homon-nurse_track-03-part-01.mp3` | 本編MP3 | 505.03秒（8:25） | 20202101 bytes | -16.0 |
| `05-homon-nurse_track-03-part-02.wav` | 本編WAV | 388.71秒（6:29） | 68568900 bytes | -16.4 |
| `05-homon-nurse_track-03-part-02.mp3` | 本編MP3 | 388.75秒（6:29） | 15551260 bytes | -16.4 |
| `05-homon-nurse_track-04.wav` | 本編WAV | 430.64秒（7:11） | 75965484 bytes | -16.0 |
| `05-homon-nurse_track-04.mp3` | 本編MP3 | 430.68秒（7:11） | 17228321 bytes | -16.0 |
| `05-homon-nurse_track-05.wav` | 本編WAV | 364.52秒（6:05） | 64302100 bytes | -16.1 |
| `05-homon-nurse_track-05.mp3` | 本編MP3 | 364.56秒（6:05） | 14583685 bytes | -16.1 |
| `05-homon-nurse_trial.wav` | 体験版WAV | 73.3秒（1:13） | 12930716 bytes | -16.4 |
| `05-homon-nurse_trial.mp3` | 体験版MP3 | 73.35秒（1:13） | 2935162 bytes | -16.4 |

## zip

| ファイル | サイズ | 中身 |
| --- | --- | --- |
| `05-homon-nurse_honpen-mp3_01.zip` | 16400332 bytes | `05-homon-nurse_track-01.mp3`、`05-homon-nurse_track-02-part-01.mp3`、`05-homon-nurse_track-02-part-02.mp3`、`05-homon-nurse_track-03-part-01.mp3`、`05-homon-nurse_track-03-part-02.mp3`、`05-homon-nurse_track-04.mp3`、`05-homon-nurse_track-05.mp3` |
| `05-homon-nurse_honpen-wav_01.zip` | 51565519 bytes | `05-homon-nurse_track-01.wav`、`05-homon-nurse_track-02-part-01.wav`、`05-homon-nurse_track-02-part-02.wav`、`05-homon-nurse_track-03-part-01.wav`、`05-homon-nurse_track-03-part-02.wav`、`05-homon-nurse_track-04.wav`、`05-homon-nurse_track-05.wav` |
| `05-homon-nurse_trial.zip` | 1007673 bytes | `05-homon-nurse_trial.mp3` |

`05-homon-nurse_track-02-part-02` の WAV と MP3 は -17.9 LUFS。他のファイルと同じ -16 LUFS 付近へ直した版は作ったが、成果物の置き場が保存を完了せず、置いてあるファイルは測ったこの値のまま。zip の中身も、この測ったファイル。
