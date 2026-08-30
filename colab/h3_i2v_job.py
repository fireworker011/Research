"""Drive job contract for unattended MiniMax H3 I2VA.

Video agents drop a folder. Grokbot enhances the still, then fal H3 Max
(default) or Colab I2VA. Affiliate URLs never go in prompts or git.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "h3-i2v-job/v1"
DRIVE_ROOT_DEFAULT = "/content/drive/MyDrive/minimax-h3-comfyui"
JOB_DIRS = ("inbox", "queued", "running", "done", "failed", "input", "output", "models")
STATUSES = ("draft", "ready", "enhancing", "queued", "running", "done", "failed")
TRANSITIONS = {
    "draft": {"ready", "failed"},
    "ready": {"enhancing", "queued", "failed"},
    "enhancing": {"queued", "failed"},
    "queued": {"running", "failed"},
    "running": {"done", "failed"},
    "done": set(),
    "failed": {"ready"},
}
FORBIDDEN = ("px.a8.net", "a8mat=", "稼げる", "必ず稼", "月収", "年収")
DEFAULT_IMAGINE_PROMPT = (
    "Photoreal quality pass of Picture 1 only. Keep the exact same young Japanese woman, "
    "face, long dark brown hair with bangs, dark navy zip-up hoodie over a white top, "
    "desk, laptop, drawing tablet, stylus, and cyan holographic UI. No anime. "
    "No illustration. No extra on-screen URL. No instruction-sheet labels or numbered panels. "
    "Clean 3:4 still, sharp, usable as MiniMax H3 first frame."
)
ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,80}$")


def drive_root(path: str | Path | None = None) -> Path:
    import os

    raw = path or os.environ.get("H3_DRIVE_ROOT") or DRIVE_ROOT_DEFAULT
    return Path(raw)


def ensure_drive_tree(root: Path | str) -> Path:
    root = Path(root)
    for name in JOB_DIRS:
        (root / name).mkdir(parents=True, exist_ok=True)
    return root


def job_path(folder: Path | str) -> Path:
    return Path(folder) / "job.json"


def load_job(folder: Path | str) -> dict[str, Any]:
    path = job_path(folder)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("job.json must be an object")
    return data


def save_job(folder: Path | str, job: dict[str, Any]) -> Path:
    path = job_path(folder)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def new_job_id(slug: str = "h3") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "-", (slug or "h3").strip())[:40].strip("-") or "h3"
    return f"{stamp}-{safe}"


def default_job(**overrides: Any) -> dict[str, Any]:
    job: dict[str, Any] = {
        "schema": SCHEMA,
        "id": new_job_id("coconala"),
        "status": "ready",
        "created_by": "video-agent",
        "source_image": "source.jpg",
        "picture1": "",
        "prompt": "",
        "width": 768,
        "height": 864,
        "duration_s": 10,
        "seed": 42,
        "steps": 4,
        "use_lora": True,
        "lora_strength": 1.0,
        "filename_prefix": "video/h3_i2va_job",
        "backend": "fal-max",
        "imagine": {
            "enabled": True,
            "model": "grok-imagine-image-2.0",
            "quality": "medium",
            "resolution": "2k",
            "aspect_ratio": "3:4",
            "prompt": DEFAULT_IMAGINE_PROMPT,
        },
        "output_mp4": "",
        "error": "",
    }
    job.update(overrides)
    return job


def set_status(job: dict[str, Any], nxt: str) -> dict[str, Any]:
    cur = str(job.get("status") or "draft")
    allowed = TRANSITIONS.get(cur, set())
    if nxt not in allowed:
        raise ValueError(f"illegal status {cur} → {nxt}")
    job["status"] = nxt
    if nxt != "failed":
        job["error"] = ""
    return job


def find_jobs(root: Path | str, *, status: str | None = None) -> list[Path]:
    root = Path(root)
    hits: list[Path] = []
    for bucket in ("inbox", "queued", "running", "done", "failed"):
        base = root / bucket
        if not base.is_dir():
            continue
        for child in sorted(base.iterdir()):
            if child.is_dir() and job_path(child).is_file():
                hits.append(child)
    if status is None:
        return hits
    out = []
    for folder in hits:
        try:
            if load_job(folder).get("status") == status:
                out.append(folder)
        except Exception:
            continue
    return out


def next_ready_job(root: Path | str) -> Path | None:
    ready = find_jobs(root, status="ready")
    if not ready:
        return None
    ready.sort(key=lambda p: p.stat().st_mtime)
    return ready[0]


def move_job(folder: Path, bucket: str, root: Path) -> Path:
    dest_dir = root / bucket / folder.name
    dest_dir.parent.mkdir(parents=True, exist_ok=True)
    if folder.resolve() == dest_dir.resolve():
        return folder
    if dest_dir.exists():
        raise FileExistsError(dest_dir)
    folder.rename(dest_dir)
    return dest_dir


def resolve_job_image(folder: Path, job: dict[str, Any]) -> Path:
    folder = Path(folder)
    for key in ("picture1", "source_image"):
        name = str(job.get(key) or "").strip()
        if not name:
            continue
        cand = folder / name
        if cand.is_file():
            return cand
        bare = folder / Path(name).name
        if bare.is_file():
            return bare
    raise FileNotFoundError(f"no still in {folder}")


def forbidden_hits(text: str) -> list[str]:
    low = (text or "").lower()
    return [w for w in FORBIDDEN if w.lower() in low]


def validate_job(job: dict[str, Any], *, folder: Path | None = None) -> list[str]:
    errs: list[str] = []
    if job.get("schema") != SCHEMA:
        errs.append(f"schema must be {SCHEMA}")
    jid = str(job.get("id") or "")
    if not ID_RE.match(jid):
        errs.append("id must be a short slug")
    if job.get("status") not in STATUSES:
        errs.append("bad status")
    w, h = int(job.get("width") or 0), int(job.get("height") or 0)
    if w % 32 or h % 32 or w < 32 or h < 32:
        errs.append("width/height must be multiples of 32")
    if abs(w / h - 8 / 9) > 0.02:
        errs.append("canvas must stay 8:9")
    dur = float(job.get("duration_s") or 0)
    if dur < 4 or dur > 15:
        errs.append("duration_s must be 4–15")
    blob = json.dumps(job, ensure_ascii=False)
    errs.extend(f"forbidden {w}" for w in forbidden_hits(blob))
    prompt = str(job.get("prompt") or "")
    errs.extend(f"forbidden in prompt {w}" for w in forbidden_hits(prompt))
    imagine = job.get("imagine") or {}
    if isinstance(imagine, dict):
        errs.extend(f"forbidden in imagine {w}" for w in forbidden_hits(str(imagine.get("prompt") or "")))
    if folder is not None:
        src = str(job.get("source_image") or "").strip()
        if src and not (Path(folder) / Path(src).name).is_file() and not (Path(folder) / src).is_file():
            pic = str(job.get("picture1") or "").strip()
            if not pic or not (Path(folder) / Path(pic).name).is_file():
                errs.append("source_image missing")
    return errs


def stage_picture1(folder: Path, src: Path, job: dict[str, Any], input_dir: Path) -> str:
    name = f"{job['id']}.jpg"
    dest_job = folder / "picture1.jpg"
    dest_in = input_dir / name
    data = Path(src).read_bytes()
    dest_job.write_bytes(data)
    input_dir.mkdir(parents=True, exist_ok=True)
    dest_in.write_bytes(data)
    job["picture1"] = "picture1.jpg"
    job["staged_input"] = name
    return name


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def adopt_orphan_stills(root: Path | str, *, slug: str = "coconala") -> list[Path]:
    """Turn a bare still in inbox/ into a ready job folder. Video agents can drop only a jpg."""
    root = Path(root)
    inbox = root / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    made: list[Path] = []
    for p in sorted(inbox.iterdir()):
        if not p.is_file() or p.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if p.name.startswith("."):
            continue
        jid = new_job_id(slug)
        folder = inbox / jid
        folder.mkdir(parents=True, exist_ok=False)
        dest = folder / "source.jpg"
        dest.write_bytes(p.read_bytes())
        p.unlink()
        job = default_job(id=jid, source_image="source.jpg", created_by="inbox-drop")
        save_job(folder, job)
        made.append(folder)
    return made

