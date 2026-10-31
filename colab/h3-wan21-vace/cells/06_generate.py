import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

if not globals().get("GPU_OK"):
    raise RuntimeError("GPU チェックを通過していません。最初のセルから実行してください。")
for _name in (
    "list_cuts",
    "render_cut",
    "generation_geometry",
    "build_prompts",
    "ffmpeg_vf",
    "ffmpeg_duration_args",
    "ffmpeg_sequence_cmd",
    "copy_control_json",
    "find_face_reference",
    "safe_cut_id",
    "summarize_cut",
    "raw_frame_count",
    "letterbox_face",
    "sampler_seed",
    "EXPORT_WIDTH",
    "EXPORT_HEIGHT",
):
    if _name not in globals():
        raise RuntimeError("制御 JSON のセルが未実行です。上から順に実行してください。")
if "FACE_DIR" not in globals() or "CONTROL_DIR" not in globals() or "OUTPUT_ROOT" not in globals():
    raise RuntimeError("セットアップセルが未実行です。")
if not os.path.isdir("/content/ComfyUI"):
    raise RuntimeError("ComfyUI がありません。セットアップセルを実行してください。")

UNET_FILE = "wan2.1_vace_14B_fp16.safetensors"
TE_FILE = "umt5_xxl_fp8_e4m3fn_scaled.safetensors"
VAE_FILE = "wan_2.1_vae.safetensors"
# 蒸留 LoRA は同梱しない。Wan 14B を uni_pc / shift 8 で回すときの通常値。
STEPS = 20
CFG = 5.0
SHIFT = 8.0
POLL_SECONDS = 10
CUT_TIMEOUT_SECONDS = 3 * 60 * 60
# None のときは VRAM で決める。A100 80GB 以上と同じ 720x1280 にするなら (720, 1280)。
GEN_SIZE_OVERRIDE = None

GENERATION_DONE = False
OUTPUT_MP4S = []
OUTPUT_JSONS = []


def comfy_call(path, payload=None, timeout=120):
    url = "http://127.0.0.1:8188" + path
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if data is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ComfyUI {path} -> {exc.code}: {body}") from exc


def pack_inputs(info, class_type, values):
    spec = info[class_type]["input"]
    required = set(spec.get("required", {}))
    optional = set(spec.get("optional", {}))
    allowed = required | optional
    missing = sorted(key for key in required if key not in values)
    if missing:
        raise RuntimeError(f"{class_type} に足りない入力: {missing}")
    return {key: value for key, value in values.items() if key in allowed}


def build_prompt(info, frame_dir, length, width, height, positive, negative, seed, prefix):
    vace_spec = info["WanVaceToVideo"]["input"]
    vace_allowed = set(vace_spec.get("required", {})) | set(vace_spec.get("optional", {}))
    for key in ("control_video", "reference_image"):
        if key not in vace_allowed:
            raise RuntimeError(f"WanVaceToVideo に {key} がありません。ComfyUI を更新してください。")
    return {
        "unet": {
            "class_type": "UNETLoader",
            "inputs": pack_inputs(info, "UNETLoader", {
                "unet_name": UNET_FILE,
                "weight_dtype": "default",
            }),
        },
        "clip": {
            "class_type": "CLIPLoader",
            "inputs": pack_inputs(info, "CLIPLoader", {
                "clip_name": TE_FILE,
                "type": "wan",
                "device": "default",
            }),
        },
        "vae": {
            "class_type": "VAELoader",
            "inputs": pack_inputs(info, "VAELoader", {"vae_name": VAE_FILE}),
        },
        "pos": {
            "class_type": "CLIPTextEncode",
            "inputs": pack_inputs(info, "CLIPTextEncode", {"text": positive, "clip": ["clip", 0]}),
        },
        "neg": {
            "class_type": "CLIPTextEncode",
            "inputs": pack_inputs(info, "CLIPTextEncode", {"text": negative, "clip": ["clip", 0]}),
        },
        "face": {
            "class_type": "LoadImage",
            "inputs": pack_inputs(info, "LoadImage", {"image": "face_ref.png"}),
        },
        "frames": {
            "class_type": "H3LoadFrameDir",
            "inputs": pack_inputs(info, "H3LoadFrameDir", {"directory": frame_dir}),
        },
        "vace": {
            "class_type": "WanVaceToVideo",
            "inputs": pack_inputs(info, "WanVaceToVideo", {
                "positive": ["pos", 0],
                "negative": ["neg", 0],
                "vae": ["vae", 0],
                "width": width,
                "height": height,
                "length": length,
                "batch_size": 1,
                "strength": 1.0,
                "control_video": ["frames", 0],
                "reference_image": ["face", 0],
            }),
        },
        "shift": {
            "class_type": "ModelSamplingSD3",
            "inputs": pack_inputs(info, "ModelSamplingSD3", {"model": ["unet", 0], "shift": SHIFT}),
        },
        "sample": {
            "class_type": "KSampler",
            "inputs": pack_inputs(info, "KSampler", {
                "model": ["shift", 0],
                "positive": ["vace", 0],
                "negative": ["vace", 1],
                "latent_image": ["vace", 2],
                "seed": seed,
                "steps": STEPS,
                "cfg": CFG,
                "sampler_name": "uni_pc",
                "scheduler": "simple",
                "denoise": 1.0,
                "control_after_generate": "fixed",
            }),
        },
        "trim": {
            "class_type": "TrimVideoLatent",
            "inputs": pack_inputs(info, "TrimVideoLatent", {
                "samples": ["sample", 0],
                "trim_amount": ["vace", 3],
            }),
        },
        "decode": {
            "class_type": "VAEDecodeTiled",
            "inputs": pack_inputs(info, "VAEDecodeTiled", {
                "samples": ["trim", 0],
                "vae": ["vae", 0],
                "tile_size": 512,
                "overlap": 64,
                "temporal_size": 64,
                "temporal_overlap": 4,
            }),
        },
        "save": {
            "class_type": "SaveImage",
            "inputs": pack_inputs(info, "SaveImage", {
                "images": ["decode", 0],
                "filename_prefix": prefix,
            }),
        },
    }


