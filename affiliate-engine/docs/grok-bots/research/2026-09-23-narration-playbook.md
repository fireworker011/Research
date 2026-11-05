# 2026-09-23 ナレーション手順（ペット / 婚活 Shorts）

日付: 2026-09-23  
対象: ペットと婚活の 9:16 Shorts。完成尺 18–24 秒。画面は 1080×1920。  
このファイルは手順書。日次の事実 inbox `2026-09-23.md` とは別。  
agents 本文、dump、IMAGINE_THROW の文言は変えていない。動画は投稿しない。

## HQ決定

**次に聴く声は Style-Bert-VITS2 JP-Extra `jvnv-F1-jp`、スタイル Neutral。**

組み立ては変えない。Imagine クリップの音声トラックは捨て、絵だけを B-roll にする。完成動画の声は外付け 1 本だけ。声だけの無映像にはしない。

今ある吹き替えは作り直す。声が落ちた本も、テロップが画面からはみ出た本も、投稿に使わない。

`XAI_API_KEY` が箱に既にあるときだけ、モデルを入れる前に xAI の日本語を 1 本聴く。機械的なら、またはキーが無いなら、`jvnv-F1-jp` に進む。キーはこの手順書に書かない。この環境にはキーが無い。

次の VOICEVOX 話者は聴かない。

## 聴き比べの記録（2026-09-23）

| 声 | 結果 |
|---|---|
| ゴールド OBxOZp | 基準。自チャンネルの日記声。research の 2026-09-23 観測では「2026年8月9日」、11 秒、再生 5226。この環境では音声ファイルは取れていない。https://youtube.com/shorts/OBxOZp_3hg0 |
| edge-tts Nanami | **不採用。** 機械的 |
| VOICEVOX 冥鳴ひまり speaker 14 | **不採用。** 人間の聴き比べで機械的。秒数は未測定（この環境の 50021 は無応答） |
| Imagine 内蔵を残した重ね | **不採用。** 二重声が残った |
| 今の吹き替えのテロップ | **不採用。** 画面内からはみ出ている。1080×1920 の枠内に焼き直す |

## 次の声

| | 現役（入れる） | キーがあるとき先に 1 本 | 聴かない |
|---|---|---|---|
| 名前 | Style-Bert-VITS2 `jvnv-F1-jp` / Neutral | xAI TTS `language=ja` | VOICEVOX の別話者 |
| 理由 | Nanami もひまりも機械的で落ちた。JVNV の F1 は大人女性の収録コーパスで、合成方式が VOICEVOX と別。公式の利用例がこのモデル。https://github.com/litagin02/Style-Bert-VITS2/blob/master/library.ipynb | 箱にキーがあるなら、数 GB のモデルの前に 1 回聴ける。日本語は公式の対応言語。https://docs.x.ai/developers/model-capabilities/audio/text-to-speech | ひまりは落ち着いた大人女性として選んだ話者。同じエンジンの波音リツは speaker 9 で、2026-06-15 の `assemble_pet2` で既に使った。機械的、は話者を替えても同じ方式に残る |
| 費用 | ローカル。CPU で合成できる（学習は GPU）。BERT とモデルの取得が要る。円は書かない | 公式料金表の数字は空欄だった。円は書かない。https://docs.x.ai/developers/models/text-to-speech | エンジンを立てない |
| ライセンス | モデルは JVNV コーパスの CC BY-SA 4.0 を継承。https://huggingface.co/litagin/style_bert_vits2_jvnv コードは AGPL-3.0。説明欄に表記する。投稿前に人間が見る | API 利用規約。キーは環境変数だけ | ひまりの規約は不採用の記録。説明欄クレジットは足さない |
| 箱 | Linux x86_64。この確認環境は Python 3.12.3。公式ノートの例は Python 3.10。3.12 で `pip` が失敗したら 3.11 の venv にする | `XAI_API_KEY` があるときだけ | 50021 は使わない |

SA を説明欄表記で受けられないときは、同じインストールのまま一度だけあみたろに替える。商用可。説明欄は `Style-BertVITS2モデル: あみたろ、あみたろの声素材工房 (https://amitaro.net/)`。年齢制限のある用途は禁止。日記の第一候補にはしない。https://github.com/litagin02/Style-Bert-VITS2/blob/master/docs/TERMS_OF_USE.md

ゴールド声のクローンはしない。

## インストール（Linux・CPU）

作業場所はホーム。リポジトリの中にモデルを置かない。

```bash
python3 -m venv "$HOME/sbv2-venv"
source "$HOME/sbv2-venv/bin/activate"
python -m pip install -U pip
python -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
python -m pip install style-bert-vits2
mkdir -p "$HOME/sbv2-work" && cd "$HOME/sbv2-work"
```

`pip` が Python 3.12 で落ちたら、3.11 を入れて venv を作り直す。モデルはまだ取らない。xAI を先に聴く箱は、キーの試聴が機械的だったあとで上を実行する。

