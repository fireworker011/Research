# 2026-09-23 ナレーション手順（ペット / 婚活 Shorts）

日付: 2026-09-23  
対象: ペットと婚活の 9:16 Shorts。完成尺 18–24 秒。  
このファイルは手順書。日次の事実 inbox `2026-09-23.md` とは別。  
agents 本文、dump、IMAGINE_THROW の文言は変えていない。動画は投稿しない。

## HQ決定

**現役候補は経路 B。VOICEVOX 冥鳴ひまり（speaker 14）。**

聴き比べ 2026-09-23 で経路 A（edge-tts `ja-JP-NanamiNeural`）は不採用。ゴールド https://youtube.com/shorts/OBxOZp_3hg0 に対して機械的。Imagine 内蔵の吹き替えを残した重ねも二重声が残った。Nanami も Imagine 声も投稿に使わない。

組み立ては変えない。Imagine クリップの音声トラックは捨て、絵だけを B-roll にする。完成動画の声は外付け 1 本（いまはひまり）だけ。声だけの無映像にはしない。

ひまりの聴き比べが日記から外れたら経路 C を試聴する。`XAI_API_KEY` が無い間は C に進まない。キーはこの手順書に書かない。

## 聴き比べの記録（2026-09-23）

| 声 | 結果 |
|---|---|
| ゴールド OBxOZp | 基準。自チャンネルの日記声。research の 2026-09-23 観測では「2026年8月9日」、11 秒、再生 5226。この環境では音声ファイルは取れていない |
| edge-tts Nanami | **不採用。** 機械的でゴールドから外れた |
| Imagine 内蔵の吹き替えを残した重ね | **不採用。** 二重声が残った。絵の音声を残したまま外付けすると同じ故障に戻る |

## 経路

| | 経路 B（現役） | 経路 A（不採用） | 経路 C（ひまりが外れたとき） |
|---|---|---|---|
| 中身 | VOICEVOX 冥鳴ひまり speaker 14 を 1 本。無音が 0.5 秒を超えたら 0.40 秒まで詰めて ffmpeg で載せる | edge-tts `ja-JP-NanamiNeural` | xAI `POST https://api.x.ai/v1/tts`、`language=ja` |
| 品質 | 聴き比べはこれから。キャラ寄り。2026-06-15 の `assemble_pet2` は波音リツ speaker 9。あれは現役にしない | 2026-09-23 の聴き比べで機械的。ja-JP 女性はこの 1 人だけだった（男性は Keita）。計測上、句点で約 0.9 秒止まっていた | 公式ドキュメントは日本語 `ja` 対応。声の名前は `GET /v1/tts/voices` を見てから聴く。ゴールド声のクローンはしない |
| 費用 | ローカル。エンジンの取得が要る。この環境の `127.0.0.1:50021` は 2026-09-23 時点で無応答 | 追加 API なし。非公式の Edge 読み上げ。不採用なので投稿経路にしない | 公式料金表の数字は取得時点で空欄。円は書かない。https://docs.x.ai/developers/models/text-to-speech |
| ライセンス | 説明欄に `VOICEVOX:冥鳴ひまり`。商用可・申請不要は本人の規約。https://www.meimeihimari.com/terms-of-use アフィ URL は説明欄に置かない | ライブラリは LGPLv3。声のサービスは Edge のオンライン TTS。正式枠は Azure Speech の同じ声。キーはこの環境に無い | API 利用規約の範囲。キーは GitHub Secrets か環境変数だけ |
| 箱 | `http://127.0.0.1:50021` が応答してから。`/speakers` に id 14 が無いときは、名前が冥鳴ひまり・ノーマルの id を使う | 使わない | `XAI_API_KEY` がある箱だけ |

映像と声の分け方: Imagine は今の IMAGINE_THROW どおり、文字なし・人の顔なし・セリフなしの縦映像。各クリップは 5 秒。完成尺ぶん繋いだあと、音声を捨ててひまりの wav を 1 本だけ載せる。環境音も残さない。2026-09-23 の二重声は、Imagine の声を残した重ねで起きている。

## 手順

台本はレシピの「テロップ／読み上げ」をそのまま `script.txt` に置く。文を足さない。CTA「詳しくはプロフィールのリンク（PR）」まで読む。

