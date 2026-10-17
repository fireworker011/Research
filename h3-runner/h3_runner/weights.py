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

Colab's ``/content/drive`` is drivefs. ``statvfs`` there reports the VM disk,
not the Google Drive quota, so a free-space check on that mount must not stop
the prepare. Writes are cached on the VM disk (``/``, including the DriveFS
cache) and uploaded after. Prepare therefore downloads one file at a time into
``/content/tmp_hf``, moves it onto Drive, deletes the local copy, and calls
``os.sync``. It does not call ``drive.flush_and_unmount``.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import time
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
# `/` free below this means the DriveFS write-back cache is still on the VM disk.
LOCAL_FREE_FLOOR_BYTES = 30_000_000_000
# Worst case while one shard is in flight: hub cache, staging copy, DriveFS cache.
LOCAL_COPIES_DURING_SHARD = 3
WAIT_SECONDS = 20
ROOT_FILES = ("modular_model_index.json", "model_index.json")
EXTRA_DIRS = ("scheduler", "audio_scheduler")

SHARED = ["text_encoder", "vae", "audio_vae", "tokenizer", "processor"]
DENOISER = {
    "t2va": "transformer",
    "fl2va": "transformer",
    "i2va": "transformer",
    "ref2va": "transformer_ref",
}
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


def is_colab_drive(path: Path) -> bool:
    """True for ``/content/drive/...``. statvfs there is the VM disk, not Drive quota."""
    return Path(path).parts[:3] == ("/", "content", "drive")


def local_encode_path(out_path: Path) -> Path:
    """Where PyAV should mux the mp4.

    ``av.open`` seeks while it writes the moov atom. The Colab Drive mount
    accepts a small JSON write and fails that mux, which leaves
    ``*.request.json`` and no mp4. Encode on the VM disk, then copy.
    """
    out_path = Path(out_path)
    if not is_colab_drive(out_path):
        return out_path
    root = Path("/content/h3-mp4") if Path("/content").is_dir() else Path(tempfile.gettempdir()) / "h3-mp4"
    parts = out_path.parts
    if "MyDrive" in parts:
        tail = parts[parts.index("MyDrive") + 1 :]
    else:
        tail = parts[3:]
    if not tail:
        tail = (out_path.name,)
    return root.joinpath(*tail)


def failure_text(stage: str, exc: BaseException) -> str:
    """One line for the cell and for ``*.error.txt``. ``request.json`` is not this."""
    return f"{stage}で止めた。{type(exc).__name__}: {exc}"


def staging_dir() -> Path:
    """Local scratch for one shard. Colab uses ``/content/tmp_hf``."""
    if Path("/content").is_dir():
        return Path("/content/tmp_hf")
    return Path(tempfile.gettempdir()) / "h3_tmp_hf"


def local_free_bytes() -> int:
    """Free bytes on ``/``. DriveFS caches uploads on this disk."""
    return int(shutil.disk_usage("/").free)


def bytes_needed(floor: int, shard_bytes: int, copies: int) -> int:
    return int(floor) + max(0, int(shard_bytes)) * int(copies)


def shard_is_current(path: Path, size: int) -> bool:
    """True when Drive already has this file at the repo size."""
    if size < 0 or not path.is_file() or path.is_symlink():
        return False
    try:
        return path.stat().st_size == size
    except OSError:
        return False


def select_repo_files(entries, tasks: list[str]) -> list[tuple[str, int]]:
    """Files to store. ``FL2VA/`` and ``Ref2VA/`` are never included."""
    folders = [*folders_for_tasks(tasks), *EXTRA_DIRS]
    prefixes = tuple(f"{name}/" for name in folders)
    selected: list[tuple[str, int]] = []
    for entry in entries:
        path = getattr(entry, "path", None)
        if path is None and isinstance(entry, dict):
            path = entry.get("path")
        if not path or path.endswith("/"):
            continue
        if path.startswith(FORBIDDEN) or path.split("/", 1)[0] in FORBIDDEN:
            continue
        head = path.split("/", 1)[0]
        if head in {"assets", "docs", "scripts"}:
            continue
        if path not in ROOT_FILES and not path.startswith(prefixes):
            continue
        size = getattr(entry, "size", None)
        if size is None and isinstance(entry, dict):
            size = entry.get("size")
        if size is None:
            continue
        selected.append((str(path), int(size)))
    selected.sort()
    return selected


def wait_for_local_free(
    need: int,
    *,
    free_fn=local_free_bytes,
    sleeper=time.sleep,
    sync_fn=None,
    wait_seconds: float = WAIT_SECONDS,
) -> int:
    """Block until ``/`` has ``need`` bytes free. DriveFS upload cache lives there."""
    if sync_fn is None:
        sync_fn = getattr(os, "sync", lambda: None)
    while True:
        sync_fn()
        free = int(free_fn())
        if free >= need:
            return free
        print(
            f"待つ: ローカル空き {free / 1e9:.1f} GB。"
            f"{need / 1e9:.1f} GB になるまで drivefs のキャッシュが上がるのを待つ。",
            flush=True,
        )
        sleeper(wait_seconds)