## 手順

台本はレシピの「テロップ／読み上げ」をそのまま `script.txt` に置く。文を足さない。CTA「詳しくはプロフィールのリンク（PR）」まで読む。

Imagine のクリップは `clip01.mp4` …。mp4 は Git に入れない。

### キーがあるときの xAI（1 本だけ）

```bash
curl -s https://api.x.ai/v1/tts/voices -H "Authorization: Bearer $XAI_API_KEY"
curl -s -X POST https://api.x.ai/v1/tts \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text":"SCRIPT_ONE_LINE","voice_id":"VOICE_FROM_LIST","language":"ja","speed":1.0}' \
  --output xai.mp3
ffmpeg -y -hide_banner -loglevel error -i xai.mp3 -ac 1 -ar 24000 xai.wav
```

`SCRIPT_ONE_LINE` は `script.txt` の全文。`VOICE_FROM_LIST` は一覧のうち大人の女性を 1 つ。一覧を見る前に声の名前を決めない。イヤホンで OBxOZp と聴く。日記として通れば、その wav を下の無音ゲートへ進める。機械的なら捨てて `jvnv-F1-jp` に進む。キーの値は履歴に残さない。

### jvnv-F1-jp

```bash
source "$HOME/sbv2-venv/bin/activate"
cd "$HOME/sbv2-work"
python - << 'PY'
from pathlib import Path
import numpy as np
import wave
from huggingface_hub import hf_hub_download
from style_bert_vits2.constants import Languages
from style_bert_vits2.nlp import bert_models
from style_bert_vits2.tts_model import TTSModel

bert_models.load_model(Languages.JP, "ku-nlp/deberta-v2-large-japanese-char-wwm")
bert_models.load_tokenizer(Languages.JP, "ku-nlp/deberta-v2-large-japanese-char-wwm")

files = [
    "jvnv-F1-jp/jvnv-F1-jp_e160_s14000.safetensors",
    "jvnv-F1-jp/config.json",
    "jvnv-F1-jp/style_vectors.npy",
]
for name in files:
    hf_hub_download("litagin/style_bert_vits2_jvnv", name, local_dir="model_assets")

text = Path("script.txt").read_text(encoding="utf-8").replace("\n", "")
model = TTSModel(
    model_path=Path("model_assets") / files[0],
    config_path=Path("model_assets") / files[1],
    style_vec_path=Path("model_assets") / files[2],
    device="cpu",
)
sr, audio = model.infer(
    text=text,
    language=Languages.JP,
    style="Neutral",
    style_weight=1.0,
    length=1.0,
    line_split=False,
)
audio = np.asarray(audio, dtype=np.float32).reshape(-1)
audio = np.clip(audio, -1.0, 1.0)
pcm = (audio * 32767.0).astype(np.int16)
with wave.open("voice.wav", "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(int(sr))
    w.writeframes(pcm.tobytes())
print("sr", sr, "sec", round(len(pcm) / sr, 3))
PY
```

`length` は大きいほどゆっくり。`tight_sec` が 18 未満または 24 超なら、`length` を 0.85 から 1.15 のあいだで一度だけ変える。文は変えない。18–24 に入らないレシピは投稿しない。`line_split` は False（既定の True は改行ごとに 0.5 秒空ける）。

無音が 0.5 秒を超えるランだけ 0.40 秒まで残す。

```bash
python - << 'PY'
import math, struct, wave
src, dst = "voice.wav", "tight.wav"
with wave.open(src, "rb") as w:
    sr = w.getframerate()
    sw = w.getsampwidth()
    ch = w.getnchannels()
    raw = w.readframes(w.getnframes())
if sw != 2 or ch != 1:
    raise SystemExit(f"expected mono s16, got sw={sw} ch={ch}")
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
ffmpeg -hide_banner -i tight.wav -af silencedetect=noise=-35dB:d=0.5 -f null -
```

`silence_duration` が出たら失敗。

### 絵は無音、1080×1920

`-an` を外すと Imagine の声が残り、二重声に戻る。`scale` のあと `setsar=1` までやってからテロップを焼く。

```bash
printf "file '%s'\n" clip*.mp4 > list.txt
ffmpeg -y -hide_banner -f concat -safe 0 -i list.txt -an \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30" \
  -c:v libx264 -pix_fmt yuv420p picture.mp4
ffmpeg -y -hide_banner -stream_loop -1 -i picture.mp4 -i tight.wav \
  -map 0:v:0 -map 1:a:0 -shortest \
  -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart silent_bed.mp4
```

### テロップは枠の中

レシピのテロップ表を `cap.srt` にする。1 行 16 字、同時 2 行まで。0–0.5 秒は文字なし。最後の 2 秒だけ CTA。

