"""After the picture exists: narration fitted to the baked mouth, captions, and music.

H3 is not asked to speak, draw text, or compose music. The baked picture already
moves the speaker's mouth. This module measures those open and close times and
fits each line's voice into that span. It does not redraw the mouth from the
audio. A story may name one voice per role. Without that map, guest and retort
share ja-JP-KeitaNeural and polite and owner share ja-JP-NanamiNeural.
Captions and the music file are the same ffmpeg step as affi_finish.
Empty lines stay empty. This module does not render H3 and does not post.

Every line is measured before anything stops. A line is first measured as a
small changed region of the whole frame. When that fails, the faces in the
line's seconds are found and only the jaw half of each face is compared with
its upper half, after the camera move is taken out. OpenCV is used only to
measure. The picture is not changed.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

import affi_finish

try:
    from gtts import gTTS
except ImportError:
    # The loader installs this before 選ぶ. A missing package must not stop the sheet.
    gTTS = None

try:
    import cv2
except ImportError:
    # Colab ships OpenCV. Without it the face pass is skipped and the line stays unmeasured.
    cv2 = None

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
# Frames are measured at H3's own canvas size. The joined mp4 is an upscale of it.
WORK_LONG_SIDE = 960
# Jaw half minus upper half of one face, mean gray difference between two frames.
# In the 2026-10-11 pet_sheet bake a silent cat beside a talking one stayed under 0.5.
JAW_MOTION = 1.0
FACE_SCORE = 0.7
FACE_MODEL = "face_detection_yunet_2023mar.onnx"
FACE_MODEL_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/" + FACE_MODEL
FACE_MODEL_SHA256 = "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"
FACE_MODEL_DIR = Path.home() / ".cache" / "affi"
ANIMAL_ROLES = frozenset({"guest", "retort", "polite", "indoor_pair"})
FaceFinder = Callable[[np.ndarray], list[tuple[int, int, int, int]]]


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
) -> list[tuple[float, float]]:
    """Write the voice track. Returns each line's (start, end) as placed.

    A line starts where its mouth opened. When the voice is longer than the
    measured opening, it runs on toward ``limit_s``, the end of the line's own
    seconds on the sheet. When even that is too short, the start moves back,
    no earlier than ``from_s`` (the start of those seconds). Only then is the
    voice sped up, so a late or short opening does not cut the line.
    """
    pieces: list[tuple[Path, float]] = []
    spans: list[tuple[float, float]] = []
    for cue in cues:
        raw = work / f"{cue['id']}-raw.wav"
        fitted = work / f"{cue['id']}.wav"
        voice = str(cue.get("voice") or voice_for(str(cue["role"])))
        _speak(synth, str(cue["text"]), str(cue["role"]), raw, voice)
        start = float(cue["start_s"])
        window = float(cue["end_s"]) - start
        limit = float(cue.get("limit_s", cue["end_s"]))
        earliest = min(start, float(cue.get("from_s", start)))
        spoken = probe_audio(raw)
        if spoken > window:
            if start + spoken <= limit:
                window = spoken
            else:
                start = max(earliest, limit - spoken)
                window = max(window, limit - start)
        subprocess.check_call(_fit_argv(raw, fitted, window))
        pieces.append((fitted, start))
        spans.append((round(start, 3), round(start + window, 3)))
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(narration_argv(duration_s, pieces, dest))
    return spans


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


def work_size(info: Mapping[str, float]) -> tuple[int, int]:
    """Width and height the frames are measured at. Larger pictures are scaled down to H3's canvas."""
    width, height = int(info["width"]), int(info["height"])
    scale = min(1.0, WORK_LONG_SIDE / max(width, height))
    if scale >= 1.0:
        return width, height
    return max(2, int(round(width * scale / 2)) * 2), max(2, int(round(height * scale / 2)) * 2)


def face_model() -> Path | None:
    """The YuNet face model, fetched once into the cache. None when it cannot be fetched or checked."""
    path = FACE_MODEL_DIR / FACE_MODEL
    if not path.is_file():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            part = path.with_suffix(".part")
            urllib.request.urlretrieve(FACE_MODEL_URL, part)
            part.replace(path)
        except Exception:
            return None
    if hashlib.sha256(path.read_bytes()).hexdigest() != FACE_MODEL_SHA256:
        path.unlink()
        return None
    return path


def _clip_box(box: Sequence[float], width: int, height: int) -> tuple[int, int, int, int] | None:
    x, y, w, h = (int(round(float(value))) for value in box[:4])
    left, top = max(0, x), max(0, y)
    right, bottom = min(width, x + w), min(height, y + h)
    if right - left < 24 or bottom - top < 24:
        return None
    return left, top, right - left, bottom - top


