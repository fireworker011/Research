# 動画テンプレ3点の実行手順（PC）

投稿しない。YouTube や TikTok へ上げない。A8 の URL はファイルに書かない。商品名は台本のナレと字幕に出さない。尺は 8.0〜10.5 秒、PR は最後の 2 秒、のまま。

## このブランチで直したこと

1. ペット（`video/pet-v2/render_pet.py` と `video/templates/pet-script.md`）
   - 猫の静止画を切り抜いて背景に載せない
   - 平面描画か、渡した 1 枚をそのまま枠に合わせる
   - 本編字幕は冒頭 1 秒のフックだけ。1 秒以降は字幕なし
   - PR は最後の 2 秒（10.5 秒なら 8.5〜10.5 の「広告 #PR」）
2. 金メモ（`video/kanememo/render_kanememo.py` と `video/templates/kane-script.md`）
   - BGM は自作（`video/common/flat_mix.py` の正弦波）。出どころは `video/kanememo/BGM-CREDIT.md`
   - 音量は声の実効値の約 15%
   - 画面に「BGM: 自作」
3. 台本 lint（`tools/script_lint.py`）
   - 表・見出しと台詞の用語がずれると FAIL（加給 / 加算）
   - ペットと金メモは、結論の 1 文が最後の 1.5 秒より前に終わることを必須
   - ペットの本編字幕がフック以外にあると FAIL
4. `tools/check_video.sh` の M15
   - 声が切れた区間にも音が残るか。残っていれば PASS。無ければ FAIL
   - 下書きで音声が無いときは SKIP。`--final` で BGM が無いときは FAIL

## PC で必要なもの

- Python 3
- ffmpeg（ffprobe も同じ場所）
- bash（Git Bash か Cygwin）
- 日本語と数字とアルファベットが入った字体。Linux は文泉驛微米黑。Windows は游ゴシックかメイリオ

Windows で字体を明示する:

```
set VIDEO_FONT=C:\Windows\Fonts\YuGothM.ttc
```

Git Bash なら `export VIDEO_FONT="/c/Windows/Fonts/YuGothM.ttc"`。

## 試作（ダミー。投稿しない）

リポジトリのルートで実行する。出力は `/tmp` か、PC なら作業フォルダ。mp4 はコミットしない。

```
python video/pet-v2/render_pet.py --out /tmp/pet.mp4
python video/kanememo/render_kanememo.py --out /tmp/kane.mp4
python video/kanememo/render_kanememo.py --out /tmp/kane-nobgm.mp4 --no-bgm
```

1 枚の画像をそのまま使うとき（切り抜かない）:

```
python video/pet-v2/render_pet.py --image path\to\one.png --out /tmp/pet-still.mp4
```

## 確認

```
bash tools/check_video.sh /tmp/pet.mp4 pet --final
bash tools/check_video.sh /tmp/kane.mp4 kane --final
bash tools/check_video.sh /tmp/kane-nobgm.mp4 kane --final
python tools/script_lint.py --self-test
python tools/script_lint.py video/templates/fixtures/term-mismatch
python tools/check_cuts.py video/templates/cuts-for-pc.md both
bash tools/check_video_duration_test.sh
```

期待:

- pet と kane の `--final` は終了コード 0。M15 は PASS
- BGM なしは M15 が FAIL、終了コードは 0 以外
- 用語ずれの台本は lint が FAIL（画面は加給、台詞は加算）
- `--self-test` は最後が「自己テスト: OK」

## Linux で確認したこと（2026-11-09）

ダミー入力で試作し、`check_video.sh --final` を実行した。

| ファイル | 結果 | M15 |
| --- | --- | --- |
| pet.mp4（平面描画） | PASS（終了 0） | PASS（約14%） |
| kane.mp4（BGM あり） | PASS（終了 0） | PASS（約15%） |
| kane-nobgm.mp4 | FAIL（終了 1） | FAIL（声以外の音が無い） |
| pet-still.mp4（1枚をそのまま） | PASS（終了 0） | PASS |

`script_lint.py --self-test` は OK。用語ずれのテスト台本は FAIL（画面は加給、台詞は加算）。ほかの項目は PASS。`check_video_duration_test.sh` は ALL PASS。尺の範囲（8.0〜10.5 秒）は変えていない。

目視: ペットは 0.4 秒に「押さなくなった？」、3 秒は字幕なし、9.2 秒に「広告 #PR」。金メモは表と「BGM: 自作」、6〜8.5 秒に「結論: 表の3行。」。
