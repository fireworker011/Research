import os
import subprocess
from pathlib import Path

DRIVE_BASE = "/content/drive/MyDrive/ComfyUI_models"
LOCAL_BASE = "/content/ComfyUI_models"
HF = "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main"
UNET_FILE = "wan2.1_vace_14B_fp16.safetensors"
TE_FILE = "umt5_xxl_fp8_e4m3fn_scaled.safetensors"
VAE_FILE = "wan_2.1_vae.safetensors"

MODEL_SPECS = [
    {
        "name": UNET_FILE,
        "url": f"{HF}/split_files/diffusion_models/{UNET_FILE}",
        "folder": "diffusion_models",
        "alts": [],
        "min_bytes": 32_000_000_000,
    },
    {
        "name": TE_FILE,
        "url": f"{HF}/split_files/text_encoders/{TE_FILE}",
        "folder": "text_encoders",
        "alts": ["clip"],
        "min_bytes": 6_400_000_000,
    },
    {
        "name": VAE_FILE,
        "url": f"{HF}/split_files/vae/{VAE_FILE}",
        "folder": "vae",
        "alts": [],
        "min_bytes": 240_000_000,
    },
]


def _is_under(path, root):
    path = os.path.abspath(path)
    root = os.path.abspath(root)
    return path == root or path.startswith(root + os.sep)


def file_ok(path, min_bytes):
    try:
        return os.path.isfile(path) and os.path.getsize(path) >= min_bytes
    except OSError:
        return False


def candidate_paths(item, drive_base, local_base):
    folders = [item["folder"], *item.get("alts", [])]
    paths = []
    for base in (drive_base, local_base):
        for folder in folders:
            paths.append(os.path.join(base, folder, item["name"]))
    return paths


def plan_models(specs, drive_base, local_base, exists=file_ok):
    """Reuse a complete file on Drive or local disk. Missing files download under local_base."""
    resolved = {}
    downloads = []
    for item in specs:
        found = None
        for path in candidate_paths(item, drive_base, local_base):
            if exists(path, item["min_bytes"]):
                found = path
                break
        if found:
            resolved[item["name"]] = found
            continue
        dest = os.path.join(local_base, item["folder"], item["name"])
        downloads.append(
            {
                "name": item["name"],
                "url": item["url"],
                "dest": dest,
                "min_bytes": item["min_bytes"],
            }
        )
        resolved[item["name"]] = dest
    return resolved, downloads


def needs_drive_space(dest, drive_base):
    return _is_under(dest, drive_base)


def removable_incomplete(path, min_bytes, local_base, drive_base):
    """Incomplete downloads we made on Colab disk can be replaced. Drive files stay."""
    if _is_under(path, drive_base) or not _is_under(path, local_base):
        return False
    try:
        return os.path.isfile(path) and os.path.getsize(path) < min_bytes
    except OSError:
        return False


def disk_free(path):
    probe = path
    while probe and not os.path.exists(probe):
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe = parent
    stat = os.statvfs(probe or "/")
    return stat.f_bavail * stat.f_frsize


def ensure_download_space(downloads, free_lookup, drive_base):
    """Check free space only on the disk that will receive the files."""
    groups = {}
    for item in downloads:
        dest = item["dest"]
        on_drive = needs_drive_space(dest, drive_base)
        key = "drive" if on_drive else "local"
        group = groups.setdefault(key, {"need": 0, "dest": dest, "on_drive": on_drive})
        group["need"] += int(item["min_bytes"])
    for group in groups.values():
        probe = drive_base if group["on_drive"] else os.path.dirname(group["dest"])
        free = int(free_lookup(probe))
        if free >= group["need"]:
            continue
        if group["on_drive"]:
            raise RuntimeError(
                f"Drive の空き {free / 1e9:.1f} GB が、Drive へ保存する"
                f" {group['need'] / 1e9:.1f} GB より小さいです。"
                "モデルは Drive に無いとき Colab ディスクへ取得します。"
                "ユーザーのファイルは消しません。"
            )
        raise RuntimeError(
            f"Colab ディスクの空き {free / 1e9:.1f} GB が、"
            f"{group['need'] / 1e9:.1f} GB より小さいです。"
            "Drive の空きでは止めません。"
        )


def extra_model_yaml(drive_base, local_base):
    def block(label, base):
        return (
            f"{label}:\n"
            f"    base_path: {base}\n"
            "    diffusion_models: diffusion_models/\n"
            "    unet: diffusion_models/\n"
            '    text_encoders: "text_encoders/\\nclip/"\n'
            "    vae: vae/\n"
            "    clip: clip/\n"
        )

    # Local first, so a complete Colab copy wins over a short file left on Drive.
    return block("h3_vace_local", local_base) + block("h3_vace_drive", drive_base)


def run_model_setup():
    if not globals().get("GPU_OK"):
        raise RuntimeError("GPU チェックを通過していません。最初のセルから実行してください。")
    if not os.path.isdir("/content/ComfyUI"):
        raise RuntimeError("セットアップセルを先に実行してください。")

    resolved, downloads = plan_models(MODEL_SPECS, DRIVE_BASE, LOCAL_BASE)
    for name, path in resolved.items():
        if any(item["name"] == name for item in downloads):
            continue
        print(f"スキップ（既存 {os.path.getsize(path) / 1e9:.1f} GB）: {path}")

    if downloads:
        ensure_download_space(downloads, disk_free, DRIVE_BASE)
        names = ", ".join(item["name"] for item in downloads)
        print(f"Drive に無いので Colab ディスクへ取得します: {names}")

    for item in downloads:
        dest = item["dest"]
        if needs_drive_space(dest, DRIVE_BASE):
            raise RuntimeError(f"モデルは Drive に書き込みません: {dest}")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if removable_incomplete(dest, item["min_bytes"], LOCAL_BASE, DRIVE_BASE):
            print(f"不完全なローカルファイルを消して取り直します: {dest}")
            os.remove(dest)
        print(f"ダウンロード: {item['name']} -> {dest}")
        result = subprocess.run(["wget", "-q", "--show-progress", "-c", "-O", dest, item["url"]])
        if result.returncode != 0 or not file_ok(dest, item["min_bytes"]):
            raise RuntimeError(
                f"ダウンロードに失敗しました: {item['name']}。このセルを再実行すると続きから取得します。"
            )
        print(f"完了: {os.path.getsize(dest) / 1e9:.1f} GB")

    yaml_path = "/content/ComfyUI/extra_model_paths.yaml"
    Path(yaml_path).write_text(extra_model_yaml(DRIVE_BASE, LOCAL_BASE), encoding="utf-8")
    globals()["MODEL_UNET"] = resolved[UNET_FILE]
    globals()["MODEL_TE"] = resolved[TE_FILE]
    globals()["MODEL_VAE"] = resolved[VAE_FILE]
    print(yaml_path)
    print("モデルセル完了。ComfyUI は Drive と Colab ディスクの両方を見ます。")


if not globals().get("_H3_LOAD_ONLY"):
    run_model_setup()
