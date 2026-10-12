"""After the picture: voice, mouth, captions, and an own music file. No H3 render."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import affi_media
import affi_post
import affi_structure as structure

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg が無い")
needs_espeak = pytest.mark.skipif(shutil.which("espeak-ng") is None, reason="espeak-ng が無い")
needs_cv2 = pytest.mark.skipif(affi_post.cv2 is None, reason="OpenCV が無い")
WIDTH = 288
HEIGHT = 512
FPS = 8
MOUTH_BOX = (120, 200, 150, 240)


def test_voices_follow_the_role() -> None:
    assert affi_post.voice_for("guest") == "ja-JP-KeitaNeural"
    assert affi_post.voice_for("retort") == "ja-JP-KeitaNeural"
    assert affi_post.voice_for("indoor_pair") == "ja-JP-KeitaNeural"
    assert affi_post.voice_for("polite") == "ja-JP-NanamiNeural"
    assert affi_post.voice_for("owner") == "ja-JP-NanamiNeural"
    assert affi_post.voice_for("other") == "ja-JP-NanamiNeural"


def test_empty_and_evidence_lines_are_not_cues() -> None:
    rows = [
        {"text": "入力", "start_s": 0.0, "end_s": 1.0, "burn": True},
        {"text": "台詞は入力", "start_s": 1.0, "end_s": 2.0, "burn": True},
        {"text": "おい、そこのデブ", "start_s": 0.0, "end_s": 1.0, "burn": False},
        {"text": "HELLO", "start_s": 0.5, "end_s": 1.2, "burn": True, "role": "guest"},
    ]
    cues = affi_post.cues_from_rows(rows, 2.0)
    assert [row["text"] for row in cues] == ["HELLO"]
    pack = structure.load()
    assert affi_post.cues_from_structure(pack) == []
    one = copy.deepcopy(pack)
    one["captions"][0]["line"] = "文1"
    spoken = affi_post.cues_from_structure(one)
    assert [row["text"] for row in spoken] == ["文1"]
    assert one["captions"][0]["source_line"] not in spoken[0]["text"]


def test_picture_in_prefers_the_joined_file(tmp_path: Path) -> None:
    clips = tmp_path / "clips"
    clips.mkdir()
    only = clips / "01.mp4"
    only.write_bytes(b"x")
    assert affi_post.picture_in(tmp_path) == only
    source = tmp_path / "source.mp4"
    source.write_bytes(b"s")
    assert affi_post.picture_in(tmp_path) == source
    story = tmp_path / "story.mp4"
    story.write_bytes(b"j")
    assert affi_post.picture_in(tmp_path) == story
    story.unlink()
    source.unlink()
    (clips / "02.mp4").write_bytes(b"y")
    assert affi_post.picture_in(tmp_path) is None


def test_a_story_map_overrides_the_shared_voices() -> None:
    voices = {
        "guest": "espeak:ja",
        "retort": "ja-JP-KeitaNeural",
        "polite": "ja-JP-NanamiNeural",
        "owner": "gtts:ja",
    }
    assert affi_post.voice_for("guest", voices) == "espeak:ja"
    assert affi_post.voice_for("retort", voices) == "ja-JP-KeitaNeural"
    assert affi_post.voice_for("indoor_pair", voices) == "ja-JP-KeitaNeural"
    assert len(set(voices.values())) == len(voices)


def test_compact_change_is_a_small_region() -> None:
    still = np.zeros((80, 40, 3), np.uint8)
    assert affi_post._compact_change(still, still) is False
    assert affi_post._compact_change(still, np.full_like(still, 255)) is False
    mouth = still.copy()
    mouth[40:48, 10:18] = 255
    assert affi_post._compact_change(still, mouth) is True
    wide = np.zeros((960, 544, 3), np.uint8)
    jaw = wide.copy()
    jaw[400:420, 250:270] = 255
    assert affi_post._compact_change(wide, jaw) is True


def test_missing_gtts_stops_in_japanese(tmp_path: Path) -> None:
    saved = affi_post.gTTS
    affi_post.gTTS = None
    try:
        with pytest.raises(ValueError, match="gTTS"):
            affi_post.synth_edge("あ", "owner", tmp_path / "line.wav", voice="gtts:ja")
    finally:
        affi_post.gTTS = saved


def test_a_missing_picture_or_music_file_blocks(tmp_path: Path) -> None:
    missing = affi_post.apply(tmp_path / "none.mp4", tmp_path / "post.mp4", rows=[])
    assert missing["status"] == "blocked"
    assert missing["blocked"] == ["つないだ動画が無い"]
    assert missing["generates_h3"] is False
    assert missing["posts"] is False


@needs_ffmpeg
def test_unfilled_lines_do_not_speak(tmp_path: Path) -> None:
    video = tmp_path / "story.mp4"
    _pattern_clip(video)
    spoken: list[str] = []

    def boom(text: str, role: str, dest: Path) -> None:
        spoken.append(text)
        raise AssertionError(text)

    blocked = affi_post.apply(
        video,
        tmp_path / "post.mp4",
        rows=[
            {"text": "入力", "start_s": 0.0, "end_s": 1.0, "burn": True},
            {"text": "おい、そこのデブ", "start_s": 0.0, "end_s": 1.0, "burn": False},
        ],
        synth=boom,
    )
    assert blocked["status"] == "blocked"
    assert blocked["blocked"] == ["せりふは入力のまま。声は作らない。"]
    assert spoken == []
    assert not (tmp_path / "post.mp4").exists()
    music = affi_post.apply(
        video,
        tmp_path / "with-music.mp4",
        rows=[{"text": "HELLO", "start_s": 0.2, "end_s": 0.8, "burn": True}],
        bgm=tmp_path / "missing.wav",
        synth=boom,
    )
    assert music["blocked"] == ["曲のファイルが無い"]
    assert spoken == []


@needs_ffmpeg
def test_voice_follows_the_measured_mouth_and_the_picture_stays(tmp_path: Path) -> None:
    video = tmp_path / "story.mp4"
    _mouth_clip(video, range(6, 10))
    before = _rgb_frames(video)
    spoken: list[str] = []

    def synth(text: str, role: str, dest: Path) -> None:
        spoken.append(text)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-f",
                "lavfi",
                "-i",
                "aevalsrc='sin(2*PI*880*t)':s=44100:d=0.5",
                "-ac",
                "2",
                str(dest),
            ],
            check=True,
        )

    bgm = tmp_path / "bed.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "aevalsrc='sin(2*PI*220*t)':s=44100:d=3",
            "-ac",
            "2",
            str(bgm),
        ],
        check=True,
    )
    out = tmp_path / "post.mp4"
    result = affi_post.apply(
        video,
        out,
        rows=[
            {"id": "skip", "text": "入力", "start_s": 0.0, "end_s": 0.4, "burn": True, "role": "guest"},
            {"id": "src", "text": "おい、そこのデブ", "start_s": 0.0, "end_s": 0.4, "burn": False, "role": "guest"},
            {"id": "c1", "text": "HELLO", "start_s": 0.25, "end_s": 1.75, "burn": True, "role": "owner", "voice": "ja-JP-NanamiNeural"},
        ],
        bgm=bgm,
        synth=synth,
        faces=_no_faces,
    )
    assert result["status"] == "ready"
    assert result["generates_h3"] is False
    assert result["posts"] is False
    assert result["cues"] == 1
    assert result["mouth"]["method"] == "picture"
    assert result["note"] == "絵の口は変えていない。開閉を測って、声をその秒に合わせた。"
    interval = result["mouth"]["intervals"][0]
    assert interval["start_s"] == pytest.approx(0.75, abs=0.02)
    assert interval["end_s"] == pytest.approx(1.25, abs=0.02)
    assert spoken == ["HELLO"]
    assert out.is_file()
    samples = affi_media._decode_mono(out, 16000)
    loud = np.flatnonzero(np.abs(samples) > 0.45)
    assert loud.size
    assert float(loud[0]) / 16000 == pytest.approx(interval["start_s"], abs=0.08)
    early = samples[: int(0.5 * 16000)]
    assert float(np.abs(early).max()) < 0.35
    after = _rgb_frames(out)
    assert _mouth_diff(before[8], after[8]) < 25
    raw = subprocess.check_output(
        ["ffmpeg", "-v", "error", "-ss", "1.0", "-i", str(out), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    )
    frame = np.frombuffer(raw, dtype=np.uint8).reshape(HEIGHT, WIDTH)
    band = frame[HEIGHT - int(HEIGHT * 0.30) - 40 : HEIGHT - int(HEIGHT * 0.30) + 5]
    assert int(band.max()) > 200
    assert int(frame[:100].max()) < 40


@needs_ffmpeg
def test_a_still_picture_does_not_invent_a_mouth(tmp_path: Path) -> None:
    video = tmp_path / "story.mp4"
    _pattern_clip(video)
    spoken: list[str] = []

    def boom(text: str, role: str, dest: Path) -> None:
        spoken.append(text)
        raise AssertionError(text)

    result = affi_post.apply(
        video,
        tmp_path / "post.mp4",
        rows=[{"id": "c1", "text": "HELLO", "start_s": 0.25, "end_s": 1.75, "burn": True, "role": "guest"}],
        synth=boom,
        faces=_no_faces,
    )
    assert result["status"] == "blocked"
    assert result["blocked"][0].startswith("絵から口の開閉が測れない: c1（0.25〜1.75秒）。")
    assert result["blocked"][-1].endswith("声も字幕も post.mp4 も作っていない。")
    assert result["posts"] is False
    assert spoken == []
    assert not (tmp_path / "post.mp4").exists()
    saved = json.loads((tmp_path / "post-work" / "mouths.json").read_text(encoding="utf-8"))
    assert [(row["id"], row["method"]) for row in saved] == [("c1", None)]


@needs_ffmpeg
def test_every_line_is_measured_before_the_finish_stops(tmp_path: Path) -> None:
    video = tmp_path / "story.mp4"
    _mouth_clip(video, range(10, 14))
    result = affi_post.apply(
        video,
        tmp_path / "post.mp4",
        rows=[
            {"id": "c01", "text": "まえ", "start_s": 0.1, "end_s": 1.0, "burn": True, "role": "retort"},
            {"id": "c02", "text": "あと", "start_s": 1.1, "end_s": 1.9, "burn": True, "role": "polite"},
        ],
        synth=_tone,
        faces=_no_faces,
    )
    assert result["status"] == "blocked"
    assert result["blocked"][0].startswith("絵から口の開閉が測れない: c01（0.1〜1秒）")
    assert "測れたせりふ 1 / 2: c02 1.25〜1.875秒" in result["blocked"]
    assert [row["method"] for row in result["mouths"]] == [None, "picture"]
    assert not (tmp_path / "post.mp4").exists()
    placed = affi_post.apply(
        video,
        tmp_path / "post.mp4",
        rows=[
            {"id": "c01", "text": "まえ", "start_s": 0.1, "end_s": 1.0, "burn": True, "role": "retort"},
            {"id": "c02", "text": "あと", "start_s": 1.1, "end_s": 1.9, "burn": True, "role": "polite"},
        ],
        synth=_tone,
        faces=_no_faces,
        sheet_seconds=True,
    )
    assert placed["status"] == "ready"
    assert placed["mouth"]["method"] == "picture+sheet"
    assert [(row["id"], row["by"]) for row in placed["mouth"]["intervals"]] == [("c01", "sheet"), ("c02", "picture")]
    assert placed["mouth"]["intervals"][0]["start_s"] == pytest.approx(0.1)
    assert "c01 は、シートのせりふの秒に置いた" in placed["note"]
    assert (tmp_path / "post.mp4").is_file()


@needs_ffmpeg
@needs_cv2
def test_a_jaw_is_measured_on_the_face_while_the_camera_pans(tmp_path: Path) -> None:
    video = tmp_path / "pan.mp4"
    boxes = _pan_clip(video, talking=range(6, 12))
    result = affi_post.measure_mouths(
        video,
        [{"id": "c01", "role": "retort", "start_s": 0.0, "end_s": 2.0}],
        affi_post.probe(video),
        faces=_scripted_faces(boxes),
    )
    row = result[0]
    assert row["method"] == "face"
    assert row["faces"] == 1
    assert row["start_s"] == pytest.approx(6 / FPS, abs=0.07)
    assert row["end_s"] == pytest.approx(13 / FPS, abs=0.07)


@needs_ffmpeg
@needs_cv2
def test_a_pan_alone_is_not_a_mouth(tmp_path: Path) -> None:
    video = tmp_path / "pan.mp4"
    boxes = _pan_clip(video, talking=range(0))
    rows = affi_post.measure_mouths(
        video,
        [{"id": "c01", "role": "retort", "start_s": 0.0, "end_s": 2.0}],
        affi_post.probe(video),
        faces=_scripted_faces(boxes),
    )
    assert rows[0]["method"] is None
    assert rows[0]["faces"] == 1
    assert affi_post.unmeasured_reason(rows[0]).endswith("顔はあるが口が動いていない。")


@needs_ffmpeg
def test_a_short_mouth_does_not_cut_the_line(tmp_path: Path) -> None:
    def long_line(text: str, role: str, dest: Path) -> None:
        _tone(text, role, dest, seconds=0.8)

    spans = affi_post.build_narration(
        [
            {"id": "c1", "role": "retort", "text": "a", "start_s": 0.5, "end_s": 0.7, "from_s": 0.4, "limit_s": 2.0},
            {"id": "c2", "role": "retort", "text": "b", "start_s": 2.2, "end_s": 2.3, "from_s": 2.0, "limit_s": 2.5},
            {"id": "c3", "role": "retort", "text": "c", "start_s": 2.9, "end_s": 3.0, "from_s": 2.7, "limit_s": 3.6},
        ],
        4.0,
        tmp_path / "voice.wav",
        tmp_path,
        long_line,
    )
    assert spans[0] == (0.5, pytest.approx(1.3, abs=0.01))
    assert spans[1] == (2.0, pytest.approx(2.5, abs=0.01))
    assert spans[2] == (2.8, pytest.approx(3.6, abs=0.01))


def test_the_face_model_is_checked_before_use(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "model.onnx"
    source.write_bytes(b"model bytes")
    digest = hashlib.sha256(b"model bytes").hexdigest()
    monkeypatch.setattr(affi_post, "FACE_MODEL_DIR", tmp_path / "cache")
    monkeypatch.setattr(affi_post, "FACE_MODEL_URL", source.as_uri())
    monkeypatch.setattr(affi_post, "FACE_MODEL_SHA256", digest)
    fetched = affi_post.face_model()
    assert fetched == tmp_path / "cache" / affi_post.FACE_MODEL
    assert fetched.read_bytes() == b"model bytes"
    monkeypatch.setattr(affi_post, "FACE_MODEL_SHA256", "0" * 64)
    assert affi_post.face_model() is None
    assert not (tmp_path / "cache" / affi_post.FACE_MODEL).exists()
    monkeypatch.setattr(affi_post, "FACE_MODEL_URL", (tmp_path / "missing.onnx").as_uri())
    assert affi_post.face_model() is None


def test_work_size_is_the_h3_canvas() -> None:
    assert affi_post.work_size({"width": 1080, "height": 1920}) == (540, 960)
    assert affi_post.work_size({"width": 544, "height": 960}) == (544, 960)
    assert affi_post.work_size({"width": 288, "height": 512}) == (288, 512)


@needs_espeak
def test_espeak_writes_a_distinct_guest_voice(tmp_path: Path) -> None:
    dest = tmp_path / "dog.wav"
    affi_post.synth_edge("本日は検品を休業しております", "guest", dest, voice="espeak:ja")
    assert dest.stat().st_size > 1000


def _write_clip(path: Path, frames: list[np.ndarray], lossless: bool = False) -> None:
    subprocess.run(
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
            f"{WIDTH}x{HEIGHT}",
            "-r",
            str(FPS),
            "-i",
            "-",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=stereo:d=2",
            "-c:v",
            "libx264",
            *(["-qp", "0"] if lossless else []),
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(path),
        ],
        input=b"".join(frame.tobytes() for frame in frames),
        check=True,
    )


def _pattern_clip(path: Path) -> None:
    frames = [np.full((HEIGHT, WIDTH, 3), 12, np.uint8) for _ in range(16)]
    _write_clip(path, frames)


def _no_faces(_role: str):
    return lambda _gray: []


def _scripted_faces(boxes: list[tuple[int, int, int, int]]):
    """The face box of each frame, in the order the measurement asks."""

    def finder(_role: str):
        calls = iter(boxes)
        return lambda _gray: [next(calls)]

    return finder


def _tone(text: str, role: str, dest: Path, seconds: float = 0.3) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"aevalsrc='sin(2*PI*660*t)':s=44100:d={seconds}",
            "-ac",
            "2",
            str(dest),
        ],
        check=True,
    )


def _pan_clip(path: Path, talking: range) -> list[tuple[int, int, int, int]]:
    """A textured wall that pans 3 px a frame, with one face on it whose jaw opens on ``talking``."""
    rng = np.random.default_rng(7)
    step = 3
    count = 16
    wide = WIDTH + step * count
    noise = rng.integers(0, 255, size=(HEIGHT // 8 + 1, wide // 8 + 1), dtype=np.uint8)
    wall = np.kron(noise, np.ones((8, 8), np.uint8))[:HEIGHT, :wide].astype(np.float32)
    wall = (wall * 0.6 + 50).astype(np.uint8)
    face_x, face_y, face_w, face_h = 140, 180, 96, 96
    wall[face_y : face_y + face_h, face_x : face_x + face_w] = 170
    wall[face_y + 25 : face_y + 35, face_x + 20 : face_x + 36] = 30
    wall[face_y + 25 : face_y + 35, face_x + 60 : face_x + 76] = 30
    frames = []
    boxes = []
    for index in range(count):
        page = wall.copy()
        if index in talking:
            depth = 8 if index % 2 == 0 else 20
            page[face_y + 66 : face_y + 66 + depth, face_x + 30 : face_x + 66] = 20
        left = step * index
        view = page[:, left : left + WIDTH]
        frames.append(np.repeat(view[:, :, None], 3, axis=2).copy())
        boxes.append((face_x - left, face_y, face_w, face_h))
    _write_clip(path, frames, lossless=True)
    return boxes


def _mouth_clip(path: Path, moving: range) -> None:
    x1, y1, x2, y2 = MOUTH_BOX
    frames = []
    for index in range(16):
        frame = np.full((HEIGHT, WIDTH, 3), 18, np.uint8)
        if index in moving:
            frame[y1:y2, x1:x2] = (40 + index * 25) % 250
        frames.append(frame)
    _write_clip(path, frames)


def _rgb_frames(path: Path) -> list[np.ndarray]:
    raw = subprocess.check_output(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    )
    frame_bytes = WIDTH * HEIGHT * 3
    count = len(raw) // frame_bytes
    return [
        np.frombuffer(raw[index * frame_bytes : (index + 1) * frame_bytes], dtype=np.uint8).reshape(HEIGHT, WIDTH, 3).copy()
        for index in range(count)
    ]


def _mouth_diff(left: np.ndarray, right: np.ndarray) -> float:
    x1, y1, x2, y2 = MOUTH_BOX
    return float(np.abs(left[y1:y2, x1:x2].astype(np.int16) - right[y1:y2, x1:x2].astype(np.int16)).mean())
