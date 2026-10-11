"""After the picture exists: narration fitted to the baked mouth, captions, and music.

H3 is not asked to speak, draw text, or compose music. The baked picture already
moves the speaker's mouth. This module measures those open and close times and
fits each line's voice into that span. It does not redraw the mouth from the
audio. A story may name one voice per role. Without that map, guest and retort
share ja-JP-KeitaNeural and polite and owner share ja-JP-NanamiNeural.
Captions and the music file are the same ffmpeg step as affi_finish.
Empty lines stay empty. This module does not render H3 and does not post.
"""

from __future__ import annotations

import inspect
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

import affi_finish

try:
    from gtts import gTTS
except ImportError:
    # The loader installs this before 選ぶ. A missing package must not stop the sheet.
    gTTS = None

SLOT = "入力"
SKIP_LINES = {SLOT, "台詞は入力", ""}
VOICES = {
    "guest": "ja-JP-KeitaNeural",
    "retort": "ja-JP-KeitaNeural",
    "polite": "ja-JP-NanamiNeural",
    "owner": "ja-JP-NanamiNeural",
    "indoor_pair": "ja-JP-KeitaNeural",
}
DEFAULT_VOICE = "ja-JP-NanamiNeural"
MOUTH_PIXEL = 18
# 0.15% of a 544x960 frame is about 800 pixels and drops a small jaw.
MOUTH_MIN_FRACTION = 0.00008
MOUTH_MAX_FRACTION = 0.12
MOUTH_MAX_BOX = 0.35
SAMPLE_RATE = 44100


def _num(value: float) -> str:
    text = f"{float(value):.3f}".rstrip("0").rstrip(".")
    return text or "0"


def probe(path: Path) -> dict[str, float]:
    """Width, height, duration, and fps from ffprobe."""
    text = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type,width,height,avg_frame_rate",
            "-of",
            "default=nw=1",
            str(path),
        ],
        text=True,
    )
    width = height = 0
    fps = 0.0
    duration = 0.0
    for line in text.splitlines():
        if line.startswith("width=") and width == 0:
            raw = line.split("=", 1)[1]
            if raw.isdigit():
                width = int(raw)
        elif line.startswith("height=") and height == 0:
            raw = line.split("=", 1)[1]
            if raw.isdigit():
                height = int(raw)
        elif line.startswith("avg_frame_rate=") and fps == 0.0:
            rate = line.split("=", 1)[1]
            if "/" in rate and not rate.startswith("0/"):
                num, den = rate.split("/", 1)
                if float(den):
                    fps = float(num) / float(den)
        elif line.startswith("duration="):
            duration = float(line.split("=", 1)[1])
    if width <= 0 or height <= 0 or duration <= 0 or fps <= 0:
        raise RuntimeError(f"動画の寸法が読めない: {path}")
    return {"width": width, "height": height, "duration_s": duration, "fps": fps}


def cues_from_rows(rows: Sequence[Mapping[str, Any]], duration_s: float) -> list[dict[str, Any]]:
    """Spoken rows. A row with burn false, or an empty line, is left out."""
    pending = []
    for row in rows:
        if row.get("burn") is False:
            continue
        text = str(row.get("text") or row.get("line") or "").strip()
        if text in SKIP_LINES:
            continue
        start = float(row["start_s"])
        end = float(row["end_s"])
        if end <= start or start >= duration_s:
            continue
        cue = {
            "id": str(row.get("id") or len(pending) + 1),
            "role": str(row.get("role") or row.get("speaker") or ""),
            "text": text,
            "start_s": start,
            "end_s": min(end, duration_s),
        }
        if str(row.get("voice") or "").strip():
            cue["voice"] = str(row["voice"]).strip()
        pending.append(cue)
    pending.sort(key=lambda item: item["start_s"])
    return pending


