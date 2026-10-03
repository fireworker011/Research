"""Write one h3-i2v-job/v1 folder. The grokbot runners consume that inbox."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

_COLAB = Path(__file__).resolve().parents[2] / "colab"
if str(_COLAB) not in sys.path:
    sys.path.insert(0, str(_COLAB))

from h3_affi_prompt import AFFI_PROMPT_KIND, validate_affi_prompt  # noqa: E402
from h3_i2v_job import (  # noqa: E402
    default_job,
    ensure_drive_tree,
    load_job,
    new_job_id,
    save_job,
    validate_job,
)

CREATED_BY = "affi-shorts"
IN_FLIGHT = {"ready", "enhancing", "queued", "running"}
REF_FILES = {"sakura": "sakura-ref.jpg", "dog": "dog-ref.jpg"}
# sakura_916.jpg is the 9:16 crop of sakura-ref already in this repo.
REF_CANDIDATES = {
    "sakura": (
        Path("assets/character/sakura-ref.jpg"),
        Path("/workspace/ai-short-video/assets/character/sakura-ref.jpg"),
        Path("docs/affi-stock/first_frames/_ref/sakura_916.jpg"),
    ),
    "dog": (
        Path("assets/character/dog-ref.jpg"),
        Path("docs/affi-stock/dog-ref.jpg"),
        Path("/workspace/affi-stock-20260930/dog-ref.jpg"),
    ),
}


def resolve_ref(kind: str, ref_dir: Path | None, extra: list[Path] | None = None) -> Path | None:
    if not kind:
        return None
    name = REF_FILES[kind]
    if ref_dir is not None:
        cand = Path(ref_dir) / name
        if cand.is_file():
            return cand
    if extra is not None:
        for root in extra:
            cand = Path(root) / name
            if cand.is_file():
                return cand
        return None
    for cand in REF_CANDIDATES[kind]:
        if cand.is_file():
            return cand
    return None


def inbox_busy(drive: Path) -> bool:
    for bucket in ("inbox", "queued", "running"):
        base = drive / bucket
        if not base.is_dir():
            continue
        for child in base.iterdir():
            path = child / "job.json"
            if not path.is_file():
                continue
            try:
                job = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if job.get("created_by") == CREATED_BY and job.get("status") in IN_FLIGHT:
                return True
    return False


def enqueue_part(
    drive: Path,
    *,
    short_id: str,
    product_id: str,
    pattern_id: str,
    part_index: int,
    part: dict[str, Any],
    script: dict[str, Any],
    ref_dir: Path | None,
    extra_roots: list[Path] | None = None,
) -> dict[str, Any]:
    """Drop a single part. Caller must already know the inbox is free."""
    drive = ensure_drive_tree(drive)
    mode = str(part["mode"])
    ref_kind = str(part.get("ref") or "")
    ref_path = resolve_ref(ref_kind, ref_dir, extra_roots)
    if ref_kind and ref_path is None:
        return {"enqueued": False, "reason": f"参照画像が無い: {REF_FILES[ref_kind]}"}
    errs = validate_affi_prompt(str(part["prompt"]))
    if errs:
        return {"enqueued": False, "reason": "；".join(errs)}
    jid = new_job_id(f"{product_id}-{part['key']}")
    folder = drive / "inbox" / jid
    folder.mkdir(parents=True, exist_ok=False)
    if ref_path is not None:
        (folder / "source.jpg").write_bytes(ref_path.read_bytes())
    job = default_job(
        id=jid,
        mode=mode,
        created_by=CREATED_BY,
        prompt=part["prompt"],
        source_image="source.jpg" if ref_path is not None else "",
        source_video="",
        width=int(part["width"]),
        height=int(part["height"]),
        duration_s=float(part["duration_s"]),
        seed=42,
        steps=9,
        use_lora=True,
        lora_strength=1.0,
        filename_prefix=f"video/h3_affi_{jid}",
        imagine={"enabled": False},
    )
    job["prompt_kind"] = AFFI_PROMPT_KIND
    job["picture1"] = ""
    v = validate_job(job, folder=folder)
    if v:
        shutil.rmtree(folder, ignore_errors=True)
        return {"enqueued": False, "reason": "；".join(v)}
    save_job(folder, job)
    side = {
        "short_id": short_id,
        "product": product_id,
        "pattern_id": pattern_id,
        "part_index": part_index,
        "part_key": part["key"],
        "mode": mode,
        "ref": ref_kind or "なし",
        "ref_file": str(ref_path) if ref_path is not None else "",
        "template_canvas": part.get("template_canvas") or "不明",
        "inbox_canvas": f"{part['width']}x{part['height']}",
        "lora": "FL2V Turbo 8step 1.0",
        "combat": False,
        "voice": "Gemini TTS Achernar",
        "h3_voice": "使わない",
        "hook": script["hook"],
        "beats": script["beats"],
        "title": script["title"],
        "description": script["description"],
        "output_mp4": "",
    }
    (folder / "affi.json").write_text(json.dumps(side, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"enqueued": True, "folder": str(folder), "id": jid, "mode": mode}


def load_side(folder: Path) -> dict[str, Any]:
    return json.loads((folder / "affi.json").read_text(encoding="utf-8"))


def remember_output(folder: Path, mp4: Path) -> None:
    job = load_job(folder)
    job["output_mp4"] = str(mp4)
    save_job(folder, job)
    side = load_side(folder)
    side["output_mp4"] = str(mp4)
    (folder / "affi.json").write_text(json.dumps(side, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
