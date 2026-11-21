"""Load frame_*.png and mask_*.png as a ComfyUI IMAGE batch and MASK batch.

The H3 VACE notebook writes this file into ComfyUI/custom_nodes before startup.
It does not download model weights. These tensors are conditioning inputs only.
"""

import glob
import os

import numpy as np
import torch
from PIL import Image


class H3LoadFrameDir:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("frames", "masks")
    FUNCTION = "load"
    CATEGORY = "h3"

    def load(self, directory):
        pattern = os.path.join(directory, "frame_*.png")
        paths = sorted(glob.glob(pattern))
        if not paths:
            raise FileNotFoundError(f"制御フレームがありません: {directory}")
        frames = []
        masks = []
        for path in paths:
            name = os.path.basename(path)
            index = name[len("frame_") : -len(".png")]
            mask_path = os.path.join(directory, f"mask_{index}.png")
            if not os.path.isfile(mask_path):
                raise FileNotFoundError(f"制御マスクがありません: {mask_path}")
            image = Image.open(path).convert("RGB")
            array = np.asarray(image).astype("float32") / 255.0
            frames.append(torch.from_numpy(array))
            mask_image = Image.open(mask_path).convert("L")
            if mask_image.size != image.size:
                raise RuntimeError(f"マスクとフレームのサイズが違います: {mask_path}")
            mask_array = np.asarray(mask_image).astype("float32") / 255.0
            masks.append(torch.from_numpy(mask_array))
        return (torch.stack(frames, dim=0), torch.stack(masks, dim=0))


NODE_CLASS_MAPPINGS = {"H3LoadFrameDir": H3LoadFrameDir}
NODE_DISPLAY_NAME_MAPPINGS = {"H3LoadFrameDir": "H3 Load Frame Directory"}
