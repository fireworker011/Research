#!/usr/bin/env python3
"""Emit a MiniMax H3 LoRA stack for one situation profile and mode.

Loads only catalog entries listed in that situation's enabled list for the mode.
Everything else (including Turbo / Acc / ref2va on FL2VA) is listed for unload.

T2V uses scenes.t2v and 9:16. I2V uses scenes.i2v and Picture 1. Never mix them.

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
SITUATIONS_SCHEMA = "h3-lora-studio-situations/v1"
MODES = ("t2v", "i2v", "r2v")
STACK_ROLES = ("act", "helper", "turbo", "cinema")
MAX_HELPERS = 2
MAX_CINEMA_NSFW = 0.6
MAX_CINEMA_SFW = 0.7
STILL_ONLY_IDS = {"photoreal-h3-still"}
FULL_STACK_IDS = {
    "anal-penetration-coachbate",
    "hmnsfw-aio-v25",
    "penis-lora-h3",
    "synth-pussy-h3",
}
SCENE_ALIASES = {"", "シーン", "（シーン）", "(シーン)", "scene"}
DEFAULT_CANVAS = {
    "t2v": {"width": 576, "height": 1024, "duration_s": 10.0, "aspect": "9:16"},
    "i2v": {"width": 768, "height": 864, "duration_s": 10.0, "aspect": "8:9"},
    "r2v": {"width": 768, "height": 864, "duration_s": 10.0, "aspect": "8:9"},
}
SECRET_KEY_RE = re.compile(
    r"(api[_-]?key|secret|token|password|authorization|hf_token|xai)",
    re.I,
)
LIVE_SECRET_RE = re.compile(
    r"\b(sk-[A-Za-z0-9_-]{8,}|hf_[A-Za-z0-9]{8,}|xai-[A-Za-z0-9_-]{8,})\b"
)
TURBO_NAME_RE = re.compile(r"(turbo|\bacc[-_]?lora|\b4step\b|\b8step\b)", re.I)
PICTURE1_RE = re.compile(r"Picture 1|first_frame", re.I)
FORBIDDEN_PATH = ROOT / "catalog" / "forbidden.json"
LOCKED_MINORS = (
    "shota",
    "syota",
    "loli",
    "lolita",
    "loliita",
    "child",
    "children",
    "kid",
    "kids",
    "toddler",
    "infant",
    "minor",
    "underage",
    "teen",
    "teenage",
    "teenager",
    "小学生",
    "中学生",
    "pedo",
)
LOCKED_COMMERCIAL = ("px.a8.net", "a8mat=")
DEFAULT_BOUNDARY = ("child", "children", "kid", "kids", "minor", "teen")
SAFETY_PREFIX = r"(?:no|not\s+a|not|without|avoid|exclude|never)"
_FULLWIDTH_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")
# Explicit ages under 21. "15 seconds" / "24fps" must not match.
UNDERAGE_YEARS_RE = re.compile(
    r"(?i)(?<!\d)(20|1[0-9]|[1-9])\s*(?:-?\s*years?\s*old|-?\s*year[- ]olds?|y\.?o\.?\b|yo\b|歳)"
)
UNDERAGE_AGE_EQ_RE = re.compile(r"(?i)\bage\s*[:=]?\s*(20|1[0-9]|[1-9])\b")
FEMININE_LOCK_MARK = "feminine_lock:"
FEMININE_LOCK_PROMPT = (
    "feminine_lock: Every visible person is an adult woman, clearly over 21. "
    "Soft feminine face, feminine body, feminine hips and breasts. "
    "No man. No male. No muscle. No masculine face. No masculine body. "
    "No muscular male physique. No muscle-bound body. No beard. No adam's apple. "
    "No broad male shoulders. The partner with a penis remains a woman, never a man."
)
FEMININE_NEGATIVE = (
    "man, male, male body, masculine, muscular man, muscular male, muscle-bound, "
    "bodybuilder, beard, mustache, adam's apple, male face, male torso, male chest, "
    "1boy, 男, 男性, 男体, 筋肉質の男, 男らしい顔, 男らしい体"
)
MALE_SUBJECT_RES = (
    (re.compile(r"(?i)\badult men\b"), "adult women, feminine bodies, not men"),
    (re.compile(r"(?i)\badult man\b"), "adult woman, feminine body, not a man"),
    (re.compile(r"(?i)(?<!not )(?<!never )(?<!no )\b(?:a|the) men\b"), "adult women"),
    (re.compile(r"(?i)(?<!not )(?<!never )(?<!no )\b(?:a|the) man\b"), "an adult woman"),
    (re.compile(r"(?i)\b1boys?\b"), "adult woman"),
    (re.compile(r"(?i)\bmuscular (?:man|male|men|male body)\b"), "soft feminine body"),
    (re.compile(r"(?i)\bmale character\b"), "adult woman"),
    (re.compile(r"(?i)\bthe male\b"), "the adult woman"),
    (re.compile(r"(?i)\bhis penis\b"), "her penis"),
    (re.compile(r"(?i)\bhis cock\b"), "her penis"),
    (re.compile(r"(?i)\ba man waits\b"), "an adult woman waits"),
    (re.compile(r"(?i)\blying on his back\b"), "lying on her back"),
    (re.compile(r"(?i)\brides him\b"), "rides her partner"),
    (re.compile(r"男性"), "成人女性"),
    (re.compile(r"マッチョ"), "柔らかい女体"),
)


class SelectError(SystemExit):
    pass


def _clean_terms(rows: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    if not isinstance(rows, list):
        return out
    for row in rows:
        term = str(row or "").strip()
        if not term:
            continue
        key = term.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(term)
    return out


def parse_extra_terms(text: str | None) -> list[str]:
    raw = str(text or "").replace("、", ",")
    return _clean_terms([p.strip() for p in raw.split(",")])


def load_forbidden(path: Path | str | None = None) -> dict[str, Any]:
    p = Path(path or FORBIDDEN_PATH)
    data: dict[str, Any] = {}
    if p.is_file():
        loaded = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            data = loaded
    minors = _clean_terms(list(LOCKED_MINORS) + list(data.get("minors") or []))
    extra = _clean_terms(data.get("extra") or [])
    commercial = _clean_terms(list(LOCKED_COMMERCIAL) + list(data.get("commercial") or []))
    boundary = {
        str(x).strip().lower()
        for x in (data.get("word_boundary") or DEFAULT_BOUNDARY)
        if str(x).strip()
    } or set(DEFAULT_BOUNDARY)
    min_age = 21
    try:
        min_age = max(21, int(data.get("min_age") or 21))
    except (TypeError, ValueError):
        min_age = 21
    return {
        "path": str(p),
        "minors": minors,
        "extra": extra,
        "commercial": commercial,
        "word_boundary": sorted(boundary),
        "min_age": min_age,
    }


def extra_terms(path: Path | str | None = None) -> list[str]:
    return list(load_forbidden(path)["extra"])


def _pattern_for(term: str, boundary: set[str]) -> str:
    escaped = re.escape(term)
    if term.lower() in boundary and re.fullmatch(r"[A-Za-z]+", term):
        return rf"\b{escaped}\b"
    return escaped


def _subject_re(minors: list[str], boundary: set[str]) -> re.Pattern[str]:
    parts = [_pattern_for(t, boundary) for t in minors if t]
    if not parts:
        parts = [_pattern_for(t, boundary) for t in LOCKED_MINORS]
    return re.compile("(" + "|".join(parts) + ")", re.I)


def _safety_re(minors: list[str]) -> re.Pattern[str]:
    body = "|".join(re.escape(t) for t in minors if t) or "child"
    grouped = rf"(?:{body})"
    return re.compile(
        rf"(?i)\b{SAFETY_PREFIX}\s+(?:a\s+)?{grouped}"
        rf"(?:\s*,\s*(?:no\s+|not\s+a\s+|not\s+)?{grouped})*"
    )


def underage_age_hits(text: str) -> list[str]:
    """Lock numeric ages under 21. JSON cannot turn this off."""
    folded = str(text or "").translate(_FULLWIDTH_DIGITS)
    hits: list[str] = []
    seen: set[str] = set()
    for rx in (UNDERAGE_YEARS_RE, UNDERAGE_AGE_EQ_RE):
        for match in rx.finditer(folded):
            n = int(match.group(1))
            if n < 1 or n >= 21:
                continue
            token = match.group(0).strip().lower()
            if token in seen:
                continue
            seen.add(token)
            hits.append(token)
    return hits


def forbidden_hits(
    text: str,
    *,
    negative: str | None = None,
    extra: list[str] | None = None,
    path: Path | str | None = None,
) -> list[str]:
    """Flag requested minors and extra banned strings. 'no child' is not a request."""
    cfg = load_forbidden(path)
    minors = list(cfg["minors"])
    extra_terms_ = _clean_terms(list(cfg["extra"]) + list(extra or []))
    boundary = set(cfg["word_boundary"])
    cleaned = str(text or "")
    neg = str(negative or "").strip()
    if neg:
        cleaned = cleaned.replace(neg, " ")
    cleaned = _safety_re(minors).sub(" ", cleaned)
    hits: set[str] = set()
    for match in _subject_re(minors, boundary).finditer(cleaned):
        hits.add(match.group(0).lower())
    hits.update(underage_age_hits(cleaned))
    low = cleaned.lower()
    for term in list(cfg.get("commercial") or LOCKED_COMMERCIAL) + extra_terms_:
        if term.lower() in low:
            hits.add(term.lower())
    return sorted(hits)


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


def always_unload_ids(catalog: dict[str, Any]) -> set[str]:
    rows = catalog.get("always_unload") or []
    if not isinstance(rows, list):
        raise SelectError("catalog.always_unload must be a list")
    return {str(x) for x in rows}


def load_profile(name: str, profiles_dir: Path = PROFILES_DIR) -> dict[str, Any]:
    path = profiles_dir / f"{name}.json"
    if not path.is_file():
        raise SelectError(f"unknown situation: {name}")
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


def profile_is_nsfw(profile: dict[str, Any]) -> bool:
    if "nsfw" in profile:
        return bool(profile.get("nsfw"))
    return True


def max_cinema(profile: dict[str, Any] | None = None, *, nsfw: bool | None = None) -> float:
    is_nsfw = profile_is_nsfw(profile) if profile is not None else bool(nsfw)
    return MAX_CINEMA_NSFW if is_nsfw else MAX_CINEMA_SFW


def turbo_family(row: dict[str, Any]) -> str:
    fam = str(row.get("turbo_family") or "").strip().lower()
    if fam:
        return fam
    blob = " ".join(str(row.get(k) or "") for k in ("id", "filename", "repo"))
    if "larry" in blob.lower():
        return "larry"
    if "lightx2v" in blob.lower() or "fl2v_turbo" in blob.lower() or "ref2v_turbo" in blob.lower():
        return "lightx2v"
    return "turbo"


def normalize_specs(rows: Any, *, where: str) -> list[dict[str, Any]]:
    if not isinstance(rows, list) or not rows:
        raise SelectError(f"{where} must be a non-empty list")
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if isinstance(row, str):
            row = {"id": row}
        if not isinstance(row, dict) or not row.get("id"):
            raise SelectError(f"{where} entries need an id")
        lid = str(row["id"])
        if lid in seen:
            raise SelectError(f"duplicate enabled id: {lid}")
        seen.add(lid)
        out.append(dict(row))
    return out


def plan_specs(profile: dict[str, Any], mode: str) -> list[dict[str, Any]] | None:
    plan = profile.get("stack_plan")
    if not isinstance(plan, dict) or not plan:
        return None
    chosen = plan.get(mode) if isinstance(plan.get(mode), dict) else plan
    if not isinstance(chosen, dict):
        return None
    if not any(role in chosen for role in STACK_ROLES):
        return None
    specs: list[dict[str, Any]] = []
    for role in STACK_ROLES:
        raw = chosen.get(role)
        if raw in (None, "", False):
            continue
        rows = raw if (role == "helper" and isinstance(raw, list)) else [raw]
        seen: set[str] = set()
        for item in rows:
            if isinstance(item, str):
                item = {"id": item}
            if not isinstance(item, dict) or not item.get("id"):
                raise SelectError(f"stack_plan.{role} needs an id")
            lid = str(item["id"])
            if lid in seen:
                raise SelectError(f"duplicate stack_plan.{role} id: {lid}")
            seen.add(lid)
            spec = dict(item)
            spec["role"] = role
            specs.append(spec)
    if not specs:
        raise SelectError(f"{profile.get('id')} stack_plan is empty")
    return specs


def enabled_specs(profile: dict[str, Any], mode: str) -> list[dict[str, Any]]:
    planned = plan_specs(profile, mode)
    if planned is not None:
        return planned
    rows = profile.get("enabled")
    if isinstance(rows, dict):
        if mode not in rows:
            raise SelectError(f"situation has no enabled LoRAs for mode {mode}")
        return normalize_specs(rows.get(mode), where=f"enabled.{mode}")
    return normalize_specs(rows, where="profile.enabled")


def default_sampler(profile: dict[str, Any], specs: list[dict[str, Any]]) -> dict[str, Any]:
    raw = profile.get("sampler")
    if isinstance(raw, dict) and raw.get("steps"):
        note = str(raw.get("note") or "")
        return {
            "sampler_name": str(raw.get("sampler_name") or "res_multistep"),
            "scheduler": str(raw.get("scheduler") or "beta"),
            "steps": int(raw.get("steps")),
            "cfg": float(raw.get("cfg") or 4.0),
            "denoise": float(raw.get("denoise") or 1.0),
            "note": note,
        }
    has_turbo = any(str(s.get("role")) == "turbo" for s in specs)
    if has_turbo:
        steps = 8 if any("larry" in str(s.get("id")) for s in specs) else 4
        return {
            "sampler_name": "euler",
            "scheduler": "simple",
            "steps": steps,
            "cfg": 4.0,
            "denoise": 1.0,
            "note": "Thin turbo. Larry and LightX2V stay mutually exclusive.",
        }
    return {
        "sampler_name": "res_multistep",
        "scheduler": "beta",
        "steps": 16,
        "cfg": 4.0,
        "denoise": 1.0,
        "note": "Quality path. Turbo off.",
    }


def assert_stack_budget(
    specs: list[dict[str, Any]],
    index: dict[str, dict[str, Any]],
    *,
    nsfw: bool = True,
) -> None:
    roles = [str(s.get("role") or "") for s in specs]
    helper_n = roles.count("helper")
    if helper_n > MAX_HELPERS:
        raise SelectError("at most two helper LoRAs")
    for role in STACK_ROLES:
        if role == "helper":
            continue
        if roles.count(role) > 1:
            raise SelectError(f"only one {role} LoRA is allowed")
    ids = {str(s["id"]) for s in specs}
    if STILL_ONLY_IDS & ids:
        raise SelectError("photoreal still is for keyframes, not the video body")
    if not nsfw:
        if "act" in roles or "helper" in roles:
            raise SelectError("SFW stack is turbo plus one quality LoRA only")
        if "turbo" not in roles:
            raise SelectError("SFW fast+quality needs one turbo LoRA")
        for spec in specs:
            row = index.get(str(spec["id"])) or {}
            if row.get("adult") is True:
                raise SelectError(f"SFW stack cannot load adult LoRA: {spec['id']}")
        non_turbo = [s for s in specs if s.get("role") != "turbo"]
        if len(non_turbo) > 1:
            raise SelectError("SFW quality is one cinematic LoRA, or none")
    else:
        if "act" not in roles:
            raise SelectError("adult stack needs one act LoRA")
        if helper_n and "cinema" in roles:
            raise SelectError("cinema replaces helper; do not stack both")
        if FULL_STACK_IDS <= ids:
            raise SelectError("refusing Anal + AIO + Penis + Synth full stack")
        non_turbo = [s for s in specs if s.get("role") != "turbo"]
        if len(non_turbo) > 3:
            raise SelectError("quality LoRAs are act + at most two helpers")
        if helper_n <= 1 and len(non_turbo) > 2:
            raise SelectError("quality LoRAs are act + optional helper or cinema only")
    families: set[str] = set()
    for spec in specs:
        row = index.get(str(spec["id"])) or {}
        if is_turbo_row(row) or spec.get("role") == "turbo":
            families.add(turbo_family(row) or turbo_family(spec))
    if "larry" in families and "lightx2v" in families:
        raise SelectError("do not stack Larry and LightX2V")
    if len(families) > 1:
        raise SelectError("only one turbo family at a time")
    act = next((s for s in specs if s.get("role") == "act"), None)
    cinema = next((s for s in specs if s.get("role") == "cinema"), None)
    turbo = next((s for s in specs if s.get("role") == "turbo"), None)
    cinema_cap = MAX_CINEMA_NSFW if nsfw else MAX_CINEMA_SFW
    if cinema is not None:
        strength = float(cinema.get("strength") or 0.4)
        if strength > cinema_cap:
            raise SelectError(f"cinema DY must stay at 0.4-{cinema_cap}")
        if act and str(act.get("id")) == "anal-penetration-coachbate":
            raise SelectError("cinema off for anal penetration")
    if turbo is not None and act and str(act.get("id")) == "anal-penetration-coachbate":
        raise SelectError("CoachBate anal penetration stays turbo off")


def strip_male_subjects(text: str) -> str:
    out = str(text or "")
    for rx, repl in MALE_SUBJECT_RES:
        out = rx.sub(repl, out)
    return out


def apply_feminine_lock(prompt: str, negative: str, profile: dict[str, Any]) -> tuple[str, str]:
    nsfw = profile_is_nsfw(profile)
    if not bool(profile.get("feminine_lock")) and not nsfw:
        return str(prompt or ""), str(negative or "")
    prompt = strip_male_subjects(prompt)
    low = prompt.lower()
    if FEMININE_LOCK_MARK not in low:
        prompt = prompt.rstrip() + "\n\n" + FEMININE_LOCK_PROMPT
    neg = str(negative or "").strip()
    extra = FEMININE_NEGATIVE
    if extra.lower() not in neg.lower():
        neg = (neg + ", " + extra).strip(", ")
    return prompt, neg


def resolve_prompt(profile: dict[str, Any], prompt_arg: str | None, mode: str) -> str:
    raw = "" if prompt_arg is None else str(prompt_arg).strip()
    if raw not in SCENE_ALIASES:
        return raw
    scenes = profile.get("scenes")
    if isinstance(scenes, dict):
        scene = str(scenes.get(mode) or "").strip()
        if scene:
            return scene
        if mode == "t2v":
            raise SelectError("t2v requires scenes.t2v; do not reuse the I2V Picture 1 prompt")
    scene = str(profile.get("scene") or "").strip()
    if mode == "t2v":
        raise SelectError("t2v requires scenes.t2v; do not reuse the I2V Picture 1 prompt")
    if not scene:
        raise SelectError("profile scene is empty")
    return scene


def resolve_canvas(profile: dict[str, Any], mode: str) -> dict[str, Any]:
    base = dict(DEFAULT_CANVAS[mode])
    canvas = profile.get("canvas")
    chosen: dict[str, Any]
    if isinstance(canvas, dict) and isinstance(canvas.get(mode), dict):
        chosen = canvas[mode]
    elif isinstance(canvas, dict) and "width" in canvas and mode != "t2v":
        chosen = canvas
    else:
        chosen = base
    out = dict(base)
    out["width"] = int(chosen.get("width") or base["width"])
    out["height"] = int(chosen.get("height") or base["height"])
    out["duration_s"] = float(chosen.get("duration_s") or base["duration_s"])
    out["aspect"] = str(chosen.get("aspect") or base["aspect"])
    return out


def assert_mode_prompt(mode: str, prompt: str) -> None:
    if mode == "t2v" and PICTURE1_RE.search(prompt):
        raise SelectError("t2v prompt must not use Picture 1 / first_frame")
    if mode == "i2v" and "Picture 1" not in prompt:
        raise SelectError("i2v scene must reference Picture 1")


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


def situation_modes(profile: dict[str, Any]) -> list[str]:
    raw = profile.get("modes")
    if isinstance(raw, list) and raw:
        return [str(m) for m in raw if str(m) in MODES]
    enabled = profile.get("enabled")
    if isinstance(enabled, dict):
        return [m for m in MODES if m in enabled]
    return list(MODES)


def list_situations(
    *,
    catalog_path: Path = CATALOG_PATH,
    profiles_dir: Path = PROFILES_DIR,
) -> dict[str, Any]:
    catalog = load_json(catalog_path)
    index = catalog_index(catalog)
    rows: list[dict[str, Any]] = []
    for path in sorted(profiles_dir.glob("*.json")):
        profile = load_json(path)
        assert_adults_only(profile)
        sid = str(profile.get("id") or path.stem)
        enabled_by_mode: dict[str, list[str]] = {}
        turbo_any = False
        for mode in situation_modes(profile):
            try:
                specs = enabled_specs(profile, mode)
            except SelectError:
                continue
            ids = [str(s["id"]) for s in specs]
            turbo_any = turbo_any or any(str(s.get("role")) == "turbo" for s in specs)
            for lid in ids:
                if lid not in index:
                    raise SelectError(f"{sid}: unknown LoRA {lid}")
            enabled_by_mode[mode] = ids
        rows.append(
            {
                "id": sid,
                "modes": list(enabled_by_mode),
                "enabled": enabled_by_mode,
                "adults_only": True,
                "nsfw": profile_is_nsfw(profile),
                "turbo": turbo_any,
            }
        )
    payload = {"schema": SITUATIONS_SCHEMA, "situations": rows}
    assert_no_secrets(payload)
    return payload


def select_loras(
    *,
    profile_name: str,
    mode: str,
    prompt_arg: str | None = "（シーン）",
    catalog_path: Path = CATALOG_PATH,
    profiles_dir: Path = PROFILES_DIR,
    turbo_override: bool | None = None,
    extra_forbidden: list[str] | None = None,
    forbidden_path: Path | str | None = None,
) -> dict[str, Any]:
    mode = str(mode).lower().strip()
    if mode not in MODES:
        raise SelectError(f"mode must be one of {MODES}")

    profile = load_profile(profile_name, profiles_dir)
    assert_adults_only(profile)
    nsfw = profile_is_nsfw(profile)
    allowed = situation_modes(profile)
    if allowed and mode not in allowed:
        raise SelectError(f"{profile_name} does not support mode {mode}")

    prompt = resolve_prompt(profile, prompt_arg, mode)
    negative = str(profile.get("negative") or "")
    prompt, negative = apply_feminine_lock(prompt, negative, profile)
    hits = forbidden_hits(
        prompt,
        negative=negative,
        extra=extra_forbidden,
        path=forbidden_path,
    )
    if hits:
        raise SelectError(f"forbidden subject in prompt: {hits}")
    assert_mode_prompt(mode, prompt)

    catalog = load_json(catalog_path)
    index = catalog_index(catalog)
    disabled_ids = always_unload_ids(catalog) | {str(x) for x in (profile.get("disabled") or [])}
    enabled = enabled_specs(profile, mode)
    if turbo_override is False:
        enabled = [spec for spec in enabled if spec.get("role") != "turbo"]
    if turbo_override is True:
        act = next((spec for spec in enabled if spec.get("role") == "act"), None)
        if act and str(act.get("id")) == "anal-penetration-coachbate":
            raise SelectError("CoachBate anal penetration stays turbo off")
        if profile.get("allow_turbo") is False:
            raise SelectError(f"{profile_name} stays turbo off (insertion with two helpers)")
    if profile.get("allow_turbo") is False and any(spec.get("role") == "turbo" for spec in enabled):
        raise SelectError(f"{profile_name} stays turbo off (insertion with two helpers)")
    assert_stack_budget(enabled, index, nsfw=nsfw)

    stack: list[dict[str, Any]] = []
    for spec in enabled:
        lid = str(spec["id"])
        if lid in disabled_ids:
            raise SelectError(f"{lid} is both enabled and disabled")
        row = index.get(lid)
        if row is None:
            raise SelectError(f"enabled id not in catalog: {lid}")
        role = str(spec.get("role") or ("turbo" if is_turbo_row(row) else "act"))
        if role == "turbo" and not is_turbo_row(row):
            raise SelectError(f"turbo slot must be a turbo LoRA: {lid}")
        if role != "turbo" and is_turbo_row(row):
            raise SelectError(f"turbo LoRA must use the turbo slot: {lid}")
        modes = [str(m) for m in (row.get("modes") or [])]
        if mode not in modes:
            raise SelectError(f"{lid} does not support mode {mode}")
        arch = str(row.get("arch") or "")
        if mode in {"t2v", "i2v"} and arch == "ref2va":
            raise SelectError(f"ref2va LoRA cannot stack on {mode}: {lid}")
        if mode == "r2v" and arch == "fl2va" and is_turbo_row(row):
            raise SelectError(f"FL2VA turbo cannot stack on r2v: {lid}")
        blob = json.dumps(row, ensure_ascii=False)
        bad = forbidden_hits(blob, extra=extra_forbidden, path=forbidden_path)
        if bad:
            raise SelectError(f"forbidden subject in catalog {lid}: {bad}")
        strength = spec.get("strength", row.get("default_strength", 1.0))
        if role == "cinema" and float(strength) > max_cinema(profile):
            raise SelectError(f"cinema DY must stay at 0.4-{max_cinema(profile)}")
        trigger = str(row.get("trigger") or "").strip()
        stack.append(
            {
                "id": lid,
                "role": role,
                "filename": str(row["filename"]),
                "repo": str(row.get("repo") or ""),
                "file": str(row.get("file") or row["filename"]),
                "arch": arch or "fl2va",
                "strength_model": float(strength),
                "trigger": trigger,
                "adult": bool(row.get("adult")),
                "turbo": bool(is_turbo_row(row)),
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
        if is_turbo_row(row) and not any(item.get("turbo") for item in stack):
            reasons.append("turbo_off")
        elif is_turbo_row(row):
            reasons.append("other_turbo")
        if mode in {"t2v", "i2v"} and str(row.get("arch") or "") == "ref2va":
            reasons.append("ref2va_not_for_fl2va")
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
    canvas = resolve_canvas(profile, mode)
    sampler = default_sampler(profile, enabled)
    has_turbo = any(item.get("turbo") for item in stack)
    payload = {
        "schema": SCHEMA,
        "situation": profile_name,
        "profile": profile_name,
        "mode": mode,
        "adults_only": True,
        "min_age": int(profile.get("min_age") or 21),
        "nsfw": nsfw,
        "turbo": has_turbo,
        "prompt": prompt,
        "negative": negative,
        "forbidden_extra": parse_extra_terms(
            ",".join(extra_terms(forbidden_path) + list(extra_forbidden or []))
        ),
        "first_frame_required": mode == "i2v",
        "canvas": canvas,
        "sampler": sampler,
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
    p.add_argument("--profile", "--situation", dest="profile", default=None)
    p.add_argument("--mode", choices=MODES, default=None)
    p.add_argument("--prompt", default="（シーン）", help="Use シーン to take scenes.<mode>")
    p.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    p.add_argument("--profiles-dir", type=Path, default=PROFILES_DIR)
    p.add_argument("--forbidden", type=Path, default=FORBIDDEN_PATH)
    p.add_argument("--extra-forbidden", default="", help="Comma-separated extra banned words")
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--list", action="store_true", help="List situations and per-mode LoRA stacks")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list:
        payload: dict[str, Any] = list_situations(
            catalog_path=args.catalog,
            profiles_dir=args.profiles_dir,
        )
    else:
        if not args.profile or not args.mode:
            raise SelectError("--profile/--situation and --mode are required (or pass --list)")
        payload = select_loras(
            profile_name=args.profile,
            mode=args.mode,
            prompt_arg=args.prompt,
            catalog_path=args.catalog,
            profiles_dir=args.profiles_dir,
            turbo_override=None,
            extra_forbidden=parse_extra_terms(args.extra_forbidden),
            forbidden_path=args.forbidden,
        )
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    sys.stdout.write(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
