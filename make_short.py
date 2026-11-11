#!/usr/bin/env python3
"""台本から短い縦動画を作る。処理本体は video/shorts/make_short.py。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from video.shorts.make_short import main

if __name__ == "__main__":
    sys.exit(main())
