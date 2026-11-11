# 短尺の直し（fix2 と fix3）

投稿していない。マージしていない。有料契約はしていない。テンプレの `video/HANDOFF.md` と `tools/check_video.sh` は書き換えていない。

金メモの実額は出してよい（2026-11-10 8:52 JST に本人が確認）。他のラインの金額は今までどおり不合格。tanomeru-hito の本番は、v2 の台本と素材が来るまで走らせていない。

## 1. setup

`bash video/shorts/setup_voicevox.sh`

```
PASS 生存確認 http://127.0.0.1:50021/version "0.26.1"
```

exit=0

公式の Linux CPU 版 0.26.1。話者は `video/shorts/lines.json`。冥鳴ひまりは 14、青山龍星は 13、四国めたんの標準は 2。エンジンで確認した。

## 2. 本番（tanomeru-hito、素材が無い）

`python3 make_short.py video/shorts/scripts/2026-11-03-婚活-tanomeru-hito.md konkatsu --jobs video/shorts/jobs/2026-11-03-婚活-tanomeru-hito.json`

```
ASSET FAIL カット1の箱のパスが無い
SRC PASS カット1 自作 （自作・IDなし）
ASSET FAIL カット2の箱のパスが無い
SRC PASS カット2 自作 （自作・IDなし）
ASSET FAIL カット3の箱のパスが無い
SRC PASS カット3 自作 （自作・IDなし）
結果: FAIL 素材が欠けているので止める。仮の絵は --dry だけ。
```

exit=1

## 3. --dry の検品

`python3 make_short.py video/shorts/fixtures/dry-fit.md konkatsu --jobs video/shorts/fixtures/dry-fit.json --dry --final`

本編の声は 2.79 秒で 8.5 秒以内。ファイル名は `dry-fit_DRY.mp4`。声は edge-tts。

```
M1   PASS コンテナ=mov,mp4,m4a,3gp,3g2,mj2（mp4系）
M2   PASS 映像コーデック=h264（許可: h264）
M3   PASS 解像度=1080x1920
M4   PASS fps=30.00
M5   PASS 長さ=10.500000秒（8〜60秒）
M6   PASS 音声=aac
M7   PASS pix_fmt=yuv420p
M8   PASS 平均音量=-13.3dB
M9   PASS 冒頭1秒に0.5秒以上の黒画面なし
M10  PASS 縦長（9:16）
M11  PASS I=-14.0 LUFS / TP=-1.5 dBTP（-14±1、TP≦-1.5）
M12  PASS 映像=10.500000秒 音声=10.500000秒（差≦0.05秒）
M13  PASS 長さ=10.500000秒（上限10.5秒）
結果: 機械チェックは全行PASS。続けて checklist の手で見る行を確認する。
```

exit=0

## 4. 尺を超えたダミーの lint

`python3 make_short.py video/shorts/fixtures/over-duration.md konkatsu --dry --lint-duration`

```
DUR FAIL 本編の終わりが11.26秒（上限8.5秒、2.76秒超え、声の合計10.46秒）
LINE PASS 「友だちに写真頼むの、気まずくて。」 2.55秒
LINE PASS 「だから、撮ってくれる人に頼んだ。」 2.36秒
LINE FAIL 「外の光で、撮ってもらった感じの写真。」 3.12秒（残り2.99秒に入らない）
LINE FAIL 「三脚は、もう持ってこなくていい。」 2.43秒（残り0.00秒に入らない）
結果: FAIL 尺を超えた。言葉は削らない。台本に戻す。
```

exit=1

## 足した check の FAIL 実測

合格の mp4 を 13 秒に延ばし、音を上げ、音声を映像より短くしたファイル。

```
M11  FAIL I=-8.0 LUFS / TP=8.6 dBTP（-14±1、TP≦-1.5）
M12  FAIL 映像=13.000000秒 音声=11.717000秒（差≦0.05秒）
M13  FAIL 長さ=13.000000秒（上限10.5秒、短尺の本番は --final の上限）
結果: FAIL 3行（M11 M12 M13）→ 止める。上のFAIL行を報告して直す。
```

exit=1

