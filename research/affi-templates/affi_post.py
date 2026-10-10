"""After the picture exists: narration, mouth, captions, and an own music file.

H3 is not asked to speak, draw text, or compose music. Narration is edge-tts
(ja-JP-NanamiNeural and ja-JP-KeitaNeural, the two Japanese voices that tool
lists). The mouth opens with the loudness of that voice when a face box is
known. Captions and the music file are the same ffmpeg step as affi_finish.
Empty lines stay empty. This module does not render H3 and does not post.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

import affi_finish

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
MOUTH_GAIN = 4.0
MOUTH_MAX = 0.45
MOUTH_SPLIT = 0.55
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
        pending.append(
            {
                "id": str(row.get("id") or len(pending) + 1),
                "role": str(row.get("role") or row.get("speaker") or ""),
                "text": text,
                "start_s": start,
                "end_s": min(end, duration_s),
            }
        )
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


def voice_for(role: str) -> str:
    return VOICES.get(role, DEFAULT_VOICE)


def synth_edge(text: str, role: str, dest: Path) -> None:
    """One line, via edge-tts. The voice is one of the two Japanese voices it lists."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "edge_tts",
            "--voice",
            voice_for(role),
            "--text",
            text,
            "--write-media",
            str(dest),
        ]
    )


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
        synth(str(cue["text"]), str(cue["role"]), raw)
        window = float(cue["end_s"]) - float(cue["start_s"])
        subprocess.check_call(_fit_argv(raw, fitted, window))
        pieces.append((fitted, float(cue["start_s"])))
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(narration_argv(duration_s, pieces, dest))


def _open_mouth(frame: np.ndarray, box: tuple[int, int, int, int], amount: float) -> np.ndarray:
    """Stretch the lower face while the voice is loud. amount 0 leaves the frame."""
    if amount <= 0.02:
        return frame
    x1, y1, x2, y2 = box
    x1 = max(0, min(frame.shape[1] - 1, x1))
    x2 = max(x1 + 1, min(frame.shape[1], x2))
    y1 = max(0, min(frame.shape[0] - 1, y1))
    y2 = max(y1 + 1, min(frame.shape[0], y2))
    face = frame[y1:y2, x1:x2]
    split = int(face.shape[0] * MOUTH_SPLIT)
    if split <= 0 or split >= face.shape[0]:
        return frame
    upper = face[:split]
    lower = face[split:]
    scale = 1.0 + min(MOUTH_MAX, amount)
    new_h = max(1, int(round(lower.shape[0] * scale)))
    if new_h == lower.shape[0]:
        return frame
    index = np.linspace(0, lower.shape[0] - 1, new_h).astype(np.int64)
    stretched = lower[index]
    target = lower.shape[0]
    if new_h >= target:
        start = (new_h - target) // 2
        fitted = stretched[start : start + target]
    else:
        fitted = np.concatenate([stretched, np.repeat(stretched[-1:], target - new_h, axis=0)], axis=0)
    out = frame.copy()
    out[y1:y2, x1:x2] = np.concatenate([upper, fitted], axis=0)
    return out


def detect_face(frame: np.ndarray) -> tuple[int, int, int, int] | None:
    """Largest frontal face as x1,y1,x2,y2. None when OpenCV or a face is absent.

    cv2 is imported here because the notebook installs it in this process after
    the module may already have been imported.
    """
    try:
        import cv2
    except ImportError:
        return None
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    found = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
    if len(found) == 0:
        return None
    x, y, w, h = max(found, key=lambda item: int(item[2]) * int(item[3]))
    return int(x), int(y), int(x + w), int(y + h)


