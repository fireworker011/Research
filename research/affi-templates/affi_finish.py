"""Captions, a title card, a name mark, and an own music file, after the clips are joined.

The H3 prompts do not draw writing, so text is drawn here with libass on the
joined master. The master keeps PCM audio. The mp4 is written last, once, so
the AAC priming is covered by the mp4 edit list a single time. Caption place
and colour come from the template sentence. Sizes, the music level, and the
quality setting are defaults, not measured values.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping, Sequence

FONT = "Noto Sans CJK JP"
FONT_DIR = Path("/usr/share/fonts/opentype/noto")
FONT_PACKAGE = "fonts-noto-cjk"
CAPTION_SIZE = 0.035
TITLE_SIZE = 0.06
LOGO_SIZE = 0.02
BGM_VOLUME = 0.25
CRF = "18"
DEFAULT_BOTTOM = 0.10

WHITE = "&H00FFFFFF"
BLACK = "&H00000000"
# ASS colours are &HAABBGGRR.
COLOURS = {
    "青": "&H00FF7800",
    "ピンク": "&H00B469FF",
    "黄": "&H0000E6FF",
    "白": WHITE,
}
_PERCENT = re.compile(r"下から約?(\d+)(?:[〜~～-](\d+))?\s*[%％]")


def ass_time(seconds: float) -> str:
    cs = max(0, int(round(float(seconds) * 100)))
    hours, rem = divmod(cs, 360_000)
    minutes, rem = divmod(rem, 6_000)
    secs, cent = divmod(rem, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{cent:02d}"


def ass_text(text: str) -> str:
    raw = str(text or "").replace("\\", "＼").replace("{", "｛").replace("}", "｝")
    return raw.replace("\r\n", "\n").replace("\n", "\\N")


def _spec_text(spec: Any) -> str:
    if isinstance(spec, Mapping):
        return " ".join(str(value) for key, value in spec.items() if key not in {"certainty", "content"})
    return str(spec or "")


def caption_style(spec: Any, *, height: int) -> dict[str, Any]:
    """Place and colour from the template's subtitle sentence."""
    text = _spec_text(spec)
    colours = [code for word, code in COLOURS.items() if word in text and word != "白"]
    if not colours:
        colours = [WHITE]
    if "白縁" in text:
        outline_colour, outline, shadow = WHITE, 6, 0
    elif "黒" in text and "縁" in text:
        outline_colour, outline, shadow = BLACK, 5, 0
    elif "影" in text:
        outline_colour, outline, shadow = BLACK, 0, 3
    else:
        outline_colour, outline, shadow = BLACK, 4, 0
    found = _PERCENT.search(text)
    if found:
        low = float(found.group(1))
        high = float(found.group(2) or low)
        alignment, margin_v = 2, int(round(height * (low + high) / 200))
        place = f"下から {(low + high) / 2:g}%"
    elif "中央" in text:
        alignment, margin_v = 5, 0
        place = "中央"
    else:
        alignment, margin_v = 2, int(round(height * DEFAULT_BOTTOM))
        place = f"下から {DEFAULT_BOTTOM * 100:g}%（型に位置が無い）"
    return {
        "alignment": alignment,
        "margin_v": margin_v,
        "bold": "太" in text,
        "colours": colours,
        "outline_colour": outline_colour,
        "outline": outline,
        "shadow": shadow,
        "place": place,
    }


def _style_line(name: str, size: int, colour: str, outline_colour: str, *, bold: bool, outline: int, shadow: int, alignment: int, margin_v: int) -> str:
    return (
        f"Style: {name},{FONT},{size},{colour},&H000000FF,{outline_colour},&H64000000,"
        f"{-1 if bold else 0},0,0,0,100,100,0,0,1,{outline},{shadow},{alignment},40,40,{margin_v},1"
    )


def ass_document(
    *,
    width: int,
    height: int,
    captions: Sequence[Mapping[str, Any]] = (),
    style: Mapping[str, Any] | None = None,
    title: str = "",
    cover_end_s: float | None = None,
    logo: str = "",
    duration_s: float | None = None,
) -> str:
    """One ASS file. Rows with ``burn`` false are left out."""
    look = dict(style or caption_style("", height=height))
    caption_size = int(round(height * CAPTION_SIZE))
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {int(width)}",
        f"PlayResY: {int(height)}",
        "WrapStyle: 2",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        _style_line(
            "Caption",
            caption_size,
            look["colours"][0],
            look["outline_colour"],
            bold=bool(look["bold"]),
            outline=int(look["outline"]),
            shadow=int(look["shadow"]),
            alignment=int(look["alignment"]),
            margin_v=int(look["margin_v"]),
        ),
        _style_line("Title", int(round(height * TITLE_SIZE)), WHITE, BLACK, bold=True, outline=4, shadow=0, alignment=5, margin_v=0),
        _style_line("Logo", int(round(height * LOGO_SIZE)), WHITE, BLACK, bold=False, outline=1, shadow=0, alignment=9, margin_v=40),
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    burned = [row for row in captions if row.get("burn") and str(row.get("text") or "").strip()]
    for index, row in enumerate(burned):
        colour = look["colours"][index % len(look["colours"])]
        tint = "" if colour == look["colours"][0] else f"{{\\1c{colour}}}"
        lines.append(
            f"Dialogue: 1,{ass_time(row['start_s'])},{ass_time(row['end_s'])},Caption,,0,0,0,,{tint}{ass_text(row['text'])}"
        )
    if title.strip() and cover_end_s and cover_end_s > 0:
        box = f"{{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&H000000&}}m 0 0 l {int(width)} 0 {int(width)} {int(height)} 0 {int(height)}{{\\p0}}"
        lines.append(f"Dialogue: 2,{ass_time(0)},{ass_time(cover_end_s)},Title,,0,0,0,,{box}")
        lines.append(f"Dialogue: 3,{ass_time(0)},{ass_time(cover_end_s)},Title,,0,0,0,,{ass_text(title.strip())}")
    if logo.strip() and duration_s:
        lines.append(f"Dialogue: 4,{ass_time(0)},{ass_time(duration_s)},Logo,,0,0,0,,{ass_text(logo.strip())}")
    return "\n".join(lines) + "\n"


def has_events(document: str) -> bool:
    return any(line.startswith("Dialogue:") for line in document.splitlines())


def finish_argv(
    master: Path,
    out_path: Path,
    *,
    ass_path: Path | None = None,
    fonts_dir: Path | None = None,
    bgm: Path | None = None,
    bgm_volume: float = BGM_VOLUME,
) -> list[str]:
    """From the PCM master to the delivery mp4. Draws text and mixes an own music file when given."""
    args = ["ffmpeg", "-y", "-i", str(master)]
    filters: list[str] = []
    video_map, audio_map = "0:v", "0:a"
    if bgm is not None:
        args.extend(["-stream_loop", "-1", "-i", str(bgm)])
        filters.append(f"[1:a]volume={bgm_volume:g}[bgm]")
        filters.append("[0:a][bgm]amix=inputs=2:duration=first:normalize=0[a]")
        audio_map = "[a]"
    if ass_path is not None:
        drawn = f"[0:v]ass=filename='{ass_path}'"
        if fonts_dir is not None:
            drawn += f":fontsdir='{fonts_dir}'"
        filters.append(drawn + "[v]")
        video_map = "[v]"
    if filters:
        args.extend(["-filter_complex", ";".join(filters)])
    args.extend(["-map", video_map, "-map", audio_map])
    if ass_path is not None:
        args.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", CRF])
    else:
        args.extend(["-c:v", "copy"])
    args.extend(["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out_path)])
    return args
