import json
import os
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

try:
    from google.colab import drive as colab_drive
    from google.colab import runtime as colab_runtime
except ImportError:
    colab_drive = None
    colab_runtime = None

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
RUN_DIR = None
IDLE_SECONDS = 30 * 60
_IDLE_TIMER = None
_IDLE_LOCK = threading.Lock()
_RUNTIME_RELEASED = False


def cancel_idle_timer():
    global _IDLE_TIMER
    with _IDLE_LOCK:
        if _IDLE_TIMER is not None:
            _IDLE_TIMER.cancel()
            _IDLE_TIMER = None


def release_runtime():
    global _RUNTIME_RELEASED
    with _IDLE_LOCK:
        if _RUNTIME_RELEASED:
            return
        _RUNTIME_RELEASED = True
    cancel_idle_timer()
    if colab_drive is None or colab_runtime is None:
        raise RuntimeError(
            "google.colab がないため、Drive の flush とランタイム削除ができません。"
        )
    try:
        colab_drive.flush_and_unmount()
        print("Drive を flush してアンマウントしました。", flush=True)
    except Exception as exc:
        print(f"Drive の flush に失敗しました: {exc}", flush=True)
    print("ランタイムを切断して削除します。", flush=True)
    colab_runtime.unassign()


def idle_disconnect():
    print("30分操作が無いので、Drive を flush してランタイムを削除します。", flush=True)
    release_runtime()


def arm_idle_timer(seconds=None, callback=None):
    global _IDLE_TIMER
    if seconds is None:
        seconds = IDLE_SECONDS
    seconds = float(seconds)
    if seconds < 0:
        raise ValueError("待機秒数は 0 以上です")
    action = idle_disconnect if callback is None else callback
    with _IDLE_LOCK:
        if _IDLE_TIMER is not None:
            _IDLE_TIMER.cancel()
        timer = threading.Timer(seconds, action)
        timer.daemon = True
        timer.start()
        _IDLE_TIMER = timer
    print(
        f"QA のためランタイムを最大 {seconds / 60:.0f} 分残します。"
        "再生成で延長し、合格なら切断セルを実行してください。",
        flush=True,
    )


CAT_REF_URL = (
    "https://raw.githubusercontent.com/fireworker011/Research/"
    "cursor/wan21-vace-14b-colab-702e/colab/h3-wan21-vace/controls/cat_ref.png"
)


def ensure_cat_reference(directory, needed=True):
    if not needed:
        return find_optional_cat_reference(directory)
    try:
        return find_cat_reference(directory)
    except FileNotFoundError:
        dest = Path(directory) / "cat_ref.png"
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"猫参照が無いので取得します: {dest}")
        result = subprocess.run(["wget", "-q", "-O", str(dest), CAT_REF_URL])
        if result.returncode != 0 or not dest.is_file() or dest.stat().st_size < 1000:
            raise FileNotFoundError(
                "猫の参照画像がありません。"
                f" {directory}/cat_ref.png に置いてください。"
            ) from None
        return dest


def publish_file(src, dest):
    src = Path(src)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() != dest.resolve():
        shutil.copyfile(src, dest)
    with dest.open("rb") as handle:
        os.fsync(handle.fileno())
    dir_fd = None
    try:
        dir_fd = os.open(dest.parent, os.O_RDONLY)
        os.fsync(dir_fd)
    except OSError as exc:
        print(f"フォルダの fsync をスキップ: {exc}")
    finally:
        if dir_fd is not None:
            os.close(dir_fd)
    return dest


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


