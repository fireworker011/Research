#@title 5b) span を1本だけ投入（既定は span-01）
PLAN = ""  #@param {type:"string"}
SHEET = "/content/drive/MyDrive/動画倉庫/ネタBOX/1024-sheet.json"  #@param {type:"string"}
SPAN = 1  #@param {type:"integer"}
OUT_DIR = "/content/drive/MyDrive/動画倉庫/00_確認待ち/2026-10-26_H3カイロ_テスト"  #@param {type:"string"}
SEED = 1024  #@param {type:"integer"}
PORT = 8188

import importlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from google.colab import drive

print("このセルは Comfy の /prompt に1本入れる。UI の生成ボタンは押さない。")

if not os.path.isdir("/content/drive/MyDrive"):
    print("Drive の接続画面では ys73497349@gmail.com を選ぶ。")
    drive.mount("/content/drive")

BRANCH = "cursor/h3-live-remake-on-minimax-80fd"
RAW = f"https://raw.githubusercontent.com/fireworker011/Research/{BRANCH}/h3"
pkg = Path("/content/h3pkg")
pkg.mkdir(exist_ok=True)
(pkg / "__init__.py").write_text("", encoding="utf-8")
for name in ("live_remake.py", "span_queue.py"):
    subprocess.run(["wget", "-q", "-O", str(pkg / name), f"{RAW}/{name}"], check=True)
if "/content" not in sys.path:
    sys.path.insert(0, "/content")
importlib.invalidate_caches()
for mod in ("h3pkg.live_remake", "h3pkg.span_queue"):
    sys.modules.pop(mod, None)
from h3pkg.live_remake import build_remake_plan, load_sheet
from h3pkg.span_queue import (
    build_ref2va_prompt,
    finished_history,
    history_video,
    mux_source_audio_argv,
    output_paths,
    post_prompt,
    select_span,
    video_vae_name,
)

if PLAN:
    plan = json.loads(Path(PLAN).read_text(encoding="utf-8"))
else:
    if not SHEET:
        raise SystemExit("PLAN か SHEET のパスを入れる。")
    plan = build_remake_plan(load_sheet(SHEET))
span = select_span(plan, int(SPAN))
os.makedirs(OUT_DIR, exist_ok=True)
video_out, audio_out = output_paths(OUT_DIR, int(SPAN))

base = f"http://127.0.0.1:{PORT}"
try:
    urllib.request.urlopen(base + "/system_stats", timeout=5)
except Exception as exc:
    raise SystemExit(f"ComfyUI が {PORT} で動いていない。先に起動セルを実行する。{exc}") from exc

comfy = Path("/content/ComfyUI")
vae_dir = comfy / "models" / "vae"
present = [item.name for item in vae_dir.glob("*.safetensors")] if vae_dir.is_dir() else []
vae = video_vae_name(plan, present)
if not (vae_dir / vae).is_file():
    raise SystemExit(f"動画 VAE が Drive の models/vae に無い: {vae}。落とさない。")

input_dir = comfy / "input"
input_dir.mkdir(parents=True, exist_ok=True)
image_files = []
for picture in span["pictures"]:
    src = Path(picture["path"])
    if not src.is_file():
        raise SystemExit(f"静止画が無い: {src}")
    shutil.copy2(src, input_dir / src.name)
    image_files.append(src.name)
    print("ref", picture["label"], src.name)

ref_path = input_dir / f"span-{int(SPAN):02d}-ref.mp4"
argv = list(span["conform_argv"])
argv[-1] = str(ref_path)
subprocess.run(argv, check=True)
counted = subprocess.check_output(
    [
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(ref_path),
    ],
    text=True,
).strip()
print("参照動画のコマ", counted, "要求", span["length"])
if counted != str(span["length"]):
    raise SystemExit(f"参照動画が {span['length']} コマではない: {counted}")

prompt = build_ref2va_prompt(
    plan,
    span,
    image_files=image_files,
    video_file=ref_path.name,
    video_vae=vae,
    seed=int(SEED),
)
prompt_id = post_prompt(base, prompt)
print("prompt_id", prompt_id, "steps", plan["model"]["steps"], "length", span["length"])

deadline = time.time() + 60 * 60
history = None
while time.time() < deadline:
    try:
        with urllib.request.urlopen(f"{base}/history/{prompt_id}", timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception:
        time.sleep(15)
        continue
    history = finished_history(body, prompt_id)
    if history is not None:
        break
    time.sleep(15)
if history is None:
    raise SystemExit("1時間待っても完了しない。/content/comfyui.log を見る。")

saved = history_video(history)
if not saved:
    raise SystemExit("履歴に mp4 が無い。")
found = list((comfy / "output").rglob(saved))
if not found:
    raise SystemExit(f"出力ファイルが無い: {saved}")
video_out, audio_out = output_paths(OUT_DIR, int(SPAN))
shutil.copy2(found[0], video_out)
subprocess.run(
    mux_source_audio_argv(str(video_out), plan["inputs"]["video"], float(span["start_s"]), int(span["frames"]), str(audio_out)),
    check=True,
)
print("WROTE", video_out)
print("WROTE", audio_out)
print("生成ボタンは押していない。")
