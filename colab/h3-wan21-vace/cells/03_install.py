import os
import subprocess
import sys
from pathlib import Path

from google.colab import drive

if not globals().get("GPU_OK"):
    raise RuntimeError(
        "GPU チェックを通過していません。最初のセルから順に実行してください。"
        "A100 未満の GPU ではここで止めます。"
    )

print("Google Drive をマウントします。")
drive.mount("/content/drive")

DRIVE_BASE = "/content/drive/MyDrive/ComfyUI_models"
WORK_ROOT = "/content/drive/MyDrive/ComfyUI_vace_h3"
FACE_DIR = WORK_ROOT + "/input"
CONTROL_DIR = WORK_ROOT + "/input/controls"
OUTPUT_ROOT = WORK_ROOT + "/output"
COMFY_DIR = "/content/ComfyUI"

for folder in (
    f"{DRIVE_BASE}/diffusion_models",
    f"{DRIVE_BASE}/text_encoders",
    f"{DRIVE_BASE}/clip",
    f"{DRIVE_BASE}/vae",
    FACE_DIR,
    CONTROL_DIR,
    OUTPUT_ROOT,
):
    os.makedirs(folder, exist_ok=True)

clone_env = os.environ.copy()
clone_env["GIT_TERMINAL_PROMPT"] = "0"
if not os.path.isdir(COMFY_DIR + "/.git"):
    print("ComfyUI を取得します。")
    subprocess.run(
        ["git", "clone", "--depth", "1", "https://github.com/comfyanonymous/ComfyUI.git", COMFY_DIR],
        check=True,
        env=clone_env,
    )
else:
    print("ComfyUI を更新します。")
    updated = subprocess.run(["git", "-C", COMFY_DIR, "pull", "--ff-only"], env=clone_env)
    if updated.returncode != 0:
        print("ComfyUI の更新をスキップし、既存の取得物で続行します。")

subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q", "-r", COMFY_DIR + "/requirements.txt"],
    check=True,
)
subprocess.run(["apt-get", "install", "-y", "-qq", "ffmpeg"], check=False)

node_dir = Path(COMFY_DIR) / "custom_nodes"
node_dir.mkdir(parents=True, exist_ok=True)
node_path = node_dir / "h3_load_frames.py"
node_path.write_text(NODE_SOURCE, encoding="utf-8")
print(f"フレーム読み込みノード: {node_path}")
print(f"モデル置き場: {DRIVE_BASE}")
print(f"顔画像: {FACE_DIR}/face_ref.png （jpg / webp も可）")
print(f"制御 JSON: {CONTROL_DIR}")
print(f"出力: {OUTPUT_ROOT}")
print("セットアップセル完了")