def validate_prompt_graph(graph):
    vace = graph["vace"]["inputs"]
    if vace.get("control_video") != ["frames", 0]:
        raise RuntimeError("control_video はフレーム読み込みだけに繋ぎます。")
    if vace.get("control_masks") != ["frames", 1]:
        raise RuntimeError("control_masks はマスク出力だけに繋ぎます。")
    if vace.get("reference_image") != ["ref", 0]:
        raise RuntimeError("reference_image は参照画像だけに繋ぎます。")
    if graph["sample"]["inputs"].get("latent_image") != ["vace", 2]:
        raise RuntimeError("サンプラーの初期潜在は VACE の潜在だけです。")
    if graph["trim"]["inputs"].get("samples") != ["sample", 0]:
        raise RuntimeError("トリムするのはサンプラー出力だけです。")
    if graph["decode"]["inputs"].get("samples") != ["trim", 0]:
        raise RuntimeError("VAE はサンプラーの出力だけを復号します。")
    if graph["save"]["inputs"].get("images") != ["decode", 0]:
        raise RuntimeError("保存するのは VAE の出力だけです。")
    for node_id in ("save", "decode", "sample", "trim"):
        for value in graph[node_id]["inputs"].values():
            if value in (["frames", 0], ["frames", 1], ["ref", 0], ["face", 0]):
                raise RuntimeError(f"{node_id} が制御入力を直接受けています。")


def build_prompt(info, frame_dir, length, width, height, positive, negative, seed, prefix, reference_name):
    frame_outputs = list((info.get("H3LoadFrameDir") or {}).get("output") or [])
    if "MASK" not in frame_outputs:
        raise RuntimeError(
            "H3LoadFrameDir が MASK を返しません。セットアップセルを再実行してください。"
        )
    vace_spec = info["WanVaceToVideo"]["input"]
    vace_allowed = set(vace_spec.get("required", {})) | set(vace_spec.get("optional", {}))
    if "control_video" not in vace_allowed or "control_masks" not in vace_allowed:
        raise RuntimeError("WanVaceToVideo に control_video / control_masks がありません。ComfyUI を更新してください。")
    if "reference_image" not in vace_allowed:
        raise RuntimeError("WanVaceToVideo に reference_image がありません。ComfyUI を更新してください。")
    vace_values = {
        "positive": ["pos", 0],
        "negative": ["neg", 0],
        "vae": ["vae", 0],
        "width": width,
        "height": height,
        "length": length,
        "batch_size": 1,
        "strength": 1.0,
        "control_video": ["frames", 0],
        "control_masks": ["frames", 1],
        "reference_image": ["ref", 0],
    }
    graph = {
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
        "frames": {
            "class_type": "H3LoadFrameDir",
            "inputs": pack_inputs(info, "H3LoadFrameDir", {"directory": frame_dir}),
        },
        "ref": {
            "class_type": "LoadImage",
            "inputs": pack_inputs(info, "LoadImage", {"image": reference_name}),
        },
    }
    graph["vace"] = {
        "class_type": "WanVaceToVideo",
        "inputs": pack_inputs(info, "WanVaceToVideo", vace_values),
    }
    graph["shift"] = {
        "class_type": "ModelSamplingSD3",
        "inputs": pack_inputs(info, "ModelSamplingSD3", {"model": ["unet", 0], "shift": SHIFT}),
    }
    graph["sample"] = {
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
    }
    graph["trim"] = {
        "class_type": "TrimVideoLatent",
        "inputs": pack_inputs(info, "TrimVideoLatent", {
            "samples": ["sample", 0],
            "trim_amount": ["vace", 3],
        }),
    }
    graph["decode"] = {
        "class_type": "VAEDecodeTiled",
        "inputs": pack_inputs(info, "VAEDecodeTiled", {
            "samples": ["trim", 0],
            "vae": ["vae", 0],
            "tile_size": 512,
            "overlap": 64,
            "temporal_size": 64,
            "temporal_overlap": 4,
        }),
    }
    graph["save"] = {
        "class_type": "SaveImage",
        "inputs": pack_inputs(info, "SaveImage", {
            "images": ["decode", 0],
            "filename_prefix": prefix,
        }),
    }
    validate_prompt_graph(graph)
    return graph


def prompt_for_cut(info, cut, frame_dir, length, width, height, prefix, prompts=None, reference_name="ref.png"):
    positive, negative = build_prompts(cut["data"], prompts)
    graph = build_prompt(
        info,
        frame_dir,
        length,
        width,
        height,
        positive,
        negative,
        sampler_seed(cut),
        prefix,
        reference_name,
    )
    return graph, positive, negative


