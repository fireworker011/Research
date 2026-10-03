"""H3 fallback: one vertical still-image slide. Does not generate images or post.

The spec asks for 5 images and also for 表紙→問題提起→5つ→締め.
This module keeps 5 images and records the assignment.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

SLIDE_DIR = Path(__file__).resolve().parent / "slides" / "orbis-dot-01"
SLIDE_ID = "orbis-dot-01"
SECONDS_EACH = 3.0
WIDTH = 1080
HEIGHT = 1920

# 一番の答えは画面（字幕・Imagine指示）に出さない。
ANSWER = "このシリーズは無香料です。出典はメーカー公式ショップのよくある質問（2026年10月3日時点）。"

SLIDES: tuple[dict[str, Any], ...] = (
    {
        "file": "01.png",
        "role": "表紙",
        "points": (),
        "caption": ("香りが好きな人ほど", "買う前に見て"),
        "imagine": (
            "Photoreal still, vertical 9:16, a quiet room at dusk, warm lamp light, "
            "softly blurred beige wall. On a light wooden table: a small lit candle "
            "in a clear unlabeled glass jar, and a slim frosted-white bottle with a "
            "plain white cap and no logo, no label, and no letters. No people, no "
            "hands, no faces, no skin, no text, no watermark."
        ),
    },
    {
        "file": "02.png",
        "role": "問題提起",
        "points": (),
        "caption": ("香りで選びたい人は", "先に見て"),
        "imagine": (
            "Photoreal still, vertical 9:16, the same dusk room and wooden table. "
            "The unlabeled candle is closer to the camera and still lit. The same "
            "frosted-white unbranded bottle sits just behind it. No people, no "
            "hands, no faces, no skin, no text, no logo."
        ),
    },
    {
        "file": "03.png",
        "role": "本文",
        "points": ("無着色", "アルコールフリー"),
        "caption": ("無着色", "アルコールフリー"),
        "imagine": (
            "Photoreal still, vertical 9:16, high angle on the same light wooden "
            "table. Only the slim frosted-white unbranded bottle, standing, cap on. "
            "No candle, no people, no hands, no faces, no skin, no text, no logo."
        ),
    },
    {
        "file": "04.png",
        "role": "本文",
        "points": ("パラベンフリー",),
        "caption": ("パラベンフリー",),
        "imagine": (
            "Photoreal still, vertical 9:16, the same unbranded frosted-white bottle "
            "beside a clear glass of water on a white tray. A single drop has just "
            "fallen and small ripples sit on the water. The bottle is not open and "
            "touches nobody. No people, no hands, no faces, no skin, no text, no logo."
        ),
    },
    {
        "file": "05.png",
        "role": "締め",
        "points": (),
        "caption": ("紹介してるのは", "プロフィールへ"),
        "imagine": (
            "Photoreal still, vertical 9:16, the same unbranded frosted-white bottle "
            "on a white tray, lower third of the frame. The upper half of the frame "
            "is only the softly blurred beige wall. No pointing hand, no people, no "
            "faces, no skin, no text, no logo, no arrow."
        ),
    },
)

POST = """アフィリエイト広告を含みます #PR
香りが好きな人ほど、買う前に。オルビスユー ドット

買う前に知っておきたい表示です。使った感想ではありません。肌に合うかどうかには個人差があります。
無着色、アルコールフリー、パラベンフリーは、メーカー公式ショップのよくある質問で確認しました（2026年10月3日時点）。最新の表示は販売ページでご確認ください。
5つ目: 不明
紹介しているものはプロフィールのリンクからどうぞ。

#PR #スキンケア #化粧水

画像はAIで生成しています。ボトルはAIで作ったイメージで、実際の商品やパッケージとは異なります。人物は出していません。

