"""Small Pillow helpers."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


def has_alpha(path: Path) -> bool:
    """True when the image really has transparent pixels, not only an alpha channel."""
    with Image.open(path) as image:
        if image.mode in ("RGBA", "LA"):
            low, _high = image.getchannel("A").getextrema()
            return low < 255
        return "transparency" in image.info
