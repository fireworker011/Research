"""Drive layout and public file names. This module does not download."""

from __future__ import annotations

GITHUB_REPO = "fireworker011/Research"
BRANCH = "cursor/wan21-vace-colab-a736"

DRIVE_ROOT = "/content/drive/MyDrive/minimax-h3-comfyui"
DRIVE_MODELS = DRIVE_ROOT + "/models"
DRIVE_REFS = DRIVE_ROOT + "/refs"
FACE_REF = DRIVE_REFS + "/sakura-face-crop.jpg"
DRIVE_OUTPUT = DRIVE_ROOT + "/outputs/trial-01"

UNET_FP16 = "wan2.1_vace_14B_fp16.safetensors"
UNET_FP8 = "wan2.1_vace_14B_fp8_scaled.safetensors"
CLIP_NAME = "umt5_xxl_fp8_e4m3fn_scaled.safetensors"
VAE_NAME = "wan_2.1_vae.safetensors"
LORA_LIGHTX2V = "wan2.1_t2v_14b_lora_rank64_lightx2v_4step.safetensors"
LORA_CAUSVID = "Wan21_CausVid_14B_T2V_lora_rank32_v2.safetensors"
LORA_SAKURA = "sakura_face.safetensors"
LORA_STYLE = "dreamcore_style.safetensors"
UPSCALE_NAME = "RealESRGAN_x2plus.pth"
RIFE_NAME = "rife47.pth"

# ComfyUI model folders the GPU notebook symlinks when they exist on Drive.
LINK_DIRS = (
    "checkpoints",
    "clip_vision",
    "controlnet",
    "diffusion_models",
    "loras",
    "text_encoders",
    "upscale_models",
    "vae",
)

WIDTH = 576
HEIGHT = 1024
SHIFT = 8.0
QUALITY_STEPS = 20
QUALITY_CFG = 5.0
FAST_STEPS = 4
FAST_CFG = 1.0

RUNTIME_FILES = (
    "wan_vace/__init__.py",
    "wan_vace/paths.py",
    "wan_vace/controls.py",
    "wan_vace/prompts.py",
    "wan_vace/guides.py",
    "wan_vace/camera.py",
    "wan_vace/workflow.py",
    "wan_vace/drive_models.py",
    "wan_vace/queue.py",
    "wan_vace/download_manifest.py",
    "wan_vace/custom_nodes/vace_control/__init__.py",
    "wan_vace/custom_nodes/vace_control/nodes.py",
    "wan_vace/custom_nodes/vace_control/camera_math.py",
    "wan_vace/trial/trial-01-script_v3.md",
    "wan_vace/trial/C1_control.json",
    "wan_vace/trial/C2_control.json",
    "wan_vace/trial/C3_control.json",
    "wan_vace/trial/C4_control.json",
)