def select_cuts(cuts, selected):
    if selected is None:
        return list(cuts)
    if not isinstance(selected, (list, tuple)) or not selected:
        raise RuntimeError("CUTS に再生成するカットを書いてください。例: CUTS = [\"C2\"]")
    wanted = []
    seen = set()
    for item in selected:
        cut_id = safe_cut_id(item)
        if cut_id in seen:
            continue
        seen.add(cut_id)
        wanted.append(cut_id)
    by_id = {cut["cut"]: cut for cut in cuts}
    missing = [cut_id for cut_id in wanted if cut_id not in by_id]
    if missing:
        known = ", ".join(cut["cut"] for cut in cuts)
        raise RuntimeError(f"CUTS に無いカット: {', '.join(missing)}。あるのは {known} です。")
    return [by_id[cut_id] for cut_id in wanted]


def _store_output(mp4, json_path, replace):
    mp4_s = str(mp4)
    json_s = str(json_path)
    if replace:
        mp4_name = Path(mp4_s).name
        json_name = Path(json_s).name
        OUTPUT_MP4S[:] = [item for item in OUTPUT_MP4S if Path(item).name != mp4_name]
        OUTPUT_JSONS[:] = [item for item in OUTPUT_JSONS if Path(item).name != json_name]
    OUTPUT_MP4S.append(mp4_s)
    OUTPUT_JSONS.append(json_s)


def wait_for_cut(prompt_id, cut_id):
    started = time.time()
    announced = -1
    while True:
        elapsed = time.time() - started
        if elapsed > CUT_TIMEOUT_SECONDS:
            raise RuntimeError(f"{cut_id} が制限時間を超えました。ランタイムを削除します。")
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


def saved_image_paths(history_item, frame_dir):
    outputs = history_item.get("outputs") or {}
    if "save" not in outputs:
        raise RuntimeError("SaveImage の出力が履歴にありません。制御フレームは使いません。")
    images = outputs["save"].get("images") or []
    control_root = os.path.abspath(frame_dir)
    paths = []
    for image in images:
        root = "/content/ComfyUI/temp" if image.get("type") == "temp" else "/content/ComfyUI/output"
        sub = image.get("subfolder") or ""
        path = os.path.abspath(os.path.join(root, sub, image["filename"]))
        if path.startswith(control_root + os.sep) or path == control_root:
            raise RuntimeError(f"制御フレームを出力に使おうとしました: {path}")
        paths.append(path)
    paths = [path for path in paths if os.path.isfile(path)]
    paths.sort()
    return paths


def export_mp4(image_paths, fps, keep_frames, geo, dest, focus=None):
    seq = Path("/content/vace_work/seq")
    if seq.exists():
        shutil.rmtree(seq)
    seq.mkdir(parents=True)
    for index, path in enumerate(image_paths):
        shutil.copyfile(path, seq / f"frame_{index:04d}.png")
    staged = Path(str(dest) + ".sized.mp4")
    duration_s = int(keep_frames) / float(fps)
    try:
        cmd = ffmpeg_sequence_cmd(
            seq / "frame_%04d.png",
            len(image_paths),
            fps,
            duration_s,
            geo,
            staged,
            keep_frames=keep_frames,
        )
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg に失敗しました: {result.stderr[-2000:]}")
        finish = ffmpeg_finish_cmd(staged, dest, keep_frames, fps, geo, focus)
        burned = subprocess.run(finish, capture_output=True, text=True)
        if burned.returncode != 0:
            raise RuntimeError(f"手ブレとフォーカスの ffmpeg に失敗しました: {burned.stderr[-2000:]}")
        assert_export_stream(dest, keep_frames, geo["export_width"], geo["export_height"])
    finally:
        if staged.exists():
            staged.unlink()


