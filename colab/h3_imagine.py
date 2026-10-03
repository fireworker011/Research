"""Grok Imagine Image 2.0 quality pass. Key comes from env, never from git."""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

EDIT_URL = "https://api.x.ai/v1/images/edits"
GENERATE_URL = "https://api.x.ai/v1/images/generations"
DEFAULT_MODEL = "grok-imagine-image-2.0"


def imagine_api_key() -> str:
    key = (os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("XAI_API_KEY がありません。Imagine 2.0 はキーが必要です。Git には書かない。")
    return key


def data_uri(path: Path) -> str:
    raw = Path(path).read_bytes()
    suffix = Path(path).suffix.lower()
    mime = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(
        suffix, "image/jpeg"
    )
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def edit_payload(
    *,
    prompt: str,
    image_path: Path,
    model: str = DEFAULT_MODEL,
    quality: str = "medium",
    resolution: str = "2k",
    aspect_ratio: str = "3:4",
) -> dict[str, Any]:
    return {
        "model": model,
        "prompt": prompt,
        "quality": quality,
        "resolution": resolution,
        "aspect_ratio": aspect_ratio,
        "response_format": "url",
        "image": {"url": data_uri(image_path), "type": "image_url"},
    }


def parse_image_url(body: dict[str, Any]) -> str:
    if body.get("url"):
        return str(body["url"])
    data = body.get("data")
    if isinstance(data, list) and data:
        url = data[0].get("url")
        if url:
            return str(url)
        b64 = data[0].get("b64_json")
        if b64:
            return "data:image/jpeg;base64," + str(b64)
    raise ValueError("Imagine response had no image url")


def post_json(url: str, payload: dict[str, Any], key: str, opener: Callable[..., Any] | None = None) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    open_fn = opener or urllib.request.urlopen
    try:
        with open_fn(req, timeout=180) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:2000]
        raise RuntimeError(f"Imagine HTTP {e.code}: {detail}") from e


def download_to(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if url.startswith("data:"):
        _, b64 = url.split(",", 1)
        dest.write_bytes(base64.b64decode(b64))
        return dest
    urllib.request.urlretrieve(url, dest)
    if not dest.is_file() or dest.stat().st_size < 1000:
        raise RuntimeError("Imagine download too small")
    return dest


def enhance_still(
    src: Path,
    dest: Path,
    *,
    prompt: str,
    model: str = DEFAULT_MODEL,
    quality: str = "medium",
    resolution: str = "2k",
    aspect_ratio: str = "3:4",
    key: str | None = None,
    opener: Callable[..., Any] | None = None,
) -> Path:
    token = key if key is not None else imagine_api_key()
    payload = edit_payload(
        prompt=prompt,
        image_path=src,
        model=model,
        quality=quality,
        resolution=resolution,
        aspect_ratio=aspect_ratio,
    )
    body = post_json(EDIT_URL, payload, token, opener=opener)
    url = parse_image_url(body)
    return download_to(url, dest)