一番の答え: このシリーズは無香料です。出典はメーカー公式ショップのよくある質問（2026年10月3日時点）。
"""

ASSIGNMENT = """仕様は「画像5枚」と「表紙→問題提起→5つ→締め」が食い違う。初稿は画像5枚に固定した。
1枚目は表紙、2枚目は問題提起、3枚目と4枚目は本文、5枚目は締め。
5つの内訳は、画面に出す無着色・アルコールフリー・パラベンフリー、画面に出さない一番の答え（無香料）、確認できない5つ目（不明）。
8枚には分けない。一番の答えは字幕にもImagine指示にも書かない。
"""


def caption_lines(slide: dict[str, Any]) -> tuple[str, ...]:
    return tuple(slide["caption"])


def on_screen_text() -> str:
    chunks: list[str] = []
    for slide in SLIDES:
        chunks.extend(slide["caption"])
        chunks.append(slide["imagine"])
    return "\n".join(chunks)


def score() -> dict[str, Any]:
    """直す: a required point is 不明, so this draft is not scheduled."""
    return {
        "verdict": "直す",
        "schedule": False,
        "reason": "5つ目が不明。A8の着地URLは不明。直近Shortsで普段の3倍は不明（未確認）。予約しない。",
        "h3_gate": "不明",
    }


def srt() -> str:
    blocks: list[str] = []
    for index, slide in enumerate(SLIDES):
        start = index * SECONDS_EACH
        end = start + SECONDS_EACH
        text = "\n".join(slide["caption"])
        blocks.append(f"{index + 1}\n{_ts(start)} --> {_ts(end)}\n{text}\n")
    return "\n".join(blocks)


def render_draft() -> str:
    parts = [
        f"# 画像スライド初稿 {SLIDE_ID}",
        "",
        "商品: オルビスユー ドット。ジャンル: 美容だけ。H3の代わり。画像はまだ作っていない。投稿しない。予約しない。",
        "",
        "## 割り当て",
        ASSIGNMENT.strip(),
        "",
        "## 画像5枚（Grok Imagine、9:16。画面の文字は入れない。字幕はあとから焼く）",
    ]
    for index, slide in enumerate(SLIDES, start=1):
        lines = " / ".join(slide["caption"])
        points = "、".join(slide["points"]) if slide["points"] else "なし"
        parts.append(f"### {index}. {slide['file']}（{slide['role']}）")
        parts.append(f"字幕: {lines}")
        parts.append(f"この枚に載せる点: {points}")
        parts.append("```text")
        parts.append(slide["imagine"])
        parts.append("```")
        parts.append("")
    parts.extend(
        [
            "## 秒数",
            "各画像 3.0 秒。5枚で 15.0 秒。1080×1920（9:16）。音声は無し。BGMを置くなら bgm/slide.m4a。",
            "",
            "## 投稿文",
            "```text",
            POST.strip(),
            "```",
            "",
            "## 採点",
            f"判定: {score()['verdict']}。{score()['reason']}",
            "H3動画が直近で完了条件を満たせなかったかの計測は、この初稿ではしていない。欄は不明。",
            "直近1年で普段の3倍以上のユー ドットShorts: 不明（未確認）。10/3の検索では3倍以上は0本。新しい計測はしていない。",
            "くたろう型の視聴数は形式の出所の数字で、この商品の再生数ではない。",
            "",
        ]
    )
    return "\n".join(parts)


def ffmpeg_script() -> str:
    return f"""#!/usr/bin/env bash
# Vertical 9:16 still slide. Does not post. Does not call Imagine.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
IMAGES="${{1:-$ROOT/images}}"
OUT="${{2:-$ROOT/{SLIDE_ID}.mp4}}"
BGM="${{3:-$ROOT/bgm/slide.m4a}}"
SRT="$ROOT/captions.srt"
FONT=""
for c in \\
  /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc \\
  /usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc \\
  /usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc
do
  if [[ -f "$c" ]]; then FONT="$c"; break; fi
done
if [[ -z "$FONT" ]]; then
  echo "日本語フォントが無い。Noto Sans CJK を入れてから実行する。" >&2
  exit 1
fi
FONTDIR="$(dirname "$FONT")"
inputs=()
for name in 01.png 02.png 03.png 04.png 05.png; do
  if [[ ! -f "$IMAGES/$name" ]]; then
    echo "画像が無い: $IMAGES/$name" >&2
    exit 1
  fi
  inputs+=(-loop 1 -t {SECONDS_EACH:.1f} -i "$IMAGES/$name")
done
filter=""
for i in 0 1 2 3 4; do
  filter+="[$i:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},fps=30,setsar=1[v$i];"
done
filter+="[v0][v1][v2][v3][v4]concat=n=5:v=1:a=0[cat];"
filter+="[cat]subtitles=$SRT:fontsdir=$FONTDIR:force_style='FontName=Noto Sans CJK JP\\,FontSize=64\\,Alignment=8\\,BorderStyle=3\\,Outline=0\\,BackColour=&H00FFFFFF&\\,PrimaryColour=&H00000000&\\,MarginV=160'[cap];"
filter+="[cap]drawtext=text='PR':fontsize=36:fontcolor=black:box=1:boxcolor=white:boxborderw=8:x=w-tw-48:y=48[vout]"
mkdir -p "$(dirname "$OUT")"
if [[ -f "$BGM" ]]; then
  ffmpeg -y "${{inputs[@]}}" -i "$BGM" \\
    -filter_complex "$filter" -map "[vout]" -map 5:a \\
    -t 15 -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest "$OUT"
else
  ffmpeg -y "${{inputs[@]}}" \\
    -filter_complex "$filter" -map "[vout]" \\
    -t 15 -c:v libx264 -pix_fmt yuv420p -an "$OUT"
fi
echo "$OUT"
"""


def _ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"
