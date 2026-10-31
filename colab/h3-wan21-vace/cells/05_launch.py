import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

if not globals().get("GPU_OK"):
    raise RuntimeError("GPU チェックを通過していません。最初のセルから実行してください。")
if not os.path.isfile("/content/ComfyUI/extra_model_paths.yaml"):
    raise RuntimeError("モデルのセルが未完了です。extra_model_paths.yaml がありません。")
if not os.path.isfile("/content/ComfyUI/custom_nodes/h3_load_frames.py"):
    raise RuntimeError("セットアップセルが未完了です。フレーム読み込みノードがありません。")

LOG_PATH = "/content/comfyui_vace.log"


def comfy_is_up():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


if comfy_is_up():
    print("ComfyUI は既に起動しています。")
else:
    COMFY_LOG = open(LOG_PATH, "w", encoding="utf-8")
    COMFY_PROC = subprocess.Popen(
        [sys.executable, "main.py", "--listen", "127.0.0.1", "--port", "8188"],
        cwd="/content/ComfyUI",
        stdout=COMFY_LOG,
        stderr=subprocess.STDOUT,
    )
    print("ComfyUI を起動しています。")
    ready = False
    for _ in range(150):
        if COMFY_PROC.poll() is not None:
            break
        if comfy_is_up():
            ready = True
            break
        time.sleep(2)
        print(".", end="", flush=True)
    print()
    if not ready:
        COMFY_LOG.flush()
        text = Path(LOG_PATH).read_text(encoding="utf-8", errors="replace")
        print(text[-2000:])
        raise RuntimeError("ComfyUI が起動しませんでした。上のログを確認してください。")
    print("ComfyUI 起動完了")