`PlayResX=1080,PlayResY=1920` を消すと、FontSize 44 が別の座標で巨大になり、枠の外に切れる。MarginL/R は 96、MarginV は 360。フォントは箱にある日本語フォントの家族名を `fc-list :lang=ja family` で見て `FontName` に書く。確認環境では WenQuanYi Micro Hei。

```bash
fc-list :lang=ja family | head
ffmpeg -y -hide_banner -i silent_bed.mp4 \
  -vf "subtitles=cap.srt:fontsdir=/usr/share/fonts:force_style='FontName=WenQuanYi Micro Hei,PlayResX=1080,PlayResY=1920,FontSize=44,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,BorderStyle=1,Outline=3,Alignment=2,MarginL=96,MarginR=96,MarginV=360'" \
  -c:v libx264 -pix_fmt yuv420p -c:a copy -movflags +faststart reel.mp4
```

焼き付けの確認。文字のある秒で 1 枚抜く。インクが端から 48px より内側に無ければ失敗。

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of default=nw=1 reel.mp4
ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 reel.mp4
ffmpeg -y -hide_banner -loglevel error -ss 2 -i reel.mp4 -frames:v 1 frame.png
python3 - << 'PY'
import subprocess
png, w, h, edge = "frame.png", 1080, 1920, 48
raw = subprocess.check_output(["ffmpeg","-hide_banner","-loglevel","error","-i",png,"-f","rawvideo","-pix_fmt","gray","-"])
if len(raw) != w * h:
    raise SystemExit(f"bad size {len(raw)}")
xs, ys = [], []
for y in range(h):
    row = raw[y * w:(y + 1) * w]
    for x, b in enumerate(row):
        if b > 40:
            xs.append(x)
            ys.append(y)
if not xs:
    raise SystemExit("no caption ink")
box = (min(xs), min(ys), max(xs), max(ys))
print("ink", box, "gaps", min(xs), w - 1 - max(xs), min(ys), h - 1 - max(ys))
if min(xs) < edge or min(ys) < edge or (w - 1 - max(xs)) < edge or (h - 1 - max(ys)) < edge:
    raise SystemExit("CLIPPED")
print("IN_FRAME")
PY
ffmpeg -hide_banner -i reel.mp4 -af silencedetect=noise=-35dB:d=0.5 -f null -
```

通過条件: `width=1080` `height=1920` `r_frame_rate=30/1`、音声ストリームが 1 本、尺が 18–24 秒、`silence_duration` が無い、`IN_FRAME`。

この確認環境で、同じ force_style を色板 1080×1920 に焼いた 2 行（WenQuanYi Micro Hei）のインクは x 335–742、y 1476–1554。下の空きは 365px。端には触れていない。本番の吹き替えファイルはこの環境に無い。

## 聴き比べ

1. https://youtube.com/shorts/OBxOZp_3hg0
2. `reel.mp4`

通す条件: 声は 1 人。大人の日本語女性。日記の速さ。クリップの境で声が変わらない。Imagine の声が被さらない。句点で 0.5 秒より長く止まらない。テロップは枠の中。機械的、二重声、はみ出しのいずれかがあれば投稿しない。

説明欄（jvnv-F1-jp のとき）:

```
音声: Style-Bert-VITS2 jvnv-F1-jp（JVNVコーパス, CC BY-SA 4.0）
https://huggingface.co/litagin/style_bert_vits2_jvnv
#PR
```

URL はアフィリンクではない。アフィ URL は説明欄にも固定コメントにも置かない。

## 投稿（人間）

この手順は `reel.mp4` まで。YouTube へは出さない。

人間がスマホで出すとき: 上の表記と `#PR`。画面の CTA は最後の 2 秒の「詳しくはプロフィールのリンク（PR）」だけ。

## この環境で測ったこと（2026-09-23）

Nanami の秒数は不採用の記録。現役の尺ではない。対象は research ブランチ `affiliate-engine/docs/grok-bots/agents/pet.md` の既存の猫と袋の読み上げ。

- edge-tts 7.2.8 の ja-JP は Nanami（女性）と Keita（男性）だけ。
- Nanami `rate=+8%` は 22.704 秒。`-35dB` で 0.5 秒以上の穴が 4 つと末尾。0.40 秒に切ると 20.18 秒。音色は不採用。
- 色板に Nanami を載せた確認用 mp4 は 20.180 秒。投稿しない。
- ひまりの秒数は未測定。人間の聴き比べで不採用。
- OBxOZp は yt-dlp がボット確認で落ちた。
- `XAI_API_KEY` は無い。VOICEVOX 50021 は無応答。
- テロップの枠内確認は色板。本番の吹き替え mp4 はここには無い。

## やらないこと

- YouTube / X への投稿
- Nanami、ひまり、他の VOICEVOX 話者、Imagine の音声を残した重ね
- はみ出したテロップのままの書き出し
- agents 本文、dump、IMAGINE_THROW の改稿
- 台本の新作
- 説明欄・固定コメントへのアフィ URL
- ゴールド声のクローン
- API キーのファイル記載
