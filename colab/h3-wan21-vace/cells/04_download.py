import os
import subprocess
from pathlib import Path

if not globals().get("GPU_OK"):
    raise RuntimeError("GPU チェックを通過していません。最初のセルから実行してください。")
if not os.path.isdir("/content/ComfyUI"):
    raise RuntimeError("セットアップセルを先に実行してください。")

DRIVE_BASE = "/content/drive/MyDrive/ComfyUI_models"
HF = "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main"
UNET_FILE = "wan2.1_vace_14B_fp16.safetensors"
TE_FILE = "umt5_xxl_fp8_e4m3fn_scaled.safetensors"
VAE_FILE = "wan_2.1_vae.safetensors"

FILES = [
    {
        "name": UNET_FILE,
        "url": f"{HF}/split_files/diffusion_models/{UNET_FILE}",
        "dest": f"{DRIVE_BASE}/diffusion_models/{UNET_FILE}",
        "alts": [],
        "min_bytes": 32_000_000_000,
    },
    {
        "name": TE_FILE,
        "url": f"{HF}/split_files/text_encoders/{TE_FILE}",
        "dest": f"{DRIVE_BASE}/text_encoders/{TE_FILE}",
        "alts": [f"{DRIVE_BASE}/clip/{TE_FILE}"],
        "min_bytes": 6_400_000_000,
    },
    {
        "name": VAE_FILE,
        "url": f"{HF}/split_files/vae/{VAE_FILE}",
        "dest": f"{DRIVE_BASE}/vae/{VAE_FILE}",
        "alts": [],
        "min_bytes": 240_000_000,
    },
]


def file_ok(path, min_bytes):
    return os.path.isfile(path) and os.path.getsize(path) >= min_bytes


resolved = {}
to_download = []
for item in FILES:
    found = None
    for path in [item["dest"], *item["alts"]]:
        if file_ok(path, item["min_bytes"]):
            found = path
            break
    if found:
        print(f"スキップ（Drive に既存 {os.path.getsize(found) / 1e9:.1f} GB）: {found}")
        resolved[item["name"]] = found
    else:
        to_download.append(item)

if to_download:
    stat = os.statvfs("/content/drive/MyDrive")
    free = stat.f_bavail * stat.f_frsize
    need = sum(item["min_bytes"] for item in to_download)
    print(f"Drive の空き目安: {free / 1e9:.1f} GB / ダウンロード目安: {need / 1e9:.1f} GB")
    if free < need:
        raise RuntimeError(
            "Drive の空きが足りない目安です。モデルは約 39GB あります。"
            "空きを作ってから、このセルを再実行してください。"
        )

for item in to_download:
    dest = item["dest"]
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.isfile(dest) and not file_ok(dest, item["min_bytes"]):
        print(f"不完全なファイルを消して取り直します: {dest}")
        os.remove(dest)
    print(f"ダウンロード: {item['name']}")
    result = subprocess.run(["wget", "-q", "--show-progress", "-c", "-O", dest, item["url"]])
    if result.returncode != 0 or not file_ok(dest, item["min_bytes"]):
        raise RuntimeError(
            f"ダウンロードに失敗しました: {item['name']}。このセルを再実行すると続きから取得します。"
        )
    resolved[item["name"]] = dest
    print(f"完了: {os.path.getsize(dest) / 1e9:.1f} GB")


def rel_folder(path):
    return os.path.relpath(os.path.dirname(path), DRIVE_BASE).replace("\\", "/")


yaml_path = "/content/ComfyUI/extra_model_paths.yaml"
unet_folder = rel_folder(resolved[UNET_FILE])
yaml_text = (
    "h3_vace:\n"
    f"    base_path: {DRIVE_BASE}\n"
    f"    diffusion_models: {unet_folder}/\n"
    f"    unet: {unet_folder}/\n"
    f"    text_encoders: {rel_folder(resolved[TE_FILE])}/\n"
    f"    vae: {rel_folder(resolved[VAE_FILE])}/\n"
    "    clip: clip/\n"
)
Path(yaml_path).write_text(yaml_text, encoding="utf-8")
MODEL_UNET = resolved[UNET_FILE]
MODEL_TE = resolved[TE_FILE]
MODEL_VAE = resolved[VAE_FILE]
print(yaml_path)
print("モデルセル完了。ComfyUI は次のセルで起動します。")
