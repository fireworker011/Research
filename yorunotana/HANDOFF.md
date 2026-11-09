# 14階（yorunotana）引き継ぎ

Cursor 担当の描画、Muse 担当の音声、Grok Build 担当の PowerShell を、このフォルダに実装してある。実行するのは Windows PC（PowerShell、`python`、`ffmpeg`、`ffprobe`）。A8 の URL はリポジトリに置いていない。

## PCでの実行手順

1. リポジトリを取得する。

```powershell
git clone <このリポジトリのURL>
cd Research
git pull
cd yorunotana
```

2. 依存を入れる。

```powershell
python -m pip install -r requirements.txt
```

3. VOICEVOX エンジンを起動し、`http://127.0.0.1:50021` で待受していることを確認する。話者IDの既定は `13`（標準の青山龍星・ノーマル）。別の低音男性にするときは `-Speaker` を変える。読み上げ速度は等倍（`speedScale = 1.0`）固定。

4. `yorunotana` をカレントにした状態で、ジョブごとに実行する。スクリプト自身も自分の場所へ移動するので、フルパスで呼んでもよい。

```powershell
powershell -ExecutionPolicy Bypass -File .\build-yorunotana.ps1 -JobFile .\jobs-v2\episode_day2.json
powershell -ExecutionPolicy Bypass -File .\build-yorunotana.ps1 -JobFile .\jobs-v2\episode_day3.json -Speaker 13
```

5. 成功の判定は、その場に上書きされる `LAST_RESULT.txt` が `PASS` で始まること。尺の合格は **60.0〜70.0秒**（2026-11-09 21:25 JST の決定）。形は `PASS | <job_id>.mp4 | 62.8s | PR:True | freeze=0.00s | silence=0.00s`。60秒未満でも70秒超でも、2.0秒以上のフリーズでも無音でも、先頭は `FAIL` で測った値が入る。詳細は `REPORT.md`（UTF-8 BOM）。`LAST_RESULT.txt` は UTF-8（BOMなし）。どちらも実行のたびに上書きされるので、day2 の1行を残すなら次を走らせる前にコピーする。

再実行するときは、このブランチを pull してから上の 4 をそのままもう一度走らせる。台本 JSON と `speedScale` は変えていない。

VOICEVOX を使わない長さ確認だけするときは `-DummyTts` を付ける。このスイッチはネットワークへ繋がない。

```powershell
powershell -ExecutionPolicy Bypass -File .\build-yorunotana.ps1 -JobFile .\jobs-v2\episode_day3.json -DummyTts
```

## 何がどこにあるか

| ファイル | 役割 |
| --- | --- |
| `src/render_frames.py` | JSON の scene を 1080x1920 / 60fps で描き、音声を載せて MP4 にする |
| `src/build_audio.py` | ナレーション WAV、`audio_timing.json`、`master_audio.wav` |
| `build-yorunotana.ps1` | 音声 → 描画 → ffprobe。UTF-8 BOM |
| `tools/make_assets.py` | BGM と SE を numpy で作る。他人の音源は使わない |
| `tools/make_dummy_timing.py` | 各 segment をちょうど 2.0 秒にした仮タイミング |
| `tools/check_pr_badge.py` | 右上 PR 領域の画素チェック |
| `tools/verify_mp4.py` | ps1 と同じ合否を Python で出す |
| `tools/content_length.py` | dummy-tts と、あれば VOICEVOX の実測の長さ。60〜70秒との差 |
| `jobs/episode_day2.json` `jobs/episode_day3.json` | 入力。原文のバイト列のまま |
| `ORDER-20261109-0634.md` | 依頼原文。一字も変えていない |

描画コマンド（ps1 の Step 2 と同じ）:

```text
python src/render_frames.py --job <json> --timing out/temp_audio/audio_timing.json --audio out/temp_audio/master_audio.wav --out out/<JobId>.mp4
```

