"""Drive job contract for unattended MiniMax H3 T2V / I2VA / R2V.

Video agents drop a folder. Grokbot starts Colab, then stops the runtime.
Affiliate URLs never go in prompts or git.

`mode` is t2v | i2v | r2v. Missing mode means i2v so older homage jobs keep working.
Grokbot duration is 10s for every mode.
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
MODES = ("t2v", "i2v", "r2v")
MODE_ALIASES = {
    "i2va": "i2v",
    "fl2va": "i2v",
    "text": "t2v",
    "t2va": "t2v",
    "ref2v": "r2v",
    "ref2va": "r2v",
}
GROKBOT_DURATION_S = 10.0
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
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".webm", ".mkv"}
PROMPT_SUFFIXES = {".txt", ".md"}
CANVAS_9_16_HIGH = (768, 1344)


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
    data["mode"] = normalize_mode(data.get("mode"))
    return data


def save_job(folder: Path | str, job: dict[str, Any]) -> Path:
    path = job_path(folder)
    path.parent.mkdir(parents=True, exist_ok=True)
    job = dict(job)
    job["mode"] = normalize_mode(job.get("mode"))
    path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def new_job_id(slug: str = "h3") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "-", (slug or "h3").strip())[:40].strip("-") or "h3"
    return f"{stamp}-{safe}"


def normalize_mode(mode: Any, *, default: str = "i2v") -> str:
    raw = str(mode or default).strip().lower()
    return MODE_ALIASES.get(raw, raw or default)


def is_8_9(width: int, height: int, *, tol: float = 0.02) -> bool:
    return height > 0 and abs(width / height - 8 / 9) <= tol


def is_9_16(width: int, height: int, *, tol: float = 0.03) -> bool:
    return height > 0 and abs(width / height - 9 / 16) <= tol


def default_job(**overrides: Any) -> dict[str, Any]:
    mode = normalize_mode(overrides.get("mode", "i2v"))
    if mode == "t2v":
        job: dict[str, Any] = {
            "schema": SCHEMA,
            "id": new_job_id("t2v"),
            "mode": "t2v",
            "status": "ready",
            "created_by": "video-agent",
            "source_image": "",
            "source_video": "",
            "picture1": "",
            "prompt": "",
            "width": 576,
            "height": 1024,
            "duration_s": GROKBOT_DURATION_S,
            "seed": 42,
            "steps": 4,
            "use_lora": True,
            "lora_strength": 1.0,
            "filename_prefix": "video/h3_t2v_job",
            "imagine": {"enabled": False},
            "output_mp4": "",
            "error": "",
        }
    elif mode == "r2v":
        job = {
            "schema": SCHEMA,
            "id": new_job_id("r2v"),
            "mode": "r2v",
            "status": "ready",
            "created_by": "video-agent",
            "source_image": "source.jpg",
            "source_video": "motion.mp4",
            "picture1": "",
            "prompt": "",
            "width": 768,
            "height": 864,
            "duration_s": GROKBOT_DURATION_S,
            "seed": 42,
            "steps": 4,
            "use_lora": True,
            "lora_strength": 1.0,
            "ref_image_size": "max",
            "filename_prefix": "video/h3_r2v_job",
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
    else:
        job = {
            "schema": SCHEMA,
            "id": new_job_id("coconala"),
            "mode": "i2v",
            "status": "ready",
            "created_by": "video-agent",
            "source_image": "source.jpg",
            "source_video": "",
            "picture1": "",
            "prompt": "",
            "width": 768,
            "height": 864,
            "duration_s": GROKBOT_DURATION_S,
            "seed": 42,
            "steps": 4,
            "use_lora": True,
            "lora_strength": 1.0,
            "filename_prefix": "video/h3_i2va_job",
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
    job["mode"] = normalize_mode(job.get("mode"), default=mode)
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


def next_ready_job(root: Path | str, mode: str | None = None) -> Path | None:
    ready = find_jobs(root, status="ready")
    want = normalize_mode(mode) if mode else None
    hits: list[Path] = []
    for folder in ready:
        try:
            job = load_job(folder)
        except Exception:
            continue
        if want and normalize_mode(job.get("mode")) != want:
            continue
        hits.append(folder)
    if not hits:
        return None
    hits.sort(key=lambda p: p.stat().st_mtime)
    return hits[0]


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
    for p in sorted(folder.iterdir()):
        if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES and not p.name.startswith("."):
            return p
    raise FileNotFoundError(f"no still in {folder}")


def resolve_job_video(folder: Path, job: dict[str, Any]) -> Path:
    folder = Path(folder)
    for key in ("source_video", "motion_video", "ref_video"):
        name = str(job.get(key) or "").strip()
        if not name:
            continue
        cand = folder / name
        if cand.is_file():
            return cand
        bare = folder / Path(name).name
        if bare.is_file():
            return bare
    for p in sorted(folder.iterdir()):
        if p.is_file() and p.suffix.lower() in VIDEO_SUFFIXES and not p.name.startswith("."):
            return p
    raise FileNotFoundError(f"no motion video in {folder}")


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
    mode = normalize_mode(job.get("mode"))
    if mode not in MODES:
        errs.append("mode must be t2v, i2v, or r2v")
        mode = "i2v"
    w, h = int(job.get("width") or 0), int(job.get("height") or 0)
    if w % 32 or h % 32 or w < 32 or h < 32:
        errs.append("width/height must be multiples of 32")
    elif mode == "t2v":
        if not is_9_16(w, h) and (w, h) != CANVAS_9_16_HIGH:
            errs.append("t2v canvas must stay 9:16")
    elif mode == "i2v":
        if not is_8_9(w, h):
            errs.append("canvas must stay 8:9")
    elif mode == "r2v":
        if not is_8_9(w, h) and not is_9_16(w, h) and (w, h) != CANVAS_9_16_HIGH:
            errs.append("r2v canvas must stay 8:9 or 9:16")
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
        if mode in ("i2v", "r2v"):
            try:
                resolve_job_image(folder, job)
            except FileNotFoundError:
                errs.append("source_image missing")
        if mode == "r2v":
            try:
                resolve_job_video(folder, job)
            except FileNotFoundError:
                errs.append("source_video missing")
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


def stage_motion(folder: Path, src: Path, job: dict[str, Any], input_dir: Path) -> str:
    name = f"{job['id']}.mp4"
    dest_job = folder / "motion.mp4"
    dest_in = input_dir / name
    data = Path(src).read_bytes()
    dest_job.write_bytes(data)
    input_dir.mkdir(parents=True, exist_ok=True)
    dest_in.write_bytes(data)
    job["source_video"] = "motion.mp4"
    job["staged_motion"] = name
    return name


def adopt_orphan_stills(root: Path | str, *, slug: str = "coconala") -> list[Path]:
    """Turn a bare still in inbox/ into a ready I2V job folder."""
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
        job = default_job(id=jid, mode="i2v", source_image="source.jpg", created_by="inbox-drop")
        save_job(folder, job)
        made.append(folder)
    return made


def adopt_orphan_prompts(root: Path | str, *, slug: str = "t2v") -> list[Path]:
    """Turn a bare prompt .txt in inbox/ into a ready T2V job folder."""
    root = Path(root)
    inbox = root / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    made: list[Path] = []
    for p in sorted(inbox.iterdir()):
        if not p.is_file() or p.suffix.lower() not in PROMPT_SUFFIXES:
            continue
        if p.name.startswith("."):
            continue
        text = p.read_text(encoding="utf-8")
        if forbidden_hits(text):
            continue
        jid = new_job_id(slug)
        folder = inbox / jid
        folder.mkdir(parents=True, exist_ok=False)
        (folder / "prompt.txt").write_text(text, encoding="utf-8")
        p.unlink()
        job = default_job(
            id=jid,
            mode="t2v",
            prompt=text,
            source_image="",
            created_by="inbox-drop",
        )
        save_job(folder, job)
        made.append(folder)
    return made


def adopt_orphan_r2v_folders(root: Path | str, *, slug: str = "r2v") -> list[Path]:
    """Inbox folder with still + mp4 and no job.json becomes an R2V job."""
    root = Path(root)
    inbox = root / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    made: list[Path] = []
    for folder in sorted(inbox.iterdir()):
        if not folder.is_dir() or job_path(folder).is_file():
            continue
        stills = [
            p
            for p in sorted(folder.iterdir())
            if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES and not p.name.startswith(".")
        ]
        vids = [
            p
            for p in sorted(folder.iterdir())
            if p.is_file() and p.suffix.lower() in VIDEO_SUFFIXES and not p.name.startswith(".")
        ]
        if not stills or not vids:
            continue
        still = stills[0]
        vid = vids[0]
        dest_img = folder / "source.jpg"
        dest_vid = folder / "motion.mp4"
        if still.resolve() != dest_img.resolve():
            dest_img.write_bytes(still.read_bytes())
        if vid.resolve() != dest_vid.resolve():
            dest_vid.write_bytes(vid.read_bytes())
        jid = folder.name if ID_RE.match(folder.name) else new_job_id(slug)
        job = default_job(
            id=jid,
            mode="r2v",
            source_image="source.jpg",
            source_video="motion.mp4",
            created_by="inbox-drop",
        )
        save_job(folder, job)
        made.append(folder)
    return made
