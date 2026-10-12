"""Time a module forward without hiding the parameter names.

diffusers' MiniMax-H3 denoiser keeps only the kwargs whose names appear on
``inspect.signature(transformer.forward)``. A bare ``*args, **kwargs`` wrapper
drops ``token_tags``, ``position_ids``, ``video_indices``, ``audio_indices``
and ``text_indices``, and the real forward then refuses to start.
"""

from __future__ import annotations

import functools
import time
from collections.abc import Callable


def attach_forward_timer(module, totals: dict[str, float], key: str, sync: Callable[[], None]) -> None:
    original = module.forward

    @functools.wraps(original)
    def wrapped(*args, **kwargs):
        sync()
        start = time.perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            sync()
            totals[key] += time.perf_counter() - start

    module.forward = wrapped
