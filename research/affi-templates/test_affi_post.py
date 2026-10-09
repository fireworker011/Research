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
WIDTH = 288
HEIGHT = 512
FPS = 8
FACE = (80, 110, 208, 300)


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


def test_mouth_opens_only_the_lower_face() -> None:
    frame = np.zeros((80, 40, 3), np.uint8)
    frame[44:, :, 0] = np.arange(36, dtype=np.uint8)[:, None]
    assert affi_post._open_mouth(frame, (0, 0, 40, 80), 0.0) is frame
    opened = affi_post._open_mouth(frame, (0, 0, 40, 80), 0.45)
    split = int(80 * affi_post.MOUTH_SPLIT)
    assert np.array_equal(opened[:split], frame[:split])
    assert not np.array_equal(opened[split:], frame[split:])


def test_a_missing_picture_or_music_file_blocks(tmp_path: Path) -> None:
    missing = affi_post.apply(tmp_path / "none.mp4", tmp_path / "post.mp4", rows=[])
    assert missing["status"] == "blocked"
    assert missing["blocked"] == ["つないだ動画が無い"]
    assert missing["generates_h3"] is False
    assert missing["posts"] is False


@needs_ffmpeg
def test_unfilled_lines_do_not_speak(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LIPSYNC_CMD", raising=False)
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
def test_voice_caption_music_and_mouth_follow_the_filled_line(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LIPSYNC_CMD", raising=False)
    video = tmp_path / "story.mp4"
    _pattern_clip(video, beep_at=0.2)
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
            {"id": "c1", "text": "HELLO", "start_s": 0.75, "end_s": 1.5, "burn": True, "role": "owner"},
        ],
        bgm=bgm,
        synth=synth,
        face_box=FACE,
    )
    assert result["status"] == "ready"
    assert result["generates_h3"] is False
    assert result["posts"] is False
    assert result["cues"] == 1
    assert result["mouth"]["method"] == "loudness"
    assert result["mouth"]["mouth_frames"] > 0
    assert spoken == ["HELLO"]
    assert out.is_file()
    assert video.read_bytes() != out.read_bytes()
    samples = affi_media._decode_mono(out, 16000)
    loud = np.flatnonzero(np.abs(samples) > 0.45)
    assert loud.size
    assert float(loud[0]) / 16000 == pytest.approx(0.75, abs=0.08)
    early = samples[: int(0.45 * 16000)]
    assert float(np.abs(early).max()) < 0.35
    assert float(np.abs(early).mean()) > 0.02
    after = _rgb_frames(out)
    quiet = _face_diff(before[1], after[1])
    opened = max(_face_diff(before[index], after[index]) for index in range(6, 12))
    assert quiet < 25
    assert opened > 60
    raw = subprocess.check_output(
        ["ffmpeg", "-v", "error", "-ss", "1.0", "-i", str(out), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    )
    frame = np.frombuffer(raw, dtype=np.uint8).reshape(HEIGHT, WIDTH)
    band = frame[HEIGHT - int(HEIGHT * 0.30) - 40 : HEIGHT - int(HEIGHT * 0.30) + 5]
    assert int(band.max()) > 200
    assert int(frame[:100].max()) < 40


@needs_ffmpeg
def test_an_external_command_keeps_the_picture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    video = tmp_path / "story.mp4"
    _pattern_clip(video)
    before = _rgb_frames(video)
    monkeypatch.setenv(
        "LIPSYNC_CMD",
        "ffmpeg -y -v error -i {video} -i {audio} -map 0:v:0 -map 1:a:0 -c:v copy -c:a pcm_s16le {out}",
    )

    def synth(text: str, role: str, dest: Path) -> None:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-f",
                "lavfi",
                "-i",
                "aevalsrc='sin(2*PI*440*t)':s=44100:d=0.4",
                "-ac",
                "2",
                str(dest),
            ],
            check=True,
        )

    out = tmp_path / "post.mp4"
    result = affi_post.apply(
        video,
        out,
        rows=[{"id": "c1", "text": "HELLO", "start_s": 0.75, "end_s": 1.4, "burn": True, "role": "guest"}],
        synth=synth,
        face_box=FACE,
    )
    assert result["status"] == "ready"
    assert result["mouth"]["method"] == "external"
    assert result["note"] == "口は外部のコマンドで合わせた。"
    assert result["posts"] is False
    after = _rgb_frames(out)
    assert _face_diff(before[8], after[8]) < 25


def _pattern_clip(path: Path, *, beep_at: float | None = None) -> None:
    frames = []
    x1, y1, x2, y2 = FACE
    split = y1 + int((y2 - y1) * affi_post.MOUTH_SPLIT)
    for _ in range(16):
        frame = np.full((HEIGHT, WIDTH, 3), 12, np.uint8)
        frame[y1:split, x1:x2] = 40
        for row in range(split, y2):
            frame[row, x1:x2] = 255 if ((row - split) // 4) % 2 == 0 else 0
        frames.append(frame)
    audio = "anullsrc=r=44100:cl=stereo:d=2"
    if beep_at is not None:
        audio = f"aevalsrc='0.8*sin(2*PI*1000*t)*between(t,{beep_at:.3f},{beep_at + 0.05:.3f})':s=44100:d=2"
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
            audio,
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


def _face_diff(left: np.ndarray, right: np.ndarray) -> float:
    x1, y1, x2, y2 = FACE
    split = y1 + int((y2 - y1) * affi_post.MOUTH_SPLIT)
    return float(np.abs(left[split:y2, x1:x2].astype(np.int16) - right[split:y2, x1:x2].astype(np.int16)).mean())