作業ディレクトリに Imagine のクリップを `clip01.mp4` … と置く。mp4 は Git に入れない。エンジンが立っていることを先に見る。

```bash
curl -sf http://127.0.0.1:50021/version
curl -sf http://127.0.0.1:50021/speakers | python3 -c 'import json,sys; d=json.load(sys.stdin);
[print(s["name"], st["id"], st["name"]) for s in d for st in s["styles"]]'
mkdir -p work && cd work
# script.txt はレシピの読み上げ。ここには新しい文を書かない。

python3 - << 'PY'
import json, urllib.parse, urllib.request
from pathlib import Path
text = Path("script.txt").read_text(encoding="utf-8").replace("\n", "")
q = urllib.parse.urlencode({"text": text, "speaker": 14})
req = urllib.request.Request(
    "http://127.0.0.1:50021/audio_query?" + q, data=b"", method="POST"
)
query = json.loads(urllib.request.urlopen(req).read().decode())
query["speedScale"] = 1.0
synth = urllib.request.Request(
    "http://127.0.0.1:50021/synthesis?speaker=14",
    data=json.dumps(query).encode(),
    headers={"Content-Type": "application/json"},
)
Path("himari.wav").write_bytes(urllib.request.urlopen(synth).read())
PY

ffmpeg -y -hide_banner -loglevel error -i himari.wav -ac 1 -ar 24000 himari_24k.wav
mv himari_24k.wav himari.wav
```

無音が 0.5 秒を超えるランだけ 0.40 秒まで残す。超えていなければ長さはそのまま。

```bash
python3 - << 'PY'
import math, struct, wave
src, dst = "himari.wav", "tight.wav"
with wave.open(src, "rb") as w:
    sr = w.getframerate()
    raw = w.readframes(w.getnframes())
samples = list(struct.unpack("<" + "h" * (len(raw) // 2), raw))
frame = int(sr * 0.02)
thr = 10 ** (-35 / 20) * 32768
flags, i = [], 0
while i < len(samples):
    chunk = samples[i:i + frame]
    rms = math.sqrt(sum(s * s for s in chunk) / len(chunk))
    flags.append(rms < thr)
    i += frame
runs, s = [], 0
for k, f in enumerate(flags):
    if k == 0 or f != flags[k - 1]:
        if k:
            runs.append((flags[k - 1], s, k))
        s = k
runs.append((flags[-1], s, len(flags)))
keep = int(0.40 / 0.02)
out = []
for is_sil, a, b in runs:
    if is_sil and (b - a) > keep:
        b = a + keep
    for fi in range(a, b):
        out.extend(samples[fi * frame:(fi + 1) * frame])
with wave.open(dst, "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(sr)
    w.writeframes(struct.pack("<" + "h" * len(out), *out))
print("tight_sec", round(len(out) / sr, 3))
PY
```

`tight_sec` が 18 未満または 24 超なら、`speedScale` を 0.9 から 1.15 のあいだで一度だけ変えて `audio_query` からやり直す。文は変えない。18–24 に入らないレシピは投稿しない。ひまりの実尺はこの環境では未測定（エンジン無応答）。

無音ゲート（0.5 秒を超える穴が 1 つでもあれば失敗）:

```bash
ffmpeg -hide_banner -i tight.wav -af silencedetect=noise=-35dB:d=0.5 -f null -
```

`silence_duration` が出たら失敗。出なければ通過。

クリップを繋いで音声を捨て、9:16 に揃える。必要本数は `ceil(完成尺/5)`。足りなければ最後のクリップをループする。黒では埋めない。`-an` を外すと Imagine の声が残り、2026-09-23 の二重声に戻る。

```bash
printf "file '%s'\n" clip*.mp4 > list.txt
ffmpeg -y -hide_banner -f concat -safe 0 -i list.txt -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" -c:v libx264 -pix_fmt yuv420p picture.mp4
ffmpeg -y -hide_banner -stream_loop -1 -i picture.mp4 -i tight.wav -map 0:v:0 -map 1:a:0 -shortest -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart silent_bed.mp4
```

テロップはレシピのテロップ表を `cap.srt` にする。1 行 16 字、同時 2 行まで。0–0.5 秒は文字なし。最後の 2 秒だけ CTA。フォントは制作箱の Noto Sans CJK Bold。Nanami 時代の焼付確認は WenQuanYi Micro Hei で、ひまりの完成動画はまだ無い。

