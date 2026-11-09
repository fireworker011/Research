# 短尺の1本目

投稿していない。テンプレの `video/HANDOFF.md` と `tools/check_video.sh` は書き換えていない。

## メモ

- Krea と Drive の画像は添付に無かった。jobs.json の path が空なので、顔の無い平面の絵を枠いっぱいに使った。切り抜き合成はしていない。有料プランには上げていない。
- VOICEVOX の CPU エンジンは 127.0.0.1:50021 に無い。予備の edge-tts（ja-JP-NanamiNeural、等倍）にした。有料の声は使っていない。
- 原文のままだと等倍で 8.5 秒までに終わらない。早回しはせず、言葉を削った。採用した読み: 「友だちに写真頼むの。」1.69秒、「だから撮ってくれる人に頼んだ。」2.07秒、「外の光で撮ってもらった。」1.85秒、「三脚は、持ってこなくていい。」2.11秒。間は 0.20 秒。
- 台本が指す subs/*.srt は添付に無かった。字幕の節から作り、映像に焼いたものと同じ内容を video/shorts/subs/2026-11-03-婚活-tanomeru-hito.srt に書いた。PR は 8.5〜10.5 秒だけ。
- 音量のやり直し: 0 回（上限 3）。BGM は自作の正弦波で、声の実効値の約15%。
- 投稿・公開はしていない。A8 の URL は置いていない。

## 音量

I=-14.40 LUFS / TP=-2.50 dBFS

## check_video.sh

```
M1   PASS コンテナ=mov,mp4,m4a,3gp,3g2,mj2（mp4系）
M2   PASS 映像コーデック=h264（許可: h264）
M3   PASS 解像度=1080x1920
M4   PASS fps=30.00
M5   PASS 長さ=10.500000秒（8〜60秒）
M6   PASS 音声=aac
M7   PASS pix_fmt=yuv420p
M8   PASS 平均音量=-14.9dB
M9   PASS 冒頭1秒に0.5秒以上の黒画面なし
M10  PASS 縦長（9:16）
---
ファイル: /agent/repos/Research/output/00_確認待ち/2026-11-03_婚活/2026-11-03-婚活-tanomeru-hito.mp4 / ライン: konkatsu / 機械チェック 10行
結果: 機械チェックは全行PASS。続けて checklist の手で見る行を確認する。
```

exit=0
