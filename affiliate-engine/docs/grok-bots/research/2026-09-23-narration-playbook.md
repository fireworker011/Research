# 2026-09-23 ナレーション手順（ペット / 婚活 Shorts）

日付: 2026-09-23  
対象: ペットと婚活の 9:16 Shorts。完成尺 18–24 秒。  
このファイルは手順書。日次の事実 inbox `2026-09-23.md` とは別。  
agents 本文、dump、IMAGINE_THROW の文言は変えていない。動画は投稿しない。

## HQ決定

**採用は経路 A。**

完成動画の声は、Imagine の外で作ったナレーション 1 本だけ。Imagine クリップの音声トラックは捨て、絵だけを B-roll にする。声だけの無映像にはしない。Imagine の内蔵ナレーション（機械音・二重声・無音穴）は投稿に使わない。

聴き比べで Nanami が日記のゴールドから外れたら経路 B。`XAI_API_KEY` が既にあるときだけ経路 C を試聴する。キーはこの手順書に書かない。

## 経路

ゴールドの参照は自チャンネルの日記声: https://youtube.com/shorts/OBxOZp_3hg0 （research の 2026-09-23 観測では「2026年8月9日」、11 秒、再生 5226。この環境では音声ファイルを取得できず、音色の距離は未測定）

| | 経路 A（採用） | 経路 B（次） | 経路 C（キーがあるとき） |
|---|---|---|---|
| 中身 | 箱の edge-tts `ja-JP-NanamiNeural` を 1 本。句点の無音を 0.40 秒まで詰めてから ffmpeg で載せる | VOICEVOX 冥鳴ひまり（speaker 14）を同じ ffmpeg で載せる | xAI `POST https://api.x.ai/v1/tts`、`language=ja` |
| 品質 | 大人の日本語女性。2026-09-23 の声一覧では ja-JP 女性はこの 1 人だけ（男性は Keita）。日記の息はゴールド未聴。句点で約 0.9 秒止まるので、詰めないと無音ゲートで落ちる | キャラ寄り。落ち着いた低めの大人女性として、アナウンスの Nanami より日記に寄る候補。2026-06-15 の `assemble_pet2` は波音リツ speaker 9。あれは日記の次点にしない | 公式ドキュメントは日本語 `ja` 対応。Imagine 内蔵声とは別エンドポイント。声の名前は、キーで `GET /v1/tts/voices` を見てから聴いて決める。ゴールド声のクローンはしない（カスタム声は Enterprise ゲートの記載） |
| 費用 | 追加 API なし。非公式の Edge 読み上げ。Microsoft が止めた実績はこの手順の範囲では未確認。止まったら同じ声の公式は Azure Speech の `ja-JP-NanamiNeural`。Azure のキーはこの環境に無い。円は書かない | ローカル。エンジンの取得が要る。この環境の `127.0.0.1:50021` は無応答 | 公式料金表の数字は取得時点で空欄。円は書かない。https://docs.x.ai/developers/models/text-to-speech |
| ライセンス | ライブラリ edge-tts 7.2.8 は LGPLv3。声のサービスは Edge のオンライン TTS。収益動画の正式枠は Azure。キーが無い間の投稿経路が A | 説明欄に `VOICEVOX:冥鳴ひまり`。商用可・申請不要は本人の規約。https://www.meimeihimari.com/terms-of-use アフィ URL は説明欄に置かない | API 利用規約の範囲。キーは GitHub Secrets か環境変数だけ |
| 箱 | ffmpeg は使える。edge-tts が無い箱は `pip install edge-tts`。Imagine の投げ文は絵のまま | エンジンを立ててから。立つまでは A | `XAI_API_KEY` がある箱だけ |

映像と声の分け方: Imagine は今の IMAGINE_THROW どおり、文字なし・人の顔なし・セリフなしの縦映像。各クリップは 5 秒。完成尺ぶん繋いだあと、音声を捨てて経路 A の wav を 1 本だけ載せる。環境音を残すと二重声とクリップ境の無音が戻る。

## 手順

台本はレシピの「テロップ／読み上げ」をそのまま `script.txt` に置く。文を足さない。CTA「詳しくはプロフィールのリンク（PR）」まで読む。

作業ディレクトリに Imagine のクリップを `clip01.mp4` … と置く。mp4 は Git に入れない。

