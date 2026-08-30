"""fal MiniMax H3 Max I2V. Fast hosted path; key from env, never git.

Playground https://fal.ai/tools/minimax-h3-max is 5×5s/day, no login — humans only.
Grokbot uses the official API (10s homage). Do not scrape the free page.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

from h3_imagine import data_uri, download_to, secret_value

ENDPOINT = "https://fal.run/minimax/h3-max/image-to-video"
MODEL_ID = "minimax/h3-max/image-to-video"


def fal_api_key() -> str:
    key = secret_value("FAL_KEY", "FAL_API_KEY")
    if not key:
        raise RuntimeError(
            "FAL_KEY がありません。H3 Max は fal API です。"
            "スマホ Colab なら左の鍵アイコン → FAL_KEY。"
            "無料ページ（ログインなし5本/5秒）は手試し専用。Git にキーを書かない。"
        )
    return key


def i2v_payload(
    *,
    prompt: str,
    image_path: Path,
    duration_s: int = 10,
    resolution: str = "768P",
    seed: int | None = 42,
    prompt_expansion_mode: str = "disabled",
) -> dict[str, Any]:
    dur = max(5, min(15, int(duration_s)))
    body: dict[str, Any] = {
        "prompt": prompt,
        "duration": dur,
        "resolution": resolution,
        "prompt_expansion_mode": prompt_expansion_mode,
        "enable_safety_checker": True,
        "image_url": data_uri(image_path),
    }
    if seed is not None:
        body["seed"] = int(seed)
    return body


def parse_video_url(body: dict[str, Any]) -> str:
    video = body.get("video") or {}
    if isinstance(video, dict) and video.get("url"):
        return str(video["url"])
    if body.get("url") and str(body["url"]).endswith(".mp4"):
        return str(body["url"])
    raise ValueError("fal H3 Max response had no video url")


def post_fal(payload: dict[str, Any], key: str, opener: Callable[..., Any] | None = None) -> dict[str, Any]:
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Key {key}",
        },
        method="POST",
    )
    open_fn = opener or urllib.request.urlopen
    try:
        with open_fn(req, timeout=300) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:2000]
        raise RuntimeError(f"fal H3 Max HTTP {e.code}: {detail}") from e


def generate_i2v(
    image_path: Path,
    dest_mp4: Path,
    *,
    prompt: str,
    duration_s: int = 10,
    resolution: str = "768P",
    seed: int | None = 42,
    prompt_expansion_mode: str = "disabled",
    key: str | None = None,
    opener: Callable[..., Any] | None = None,
) -> Path:
    token = key if key is not None else fal_api_key()
    payload = i2v_payload(
        prompt=prompt,
        image_path=image_path,
        duration_s=duration_s,
        resolution=resolution,
        seed=seed,
        prompt_expansion_mode=prompt_expansion_mode,
    )
    body = post_fal(payload, token, opener=opener)
    url = parse_video_url(body)
    return download_to(url, dest_mp4)


def is_fal_backend(name: str | None) -> bool:
    n = (name or "").strip().lower()
    return n in ("fal-max", "fal", "h3-max", "max")


def is_colab_backend(name: str | None) -> bool:
    n = (name or "").strip().lower()
    return n in ("colab", "comfy", "comfyui", "local")


def resolve_backend(args_backend: str | None = None, job: dict[str, Any] | None = None) -> str:
    """CLI > job.json > H3_BACKEND > fal-max. Colab is fallback, not default."""
    raw = (args_backend or "").strip()
    if raw:
        return raw
    raw = str((job or {}).get("backend") or "").strip()
    if raw:
        return raw
    return (os.environ.get("H3_BACKEND") or "fal-max").strip() or "fal-max"


def payload_log(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    url = str(out.get("image_url") or "")
    if url.startswith("data:"):
        out["image_url"] = f"data-uri:{len(url)}chars"
    return out
