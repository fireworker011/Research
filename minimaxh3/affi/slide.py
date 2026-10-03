"""H3 fallback: one vertical still-image slide. Does not generate images or post.

Eight stills: 表紙 → 問題提起 → five checked facts → 締め.
The biggest answer stays off the picture and at the end of the post.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from minimaxh3.affi.cutlist import write_cuts

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
            "Photoreal edit of sakura-ref.jpg: keep only Sakura's face, long straight "
            "dark-brown hair and bangs. Medium close-up from the chest up, vertical "
            "9:16, a quiet room at dusk, warm lamp light, softly blurred beige wall. "
            "Sakura in a plain oatmeal knit sweater looks into the camera with a calm "
            "closed-lip smile. A small lit candle in a clear unlabeled jar and a slim "
            "frosted-white unbranded bottle sit small on the table behind her. Hands "
            "out of frame. No other people, no hands, no new face, no text, no watermark."
        ),
    },
    {
        "file": "02.png",
        "role": "問題提起",
        "points": (),
        "caption": ("香りで選びたい人は", "先に見て"),
        "imagine": (
            "Photoreal edit of sakura-ref.jpg: keep only Sakura's face, long straight "
            "dark-brown hair and bangs. The same chest-up framing, vertical 9:16, dusk "
            "room. Sakura looks into the camera with slightly lowered brows and a "
            "closed-lip smile. The unlabeled candle and the frosted-white unbranded "
            "bottle stay small behind her. Hands out of frame. No other people, no "
            "hands, no new face, no text, no logo."
        ),
    },
    {
        "file": "03.png",
        "role": "本文",
        "points": ("無着色",),
        "caption": ("無着色",),
        "imagine": (
            "Photoreal edit of sakura-ref.jpg: keep only Sakura's face, long straight "
            "dark-brown hair and bangs. Chest-up, vertical 9:16, soft daylight. Sakura "
            "looks into the camera, closed-lip smile. The slim frosted-white unbranded "
            "bottle stands small beside her, cap on. Hands out of frame. No other "
            "people, no hands, no new face, no text, no logo."
        ),
    },
    {
        "file": "04.png",
        "role": "本文",
        "points": ("アルコールフリー",),
        "caption": ("アルコールフリー",),
        "imagine": (
            "Photoreal edit of sakura-ref.jpg: keep only Sakura's face, long straight "
            "dark-brown hair and bangs. Chest-up, vertical 9:16. Sakura looks into the "
            "camera. Small behind her, the closed unbranded frosted-white bottle beside "
            "a clear glass of water. Hands out of frame. No other people, no hands, no "
            "new face, no text, no logo."
        ),
    },
    {
        "file": "05.png",
        "role": "本文",
        "points": ("パラベンフリー",),
        "caption": ("パラベンフリー",),
        "imagine": (
            "Photoreal edit of sakura-ref.jpg: keep only Sakura's face, long straight "
            "dark-brown hair and bangs. Chest-up, vertical 9:16, soft window light. "
            "Sakura looks into the camera. The closed unbranded bottle is small on a "
            "white tray behind her. Hands out of frame. No other people, no hands, no "
            "new face, no text, no logo."
        ),
    },
    {
        "file": "06.png",
        "role": "本文",
        "points": ("朝晩使える", "メイク前にも"),
        "caption": ("朝晩使える", "メイク前にも"),
        "imagine": (
            "Photoreal edit of sakura-ref.jpg: keep only Sakura's face, long straight "
            "dark-brown hair and bangs. Chest-up, vertical 9:16, quiet morning light. "
            "Sakura looks into the camera. The closed unbranded bottle is small on a "
            "pale windowsill behind her. The window is out of focus. No clock. Hands "
            "out of frame. No other people, no hands, no new face, no text, no logo."
        ),
    },
    {
        "file": "07.png",
        "role": "本文",
        "points": ("ウォッシュ1cm程度", "ローションは100円硬貨程度", "モイスチャライザーはパール1～2粒程度"),
        "caption": ("ウォッシュ1cm、ローションは硬貨", "モイスチャライザーはパール1～2粒"),
        "imagine": (
            "Photoreal edit of sakura-ref.jpg: keep only Sakura's face, long straight "
            "dark-brown hair and bangs. Chest-up, vertical 9:16. Sakura looks into the "
            "camera. Small on a white tray behind her: the closed unbranded bottle, a "
            "plain metal coin, and two small clear gel droplets. No numbers, no letters. "
            "Hands out of frame. No other people, no hands, no new face, no logo."
        ),
    },
    {
        "file": "08.png",
        "role": "締め",
        "points": (),
        "caption": ("紹介してるのは", "プロフィールへ"),
        "imagine": (
            "Photoreal edit of sakura-ref.jpg: keep only Sakura's face, long straight "
            "dark-brown hair and bangs. Chest-up, vertical 9:16, softly blurred beige "
            "wall. Sakura looks into the camera with a calm closed-lip smile and does "
            "not point. The unbranded bottle is small in the lower background. Hands "
            "out of frame. No other people, no hands, no new face, no text, no logo, "
            "no arrow."
        ),
    },
)

POST = """アフィリエイト広告を含みます #PR
香りが好きな人ほど、買う前に。オルビスユー ドット

