"""Speaker turns for one wav file.

Run only with ``PYTHONPATH`` set to the folder ``affi_media.speaker_install_argv``
writes. That folder has its own CPU torch, so the torch H3 uses is not replaced.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from pyannote.audio import Pipeline


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print("usage: affi_speaker.py WAV OUT.json MODEL", file=sys.stderr)
        return 2
    wav, out, model = Path(argv[1]), Path(argv[2]), argv[3]
    token = os.environ.get("HF_TOKEN") or None
    gate = "このトークンのアカウントでは読めない。同意したアカウントの Read トークンを欄に貼る。"
    try:
        pipeline = Pipeline.from_pretrained(model, use_auth_token=token)
    except Exception as exc:
        print(type(exc).__name__, file=sys.stderr)
        print(gate, file=sys.stderr)
        return 1
    if pipeline is None:
        print(gate, file=sys.stderr)
        return 1
    result = pipeline(str(wav))
    turns = [
        {"start_s": float(segment.start), "end_s": float(segment.end), "speaker": str(label)}
        for segment, _track, label in result.itertracks(yield_label=True)
    ]
    out.write_text(json.dumps(turns, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
