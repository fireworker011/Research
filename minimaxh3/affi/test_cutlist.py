"""CPU checks for cut-list-ffmpeg. Does not render the Orbis production mp4."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from minimaxh3.affi.cutlist import render_cutlist, write_cuts  # noqa: E402


def test_empty_subtitle_exits_1_without_mp4(tmp_path: Path) -> None:
    png = tmp_path / "a.png"
    _png(png, "red")
    csv_path = tmp_path / "cuts.csv"
    write_cuts(csv_path, [{"index": 1, "src": png.name, "in": 0, "out": 0.5, "subtitle": "  "}])
    out = tmp_path / "final.mp4"
    code = render_cutlist(csv_path, out, "slide")
    assert code == 1
    assert not out.exists()
    assert not list(tmp_path.glob("*.partial"))


def test_conversation_filler_is_refused(tmp_path: Path) -> None:
    png = tmp_path / "a.png"
    _png(png, "blue")
    csv_path = tmp_path / "cuts.csv"
    write_cuts(csv_path, [{"index": 1, "src": png.name, "in": 0, "out": 0.5, "subtitle": "残す"}])
    out = tmp_path / "final.mp4"
    assert render_cutlist(csv_path, out, "filler") == 2
    assert not out.exists()


def test_stills_are_1080x1920_at_30fps(tmp_path: Path, capsys) -> None:
    _png(tmp_path / "a.png", "0x336699")
    _png(tmp_path / "b.png", "0x993333")
    csv_path = tmp_path / "cuts.csv"
    write_cuts(
        csv_path,
        [
            {"index": 1, "src": "a.png", "in": 0, "out": 0.5, "subtitle": "一行目 / 二行目"},
            {"index": 2, "src": "b.png", "in": 0, "out": 0.5, "subtitle": "次"},
        ],
    )
    out = tmp_path / "final.mp4"
    code = render_cutlist(csv_path, out, "slide")
    assert code == 0
    assert out.is_file()
    printed = capsys.readouterr().out
    assert str(out.resolve()) in printed
    assert str(csv_path.resolve()) in printed
    probe = _probe(out)
    assert probe["width"] == 1080
    assert probe["height"] == 1920
    assert probe["r_frame_rate"] == "30/1"


def _png(path: Path, color: str) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", f"color=c={color}:s=64x64",
            "-frames:v", "1", str(path),
        ],
        check=True,
    )


def _probe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate",
            "-of", "json", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)["streams"][0]