買う前に知っておきたい表示です。使った感想ではありません。肌に合うかどうかには個人差があります。
メーカー公式ショップのよくある質問で確認しました（2026年10月3日時点）。
無着色。アルコールフリー。パラベンフリー。朝晩お使いいただけます。メイク前にもお使いいただけます。
ウォッシュは1cm程度。ローションは手のひらに100円硬貨程度。モイスチャライザーはパール1～2粒程度。
最新の表示は販売ページでご確認ください。
紹介しているものはプロフィールのリンクからどうぞ。

#PR #スキンケア #化粧水

画像はAIで生成しています。ボトルはAIで作ったイメージで、実際の商品やパッケージとは異なります。人物は既存のキャラクター（サクラ）だけです。新しい顔は作っていません。

一番の答え: このシリーズは無香料です。出典はメーカー公式ショップのよくある質問（2026年10月3日時点）。
"""

ASSIGNMENT = """8枚。並びは表紙、問題提起、確認できた5つ、締め。
1枚目は表紙、2枚目は問題提起、3枚目から7枚目が5つ、8枚目は締め。
語り手はサクラ。顔は既存の sakura-ref.jpg だけ。新しい顔は作らない。手元だけの絵は使わない。
5つは、無着色、アルコールフリー、パラベンフリー、朝晩とメイク前、使う量。出典はメーカー公式ショップのよくある質問（2026年10月3日）。
使う量は、ウォッシュ1cm程度、ローションは手のひらに100円硬貨程度、モイスチャライザーはパール1～2粒程度。
無油分はシリーズのよくある質問には無い。着地URLも不明なので使わない。
一番の答え（無香料）は画面に出さない。字幕にもImagine指示にも書かない。投稿文の末尾に置く。
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
    """直す: the landing URL and the recent-Shorts check are still 不明."""
    return {
        "verdict": "直す",
        "schedule": False,
        "reason": "A8の着地URLは不明。直近Shortsで普段の3倍は不明（未確認）。予約しない。",
        "h3_gate": "不明",
    }


def cut_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, slide in enumerate(SLIDES, start=1):
        rows.append(
            {
                "index": index,
                "src": f"images/{slide['file']}",
                "in": 0.0,
                "out": SECONDS_EACH,
                "subtitle": " / ".join(slide["caption"]),
            }
        )
    return rows


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
        "## 画像8枚（Grok Imagine、9:16。画面の文字は入れない。字幕はあとから焼く）",
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
            "各画像 3.0 秒。8枚で 24.0 秒。1080×1920（9:16）。音声は無し。BGMを置くなら bgm/slide.m4a。",
            "書き出しは cut-list-ffmpeg。タイムラインは作らず、cuts.csv（列は index,src,in,out,subtitle）を読む。",
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
# cut-list-ffmpeg wrapper. Does not post. Does not call Imagine.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$ROOT/../../../.." && pwd)"
OUT="${{1:-$ROOT/{SLIDE_ID}.mp4}}"
cd "$REPO"
exec python -m minimaxh3.affi cutlist render \\
  --csv "$ROOT/cuts.csv" \\
  --out "$OUT" \\
  --purpose slide \\
  --bgm "$ROOT/bgm/slide.m4a"
"""


def write_artifacts() -> None:
    SLIDE_DIR.mkdir(parents=True, exist_ok=True)
    (SLIDE_DIR / "draft.md").write_text(render_draft(), encoding="utf-8")
    (SLIDE_DIR / "captions.srt").write_text(srt(), encoding="utf-8")
    write_cuts(SLIDE_DIR / "cuts.csv", cut_rows())
    script = SLIDE_DIR / "build_slide.sh"
    script.write_text(ffmpeg_script(), encoding="utf-8")
    script.chmod(0o755)


def _ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"
