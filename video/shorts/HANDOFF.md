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

箱の -15.0 / -1.5 / 10.467秒は BGM 比 0.70 と一致する。VM の -16.4 は比 0.15 に圧縮を足したファイル。圧縮を外した比 0.15 は -16.9。差の本体は BGM の比率で、TP と長さは同じ。make_short の下地は 0.70 にした。テンプレのペットと金メモの 15% はそのまま。
