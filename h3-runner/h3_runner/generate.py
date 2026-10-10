"""Run one H3 clip with the diffusers calls the MiniMax README points at.

bf16 path: the "one 80 GB card" recipe in the diffusers MiniMax-H3 docs
(``ComponentsManager.enable_auto_cpu_offload``, margin ``"12GB"``). LoRA weights
are loaded and fused before that offload. Leaving them unfused costs about
9–13% per still. An FL2V LoRA is not loaded into ``transformer_ref``.

int8 path: the same docs' consumer-card recipe (``TorchAoConfig`` int8 weight
only, block offload on the transformer, leaf offload on the text encoder).
LoRA is not applied on this path.
"""

from __future__ import annotations

import gc
import json
import shutil
import time
from pathlib import Path

import torch
from diffusers import ComponentsManager, MiniMaxH3Transformer3DModel, ModularPipeline, TorchAoConfig
from diffusers.hooks import apply_group_offloading
from diffusers.modular_pipelines.minimax_h3 import (
    MiniMaxH3AudioReference,
    MiniMaxH3ImageReference,
    MiniMaxH3VideoReference,
)
from diffusers.utils.export_utils import encode_video
from PIL import Image
from torchao.quantization import Int8WeightOnlyConfig
from transformers import Qwen3VLForConditionalGeneration
from transformers import TorchAoConfig as TransformersTorchAoConfig

from h3_runner.ffmpeg_join import clip_is_done, join_clips
from h3_runner.loras import LoraSpec, reject_pruned_adaln
from h3_runner.official import AUDIO_FLOW_SHIFT, FPS, pipeline_workflow
from h3_runner.planner import ClipJob, Plan
from h3_runner.slice_media import ensure_reference_slice
from h3_runner.weights import failure_text, local_encode_path, require_present

_TRANSFORMER_SKIP = [
    "proj_in",
    "audio_proj_in",
    "context_embedder",
    "time_embedder",
    "time_proj",
    "token_refiner",
    "norm_out",
    "proj_out",
    "audio_proj_out",
]
_TEXT_SKIP = [
    "model.visual",
    "model.language_model.embed_tokens",
    "model.language_model.norm",
    "lm_head",
]


def _is_oom(exc: BaseException) -> bool:
    if isinstance(exc, torch.cuda.OutOfMemoryError):
        return True
    text = str(exc).lower()
    return "out of memory" in text or "cuda oom" in text


def _release() -> None:
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def _denoiser(pipe: ModularPipeline, task: str):
    if task == "ref2va":
        return pipe.transformer_ref
    if task in ("t2va", "fl2va", "i2va"):
        return pipe.transformer
    raise ValueError(task)


def _apply_shifts(pipe: ModularPipeline, video_shift: float) -> None:
    pipe.scheduler.set_shift(float(video_shift))
    audio = getattr(pipe, "audio_scheduler", None)
    if audio is not None and hasattr(audio, "set_shift"):
        audio.set_shift(float(AUDIO_FLOW_SHIFT))
    print(f"shift video={float(video_shift):g} audio={AUDIO_FLOW_SHIFT:g}", flush=True)


def _fuse_loras(pipe: ModularPipeline, task: str, loras: list[LoraSpec]) -> None:
    if not loras:
        return
    for spec in loras:
        reject_pruned_adaln(spec.path)
    into_ref = task == "ref2va"
    for spec in loras:
        print(
            f"lora {spec.name} scale={spec.scale:g} into_transformer_ref={into_ref} path={spec.path}",
            flush=True,
        )
        pipe.load_lora_weights(
            str(spec.path),
            adapter_name=spec.name,
            load_into_transformer_ref=into_ref,
        )
    pipe.set_adapters([spec.name for spec in loras], [spec.scale for spec in loras])
    pipe.fuse_lora()
    pipe.unload_lora_weights()


