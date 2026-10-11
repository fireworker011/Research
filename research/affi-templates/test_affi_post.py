"""After the picture: voice, mouth, captions, and an own music file. No H3 render."""

from __future__ import annotations

import copy
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
    )
    assert result["status"] == "blocked"
    assert result["blocked"] == ["絵から口の開閉が測れない: c1"]
    assert result["posts"] is False
    assert spoken == []
    assert not (tmp_path / "post.mp4").exists()


@needs_espeak
def test_espeak_writes_a_distinct_guest_voice(tmp_path: Path) -> None:
    dest = tmp_path / "dog.wav"
    affi_post.synth_edge("本日は検品を休業しております", "guest", dest, voice="espeak:ja")
    assert dest.stat().st_size > 1000


def _write_clip(path: Path, frames: list[np.ndarray]) -> None:
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
