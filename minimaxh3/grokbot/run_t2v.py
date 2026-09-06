#!/usr/bin/env python3
"""Grokbot T2V: prompt → Colab 10s T2V → stop. No still. No Imagine."""

from __future__ import annotations

from engine import run as _run


def run(argv: list[str] | None = None) -> int:
    return _run(argv, default_mode="t2v", default_session="h3-t2v")


if __name__ == "__main__":
    raise SystemExit(run())