def face_finder(role: str) -> FaceFinder | None:
    """Faces in one gray frame. YuNet for every role, and OpenCV's cat-face cascade for animals.

    None when OpenCV is missing. A person's line does not use the cat cascade,
    which also fires on knees and hands.
    """
    if cv2 is None:
        return None
    detectors: list[Callable[[np.ndarray], list[tuple[int, int, int, int]]]] = []
    model = face_model() if hasattr(cv2, "FaceDetectorYN") else None
    if model is not None:
        yunet = cv2.FaceDetectorYN.create(str(model), "", (320, 320), score_threshold=FACE_SCORE)

        def by_yunet(gray: np.ndarray) -> list[tuple[int, int, int, int]]:
            height, width = gray.shape[:2]
            yunet.setInputSize((width, height))
            _count, found = yunet.detect(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR))
            boxes = [] if found is None else [_clip_box(row, width, height) for row in found]
            return [box for box in boxes if box is not None]

        detectors.append(by_yunet)
    cascade_path = Path(getattr(getattr(cv2, "data", None), "haarcascades", "")) / "haarcascade_frontalcatface_extended.xml"
    if role in ANIMAL_ROLES and cascade_path.is_file() and hasattr(cv2, "CascadeClassifier"):
        cascade = cv2.CascadeClassifier(str(cascade_path))

        def by_cascade(gray: np.ndarray) -> list[tuple[int, int, int, int]]:
            height, width = gray.shape[:2]
            found = cascade.detectMultiScale(cv2.equalizeHist(gray), scaleFactor=1.1, minNeighbors=3, minSize=(48, 48))
            boxes = [_clip_box(row, width, height) for row in found]
            return [box for box in boxes if box is not None]

        detectors.append(by_cascade)
    if not detectors:
        return None

    def find(gray: np.ndarray) -> list[tuple[int, int, int, int]]:
        boxes: list[tuple[int, int, int, int]] = []
        for detect in detectors:
            boxes.extend(detect(gray))
        return boxes

    return find


def _iou(left: Sequence[int], right: Sequence[int]) -> float:
    ax, ay, aw, ah = left
    bx, by, bw, bh = right
    width = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    height = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = width * height
    union = aw * ah + bw * bh - inter
    return inter / union if union else 0.0


def _camera(prev: np.ndarray, cur: np.ndarray) -> np.ndarray | None:
    """The whole-frame move between two gray frames (shift, turn, scale). None when it cannot be found."""
    points = cv2.goodFeaturesToTrack(prev, 300, 0.01, 8)
    if points is None or len(points) < 12:
        return None
    moved, status, _err = cv2.calcOpticalFlowPyrLK(prev, cur, points, None)
    kept = status.reshape(-1) == 1
    if int(kept.sum()) < 12:
        return None
    matrix, inliers = cv2.estimateAffinePartial2D(
        points[kept], moved[kept], method=cv2.RANSAC, ransacReprojThreshold=1.0
    )
    if matrix is None or inliers is None or int(inliers.sum()) < 12:
        return None
    return matrix


def _jaw_score(prev: np.ndarray, cur: np.ndarray, box: Sequence[int]) -> float | None:
    """How much more the jaw half of one face changed than its upper half.

    The upper half is lined up first, so a head that turns or slides moves both
    halves alike and cancels out.
    """
    x, y, w, h = (int(value) for value in box)
    before = prev[y : y + h, x : x + w].astype(np.float32)
    after = cur[y : y + h, x : x + w].astype(np.float32)
    if before.shape != after.shape or min(before.shape[:2]) < 24:
        return None
    top = h // 2
    window = cv2.createHanningWindow((w, top), cv2.CV_32F)
    (dx, dy), _response = cv2.phaseCorrelate(before[:top], after[:top], window)
    shift = np.float32([[1, 0, dx], [0, 1, dy]])
    before = cv2.warpAffine(before, shift, (w, h), borderMode=cv2.BORDER_REPLICATE)
    diff = np.abs(cv2.GaussianBlur(after, (3, 3), 0) - cv2.GaussianBlur(before, (3, 3), 0))
    left, right = int(0.2 * w), int(0.8 * w)
    upper = diff[int(0.15 * h) : int(0.5 * h), left:right]
    jaw = diff[int(0.6 * h) :, left:right]
    if upper.size == 0 or jaw.size == 0:
        return None
    return float(jaw.mean() - upper.mean())


