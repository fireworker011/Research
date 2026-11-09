"""各エピソードの音声の長さを出す。75秒との差も書く。

--dummy-tts は build_audio と同じ見積もり（尺は埋めない）。
--timing に VOICEVOX などが書いた audio_timing.json を渡すと、その実測も出す。
エンジンが止まっているときは voicevox を unavailable と書く。合成はしない。
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import build_audio


def voicevox_up(url: str) -> bool:
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/version", timeout=2) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def dummy_seconds(job: dict) -> float:
    units = build_audio.speech_units(job)
    lengths = [build_audio.estimate_speech_sec(unit["text"]) for unit in units]
    _items, total = build_audio.timeline(units, lengths)
    return total


def gap(seconds: float) -> str:
    if seconds < 75.0:
        return f"short_of_75={75.0 - seconds:.2f}s"
    if seconds > 95.0:
        return f"over_95={seconds - 95.0:.2f}s"
    return "within_75_95"


def main() -> int:
    parser = argparse.ArgumentParser(description="エピソードの音声長を測る")
    parser.add_argument("jobs", nargs="+")
    parser.add_argument("--dummy-tts", action="store_true", help="見積もりを出す（既定でも出す）")
    parser.add_argument("--timing", help="実測の audio_timing.json。1ジョブのときだけ使う")
    parser.add_argument("--voicevox-url", default="http://127.0.0.1:50021")
    args = parser.parse_args()
    if args.timing and len(args.jobs) != 1:
        raise SystemExit("--timing はジョブを1つだけ指定したときに使ってください")
    engine = voicevox_up(args.voicevox_url)
    for job_path in args.jobs:
        path = Path(job_path)
        job = json.loads(path.read_text(encoding="utf-8"))
        estimated = dummy_seconds(job)
        print(f"{path.name} job={job.get('job_id')}")
        print(f"  dummy-tts: {estimated:.2f}s  {gap(estimated)}")
        if args.timing:
            timing = json.loads(Path(args.timing).read_text(encoding="utf-8"))
            measured = float(timing["duration_sec"])
            source = "dummy-tts" if timing.get("dummy_tts") else "voicevox"
            print(f"  timing[{source}]: {measured:.2f}s  {gap(measured)}")
        elif engine:
            print("  voicevox: engine is up; pass --timing after build_audio.py")
        else:
            print("  voicevox: unavailable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
