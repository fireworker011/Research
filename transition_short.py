"""年ごとの写真を、顔位置を固定したまま次の写真へモーフするショートの前処理と結合。

参考にした作り（縦 720x1280）:
- 顔の中心を画面の高さ 25% に置く
- 顔の大きさは、目の高さから顎（顔検出箱の下端）までを画面の高さの 16% にする
- 字幕は「2013 18yo」。色 #E8CB28、黒フチ、文字の中心を画面の高さ 63.5%（62〜65% の中央）
- ナレーションは入れない。音は渡された BGM だけ

ComfyUI 側は同じ Wan 2.2 I2V（high/low + LightX2V）を
WanFirstLastFrameToVideo で開始写真と終了写真の両方に繋ぐ。
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path

# cv2 / numpy は顔の整列でのみ使う。Colab ではワークフロー保存のあとに
# opencv を入れるので、ここでは読まない。

FRAME_W = 720
FRAME_H = 1280
FACE_CENTER_X_RATIO = 0.5
FACE_CENTER_Y_RATIO = 0.25
# 目のラインから検出箱の下端まで。参考動画の実測はおよそ 0.14〜0.17。
FACE_SIZE_RATIO = 0.16
CAPTION_CENTER_Y_RATIO = 0.635
CAPTION_COLOR = "0xE8CB28"
CAPTION_COLOR_RGB = (0xE8, 0xCB, 0x28)
CAPTION_FONTSIZE = 58
CAPTION_STROKE = 8
FPS = 24
LENGTH = 97  # 4n+1。24fps で約4秒
BIRTH_YEAR = 1995  # ジミン。字幕の年齢は「年 - 生まれ年」

POSITIVE = (
    "same person, face locked in place at a fixed size, static locked-off camera, "
    "no zoom, no pan, no tilt, smooth natural morph from the start photo to the end photo, "
    "clothes hair and background change gradually, sharp face, vertical portrait"
)
NEGATIVE = (
    "camera move, zoom in, zoom out, pan, tilt, dolly, parallax, handheld, "
    "face moving up, face moving down, face size change, different person, "
    "distorted face, extra limbs, watermark, text, subtitle, logo, nsfw, blurry"
)

HIGH_UNET = "wan2.2_i2v_high_noise_14B_fp16.safetensors"
LOW_UNET = "wan2.2_i2v_low_noise_14B_fp16.safetensors"
HIGH_LORA = "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors"
LOW_LORA = "wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors"
CLIP_NAME = "umt5_xxl_fp8_e4m3fn_scaled.safetensors"
VAE_NAME = "wan_2.1_vae.safetensors"
CLIP_VISION_NAME = "clip_vision_h.safetensors"

YUNET_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    "face_detection_yunet/face_detection_yunet_2023mar.onnx"
)

WORKFLOW_NAME = "wan22_flf_year_morph.json"


@dataclass(frozen=True)
class Face:
    x: float
    y: float
    w: float
    h: float
    eye_y: float

    @property
    def center_x(self) -> float:
        return self.x + self.w / 2

    @property
    def center_y(self) -> float:
        return self.y + self.h / 2

    @property
    def eye_to_chin(self) -> float:
        return (self.y + self.h) - self.eye_y


@dataclass(frozen=True)
class YearPhoto:
    year: int
    age: int
    label: str
    path: Path


def age_label(year: int, birth_year: int = BIRTH_YEAR) -> str:
    return f"{year} {year - birth_year}yo"


def font_path() -> str:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/croscore/Arimo-Bold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("太字のサンセリフが見つかりません")


def ensure_yunet(dest: Path | None = None) -> Path:
    if dest is None:
        dest = Path.home() / ".cache" / "transition_short" / "yunet.onnx"
    if dest.exists() and dest.stat().st_size > 100_000:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(YUNET_URL, dest)
    return dest


def detect_face(image, model_path: Path):
    import cv2

    height, width = image.shape[:2]
    detector = cv2.FaceDetectorYN_create(
        str(model_path), "", (width, height), 0.6, 0.3, 5000
    )
    detector.setInputSize((width, height))
    _, faces = detector.detect(image)
    if faces is None or len(faces) == 0:
        return None
    row = max(faces, key=lambda item: float(item[2]) * float(item[3]))
    eye_y = (float(row[5]) + float(row[7])) / 2
    return Face(
        x=float(row[0]),
        y=float(row[1]),
        w=float(row[2]),
        h=float(row[3]),
        eye_y=eye_y,
    )


def align_matrix(face: Face, out_w: int = FRAME_W, out_h: int = FRAME_H):
    """ソース座標を、顔中心 25%・目から顎まで 16% のキャンバスへ写す 2x3 行列。"""
    span = face.eye_to_chin
    if span < 2:
        raise ValueError("顔の目から顎までの長さが取れません")
    scale = (FACE_SIZE_RATIO * out_h) / span
    tx = (FACE_CENTER_X_RATIO * out_w) - scale * face.center_x
    ty = (FACE_CENTER_Y_RATIO * out_h) - scale * face.center_y
    return scale, tx, ty


def align_image(image, model_path: Path, out_w: int = FRAME_W, out_h: int = FRAME_H):
    import cv2
    import numpy as np

    face = detect_face(image, model_path)
    if face is None:
        raise ValueError("顔が見つかりません")
    scale, tx, ty = align_matrix(face, out_w, out_h)
    matrix = np.array([[scale, 0, tx], [0, scale, ty]], dtype=np.float32)
    return cv2.warpAffine(
        image,
        matrix,
        (out_w, out_h),
        flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_REPLICATE,
    )


def list_year_photos(photo_dir: Path, birth_year: int = BIRTH_YEAR) -> list[YearPhoto]:
    photos: list[YearPhoto] = []
    for path in sorted(photo_dir.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        if not path.stem.isdigit() or len(path.stem) != 4:
            continue
        year = int(path.stem)
        photos.append(
            YearPhoto(
                year=year,
                age=year - birth_year,
                label=age_label(year, birth_year),
                path=path,
            )
        )
    photos.sort(key=lambda item: item.year)
    return photos


def prepare_year_photos(
    photo_dir: str | Path,
    aligned_dir: str | Path,
    birth_year: int = BIRTH_YEAR,
    model_path: Path | None = None,
) -> list[YearPhoto]:
    import cv2

    photo_dir = Path(photo_dir)
    aligned_dir = Path(aligned_dir)
    aligned_dir.mkdir(parents=True, exist_ok=True)
    model_path = ensure_yunet(model_path)
    photos = list_year_photos(photo_dir, birth_year)
    if len(photos) < 2:
        raise ValueError(
            f"年の写真が2枚未満です（{photo_dir} に 2013.jpg のように置いてください）"
        )
    written: list[YearPhoto] = []
    for photo in photos:
        image = cv2.imread(str(photo.path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"読めません: {photo.path}")
        try:
            aligned = align_image(image, model_path)
        except ValueError as exc:
            raise ValueError(f"{photo.path.name}: {exc}") from exc
        dest = aligned_dir / f"{photo.year}.png"
        if not cv2.imwrite(str(dest), aligned):
            raise ValueError(f"書けません: {dest}")
        written.append(
            YearPhoto(photo.year, photo.age, photo.label, dest)
        )
    manifest = {
        "birth_year": birth_year,
        "frame": [FRAME_W, FRAME_H],
        "face_center_y": FACE_CENTER_Y_RATIO,
        "face_size": FACE_SIZE_RATIO,
        "caption_center_y": CAPTION_CENTER_Y_RATIO,
        "caption_color": "#E8CB28",
        "photos": [
            {
                "year": photo.year,
                "age": photo.age,
                "label": photo.label,
                "file": photo.path.name,
            }
            for photo in written
        ],
    }
    (aligned_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return written


def _drawtext(label: str, enable: str, fontsize: int, stroke: int) -> str:
    font = font_path().replace("\\", "/")
    # ffmpeg の drawtext は ':' と ',' をエスケープする。字幕は年と年齢だけ。
    text = label.replace("\\", "\\\\").replace(":", "\\:").replace(",", "\\,")
    y_expr = f"(h*{CAPTION_CENTER_Y_RATIO}-text_h/2)"
    return (
        "drawtext="
        f"fontfile={font}:text='{text}':fontsize={fontsize}:"
        f"fontcolor={CAPTION_COLOR}:borderw={stroke}:bordercolor=black:"
        f"x=(w-text_w)/2:y={y_expr}:enable='{enable}'"
    )


def caption_filters(start_label: str, end_label: str, midpoint: float) -> str:
    fontsize = CAPTION_FONTSIZE
    stroke = CAPTION_STROKE
    first = _drawtext(start_label, f"lt(t,{midpoint:.3f})", fontsize, stroke)
    second = _drawtext(end_label, f"gte(t,{midpoint:.3f})", fontsize, stroke)
    return f"{first},{second}"


def _probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def morph_pairs(aligned_dir: Path) -> list[tuple[YearPhoto, YearPhoto]]:
    manifest_path = aligned_dir / "manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"manifest がありません: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    photos = [
        YearPhoto(
            year=item["year"],
            age=item["age"],
            label=item["label"],
            path=aligned_dir / item["file"],
        )
        for item in manifest["photos"]
    ]
    return list(zip(photos, photos[1:]))


def assemble_short(
    morph_dir: str | Path,
    aligned_dir: str | Path,
    out_path: str | Path,
    bgm_path: str | Path | None = None,
) -> Path:
    """モーフ動画を年順に繋ぐ。音は BGM だけ。ナレーションは付けない。"""
    morph_dir = Path(morph_dir)
    aligned_dir = Path(aligned_dir)
    out_path = Path(out_path)
    pairs = morph_pairs(aligned_dir)
    clips: list[tuple[Path, YearPhoto, YearPhoto]] = []
    for start, end in pairs:
        found = None
        for suffix in (".webp", ".mp4", ".webm"):
            candidate = morph_dir / f"{start.year}_{end.year}{suffix}"
            if candidate.exists():
                found = candidate
                break
        if found is None:
            raise ValueError(
                f"モーフがありません: {morph_dir}/{start.year}_{end.year}.webp"
            )
        clips.append((found, start, end))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-y"]
    if bgm_path:
        cmd += ["-stream_loop", "-1", "-i", str(bgm_path)]
    for clip, _, _ in clips:
        cmd += ["-i", str(clip)]
    filters = []
    labels = []
    audio_offset = 1 if bgm_path else 0
    for index, (clip, start, end) in enumerate(clips):
        duration = _probe_duration(clip)
        midpoint = duration / 2
        filters.append(
            f"[{audio_offset + index}:v]{caption_filters(start.label, end.label, midpoint)},"
            f"scale={FRAME_W}:{FRAME_H}:flags=lanczos,fps={FPS},format=yuv420p[v{index}]"
        )
        labels.append(f"[v{index}]")
    filters.append(
        f"{''.join(labels)}concat=n={len(clips)}:v=1:a=0[v]"
    )
    cmd += [
        "-filter_complex", ";".join(filters),
        "-map", "[v]",
    ]
    if bgm_path:
        cmd += ["-map", "0:a", "-shortest"]
    else:
        cmd += ["-an"]
    cmd += [
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        str(out_path),
    ]
    subprocess.run(cmd, check=True)
    return out_path


def api_prompt(start_image: str, end_image: str, filename_prefix: str, seed: int) -> dict:
    """ComfyUI /prompt に渡す API 形式。開始と終了の2枚をモーフする。"""
    return {
        "1": {"class_type": "UNETLoader", "inputs": {
            "unet_name": HIGH_UNET, "weight_dtype": "default"}},
        "16": {"class_type": "UNETLoader", "inputs": {
            "unet_name": LOW_UNET, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {
            "clip_name": CLIP_NAME, "type": "wan", "device": "default"}},
        "3": {"class_type": "CLIPVisionLoader", "inputs": {
            "clip_name": CLIP_VISION_NAME}},
        "4": {"class_type": "VAELoader", "inputs": {"vae_name": VAE_NAME}},
        "15": {"class_type": "LoraLoader", "inputs": {
            "model": ["1", 0], "clip": ["2", 0],
            "lora_name": HIGH_LORA, "strength_model": 1.0, "strength_clip": 1.0}},
        "17": {"class_type": "LoraLoader", "inputs": {
            "model": ["16", 0], "clip": ["2", 0],
            "lora_name": LOW_LORA, "strength_model": 1.0, "strength_clip": 1.0}},
        "5": {"class_type": "LoadImage", "inputs": {"image": start_image}},
        "20": {"class_type": "LoadImage", "inputs": {"image": end_image}},
        "6": {"class_type": "ImageScale", "inputs": {
            "image": ["5", 0], "upscale_method": "lanczos",
            "width": FRAME_W, "height": FRAME_H, "crop": "disabled"}},
        "21": {"class_type": "ImageScale", "inputs": {
            "image": ["20", 0], "upscale_method": "lanczos",
            "width": FRAME_W, "height": FRAME_H, "crop": "disabled"}},
        "7": {"class_type": "CLIPVisionEncode", "inputs": {
            "clip_vision": ["3", 0], "image": ["6", 0], "crop": "center"}},
        "22": {"class_type": "CLIPVisionEncode", "inputs": {
            "clip_vision": ["3", 0], "image": ["21", 0], "crop": "center"}},
        "8": {"class_type": "CLIPTextEncode", "inputs": {
            "clip": ["15", 1], "text": POSITIVE}},
        "9": {"class_type": "CLIPTextEncode", "inputs": {
            "clip": ["15", 1], "text": NEGATIVE}},
        "10": {"class_type": "WanFirstLastFrameToVideo", "inputs": {
            "positive": ["8", 0], "negative": ["9", 0], "vae": ["4", 0],
            "width": FRAME_W, "height": FRAME_H, "length": LENGTH, "batch_size": 1,
            "clip_vision_start_image": ["7", 0],
            "clip_vision_end_image": ["22", 0],
            "start_image": ["6", 0], "end_image": ["21", 0]}},
        "11": {"class_type": "VideoLinearCFGGuidance", "inputs": {
            "model": ["15", 0], "min_cfg": 2.0}},
        "18": {"class_type": "VideoLinearCFGGuidance", "inputs": {
            "model": ["17", 0], "min_cfg": 2.0}},
        "12": {"class_type": "KSamplerAdvanced", "inputs": {
            "model": ["11", 0], "positive": ["10", 0], "negative": ["10", 1],
            "latent_image": ["10", 2],
            "add_noise": "enable", "noise_seed": seed, "steps": 6, "cfg": 4.0,
            "sampler_name": "euler", "scheduler": "beta",
            "start_at_step": 0, "end_at_step": 3,
            "return_with_leftover_noise": "enable"}},
        "19": {"class_type": "KSamplerAdvanced", "inputs": {
            "model": ["18", 0], "positive": ["10", 0], "negative": ["10", 1],
            "latent_image": ["12", 0],
            "add_noise": "disable", "noise_seed": seed, "steps": 6, "cfg": 4.0,
            "sampler_name": "euler", "scheduler": "beta",
            "start_at_step": 3, "end_at_step": 6,
            "return_with_leftover_noise": "disable"}},
        "13": {"class_type": "VAEDecodeTiled", "inputs": {
            "samples": ["19", 0], "vae": ["4", 0],
            "tile_size": 512, "overlap": 64,
            "temporal_size": 64, "temporal_overlap": 4}},
        "14": {"class_type": "SaveAnimatedWEBP", "inputs": {
            "images": ["13", 0], "filename_prefix": filename_prefix,
            "fps": float(FPS), "lossless": True, "quality": 95, "method": "default"}},
    }


def ui_workflow() -> dict:
    """ComfyUI の Load メニュー用。中身は api_prompt と同じ接続。"""
    return {
        "version": 0.4,
        "last_node_id": 22,
        "last_link_id": 32,
        "nodes": [
            _ui_unet(1, 50, 50, HIGH_UNET, [19]),
            _ui_unet(16, 50, 680, LOW_UNET, [21]),
            _ui_clip(2, [20, 22]),
            _ui_clip_vision_loader(3, [4, 28]),
            _ui_vae(4, [5, 18]),
            _ui_lora(15, 450, 80, 19, 20, HIGH_LORA, [1], [2, 3]),
            _ui_lora(17, 450, 680, 21, 22, LOW_LORA, [23], []),
            _ui_load_image(5, 860, 50, "start.png", [6]),
            _ui_load_image(20, 860, 420, "end.png", [29]),
            _ui_scale(6, 1230, 50, 6, [7, 8]),
            _ui_scale(21, 1230, 420, 29, [30, 31]),
            _ui_clip_vision(7, 1600, 50, 4, 7, [9]),
            _ui_clip_vision(22, 1600, 420, 28, 30, [32]),
            _ui_text(8, 1600, 220, 2, POSITIVE, [10]),
            _ui_text(9, 1600, 480, 3, NEGATIVE, [11]),
            _ui_flf(10),
            _ui_cfg(11, 2100, 80, 1, [15]),
            _ui_cfg(18, 2100, 680, 23, [24]),
            _ui_sampler(12, 2500, 80, 15, 12, 13, 14, "enable", 0, 3, "enable", [16]),
            _ui_sampler(19, 2500, 480, 24, 25, 26, 16, "disable", 3, 6, "disable", [27]),
            _ui_decode(13, 2900, 300, 27, 18, [17]),
            _ui_save(14, 3280, 300, 17),
        ],
        "links": [
            [19, 1, 0, 15, 0, "MODEL"],
            [20, 2, 0, 15, 1, "CLIP"],
            [21, 16, 0, 17, 0, "MODEL"],
            [22, 2, 0, 17, 1, "CLIP"],
            [1, 15, 0, 11, 0, "MODEL"],
            [2, 15, 1, 8, 0, "CLIP"],
            [3, 15, 1, 9, 0, "CLIP"],
            [23, 17, 0, 18, 0, "MODEL"],
            [4, 3, 0, 7, 0, "CLIP_VISION"],
            [28, 3, 0, 22, 0, "CLIP_VISION"],
            [6, 5, 0, 6, 0, "IMAGE"],
            [29, 20, 0, 21, 0, "IMAGE"],
            [7, 6, 0, 7, 1, "IMAGE"],
            [30, 21, 0, 22, 1, "IMAGE"],
            [8, 6, 0, 10, 9, "IMAGE"],
            [31, 21, 0, 10, 10, "IMAGE"],
            [9, 7, 0, 10, 7, "CLIP_VISION_OUTPUT"],
            [32, 22, 0, 10, 8, "CLIP_VISION_OUTPUT"],
            [5, 4, 0, 10, 2, "VAE"],
            [10, 8, 0, 10, 0, "CONDITIONING"],
            [11, 9, 0, 10, 1, "CONDITIONING"],
            [12, 10, 0, 12, 1, "CONDITIONING"],
            [13, 10, 1, 12, 2, "CONDITIONING"],
            [14, 10, 2, 12, 3, "LATENT"],
            [15, 11, 0, 12, 0, "MODEL"],
            [16, 12, 0, 19, 3, "LATENT"],
            [25, 10, 0, 19, 1, "CONDITIONING"],
            [26, 10, 1, 19, 2, "CONDITIONING"],
            [24, 18, 0, 19, 0, "MODEL"],
            [27, 19, 0, 13, 0, "LATENT"],
            [18, 4, 0, 13, 1, "VAE"],
            [17, 13, 0, 14, 0, "IMAGE"],
        ],
        "groups": [],
        "config": {},
        "extra": {"ds": {"scale": 0.35, "offset": [0, 0]}},
    }


def _multipart(fields: dict, files: dict) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode()
        )
    for name, (filename, raw, content_type) in files.items():
        chunks.append(
            (
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"; "
                f"filename=\"{filename}\"\r\nContent-Type: {content_type}\r\n\r\n"
            ).encode()
            + raw
            + b"\r\n"
        )
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), boundary


def upload_image(base_url: str, path: Path) -> str:
    raw = path.read_bytes()
    body, boundary = _multipart(
        {"overwrite": "true"},
        {"image": (path.name, raw, "image/png")},
    )
    request = urllib.request.Request(
        base_url.rstrip("/") + "/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(request) as response:
        payload = json.loads(response.read().decode())
    return payload["name"]


def queue_year_morphs(
    aligned_dir: str | Path,
    morph_dir: str | Path,
    base_url: str = "http://127.0.0.1:8188",
    poll_seconds: float = 5.0,
    timeout_seconds: float = 3600.0,
) -> list[Path]:
    """整列済みの年写真を1組ずつ Wan の開始/終了フレームに渡してモーフを保存する。"""
    aligned_dir = Path(aligned_dir)
    morph_dir = Path(morph_dir)
    morph_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for start, end in morph_pairs(aligned_dir):
        start_name = upload_image(base_url, start.path)
        end_name = upload_image(base_url, end.path)
        seed = (start.year * 10000 + end.year) & 0xFFFFFFFF
        prompt = api_prompt(
            start_name,
            end_name,
            f"yearmorph/{start.year}_{end.year}",
            seed,
        )
        request = urllib.request.Request(
            base_url.rstrip("/") + "/prompt",
            data=json.dumps({"prompt": prompt}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request) as response:
            prompt_id = json.loads(response.read().decode())["prompt_id"]
        deadline = time.time() + timeout_seconds
        output = None
        while time.time() < deadline:
            history_url = base_url.rstrip("/") + "/history/" + prompt_id
            with urllib.request.urlopen(history_url) as response:
                history = json.loads(response.read().decode())
            if prompt_id in history:
                status = history[prompt_id].get("status", {})
                if status.get("status_str") == "error":
                    raise RuntimeError(f"ComfyUI が失敗しました: {start.year}_{end.year}")
                output = history[prompt_id].get("outputs", {})
                break
            time.sleep(poll_seconds)
        if output is None:
            raise TimeoutError(f"モーフが終わりません: {start.year}_{end.year}")
        filename = _first_output_file(output)
        view = (
            base_url.rstrip("/")
            + "/view?filename="
            + urllib.request.quote(filename["filename"])
            + "&type="
            + urllib.request.quote(filename.get("type", "output"))
            + "&subfolder="
            + urllib.request.quote(filename.get("subfolder", ""))
        )
        dest = morph_dir / f"{start.year}_{end.year}.webp"
        urllib.request.urlretrieve(view, dest)
        saved.append(dest)
        print(f"保存 {dest.name}")
    return saved


def _first_output_file(outputs: dict) -> dict:
    for node in outputs.values():
        for key in ("images", "gifs", "videos"):
            files = node.get(key) or []
            if files:
                return files[0]
    raise ValueError("ComfyUI の出力ファイルが見つかりません")


def write_ui_workflow(path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(ui_workflow(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def _ui_unet(node_id, x, y, name, links):
    return {
        "id": node_id, "type": "UNETLoader",
        "pos": [x, y], "size": [340, 98], "flags": {}, "order": 0, "mode": 0,
        "inputs": [
            {"name": "unet_name", "type": "COMBO", "widget": {"name": "unet_name"}, "link": None},
            {"name": "weight_dtype", "type": "COMBO", "widget": {"name": "weight_dtype"}, "link": None},
        ],
        "outputs": [{"name": "MODEL", "type": "MODEL", "slot_index": 0, "links": links}],
        "properties": {"Node name for S&R": "UNETLoader"},
        "widgets_values": [name, "default"],
    }


def _ui_clip(node_id, links):
    return {
        "id": node_id, "type": "CLIPLoader",
        "pos": [50, 200], "size": [340, 106], "flags": {}, "order": 2, "mode": 0,
        "inputs": [
            {"name": "clip_name", "type": "COMBO", "widget": {"name": "clip_name"}, "link": None},
            {"name": "type", "type": "COMBO", "widget": {"name": "type"}, "link": None},
            {"name": "device", "type": "COMBO", "widget": {"name": "device"}, "link": None},
        ],
        "outputs": [{"name": "CLIP", "type": "CLIP", "slot_index": 0, "links": links}],
        "properties": {"Node name for S&R": "CLIPLoader"},
        "widgets_values": [CLIP_NAME, "wan", "default"],
    }


def _ui_clip_vision_loader(node_id, links):
    return {
        "id": node_id, "type": "CLIPVisionLoader",
        "pos": [50, 360], "size": [340, 82], "flags": {}, "order": 3, "mode": 0,
        "inputs": [{"name": "clip_name", "type": "COMBO", "widget": {"name": "clip_name"}, "link": None}],
        "outputs": [{"name": "CLIP_VISION", "type": "CLIP_VISION", "slot_index": 0, "links": links}],
        "properties": {"Node name for S&R": "CLIPVisionLoader"},
        "widgets_values": [CLIP_VISION_NAME],
    }


def _ui_vae(node_id, links):
    return {
        "id": node_id, "type": "VAELoader",
        "pos": [50, 490], "size": [340, 82], "flags": {}, "order": 4, "mode": 0,
        "inputs": [{"name": "vae_name", "type": "COMBO", "widget": {"name": "vae_name"}, "link": None}],
        "outputs": [{"name": "VAE", "type": "VAE", "slot_index": 0, "links": links}],
        "properties": {"Node name for S&R": "VAELoader"},
        "widgets_values": [VAE_NAME],
    }


def _ui_lora(node_id, x, y, model_link, clip_link, name, model_out, clip_out):
    return {
        "id": node_id, "type": "LoraLoader",
        "pos": [x, y], "size": [340, 126], "flags": {}, "order": 6, "mode": 0,
        "inputs": [
            {"name": "model", "type": "MODEL", "link": model_link},
            {"name": "clip", "type": "CLIP", "link": clip_link},
            {"name": "lora_name", "type": "COMBO", "widget": {"name": "lora_name"}, "link": None},
            {"name": "strength_model", "type": "FLOAT", "widget": {"name": "strength_model"}, "link": None},
            {"name": "strength_clip", "type": "FLOAT", "widget": {"name": "strength_clip"}, "link": None},
        ],
        "outputs": [
            {"name": "MODEL", "type": "MODEL", "slot_index": 0, "links": model_out},
            {"name": "CLIP", "type": "CLIP", "slot_index": 1, "links": clip_out},
        ],
        "properties": {"Node name for S&R": "LoraLoader"},
        "widgets_values": [name, 1.0, 1.0],
    }


def _ui_load_image(node_id, x, y, filename, links):
    return {
        "id": node_id, "type": "LoadImage",
        "pos": [x, y], "size": [315, 314], "flags": {}, "order": 5, "mode": 0,
        "inputs": [
            {"name": "image", "type": "COMBO", "widget": {"name": "image"}, "link": None},
            {"name": "upload", "type": "IMAGEUPLOAD", "widget": {"name": "upload"}, "link": None},
        ],
        "outputs": [
            {"name": "IMAGE", "type": "IMAGE", "slot_index": 0, "links": links},
            {"name": "MASK", "type": "MASK", "slot_index": 1, "links": []},
        ],
        "properties": {"Node name for S&R": "LoadImage"},
        "widgets_values": [filename, "image"],
    }


def _ui_scale(node_id, x, y, image_link, links):
    return {
        "id": node_id, "type": "ImageScale",
        "pos": [x, y], "size": [315, 130], "flags": {}, "order": 12, "mode": 0,
        "inputs": [
            {"name": "image", "type": "IMAGE", "link": image_link},
            {"name": "upscale_method", "type": "COMBO", "widget": {"name": "upscale_method"}, "link": None},
            {"name": "width", "type": "INT", "widget": {"name": "width"}, "link": None},
            {"name": "height", "type": "INT", "widget": {"name": "height"}, "link": None},
            {"name": "crop", "type": "COMBO", "widget": {"name": "crop"}, "link": None},
        ],
        "outputs": [{"name": "IMAGE", "type": "IMAGE", "slot_index": 0, "links": links}],
        "properties": {"Node name for S&R": "ImageScale"},
        "widgets_values": ["lanczos", FRAME_W, FRAME_H, "disabled"],
    }


def _ui_clip_vision(node_id, x, y, vision_link, image_link, links):
    return {
        "id": node_id, "type": "CLIPVisionEncode",
        "pos": [x, y], "size": [315, 98], "flags": {}, "order": 13, "mode": 0,
        "inputs": [
            {"name": "clip_vision", "type": "CLIP_VISION", "link": vision_link},
            {"name": "image", "type": "IMAGE", "link": image_link},
            {"name": "crop", "type": "COMBO", "widget": {"name": "crop"}, "link": None},
        ],
        "outputs": [{"name": "CLIP_VISION_OUTPUT", "type": "CLIP_VISION_OUTPUT", "slot_index": 0, "links": links}],
        "properties": {"Node name for S&R": "CLIPVisionEncode"},
        "widgets_values": ["center"],
    }


def _ui_text(node_id, x, y, clip_link, text, links):
    return {
        "id": node_id, "type": "CLIPTextEncode",
        "pos": [x, y], "size": [425, 180], "flags": {}, "order": 10, "mode": 0,
        "inputs": [
            {"name": "clip", "type": "CLIP", "link": clip_link},
            {"name": "text", "type": "STRING", "widget": {"name": "text"}, "link": None},
        ],
        "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "slot_index": 0, "links": links}],
        "properties": {"Node name for S&R": "CLIPTextEncode"},
        "widgets_values": [text],
    }


def _ui_flf(node_id):
    return {
        "id": node_id, "type": "WanFirstLastFrameToVideo",
        "pos": [2100, 220], "size": [360, 290], "flags": {}, "order": 14, "mode": 0,
        "inputs": [
            {"name": "positive", "type": "CONDITIONING", "link": 10},
            {"name": "negative", "type": "CONDITIONING", "link": 11},
            {"name": "vae", "type": "VAE", "link": 5},
            {"name": "width", "type": "INT", "widget": {"name": "width"}, "link": None},
            {"name": "height", "type": "INT", "widget": {"name": "height"}, "link": None},
            {"name": "length", "type": "INT", "widget": {"name": "length"}, "link": None},
            {"name": "batch_size", "type": "INT", "widget": {"name": "batch_size"}, "link": None},
            {"name": "clip_vision_start_image", "type": "CLIP_VISION_OUTPUT", "link": 9},
            {"name": "clip_vision_end_image", "type": "CLIP_VISION_OUTPUT", "link": 32},
            {"name": "start_image", "type": "IMAGE", "link": 8},
            {"name": "end_image", "type": "IMAGE", "link": 31},
        ],
        "outputs": [
            {"name": "positive", "type": "CONDITIONING", "slot_index": 0, "links": [12, 25]},
            {"name": "negative", "type": "CONDITIONING", "slot_index": 1, "links": [13, 26]},
            {"name": "latent", "type": "LATENT", "slot_index": 2, "links": [14]},
        ],
        "properties": {"Node name for S&R": "WanFirstLastFrameToVideo"},
        "widgets_values": [FRAME_W, FRAME_H, LENGTH, 1],
    }


def _ui_cfg(node_id, x, y, model_link, links):
    return {
        "id": node_id, "type": "VideoLinearCFGGuidance",
        "pos": [x, y], "size": [340, 82], "flags": {}, "order": 8, "mode": 0,
        "inputs": [
            {"name": "model", "type": "MODEL", "link": model_link},
            {"name": "min_cfg", "type": "FLOAT", "widget": {"name": "min_cfg"}, "link": None},
        ],
        "outputs": [{"name": "MODEL", "type": "MODEL", "slot_index": 0, "links": links}],
        "properties": {"Node name for S&R": "VideoLinearCFGGuidance"},
        "widgets_values": [2],
    }


def _ui_sampler(node_id, x, y, model_link, pos_link, neg_link, latent_link, add_noise, start, end, leftover, links):
    return {
        "id": node_id, "type": "KSamplerAdvanced",
        "pos": [x, y], "size": [340, 310], "flags": {}, "order": 15, "mode": 0,
        "inputs": [
            {"name": "model", "type": "MODEL", "link": model_link},
            {"name": "positive", "type": "CONDITIONING", "link": pos_link},
            {"name": "negative", "type": "CONDITIONING", "link": neg_link},
            {"name": "latent_image", "type": "LATENT", "link": latent_link},
            {"name": "add_noise", "type": "COMBO", "widget": {"name": "add_noise"}, "link": None},
            {"name": "noise_seed", "type": "INT", "widget": {"name": "noise_seed"}, "link": None},
            {"name": "steps", "type": "INT", "widget": {"name": "steps"}, "link": None},
            {"name": "cfg", "type": "FLOAT", "widget": {"name": "cfg"}, "link": None},
            {"name": "sampler_name", "type": "COMBO", "widget": {"name": "sampler_name"}, "link": None},
            {"name": "scheduler", "type": "COMBO", "widget": {"name": "scheduler"}, "link": None},
            {"name": "start_at_step", "type": "INT", "widget": {"name": "start_at_step"}, "link": None},
            {"name": "end_at_step", "type": "INT", "widget": {"name": "end_at_step"}, "link": None},
            {"name": "return_with_leftover_noise", "type": "COMBO", "widget": {"name": "return_with_leftover_noise"}, "link": None},
        ],
        "outputs": [{"name": "LATENT", "type": "LATENT", "slot_index": 0, "links": links}],
        "properties": {"Node name for S&R": "KSamplerAdvanced"},
        "widgets_values": [add_noise, 654150814691069, "fixed", 6, 4.0, "euler", "beta", start, end, leftover],
    }


def _ui_decode(node_id, x, y, samples_link, vae_link, links):
    return {
        "id": node_id, "type": "VAEDecodeTiled",
        "pos": [x, y], "size": [315, 150], "flags": {}, "order": 17, "mode": 0,
        "inputs": [
            {"name": "samples", "type": "LATENT", "link": samples_link},
            {"name": "vae", "type": "VAE", "link": vae_link},
            {"name": "tile_size", "type": "INT", "widget": {"name": "tile_size"}, "link": None},
            {"name": "overlap", "type": "INT", "widget": {"name": "overlap"}, "link": None},
            {"name": "temporal_size", "type": "INT", "widget": {"name": "temporal_size"}, "link": None},
            {"name": "temporal_overlap", "type": "INT", "widget": {"name": "temporal_overlap"}, "link": None},
        ],
        "outputs": [{"name": "IMAGE", "type": "IMAGE", "slot_index": 0, "links": links}],
        "properties": {"Node name for S&R": "VAEDecodeTiled"},
        "widgets_values": [512, 64, 64, 4],
    }


def _ui_save(node_id, x, y, images_link):
    return {
        "id": node_id, "type": "SaveAnimatedWEBP",
        "pos": [x, y], "size": [340, 170], "flags": {}, "order": 18, "mode": 0,
        "inputs": [
            {"name": "images", "type": "IMAGE", "link": images_link},
            {"name": "filename_prefix", "type": "STRING", "widget": {"name": "filename_prefix"}, "link": None},
            {"name": "fps", "type": "FLOAT", "widget": {"name": "fps"}, "link": None},
            {"name": "lossless", "type": "BOOLEAN", "widget": {"name": "lossless"}, "link": None},
            {"name": "quality", "type": "INT", "widget": {"name": "quality"}, "link": None},
            {"name": "method", "type": "COMBO", "widget": {"name": "method"}, "link": None},
        ],
        "outputs": [],
        "properties": {},
        "widgets_values": ["yearmorph/pair", float(FPS), True, 95, "default"],
    }
