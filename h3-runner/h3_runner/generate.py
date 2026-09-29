"""Run one H3 clip with the diffusers calls the MiniMax README points at.

bf16 path: the "one 80 GB card" recipe in the diffusers MiniMax-H3 docs
(``ComponentsManager.enable_auto_cpu_offload``, margin ``"12GB"``).

int8 path: the same docs' consumer-card recipe (``TorchAoConfig`` int8 weight
only, block offload on the transformer, leaf offload on the text encoder).
Colab high-RAM is about 83 GB of host RAM, which is the int8 note ("around
75 GB"), not the 61.7+62.1 GB bf16 pair.

No LoRA is loaded. The released checkpoints are the CFG-distilled bf16 weights.
"""

from __future__ import annotations

import gc
import json
from pathlib import Path

import torch
from diffusers import ComponentsManager, MiniMaxH3Transformer3DModel, ModularPipeline, TorchAoConfig
from diffusers.hooks import apply_group_offloading
from diffusers.modular_pipelines.minimax_h3 import MiniMaxH3ImageReference
from diffusers.utils.export_utils import encode_video
from torchao.quantization import Int8WeightOnlyConfig
from transformers import Qwen3VLForConditionalGeneration
from transformers import TorchAoConfig as TransformersTorchAoConfig

from h3_runner.ffmpeg_join import join_clips
from h3_runner.official import FPS
from h3_runner.planner import ClipJob, Plan
from h3_runner.weights import prepare

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
    if task == "t2va":
        return pipe.transformer
    raise ValueError(task)


def _load_bf16(task: str, model_dir: Path) -> tuple[ModularPipeline, ComponentsManager]:
    # local_files_only plus the local directory: the index's hub id must not fetch FL2VA/ or Ref2VA/.
    manager = ComponentsManager()
    pipe = ModularPipeline.from_pretrained(
        str(model_dir),
        workflow=task,
        components_manager=manager,
        local_files_only=True,
    )
    pipe.load_components(
        dtype=torch.bfloat16,
        pretrained_model_name_or_path=str(model_dir),
        local_files_only=True,
    )
    manager.enable_auto_cpu_offload(device="cuda", memory_reserve_margin="12GB")
    # _flash_3_hub is the Hopper kernel in the official docs (compute capability 9).
    # A100 is 8. Blackwell (RTX PRO 6000) is 10, so leave its default attention.
    major, _minor = torch.cuda.get_device_capability()
    denoiser = _denoiser(pipe, task)
    if major == 9 and hasattr(denoiser, "set_attention_backend"):
        denoiser.set_attention_backend("_flash_3_hub")
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


def _load_int8(task: str, model_dir: Path) -> tuple[ModularPipeline, None]:
    # Official snippet: build the pipeline, replace the two large modules, then
    # load_components(workflow=) so the other transformer partition stays unloaded.
    pipe = ModularPipeline.from_pretrained(str(model_dir), local_files_only=True)
    text_encoder = _quantized_text_encoder(model_dir)
    if task == "ref2va":
        pipe.update_components(
            transformer_ref=_quantized_transformer(model_dir, "transformer_ref"),
            text_encoder=text_encoder,
        )
    elif task == "t2va":
        pipe.update_components(
            transformer=_quantized_transformer(model_dir, "transformer"),
            text_encoder=text_encoder,
        )
    else:
        raise ValueError(task)
    pipe.load_components(
        workflow=task,
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
    return pipe, None


def load_pipeline(task: str, offload: str, model_dir: Path) -> ModularPipeline:
    if offload == "bf16":
        pipe, _manager = _load_bf16(task, model_dir)
        return pipe
    if offload == "int8":
        pipe, _manager = _load_int8(task, model_dir)
        return pipe
    raise ValueError(offload)


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
        if job.image_path is None:
            raise ValueError("ref2va clip has no image")
        kwargs["references"] = [MiniMaxH3ImageReference.from_file(str(job.image_path))]
    return pipe(**kwargs)


def generate_clip(job: ClipJob, *, offload: str, model_dir: Path) -> Path:
    job.out_path.parent.mkdir(parents=True, exist_ok=True)
    last_error: BaseException | None = None
    for height, width, edge in job.canvases():
        pipe = None
        results = None
        try:
            print(f"load {job.task} offload={offload} canvas={width}x{height} frames={job.num_frames}", flush=True)
            pipe = load_pipeline(job.task, offload, model_dir)
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
            request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            results = _call_pipe(pipe, job, height=height, width=width)
            encode_video(
                results["videos"][0],
                fps=FPS,
                output_path=str(job.out_path),
                audio=results["audio"][0],
                audio_sample_rate=results["sampling_rate"],
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
    written: list[Path] = []
    for job in plan.jobs:
        # T2VA first. prepare() deletes transformer_ref/ or transformer/ before the next download.
        local = prepare(model_dir, job.task)
        written.append(generate_clip(job, offload=plan.offload, model_dir=local))
    if plan.trim and len(plan.jobs) > 1:
        parts = []
        for job, path in zip(plan.jobs, written):
            if job.trim_s is None:
                raise ValueError(f"{job.out_path.name} に trim 秒が無い")
            parts.append((path, job.trim_s))
        join_clips(parts, plan.delivery_path)
        print(f"joined {plan.delivery_path}", flush=True)
    return 0
