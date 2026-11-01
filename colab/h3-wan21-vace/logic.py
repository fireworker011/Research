"""Wan2.1 VACE 14B Colab が、カット制御 JSON をそのまま読むための関数。

JSON のキーは書き換えない。画の文は同じフォルダの prompts.json（ブロック A、人が映るカットだけのブロック S、カットの文、ネガティブ）。描画に使う単位は次のとおり。

- camera_vector.translate: ピクセル。x は右、y は下、z はドリー（フレーム高さに対する倍率）。
- camera_vector.rotate: 度。x はピッチ、y はヨー、z はロール。
- camera_vector.shake.amp_px: 手ブレの振幅（ピクセル）。seed で決まる。
- wrist_to_handle_cm: 1cm をフレーム高さの 2% として制御画像に描く。
- OpenPose / Depth の学習済み重みは使わない。線と濃淡はこのファイルが描く。
- focus_sweep と openpose の時刻範囲の外は、端の値を保持する。描画の時刻は JSON の絶対時刻のまま。
- プロンプトに書くキーフレーム時刻は、source_seconds の開始を 0 としたカット内の時刻。
- caption の発話は映像プロンプトに入れない。声はあとから足す。
- 残すフレーム数は duration_s * fps を丸めた枚数。VACE の長さはそれ以上の最小の 4n+1。書き出しで枚数へ切る。
- OpenPose の線、マスク、顔参照は mp4 に合成しない。深度の楕円も RGB には描き込まない。
"""

import json
import math
import random
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

FACE_FILENAMES = ("face_ref.png", "face_ref.jpg", "face_ref.jpeg", "face_ref.webp")
CAT_FILENAMES = ("cat_ref.png", "cat_ref.jpg", "cat_ref.jpeg", "cat_ref.webp")
FOCUS_BLUR_MAX = 4.0
FOCUS_RECOVERY_SECONDS = 0.5
FOCUS_RECOVERY_RATIO = 0.8
SCENE_PROMPTS_NAME = "prompts.json"
EXPORT_WIDTH = 720
EXPORT_HEIGHT = 1280
GEN_480P = (480, 832)
GEN_720P = (720, 1280)
VRAM_NATIVE_9_16_MIB = 70000
MAX_VACE_FRAMES = 241
SSIM_REJECT = 0.6
# The letterbox is mostly flat gray, so a normal frame can share brightness
# without being the reference. Only a near-copy should fail this one.
REFERENCE_SSIM_REJECT = 0.95
SKELETON_FAMILY_FRACTION = 0.0004
SKELETON_FAMILY_MIN = 3
SKELETON_FAMILIES = (
    ("red", ((255, 0, 0), (255, 0, 85), (255, 0, 170), (255, 85, 0))),
    ("green", ((85, 255, 0), (0, 255, 85), (170, 255, 0))),
    ("orange", ((255, 170, 0),)),
    ("blue", ((0, 0, 255), (0, 85, 255))),
    ("cyan", ((0, 255, 255),)),
    ("magenta", ((255, 0, 255), (170, 0, 255))),
    ("yellow", ((255, 255, 0),)),
)
CM_OF_FRAME_HEIGHT = 0.02
MIN_GAP_CM = 1.0
HANDLE_XY = (0.68, 0.50)
CAT_XY = (0.38, 0.50)
_WRIST_X = 0.45
_WRIST_Y = 0.75
_WRIST_NORM = math.hypot(_WRIST_X, _WRIST_Y)
WRIST_DIR = (_WRIST_X / _WRIST_NORM, _WRIST_Y / _WRIST_NORM)
FACE_PAD = (128, 128, 128)

POSES = {
    "back_to_camera": {"facing": 0.0, "paw": 0.0},
    "face_to_camera": {"facing": 1.0, "paw": 0.0},
    "front": {"facing": 1.0, "paw": 0.0},
    "forepaw_to_mouth": {"facing": 1.0, "paw": 1.0},
    "paw_returned": {"facing": 1.0, "paw": 0.0},
}

DEPTH_LOOK = {
    "near": {"bg": 25, "cat": 235, "cat_scale": 1.20, "handle": 70},
    "far": {"bg": 110, "cat": 140, "cat_scale": 0.62, "handle": 120},
    "cat": {"bg": 30, "cat": 240, "cat_scale": 1.05, "handle": 45},
    "handle": {"bg": 28, "cat": 60, "cat_scale": 0.85, "handle": 245},
}

_BACK = {
    "head": (0.38, 0.26),
    "lear": (0.31, 0.20),
    "rear": (0.45, 0.20),
    "neck": (0.38, 0.36),
    "chest": (0.38, 0.48),
    "lsho": (0.30, 0.46),
    "rsho": (0.46, 0.46),
    "pelvis": (0.38, 0.64),
    "lhind": (0.30, 0.86),
    "rhind": (0.46, 0.86),
    "tail": (0.22, 0.62),
}
_FRONT = {
    "head": (0.38, 0.26),
    "lear": (0.30, 0.18),
    "rear": (0.46, 0.18),
    "neck": (0.38, 0.36),
    "chest": (0.38, 0.48),
    "lsho": (0.26, 0.46),
    "rsho": (0.50, 0.46),
    "pelvis": (0.38, 0.64),
    "lhind": (0.28, 0.88),
    "rhind": (0.48, 0.88),
    "tail": (0.56, 0.60),
}
_LF_REST = (0.24, 0.72)
_RF_REST = (0.52, 0.72)
_LF_MOUTH = (0.36, 0.34)
_LIMBS = (
    ("lear", "head", (255, 0, 85)),
    ("rear", "head", (255, 0, 170)),
    ("head", "neck", (255, 0, 0)),
    ("neck", "chest", (255, 85, 0)),
    ("chest", "lsho", (85, 255, 0)),
    ("lsho", "lf_paw", (0, 255, 85)),
    ("chest", "rsho", (255, 170, 0)),
    ("rsho", "rf_paw", (170, 255, 0)),
    ("chest", "pelvis", (0, 255, 255)),
    ("pelvis", "lhind", (0, 85, 255)),
    ("pelvis", "rhind", (0, 0, 255)),
    ("pelvis", "tail", (170, 0, 255)),
)


