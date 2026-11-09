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
powershell -ExecutionPolicy Bypass -File .\build-yorunotana.ps1 -JobFile .\jobs\episode_day2.json
powershell -ExecutionPolicy Bypass -File .\build-yorunotana.ps1 -JobFile .\jobs\episode_day3.json -Speaker 13
```

5. 成功の判定は、その場に上書きされる `LAST_RESULT.txt` が `PASS` で始まること。形は `PASS | <job_id>.mp4 | 86.8s | PR:True | freeze=0.00s | silence=0.00s`。足りない尺は静止画で埋めないので、75秒未満なら先頭が `FAIL` になり、測った秒数が入る。詳細は `REPORT.md`（UTF-8 BOM）。`LAST_RESULT.txt` は UTF-8（BOMなし）。どちらも実行のたびに上書きされるので、day2 の1行を残すなら次を走らせる前にコピーする。

VOICEVOX を使わない長さ確認だけするときは `-DummyTts` を付ける。このスイッチはネットワークへ繋がない。

```powershell
powershell -ExecutionPolicy Bypass -File .\build-yorunotana.ps1 -JobFile .\jobs\episode_day3.json -DummyTts
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
| `tools/content_length.py` | dummy-tts と、あれば VOICEVOX の実測の長さ。75秒との差 |
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
- 本物の VOICEVOX も測った長さのまま等倍で置く。速度は変えない。短いからといって最後の絵を止めたり、75秒の下限を下げたりしない。75秒未満は検査が FAIL になる。
- 描画は `audio_timing.json` の終わりに従う。`pad_sec` や音声より先へ伸ばす場合も、尾は最大 1.0 秒。それ以上の静止は作らない。
- 検査は ffprobe に加え、`freezedetect=n=-60dB:d=2` と `silencedetect=n=-50dB:d=2`。2.0秒以上のフリーズまたは無音で FAIL。測った値は `REPORT.md` と `LAST_RESULT.txt` に書く。

`audio_timing.json` の各 item は `kind`（`segment` / `choice_card` / `day_end_card` / `promo_outro`）、`segment_id`、`start_sec`、`end_sec`、`audio_sec`、`pause_after_ms`、`pad_sec`、`wav`。描画は `start_sec` から `end_sec` まで同じ画面を出し、segment の中身はジョブ JSON から取る。

## Linux での検証

pwsh はこの環境に無かった。合否は `tools/verify_mp4.py` で ps1 と同じ条件にした。dummy-tts の本編は 75 秒に届かないので FAIL。末尾の水増しは無い。残っているフリーズは、2秒以上同じ絵が続くカット（day3 のステップは 4.00 秒が2回）。

`FAIL | yorunotana_14f_day2.mp4 | 58.8s | PR:False | freeze=3.45s | silence=0.00s`

`FAIL | yorunotana_14f_day3_audible.mp4 | 62.8s | PR:True | freeze=4.00s | silence=0.00s`

| 出力 | 解像度 | fps | 尺 | 音声 | 最長フリーズ | 最長無音 |
| --- | --- | --- | --- | --- | --- | --- |
| day2 | 1080x1920 | 60/1 | 58.750s | あり | 3.45s | 0.00s |
| day3 | 1080x1920 | 60/1 | 62.750s | あり | 4.00s | 0.00s |

`tools/content_length.py --dummy-tts` の見積もりは day2 が 58.75秒（75秒まで 16.25秒不足）、day3 が 62.75秒（12.25秒不足）。この Linux では VOICEVOX は unavailable。PC の実測（フリーズが始まった時刻）は day2 が 64.3秒（10.7秒不足）、day3 が 59.8秒（15.2秒不足）。

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

- day3: 5220/5220 フレーム。文字輝度の最小 253.68、下地との差の最小 245.01。バッジあり/なし静止画の PR 矩形の平均絶対差は 30.78（下地はどちらも暗いので、差は文字に集中する）。
- day2: 0/5280 フレーム。文字位置の輝度は最大 11.33。

```text
python tools/check_pr_badge.py --video out/yorunotana_14f_day3_audible.mp4 --expect true --report out/pr_check_day3.json
python tools/check_pr_badge.py --video out/yorunotana_14f_day2.mp4 --expect false --report out/pr_check_day2.json
```

## 描画の対応

共通: 左上に赤丸 + `DAY n`、時刻、`floor_label`。`pr_badge: true` のとき右上に半透明の黒地と白の `PR`。`top_card` は赤バッジ、白のタイトル、赤線。字幕は Y=1350、太字に黒フチ。`yellow` は `#FFEE33`、`white` は `#FFFFFF`。

シーン: `door_view`（隙間の光と2本の影、`shake` は ±6px）、`room_stickman`（星空の窓、本棚、膝つき、スマホの青光、イヤホン）、`phone_tap`（4x5 アイコンと右下からの腕、波紋）、`window_grid`（5x5、`sequential_blackout` はシード固定の順で消灯）、`peephole_stickman`（赤い同心円と目玉）、`phone_message`、`app_demo_screen`（`dark_waveform_only` はほぼ黒にオレンジの波形）、`morning_window`、`choice_card`、`day_end_card`、`promo_outro`（ステップ①②とプロフィール誘導。URL は描かない）。

## 次に触るとき

- 75秒に届かせるのは台本側。速度は上げない。75秒の下限も下げない。JSON はこの修正では変えていない。
- 2秒以上同じ絵が続くカットも FAIL になる。短くするか、絵を動かすかは人間の判断。
- 話者 13 が無いエラーなら `-Speaker` を、インストール済みの低音男性 ID に変える。
- 生成物 `out/`、`assets/**/*.wav`、`REPORT.md`、`LAST_RESULT.txt` はコミットしない。
