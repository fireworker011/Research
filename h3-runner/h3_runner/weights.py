"""Download only the diffusers subfolders one task loads, then delete the other denoiser.

Sizes are the file-byte sums from
``GET /api/models/MiniMaxAI/MiniMax-H3/tree/main?recursive=1``
(read while writing this runner). ``FL2VA/`` and ``Ref2VA/`` are each about
144.1 GB and are not what ``ModularPipeline`` loads. Do not fetch them.

``ModularPipeline.from_pretrained`` does not snapshot the whole repo. In
diffusers ``5ff8e59`` it reads ``modular_model_index.json``
(``modular_pipeline.py``). ``load_components(workflow=)`` then loads only that
workflow's components. Each component ``from_pretrained(subfolder=)`` calls
``snapshot_download`` with ``allow_patterns`` set to that subfolder's shard
names (``hub_utils.py``). The index still stores the hub id
``MiniMaxAI/MiniMax-H3``, so a later load can reach the hub unless
``pretrained_model_name_or_path`` is the local directory and
``local_files_only=True``.

``huggingface_hub`` 0.36 ``snapshot_download(local_dir=)`` does not also fill
``cache_dir``. Files live once under ``local_dir``, so deleting ``transformer/``
frees its bytes before ``transformer_ref/`` is fetched.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from h3_runner.official import MODEL_ID

# Byte sums of the files in each directory. Not GiB, so they match the API.
FOLDER_BYTES: dict[str, int] = {
    "text_encoder": 66_726_510_529,
    "transformer": 66_280_569_250,
    "transformer_ref": 66_280_569_250,
    "vae": 10_415_635_127,
    "audio_vae": 605_431_611,
    "tokenizer": 11_492_078,
    "processor": 11_498_352,
}
# Largest needed shard (vae/diffusion_pytorch_model-00001-of-00003.safetensors).
# huggingface_hub writes that as ``*.incomplete`` beside the finished file.
LARGEST_SHARD_BYTES = 5_061_033_024

SHARED = ["text_encoder", "vae", "audio_vae", "tokenizer", "processor"]
DENOISER = {"t2va": "transformer", "ref2va": "transformer_ref"}
OTHER_DENOISER = {"t2va": "transformer_ref", "ref2va": "transformer"}
FORBIDDEN = ("FL2VA", "Ref2VA")


def model_dir_name() -> str:
    return "MiniMax-H3"

IGNORE_PATTERNS = [
    "FL2VA/*",
    "FL2VA/**",
    "FL2VA/**/*",
    "Ref2VA/*",
    "Ref2VA/**",
    "Ref2VA/**/*",
    "assets/*",
    "assets/**",
    "docs/*",
    "docs/**",
    "scripts/*",
    "scripts/**",
]


def folders_for(task: str) -> list[str]:
    if task not in DENOISER:
        raise ValueError(task)
    return [*SHARED, DENOISER[task]]


def allow_patterns(folders: list[str]) -> list[str]:
    for name in folders:
        if name in FORBIDDEN or name.startswith("FL2VA") or name.startswith("Ref2VA"):
            raise ValueError(f"拒否するフォルダ: {name}")
    patterns = [
        "modular_model_index.json",
        "model_index.json",
        "scheduler/*",
        "audio_scheduler/*",
    ]
    for name in folders:
        patterns.append(f"{name}/*")
        patterns.append(f"{name}/**")
        patterns.append(f"{name}/**/*")
    return patterns


def snapshot_kwargs(task: str) -> dict[str, list[str]]:
    return {
        "allow_patterns": allow_patterns(folders_for(task)),
        "ignore_patterns": list(IGNORE_PATTERNS),
    }


def on_disk_bytes(local: Path, folder: str) -> int:
    path = local / folder
    if not path.exists():
        return 0
    total = 0
    for item in path.rglob("*"):
        if item.is_file() and not item.is_symlink():
            total += item.stat().st_size
    return total


def disk_anchor(path: Path) -> Path:
    current = path
    while not current.exists():
        if current.parent == current:
            return path
        current = current.parent
    return current


@dataclass
class DiskPreview:
    text: str
    ok: bool


def disk_preview(
    local: Path,
    tasks: list[str],
    *,
    free_bytes: int | None = None,
    sizes: dict[str, int] | None = None,
) -> DiskPreview:
    """Say whether each task fits after the other denoiser is deleted."""
    anchor = disk_anchor(local)
    free = shutil.disk_usage(anchor).free if free_bytes is None else int(free_bytes)
    logical = dict(sizes) if sizes is not None else {name: on_disk_bytes(local, name) for name in FOLDER_BYTES}
    lines = [
        f"キャッシュ: {local}",
        f"ディスク {anchor}: 空き {free / 1e9:.1f} GB（10^9 バイト）。重みはここに置く。Drive には置かない。",
        "FL2VA/ と Ref2VA/ は落とさない（各約 144.1GB）。T2VA のあと transformer/ を消してから transformer_ref/ を取る。",
    ]
    ok = True
    running_free = free
    for task in tasks:
        if task not in DENOISER:
            raise ValueError(task)
        other = OTHER_DENOISER[task]
        running_free += int(logical.get(other, 0))
        logical[other] = 0
        gap = 0
        incomplete = False
        for name in folders_for(task):
            have = int(logical.get(name, 0))
            want = FOLDER_BYTES[name]
            if have < want:
                gap += want - have
                incomplete = True
        shard = LARGEST_SHARD_BYTES if incomplete else 0
        need = gap + shard
        lines.append(
            f"{task}: 反対側の denoiser を消したあと必要 {need / 1e9:.1f} GB、その時点の空き {running_free / 1e9:.1f} GB"
        )
        if running_free < need:
            ok = False
            lines.append(
                f"止める: {task} の空きが足りない。必要 {need / 1e9:.1f} GB、空き {running_free / 1e9:.1f} GB。"
            )
            break
        running_free -= need
        if incomplete:
            running_free += shard
        for name in folders_for(task):
            logical[name] = FOLDER_BYTES[name]
    if not ok:
        lines.append("この段を始める前に止める。FL2VA/ と Ref2VA/ を足しても入らない。")
    return DiskPreview("\n".join(lines), ok)


def _reject_forbidden(local: Path) -> None:
    found = [name for name in FORBIDDEN if (local / name).exists()]
    for name in found:
        shutil.rmtree(local / name)
    if found:
        raise SystemExit(
            f"{', '.join(found)} がキャッシュに入ったので消した。推論では使わない。"
            "allow_patterns が壊れている。"
        )


def prepare(local: Path, task: str) -> Path:
    """Drop the other denoiser, require free space, then snapshot the task's folders."""
    if task not in DENOISER:
        raise ValueError(task)
    local.mkdir(parents=True, exist_ok=True)
    other = local / OTHER_DENOISER[task]
    if other.exists():
        print(f"削除して空きを戻す: {other}", flush=True)
        shutil.rmtree(other)
    _reject_forbidden(local)
    sizes = {name: on_disk_bytes(local, name) for name in FOLDER_BYTES}
    preview = disk_preview(local, [task], sizes=sizes)
    print(preview.text, flush=True)
    if not preview.ok:
        raise SystemExit(preview.text)
    need_names = [name for name in folders_for(task) if sizes.get(name, 0) < FOLDER_BYTES[name]]
    if need_names or not (local / "modular_model_index.json").is_file():
        # Deferred so `disk_preview` and unit tests do not require huggingface_hub.
        from huggingface_hub import snapshot_download

        kwargs = snapshot_kwargs(task)
        print(
            f"download {MODEL_ID} local_dir={local} folders={', '.join(folders_for(task))}",
            flush=True,
        )
        snapshot_download(
            MODEL_ID,
            local_dir=str(local),
            allow_patterns=kwargs["allow_patterns"],
            ignore_patterns=kwargs["ignore_patterns"],
        )
    _reject_forbidden(local)
    return local
