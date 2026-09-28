"""Decide offload, canvas, and whether a 15s Ref2VA clip is one job or two.

Published anchors, not measured on this machine:

- Diffusers docs: the transformer is 61.7 GB bf16 and the Qwen3-VL conditioner is
  62.1 GB. One 80 GB card uses ``ComponentsManager.enable_auto_cpu_offload`` with
  ``memory_reserve_margin="12GB"``. The int8 recipe is the one whose host RAM
  note is "around 75 GB".
- Diffusers PR 14371: a Ref2VA request at the default canvas with one image
  reference does not fit on 80 GB, because the reference is encoded at a 2048
  short edge. The comparison that did run used ``height=512``, ``width=896`` and
  ``num_frames=124`` (about 5.2 seconds).
- ``before_encoder.py`` rejects 362 frames (15 seconds snapped up) because
  362 / 24 = 15.083 seconds is past ``max_duration``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from h3_runner.official import (
    CANVAS_MULTIPLE,
    CANVAS_SHORT_EDGE,
    DEFAULT_STEPS,
    FPS,
    MODEL_ID,
    README_MAX_DURATION_S,
    README_MIN_DURATION_S,
    align_num_frames,
    aligned_duration_s,
    build_video_request,
    diffusers_accepts,
    frames_for_seconds,
    largest_legal_frames,
    parse_aspect,
    resolve_canvas_size,
    spatial_tokens,
    video_latent_num_frames,
)

# PR 14371 comparison canvas that was able to run Ref2VA on one 80 GB card.
REF2VA_FIT_HEIGHT = 512
REF2VA_FIT_WIDTH = 896
REF2VA_FIT_FRAMES = 124
# Host RAM for the bf16 offload recipe: 61.7 + 62.1, plus VAE headroom.
BF16_HOST_RAM_GB = 140.0
INT8_HOST_RAM_GB = 70.0
A100_80_VRAM_GB = 70.0
# 124-frame 768p T2VA is the shape the single-80GB docs say works. 6 seconds is
# 158 frames, about 1.27× the latent frames of that example. Past 1.35×, step
# the canvas down. This slack is not an official limit.
T2VA_EXAMPLE_SLACK = 1.35
DELIVERY_WIDTH = 1080
DELIVERY_HEIGHT = 1920


def _fit_proxy(task: str) -> float:
    if task == "ref2va":
        latent = video_latent_num_frames(REF2VA_FIT_FRAMES)
        return float(latent * spatial_tokens(REF2VA_FIT_HEIGHT, REF2VA_FIT_WIDTH))
    if task == "t2va":
        height, width = resolve_canvas_size(16, 9)
        latent = video_latent_num_frames(REF2VA_FIT_FRAMES)
        return float(latent * spatial_tokens(height, width) * T2VA_EXAMPLE_SLACK)
    raise ValueError(task)


def sequence_proxy(task: str, num_frames: int, height: int, width: int) -> float:
    if task not in ("t2va", "ref2va"):
        raise ValueError(task)
    return float(video_latent_num_frames(num_frames) * spatial_tokens(height, width))


def within_fit_budget(task: str, num_frames: int, height: int, width: int) -> bool:
    return sequence_proxy(task, num_frames, height, width) <= _fit_proxy(task)


def short_edge_candidates() -> list[int]:
    return list(range(CANVAS_SHORT_EDGE, 255, -16))


def canvas_for(aspect: str, short_edge: int) -> tuple[int, int]:
    aspect_w, aspect_h = parse_aspect(aspect)
    return resolve_canvas_size(aspect_w, aspect_h, short_edge=short_edge)


def aspect_error(height: int, width: int, aspect: str) -> float:
    aspect_w, aspect_h = parse_aspect(aspect)
    target = aspect_w / aspect_h
    return abs((width / height) - target) / target


def choose_short_edges(
    task: str,
    num_frames: int,
    aspect: str,
    *,
    explicit: int | None = None,
) -> list[int]:
    """Largest fitting short edge first, then smaller rungs for an OOM retry.

    A candidate has to stay inside the published token budget and within 3% of
    the requested aspect. Rounding to 32 can otherwise pick a wider canvas.
    """
    if explicit is not None:
        smaller = [edge for edge in short_edge_candidates() if edge < int(explicit)][:2]
        return [int(explicit), *smaller]
    fitting: list[int] = []
    for edge in short_edge_candidates():
        height, width = canvas_for(aspect, edge)
        if not within_fit_budget(task, num_frames, height, width):
            continue
        if aspect_error(height, width, aspect) > 0.03:
            continue
        fitting.append(edge)
    if fitting:
        return fitting[:1] + [edge for edge in short_edge_candidates() if edge < fitting[0]][:2]
    return [256, 288]


def offload_mode(host_ram_gb: float, requested: str = "auto") -> str:
    if requested in ("bf16", "int8"):
        return requested
    if requested != "auto":
        raise ValueError(requested)
    if host_ram_gb >= BF16_HOST_RAM_GB:
        return "bf16"
    if host_ram_gb >= INT8_HOST_RAM_GB:
        return "int8"
    raise ValueError(
        f"ホストRAM {host_ram_gb:.0f} GB では公式の offload が載らない。"
        f"bf16 は約 {BF16_HOST_RAM_GB:.0f} GB、int8 は約 75 GB のホストRAMが要る。"
    )


@dataclass
class ClipJob:
    task: str
    prompt_path: Path
    image_path: Path | None
    requested_s: float
    num_frames: int
    aligned_s: float
    aspect: str
    short_edges: list[int]
    height: int
    width: int
    seed: int
    steps: int
    out_path: Path
    trim_s: float | None = None

    def canvases(self) -> list[tuple[int, int, int]]:
        """``(height, width, short_edge)`` largest first. ``short_edge`` 0 means width/height were explicit."""
        if self.short_edges == [0]:
            return [(self.height, self.width, 0)]
        found: list[tuple[int, int, int]] = []
        for edge in self.short_edges:
            height, width = canvas_for(self.aspect, edge)
            found.append((height, width, edge))
        return found

    def request_json(self, short_edge: int, image_uri: str | None) -> dict:
        return build_video_request(
            task=self.task,
            prompt=self.prompt_path.read_text(encoding="utf-8"),
            duration_s=self.requested_s,
            aspect_ratio=self.aspect,
            short_edge=short_edge,
            seed=self.seed,
            steps=self.steps,
            image_uri=image_uri if self.task == "ref2va" else None,
        )


@dataclass
class Plan:
    jobs: list[ClipJob]
    offload: str
    delivery_path: Path
    trim: bool
    notes: list[str] = field(default_factory=list)
    blocked: str | None = None

    def report(self) -> str:
        lines = list(self.notes)
        if self.blocked:
            lines.append("止める: " + self.blocked)
            return "\n".join(lines)
        lines.append(f"offload: {self.offload}")
        for job in self.jobs:
            _height, width, edge = job.canvases()[0]
            lines.append(
                f"{job.task} {job.requested_s:g}s → {job.num_frames} frames "
                f"({job.aligned_s:.3f}s) canvas {width}x{_height} "
                f"short_edge {edge} seed {job.seed}"
            )
        lines.append(f"書き出し: {self.delivery_path}")
        return "\n".join(lines)


def _clip(
    *,
    task: str,
    prompt_path: Path,
    image_path: Path | None,
    requested_s: float,
    aspect: str,
    seed: int,
    steps: int,
    out_path: Path,
    short_edge: int | None,
    width: int | None,
    height: int | None,
    num_frames: int | None = None,
    trim_s: float | None = None,
) -> ClipJob:
    if num_frames is None:
        raw = frames_for_seconds(requested_s)
        if not diffusers_accepts(raw):
            legal = largest_legal_frames(raw)
            if legal is None:
                raise ValueError(f"{requested_s:g}s は公式の 5–15 秒の枠に入らない")
            num_frames = legal
        else:
            num_frames = align_num_frames(raw)
    if width is not None or height is not None:
        if width is None or height is None:
            raise ValueError("width と height は両方指定する")
        if width % CANVAS_MULTIPLE or height % CANVAS_MULTIPLE:
            raise ValueError(f"width と height は {CANVAS_MULTIPLE} の倍数: {width}x{height}")
        edges = [0]
        canvas_h, canvas_w = height, width
    else:
        edges = choose_short_edges(task, num_frames, aspect, explicit=short_edge)
        canvas_h, canvas_w = canvas_for(aspect, edges[0])
    return ClipJob(
        task=task,
        prompt_path=prompt_path,
        image_path=image_path,
        requested_s=float(requested_s),
        num_frames=int(num_frames),
        aligned_s=num_frames / FPS,
        aspect=aspect,
        short_edges=edges,
        height=canvas_h,
        width=canvas_w,
        seed=int(seed),
        steps=int(steps),
        out_path=out_path,
        trim_s=trim_s,
    )


def one_shot_refusal(task: str, duration_s: float, aspect: str) -> str | None:
    """Why a single clip should not be the A100 80GB path. None when it is in budget."""
    raw = frames_for_seconds(duration_s)
    if not diffusers_accepts(raw):
        aligned = align_num_frames(raw)
        return (
            f"{duration_s:g}秒は round({duration_s:g}*24)={raw} フレームで、"
            f"公式の align は {aligned} フレーム ({aligned_duration_s(raw):.3f}秒)。"
            "diffusers の before_encoder.py は 5秒以上15秒以下だけ通し、"
            "362フレーム (15.083秒) は拒否する。合法な最長は 345 フレーム (14.375秒)。"
        )
    frames = align_num_frames(raw)
    height, width = canvas_for(aspect, CANVAS_SHORT_EDGE)
    if task == "ref2va" and not within_fit_budget(task, frames, height, width):
        fit_h, fit_w = canvas_for(aspect, choose_short_edges(task, frames, aspect)[0])
        return (
            "Ref2VA を公式の短辺 768（この縦横比では "
            f"{width}x{height}）で回すと、diffusers PR 14371 が 80GB で OOM とした"
            "既定キャンバスと同じ系統になる。参照画像は短辺 2048 で符号化される。"
            f"予算内の短辺に落とすと {fit_w}x{fit_h}。"
            "15秒相当のフレーム数では、PR 14371 が通せた 124 フレームより列が長い。"
        )
    return None


def check_machine(vram_gb: float, host_ram_gb: float, offload: str) -> str | None:
    if vram_gb < A100_80_VRAM_GB:
        return (
            f"GPU メモリ {vram_gb:.1f} GB。このランナーは A100 80GB 向け。"
            "40GB では公式の Ref2VA（参照画像は短辺 2048）は通らない。"
        )
    try:
        offload_mode(host_ram_gb, offload)
    except ValueError as exc:
        return str(exc)
    return None


def orbis01_plan(
    root: Path,
    out_dir: Path,
    *,
    seed: int = 0,
    steps: int = DEFAULT_STEPS,
    aspect: str = "9:16",
    vram_gb: float = 80.0,
    host_ram_gb: float = 83.0,
    offload: str = "auto",
    force_one_shot: bool = False,
) -> Plan:
    """Sakura still + the bundled prompts. Default is 6s T2VA + 9s Ref2VA."""
    root = Path(root)
    out_dir = Path(out_dir)
    image = root / "assets" / "sakura-ref.jpg"
    prompt_15 = root / "prompts" / "orbis01_ref2va_15s.txt"
    prompt_6 = root / "prompts" / "orbis01_t2va_6s.txt"
    prompt_9 = root / "prompts" / "orbis01_ref2va_9s.txt"
    delivery = out_dir / "orbis01.mp4"
    notes = [
        f"モデル: {MODEL_ID}。LoRA は使わない（公式の推論スクリプトはベースの BF16 のみ）。",
        "H3-Context-IR と H3-Regenerate-2K はオープンソースに無い。プロンプトは既に Context-IR の形。",
        "参照動画は渡さない。Ref2VA の conditions は静止画 1 枚、role=reference。",
    ]
    blocked = check_machine(vram_gb, host_ram_gb, offload)
    mode = "int8"
    if blocked is None:
        mode = offload_mode(host_ram_gb, offload)
    if force_one_shot:
        raw = frames_for_seconds(15)
        frames = largest_legal_frames(raw)
        assert frames is not None
        notes.append(
            "force-one-shot: 15秒の snap は 362 フレームで diffusers が拒否するため、"
            f"合法な {frames} フレーム ({frames / FPS:.3f}秒) にする。"
            "画は予算に入る短辺まで落とす。ノートの既定ではない。"
        )
        job = _clip(
            task="ref2va",
            prompt_path=prompt_15,
            image_path=image,
            requested_s=15,
            aspect=aspect,
            seed=seed,
            steps=steps,
            out_path=out_dir / "orbis01_oneshot.mp4",
            short_edge=None,
            width=None,
            height=None,
            num_frames=frames,
            trim_s=None,
        )
        return Plan(
            jobs=[job],
            offload=mode,
            delivery_path=out_dir / "orbis01_oneshot.mp4",
            trim=False,
            notes=notes,
            blocked=blocked,
        )
    refusal = one_shot_refusal("ref2va", 15, aspect)
    notes.append("15秒 1本にはしない。理由: " + (refusal or ""))
    notes.append(
        "メモリ: 公式は transformer 61.7GB + テキストエンコーダ 62.1GB で、80GB 1枚は "
        "CPU offload（margin 12GB）か int8 group offload。diffusers PR 14371 は、"
        "参照画像つき Ref2VA の既定キャンバスが 80GB で OOM し、通した比較は "
        "512x896・124フレーム（約5.2秒）だと書いている。15秒の列はその約2.8倍。"
    )
    notes.append(
        "代わりに予備プロンプトを 2 本出す。T2VA 6秒（顔なし）と Ref2VA 9秒（サクラの静止画）。"
        "各本は 17*n+5 に切り上がる（6秒→158フレーム=6.583秒、9秒→226フレーム=9.417秒）。"
        "つなぎの完成ファイルだけ、指定の 6.00秒と 9.00秒で切って 15.00秒にし、1080x1920 にする。"
        "切る前の mp4 も同じフォルダに残す。"
    )
    jobs = [
        _clip(
            task="t2va",
            prompt_path=prompt_6,
            image_path=None,
            requested_s=6,
            aspect=aspect,
            seed=seed,
            steps=steps,
            out_path=out_dir / "orbis01_6s.mp4",
            short_edge=None,
            width=None,
            height=None,
            trim_s=6.0,
        ),
        _clip(
            task="ref2va",
            prompt_path=prompt_9,
            image_path=image,
            requested_s=9,
            aspect=aspect,
            seed=seed,
            steps=steps,
            out_path=out_dir / "orbis01_9s.mp4",
            short_edge=None,
            width=None,
            height=None,
            trim_s=9.0,
        ),
    ]
    return Plan(jobs=jobs, offload=mode, delivery_path=delivery, trim=True, notes=notes, blocked=blocked)


def single_plan(
    *,
    task: str,
    prompt_path: Path,
    image_path: Path | None,
    duration_s: float,
    aspect: str,
    seed: int,
    steps: int,
    out_path: Path,
    short_edge: int | None,
    width: int | None,
    height: int | None,
    vram_gb: float,
    host_ram_gb: float,
    offload: str,
    force: bool,
    split_t2va: Path | None = None,
    split_ref2va: Path | None = None,
    split_image: Path | None = None,
) -> Plan:
    if not README_MIN_DURATION_S <= duration_s <= README_MAX_DURATION_S:
        raise ValueError(f"duration は {README_MIN_DURATION_S:g}〜{README_MAX_DURATION_S:g}")
    notes = [f"モデル: {MODEL_ID}。追加 LoRA は無し。"]
    blocked = check_machine(vram_gb, host_ram_gb, offload)
    mode = offload_mode(host_ram_gb, offload) if blocked is None else "int8"
    raw = frames_for_seconds(duration_s)
    legal = diffusers_accepts(raw)
    if task == "ref2va" and image_path is None:
        raise ValueError("ref2va には --image が要る")
    if task == "t2va" and image_path is not None:
        raise ValueError("t2va に参照画像は渡さない")
    use_split = (
        not force
        and task == "ref2va"
        and split_t2va is not None
        and split_ref2va is not None
        and (not legal or one_shot_refusal(task, duration_s, aspect) is not None)
    )
    if use_split:
        notes.append(one_shot_refusal(task, duration_s, aspect) or "1本にはしない。")
        notes.append("指定の分割プロンプトで 6秒 T2VA と 9秒 Ref2VA を出し、ffmpeg で 15秒にする。")
        jobs = [
            _clip(
                task="t2va",
                prompt_path=split_t2va,
                image_path=None,
                requested_s=6,
                aspect=aspect,
                seed=seed,
                steps=steps,
                out_path=out_path.with_name(out_path.stem + "_6s.mp4"),
                short_edge=short_edge,
                width=width,
                height=height,
                trim_s=6.0,
            ),
            _clip(
                task="ref2va",
                prompt_path=split_ref2va,
                image_path=split_image or image_path,
                requested_s=9,
                aspect=aspect,
                seed=seed,
                steps=steps,
                out_path=out_path.with_name(out_path.stem + "_9s.mp4"),
                short_edge=short_edge,
                width=width,
                height=height,
                trim_s=9.0,
            ),
        ]
        return Plan(jobs=jobs, offload=mode, delivery_path=out_path, trim=True, notes=notes, blocked=blocked)
    if not legal and not force:
        aligned = align_num_frames(raw)
        raise ValueError(
            f"{duration_s:g}秒は {aligned} フレーム ({aligned / FPS:.3f}秒) に切り上がり、"
            "diffusers の 5–15 秒チェックを通らない。"
            "15秒の完成尺は --preset orbis01（6秒+9秒）を使う。"
        )
    frames = align_num_frames(raw) if legal else largest_legal_frames(raw)
    if frames is None:
        raise ValueError(f"{duration_s:g}秒は生成できない")
    if not legal:
        notes.append(f"force: {frames} フレーム ({frames / FPS:.3f}秒) に縮める。")
    job = _clip(
        task=task,
        prompt_path=prompt_path,
        image_path=image_path,
        requested_s=duration_s,
        aspect=aspect,
        seed=seed,
        steps=steps,
        out_path=out_path,
        short_edge=short_edge,
        width=width,
        height=height,
        num_frames=frames,
        trim_s=None,
    )
    return Plan(jobs=[job], offload=mode, delivery_path=out_path, trim=False, notes=notes, blocked=blocked)
