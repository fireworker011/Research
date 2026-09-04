"""Colab helper for stacking MiniMax H3 NSFW LoRAs.

Turbo stays off. Adults 21+ only. Never print API keys.
Fal H3 Max cannot take LoRAs — this is local Comfy FL2VA only.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from h3_civitai import apply_civitai_token, civitai_headers, load_civitai_token

STUDIO_ROOT = Path(__file__).resolve().parents[1] / "h3-lora-studio"
if not STUDIO_ROOT.is_dir():
    STUDIO_ROOT = Path("/content/h3-lora-studio")

OPTIONAL_IDS = {
    "astro-nsfw-h3": 0.35,
    "tiddies-realism-slider": 1.2,
    "h3-realism-people": 1.0,
    "photoreal-h3-still": 1.0,
}

SITUATION_DOWNLOAD = {
    "anal_closeup": ["synth-pussy-h3", "anal-penetration-coachbate"],
    "anal_penetration": ["hmnsfw-aio-v25", "anal-penetration-coachbate"],
    "futa_blowjob": ["futa-h3-v51", "penis-lora-h3", "blowjob-h3"],
    "oral": ["blowjob-h3", "penis-lora-h3"],
    "riding": ["riding-pose-i2v", "hmnsfw-aio-v25", "h3-realism-people"],
}

SITUATION_JA = {
    "穴アップ（舐め・指）": "anal_closeup",
    "アナル挿入": "anal_penetration",
    "ふたなりフェラ": "futa_blowjob",
    "フェラ": "oral",
    "騎乗位": "riding",
    "anal_closeup": "anal_closeup",
    "anal_penetration": "anal_penetration",
    "futa_blowjob": "futa_blowjob",
    "oral": "oral",
    "riding": "riding",
}

MODE_JA = {
    "テキストから（写真なし）": "t2v",
    "写真から（1枚必要）": "i2v",
    "t2v": "t2v",
    "i2v": "i2v",
}

SITUATION_HELP = {
    "anal_closeup": "穴がよく見えるアップ。舐め・指。部品は穴の見え方とアナル挿入。",
    "anal_penetration": "後ろからの挿入。穴が膣に逃げやすいときのセット。部品は総合えっちとアナル挿入。",
    "futa_blowjob": "ふたなりフェラ。部品はふたなり・竿・フェラ。写真からの方が安定。",
    "oral": "フェラ。部品はフェラと竿。",
    "riding": "騎乗位。写真からなら騎乗用、テキストからなら総合えっち。",
}

LORA_JA = {
    "synth-pussy-h3": "穴の見え方",
    "anal-penetration-coachbate": "アナル挿入",
    "hmnsfw-aio-v25": "総合えっち",
    "futa-h3-v51": "ふたなり",
    "penis-lora-h3": "竿",
    "blowjob-h3": "フェラ",
    "riding-pose-i2v": "騎乗のポーズ",
    "h3-realism-people": "肌のリアルさ",
    "tiddies-realism-slider": "胸の大きさ",
    "astro-nsfw-h3": "動きの底上げ",
    "photoreal-h3-still": "静止画用の写実",
}


def resolve_situation(name: str) -> str:
    key = str(name or "").strip()
    if key in SITUATION_JA:
        return SITUATION_JA[key]
    raise SystemExit(
        "シーンの名前が分かりません。フォームのリストから選んでください。"
        f" 入力: {name}"
    )


def resolve_mode(name: str) -> str:
    key = str(name or "").strip()
    if key in MODE_JA:
        return MODE_JA[key]
    raise SystemExit("作り方は「テキストから（写真なし）」か「写真から（1枚必要）」を選んでください。")


def friendly_lora(lora_id: str) -> str:
    return LORA_JA.get(str(lora_id), str(lora_id))


def explain_choice(situation: str, mode: str) -> str:
    sid = resolve_situation(situation)
    mid = resolve_mode(mode)
    how = "テキストから動画（写真は使いません）" if mid == "t2v" else "写真1枚から動画（Drive の input に jpg）"
    parts = "、".join(friendly_lora(x) for x in SITUATION_DOWNLOAD[sid])
    return (
        f"シーン: {situation}\n"
        f"作り方: {how}\n"
        f"説明: {SITUATION_HELP[sid]}\n"
        f"使う部品: {parts}\n"
        "速いモード（Turbo）は使いません。"
    )


def civitai_token(pasted: str = "", drive_root: Path | str | None = None) -> str:
    token, _source = load_civitai_token(pasted=pasted, drive_root=drive_root)
    apply_civitai_token(token)
    return token


def load_catalog(studio_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(studio_root or STUDIO_ROOT)
    path = root / "catalog" / "loras.json"
    return json.loads(path.read_text(encoding="utf-8"))


def catalog_by_id(catalog: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    data = catalog or load_catalog()
    return {str(row["id"]): row for row in data.get("loras") or [] if row.get("id")}


def civitai_download_url(row: dict[str, Any]) -> str:
    version = int(row["civitai_version_id"])
    file_id = int(row["civitai_file_id"])
    return f"https://civitai.com/api/download/models/{version}?fileId={file_id}"


def download_jobs_for(
    ids: list[str],
    lora_dir: Path | str,
    *,
    catalog: dict[str, Any] | None = None,
) -> list[tuple[str, Path, dict[str, Any]]]:
    index = catalog_by_id(catalog)
    dest_dir = Path(lora_dir)
    jobs: list[tuple[str, Path, dict[str, Any]]] = []
    seen: set[str] = set()
    for lid in ids:
        if lid in seen:
            continue
        seen.add(lid)
        row = index.get(lid)
        if row is None:
            raise SystemExit(f"unknown LoRA id: {lid}")
        dest = dest_dir / str(row["filename"])
        source = str(row.get("source") or "hf")
        if source == "civitai":
            url = civitai_download_url(row)
        elif row.get("repo") and not str(row["repo"]).startswith("civitai:"):
            url = (
                "https://huggingface.co/"
                + str(row["repo"])
                + "/resolve/main/"
                + str(row.get("file") or row["filename"])
            )
        else:
            continue
        jobs.append((url, dest, row))
    return jobs


def fetch_weight(
    url: str,
    dest: Path,
    *,
    token: str = "",
    auth: str = "",
    min_bytes: int = 1_000_000,
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > min_bytes:
        print(f"skip {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
        return
    tmp = dest.with_name(dest.name + ".part")
    headers = {"User-Agent": "h3-lora-studio/colab"}
    if auth == "civitai" and token:
        headers.update(civitai_headers(token))
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=600) as resp, open(tmp, "wb") as out:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
    except urllib.error.HTTPError as exc:
        if tmp.exists():
            tmp.unlink()
        if exc.code in {401, 403}:
            raise SystemExit(
                f"Civitai が {exc.code} を返した: {dest.name}。"
                "Drive の civitai_api_token.txt か ①のフォームに API キーを入れてやり直す。"
                "取り方: https://civitai.com/user/account → API Keys。キー自体はログに出さない。"
            ) from exc
        raise SystemExit(f"DL 失敗 {exc.code}: {dest.name}") from exc
    if not tmp.is_file() or tmp.stat().st_size < min_bytes:
        if tmp.exists():
            tmp.unlink()
        raise SystemExit(f"DL 失敗（小さい）: {dest.name}")
    tmp.replace(dest)
    print(f"saved {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")


def inject_lora_stack(
    g: dict[str, Any],
    stack: list[dict[str, Any]],
    *,
    steps: int = 16,
    unet_node: str = "1",
) -> dict[str, Any]:
    """Chain LoraLoaderModelOnly. Always turbo-off sampler."""
    if g.get("2", {}).get("class_type") == "LoraLoaderModelOnly":
        del g["2"]
    prev = unet_node
    last = unet_node
    for i, item in enumerate(stack, start=1):
        name = str(item.get("filename") or item.get("lora_name") or "")
        if not name:
            raise ValueError("stack item needs filename")
        nid = str(200 + i)
        g[nid] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": [prev, 0],
                "lora_name": name,
                "strength_model": float(item.get("strength_model", item.get("strength", 1.0))),
            },
        }
        prev = nid
        last = nid
    model = [last, 0] if stack else [unet_node, 0]
    if "22" in g:
        g["22"]["inputs"]["sampler_name"] = "res_multistep"
    if "23" in g:
        g["23"]["inputs"]["model"] = model
        g["23"]["inputs"]["scheduler"] = "beta"
        g["23"]["inputs"]["steps"] = max(int(steps), 16)
    if "24" in g:
        g["24"]["inputs"]["model"] = model
    return g


def merge_optional(
    stack: list[dict[str, Any]],
    *,
    extras: list[str],
    catalog: dict[str, Any] | None = None,
    mode: str = "t2v",
) -> list[dict[str, Any]]:
    index = catalog_by_id(catalog)
    have = {item["id"] for item in stack}
    out = list(stack)
    for lid in extras:
        if lid in have:
            continue
        row = index.get(lid)
        if row is None:
            raise SystemExit(f"unknown extra LoRA: {lid}")
        modes = [str(m) for m in (row.get("modes") or [])]
        if mode not in modes:
            print(f"skip extra {lid}: not for {mode}")
            continue
        if row.get("turbo") is True:
            print(f"skip extra {lid}: turbo stays off")
            continue
        out.append(
            {
                "id": lid,
                "filename": str(row["filename"]),
                "strength_model": float(OPTIONAL_IDS.get(lid, row.get("default_strength") or 1.0)),
                "trigger": str(row.get("trigger") or ""),
            }
        )
        have.add(lid)
    return out


def situation_ids(situation: str) -> list[str]:
    ids = SITUATION_DOWNLOAD.get(situation)
    if not ids:
        raise SystemExit(f"unknown situation: {situation}")
    return list(ids)


def prepend_triggers(prompt: str, stack: list[dict[str, Any]]) -> str:
    triggers = []
    low = prompt.lower()
    for item in stack:
        trig = str(item.get("trigger") or "").strip()
        if trig and trig.lower() not in low:
            triggers.append(trig)
    if not triggers:
        return prompt
    return ", ".join(triggers) + "\n" + prompt


def assert_no_secret_text(text: str) -> None:
    blob = text.lower()
    if "civitai_api_token=" in blob or "xai_api_key=" in blob:
        raise SystemExit("refusing to print API keys")


def studio_sys_path(studio_root: Path | str | None = None) -> None:
    root = Path(studio_root or STUDIO_ROOT)
    scripts = root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
