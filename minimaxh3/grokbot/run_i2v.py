#!/usr/bin/env python3
"""Grokbot I2VA: Imagine 2.0 → Colab 10s I2VA → stop."""

from __future__ import annotations

from engine import run as _run


def run(argv: list[str] | None = None) -> int:
    return _run(argv, default_mode="i2v", default_session="h3-i2v")


if __name__ == "__main__":
    raise SystemExit(run())