def safe_cut_id(cut_id):
    if not re.fullmatch(r"[A-Za-z]+[0-9]+", str(cut_id)):
        raise ValueError(f"cut 名が不正です: {cut_id}")
    return str(cut_id)


def cut_sort_key(cut_id):
    match = re.fullmatch(r"([A-Za-z]+)([0-9]+)", str(cut_id))
    if match is None:
        return (1, 0, str(cut_id))
    return (0, int(match.group(2)), match.group(1))


def _vec3(value, label):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(f"camera_vector.{label} は数値3つです")
    return [float(item) for item in value]


def _pose_from_name(name):
    if name not in POSES:
        known = ", ".join(sorted(POSES))
        raise ValueError(f"未知の openpose ラベルです: {name}。既知: {known}")
    return POSES[name]


def _depth_look(label):
    if label not in DEPTH_LOOK:
        known = ", ".join(sorted(DEPTH_LOOK))
        raise ValueError(f"未知の depth ラベルです: {label}。既知: {known}")
    return DEPTH_LOOK[label]


def load_cut(path):
    path = Path(path)
    raw_text = path.read_text(encoding="utf-8")
    data = json.loads(raw_text)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: 制御 JSON はオブジェクトです")
    required = (
        "cut",
        "source_seconds",
        "aspect",
        "fps",
        "openpose_keyframes",
        "depth",
        "camera_vector",
        "duration_s",
    )
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"{path}: 足りないキー: {', '.join(missing)}")
    cut_id = safe_cut_id(data["cut"])
    if data.get("aspect") != "9:16":
        raise ValueError(f"{path}: aspect は 9:16 だけを受けます: {data.get('aspect')}")
    duration_s = float(data["duration_s"])
    fps = float(data["fps"])
    if duration_s <= 0 or fps <= 0:
        raise ValueError(f"{path}: duration_s と fps は正の数です")
    source = data["source_seconds"]
    if not isinstance(source, (list, tuple)) or len(source) != 2:
        raise ValueError(f"{path}: source_seconds は [開始, 終了] です")
    t0 = float(source[0])
    t1 = float(source[1])
    if t1 <= t0:
        raise ValueError(f"{path}: source_seconds の終了は開始より後です")
    if abs((t1 - t0) - duration_s) > 0.051:
        raise ValueError(
            f"{path}: source_seconds の長さ {t1 - t0} と duration_s {duration_s} が一致しません"
        )
    keyframes = data["openpose_keyframes"]
    if not isinstance(keyframes, list) or not keyframes:
        raise ValueError(f"{path}: openpose_keyframes が空です")
    for kf in keyframes:
        if not isinstance(kf, dict) or "t" not in kf:
            raise ValueError(f"{path}: openpose キーフレームに t がありません")
        float(kf["t"])
        if "cat" in kf:
            _pose_from_name(kf["cat"])
        if "cat_jaw_deg" in kf:
            float(kf["cat_jaw_deg"])
        if "wrist_to_handle_cm" in kf:
            float(kf["wrist_to_handle_cm"])
    depth = data["depth"]
    if not isinstance(depth, dict) or "focus_sweep" not in depth:
        raise ValueError(f"{path}: depth.focus_sweep がありません")
    sweep = depth["focus_sweep"]
    if not isinstance(sweep, list) or not sweep:
        raise ValueError(f"{path}: depth.focus_sweep が空です")
    for item in sweep:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError(f"{path}: focus_sweep の要素は [時刻, ラベル] です")
        float(item[0])
        if not isinstance(item[1], str) or not item[1]:
            raise ValueError(f"{path}: depth ラベルが文字列ではありません")
        _depth_look(item[1])
    if "sakura_hands" in depth and depth["sakura_hands"] != "defocused":
        raise ValueError(f"{path}: sakura_hands は defocused だけを受けます")
    camera = data["camera_vector"]
    if not isinstance(camera, dict):
        raise ValueError(f"{path}: camera_vector がオブジェクトではありません")
    _vec3(camera.get("translate"), "translate")
    _vec3(camera.get("rotate"), "rotate")
    if "shake" in camera and camera["shake"] is not None:
        shake = camera["shake"]
        if not isinstance(shake, dict):
            raise ValueError(f"{path}: shake がオブジェクトではありません")
        if shake.get("type") != "handheld":
            raise ValueError(f"{path}: 未対応の shake.type です: {shake.get('type')}")
        amp = shake.get("amp_px")
        if not isinstance(amp, (list, tuple)) or not 1 <= len(amp) <= 2:
            raise ValueError(f"{path}: shake.amp_px は数値1つか2つです")
        float(amp[0])
        if len(amp) == 2:
            float(amp[1])
        if "seed" not in shake:
            raise ValueError(f"{path}: shake.seed がありません")
        int(shake["seed"])
        if "irregular" in shake and not isinstance(shake["irregular"], bool):
            raise ValueError(f"{path}: shake.irregular は true / false です")
    if "caption" in data:
        if not isinstance(data["caption"], list):
            raise ValueError(f"{path}: caption は配列です")
        for cap in data["caption"]:
            if not isinstance(cap, dict) or "text" not in cap or "t" not in cap:
                raise ValueError(f"{path}: caption に t と text がありません")
            if not isinstance(cap["t"], (list, tuple)) or len(cap["t"]) != 2:
                raise ValueError(f"{path}: caption.t は [開始, 終了] です")
    if "jaw_max_deg" in data:
        limit = float(data["jaw_max_deg"])
        for kf in keyframes:
            if "cat_jaw_deg" in kf and float(kf["cat_jaw_deg"]) - limit > 1e-6:
                raise ValueError(f"{path}: cat_jaw_deg が jaw_max_deg を超えています")
    if "sakura" in data and data["sakura"] != "static":
        raise ValueError(f"{path}: 未対応の sakura です: {data['sakura']}")
    if "contact" in data and not isinstance(data["contact"], bool):
        raise ValueError(f"{path}: contact は true / false です")
    if "hard_cut_before_touch" in data and not isinstance(data["hard_cut_before_touch"], bool):
        raise ValueError(f"{path}: hard_cut_before_touch は true / false です")
    if "fingers_visible" in data:
        fingers = int(data["fingers_visible"])
        if fingers < 0 or fingers > 5:
            raise ValueError(f"{path}: fingers_visible は 0 から 5 です")
    return {
        "path": str(path),
        "raw_text": raw_text,
        "data": data,
        "cut": cut_id,
        "duration_s": duration_s,
        "fps": fps,
        "aspect": data["aspect"],
        "openpose_keyframes": keyframes,
        "depth": depth,
        "camera_vector": camera,
        "source_seconds": (t0, t1),
    }


