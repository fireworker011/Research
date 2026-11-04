"""Write the Colab notebooks and the example API workflow."""

from __future__ import annotations

import json
from pathlib import Path

from wan_vace.controls import load_control
from wan_vace.paths import BRANCH, GITHUB_REPO, LORA_LIGHTX2V, RUNTIME_FILES, UPSCALE_NAME
from wan_vace.prompts import load_prompts, with_face_lock
from wan_vace.workflow import build_prompt, fast_options, linked_nodes

ROOT = Path(__file__).resolve().parents[1]
TRIAL = Path(__file__).resolve().parent / "trial"


def _lines(text: str) -> list[str]:
    if not text.endswith("\n"):
        text += "\n"
    return text.splitlines(keepends=True)


def _md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": _lines(text)}


def _code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": _lines(text),
    }


def _notebook(cells: list[dict], accelerator: str, gpu_type: str | None) -> dict:
    colab: dict = {"provenance": []}
    if gpu_type:
        colab["gpuType"] = gpu_type
    return {
        "nbformat": 4,
        "nbformat_minor": 0,
        "metadata": {
            "accelerator": accelerator,
            "colab": colab,
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "cells": cells,
    }


def example_prompt() -> dict:
    control = load_control(TRIAL / "C2_control.json")
    cut = with_face_lock(load_prompts(TRIAL / "trial-01-script_v3.md")["C2"], True)
    built = build_prompt(
        control,
        cut,
        pose_dir="/content/wan-vace-work/C2/pose",
        depth_dir="/content/wan-vace-work/C2/depth",
        face_image="sakura-face-crop.jpg",
        options=fast_options(),
        present_files={LORA_LIGHTX2V, UPSCALE_NAME},
    )
    linked_nodes(built.prompt)
    return built.prompt


def gpu_notebook() -> dict:
    listing = "\n".join(f'    "{name}",' for name in RUNTIME_FILES)
    return _notebook(
        [
            _md(
                """# Wan2.1 VACE 14B（顔参照 + OpenPose + Depth + カメラ）

縦 9:16 の mp4 を、ComfyUI の **Wan2.1 VACE 14B** で C1 から C4 まで作ります。
有料の外部 API は呼びません。このノートは重みをダウンロードしません。

## 起動手順

1. 先にダウンロード用ノートを開く。リンクは `wan_vace/README.md` にあります。
2. そのノートは **CPU** のまま、上から実行する。終わったら最後のセルでランタイムを消す。
3. 顔の画像 `sakura-face-crop.jpg` を Drive の `minimax-h3-comfyui/refs/` に置く。C2 と C4 で使います。
4. このノートを開く。
5. メニュー **ランタイム → ランタイムのタイプを変更 → A100 GPU** を選ぶ。T4 や L4 では止まります。A100 は Colab Pro の一覧に出ます。
6. 上から順にセルを実行する。Drive の接続を求められたら許可する。
7. 起動セルが印刷する URL が `COMFY_URL` です。開いて様子を見ても、閉じたまま待っても同じです。タブは閉じない。
8. 生成セルが終わると、Drive の `minimax-h3-comfyui/outputs/trial-01/` に `C1.mp4` … `C4.mp4` が入ります。
9. 最後のセルを実行してランタイムを消す。消さないと GPU の枠が残ります。

## このノートが選んでいるもの

- **40GB の A100** は fp8 の VACE 14B。A100 には fp8 の専用演算が無いので、速さのためではなく重さが半分になるので使います。**80GB** は fp16 を使います。
- **fast**（初期値）は lightx2v の 4 step LoRA、cfg 1、shift 8。CausVid は同じ系統の古い蒸留で、`MODE` を `causvid` にすると使えます。`quality` は蒸留なし、20 step、cfg 5、shift 8 です。
- **SageAttention** と **torch.compile**（`--fast` の `fp16_accumulation` と `autotune`）は入れば使います。fp8 の行列積は入れません。
- **TeaCache**、**RealESRGAN x2**、**RIFE**（bfloat16）は初期値オフです。生成セルのスイッチで足せます。
- **顔の固定**は、C2 と C4 だけ参照画像を渡し、顔のあたりの制御を少し弱めます。サクラ LoRA と dreamcore LoRA は Drive の `models/loras/` にファイルがあり、strength が 0 より大きいときだけ読みます。ログインや支払いが要る LoRA は落としません。
- OpenPose と Depth の前処理ノードはグラフに入っています。初期値は台本の制御 JSON から描いたガイドです。手元の連番画像があるときだけ `PLATE_DIR` を入れます。
- カメラは VACE の制御画像をずらします。別の Fun Camera モデルは読みません。
- 出力は H.264 の `video/mp4`（`yuv420p`）です。画に文字は入れません。
"""
            ),
            _code(
                """#@title 1) GPU を確認する（A100 以上）
import torch

if not torch.cuda.is_available():
    raise SystemExit("GPU が無い。ランタイムのタイプを A100 に変えて、最初から実行する。")
name = torch.cuda.get_device_name(0)
vram = torch.cuda.get_device_properties(0).total_memory
print("GPU:", name)
print("VRAM GiB:", round(vram / 1024**3, 1))
if not any(token in name.upper() for token in ("A100", "H100", "H200", "B200")):
    raise SystemExit("A100 以上が必要。今は " + name + " 。ランタイムのタイプを A100 に変える。")
"""
            ),
            _code(
                """#@title 2) Google Drive をマウントする
DRIVE_ROOT = "/content/drive/MyDrive/minimax-h3-comfyui"  #@param {type:"string"}
from google.colab import drive

drive.mount("/content/drive")
print("Drive:", DRIVE_ROOT)
"""
            ),
            _code(
                f"""#@title 3) ComfyUI とカスタムノードを入れる
import os
import subprocess
import sys
from pathlib import Path

BRANCH = "{BRANCH}"
REPO = "{GITHUB_REPO}"
COMFY_DIR = Path("/content/ComfyUI")
FILES = [
{listing}
]

if not (COMFY_DIR / "main.py").is_file():
    subprocess.run(["git", "clone", "--depth", "1", "https://github.com/Comfy-Org/ComfyUI.git", str(COMFY_DIR)], check=True)
os.chdir(COMFY_DIR)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"], check=True)

nodes = COMFY_DIR / "custom_nodes"
nodes.mkdir(exist_ok=True)
repos = [
    ("https://github.com/Fannovel16/comfyui_controlnet_aux.git", "comfyui_controlnet_aux"),
    ("https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git", "ComfyUI-VideoHelperSuite"),
    ("https://github.com/Fannovel16/ComfyUI-Frame-Interpolation.git", "ComfyUI-Frame-Interpolation"),
    ("https://github.com/welltop-cn/ComfyUI-TeaCache.git", "ComfyUI-TeaCache"),
]
for url, folder in repos:
    dest = nodes / folder
    if not dest.is_dir():
        subprocess.run(["git", "clone", "--depth", "1", url, str(dest)], check=True)
    req = dest / "requirements.txt"
    if req.is_file():
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(req)], check=True)

for rel in FILES:
    dest = Path("/content") / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://raw.githubusercontent.com/{{REPO}}/{{BRANCH}}/{{rel}}"
    subprocess.run(["wget", "-q", "-O", str(dest), url], check=True)
    if dest.stat().st_size < 10:
        raise SystemExit("取得に失敗した: " + rel)

node_src = Path("/content/wan_vace/custom_nodes/vace_control")
node_dest = nodes / "vace_control"
if node_dest.exists():
    subprocess.run(["rm", "-rf", str(node_dest)], check=True)
subprocess.run(["cp", "-a", str(node_src), str(node_dest)], check=True)
print("ComfyUI とノードを置いた")
"""
            ),
            _code(
                """#@title 4) Drive の重みを繋ぐ（ダウンロードしない）
import importlib.util
import subprocess
import sys
from pathlib import Path

import torch

USE_SAGE = True  #@param {type:"boolean"}
USE_COMPILE = True  #@param {type:"boolean"}
DRIVE_ROOT = "/content/drive/MyDrive/minimax-h3-comfyui"  #@param {type:"string"}
DRIVE_MODELS = "/content/drive/MyDrive/minimax-h3-comfyui/models"

if "/content" not in sys.path:
    sys.path.insert(0, "/content")
from wan_vace.drive_models import link_comfy_models, require_wan
from wan_vace.paths import UNET_FP16, UNET_FP8

vram = torch.cuda.get_device_properties(0).total_memory
UNET_NAME = UNET_FP16 if vram >= 70 * 1024**3 else UNET_FP8
print("unet:", UNET_NAME)
require_wan(Path(DRIVE_MODELS), UNET_NAME)
linked = link_comfy_models(Path("/content/ComfyUI/models"), Path(DRIVE_MODELS))
print("linked", ", ".join(linked))

Path("/content/annotator-tmp").mkdir(exist_ok=True)
annotators = Path(DRIVE_MODELS) / "annotators"
aux = Path("/content/ComfyUI/custom_nodes/comfyui_controlnet_aux")
if aux.is_dir():
    (aux / "config.yaml").write_text(
        "\\n".join(
            [
                "annotator_ckpts_path: " + str(annotators),
                "custom_temp_path: /content/annotator-tmp",
                "USE_SYMLINKS: false",
                "EP_list:",
                "  - CUDAExecutionProvider",
                "  - CPUExecutionProvider",
                "",
            ]
        ),
        encoding="utf-8",
    )
rife_src = Path(DRIVE_MODELS) / "rife" / "rife47.pth"
rife_dir = Path("/content/ComfyUI/custom_nodes/ComfyUI-Frame-Interpolation/ckpts/rife")
if rife_src.is_file():
    rife_dir.mkdir(parents=True, exist_ok=True)
    dest = rife_dir / "rife47.pth"
    if dest.is_symlink() or dest.is_file():
        dest.unlink()
    dest.symlink_to(rife_src)

sage_ok = False
if USE_SAGE:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "sageattention"], check=False)
    sage_ok = importlib.util.find_spec("sageattention") is not None
    if not sage_ok:
        print("SageAttention は入らなかった。SDPA のまま起動する。")

help_text = subprocess.check_output([sys.executable, "main.py", "--help"], cwd="/content/ComfyUI", text=True, stderr=subprocess.STDOUT)
extra = ["--highvram" if vram >= 70 * 1024**3 else "--normalvram"]
if sage_ok and "--use-sage-attention" in help_text:
    extra.append("--use-sage-attention")
if USE_COMPILE and "--fast" in help_text:
    # fp8 行列積は A100 では使わない。
    extra.extend(["--fast", "fp16_accumulation", "autotune"])
Path("/content/wan-vace-launch.txt").write_text("\\n".join([UNET_NAME, *extra]), encoding="utf-8")
print("launch args:", " ".join(extra))
"""
            ),
            _code(
                """#@title 5) ComfyUI を起動して COMFY_URL を印刷する
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

PORT = 8188
LOG_PATH = "/content/comfyui.log"
COMFY_DIR = "/content/ComfyUI"
launch = Path("/content/wan-vace-launch.txt").read_text(encoding="utf-8").splitlines()
UNET_NAME, *extra = launch
DRIVE_ROOT = "/content/drive/MyDrive/minimax-h3-comfyui"

for command in (f"fuser -k {PORT}/tcp", "pkill -f 'python.*main.py'"):
    subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)

env = os.environ.copy()
env["HF_HOME"] = DRIVE_ROOT + "/models/hf-home"
env["HF_HUB_OFFLINE"] = "1"
env["TRANSFORMERS_OFFLINE"] = "1"
env["HF_HUB_DISABLE_TELEMETRY"] = "1"
log_file = open(LOG_PATH, "w", buffering=1)
cmd = [sys.executable, "main.py", "--listen", "0.0.0.0", "--port", str(PORT), "--disable-auto-launch", *extra]
print("starting:", " ".join(cmd))
proc = subprocess.Popen(cmd, cwd=COMFY_DIR, env=env, stdout=log_file, stderr=subprocess.STDOUT, start_new_session=True)

deadline = time.time() + 180
ready = False
while time.time() < deadline:
    if proc.poll() is not None:
        break
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/", timeout=2)
        ready = True
        break
    except Exception:
        time.sleep(2)
if not ready:
    log_file.flush()
    print(Path(LOG_PATH).read_text(encoding="utf-8", errors="replace")[-4000:])
    raise SystemExit("ComfyUI が起動しない。上のログを見る。")

with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/object_info", timeout=60) as response:
    node_info = json.loads(response.read().decode("utf-8"))
needed = (
    "WanVaceToVideo",
    "VHS_VideoCombine",
    "OpenposePreprocessor",
    "DepthAnythingPreprocessor",
    "VacePoseDepthCamera",
    "VaceControlSource",
)
missing = [name for name in needed if name not in node_info]
if missing:
    raise SystemExit("ノードが読めていない: " + ", ".join(missing))

COMFY_URL = None
try:
    from google.colab.output import eval_js
    COMFY_URL = eval_js(f"google.colab.kernel.proxyPort({PORT})")
except Exception as exc:
    print("proxyPort 失敗:", exc)
print("COMFY_URL=" + (COMFY_URL or ""))
try:
    from google.colab import output as colab_output
    colab_output.serve_kernel_port_as_window(PORT)
except Exception as exc:
    print("window:", exc)
print("このセルを止めてもサーバーは残る。次のセルが C1 から C4 を入れる。")
"""
            ),
            _code(
                """#@title 6) C1 から C4 を入れて Drive に mp4 を書く
MODE = "fast"  #@param ["fast", "quality", "causvid"]
WIDTH = 576  #@param {type:"integer"}
HEIGHT = 1024  #@param {type:"integer"}
SEED = 1  #@param {type:"integer"}
USE_TEACACHE = False  #@param {type:"boolean"}
USE_UPSCALE = False  #@param {type:"boolean"}
USE_RIFE = False  #@param {type:"boolean"}
FACE_CONSISTENCY = True  #@param {type:"boolean"}
FACE_PROTECT = 0.35  #@param {type:"number"}
SAKURA_STRENGTH = 0.0  #@param {type:"number"}
STYLE_STRENGTH = 0.0  #@param {type:"number"}
PLATE_DIR = ""  #@param {type:"string"}
FACE_REF = "/content/drive/MyDrive/minimax-h3-comfyui/refs/sakura-face-crop.jpg"  #@param {type:"string"}
DRIVE_MODELS = "/content/drive/MyDrive/minimax-h3-comfyui/models"
DRIVE_OUT = "/content/drive/MyDrive/minimax-h3-comfyui/outputs/trial-01"

import json
import sys
import urllib.request
from pathlib import Path

if "/content" not in sys.path:
    sys.path.insert(0, "/content")
from wan_vace.queue import queue_cuts
from wan_vace.workflow import describe, options_for_mode

if USE_TEACACHE or USE_RIFE:
    with urllib.request.urlopen("http://127.0.0.1:8188/object_info", timeout=60) as response:
        node_info = json.loads(response.read().decode("utf-8"))
    if USE_TEACACHE and "TeaCache" not in node_info:
        raise SystemExit("TeaCache ノードが無い。セル3のインストールを見る。")
    if USE_RIFE and "RIFE VFI" not in node_info:
        raise SystemExit("RIFE ノードが無い。セル3のインストールを見る。")

UNET_NAME = Path("/content/wan-vace-launch.txt").read_text(encoding="utf-8").splitlines()[0]
options = options_for_mode(
    MODE,
    width=int(WIDTH),
    height=int(HEIGHT),
    seed=int(SEED),
    unet_name=UNET_NAME,
    teacache=bool(USE_TEACACHE),
    upscale=bool(USE_UPSCALE),
    rife=bool(USE_RIFE),
    face_consistency=bool(FACE_CONSISTENCY),
    face_protect=float(FACE_PROTECT),
    sakura_strength=float(SAKURA_STRENGTH),
    style_strength=float(STYLE_STRENGTH),
)
for line in describe(options):
    print(line)
written = queue_cuts(
    "http://127.0.0.1:8188",
    Path("/content/wan_vace/trial/trial-01-script_v3.md"),
    Path("/content/wan_vace/trial"),
    Path(FACE_REF),
    Path("/content/wan-vace-work"),
    Path("/content/ComfyUI/output"),
    Path("/content/ComfyUI/input"),
    Path(DRIVE_OUT),
    Path(DRIVE_MODELS),
    options,
    plate_dir=PLATE_DIR or None,
)
for path in written:
    print("WROTE", path)
"""
            ),
            _md(
                """## 最後にランタイムを消す

上のセルが `WROTE .../C4.mp4` まで印刷してから、次のセルを実行する。
このセルは Colab のランタイムを削除する。
"""
            ),
            _code(
                """#@title 7) ランタイムを削除する
from google.colab import runtime

runtime.unassign()
"""
            ),
        ],
        accelerator="GPU",
        gpu_type="A100",
    )


def cpu_notebook() -> dict:
    return _notebook(
        [
            _md(
                """# Wan2.1 VACE 14B の重みを Drive に置く（CPU・1回だけ）

このノートだけが重みを落とします。生成用ノートは Drive を読むだけで、実行中にダウンロードしません。

## 手順

1. メニュー **ランタイム → ランタイムのタイプを変更 → CPU**（ハードウェアアクセラレータは「なし」）にする。GPU のまま実行すると止まります。
2. 上から順にセルを実行する。Drive の接続を求められたら許可する。
3. 終わるまでタブを閉じない。fp16 と fp8 を合わせると大きいです。既に同じ大きさのファイルがあるものは飛ばします。
4. 終わったら最後のセルでランタイムを消す。
5. `minimax-h3-comfyui/refs/sakura-face-crop.jpg` を自分で置く。このノートは顔画像も LoRA も落としません。
6. そのあと生成用ノートを A100 で開く。

置く場所は `マイドライブ/minimax-h3-comfyui/models/` です。
"""
            ),
            _code(
                """#@title 1) CPU であることを確認する
import shutil
import subprocess

nvidia = shutil.which("nvidia-smi")
if nvidia:
    result = subprocess.run([nvidia, "-L"], capture_output=True, text=True)
    if result.returncode == 0 and "GPU" in result.stdout.upper():
        raise SystemExit("GPU ランタイムになっている。タイプを CPU に変えて、最初から実行する。")
print("CPU のまま進む")
"""
            ),
            _code(
                """#@title 2) Google Drive をマウントする
DRIVE_MODELS = "/content/drive/MyDrive/minimax-h3-comfyui/models"  #@param {type:"string"}
from google.colab import drive

drive.mount("/content/drive")
print(DRIVE_MODELS)
"""
            ),
            _code(
                f"""#@title 3) 公開の重みを Drive に置く
# このノートだけが huggingface.co と GitHub releases から重みを落とす。GPUノートは落とさない。
import subprocess
import sys
from pathlib import Path

BRANCH = "{BRANCH}"
REPO = "{GITHUB_REPO}"
DRIVE_MODELS = "/content/drive/MyDrive/minimax-h3-comfyui/models"
dest = Path("/content/wan_vace/download_manifest.py")
dest.parent.mkdir(parents=True, exist_ok=True)
url = f"https://raw.githubusercontent.com/{{REPO}}/{{BRANCH}}/wan_vace/download_manifest.py"
subprocess.run(["wget", "-q", "-O", str(dest), url], check=True)
if "/content" not in sys.path:
    sys.path.insert(0, "/content")
from wan_vace.download_manifest import download_all

download_all(Path(DRIVE_MODELS))
print("Drive に置いた:", DRIVE_MODELS)
"""
            ),
            _md("ダウンロードが終わってから次のセルを実行すると、この CPU ランタイムが消えます。"),
            _code(
                """#@title 4) ランタイムを削除する
from google.colab import runtime

runtime.unassign()
"""
            ),
        ],
        accelerator="CPU",
        gpu_type=None,
    )


def main() -> None:
    (ROOT / "wan21_vace_colab.ipynb").write_text(
        json.dumps(gpu_notebook(), ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    (ROOT / "wan21_vace_download_colab.ipynb").write_text(
        json.dumps(cpu_notebook(), ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    example = ROOT / "wan_vace" / "workflows" / "wan21_vace_14b_api.json"
    example.parent.mkdir(parents=True, exist_ok=True)
    example.write_text(json.dumps(example_prompt(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote notebooks and", example)


if __name__ == "__main__":
    main()
