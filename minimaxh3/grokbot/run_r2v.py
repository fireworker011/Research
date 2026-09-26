#!/usr/bin/env python3
"""Grokbot R2V: still + motion mp4 → Colab 10s ReferenceToVideo → stop."""

from __future__ import annotations

from engine import run as _run


def run(argv: list[str] | None = None) -> int:
    return _run(argv, default_mode="r2v", default_session="h3-r2v")


if __name__ == "__main__":
    raise SystemExit(run())