def run_generation(selected=None, run_dir=None, fresh_run=True, prompts=None):
    global GENERATION_DONE, RUN_DIR
    if not globals().get("GPU_OK"):
        raise RuntimeError("GPU チェックを通過していません。最初のセルから実行してください。")
    for _name in (
        "list_cuts",
        "render_cut",
        "generation_geometry",
        "build_prompts",
        "uses_face_reference",
        "ffmpeg_vf",
        "ffmpeg_sequence_cmd",
        "ffmpeg_finish_cmd",
        "assert_export_stream",
        "assert_generated_still",
        "read_first_frame",
        "copy_control_json",
        "find_face_reference",
        "safe_cut_id",
        "summarize_cut",
        "target_frame_count",
        "vace_frame_count",
        "letterbox_face",
        "side_by_side_reference",
        "find_cat_reference",
        "find_optional_cat_reference",
        "cut_has_cat",
        "scene_spec",
        "read_frame_index",
        "assert_sharpness_recovered",
        "FOCUS_RECOVERY_SECONDS",
        "sampler_seed",
        "load_scene_prompts",
        "EXPORT_WIDTH",
        "EXPORT_HEIGHT",
    ):
        if _name not in globals():
            raise RuntimeError("制御 JSON のセルが未実行です。上から順に実行してください。")
    if "FACE_DIR" not in globals() or "CONTROL_DIR" not in globals() or "OUTPUT_ROOT" not in globals():
        raise RuntimeError("セットアップセルが未実行です。")
    if not os.path.isdir("/content/ComfyUI"):
        raise RuntimeError("ComfyUI がありません。セットアップセルを実行してください。")
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
    if prompts is None:
        prompts = load_scene_prompts(CONTROL_DIR)
    cat_needed = any(cut_has_cat(prompts, cid) for cid in prompts["cuts"])
    cat_path = ensure_cat_reference(FACE_DIR, cat_needed)
    os.makedirs("/content/ComfyUI/input", exist_ok=True)
    print(f"顔参照: {face_path}")
    print(f"猫参照: {cat_path}")

    if prompts is None:
        prompts = load_scene_prompts(CONTROL_DIR)
    print(f"prompts.json を読みました: {CONTROL_DIR}/prompts.json")
    cuts = select_cuts(list_cuts(CONTROL_DIR), selected)
    if run_dir is None:
        run_dir = Path(OUTPUT_ROOT) / time.strftime("%Y%m%d-%H%M%S")
    else:
        run_dir = Path(run_dir)
    run_id = run_dir.name
    run_dir.mkdir(parents=True, exist_ok=True)
    RUN_DIR = str(run_dir)
    print(f"出力フォルダ: {run_dir}")
    if fresh_run:
        OUTPUT_MP4S.clear()
        OUTPUT_JSONS.clear()

    for cut in cuts:
        cut_id = safe_cut_id(cut["cut"])
        frame_dir = f"/content/vace_work/{cut_id}/frames"
        rendered = render_cut(cut, frame_dir, geo["width"], geo["height"])
        vace_count = rendered["count"]
        keep_count = rendered["target_count"]
        print(summarize_cut(cut, keep_count))
        if vace_count != keep_count:
            print(f"VACE は {vace_count} フレーム（4n+1）を生成し、{keep_count} フレームに切ります。")
        ref_name = f"ref_{cut_id}.png"
        if cat_path is None or not cut_has_cat(prompts, cut_id):
            reference = letterbox_face(Image.open(face_path), geo["width"], geo["height"])
        elif uses_face_reference(cut_id, prompts):
            cat_image = Image.open(cat_path)
            face_image = Image.open(face_path)
            reference = side_by_side_reference(cat_image, face_image, geo["width"], geo["height"])
        else:
            reference = letterbox_face(Image.open(cat_path), geo["width"], geo["height"])
        reference.save(Path("/content/ComfyUI/input") / ref_name)
        prefix = f"h3_{run_id}_{cut_id}"
        out_root = Path("/content/ComfyUI/output")
        out_root.mkdir(parents=True, exist_ok=True)
        for old in out_root.glob(prefix + "*"):
            if old.is_file():
                old.unlink()
        prompt, positive, negative = prompt_for_cut(
            info,
            cut,
            frame_dir,
            vace_count,
            geo["width"],
            geo["height"],
            prefix,
            prompts,
            ref_name,
        )
        print(positive)
        print(negative)
        queued = comfy_call("/prompt", {"prompt": prompt})
        if queued.get("node_errors") or "prompt_id" not in queued:
            raise RuntimeError(json.dumps(queued, ensure_ascii=False)[:4000])
        item = wait_for_cut(queued["prompt_id"], cut_id)
        paths = saved_image_paths(item, frame_dir)
        if len(paths) != vace_count:
            raise RuntimeError(f"{cut_id}: フレーム数が {len(paths)} でした。{vace_count} を期待しています。")
        control_image = Image.open(Path(frame_dir) / "frame_0000.png").convert("RGB")
        sampler_image = Image.open(paths[0]).convert("RGB")
        reference_image = Image.open(Path("/content/ComfyUI/input") / ref_name).convert("RGB")
        stats = assert_generated_still(sampler_image, control_image, reference_image)
        print(
            f"{cut_id}: 先頭フレーム SSIM {stats['ssim']:.3f} / 骨格色 {stats['skeleton_families']} 系統"
        )
        local_mp4 = Path(f"/content/vace_work/{cut_id}.mp4")
        focus = scene_spec(prompts, cut_id)["focus"]
        export_mp4(paths, cut["fps"], keep_count, geo, local_mp4, focus)
        final_image = read_first_frame(local_mp4)
        assert_generated_still(final_image, control_image, reference_image)
        if keep_count / float(cut["fps"]) >= FOCUS_RECOVERY_SECONDS:
            later_index = int(round(FOCUS_RECOVERY_SECONDS * float(cut["fps"])))
            later_image = read_frame_index(local_mp4, later_index)
            assert_sharpness_recovered(later_image, final_image)
        dest_mp4 = publish_file(local_mp4, run_dir / f"{cut_id}.mp4")
        copied_json = copy_control_json(cut, run_dir)
        dest_json = publish_file(copied_json, copied_json)
        if dest_mp4.stat().st_size <= 0 or dest_json.stat().st_size <= 0:
            raise RuntimeError(f"{cut_id}: 出力が空です")
        _store_output(dest_mp4, dest_json, replace=not fresh_run)
        print(f"書き出し: {dest_mp4} ({dest_mp4.stat().st_size} bytes)")
        print(f"制御 JSON: {dest_json}")
        try:
            comfy_call("/free", {"unload_models": False, "free_memory": True})
        except Exception as exc:
            print(f"メモリ解放をスキップ: {exc}")

    missing = []
    for cut in cuts:
        cut_id = safe_cut_id(cut["cut"])
        mp4 = run_dir / f"{cut_id}.mp4"
        if not mp4.is_file() or mp4.stat().st_size <= 0:
            missing.append(cut_id)
    if missing or (fresh_run and (len(OUTPUT_MP4S) != len(cuts) or len(OUTPUT_JSONS) != len(cuts))):
        raise RuntimeError(f"出力フォルダに無いカット: {', '.join(missing) or '本数不一致'} ({run_dir})")
    subprocess.run(["sync"], check=False)
    print(f"出力フォルダの中身: {run_dir}")
    for path in sorted(run_dir.iterdir()):
        if path.is_file():
            print(f"  {path.name} {path.stat().st_size} bytes")
    GENERATION_DONE = True
    if fresh_run:
        print("全カットの mp4 と制御 JSON を Drive に書きました。")
    else:
        print(f"再生成したカットを {run_dir} に書きました。")
    arm_idle_timer()


def regenerate_cuts(selected, prompts=None):
    if not globals().get("GENERATION_DONE"):
        raise RuntimeError("先に全カットの生成を終えてください。")
    if not RUN_DIR:
        raise RuntimeError("出力フォルダがありません。生成セルを先に実行してください。")
    run_generation(selected=selected, run_dir=RUN_DIR, fresh_run=False, prompts=prompts)


# テストはこのセルを _H3_LOAD_ONLY 付きで読み、ComfyUI へは繋がない。
if not globals().get("_H3_LOAD_ONLY"):
    try:
        run_generation()
    except Exception as exc:
        print(f"生成に失敗しました: {exc}", flush=True)
        print("Drive を flush してランタイムを削除します。", flush=True)
        try:
            release_runtime()
        except Exception as release_exc:
            print(f"ランタイム削除に失敗しました: {release_exc}", flush=True)
        raise
