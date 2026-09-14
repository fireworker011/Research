"""Runtime TIB bind for MiniMax H3 studio. thumbinbutt-h3 -> H3_ThumbInButt.safetensors."""
from __future__ import annotations

from pathlib import Path

TIB_LORA_ID = "thumbinbutt-h3"
TIB_FILE = "H3_ThumbInButt.safetensors"
TIB_FILE_ALIASES = (
    TIB_FILE,
    "MiniMax H3 - ThumbInButt.safetensors",
    "MiniMax_H3_-_ThumbInButt.safetensors",
)
TIB_STRENGTH = 0.55
TIB_MAX_HELPERS = 3
STUDIO_REV_BIND = "h3-20260914-anal-14"


def _roots(*dirs):
    out = []
    for d in dirs:
        if d is None:
            continue
        try:
            out.append(Path(d))
        except TypeError:
            continue
    return out


def _file_in_roots(name: str, roots: list[Path]) -> bool:
    raw = Path(str(name or "")).name
    if not raw:
        return False
    keys = {raw.lower()}
    if raw == TIB_LORA_ID or raw.lower() in {a.lower() for a in TIB_FILE_ALIASES}:
        keys |= {a.lower() for a in TIB_FILE_ALIASES}
        keys.add(TIB_LORA_ID.lower())
    for root in roots:
        for key in keys:
            hit = root / key
            try:
                if hit.is_file() and hit.stat().st_size > 1_000_000:
                    return True
            except OSError:
                continue
    return False


def install(mod=None):
    import inspect
    if mod is None:
        import h3_lora_studio as m
    else:
        m = mod
    m.TIB_LORA_ID = TIB_LORA_ID
    m.TIB_FILE = TIB_FILE
    m.TIB_FILE_ALIASES = TIB_FILE_ALIASES
    m.TIB_STRENGTH = getattr(m, "TIB_STRENGTH", TIB_STRENGTH)
    m.TIB_MAX_HELPERS = TIB_MAX_HELPERS
    m.OPTIONAL_LORA_IDS = frozenset({TIB_LORA_ID}) | set(getattr(m, "OPTIONAL_LORA_IDS", ()))
    m.STUDIO_REV = STUDIO_REV_BIND

    def extra_tib_download_ids() -> list[str]:
        return [TIB_LORA_ID]

    def extra_anal_pen_download_ids() -> list[str]:
        table = getattr(m, "SITUATION_DOWNLOAD", {}) or {}
        return list(table.get("anal_penetration") or ["mystic-xxx-h3", "penis-lora-h3", "synth-pussy-h3"])

    def merge_download_ids(*groups):
        out, seen = [], set()
        for group in groups:
            for lid in group or []:
                key = str(lid or "").strip()
                if key and key not in seen:
                    seen.add(key)
                    out.append(key)
        return out

    _orig_sit = m.situation_ids

    def situation_ids(situation: str) -> list[str]:
        ids = list(_orig_sit(situation))
        return merge_download_ids(ids, extra_tib_download_ids(), extra_anal_pen_download_ids())

    def fill_stack_filenames(stack):
        rows = [dict(r) for r in (stack or [])]
        aliases = {n.lower() for n in TIB_FILE_ALIASES}
        for row in rows:
            if str(row.get("id") or "") != TIB_LORA_ID:
                continue
            fn = str(row.get("filename") or "").strip()
            ln = str(row.get("lora_name") or "").strip()
            if fn.lower() not in aliases:
                row["filename"] = TIB_FILE
            if ln.lower() not in aliases:
                row["lora_name"] = str(row.get("filename") or TIB_FILE)
        return rows

    _orig_apply = m.apply_thumbinbutt_stack

    def apply_thumbinbutt_stack(stack=None, on=False, *, thumb_in_butt=None):
        try:
            rows = _orig_apply(stack, on=on, thumb_in_butt=thumb_in_butt)
        except TypeError:
            rows = _orig_apply(stack, on=on)
        return fill_stack_filenames(rows)

    _orig_missing = m.missing_stack_files

    def _call_orig_missing(rows, lora_dir, extra_dirs):
        try:
            n = len(inspect.signature(_orig_missing).parameters)
        except (TypeError, ValueError):
            n = 2
        if n >= 3:
            try:
                return list(_orig_missing(rows, lora_dir, *extra_dirs))
            except TypeError:
                pass
        return list(_orig_missing(rows, lora_dir))

    def missing_stack_files(stack, lora_dir, *extra_dirs):
        rows = fill_stack_filenames(stack)
        roots = _roots(lora_dir, *extra_dirs)
        missing = _call_orig_missing(rows, lora_dir, extra_dirs)
        out = []
        for name in missing:
            raw = str(name or "")
            if _file_in_roots(raw, roots):
                continue
            if raw == TIB_LORA_ID or raw.lower() in {a.lower() for a in TIB_FILE_ALIASES}:
                out.append(TIB_FILE)
            else:
                out.append(raw)
        return out

    def missing_required_stack_files(stack, lora_dir, *extra_dirs):
        skip = {TIB_LORA_ID.lower(), TIB_FILE.lower(), *(a.lower() for a in TIB_FILE_ALIASES)}
        return [x for x in missing_stack_files(stack, lora_dir, *extra_dirs) if Path(str(x)).name.lower() not in skip]

    def drop_missing_optional_loras(stack, lora_dir, *extra_dirs):
        miss = {Path(str(x)).name.lower() for x in missing_stack_files(stack, lora_dir, *extra_dirs)}
        out = []
        for row in stack or []:
            rid = str(row.get("id") or "")
            fn = Path(str(row.get("filename") or rid)).name.lower()
            if rid.lower() in miss or fn in miss:
                if rid == TIB_LORA_ID or fn in {a.lower() for a in TIB_FILE_ALIASES}:
                    continue
            out.append(row)
        return out

    m.extra_tib_download_ids = extra_tib_download_ids
    m.extra_anal_pen_download_ids = extra_anal_pen_download_ids
    m.merge_download_ids = merge_download_ids
    m.situation_ids = situation_ids
    m.fill_stack_filenames = fill_stack_filenames
    m.apply_thumbinbutt_stack = apply_thumbinbutt_stack
    m.missing_stack_files = missing_stack_files
    m.missing_required_stack_files = missing_required_stack_files
    m.drop_missing_optional_loras = drop_missing_optional_loras
    return m.STUDIO_REV, m.TIB_FILE