```bash
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 silent_bed.mp4
ffmpeg -y -hide_banner -i silent_bed.mp4 \
  -vf "subtitles=cap.srt:fontsdir=/usr/share/fonts:force_style='FontName=Noto Sans CJK JP,PlayResX=1080,PlayResY=1920,FontSize=44,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,BorderStyle=1,Outline=4,Alignment=2,MarginV=280'" \
  -c:v libx264 -pix_fmt yuv420p -c:a copy -movflags +faststart reel.mp4
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of default=nw=1 reel.mp4
ffprobe -v error -select_streams a -show_entries stream=codec_type -of default=nw=1 reel.mp4
ffmpeg -hide_banner -i reel.mp4 -af silencedetect=noise=-35dB:d=0.5 -f null -
```

通過条件: `width=1080` `height=1920` `r_frame_rate=30/1`、尺が 18–24 秒、音声ストリームが 1 本、`silence_duration` が無い。

## 聴き比べ（ひまり）

イヤホンで次を続けて聴く。投稿の前。

1. https://youtube.com/shorts/OBxOZp_3hg0
2. `reel.mp4`

通す条件: 声は 1 人。大人の日本語女性。日記の速さ。クリップの境で声が変わらない。Imagine の声が被さらない。句点で 0.5 秒より長く止まらない。機械的、または二重声が残ったら投稿しない。

説明欄に `VOICEVOX:冥鳴ひまり` を足す。アフィ URL は置かない。

経路 C は、ひまりが上の条件で外れたとき、かつキーがあるときだけ。

```bash
curl -s https://api.x.ai/v1/tts/voices -H "Authorization: Bearer $XAI_API_KEY"
curl -s -X POST https://api.x.ai/v1/tts \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text":"SCRIPT_ONE_LINE","voice_id":"VOICE_FROM_LIST","language":"ja"}' \
  --output xai.mp3
```

`SCRIPT_ONE_LINE` は `script.txt` の全文。載せ方は同じ（Imagine は無音、外付け 1 本）。キーの値はコマンドラインの履歴に残さない。

## 投稿（人間）

この手順は `reel.mp4` まで。YouTube へは出さない。

人間がスマホで出すとき: 説明欄に URL を置かない。説明欄に `#PR` と `VOICEVOX:冥鳴ひまり`。固定コメントに URL を置かない。画面の CTA は最後の 2 秒の「詳しくはプロフィールのリンク（PR）」だけ。

## この環境で測ったこと（2026-09-23）

対象は research ブランチ `affiliate-engine/docs/grok-bots/agents/pet.md` にある既存の猫と袋の読み上げ。新しい文は作っていない。Nanami の秒数は不採用の記録であり、現役の尺ではない。

- edge-tts 7.2.8 の ja-JP は `ja-JP-NanamiNeural`（女性）と `ja-JP-KeitaNeural`（男性）だけ。
- 同じ文を Nanami `rate=+8%` で読むと 22.704 秒。`silencedetect=noise=-35dB:d=0.5` の穴は 0.892 秒、0.922 秒、0.939 秒、0.915 秒、末尾 0.842 秒。
- その無音ランを 0.40 秒に切ると 20.18 秒。同じ検出で 0.5 秒以上の穴は無い。音色の不採用はこの圧縮の後の聴き比べ。
- `rate=+0%` の圧縮前は 24.504 秒。
- 色板 1080×1920・30fps に Nanami の `tight.wav` を載せた確認用 mp4 は 20.180 秒、音声 1 本。Imagine の絵ではない。投稿しない。ひまりの完成動画はまだ無い。
- `https://youtube.com/shorts/OBxOZp_3hg0` は yt-dlp が「Sign in to confirm you're not a bot」で落ちた。
- `XAI_API_KEY` はこの環境に無い。VOICEVOX の 50021 は無応答。ひまりの秒数は未測定。

## やらないこと

- YouTube / X への投稿
- Nanami、または Imagine の音声を残した重ね
- agents 本文、dump、IMAGINE_THROW の改稿
- 台本の新作
- 説明欄・固定コメントへのアフィ URL
- ゴールド声のクローン
- API キーのファイル記載
