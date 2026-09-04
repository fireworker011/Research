#!/usr/bin/env python3
"""Emit a MiniMax H3 LoRA stack for one h3-lora-studio profile.

Loads only catalog entries listed in the profile's `enabled` list.
Everything else (including Turbo / Acc / ref2va-on-I2V) is listed for unload.

This script never reads `.env` and never prints API keys.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog" / "loras.json"
PROFILES_DIR = ROOT / "profiles"
SCHEMA = "h3-lora-studio/v1"
MODES = ("t2v", "i2v", "r2v")
SCENE_ALIASES = {"", "シーン", "（シーン）", "(シーン)", "scene"}
SECRET_KEY_RE = re.compile(
    r"(api[_-]?key|secret|token|password|authorization|hf_token|xai)",
    re.I,
)
LIVE_SECRET_RE = re.compile(
    r"\b(sk-[A-Za-z0-9_-]{8,}|hf_[A-Za-z0-9]{8,}|xai-[A-Za-z0-9_-]{8,})\b"
)
FORBIDDEN_SUBJECT_RE = re.compile(
    r"(shota|syota|loli|lolita|\bchild\b|\bchildren\b|\bkids?\b|toddler|"
    r"infant|\bminor\b|underage|\bteen\b|teenage|schoolgirl|"
    r"小学生|中学生| pedo|loliita)",
    re.I,
)
TURBO_NAME_RE = re.compile(r"(turbo|\bacc[-_]?lora|\b4step\b|\b8step\b)", re.I)


class SelectError(SystemExit):
    pass


def load_json(path: Path) -> Any:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SelectError(f"{path} must be a JSON object")
    return data


def catalog_index(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = catalog.get("loras")
    if not isinstance(rows, list) or not rows:
        raise SelectError("catalog.loras must be a non-empty list")
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not row.get("id"):
            raise SelectError("each catalog LoRA needs an id")
        lid = str(row["id"])
        if lid in out:
            raise SelectError(f"duplicate catalog id: {lid}")
        out[lid] = row
    return out


def load_profile(name: str, profiles_dir: Path = PROFILES_DIR) -> dict[str, Any]:
    path = profiles_dir / f"{name}.json"
    if not path.is_file():
        raise SelectError(f"unknown profile: {name}")
    profile = load_json(path)
    if str(profile.get("id") or "") != name:
        raise SelectError(f"profile id mismatch in {path}")
    return profile


def is_turbo_row(row: dict[str, Any]) -> bool:
    if row.get("turbo") is True:
        return True
    blob = " ".join(
        str(row.get(k) or "")
        for k in ("id", "filename", "repo", "file", "arch")
    )
    return bool(TURBO_NAME_RE.search(blob))


def forbidden_hits(text: str) -> list[str]:
    return sorted({m.group(0).lower() for m in FORBIDDEN_SUBJECT_RE.finditer(text)})


def resolve_prompt(profile: dict[str, Any], prompt_arg: str | None) -> str:
    raw = "" if prompt_arg is None else str(prompt_arg).strip()
    if raw in SCENE_ALIASES:
        scene = str(profile.get("scene") or "").strip()
        if not scene:
            raise SelectError("profile.scene is empty")
        return scene
    return raw


def enabled_specs(profile: dict[str, Any]) -> list[dict[str, Any]]:
    rows = profile.get("enabled")
    if not isinstance(rows, list) or not rows:
        raise SelectError("profile.enabled must be a non-empty list")
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if isinstance(row, str):
            row = {"id": row}
        if not isinstance(row, dict) or not row.get("id"):
            raise SelectError("enabled entries need an id")
        lid = str(row["id"])
        if lid in seen:
            raise SelectError(f"duplicate enabled id: {lid}")
        seen.add(lid)
        out.append(row)
    return out


def assert_adults_only(profile: dict[str, Any]) -> None:
    if profile.get("adults_only") is not True:
        raise SelectError("adults_only must be true")
    min_age = int(profile.get("min_age") or 0)
    if min_age < 18:
        raise SelectError("min_age must be >= 18")


def assert_no_secrets(payload: dict[str, Any]) -> None:
    dumped = json.dumps(payload, ensure_ascii=False)
    if LIVE_SECRET_RE.search(dumped):
        raise SelectError("refusing to emit a live-looking API key")
    if SECRET_KEY_RE.search(dumped):
        raise SelectError("refusing to emit secret-like keys; keep them in .env")


def comfy_lora_nodes(stack: list[dict[str, Any]], *, model_node: str = "1") -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    prev = model_node
    for i, item in enumerate(stack, start=1):
        nid = str(200 + i)
        nodes.append(
            {
                "id": nid,
                "class_type": "LoraLoaderModelOnly",
                "inputs": {
                    "model": [prev, 0],
                    "lora_name": item["filename"],
                    "strength_model": float(item["strength_model"]),
                },
            }
        )
        prev = nid
    return nodes


def select_loras(
    *,
    profile_name: str,
    mode: str,
    prompt_arg: str | None = "（シーン）",
    catalog_path: Path = CATALOG_PATH,
    profiles_dir: Path = PROFILES_DIR,
    turbo_override: bool | None = False,
) -> dict[str, Any]:
    mode = str(mode).lower().strip()
    if mode not in MODES:
        raise SelectError(f"mode must be one of {MODES}")

    profile = load_profile(profile_name, profiles_dir)
    assert_adults_only(profile)
    turbo = bool(profile.get("turbo")) if turbo_override is None else bool(turbo_override)
    if turbo:
        raise SelectError("Turbo must stay off for this studio profile")

    prompt = resolve_prompt(profile, prompt_arg)
    hits = forbidden_hits(prompt)
    if hits:
        raise SelectError(f"forbidden subject in prompt: {hits}")

    index = catalog_index(load_json(catalog_path))
    disabled_ids = {str(x) for x in (profile.get("disabled") or [])}
    enabled = enabled_specs(profile)

    stack: list[dict[str, Any]] = []
    for spec in enabled:
        lid = str(spec["id"])
        if lid in disabled_ids:
            raise SelectError(f"{lid} is both enabled and disabled")
        row = index.get(lid)
        if row is None:
            raise SelectError(f"enabled id not in catalog: {lid}")
        if is_turbo_row(row):
            raise SelectError(f"refusing turbo LoRA in stack: {lid}")
        modes = [str(m) for m in (row.get("modes") or [])]
        if mode not in modes:
            raise SelectError(f"{lid} does not support mode {mode}")
        arch = str(row.get("arch") or "")
        if mode in {"t2v", "i2v"} and arch == "ref2va":
            raise SelectError(f"ref2va LoRA cannot stack on {mode}: {lid}")
        blob = json.dumps(row, ensure_ascii=False)
        bad = forbidden_hits(blob)
        if bad:
            raise SelectError(f"forbidden subject in catalog {lid}: {bad}")
        strength = spec.get("strength", row.get("default_strength", 1.0))
        trigger = str(row.get("trigger") or "").strip()
        stack.append(
            {
                "id": lid,
                "filename": str(row["filename"]),
                "repo": str(row.get("repo") or ""),
                "file": str(row.get("file") or row["filename"]),
                "arch": arch or "fl2va",
                "strength_model": float(strength),
                "trigger": trigger,
                "adult": bool(row.get("adult")),
            }
        )

    enabled_ids = {item["id"] for item in stack}
    unload: list[dict[str, Any]] = []
    for lid, row in index.items():
        if lid in enabled_ids:
            continue
        reasons: list[str] = []
        if lid in disabled_ids:
            reasons.append("profile_disabled")
        if is_turbo_row(row):
            reasons.append("turbo_off")
        if mode in {"t2v", "i2v"} and str(row.get("arch") or "") == "ref2va":
            reasons.append("ref2va_not_for_i2v")
        if mode not in [str(m) for m in (row.get("modes") or [])]:
            reasons.append("wrong_mode")
        if not reasons:
            reasons.append("not_enabled")
        unload.append(
            {
                "id": lid,
                "filename": str(row.get("filename") or ""),
                "reason": "+".join(reasons),
                "action": "unload",
            }
        )

    nodes = comfy_lora_nodes(stack)
    model_out = nodes[-1]["id"] if nodes else "1"
    canvas = profile.get("canvas") if isinstance(profile.get("canvas"), dict) else {}
    payload = {
        "schema": SCHEMA,
        "profile": profile_name,
        "mode": mode,
        "adults_only": True,
        "min_age": int(profile.get("min_age") or 21),
        "turbo": False,
        "prompt": prompt,
        "negative": str(profile.get("negative") or ""),
        "first_frame_required": mode == "i2v",
        "canvas": {
            "width": int(canvas.get("width") or 768),
            "height": int(canvas.get("height") or 864),
            "duration_s": float(canvas.get("duration_s") or 10.0),
            "aspect": str(canvas.get("aspect") or "8:9"),
        },
        "sampler": {
            "sampler_name": "res_multistep",
            "scheduler": "beta",
            "steps": 16,
            "cfg": 4.0,
            "denoise": 1.0,
            "note": "Turbo is off. Do not switch to euler/simple/4-step even if LoRAs are stacked.",
        },
        "stack": stack,
        "unload": unload,
        "comfy": {
            "lora_nodes": nodes,
            "model_out": [model_out, 0] if nodes else ["1", 0],
            "do_not_load": [u["filename"] for u in unload if u.get("filename")],
        },
    }
    assert_no_secrets(payload)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--profile", required=True)
    p.add_argument("--mode", required=True, choices=MODES)
    p.add_argument("--prompt", default="（シーン）", help="Use シーン to take profile.scene")
    p.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    p.add_argument("--profiles-dir", type=Path, default=PROFILES_DIR)
    p.add_argument("--out", type=Path, default=None)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = select_loras(
        profile_name=args.profile,
        mode=args.mode,
        prompt_arg=args.prompt,
        catalog_path=args.catalog,
        profiles_dir=args.profiles_dir,
        turbo_override=False,
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    sys.stdout.write(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
