"""Source audio must be absent once narration is mixed in."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from finish_with_narration import (  # noqa: E402
    SR,
    audio_stream_count,
    dominant_freq,
    extract_muted_picture,
    mix_voice_and_bgm,
    mux,
    run,
    write_bed,
    write_wav,
)


def _tone(path: Path, freq: float, seconds: float = 2.0) -> None:
    t = np.arange(int(SR * seconds)) / SR
    write_wav(path, (0.4 * np.sin(2 * np.pi * freq * t)).astype(np.float32), SR)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        source_tone = work / "source-tone.wav"
        narration = work / "narration.wav"
        bed = work / "bed.wav"
        picture_with_voice = work / "imagine.mp4"
        muted = work / "muted.mp4"
        mix = work / "mix.wav"
        final = work / "final.mp4"
        _tone(source_tone, 440.0)
        _tone(narration, 880.0)
        write_bed(bed, 2.0, "night_pad")
        run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=0x224466:s=1080x1920:r=30:d=2",
                "-i",
                str(source_tone),
                "-shortest",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                str(picture_with_voice),
            ]
        )
        if audio_stream_count(picture_with_voice) != 1:
            raise SystemExit("fixture should contain the Imagine voice")
        extract_muted_picture(picture_with_voice, muted, fps=30)
        if audio_stream_count(muted) != 0:
            raise SystemExit("muted picture still has the source voice")
        mix_voice_and_bgm(narration, bed, mix, 2.0)
        mux(muted, mix, final)
        if audio_stream_count(final) != 1:
            raise SystemExit("final should have one narration mix, not the source")
        freq = dominant_freq(final)
        if abs(freq - 880.0) > 30:
            raise SystemExit(f"narration tone missing, dominant {freq:.1f} Hz")
        if abs(freq - 440.0) < 20:
            raise SystemExit("source 440 Hz voice is still in the mix")
    print("ok source audio discarded when narration is added")


if __name__ == "__main__":
    main()