全文は `review/fail-demo/check.txt`。合格側は `review/dry-fit/check.txt`。

## 金メモの実額（2026-11-10 確認）

tanomeru-hito の本番は走らせていない。

金メモ:

```
MONEY	PASS（実額は出してよい: 15000円）
```

exit=0

ペット（他のラインは同じ禁止）:

```
MONEY	FAIL（15000円）
```

exit=1

婚活:

```
MONEY	FAIL（15000円）
```

exit=1

`python3 tools/script_lint.py --self-test` は exit 0。金額の自己テストは「金メモの実額は合格」「ペットの金額は不合格」。

## M11 の箱と VM（同じ v2 の声）

基準は -14±1 LUFS、TP≦-1.5 のまま。tanomeru-hito の本番は回していない。

同じ3本の声（合計 2.92 秒、本編 8.5 秒の 34.3%）を loudnorm 2パス（linear、I=-14、TP=-1.5、LRA=11）に通した。

| BGM比 | I | TP | 長さ |
| --- | --- | --- | --- |
| 0.15（これまでのコード） | -16.9 LUFS | -1.5 dBFS | 10.466667秒 |
| 0.70 | -15.0 LUFS | -1.5 dBFS | 10.466667秒 |

箱の -15.0 / -1.5 / 10.467秒は BGM 比 0.70 と一致する。VM の -16.4 は比 0.15 に圧縮を足したファイル。圧縮を外した比 0.15 は -16.9。その後、BGM は声の約15%へ戻し、ffmpeg を静的ビルドに固定した。

## ffmpeg を固定した v3（声OK前・投稿用に使わない）

版: `ffmpeg version n8.1.3-34-ga35157abb9-20261109`

取得元: https://github.com/FFmpeg-Builds/FFmpeg-Builds/releases/download/autobuild-2026-11-09-12-42/ffmpeg-n8.1.3-34-ga35157abb9-linux64-gpl-8.1.tar.xz

BGM は声の約15%。コンプレッサーは使っていない。loudnorm は2パス、linear、I=-14、TP=-1.5。

VM: I=-14.5 LUFS、TP=-1.5 dBTP、長さ 10.466667 秒。`check_video.sh konkatsu` は exit 0。声の合計 6.02 秒、本編の終わり 6.62 秒、RATIO PASS 70.8%。

字幕はセリフ1行につき1本。アクセント句では切らない。この時点の script_lint は、台本の秒と字幕の秒が違うため exit 1。次の節で、実際の切れ目に切り替えた。

## 切れ目は読んだ長さ（声OK前・投稿用に使わない）

台本の秒は目安。切れ目は行と行の無音の真ん中。最後のカットは本編の終わり 8.5 秒まで。絶対パスの台本でも動く。

VM で `/tmp/x/2026-11-10-婚活-tanomeru-hito-v3.md`（sha256 60358a039b4d334476de841ef36155fcd63b9aa716b27dae926e128518fc4223）を指定した。make_short は exit 0。check_video.sh konkatsu は exit 0。I=-14.5 LUFS、TP=-1.5 dBTP、長さ 10.500000 秒。script_lint は exit 0。

timing.json:

```
content_end 8.5
カット1 0.0-2.908 友だちに写真頼むの、気まずくて。
カット2 2.908-5.157 だから撮ってくれる人に頼んでみた。
カット3 5.157-8.5 三脚はもういらない。
PR 8.5-10.5
```

字幕を 0.200-3.200 に延ばしたダミーは `FAIL（0.200-3.200が0.000-2.908からはみ出す）`、script_lint exit 1。

箱で同じ手順:

```
bash video/shorts/setup_voicevox.sh
export PATH="/tmp/ffmpeg-static:$PATH"
ffmpeg -version | head -1
python3 make_short.py /home/box/shorts/daihon/scripts/2026-11-10-婚活-tanomeru-hito-v3.md konkatsu --jobs <jobs.json> --out <台本名>.mp4
bash video/shorts/check_video.sh <台本名>.mp4 konkatsu
python3 tools/script_lint.py <台本・字幕・timing.json・cuts-for-pc.md があるディレクトリ>
```
