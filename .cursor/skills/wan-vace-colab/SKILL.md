---
name: wan-vace-colab
description: Run, tune, and extend the Wan2.1 VACE 14B ComfyUI Colab pipeline (Drive weights, C1–C4 controls, no paid APIs).
---

# Wan2.1 VACE Colab

Use this when a cut needs reference-guided Wan2.1 VACE 14B on Colab: face image, OpenPose, depth, and the camera vector in the control JSON. The notebooks are `wan21_vace_colab.ipynb` (A100) and `wan21_vace_download_colab.ipynb` (CPU, once).

Do not add fal or any other paid generation API. Do not download weights from the GPU notebook. Do not put secrets in the repo. Do not burn caption text into the frames. The trial script already says the picture has no text.

## Layout

- `wan21_vace_colab.ipynb` mounts Drive, installs ComfyUI, prints `COMFY_URL`, queues C1..C4, then `runtime.unassign()`.
- `wan21_vace_download_colab.ipynb` is the only notebook that fetches public files. It refuses a GPU runtime.
- `wan_vace/download_manifest.py` lists URLs and Content-Length bytes.
- `wan_vace/drive_models.py` symlinks Drive onto ComfyUI and checks the unet, UMT5, and VAE. It does not download.
- `wan_vace/guides.py` draws pose sticks and a focus map from the control JSON.
- `wan_vace/custom_nodes/vace_control/` merges those guides and applies the camera. `VaceControlSource` is lazy, so the OpenPose and Depth preprocessors do not run unless `source` is `preprocess`.
- `wan_vace/workflow.py` builds the API prompt. `wan_vace/workflows/wan21_vace_14b_api.json` is the fast C2 example.
- `wan_vace/queue.py` posts each cut and copies `C1.mp4`..`C4.mp4` to Drive.
- `wan_vace/trial/` holds the script and `C1_control.json`..`C4_control.json`.

Drive root is `/content/drive/MyDrive/minimax-h3-comfyui`. Weights live in `models/`. The face file is `refs/sakura-face-crop.jpg`. Outputs land in `outputs/trial-01/`.

## Run

CPU notebook first, then the A100 notebook, cells from the top. A100 is required (`A100`, `H100`, `H200`, or `B200` in the device name). 40GB selects `wan2.1_vace_14B_fp8_scaled.safetensors` because Ampere has no FP8 tensor cores and the fp16 file is about 32GB. 80GB selects the fp16 file. The text encoder is `umt5_xxl_fp8_e4m3fn_scaled.safetensors`. The VAE is `wan_2.1_vae.safetensors`.

The server starts with `HF_HUB_OFFLINE=1` and `HF_HOME` pointed at `models/hf-home`.

After a code change, regenerate the notebooks and the example JSON:

```bash
python -m wan_vace.make_notebooks
python -m unittest wan_vace.test_wan_vace
```

## Tune

`MODE` in the queue cell:

- `fast`: lightx2v rank64 4-step LoRA, 4 steps, cfg 1, shift 8. This is the default. The LoRA is the T2V 14B distill because VACE 14B is that family.
- `causvid`: `Wan21_CausVid_14B_T2V_lora_rank32_v2.safetensors`, same 4 steps and cfg 1. Older distill. Prefer lightx2v unless a cut needs the comparison.
- `quality`: no distill LoRA, 20 steps, cfg 5, shift 8. cfg 5 is the Wan 14B guide scale. shift 8 matches the ComfyUI VACE template.

Sampler stays `uni_pc` / `simple`. Resolution must be exact 9:16 and divisible by 16. The shipped default is 576×1024. 720×1280 and 432×768 also pass the check. Frame count is the nearest 4n+1 to `duration_s * fps`.

Optional switches, default off:

- `USE_TEACACHE`: TeaCache node, `model_type=wan2.1_t2v_14B`, `rel_l1_thresh=0.2`, start 0, end 1. Skip it on 4-step runs if motion collapses.
- `USE_SAGE` / `USE_COMPILE` in the link cell: `--use-sage-attention` when the package imports, and `--fast fp16_accumulation autotune`. Do not add `fp8_matrix_mult` on A100.
- `USE_UPSCALE`: `RealESRGAN_x2plus.pth` via `ImageUpscaleWithModel`.
- `USE_RIFE`: `RIFE VFI`, checkpoint `rife47.pth`, multiplier 2, dtype `bfloat16`, `torch_compile` false. Playback fps rises so the cut duration stays put.
- `FACE_CONSISTENCY` and `FACE_PROTECT` (default 0.35): reference image plus a state phrase, and a weaker control mask on the upper-center ellipse. Only C2 and C4. Lower the protect value if the cat's face breaks.
- `SAKURA_STRENGTH` and `STYLE_STRENGTH`: `LoraLoaderModelOnly` for `sakura_face.safetensors` and `dreamcore_style.safetensors`. Strength 0 or a missing file removes the node. Do not add a downloader for those files.

`PLATE_DIR` switches `VaceControlSource` to `preprocess` and runs `OpenposePreprocessor` plus `DepthAnythingPreprocessor` (`depth_anything_vits14.pth`, which the current aux node maps to `LiheYoung/depth-anything-small-hf` in the Drive cache).

Camera widgets are `tx ty tz rx ry rz` plus shake pixels and seed. They warp the control frames. Do not wire `WanCameraEmbedding` into `WanVaceToVideo`. That embedding belongs to `wan2.1_fun_camera`, which this graph does not load.

## Extend

A new cut needs a `C5_control.json` with the same fields as C1 (`cut`, `source_seconds`, `aspect` `9:16`, `fps`, `openpose_keyframes`, `depth.focus_sweep`, `camera_vector`, `duration_s`) and a `- C5:` line under the script's prompt heading. `control_paths()` in `wan_vace/controls.py` is the list the queue walks. Pose names the drawer knows: `back_to_camera`, `face_to_camera`, `front`, `forepaw_to_mouth`, `paw_returned`, plus `cat_jaw_deg` and `wrist_to_handle_cm`. Focus labels: `near`, `far`, `cat`, `handle`.

10 cm of wrist distance is drawn as 25% of the frame width. That scale is only for the stick guide.

Keep new public weights in `download_manifest.py` with the Content-Length you measured. Character LoRAs stay as files the person copies into `models/loras/`. After changing the prompt builder, run `python -m wan_vace.make_notebooks` so `wan21_vace_14b_api.json` and the notebooks stay aligned, then the unittest module.