```bash
python3 -m pip install -q edge-tts
mkdir -p work && cd work
# script.txt はレシピの読み上げ。ここには新しい文を書かない。

python3 - << 'PY'
import asyncio
from pathlib import Path
import edge_tts
text = Path("script.txt").read_text(encoding="utf-8").replace("\n", "")
async def main():
    comm = edge_tts.Communicate(text, "ja-JP-NanamiNeural", rate="+8%", pitch="+0Hz")
    await comm.save("nanami.mp3")
asyncio.run(main())
PY

ffmpeg -y -hide_banner -loglevel error -i nanami.mp3 -ac 1 -ar 24000 nanami.wav

python3 - << 'PY'
import math, struct, wave
src, dst = "nanami.wav", "tight.wav"
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

`tight_sec` が 18 未満または 24 超なら、`rate` を `+0%` と `+12%` のあいだで一度だけ変えて同じ圧縮をやり直す。文は変えない。18–24 に入らないレシピは投稿しない。

無音ゲート（0.5 秒を超える穴が 1 つでもあれば失敗）:

```bash
ffmpeg -hide_banner -i tight.wav -af silencedetect=noise=-35dB:d=0.5 -f null -
```

`silence_duration` が出たら失敗。出なければ通過。

クリップを繋いで音声を捨て、9:16 に揃える。必要本数は `ceil(完成尺/5)`。足りなければ最後のクリップをループする。黒では埋めない。

```bash
printf "file '%s'\n" clip*.mp4 > list.txt
ffmpeg -y -hide_banner -f concat -safe 0 -i list.txt -an -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" -c:v libx264 -pix_fmt yuv420p picture.mp4
ffmpeg -y -hide_banner -stream_loop -1 -i picture.mp4 -i tight.wav -map 0:v:0 -map 1:a:0 -shortest -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart silent_bed.mp4
```

テロップはレシピのテロップ表を `cap.srt` にする。1 行 16 字、同時 2 行まで。0–0.5 秒は文字なし。最後の 2 秒だけ CTA。フォントは制作箱の Noto Sans CJK Bold。この検証環境にはそれが無く、焼付確認は WenQuanYi Micro Hei で行った。

```bash
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 silent_bed.mp4
ffmpeg -y -hide_banner -i silent_bed.mp4 \
  -vf "subtitles=cap.srt:fontsdir=/usr/share/fonts:force_style='FontName=Noto Sans CJK JP,PlayResX=1080,PlayResY=1920,FontSize=44,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,BorderStyle=1,Outline=4,Alignment=2,MarginV=280'" \
  -c:v libx264 -pix_fmt yuv420p -c:a copy -movflags +faststart reel.mp4
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of default=nw=1 reel.mp4
ffmpeg -hide_banner -i reel.mp4 -af silencedetect=noise=-35dB:d=0.5 -f null -
```

通過条件: `width=1080` `height=1920` `r_frame_rate=30/1`、尺が 18–24 秒、`silence_duration` が無い、音声ストリームが 1 本。

## 聴き比べ

イヤホンで次を続けて聴く。

1. https://youtube.com/shorts/OBxOZp_3hg0
2. `reel.mp4`

通す条件: 声は 1 人。大人の日本語女性。日記の速さ。クリップの境で声が変わらない。もう一人が被さらない。句点で 0.5 秒より長く止まらない。機械的でゴールドの日記から外れたら投稿せず、経路 B の同じ `script.txt` で聞き直す。

経路 B の生成（エンジンが `127.0.0.1:50021` にいるとき）:

```bash
python3 - << 'PY'
import json, urllib.parse, urllib.request
from pathlib import Path
text = Path("script.txt").read_text(encoding="utf-8").replace("\n", "")
q = urllib.parse.urlencode({"text": text, "speaker": 14})
req = urllib.request.Request("http://127.0.0.1:50021/audio_query?" + q, data=b"", method="POST")
query = urllib.request.urlopen(req).read()
synth = urllib.request.Request(
    "http://127.0.0.1:50021/synthesis?speaker=14",
    data=query,
    headers={"Content-Type": "application/json"},
)
Path("himari.wav").write_bytes(urllib.request.urlopen(synth).read())
PY
```

その後は A と同じ無音圧縮と ffmpeg。説明欄に `VOICEVOX:冥鳴ひまり` を足す。

経路 C はキーがあるときだけ。声名はレスポンスを見てから:

```bash
curl -s https://api.x.ai/v1/tts/voices -H "Authorization: Bearer $XAI_API_KEY"
curl -s -X POST https://api.x.ai/v1/tts \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text":"SCRIPT_ONE_LINE","voice_id":"VOICE_FROM_LIST","language":"ja"}' \
  --output xai.mp3
```

`SCRIPT_ONE_LINE` は `script.txt` の全文。キーの値はコマンドラインの履歴に残さない。

## 投稿（人間）

この手順は `reel.mp4` まで。YouTube へは出さない。

人間がスマホで出すとき: 説明欄に URL を置かない。説明欄に `#PR`。固定コメントに URL を置かない。画面の CTA は最後の 2 秒の「詳しくはプロフィールのリンク（PR）」だけ。

## この環境で測ったこと（2026-09-23）

対象は research ブランチ `affiliate-engine/docs/grok-bots/agents/pet.md` にある既存の猫と袋の読み上げ。新しい文は作っていない。

- edge-tts 7.2.8 の ja-JP は `ja-JP-NanamiNeural`（女性）と `ja-JP-KeitaNeural`（男性）だけ。
- 同じ文を Nanami `rate=+8%` で読むと 22.704 秒。`silencedetect=noise=-35dB:d=0.5` の穴は 0.892 秒、0.922 秒、0.939 秒、0.915 秒、末尾 0.842 秒。
- 無音ランを 0.40 秒に切ると 20.18 秒。同じ検出で 0.5 秒以上の穴は無い。
- `rate=+0%` の圧縮前は 24.504 秒で、24 秒の上限を超える。
- 色板 1080×1920・30fps に `tight.wav` と srt を載せた確認用 mp4 は 20.180 秒、音声 1 本、0.5 秒以上の穴なし。Imagine の絵ではない。投稿しない。
- `https://youtube.com/shorts/OBxOZp_3hg0` は yt-dlp が「Sign in to confirm you're not a bot」で落ちた。音色の採点は人間の聴き比べまで未判定。
- `XAI_API_KEY` はこの環境に無い。VOICEVOX の 50021 は無応答。

## やらないこと

- YouTube / X への投稿
- agents 本文、dump、IMAGINE_THROW の改稿
- 台本の新作
- 説明欄・固定コメントへのアフィ URL
- ゴールド声のクローン
- API キーのファイル記載