def cues_from_structure(pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Filled structure lines only. The evidence line is not the spoken line."""
    shots = {shot["id"]: shot for shot in pack["shots"]}
    pending = []
    for row in pack["captions"]:
        text = str(row.get("line") or "").strip()
        if text in SKIP_LINES:
            continue
        seen = [float(item) for item in row["seen_s"]]
        start = min(seen)
        shot_end = float(shots[row["shot"]]["end_s"])
        pending.append(
            {
                "id": row["id"],
                "role": row["role"],
                "text": text,
                "voice": voice_for(str(row["role"]), pack.get("voices")),
                "start_s": start,
                "shot_end": shot_end,
            }
        )
    pending.sort(key=lambda item: item["start_s"])
    duration = float(pack["duration_s"])
    cues = []
    for index, row in enumerate(pending):
        nxt = pending[index + 1]["start_s"] if index + 1 < len(pending) else row["shot_end"]
        end = min(row["shot_end"], nxt, duration)
        if end <= row["start_s"]:
            end = min(duration, row["start_s"] + 0.4)
        if row["start_s"] >= duration:
            continue
        cues.append(
            {
                "id": row["id"],
                "role": row["role"],
                "text": row["text"],
                "voice": row["voice"],
                "start_s": row["start_s"],
                "end_s": end,
            }
        )
    return cues


def picture_in(job_dir: Path) -> Path | None:
    """The joined mp4, or the only clip when the join has not been written."""
    folder = Path(job_dir)
    for name in ("story.mp4", "source.mp4"):
        path = folder / name
        if path.is_file():
            return path
    clips_dir = folder / "clips"
    clips = sorted(clips_dir.glob("*.mp4")) if clips_dir.is_dir() else []
    if len(clips) == 1:
        return clips[0]
    return None


def speak_seconds(text: str, role: str, voices: Mapping[str, Any] | None = None) -> float | None:
    """How long this line takes in its role voice. None when that cannot be measured."""
    try:
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "line.wav"
            synth_edge(text, role, dest, voice=voice_for(role, voices))
            return probe_audio(dest)
    except Exception:
        return None


def voice_for(role: str, voices: Mapping[str, Any] | None = None) -> str:
    """The story map wins. Without one, the shared defaults stay."""
    if voices and str(voices.get(role) or "").strip():
        return str(voices[role]).strip()
    return VOICES.get(role, DEFAULT_VOICE)


def synth_edge(text: str, role: str, dest: Path, voice: str | None = None) -> None:
    """One line. ``espeak:`` and ``gtts:`` are extra Japanese voices. Anything else is edge-tts."""
    chosen = voice or voice_for(role)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if chosen.startswith("espeak:"):
        name = chosen.split(":", 1)[1].strip() or "ja"
        subprocess.check_call(["espeak-ng", "-v", name, "-w", str(dest), text])
        return
    if chosen.startswith("gtts:"):
        if gTTS is None:
            raise ValueError("gTTS が無い。読み込みをやり直す。")
        lang = chosen.split(":", 1)[1].strip() or "ja"
        gTTS(text, lang=lang).save(str(dest))
        return
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "edge_tts",
            "--voice",
            chosen,
            "--text",
            text,
            "--write-media",
            str(dest),
        ]
    )


def _speak(synth: Callable[..., None], text: str, role: str, dest: Path, voice: str) -> None:
    params = inspect.signature(synth).parameters
    if "voice" in params:
        synth(text, role, dest, voice=voice)
        return
    synth(text, role, dest)


def _fit_argv(src: Path, dest: Path, window_s: float) -> list[str]:
    info = probe_audio(src)
    if info > window_s + 0.05:
        tempo = min(2.0, info / window_s)
        filt = f"atempo={tempo:.4f},atrim=0:{window_s:.3f},apad=whole_dur={window_s:.3f}"
    else:
        filt = f"apad=whole_dur={window_s:.3f},atrim=0:{window_s:.3f}"
    return [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-i",
        str(src),
        "-af",
        filt,
        "-ar",
        str(SAMPLE_RATE),
        "-ac",
        "2",
        str(dest),
    ]


def probe_audio(path: Path) -> float:
    text = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        text=True,
    )
    return float(text.strip())


def narration_argv(duration_s: float, pieces: Sequence[tuple[Path, float]], out: Path) -> list[str]:
    """Silence for the whole picture, with each fitted line delayed to its start."""
    args = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-f",
        "lavfi",
        "-i",
        f"anullsrc=r={SAMPLE_RATE}:cl=stereo:d={duration_s:.3f}",
    ]
    filters = []
    labels = []
    for index, (wav, start_s) in enumerate(pieces, start=1):
        args.extend(["-i", str(wav)])
        delay = max(0, int(round(start_s * 1000)))
        label = f"a{index}"
        filters.append(f"[{index}:a]adelay={delay}|{delay},apad[{label}]")
        labels.append(f"[{label}]")
    count = 1 + len(pieces)
    mix = "".join(labels)
    filters.append(f"[0:a]{mix}amix=inputs={count}:duration=first:dropout_transition=0:normalize=0[a]")
    args.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[a]",
            "-c:a",
            "pcm_s16le",
            str(out),
        ]
    )
    return args


def build_narration(
    cues: Sequence[Mapping[str, Any]],
    duration_s: float,
    dest: Path,
    work: Path,
    synth: Callable[[str, str, Path], None],
) -> None:
    pieces: list[tuple[Path, float]] = []
    for cue in cues:
        raw = work / f"{cue['id']}-raw.wav"
        fitted = work / f"{cue['id']}.wav"
        voice = str(cue.get("voice") or voice_for(str(cue["role"])))
        _speak(synth, str(cue["text"]), str(cue["role"]), raw, voice)
        window = float(cue["end_s"]) - float(cue["start_s"])
        subprocess.check_call(_fit_argv(raw, fitted, window))
        pieces.append((fitted, float(cue["start_s"])))
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(narration_argv(duration_s, pieces, dest))


def _compact_change(prev: np.ndarray, frame: np.ndarray) -> bool:
    """True when a small region changed. A cut or a still frame is not a mouth."""
    diff = np.abs(frame.astype(np.int16) - prev.astype(np.int16))
    if diff.ndim == 3:
        diff = diff.mean(axis=2)
    changed = diff > MOUTH_PIXEL
    fraction = float(changed.mean())
    if fraction < MOUTH_MIN_FRACTION or fraction > MOUTH_MAX_FRACTION:
        return False
    ys, xs = np.nonzero(changed)
    if ys.size == 0:
        return False
    box = int(ys.max() - ys.min() + 1) * int(xs.max() - xs.min() + 1)
    frame_area = int(frame.shape[0]) * int(frame.shape[1])
    return box / frame_area <= MOUTH_MAX_BOX


def mouths_for_cues(
    video: Path,
    cues: Sequence[Mapping[str, Any]],
    info: Mapping[str, float],
) -> list[dict[str, Any]]:
    """Fit each line to the mouth motion inside its shot. The picture is not rewritten.

    A mouth interval is the first compact change through the last one in that line's
    seconds. One change that stays counts through the end of those seconds.
    """
    width, height = int(info["width"]), int(info["height"])
    fps = float(info["fps"])
    if fps <= 0:
        raise ValueError("絵のフレームレートが読めない")
    frame_bytes = width * height * 3
    pending = [
        {"active": [], "anchor": None, "held": False}
        for _cue in cues
    ]
    decode = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", str(video), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE,
    )
    assert decode.stdout is not None
    index = 0
    prev: np.ndarray | None = None
    while True:
        buf = decode.stdout.read(frame_bytes)
        if len(buf) < frame_bytes:
            break
        frame = np.frombuffer(buf, dtype=np.uint8).reshape((height, width, 3)).copy()
        if prev is not None:
            stamp = index / fps
            changed = _compact_change(prev, frame)
            for cue, state in zip(cues, pending):
                start = float(cue["start_s"])
                end = float(cue["end_s"])
                if stamp < start or stamp >= end:
                    continue
                if changed:
                    state["active"].append(index)
                    if state["anchor"] is None:
                        state["anchor"] = prev.copy()
                anchor = state["anchor"]
                if anchor is not None and _compact_change(anchor, frame):
                    state["held"] = True
        prev = frame.copy()
        index += 1
    decode.wait()
    if index == 0:
        raise ValueError("絵のフレームが読めない")
    fitted: list[dict[str, Any]] = []
    for cue, state in zip(cues, pending):
        active: list[int] = state["active"]
        end = float(cue["end_s"])
        if len(active) >= 2:
            open_s = active[0] / fps
            close_s = min(end, (active[-1] + 1) / fps)
        elif len(active) == 1 and state["held"]:
            open_s = active[0] / fps
            close_s = end
        else:
            raise ValueError(f"絵から口の開閉が測れない: {cue['id']}")
        if close_s <= open_s:
            raise ValueError(f"絵から口の開閉が測れない: {cue['id']}")
        row = dict(cue)
        row["start_s"] = round(open_s, 3)
        row["end_s"] = round(close_s, 3)
        if row["end_s"] <= row["start_s"]:
            raise ValueError(f"絵から口の開閉が測れない: {cue['id']}")
        fitted.append(row)
    return fitted


def mux_picture(video: Path, audio: Path, dest: Path) -> None:
    """Keep the baked picture and replace its audio. The mouth pixels stay."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(video),
            "-i",
            str(audio),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "pcm_s16le",
            str(dest),
        ]
    )