パスは `pathlib` なので `\` でも `/` でもよい。

## フォント

太字ゴシックをこの順で探す。

1. `YuGothB.ttc` / `YuGothB.ttf`（游ゴシック Bold）
2. `BIZ-UDGothicB.ttc`
3. `meiryob.ttc`（メイリオ Bold）
4. Noto Sans CJK Bold（JP のフェイス）
5. Noto Sans CJK Regular、その後に游ゴシック Medium / メイリオ / MS ゴシック

この Linux では `Noto Sans CJK JP Bold` を使った。

## 音声

- 読む順は segments の `subtitle`、`choice_card.narration`、`day_end_card.narration`、有効なときだけ `promo_outro.narration`。
- 各発話の終わりに segment の `pause_after_ms` を足す。カードに pause は無い。
- promo の見た目は `steps[].duration_sec` の合計より短くしない（day3 は 8 秒）。
- BGM `assets/bgm/dark_ambient_drone.wav` を -18 dB で全編ループ。SE は segment の開始に混ぜる。ファイルが無ければ `tools/make_assets.py` が生成する。
- VOICEVOX に繋がらないときは、メッセージを出して終了する。別の TTS には切り替えない。確認済み: `Connection refused` で終了コード 1。
- `--dummy-tts` は無音だけで、等倍に近い長さをモーラから見積もる。`target_duration_sec` まで引き伸ばさない。
- 本物の VOICEVOX も測った長さのまま等倍で置く。速度は変えない。60秒未満は検査が FAIL になる。下限は 2026-11-09 21:25 に 60.0〜70.0秒へ変わった。
- 描画は `audio_timing.json` の終わりに従う。`pad_sec` や音声より先へ伸ばす場合も、尾は最大 1.0 秒。それ以上の静止は作らない。
- 検査は ffprobe に加え、`freezedetect=n=-60dB:d=2` と `silencedetect=n=-50dB:d=2`。2.0秒以上のフリーズまたは無音で FAIL。測った値は `REPORT.md` と `LAST_RESULT.txt` に書く。

`audio_timing.json` の各 item は `kind`（`segment` / `choice_card` / `day_end_card` / `promo_outro`）、`segment_id`、`start_sec`、`end_sec`、`audio_sec`、`pause_after_ms`、`pad_sec`、`wav`。描画は `start_sec` から `end_sec` まで同じ画面を出し、segment の中身はジョブ JSON から取る。

## Linux での検証（非常灯 / jobs-v2）

再実行は `jobs-v2/episode_day2.json` と `jobs-v2/episode_day3.json`。シリーズ名は JSON の `series_title`（非常灯）、階は `floor_label`（7階）。`jobs/` の旧「14階」は残すが、PC では使わない。

pwsh はこの環境に無かった。dummy-tts の合否は `tools/verify_mp4.py` で ps1 と同じ条件にした。

`PASS | yorunotana_hijolight_day2.mp4 | 61.9s | PR:False | freeze=0.00s | silence=0.00s`

`PASS | yorunotana_hijolight_day3_audible.mp4 | 66.3s | PR:True | freeze=0.00s | silence=0.00s`

新規シーンは `corridor_blink`、`breaker_panel`、`door_note`、`elevator_display`、`thin_wall`、`door_handle`。旧モチーフ（足影、覗き穴、窓グリッド、差出人不明）は新話では使わない。画面本体だけを 1.5秒ごとに少しずらし、HUD と PR は固定する。day3 の PR は 3976/3976 フレームにある。台本の文言は変えていない。

フリーズ検査の切り分け: 絵が動き続ける 4 秒のファイルは freeze なし。最後の絵を 4 秒止めたファイルは freeze=4.03s で FAIL。

2秒ダミー（尺ゲートの対象外。segment はすべて 2.000 秒。day3 の promo は steps 合計の 8 秒）:

| 出力 | 解像度 | fps | フレーム | 尺 | 音声 |
| --- | --- | --- | --- | --- | --- |
| `out/smoke_day2.mp4` | 1080x1920 | 60/1 | 3600 | 60.000s | あり |
| `out/smoke_day3.mp4` | 1080x1920 | 60/1 | 3720 | 62.000s | あり |

作り方:

```text
python tools/make_dummy_timing.py --job jobs/episode_day2.json --out out/smoke_day2/audio_timing.json --silence out/smoke_day2/master_audio.wav
python src/render_frames.py --job jobs/episode_day2.json --timing out/smoke_day2/audio_timing.json --audio out/smoke_day2/master_audio.wav --out out/smoke_day2.mp4
```

シーン一覧は `python src/render_frames.py --stills out/previews`。`contact_sheet.png` と、11 シーン + HUD / PRバッジ / top_card / 字幕の PNG が出る。

## PR の画素チェック

判定は、白文字「PR」の画素平均が 150 以上、かつ下地との差が 60 以上。day3（`pr_badge: true`）は全フレームで成立。day2（`false`）は全フレームで不成立。

- day3（動きを入れた 62.750秒版）: 3765/3765 フレーム。文字輝度の最小 253.68、下地との差の最小 245.01。

```text
python tools/check_pr_badge.py --video out/yorunotana_14f_day3_audible.mp4 --expect true --report out/pr_check_day3.json
python tools/check_pr_badge.py --video out/yorunotana_14f_day2.mp4 --expect false --report out/pr_check_day2.json
```

## 描画の対応

共通: 左上に赤丸 + `DAY n`、時刻、JSON の `floor_label`、その下に `series_title`。`pr_badge: true` のとき右上に半透明の黒地と白の `PR`。`top_card` は赤バッジ、白のタイトル、赤線。字幕は Y=1350、太字に黒フチ。`yellow` は `#FFEE33`、`white` は `#FFFFFF`。

非常灯で足したシーン: `corridor_blink`（廊下の一点透視と非常灯）、`breaker_panel`（配電箱）、`door_note`（扉下の紙。足影なし）、`elevator_display`（階数LED）、`thin_wall`（壁越し。覗き穴の双眸は使わない）、`door_handle`（室内側ノブ）。旧シーンの door_view / peephole_stickman / window_grid / phone_message は新話では使わない。

## 次に触るとき

- 合格の尺は 60.0〜70.0秒。2026-11-09 21:25 JST の決定。速度は上げない。JSON の文言は変えていない。
- PC で走らせるジョブは `jobs-v2`。`git pull` のあと、上の PowerShell をそのまま再実行する。
- 話者 13 が無いエラーなら `-Speaker` を、インストール済みの低音男性 ID に変える。
- 生成物 `out/`、`assets/**/*.wav`、`REPORT.md`、`LAST_RESULT.txt` はコミットしない。