def _decode(video: Path, size: tuple[int, int], info: Mapping[str, float]) -> subprocess.Popen:
    width, height = size
    argv = ["ffmpeg", "-v", "error", "-i", str(video)]
    if (width, height) != (int(info["width"]), int(info["height"])):
        argv.extend(["-vf", f"scale={width}:{height}:flags=area"])
    argv.extend(["-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    return subprocess.Popen(argv, stdout=subprocess.PIPE)


def _cue_at(cues: Sequence[Mapping[str, Any]], stamp: float) -> list[int]:
    return [
        index
        for index, cue in enumerate(cues)
        if float(cue["start_s"]) <= stamp < float(cue["end_s"])
    ]


def measure_mouths(
    video: Path,
    cues: Sequence[Mapping[str, Any]],
    info: Mapping[str, float],
    *,
    faces: Callable[[str], FaceFinder | None] | None = None,
) -> list[dict[str, Any]]:
    """One row per line: where the mouth opened and closed, or why it could not be measured.

    The picture pass counts a frame when a small region of the whole frame
    changed. Its interval runs from the first such frame to the last one; one
    change that stays counts through the end of the line's seconds. The face
    pass is used only when the picture pass found nothing: each face seen at
    least three times is followed, and the face whose jaw moved in the most
    frames is the speaker. Nothing is drawn or guessed for a line without one.
    """
    fps = float(info["fps"])
    if fps <= 0:
        raise ValueError("絵のフレームレートが読めない")
    size = work_size(info)
    width, height = size
    finders = faces or face_finder
    use_faces = cv2 is not None
    picture = [{"active": [], "anchor": None, "held": False} for _cue in cues]
    tracks: list[list[dict[str, Any]]] = [[] for _cue in cues]
    finder_of: dict[str, FaceFinder | None] = {}
    decode = _decode(video, size, info)
    assert decode.stdout is not None
    frame_bytes = width * height * 3
    index = 0
    prev: np.ndarray | None = None
    prev_gray: np.ndarray | None = None
    while True:
        buf = decode.stdout.read(frame_bytes)
        if len(buf) < frame_bytes:
            break
        frame = np.frombuffer(buf, dtype=np.uint8).reshape((height, width, 3)).copy()
        stamp = index / fps
        inside = _cue_at(cues, stamp)
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY) if use_faces and inside else None
        if prev is not None and inside:
            changed = _compact_change(prev, frame)
            for slot in inside:
                state = picture[slot]
                if changed:
                    state["active"].append(index)
                    if state["anchor"] is None:
                        state["anchor"] = prev.copy()
                anchor = state["anchor"]
                if anchor is not None and _compact_change(anchor, frame):
                    state["held"] = True
        if gray is not None:
            reference = None
            for slot in inside:
                role = str(cues[slot].get("role") or "")
                if role not in finder_of:
                    finder_of[role] = finders(role)
                finder = finder_of[role]
                if finder is None:
                    continue
                for box in finder(gray):
                    best = max(tracks[slot], key=lambda track: _iou(track["box"], box), default=None)
                    if best is not None and best["last"] != index and _iou(best["box"], box) > 0.3:
                        best["box"], best["last"] = box, index
                        best["hits"] += 1
                    else:
                        tracks[slot].append({"box": box, "last": index, "hits": 1, "active": []})
                if prev_gray is None:
                    continue
                if reference is None:
                    matrix = _camera(prev_gray, gray)
                    reference = prev_gray if matrix is None else cv2.warpAffine(
                        prev_gray, matrix, (width, height), borderMode=cv2.BORDER_REPLICATE
                    )
                for track in tracks[slot]:
                    if index - track["last"] > 3:
                        continue
                    score = _jaw_score(reference, gray, track["box"])
                    if score is not None and score > JAW_MOTION:
                        track["active"].append(index)
        prev = frame
        prev_gray = gray
        index += 1
    decode.wait()
    if index == 0:
        raise ValueError("絵のフレームが読めない")
    rows: list[dict[str, Any]] = []
    for slot, cue in enumerate(cues):
        start = float(cue["start_s"])
        end = float(cue["end_s"])
        row: dict[str, Any] = {
            "id": str(cue["id"]),
            "role": str(cue.get("role") or ""),
            "window_s": [round(start, 3), round(end, 3)],
            "method": None,
            "start_s": None,
            "end_s": None,
            "faces": None,
            "face_search": "yes" if use_faces and finder_of.get(str(cue.get("role") or "")) else (
                "no-detector" if use_faces else "no-opencv"
            ),
        }
        active: list[int] = picture[slot]["active"]
        found: tuple[float, float] | None = None
        if len(active) >= 2:
            found = (active[0] / fps, min(end, (active[-1] + 1) / fps))
        elif len(active) == 1 and picture[slot]["held"]:
            found = (active[0] / fps, end)
        if found is not None and round(found[1], 3) > round(found[0], 3):
            row.update(method="picture", start_s=round(found[0], 3), end_s=round(found[1], 3))
        role = row["role"]
        if use_faces and finder_of.get(role) is not None:
            seen = [track for track in tracks[slot] if track["hits"] >= 3]
            row["faces"] = len(seen)
            talking = [track for track in seen if len(track["active"]) >= 2]
            if row["method"] is None and talking:
                best = max(talking, key=lambda track: len(track["active"]))
                frames = best["active"]
                open_s = max(start, frames[0] / fps)
                close_s = min(end, (frames[-1] + 1) / fps)
                if round(close_s, 3) > round(open_s, 3):
                    row.update(
                        method="face",
                        start_s=round(open_s, 3),
                        end_s=round(close_s, 3),
                        face=list(best["box"]),
                    )
        rows.append(row)
    return rows


def unmeasured_reason(row: Mapping[str, Any]) -> str:
    """One Japanese line for a line whose mouth was not measured."""
    start, end = row["window_s"]
    head = f"絵から口の開閉が測れない: {row['id']}（{_num(start)}〜{_num(end)}秒）"
    search = row.get("face_search")
    if search == "no-opencv":
        return head + "。顔を探せなかった（OpenCV が無い）。"
    if search == "no-detector":
        return head + "。この役の顔の検出器が無い（YuNet が取れなかった）。"
    if not row.get("faces"):
        return head + "。正面の顔が映っていない。"
    return head + "。顔はあるが口が動いていない。"


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
    faces: Callable[[str], FaceFinder | None] | None = None,
    sheet_seconds: bool = False,
) -> dict[str, Any]:
    """Measure the baked mouth, then fit the voice. Does nothing when every line is empty.

    Every line is measured and written to ``post-work/mouths.json`` first. Any
    unmeasured line stops the finish and every such line is listed. With
    ``sheet_seconds`` those lines are placed on their own seconds from the sheet
    instead, and the result says which lines were placed that way.
    """
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
        report = measure_mouths(path, cues, info, faces=faces)
    except ValueError as exc:
        return _blocked([str(exc)])
    folder = Path(work) if work is not None else dest.parent / "post-work"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "mouths.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    missing = [row for row in report if row["method"] is None]
    if missing and not sheet_seconds:
        measured = [row for row in report if row["method"] is not None]
        lines = [unmeasured_reason(row) for row in missing]
        if measured:
            lines.append(
                f"測れたせりふ {len(measured)} / {len(report)}: "
                + "、".join(f"{row['id']} {_num(row['start_s'])}〜{_num(row['end_s'])}秒" for row in measured)
            )
        lines.append(f"測った結果は {folder / 'mouths.json'}。声も字幕も post.mp4 も作っていない。")
        result = _blocked(lines)
        result["mouths"] = report
        return result
    fitted: list[dict[str, Any]] = []
    for cue, row in zip(cues, report):
        placed = dict(cue)
        placed["from_s"] = float(cue["start_s"])
        placed["limit_s"] = float(cue["end_s"])
        if row["method"] is None:
            row["method"] = "sheet"
            row["start_s"], row["end_s"] = row["window_s"]
        placed["start_s"] = float(row["start_s"])
        placed["end_s"] = float(row["end_s"])
        fitted.append(placed)
    narration = folder / "narration.wav"
    spans = build_narration(fitted, float(info["duration_s"]), narration, folder, synth or synth_edge)
    picture = folder / "picture.mov"
    mux_picture(path, narration, picture)
    height = int(info["height"])
    style = affi_finish.caption_style("白ゴシック。細い影。画面の下から約30%。", height=height)
    captions = [
        {"start_s": start, "end_s": end, "text": cue["text"], "burn": True}
        for cue, (start, end) in zip(fitted, spans)
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
    intervals = [
        {
            "id": cue["id"],
            "start_s": cue["start_s"],
            "end_s": cue["end_s"],
            "by": row["method"],
            "voice_s": [start, end],
        }
        for cue, row, (start, end) in zip(fitted, report, spans)
    ]
    for row, (start, end) in zip(report, spans):
        row["voice_s"] = [start, end]
    on_sheet = [row["id"] for row in report if row["method"] == "sheet"]
    note = "絵の口は変えていない。開閉を測って、声をその秒に合わせた。"
    if on_sheet:
        note += f"口が測れなかった {'、'.join(on_sheet)} は、シートのせりふの秒に置いた。"
    (folder / "mouths.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "ready",
        "blocked": [],
        "out": str(dest),
        "cues": len(fitted),
        "mouth": {"method": "picture+sheet" if on_sheet else "picture", "intervals": intervals},
        "mouths": report,
        "note": note,
        "generates_h3": False,
        "posts": False,
    }