def _load_bf16(
    task: str,
    model_dir: Path,
    loras: list[LoraSpec],
    video_shift: float,
) -> tuple[ModularPipeline, ComponentsManager]:
    # local_files_only plus the local directory: the index's hub id must not fetch FL2VA/ or Ref2VA/.
    manager = ComponentsManager()
    pipe = ModularPipeline.from_pretrained(
        str(model_dir),
        workflow=pipeline_workflow(task),
        components_manager=manager,
        local_files_only=True,
    )
    pipe.load_components(
        dtype=torch.bfloat16,
        pretrained_model_name_or_path=str(model_dir),
        local_files_only=True,
    )
    # Fuse before offload. An unfused LoRA adds about 9–13% per still.
    _fuse_loras(pipe, task, loras)
    manager.enable_auto_cpu_offload(device="cuda", memory_reserve_margin="12GB")
    _apply_shifts(pipe, video_shift)
    # _flash_3_hub is the Hopper kernel in the official docs (compute capability 9).
    # Blackwell (RTX PRO 6000 is 12, B200 is 10) has no kernel for that hub build.
    major, _minor = torch.cuda.get_device_capability()
    denoiser = _denoiser(pipe, task)
    if hasattr(denoiser, "set_attention_backend"):
        if major == 9:
            denoiser.set_attention_backend("_flash_3_hub")
        elif major >= 10:
            denoiser.set_attention_backend("native")
            print(f"attention native (compute capability {major})", flush=True)
    return pipe, manager


def _quantized_transformer(model_dir: Path, subfolder: str) -> MiniMaxH3Transformer3DModel:
    return MiniMaxH3Transformer3DModel.from_pretrained(
        str(model_dir),
        subfolder=subfolder,
        dtype=torch.bfloat16,
        quantization_config=TorchAoConfig(
            Int8WeightOnlyConfig(version=2),
            modules_to_not_convert=list(_TRANSFORMER_SKIP),
        ),
        low_cpu_mem_usage=False,
        local_files_only=True,
    )


def _quantized_text_encoder(model_dir: Path) -> Qwen3VLForConditionalGeneration:
    return Qwen3VLForConditionalGeneration.from_pretrained(
        str(model_dir),
        subfolder="text_encoder",
        dtype=torch.bfloat16,
        quantization_config=TransformersTorchAoConfig(
            Int8WeightOnlyConfig(version=2),
            modules_to_not_convert=list(_TEXT_SKIP),
        ),
        local_files_only=True,
    )


def _load_int8(task: str, model_dir: Path, video_shift: float) -> tuple[ModularPipeline, None]:
    # Official snippet: build the pipeline, replace the two large modules, then
    # load_components(workflow=) so the other transformer partition stays unloaded.
    pipe = ModularPipeline.from_pretrained(str(model_dir), local_files_only=True)
    text_encoder = _quantized_text_encoder(model_dir)
    if task == "ref2va":
        pipe.update_components(
            transformer_ref=_quantized_transformer(model_dir, "transformer_ref"),
            text_encoder=text_encoder,
        )
    elif task in ("t2va", "fl2va", "i2va"):
        pipe.update_components(
            transformer=_quantized_transformer(model_dir, "transformer"),
            text_encoder=text_encoder,
        )
    else:
        raise ValueError(task)
    pipe.load_components(
        workflow=pipeline_workflow(task),
        dtype=torch.bfloat16,
        pretrained_model_name_or_path=str(model_dir),
        local_files_only=True,
    )
    denoiser = _denoiser(pipe, task)
    denoiser.requires_grad_(False)
    pipe.text_encoder.requires_grad_(False)
    offload = dict(onload_device=torch.device("cuda"), offload_device=torch.device("cpu"), use_stream=True)
    denoiser.enable_group_offload(offload_type="block_level", num_blocks_per_group=1, **offload)
    apply_group_offloading(pipe.text_encoder.model, offload_type="leaf_level", **offload)
    pipe.vae.to("cuda")
    pipe.audio_vae.to("cuda")
    _apply_shifts(pipe, video_shift)
    return pipe, None


