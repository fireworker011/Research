# ナレーションを足すときの音声

Imagine のクリップには、すでに声が入っている。そこにこちらのナレーションを重ねると、声が二重になる。

ナレーションを足すときは、元の音声ストリームを混ぜない。音量を下げるのでも、ダッキングするのでもない。ffmpeg では `-an` で落とし、完成ファイルの音声入力はナレーションと BGM だけにする。

- BGM は声の振幅の 0.15（約 -16.5 dB）。
- 金メモの話速の初期値は VOICEVOX の speedScale 1.12。pitchScale は 0。
- 金メモの行間は 0.16 秒（無音の端を含めても 0.3 秒を超えないようにしている）。シーンの長さは、その声の長さに合わせる。
- 最後の 2 秒だけ PR。商品 URL は入れない。

`shorts-stock/finish.sh`（PR #203）の `mix_voice` は、クリップの音声を `bed` として音量 1.0 で残し、ナレーションを重ねている。ナレーションがあるときは、その bed を無音に置き換える。

```bash
if [[ "$narration" == "yes" ]]; then
  ffmpeg -y -nostdin -loglevel error -f lavfi -i "anullsrc=r=48000:cl=stereo" \
    -t "$picture_sec" -ar 48000 -ac 2 "$work/bed.wav"
fi
```

この置き換えは、ナレーションを足す直前に行う。ナレーションが無い本は、これまでどおりクリップの音を残してよい。`shorts-stock/finish.sh` 本体の修正は `cursor/mute-imagine-bed-bb29` にある。

## このフォルダで書き直した本

素材がリポジトリにあったものだけ。投稿はしていない。

- Imagine 5本: `affiliate-shorts/v2/retrofit/src/<題名>.mp4` の音声を消して、ナレーションと BGM だけを乗せた。
- 金メモ 01–03: 無音の `video_noaudio.mp4` を、話速 1.12・行間 0.16 秒に合わせて縮めた。

## 書き直せなかった本

- 金メモ 04–10。各フォルダに `video_noaudio.mp4` が無い。あるのは `narration.txt` `subs.srt` `yomi.csv` `description.txt` `script.md` `pr_last2s.txt`。
- `shorts-stock/` の Imagine パックは IMAGINE.md と `voice/narration.wav` が 109 本。絵の mp4 はプレースホルダ 2 本だけで、本編クリップは無い。