def sync_mouths(
    video: Path,
    audio: Path,
    dest: Path,
    *,
    box: tuple[int, int, int, int] | None = None,
    command: str | None = None,
) -> dict[str, Any]:
    """Rewrite the mouth from the narration, or run an external command when one is set."""
    if command:
        subprocess.check_call(command, shell=True)
        return {"method": "external", "mouth_frames": None, "face": None}
    info = probe(video)
    width, height, fps = int(info["width"]), int(info["height"]), float(info["fps"])
    samples = np.frombuffer(
        subprocess.check_output(
            [
                "ffmpeg",
                "-v",
                "error",
                "-i",
                str(audio),
                "-ac",
                "1",
                "-ar",
                "16000",
                "-f",
                "f32le",
                "-",
            ]
        ),
        dtype=np.float32,
    )
    hop = max(1, int(round(16000 / fps)))
    frame_bytes = width * height * 3
    decode = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", str(video), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE,
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    encode = subprocess.Popen(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{width}x{height}",
            "-r",
            _num(fps),
            "-i",
            "-",
            "-i",
            str(audio),
            "-map",
            "0:v",
            "-map",
            "1:a",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "pcm_s16le",
            str(dest),
        ],
        stdin=subprocess.PIPE,
    )
    frames = 0
    mouth_frames = 0
    face_frames = 0
    cached: tuple[int, int, int, int] | None = box
    assert decode.stdout is not None and encode.stdin is not None
    while True:
        buf = decode.stdout.read(frame_bytes)
        if len(buf) < frame_bytes:
            break
        frame = np.frombuffer(buf, dtype=np.uint8).reshape((height, width, 3))
        start = frames * hop
        chunk = samples[start : start + hop]
        rms = float(np.sqrt(np.mean(np.square(chunk)))) if chunk.size else 0.0
        if box is None and frames % 6 == 0:
            cached = detect_face(frame)
        used = box if box is not None else cached
        if used is not None:
            face_frames += 1
            amount = min(MOUTH_MAX, rms * MOUTH_GAIN)
            if amount > 0.02:
                frame = _open_mouth(frame, used, amount)
                mouth_frames += 1
        encode.stdin.write(np.ascontiguousarray(frame).tobytes())
        frames += 1
    encode.stdin.close()
    decode.wait()
    code = encode.wait()
    if code != 0 or frames == 0:
        raise RuntimeError(f"口の書き出しに失敗した。終了コード {code}")
    return {
        "method": "loudness",
        "frames": frames,
        "mouth_frames": mouth_frames,
        "face_frames": face_frames,
        "face": face_frames > 0,
    }


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
    synth: Callable[[str, str, Path], None] | None = None,
    face_box: tuple[int, int, int, int] | None = None,
    work: str | Path | None = None,
) -> dict[str, Any]:
    """Narration, mouth, captions, and optional music. Does nothing when every line is empty."""
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
    folder = Path(work) if work is not None else dest.parent / "post-work"
    folder.mkdir(parents=True, exist_ok=True)
    narration = folder / "narration.wav"
    build_narration(cues, float(info["duration_s"]), narration, folder, synth or synth_edge)
    mouthed = folder / "mouthed.mov"
    command = os.environ.get("LIPSYNC_CMD", "").strip()
    if command:
        command = command.format(
            video=shlex.quote(str(path)),
            audio=shlex.quote(str(narration)),
            out=shlex.quote(str(mouthed)),
        )
    mouth = sync_mouths(path, narration, mouthed, box=face_box, command=command or None)
    height = int(info["height"])
    style = affi_finish.caption_style("白ゴシック。細い影。画面の下から約30%。", height=height)
    captions = [
        {"start_s": cue["start_s"], "end_s": cue["end_s"], "text": cue["text"], "burn": True}
        for cue in cues
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
            mouthed,
            dest,
            ass_path=ass,
            fonts_dir=affi_finish.FONT_DIR if affi_finish.FONT_DIR.is_dir() else None,
            bgm=music,
        )
    )
    note = "顔が無い区間は絵のまま。声だけ載せた。"
    if mouth.get("face"):
        note = f"口を開けたフレームは {mouth['mouth_frames']}。"
    if mouth.get("method") == "external":
        note = "口は外部のコマンドで合わせた。"
    return {
        "status": "ready",
        "blocked": [],
        "out": str(dest),
        "cues": len(cues),
        "mouth": mouth,
        "note": note,
        "generates_h3": False,
        "posts": False,
    }