def wait_for_cut(prompt_id, cut_id):
    started = time.time()
    announced = -1
    while True:
        elapsed = time.time() - started
        if elapsed > CUT_TIMEOUT_SECONDS:
            raise RuntimeError(f"{cut_id} が制限時間を超えました。ランタイムは消しません。")
        hist = comfy_call(f"/history/{prompt_id}")
        if prompt_id in hist:
            item = hist[prompt_id]
            status = item.get("status") or {}
            if status.get("status_str") == "error":
                detail = json.dumps(status.get("messages"), ensure_ascii=False)[:4000]
                lowered = detail.lower()
                if "out of memory" in lowered or "allocation" in lowered:
                    print(
                        "VRAM 不足です。GEN_SIZE_OVERRIDE を None のままにするか、"
                        "より大きい GPU で (720, 1280) を指定してください。"
                    )
                raise RuntimeError(f"{cut_id} の生成に失敗しました: {detail}")
            if status.get("completed") or item.get("outputs"):
                return item
        minute = int(elapsed // 60)
        if minute != announced:
            print(f"{cut_id}: 生成中 {minute} 分")
            announced = minute
        time.sleep(POLL_SECONDS)


def export_mp4(image_paths, fps, duration_s, geo, dest):
    seq = Path("/content/vace_work/seq")
    if seq.exists():
        shutil.rmtree(seq)
    seq.mkdir(parents=True)
    for index, path in enumerate(image_paths):
        shutil.copyfile(path, seq / f"frame_{index:04d}.png")
    cmd = ffmpeg_sequence_cmd(
        seq / "frame_%04d.png",
        len(image_paths),
        fps,
        duration_s,
        geo,
        dest,
    )
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg に失敗しました: {result.stderr[-2000:]}")
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0:s=x",
            str(dest),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    got = probe.stdout.strip()
    expect = f"{EXPORT_WIDTH}x{EXPORT_HEIGHT}"
    if got != expect:
        raise RuntimeError(f"書き出しサイズが {got} です。{expect} が必要です。")


if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
    raise RuntimeError("ffmpeg がありません。セットアップセルを再実行してください。")

try:
    comfy_call("/system_stats", timeout=5)
except Exception as exc:
    raise RuntimeError("ComfyUI が起動していません。起動セルを実行してください。") from exc

info = comfy_call("/object_info")
for node_name in (
    "UNETLoader",
    "CLIPLoader",
    "VAELoader",
    "CLIPTextEncode",
    "LoadImage",
    "WanVaceToVideo",
    "ModelSamplingSD3",
    "KSampler",
    "TrimVideoLatent",
    "VAEDecodeTiled",
    "SaveImage",
    "H3LoadFrameDir",
):
    if node_name not in info:
        raise RuntimeError(f"ノードがありません: {node_name}。セットアップのあとランタイムを入れ直してください。")

geo = generation_geometry(_GPU_VRAM, GEN_SIZE_OVERRIDE)
print(
    f"生成 {geo['width']}x{geo['height']} / 書き出し {geo['export_width']}x{geo['export_height']}"
    f"（9:16{'、そのまま' if geo['native'] else '、480p をパッド'}）"
)
face_path = find_face_reference(FACE_DIR)
boxed = letterbox_face(Image.open(face_path), geo["width"], geo["height"])
os.makedirs("/content/ComfyUI/input", exist_ok=True)
boxed.save("/content/ComfyUI/input/face_ref.png")
print(f"顔参照: {face_path}")

cuts = list_cuts(CONTROL_DIR)
run_id = time.strftime("%Y%m%d-%H%M%S")
run_dir = Path(OUTPUT_ROOT) / run_id
run_dir.mkdir(parents=True, exist_ok=True)
print(f"出力フォルダ: {run_dir}")

for cut in cuts:
    cut_id = safe_cut_id(cut["cut"])
    count = render_cut(
        cut,
        f"/content/vace_work/{cut_id}/frames",
        geo["width"],
        geo["height"],
    )["count"]
    raw = raw_frame_count(cut["duration_s"], cut["fps"])
    print(summarize_cut(cut, count))
    if count != raw:
        print(f"注意: {raw} フレームを VACE の制約で {count} フレームに揃えます（4n+1、最大 81）。")
    positive, negative = build_prompts(cut["data"])
    print(positive)
    prefix = f"h3_{run_id}_{cut_id}"
    out_root = Path("/content/ComfyUI/output")
    out_root.mkdir(parents=True, exist_ok=True)
    for old in out_root.glob(prefix + "*"):
        if old.is_file():
            old.unlink()
    prompt = build_prompt(
        info,
        f"/content/vace_work/{cut_id}/frames",
        count,
        geo["width"],
        geo["height"],
        positive,
        negative,
        sampler_seed(cut),
        prefix,
    )
    queued = comfy_call("/prompt", {"prompt": prompt})
    if queued.get("node_errors") or "prompt_id" not in queued:
        raise RuntimeError(json.dumps(queued, ensure_ascii=False)[:4000])
    item = wait_for_cut(queued["prompt_id"], cut_id)
    images = []
    for node_out in item.get("outputs", {}).values():
        images.extend(node_out.get("images") or [])
    paths = []
    for image in images:
        root = "/content/ComfyUI/temp" if image.get("type") == "temp" else "/content/ComfyUI/output"
        sub = image.get("subfolder") or ""
        paths.append(os.path.join(root, sub, image["filename"]))
    paths = [path for path in paths if os.path.isfile(path)]
    paths.sort()
    if len(paths) != count:
        raise RuntimeError(f"{cut_id}: フレーム数が {len(paths)} でした。{count} を期待しています。")
    local_mp4 = Path(f"/content/vace_work/{cut_id}.mp4")
    export_mp4(paths, cut["fps"], cut["duration_s"], geo, local_mp4)
    dest_mp4 = run_dir / f"{cut_id}.mp4"
    shutil.copyfile(local_mp4, dest_mp4)
    dest_json = copy_control_json(cut, run_dir)
    if dest_mp4.stat().st_size <= 0 or dest_json.stat().st_size <= 0:
        raise RuntimeError(f"{cut_id}: 出力が空です")
    OUTPUT_MP4S.append(str(dest_mp4))
    OUTPUT_JSONS.append(str(dest_json))
    print(f"書き出し: {dest_mp4}")
    print(f"制御 JSON: {dest_json}")
    try:
        comfy_call("/free", {"unload_models": False, "free_memory": True})
    except Exception as exc:
        print(f"メモリ解放をスキップ: {exc}")

if len(OUTPUT_MP4S) != len(cuts) or len(OUTPUT_JSONS) != len(cuts):
    raise RuntimeError("出力本数がカット数と一致しません。")
GENERATION_DONE = True
print("全カットの mp4 と制御 JSON を Drive に書きました。")
print("次のセルでランタイムを削除します。")