def _blocked(reasons: list[str]) -> dict[str, Any]:
    return {
        "status": "blocked",
        "blocked": reasons,
        "out": "",
        "generates_h3": False,
        "posts": False,
    }


def apply(
    video: str | Path,
    out: str | Path,
    *,
    rows: Sequence[Mapping[str, Any]] | None = None,
    pack: Mapping[str, Any] | None = None,
    bgm: str | Path | None = None,
    synth: Callable[..., None] | None = None,
    work: str | Path | None = None,
) -> dict[str, Any]:
    """Measure the baked mouth, then fit the voice. Does nothing when every line is empty."""
    path = Path(video)
    dest = Path(out)
    if not path.is_file():
        return _blocked(["つないだ動画が無い"])
    info = probe(path)
    cues = cues_from_structure(pack) if pack is not None else cues_from_rows(rows or [], float(info["duration_s"]))
    if not cues:
        return _blocked(["せりふは入力のまま。声は作らない。"])
    music = Path(bgm) if bgm else None
    if music is not None and not music.is_file():
        return _blocked(["曲のファイルが無い"])
    try:
        fitted = mouths_for_cues(path, cues, info)
    except ValueError as exc:
        return _blocked([str(exc)])
    folder = Path(work) if work is not None else dest.parent / "post-work"
    folder.mkdir(parents=True, exist_ok=True)
    narration = folder / "narration.wav"
    build_narration(fitted, float(info["duration_s"]), narration, folder, synth or synth_edge)
    picture = folder / "picture.mov"
    mux_picture(path, narration, picture)
    height = int(info["height"])
    style = affi_finish.caption_style("白ゴシック。細い影。画面の下から約30%。", height=height)
    captions = [
        {"start_s": cue["start_s"], "end_s": cue["end_s"], "text": cue["text"], "burn": True}
        for cue in fitted
    ]
    ass = folder / "captions.ass"
    ass.write_text(
        affi_finish.ass_document(
            width=int(info["width"]),
            height=height,
            captions=captions,
            style=style,
        ),
        encoding="utf-8",
    )
    subprocess.check_call(
        affi_finish.finish_argv(
            picture,
            dest,
            ass_path=ass,
            fonts_dir=affi_finish.FONT_DIR if affi_finish.FONT_DIR.is_dir() else None,
            bgm=music,
        )
    )
    intervals = [{"id": cue["id"], "start_s": cue["start_s"], "end_s": cue["end_s"]} for cue in fitted]
    return {
        "status": "ready",
        "blocked": [],
        "out": str(dest),
        "cues": len(fitted),
        "mouth": {"method": "picture", "intervals": intervals},
        "note": "絵の口は変えていない。開閉を測って、声をその秒に合わせた。",
        "generates_h3": False,
        "posts": False,
    }