def _align_rope_device(pipe: ModularPipeline, task: str) -> None:
    """Put the RoPE buffer on the same device as ``position_ids``.

    Pinned diffusers ``5ff8e59`` only casts the ids to float32. ``inv_freq`` is a
    non-persistent buffer, so CPU offload can leave it on CPU while the ids are
    on CUDA. That raises on the first denoiser step, after ``request.json``.
    """
    rope = getattr(_denoiser(pipe, task), "rope", None)
    if rope is None or getattr(rope, "_device_aligned", False):
        return
    original = rope.forward

    def forward(position_ids: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        inv = rope._buffers.get("inv_freq")
        if inv is not None and inv.device != position_ids.device:
            rope._buffers["inv_freq"] = inv.to(device=position_ids.device)
        return original(position_ids)

    rope.forward = forward
    rope._device_aligned = True


def load_pipeline(
    task: str,
    offload: str,
    model_dir: Path,
    loras: list[LoraSpec],
    video_shift: float,
) -> ModularPipeline:
    if offload == "bf16":
        pipe, _manager = _load_bf16(task, model_dir, loras, video_shift)
    elif offload == "int8":
        if loras:
            print("int8 経路では LoRA を無効にする。", flush=True)
        pipe, _manager = _load_int8(task, model_dir, video_shift)
    else:
        raise ValueError(offload)
    _align_rope_device(pipe, task)
    return pipe


def _call_pipe(
    pipe: ModularPipeline,
    job: ClipJob,
    *,
    height: int,
    width: int,
) -> dict:
    prompt = job.prompt_path.read_text(encoding="utf-8")
    generator = torch.Generator(device="cpu").manual_seed(int(job.seed))
    kwargs = {
        "prompt": prompt,
        "num_frames": int(job.num_frames),
        "height": int(height),
        "width": int(width),
        "num_inference_steps": int(job.steps),
        "generator": generator,
        "output": ["videos", "audio", "sampling_rate"],
    }
    if job.task == "ref2va":
        references = []
        if job.image_path is not None:
            references.append(MiniMaxH3ImageReference.from_file(str(job.image_path)))
        if job.video_path is not None:
            media = ensure_reference_slice(
                job.video_path,
                job.video_start_s,
                job.video_end_s,
                pad_to_s=job.aligned_s,
            )
            print(f"参照動画 {media}", flush=True)
            references.append(MiniMaxH3VideoReference.from_file(str(media)))
        if job.audio_path is not None:
            references.append(MiniMaxH3AudioReference.from_file(str(job.audio_path)))
        if not references:
            raise ValueError("ref2va clip has no reference")
        kwargs["references"] = references
    elif job.task in ("fl2va", "i2va"):
        if job.image_path is None:
            raise ValueError(f"{job.task} clip has no image")
        still = Image.open(job.image_path)
        try:
            frame = still.convert("RGB")
            if frame is still:
                frame = still.copy()
            frame.load()
        finally:
            still.close()
        kwargs["image"] = frame
    elif job.task != "t2va":
        raise ValueError(job.task)
    return pipe(**kwargs)


def _attach_stage_timers(pipe: ModularPipeline, task: str) -> dict[str, float]:
    """Wall time of text-encoder, denoiser, and VAE forwards, after CUDA sync."""
    totals = {"text": 0.0, "denoise": 0.0, "vae": 0.0}

    def wrap(module, key: str) -> None:
        original = module.forward

        def wrapped(*args, **kwargs):
            if torch.cuda.is_available():
                torch.cuda.synchronize()
            start = time.perf_counter()
            try:
                return original(*args, **kwargs)
            finally:
                if torch.cuda.is_available():
                    torch.cuda.synchronize()
                totals[key] += time.perf_counter() - start

        module.forward = wrapped

    text = getattr(pipe, "text_encoder", None)
    if text is not None:
        wrap(text, "text")
    wrap(_denoiser(pipe, task), "denoise")
    for name in ("vae", "audio_vae"):
        module = getattr(pipe, name, None)
        if module is not None:
            wrap(module, "vae")
    return totals


def _note_failure(out_path: Path, stage: str, exc: BaseException) -> None:
    text = failure_text(stage, exc)
    print(text, flush=True)
    note = out_path.with_suffix(".error.txt")
    try:
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(text + "\n", encoding="utf-8")
        print("理由を書いた", note, flush=True)
    except OSError as write_exc:
        print("理由のファイルは書けなかった", write_exc, flush=True)


def _clear_failure(out_path: Path) -> None:
    note = out_path.with_suffix(".error.txt")
    if note.is_file():
        note.unlink()


def generate_clip(
    job: ClipJob,
    *,
    offload: str,
    model_dir: Path,
    loras: list[LoraSpec] | None = None,
    video_shift: float | None = None,
) -> Path:
    job.out_path.parent.mkdir(parents=True, exist_ok=True)
    applied = list(loras or [])
    shift = float(job.video_shift if video_shift is None else video_shift)
    last_error: BaseException | None = None
    for height, width, edge in job.canvases():
        pipe = None
        results = None
        try:
            print(f"load {job.task} offload={offload} canvas={width}x{height} frames={job.num_frames}", flush=True)
            started = time.perf_counter()
            pipe = load_pipeline(job.task, offload, model_dir, applied, shift)
            load_s = time.perf_counter() - started
            totals = _attach_stage_timers(pipe, job.task)
            image_uri = None
            if job.image_path is not None:
                image_uri = job.image_path.resolve().as_uri()
            request = job.request_json(edge if edge else max(width, height), image_uri)
            request["resolved"] = {
                "height": height,
                "width": width,
                "num_frames": job.num_frames,
                "offload": offload,
            }
            request_path = job.out_path.with_suffix(".request.json")
            request_path.parent.mkdir(parents=True, exist_ok=True)
            request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            encode_path = local_encode_path(job.out_path)
            try:
                print("推論開始", flush=True)
                results = _call_pipe(pipe, job, height=height, width=width)
            except Exception as exc:
                if _is_oom(exc):
                    raise
                _note_failure(job.out_path, "推論", exc)
                raise
            print(f"mp4 を書く {encode_path}", flush=True)
            try:
                encode_path.parent.mkdir(parents=True, exist_ok=True)
                encode_video(
                    results["videos"][0],
                    fps=FPS,
                    output_path=str(encode_path),
                    audio=results["audio"][0],
                    audio_sample_rate=results["sampling_rate"],
                )
                if encode_path != job.out_path:
                    job.out_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(encode_path, job.out_path)
                    print(f"コピーした {job.out_path} bytes {job.out_path.stat().st_size}", flush=True)
            except Exception as exc:
                if _is_oom(exc):
                    raise
                _note_failure(job.out_path, "mp4", exc)
                if encode_path.is_file() and encode_path != job.out_path:
                    print(
                        f"ローカルには残っている {encode_path} {encode_path.stat().st_size} bytes",
                        flush=True,
                    )
                raise
            _clear_failure(job.out_path)
            print(
                f"TIMING load={load_s:.3f} text={totals['text']:.3f} "
                f"denoise={totals['denoise']:.3f} vae={totals['vae']:.3f}",
                flush=True,
            )
            print(f"wrote {job.out_path}", flush=True)
            return job.out_path
        except Exception as exc:
            if not _is_oom(exc):
                raise
            last_error = exc
            print(f"OOM at {width}x{height}: {exc}", flush=True)
        finally:
            # Drop the pipeline before the next rung. The names stay in this frame until cleared.
            pipe = None
            results = None
            _release()
    raise RuntimeError(f"OOM が続き、{job.out_path.name} は出なかった") from last_error


def run_plan(plan: Plan, model_dir: Path) -> int:
    if plan.blocked:
        raise SystemExit(plan.blocked)
    # Reads the Drive snapshot. Does not download.
    require_present(model_dir, [job.task for job in plan.jobs])
    written: list[Path] = []
    made_new = False
    total = len(plan.jobs)
    for index, job in enumerate(plan.jobs, start=1):
        minimum = job.trim_s if job.trim_s is not None else job.requested_s
        print(f"進捗 {index}/{total} {job.task} → {job.out_path}", flush=True)
        if clip_is_done(job.out_path, min_seconds=minimum):
            print(f"スキップ: {job.out_path} は Drive にある", flush=True)
            written.append(job.out_path)
            continue
        print(f"生成開始 {index}/{total} {job.task}", flush=True)
        written.append(
            generate_clip(
                job,
                offload=plan.offload,
                model_dir=model_dir,
                loras=plan.loras,
                video_shift=plan.video_shift,
            )
        )
        made_new = True
        print(
            f"Drive に保存 {index}/{total}: {job.out_path} bytes {job.out_path.stat().st_size}",
            flush=True,
        )
    if plan.trim and len(plan.jobs) > 1:
        delivery_min = sum(job.trim_s or 0 for job in plan.jobs)
        if clip_is_done(plan.delivery_path, min_seconds=delivery_min) and not made_new:
            print(f"スキップ: {plan.delivery_path} は Drive にある", flush=True)
            return 0
        parts = []
        for job, path in zip(plan.jobs, written):
            if job.trim_s is None:
                raise ValueError(f"{job.out_path.name} に trim 秒が無い")
            parts.append((path, job.trim_s))
        print(f"進捗 結合 → {plan.delivery_path}", flush=True)
        join_clips(parts, plan.delivery_path)
        print(f"Drive に保存: {plan.delivery_path}", flush=True)
    return 0