def list_cuts(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise FileNotFoundError(f"制御 JSON のフォルダがありません: {directory}")
    paths = sorted(
        path
        for path in directory.iterdir()
        if path.is_file()
        and path.suffix.lower() == ".json"
        and path.name != SCENE_PROMPTS_NAME
    )
    if not paths:
        raise FileNotFoundError(
            f"制御 JSON がありません。{directory} に C1 から C4 の json を、中身を変えずに置いてください。"
            " 画の文は prompts.json です。"
        )
    cuts = [load_cut(path) for path in paths]
    seen = {}
    for cut in cuts:
        if cut["cut"] in seen:
            raise ValueError(f"cut {cut['cut']} が重複しています: {seen[cut['cut']]} と {cut['path']}")
        seen[cut["cut"]] = cut["path"]
    cuts.sort(key=lambda cut: cut_sort_key(cut["cut"]))
    return cuts


def _find_named_image(directory, filenames, label):
    directory = Path(directory)
    matches = [directory / name for name in filenames if (directory / name).is_file()]
    if not matches:
        names = ", ".join(filenames)
        raise FileNotFoundError(
            f"{label}がありません。"
            f" {directory} に置いてください。"
            f"ファイル名は {names} のいずれかです。"
        )
    return matches[0]


def find_face_reference(directory):
    return _find_named_image(directory, FACE_FILENAMES, "顔の参照画像")


def find_cat_reference(directory):
    return _find_named_image(directory, CAT_FILENAMES, "猫の参照画像")


def find_optional_cat_reference(directory):
    try:
        return find_cat_reference(directory)
    except FileNotFoundError:
        return None


def cut_has_cat(prompts, cut_id):
    """Per-cut has_cat wins, then top-level has_cat. Default True (older prompts.json)."""
    spec = scene_spec(prompts, cut_id)
    if "has_cat" in spec:
        return bool(spec["has_cat"])
    return bool(prompts.get("has_cat", True))


def copy_control_json(cut, dest_dir):
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / Path(cut["path"]).name
    dest.write_bytes(Path(cut["path"]).read_bytes())
    return dest


def target_frame_count(duration_s, fps):
    return max(1, int(round(float(duration_s) * float(fps))))


def raw_frame_count(duration_s, fps):
    return target_frame_count(duration_s, fps)


def vace_length_for_count(target, max_frames=MAX_VACE_FRAMES):
    target = int(target)
    if target < 1:
        raise ValueError("フレーム数は 1 以上です")
    # Smallest 4n+1 that is >= target. 1, 5, 9, ... and 81, 85, 241.
    length = ((target + 2) // 4) * 4 + 1
    cap = int(max_frames)
    if cap < 1:
        raise ValueError("max_frames は 1 以上です")
    max_ok = ((cap - 1) // 4) * 4 + 1
    if length > max_ok:
        raise ValueError(
            f"VACE の長さ {length} が上限 {max_ok} を超えます。必要フレームは {target} です。"
        )
    return length


def vace_frame_count(duration_s, fps, max_frames=MAX_VACE_FRAMES):
    return vace_length_for_count(target_frame_count(duration_s, fps), max_frames=max_frames)


def wan_frame_count(duration_s, fps, max_frames=MAX_VACE_FRAMES):
    return vace_frame_count(duration_s, fps, max_frames=max_frames)


def frame_source_time(cut, index, count):
    t0, t1 = cut["source_seconds"]
    if count <= 1:
        return float(t0)
    return float(t0) + (float(t1) - float(t0)) * (index / (count - 1))


def index_for_time(cut, t, count):
    t0, t1 = cut["source_seconds"]
    if count <= 1 or t1 == t0:
        return 0
    frac = (float(t) - float(t0)) / (float(t1) - float(t0))
    index = int(round(frac * (count - 1)))
    return max(0, min(count - 1, index))


def generation_geometry(vram_mib, override=None):
    if override is not None:
        width, height = int(override[0]), int(override[1])
        if width % 16 or height % 16 or width < 16 or height < 16:
            raise ValueError("生成サイズは 16 の倍数にしてください")
        native = (width, height) == (EXPORT_WIDTH, EXPORT_HEIGHT)
        return {
            "width": width,
            "height": height,
            "export_width": EXPORT_WIDTH,
            "export_height": EXPORT_HEIGHT,
            "native": native,
        }
    if int(vram_mib) >= VRAM_NATIVE_9_16_MIB:
        width, height = GEN_720P
        native = True
    else:
        width, height = GEN_480P
        native = False
    return {
        "width": width,
        "height": height,
        "export_width": EXPORT_WIDTH,
        "export_height": EXPORT_HEIGHT,
        "native": native,
    }


def ffmpeg_vf(geo):
    if geo["native"]:
        return "setsar=1"
    export_w = geo["export_width"]
    export_h = geo["export_height"]
    return (
        f"scale={export_w}:{export_h}:force_original_aspect_ratio=decrease,"
        f"pad={export_w}:{export_h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1"
    )


def ffmpeg_frame_args(keep_frames):
    keep = int(keep_frames)
    if keep < 1:
        raise ValueError("keep_frames は 1 以上です")
    return ["-frames:v", str(keep)]


def ffmpeg_sequence_cmd(sequence_pattern, frame_count, fps, duration_s, geo, dest, keep_frames=None):
    if float(duration_s) <= 0 or float(fps) <= 0:
        raise ValueError("duration_s と fps は正の数です")
    produced = int(frame_count)
    keep = produced if keep_frames is None else int(keep_frames)
    if keep < 1 or keep > produced:
        raise ValueError(f"切り出しフレーム {keep} が入力 {produced} の範囲外です")
    return [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(sequence_pattern),
        "-vf",
        ffmpeg_vf(geo),
        *ffmpeg_frame_args(keep),
        "-r",
        str(fps),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(dest),
    ]


def focus_level(label):
    name = str(label).strip().lower()
    if name in ("near", "cat"):
        return 0.0
    if name in ("far", "handle"):
        return 1.0
    raise ValueError(f"未知の focus ラベルです: {label}")


def focus_points(sweep):
    if not isinstance(sweep, (list, tuple)) or len(sweep) < 2:
        raise ValueError("focus は [時刻, ラベル] を2つ以上です")
    points = []
    for item in sweep:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise ValueError("focus の要素は [時刻, ラベル] です")
        points.append((float(item[0]), focus_level(item[1])))
    points.sort(key=lambda item: item[0])
    return points


def focus_weight_at(sweep, t):
    points = focus_points(sweep)
    t = float(t)
    if t <= points[0][0]:
        return points[0][1]
    if t >= points[-1][0]:
        return points[-1][1]
    for (t0, v0), (t1, v1) in zip(points, points[1:]):
        if t0 <= t <= t1:
            if t1 == t0:
                return v1
            alpha = (t - t0) / (t1 - t0)
            return v0 + (v1 - v0) * alpha
    return points[-1][1]


def focus_weight_expr(sweep):
    points = focus_points(sweep)
    expr = f"{points[-1][1]:.6f}"
    for (t0, v0), (t1, v1) in reversed(list(zip(points, points[1:]))):
        span = t1 - t0
        if span <= 0:
            piece = f"{v1:.6f}"
        else:
            piece = f"({v0:.6f}+({v1 - v0:.6f})*(T-{t0:.6f})/{span:.6f})"
        expr = f"if(lt(T\\,{t1:.6f})\\,{piece}\\,{expr})"
    t0, v0 = points[0]
    return f"if(lt(T\\,{t0:.6f})\\,{v0:.6f}\\,{expr})"


def ffmpeg_post_filter(width, height, keep_frames, fps, focus=None):
    keep = int(keep_frames)
    rate = float(fps)
    if keep < 1 or rate <= 0:
        raise ValueError("keep_frames と fps は正の数です")
    if focus is None:
        focus = [(0.0, "near"), (0.25, "far"), (0.5, "near")]
    # ±2 px in x and ±1 px in y. Frame 0 sits on the center of that window.
    shake = (
        "crop=w=iw-4:h=ih-4:"
        "x='2+2*sin(n*0.35)':"
        "y='2+1*sin(n*0.57)',"
        f"scale={int(width)}:{int(height)}:flags=bilinear,setsar=1"
    )
    # Depth schedule only. Weight 0 is sharp. Weight 1 is a 4px blur, then it returns.
    weight = f"clip({focus_weight_expr(focus)}\\,0\\,1)"
    return (
        f"[0:v]{shake},"
        "split[sharp][toblur];"
        f"[toblur]gblur=sigma={FOCUS_BLUR_MAX:.0f}[blurred];"
        f"[sharp][blurred]blend=all_expr='A*(1-{weight})+B*{weight}'[vout]"
    )


def ffmpeg_finish_cmd(src, dest, keep_frames, fps, geo, focus=None):
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-filter_complex",
        ffmpeg_post_filter(
            geo["export_width"],
            geo["export_height"],
            keep_frames,
            fps,
            focus,
        ),
        "-map",
        "[vout]",
        *ffmpeg_frame_args(keep_frames),
        "-r",
        str(fps),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(dest),
    ]


def probe_video_stream(path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-count_frames",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,nb_read_frames",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe に失敗しました: {result.stderr[-2000:]}")
    payload = json.loads(result.stdout or "{}")
    streams = payload.get("streams") or []
    if not streams or "nb_read_frames" not in streams[0]:
        raise RuntimeError(f"ffprobe がフレーム数を返しませんでした: {result.stdout[:500]}")
    stream = streams[0]
    return {
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "frames": int(stream["nb_read_frames"]),
    }


def assert_export_stream(path, frames, width, height):
    got = probe_video_stream(path)
    if got["frames"] != int(frames) or got["width"] != int(width) or got["height"] != int(height):
        raise RuntimeError(
            f"書き出しが {got['width']}x{got['height']} {got['frames']} フレームです。"
            f" {int(width)}x{int(height)} {int(frames)} フレームが必要です。"
        )
    return got


def _resample_luma(image, side):
    gray = image.convert("L").resize((side, side), Image.Resampling.BOX)
    return list(gray.getdata())


def _ssim_block(left, right):
    n = len(left)
    mean_a = sum(left) / n
    mean_b = sum(right) / n
    var_a = sum((value - mean_a) ** 2 for value in left) / n
    var_b = sum((value - mean_b) ** 2 for value in right) / n
    cov = sum((a - mean_a) * (b - mean_b) for a, b in zip(left, right)) / n
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    denom = (mean_a ** 2 + mean_b ** 2 + c1) * (var_a + var_b + c2)
    if denom == 0:
        return 1.0
    return ((2 * mean_a * mean_b + c1) * (2 * cov + c2)) / denom


def frame_ssim(left, right, side=64, window=8):
    if side % window != 0:
        raise ValueError("side は window の倍数です")
    sample_a = _resample_luma(left, side)
    sample_b = _resample_luma(right, side)
    scores = []
    for origin_y in range(0, side, window):
        for origin_x in range(0, side, window):
            block_a = []
            block_b = []
            for offset_y in range(window):
                row = (origin_y + offset_y) * side + origin_x
                block_a.extend(sample_a[row : row + window])
                block_b.extend(sample_b[row : row + window])
            scores.append(_ssim_block(block_a, block_b))
    return sum(scores) / len(scores)


def _skeleton_pixels(image):
    rgb = image.convert("RGB")
    raw = rgb.tobytes()
    total = rgb.size[0] * rgb.size[1]
    family_hits = [0] * len(SKELETON_FAMILIES)
    if total <= 0:
        return total, family_hits
    for index in range(0, len(raw), 3):
        red = raw[index]
        green = raw[index + 1]
        blue = raw[index + 2]
        if max(red, green, blue) < 240 or min(red, green, blue) > 30:
            continue
        best = None
        best_distance = 49
        for family_index, (_name, colors) in enumerate(SKELETON_FAMILIES):
            for color in colors:
                distance = abs(red - color[0]) + abs(green - color[1]) + abs(blue - color[2])
                if distance < best_distance:
                    best = family_index
                    best_distance = distance
        if best is not None:
            family_hits[best] += 1
    return total, family_hits


def saturated_skeleton_fraction(image):
    total, family_hits = _skeleton_pixels(image)
    if total <= 0:
        return 0.0
    return sum(family_hits) / total


def saturated_skeleton_families(image):
    total, family_hits = _skeleton_pixels(image)
    if total <= 0:
        return 0
    present = 0
    for count in family_hits:
        if count / total > SKELETON_FAMILY_FRACTION:
            present += 1
    return present


def assert_generated_still(output_image, control_image, reference_image=None):
    score = frame_ssim(output_image, control_image)
    fraction = saturated_skeleton_fraction(output_image)
    families = saturated_skeleton_families(output_image)
    if score > SSIM_REJECT:
        raise RuntimeError(
            f"出力の先頭フレームが制御フレームに似すぎています (SSIM {score:.3f} > {SSIM_REJECT})。"
            " 制御画像をそのまま書いています。"
        )
    if families >= SKELETON_FAMILY_MIN:
        raise RuntimeError(
            f"出力の先頭フレームに骨格の原色が残っています ({families} 色, 割合 {fraction:.4f})。"
            " サンプラー出力ではありません。"
        )
    ref_score = None
    if reference_image is not None:
        ref_score = frame_ssim(output_image, reference_image)
        if ref_score > REFERENCE_SSIM_REJECT:
            raise RuntimeError(
                f"出力の先頭フレームが顔参照に似すぎています (SSIM {ref_score:.3f} > {REFERENCE_SSIM_REJECT})。"
                " 参照画像を合成しています。"
            )
    return {
        "ssim": score,
        "skeleton": fraction,
        "skeleton_families": families,
        "reference_ssim": ref_score,
    }


def read_first_frame(path):
    return read_frame_index(path, 0)


def read_frame_index(path, index):
    index = int(index)
    if index < 0:
        raise ValueError("frame index")
    temp_dir = Path(tempfile.mkdtemp(prefix="h3frame_"))
    dest = temp_dir / "frame.png"
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(path),
                "-vf",
                f"select=eq(n\\,{index})",
                "-frames:v",
                "1",
                str(dest),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not dest.is_file():
            raise RuntimeError(f"フレーム {index} を読めません: {result.stderr[-2000:]}")
        image = Image.open(dest).convert("RGB")
        image.load()
        return image
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def laplacian_variance(image, side=64):
    gray = list(image.convert("L").resize((side, side), Image.Resampling.BOX).getdata())
    total = 0.0
    total_sq = 0.0
    count = 0
    for y in range(1, side - 1):
        for x in range(1, side - 1):
            center = y * side + x
            value = (
                gray[center - side]
                + gray[center - 1]
                + gray[center + 1]
                + gray[center + side]
                - 4 * gray[center]
            )
            total += value
            total_sq += value * value
            count += 1
    mean = total / count
    return total_sq / count - mean * mean


def assert_sharpness_recovered(later, earlier, ratio=FOCUS_RECOVERY_RATIO):
    base = laplacian_variance(earlier)
    got = laplacian_variance(later)
    if base <= 1e-6:
        raise RuntimeError("先頭フレームに輪郭が無いので、ピントの戻りを測れません。")
    if got < float(ratio) * base:
        raise RuntimeError(
            f"0.5秒の鮮鋭度が先頭の {got / base:.0%} です。"
            f" {ratio:.0%} 以上が必要です。"
        )
    return {"earlier": base, "later": got, "ratio": got / base}


def _lerp(samples, t, default):
    if not samples:
        return default
    ordered = sorted(samples, key=lambda item: item[0])
    if t <= ordered[0][0]:
        return ordered[0][1]
    if t >= ordered[-1][0]:
        return ordered[-1][1]
    for (t0, v0), (t1, v1) in zip(ordered, ordered[1:]):
        if t0 <= t <= t1:
            if t1 == t0:
                return v1
            alpha = (t - t0) / (t1 - t0)
            return float(v0) + (float(v1) - float(v0)) * alpha
    return ordered[-1][1]


def contact_allowed(data):
    if "contact" not in data:
        return True
    return bool(data["contact"])


def pose_state_at(data, t):
    facing_samples = []
    paw_samples = []
    jaw_samples = []
    wrist_samples = []
    for kf in data["openpose_keyframes"]:
        ts = float(kf["t"])
        if "cat" in kf:
            pose = _pose_from_name(kf["cat"])
            facing_samples.append((ts, pose["facing"]))
            paw_samples.append((ts, pose["paw"]))
        if "cat_jaw_deg" in kf:
            jaw_samples.append((ts, float(kf["cat_jaw_deg"])))
        if "wrist_to_handle_cm" in kf:
            wrist_samples.append((ts, float(kf["wrist_to_handle_cm"])))
    wrist = None
    if wrist_samples:
        wrist = float(_lerp(wrist_samples, t, wrist_samples[0][1]))
        if not contact_allowed(data):
            wrist = max(wrist, MIN_GAP_CM)
    return {
        "facing": float(_lerp(facing_samples, t, 1.0)),
        "paw": float(_lerp(paw_samples, t, 0.0)),
        "jaw_deg": float(_lerp(jaw_samples, t, 0.0)),
        "wrist_cm": wrist,
    }


def depth_sample(data, t):
    points = [(float(item[0]), str(item[1])) for item in data["depth"]["focus_sweep"]]
    points.sort(key=lambda item: item[0])
    if t <= points[0][0] or t >= points[-1][0]:
        label = points[0][1] if t <= points[0][0] else points[-1][1]
        return label, label, 0.0
    for (t0, left), (t1, right) in zip(points, points[1:]):
        if t0 <= t <= t1:
            alpha = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            return left, right, alpha
    label = points[-1][1]
    return label, label, 0.0


def _angle_shift(degrees, span):
    clamped = max(-80.0, min(80.0, float(degrees)))
    return math.tan(math.radians(clamped)) * (float(span) * 0.25)


def handheld_path(frame_count, amp_x, amp_y, seed, irregular):
    count = int(frame_count)
    if count < 1:
        raise ValueError("frame_count")
    rng = random.Random(int(seed))
    if not irregular:
        phase = rng.random() * math.tau
        path = []
        for index in range(count):
            u = index / max(count - 1, 1)
            dx = amp_x * math.sin(2 * math.pi * u + phase)
            dy = amp_y * math.sin(2 * math.pi * u * 1.37 + phase * 0.7)
            path.append((dx, dy))
        return path
    raw = []
    x = 0.0
    y = 0.0
    for _ in range(count):
        x += rng.uniform(-1.0, 1.0)
        y += rng.uniform(-1.0, 1.0)
        raw.append((x, y))
    window = max(3, count // 8)
    smoothed = []
    for index in range(count):
        acc_x = 0.0
        acc_y = 0.0
        n = 0
        start = max(0, index - window)
        end = min(count, index + window + 1)
        for cursor in range(start, end):
            acc_x += raw[cursor][0]
            acc_y += raw[cursor][1]
            n += 1
        smoothed.append((acc_x / n, acc_y / n))
    peak_x = max(abs(point[0]) for point in smoothed) or 1.0
    peak_y = max(abs(point[1]) for point in smoothed) or 1.0
    return [(amp_x * point[0] / peak_x, amp_y * point[1] / peak_y) for point in smoothed]


def camera_delta(camera_vector, frame_index, frame_count, width, height):
    translate = _vec3(camera_vector.get("translate"), "translate")
    rotate = _vec3(camera_vector.get("rotate"), "rotate")
    shake_x = 0.0
    shake_y = 0.0
    shake = camera_vector.get("shake")
    if shake:
        amp = shake.get("amp_px") or [0, 0]
        amp_x = float(amp[0])
        amp_y = float(amp[1]) if len(amp) > 1 else amp_x
        path = handheld_path(
            frame_count,
            amp_x,
            amp_y,
            int(shake.get("seed", 0)),
            bool(shake.get("irregular", False)),
        )
        shake_x, shake_y = path[frame_index]
    scale = 1.0 + (translate[2] / float(height if height else 1))
    scale = max(0.5, min(2.0, scale))
    return {
        "dx": translate[0] + shake_x + _angle_shift(rotate[1], width),
        "dy": translate[1] + shake_y + _angle_shift(rotate[0], height),
        "roll": rotate[2],
        "scale": scale,
    }


def _identity(delta):
    return (
        abs(delta["dx"]) < 1e-6
        and abs(delta["dy"]) < 1e-6
        and abs(delta["roll"]) < 1e-6
        and abs(delta["scale"] - 1.0) < 1e-6
    )


def warp_image(image, delta):
    if _identity(delta):
        return image
    width, height = image.size
    cx = (width - 1) / 2.0
    cy = (height - 1) / 2.0
    scale = delta["scale"]
    theta = math.radians(delta["roll"])
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    dx = delta["dx"]
    dy = delta["dy"]
    a = cos_t / scale
    b = sin_t / scale
    d = -sin_t / scale
    e = cos_t / scale
    c = cx - a * (cx + dx) - b * (cy + dy)
    f = cy - d * (cx + dx) - e * (cy + dy)
    fill = 0 if image.mode == "L" else (0, 0, 0)
    return image.transform(
        (width, height),
        Image.Transform.AFFINE,
        (a, b, c, d, e, f),
        resample=Image.Resampling.BICUBIC,
        fillcolor=fill,
    )


def _mix(a, b, facing):
    return (a[0] + (b[0] - a[0]) * facing, a[1] + (b[1] - a[1]) * facing)


def _px(point, width, height):
    return (point[0] * width, point[1] * height)


def _line_width(width):
    return max(2, int(width) // 96)


def cut_mentions_handle(data):
    if any("wrist_to_handle_cm" in kf for kf in data["openpose_keyframes"]):
        return True
    return any(str(item[1]) == "handle" for item in data["depth"]["focus_sweep"])


def draw_pose(state, data, width, height):
    image = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    facing = max(0.0, min(1.0, state["facing"]))
    paw = max(0.0, min(1.0, state["paw"]))
    points = {}
    for name in _BACK:
        points[name] = _mix(_BACK[name], _FRONT[name], facing)
    points["lf_paw"] = _mix(_LF_REST, _LF_MOUTH, paw)
    points["rf_paw"] = _RF_REST
    lw = _line_width(width)
    for start, end, color in _LIMBS:
        draw.line([_px(points[start], width, height), _px(points[end], width, height)], fill=color, width=lw)
    head = _px(points["head"], width, height)
    radius = max(2, int(width * 0.03))
    draw.ellipse(
        (head[0] - radius, head[1] - radius, head[0] + radius, head[1] + radius),
        fill=(255, 0, 0),
    )
    if facing > 0.45:
        eye_r = max(1, int(radius * facing * 0.35))
        left_eye = _px((0.34, 0.25), width, height)
        right_eye = _px((0.42, 0.25), width, height)
        for eye, color in ((left_eye, (255, 0, 255)), (right_eye, (170, 0, 255))):
            draw.ellipse(
                (eye[0] - eye_r, eye[1] - eye_r, eye[0] + eye_r, eye[1] + eye_r),
                fill=color,
            )
    if state["jaw_deg"] > 0.5:
        drop = (state["jaw_deg"] / 45.0) * 0.05 * height
        jaw = (head[0], head[1] + radius + drop)
        draw.line([head, jaw], fill=(255, 85, 0), width=lw)
    if state["wrist_cm"] is not None:
        hx = HANDLE_XY[0] * width
        hy = HANDLE_XY[1] * height
        dist = float(state["wrist_cm"]) * CM_OF_FRAME_HEIGHT * height
        wx = hx + WRIST_DIR[0] * dist
        wy = hy + WRIST_DIR[1] * dist
        draw.line([(hx, hy - 0.08 * height), (hx, hy + 0.08 * height)], fill=(0, 255, 255), width=lw)
        elbow = (wx + WRIST_DIR[0] * 0.10 * height, wy + WRIST_DIR[1] * 0.10 * height)
        draw.line([elbow, (wx, wy)], fill=(170, 255, 0), width=lw)
        joint = max(2, lw)
        draw.ellipse((wx - joint, wy - joint, wx + joint, wy + joint), fill=(255, 255, 0))
        if "fingers_visible" in data:
            fingers = int(data["fingers_visible"])
            px, py = -WRIST_DIR[1], WRIST_DIR[0]
            for finger in range(fingers):
                spread = (finger - (fingers - 1) / 2.0) * 0.012 * width
                base = (wx + px * spread * 0.35, wy + py * spread * 0.35)
                tip = (
                    wx - WRIST_DIR[0] * 0.008 * height + px * spread,
                    wy - WRIST_DIR[1] * 0.008 * height + py * spread,
                )
                draw.line([base, tip], fill=(255, 255, 0), width=max(1, lw - 1))
    return image


def _paint_depth(label, data, width, height):
    look = _depth_look(label)
    image = Image.new("L", (width, height), int(look["bg"]))
    draw = ImageDraw.Draw(image)
    scale = float(look["cat_scale"])
    cx = CAT_XY[0] * width
    cy = CAT_XY[1] * height
    rw = 0.14 * width * scale
    rh = 0.24 * height * scale
    draw.ellipse((cx - rw, cy - rh, cx + rw, cy + rh), fill=int(look["cat"]))
    if cut_mentions_handle(data):
        hx = HANDLE_XY[0] * width
        hy = HANDLE_XY[1] * height
        hw = 0.025 * width
        hh = 0.09 * height
        draw.rectangle((hx - hw, hy - hh, hx + hw, hy + hh), fill=int(look["handle"]))
    return image


def draw_depth(label_a, label_b, alpha, data, width, height):
    left = _paint_depth(label_a, data, width, height)
    if label_a == label_b or alpha <= 0.0:
        image = left
    elif alpha >= 1.0:
        image = _paint_depth(label_b, data, width, height)
    else:
        right = _paint_depth(label_b, data, width, height)
        image = Image.blend(left, right, float(alpha))
    if data["depth"].get("sakura_hands") == "defocused":
        top = int(height * 0.68)
        band = image.crop((0, top, width, height)).filter(
            ImageFilter.GaussianBlur(radius=max(2, height // 48))
        )
        image = image.copy()
        image.paste(band, (0, top))
    return image


def composite_controls(pose, depth):
    depth_rgb = depth.convert("RGB")
    mask = pose.convert("L").point(lambda value: 255 if value > 12 else 0)
    return Image.composite(pose, depth_rgb, mask)


def render_control_frame(cut, index, count, width, height):
    if count < 1:
        raise ValueError("count")
    if index < 0 or index >= count:
        raise IndexError(index)
    t = frame_source_time(cut, index, count)
    data = cut["data"]
    state = pose_state_at(data, t)
    label_a, label_b, alpha = depth_sample(data, t)
    pose = draw_pose(state, data, width, height)
    depth = draw_depth(label_a, label_b, alpha, data, width, height)
    delta = camera_delta(cut["camera_vector"], index, count, width, height)
    pose_w = warp_image(pose, delta)
    depth_w = warp_image(depth, delta)
    return {
        "time": t,
        "pose_state": state,
        "depth": (label_a, label_b, alpha),
        "camera": delta,
        "pose_raw": pose,
        "depth_raw": depth,
        "pose": pose_w,
        "depth_out": depth_w,
        "composite": composite_controls(pose_w, depth_w),
    }


def render_cut(cut, dest_dir, width, height):
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    for old in list(dest.glob("frame_*.png")) + list(dest.glob("mask_*.png")):
        old.unlink()
    target = target_frame_count(cut["duration_s"], cut["fps"])
    count = vace_frame_count(cut["duration_s"], cut["fps"])
    metas = []
    for index in range(count):
        # Pad by repeating the last kept frame so the 4n+1 tail can be trimmed off.
        source_index = min(index, target - 1)
        frame = render_control_frame(cut, source_index, target, width, height)
        # Pose only. Depth ellipses and the reference photo stay out of this RGB.
        frame["pose"].save(dest / f"frame_{index:04d}.png")
        # All-ones mask: WanVaceToVideo keeps control pixels where the mask is 0.
        Image.new("L", (int(width), int(height)), 255).save(dest / f"mask_{index:04d}.png")
        metas.append(
            {
                "time": frame["time"],
                "camera": frame["camera"],
                "pose_state": frame["pose_state"],
                "depth": frame["depth"],
            }
        )
    return {
        "directory": str(dest),
        "count": count,
        "target_count": target,
        "metas": metas,
        "width": width,
        "height": height,
    }


def letterbox_face(image, width, height):
    if image.mode != "RGB":
        image = image.convert("RGB")
    canvas = Image.new("RGB", (int(width), int(height)), FACE_PAD)
    fitted = image.copy()
    max_w = max(1, int(width * 0.72))
    max_h = max(1, int(height * 0.42))
    fitted.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    x = (int(width) - fitted.width) // 2
    y = max(0, int(height * 0.08))
    canvas.paste(fitted, (x, y))
    return canvas


def _fit_on_canvas(canvas, image, box):
    x0, y0, x1, y1 = box
    bound_w = max(1, int(x1) - int(x0))
    bound_h = max(1, int(y1) - int(y0))
    fitted = image.convert("RGB")
    fitted.thumbnail((bound_w, bound_h), Image.Resampling.LANCZOS)
    x = int(x0) + (bound_w - fitted.width) // 2
    y = int(y0) + (bound_h - fitted.height) // 2
    canvas.paste(fitted, (x, y))
    return fitted.size


def side_by_side_reference(cat, face, width, height):
    """One VACE reference image. The node keeps only the first frame, so cat and face share it."""
    canvas = Image.new("RGB", (int(width), int(height)), FACE_PAD)
    mid = int(width) // 2
    pad = max(2, int(width) // 64)
    _fit_on_canvas(canvas, cat, (pad, pad, mid - pad, int(height) - pad))
    _fit_on_canvas(canvas, face, (mid + pad, pad, int(width) - pad, int(height) - pad))
    return canvas


def resolve_prompts_path(directory=None):
    if directory is None:
        directory = globals().get("CONTROL_DIR")
    if directory:
        path = Path(str(directory)) / SCENE_PROMPTS_NAME
        if not path.is_file():
            raise FileNotFoundError(
                "プロンプトがありません。"
                f" {path} に固定語ブロックとカットごとの文を置いてください。"
            )
        return path
    cwd = Path.cwd()
    candidates = []
    here = globals().get("__file__")
    if here:
        candidates.append(Path(here).resolve().parent / "controls" / SCENE_PROMPTS_NAME)
    for base in (cwd, *list(cwd.parents)[:6]):
        candidates.append(base / "controls" / SCENE_PROMPTS_NAME)
        candidates.append(base / "colab" / "h3-wan21-vace" / "controls" / SCENE_PROMPTS_NAME)
    seen = set()
    for path in candidates:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        if path.is_file():
            return path
    raise FileNotFoundError(
        "prompts.json がありません。"
        " マイドライブ/ComfyUI_vace_h3/input/controls/prompts.json に置いてください。"
    )


def load_scene_prompts(directory=None):
    path = resolve_prompts_path(directory)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: プロンプトはオブジェクトです")
    for key in ("block_a", "block_s", "negative_common"):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{path}: {key} が空です")
    cuts = data.get("cuts")
    if not isinstance(cuts, dict) or not cuts:
        raise ValueError(f"{path}: cuts がありません")
    for cut_id, spec in cuts.items():
        safe_cut_id(cut_id)
        if not isinstance(spec, dict):
            raise ValueError(f"{path}: {cut_id} はオブジェクトです")
        prompt = spec.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"{path}: {cut_id} の prompt が空です")
        if not isinstance(spec.get("has_person"), bool):
            raise ValueError(f"{path}: {cut_id} の has_person は true / false です")
        negative = spec.get("negative", "")
        if not isinstance(negative, str):
            raise ValueError(f"{path}: {cut_id} の negative は文字列です")
        focus = spec.get("focus")
        points = focus_points(focus)
        if points[0][0] > 0.0:
            raise ValueError(f"{path}: {cut_id} の focus は 0 秒から始まります")
        if focus_weight_at(focus, 0.0) != 0.0 or focus_weight_at(focus, FOCUS_RECOVERY_SECONDS) != 0.0:
            raise ValueError(f"{path}: {cut_id} の focus は 0.5 秒で近景に戻ります")
    return data


def scene_spec(prompts, cut_id):
    cut_id = safe_cut_id(cut_id)
    cuts = prompts["cuts"]
    if cut_id not in cuts:
        known = ", ".join(sorted(cuts, key=cut_sort_key))
        raise ValueError(f"prompts.json に {cut_id} がありません。記載: {known}")
    return cuts[cut_id]


def uses_face_reference(cut_id, prompts=None):
    if prompts is None:
        prompts = load_scene_prompts()
    return scene_spec(prompts, cut_id)["has_person"]


def prompt_time(data, t):
    """Keyframe times in the JSON are script-absolute. Prompts use seconds from the cut start."""
    start = float(data["source_seconds"][0])
    duration = round(float(data["duration_s"]), 3)
    local = round(float(t) - start, 3)
    if local < 0.0:
        local = 0.0
    if local > duration:
        local = duration
    return format_seconds(local)


def format_seconds(t):
    text = f"{float(t):.3f}".rstrip("0").rstrip(".")
    if "." not in text:
        text += ".0"
    return text


def focus_prompt_line(sweep):
    parts = []
    for item in sweep:
        parts.append(f"{item[1]} at {format_seconds(item[0])}s")
    return "focus pull " + ", ".join(parts) + ", sharp again by 0.5s, blur radius at most 4px"


def _control_lines(data, has_person, has_cat=True):
    lines = ["vertical 9:16 shot"]
    if has_cat:
        lines.append("same cat as reference")
    if has_person:
        lines.append("the person's face matches the reference image")
    lines.append("follow the OpenPose control, the depth control, and the camera move")
    sweep = data["depth"]["focus_sweep"]
    focus_start = str(sweep[0][1]).replace("_", " ")
    focus_end = str(sweep[-1][1]).replace("_", " ")
    lines.append(f"one focus pull from {focus_start} to {focus_end}")
    lines.append(f"duration {float(data['duration_s'])} seconds")
    if has_cat and data.get("sakura") == "static":
        lines.append("the cat stays in place except for its jaw")
    for kf in data["openpose_keyframes"]:
        t = prompt_time(data, kf["t"])
        if has_cat and "cat" in kf:
            lines.append(f"at {t}s cat pose {str(kf['cat']).replace('_', ' ')}")
        if has_cat and "cat_jaw_deg" in kf:
            lines.append(f"at {t}s cat jaw {kf['cat_jaw_deg']} degrees")
        if "wrist_to_handle_cm" in kf:
            lines.append(f"at {t}s wrist is {kf['wrist_to_handle_cm']} cm from the handle")
    if data.get("contact") is False:
        lines.append("the hand does not touch the handle")
    if data.get("hard_cut_before_touch") is True:
        lines.append("cut before the hand touches")
    if "fingers_visible" in data:
        lines.append(f"{int(data['fingers_visible'])} fingers are visible")
    return lines


def _stock_negatives(data):
    parts = [
        "low quality",
        "blurry",
        "watermark",
        "subtitles",
        "captions",
        "on-screen text",
        "letters",
        "extra limbs",
        "deformed hands",
        "frozen video",
    ]
    if data.get("contact") is False:
        parts.append("hand touching the handle")
        parts.append("grip")
    return parts


def build_prompts(data, prompts=None):
    if prompts is None:
        prompts = load_scene_prompts()
    spec = scene_spec(prompts, data["cut"])
    has_person = spec["has_person"]
    script_parts = [prompts["block_a"]]
    if has_person:
        script_parts.append(prompts["block_s"])
    script_parts.append(spec["prompt"])
    positive = ", ".join(script_parts) + ". " + ". ".join(
        _control_lines(data, has_person, cut_has_cat(prompts, data["cut"]))
    )
    positive = positive + ". " + focus_prompt_line(spec["focus"])
    negative_parts = [prompts["negative_common"]]
    extra = spec.get("negative", "").strip()
    if extra:
        negative_parts.append(extra)
    negative_parts.extend(_stock_negatives(data))
    return positive, ", ".join(negative_parts)


def summarize_cut(cut, frame_count):
    return (
        f"{cut['cut']}: duration_s={cut['duration_s']} fps={cut['fps']} "
        f"frames={frame_count} source={list(cut['source_seconds'])} "
        f"openpose={len(cut['openpose_keyframes'])} "
        f"depth={len(cut['depth']['focus_sweep'])}"
    )


def sampler_seed(cut):
    shake = cut["camera_vector"].get("shake") or {}
    return 10000 + int(shake.get("seed", 0))
