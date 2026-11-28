"""segments を各2秒にした仮の audio_timing.json を作る。

choice_card / day_end_card も 2秒。promo_outro は有効なとき、
steps の duration_sec 合計（無ければ 2秒）を1区間にする。
このファイルは描画の煙テスト用で、60〜70秒の尺ゲートには使わない。
--silence を付けると、同じ長さの無音WAVも書く。
"""

from __future__ import annotations

import argparse
import json
import wave
from pathlib import Path

SR = 24000
SEGMENT_SEC = 2.0


def _units(job: dict) -> list[dict]:
    units = []
    for seg in job["segments"]:
        units.append(
            {
                "kind": "segment",
                "segment_id": seg["id"],
                "scene": seg.get("scene"),
                "text": seg.get("subtitle") or "",
                "se": seg.get("se"),
                "duration": SEGMENT_SEC,
                "pause_after_ms": 0,
            }
        )
    choice = job.get("choice_card") or {}
    units.append(
        {
            "kind": "choice_card",
            "segment_id": None,
            "scene": "choice_card",
            "text": choice.get("narration") or "",
            "se": None,
            "duration": SEGMENT_SEC,
            "pause_after_ms": 0,
        }
    )
    day_end = job.get("day_end_card") or {}
    units.append(
        {
            "kind": "day_end_card",
            "segment_id": None,
            "scene": "day_end_card",
            "text": day_end.get("narration") or "",
            "se": None,
            "duration": SEGMENT_SEC,
            "pause_after_ms": 0,
        }
    )
    promo = job.get("promo_outro") or {}
    if promo.get("enabled"):
        steps = promo.get("steps") or []
        dur = sum(float(step.get("duration_sec") or 0) for step in steps) or SEGMENT_SEC
        units.append(
            {
                "kind": "promo_outro",
                "segment_id": None,
                "scene": "promo_outro",
                "text": promo.get("narration") or "",
                "se": None,
                "duration": dur,
                "pause_after_ms": 0,
            }
        )
    return units


def build_timing(job: dict) -> dict:
    items = []
    cursor = 0.0
    for index, unit in enumerate(_units(job), start=1):
        start = cursor
        end = cursor + float(unit["duration"])
        items.append(
            {
                "index": index,
                "kind": unit["kind"],
                "segment_id": unit["segment_id"],
                "scene": unit["scene"],
                "text": unit["text"],
                "wav": f"seg_{index:02d}.wav",
                "se": unit["se"],
                "audio_sec": round(float(unit["duration"]), 4),
                "pause_after_ms": 0,
                "pad_sec": 0.0,
                "start_sec": round(start, 4),
                "end_sec": round(end, 4),
            }
        )
        cursor = end
    return {
        "job_id": job["job_id"],
        "generator": "make_dummy_timing",
        "segment_sec": SEGMENT_SEC,
        "sample_rate": SR,
        "duration_sec": round(cursor, 4),
        "items": items,
    }


def write_silence(path: Path, seconds: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = max(1, int(round(seconds * SR)))
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        chunk = b"\x00\x00\x00\x00" * SR
        full, rem = divmod(frames, SR)
        for _ in range(full):
            handle.writeframes(chunk)
        if rem:
            handle.writeframes(b"\x00\x00\x00\x00" * rem)


def main() -> None:
    parser = argparse.ArgumentParser(description="各セグメント2秒の仮タイミングを書く")
    parser.add_argument("--job", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--silence", help="同じ長さの無音WAVの出力先")
    args = parser.parse_args()
    job = json.loads(Path(args.job).read_text(encoding="utf-8"))
    timing = build_timing(job)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(timing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} duration={timing['duration_sec']:.3f}s items={len(timing['items'])}")
    if args.silence:
        write_silence(Path(args.silence), float(timing["duration_sec"]))
        print(f"wrote {args.silence}")


if __name__ == "__main__":
    main()
