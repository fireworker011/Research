"""Download the diffusers subfolders once and keep both denoisers.

Sizes are the file-byte sums from
``GET /api/models/MiniMaxAI/MiniMax-H3/tree/main?recursive=1``
(read while writing this runner). ``FL2VA/`` and ``Ref2VA/`` are each about
144.1 GB and are not what ``ModularPipeline`` loads. Do not fetch them.

Both ``transformer/`` and ``transformer_ref/`` stay on disk. Generation never
calls ``snapshot_download``; it only reads a directory that already has the
files (``local_files_only=True``).

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
``cache_dir``. Files live once under ``local_dir``.
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


def folders_for_tasks(tasks: list[str]) -> list[str]:
    """Shared folders once, then each task's denoiser. Both stay."""
    names: list[str] = []
    for task in tasks:
        for name in folders_for(task):
            if name not in names:
                names.append(name)
    return names


def stored_bytes(tasks: list[str]) -> int:
    return sum(FOLDER_BYTES[name] for name in folders_for_tasks(tasks))


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
    return snapshot_kwargs_for(folders_for(task))


def snapshot_kwargs_for(folders: list[str]) -> dict[str, list[str]]:
    return {
        "allow_patterns": allow_patterns(folders),
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
    """Say whether both denoisers fit at once. Nothing is deleted to make room."""
    anchor = disk_anchor(local)
    free = shutil.disk_usage(anchor).free if free_bytes is None else int(free_bytes)
    logical = dict(sizes) if sizes is not None else {name: on_disk_bytes(local, name) for name in FOLDER_BYTES}
    folders = folders_for_tasks(tasks)
    total = sum(FOLDER_BYTES[name] for name in folders)
    gap = 0
    incomplete = False
    lines = [
        f"キャッシュ: {local}",
        f"ディスク {anchor}: 空き {free / 1e9:.1f} GB（10^9 バイト）。",
        "T2VA と Ref2VA の両方を残す。FL2VA/ と Ref2VA/ は落とさない（各約 144.1GB）。",
    ]
    for name in folders:
        want = FOLDER_BYTES[name]
        have = int(logical.get(name, 0))
        lines.append(f"  {name}: {want / 1e9:.2f} GB（ディスク上 {have / 1e9:.2f} GB）")
        if have < want:
            gap += want - have
            incomplete = True
    shard = LARGEST_SHARD_BYTES if incomplete else 0
    need = gap + shard
    lines.append(f"両方置いた合計: {total / 1e9:.1f} GB。未完了分 {need / 1e9:.1f} GB（未完了シャード最大 {LARGEST_SHARD_BYTES / 1e9:.1f} GB を含む）。")
    if free < need:
        short = need - free
        lines.append(
            f"止める: 空きが {short / 1e9:.1f} GB 足りない。必要 {need / 1e9:.1f} GB、空き {free / 1e9:.1f} GB。"
        )
        lines.append(
            "運用: Drive のゴミ箱を空にするか、大きなファイルを別の場所へ移して、"
            f"空きを {need / 1e9:.1f} GB 以上にしてからこのセルをやり直す。"
            "G4 では重みを落とさない。片方だけ置いて生成のたびに取り直すことはしない。"
        )
        return DiskPreview("\n".join(lines), False)
    lines.append("空きは足りている。揃っているフォルダは落とさない。")
    return DiskPreview("\n".join(lines), True)


def _reject_forbidden(local: Path) -> None:
    found = [name for name in FORBIDDEN if (local / name).exists()]
    for name in found:
        shutil.rmtree(local / name)
    if found:
        raise SystemExit(
            f"{', '.join(found)} がキャッシュに入ったので消した。推論では使わない。"
            "allow_patterns が壊れている。"
        )


def missing_folders(local: Path, tasks: list[str]) -> list[str]:
    missing = [
        name
        for name in folders_for_tasks(tasks)
        if on_disk_bytes(local, name) < FOLDER_BYTES[name]
    ]
    if not (local / "modular_model_index.json").is_file():
        missing.append("modular_model_index.json")
    return missing


def require_present(local: Path, tasks: list[str]) -> None:
    """Generation path. Never downloads."""
    missing = missing_folders(local, tasks)
    if not missing:
        print(f"重みは揃っている: {local}", flush=True)
        return
    raise SystemExit(
        "重みが揃っていないので生成しない（この処理はダウンロードしない）: "
        + ", ".join(missing)
        + f"。先に CPU ランタイムで --prepare-weights を実行し、{local} に置く。"
    )


def prepare_all(local: Path, tasks: list[str]) -> Path:
    """Download every folder the tasks need. Keep both denoisers. No GPU."""
    local.mkdir(parents=True, exist_ok=True)
    _reject_forbidden(local)
    sizes = {name: on_disk_bytes(local, name) for name in FOLDER_BYTES}
    preview = disk_preview(local, tasks, sizes=sizes)
    print(preview.text, flush=True)
    if not preview.ok:
        raise SystemExit(preview.text)
    if missing_folders(local, tasks):
        # Deferred so disk checks and unit tests do not require huggingface_hub.
        from huggingface_hub import snapshot_download

        folders = folders_for_tasks(tasks)
        kwargs = snapshot_kwargs_for(folders)
        print(
            f"download {MODEL_ID} local_dir={local} folders={', '.join(folders)}",
            flush=True,
        )
        snapshot_download(
            MODEL_ID,
            local_dir=str(local),
            allow_patterns=kwargs["allow_patterns"],
            ignore_patterns=kwargs["ignore_patterns"],
        )
    else:
        print("既に揃っている。ダウンロードしない。", flush=True)
    _reject_forbidden(local)
    still = missing_folders(local, tasks)
    if still:
        raise SystemExit("ダウンロード後も足りない: " + ", ".join(still))
    print(f"重み準備完了: {local}", flush=True)
    return local