def sync_disk() -> None:
    sync = getattr(os, "sync", None)
    if sync is not None:
        sync()


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
        f"置く denoiser: {', '.join(dict.fromkeys(DENOISER[task] for task in tasks))}。"
        "FL2VA/ と Ref2VA/ は落とさない（各約 144.1GB）。",
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
    lines.append(f"置く合計: {total / 1e9:.1f} GB。未完了分 {need / 1e9:.1f} GB（未完了シャード最大 {LARGEST_SHARD_BYTES / 1e9:.1f} GB を含む）。")
    if is_colab_drive(local):
        lines.append(
            f"参考: ディスク {anchor} の空き {free / 1e9:.1f} GB。"
            "Colab のマウントは VM ディスクの値を返すので Drive 実容量ではない。この数字では止めない。"
        )
        lines.append(
            "シャードを1本ずつローカルへ落として Drive へ移す。"
            f"`/` の空きが {LOCAL_FREE_FLOOR_BYTES / 1e9:.0f} GB を切ったら、"
            "drivefs のキャッシュが上がるまで待つ。"
        )
        return DiskPreview("\n".join(lines), True)
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


def _point_hub_cache(staging: Path) -> None:
    home = staging / "hf-home"
    home.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(home)
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(home / "hub")
    os.environ["HF_HUB_CACHE"] = str(home / "hub")


def _wipe_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _publish_shard(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".partial")
    if partial.exists():
        partial.unlink()
    shutil.copyfile(src, partial)
    os.replace(partial, dest)


def _progress(index: int, total: int, done: int, total_bytes: int, verb: str, rel: str) -> None:
    print(
        f"{index}/{total}  {done / 1e9:.2f}/{total_bytes / 1e9:.2f} GB  {verb}  {rel}",
        flush=True,
    )


def _clear_partials(local: Path) -> None:
    if not local.exists():
        return
    for item in local.rglob("*"):
        if item.is_file() and item.suffix in {".incomplete", ".partial"}:
            item.unlink()


def prepare_all(local: Path, tasks: list[str]) -> Path:
    """Download every needed file, one at a time. Keep both denoisers. No GPU.

    ``drive.flush_and_unmount`` is not used. Each shard is synced with ``os.sync``.
    """
    local.mkdir(parents=True, exist_ok=True)
    _clear_partials(local)
    _reject_forbidden(local)
    sizes = {name: on_disk_bytes(local, name) for name in FOLDER_BYTES}
    preview = disk_preview(local, tasks, sizes=sizes)
    print(preview.text, flush=True)
    if not preview.ok:
        raise SystemExit(preview.text)
    if not missing_folders(local, tasks):
        print("既に揃っている。ダウンロードしない。", flush=True)
        print(f"重み準備完了: {local}", flush=True)
        return local

    staging = staging_dir()
    if local.resolve() == staging or staging in local.resolve().parents or local.resolve() in staging.parents:
        raise SystemExit(f"一時ディレクトリが保存先と重なる: {staging} / {local}")
    _wipe_dir(staging)
    _point_hub_cache(staging)
    # Deferred so disk checks and unit tests do not require huggingface_hub.
    from huggingface_hub import HfApi, hf_hub_download

    files = select_repo_files(HfApi().list_repo_tree(MODEL_ID, recursive=True), tasks)
    if not files:
        raise SystemExit("リポジトリ一覧から落とすファイルが0件。")
    total_n = len(files)
    total_bytes = sum(max(0, size) for _, size in files)
    print(
        f"シャード {total_n} 本、合計 {total_bytes / 1e9:.2f} GB。1本ずつ {local} へ。一時先 {staging}。",
        flush=True,
    )
    done = 0
    for index, (rel, size) in enumerate(files, start=1):
        dest = local / rel
        if shard_is_current(dest, size):
            done += max(0, size)
            _progress(index, total_n, done, total_bytes, "飛ばす", rel)
            continue
        room = bytes_needed(LOCAL_FREE_FLOOR_BYTES, max(0, size), LOCAL_COPIES_DURING_SHARD)
        wait_for_local_free(room)
        _wipe_dir(staging)
        _point_hub_cache(staging)
        got = Path(
            hf_hub_download(
                MODEL_ID,
                rel,
                local_dir=str(staging),
                cache_dir=str(staging / "hf-home" / "hub"),
            )
        )
        wait_for_local_free(bytes_needed(LOCAL_FREE_FLOOR_BYTES, max(0, size), 1))
        _publish_shard(got, dest)
        _wipe_dir(staging)
        sync_disk()
        wait_for_local_free(LOCAL_FREE_FLOOR_BYTES)
        wrote = dest.stat().st_size if dest.is_file() else max(0, size)
        done += wrote
        _progress(index, total_n, done, total_bytes, "書いた", rel)
    _reject_forbidden(local)
    still = missing_folders(local, tasks)
    if still:
        raise SystemExit("ダウンロード後も足りない: " + ", ".join(still))
    print(f"重み準備完了: {local}", flush=True)
    return local
