"""Load a directory of frame_*.png as a ComfyUI IMAGE batch.

The H3 VACE notebook writes this file into ComfyUI/custom_nodes before startup.
It does not download model weights.
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

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "load"
    CATEGORY = "h3"

    def load(self, directory):
        pattern = os.path.join(directory, "frame_*.png")
        paths = sorted(glob.glob(pattern))
        if not paths:
            raise FileNotFoundError(f"制御フレームがありません: {directory}")
        frames = []
        for path in paths:
            image = Image.open(path).convert("RGB")
            array = np.asarray(image).astype("float32") / 255.0
            frames.append(torch.from_numpy(array))
        batch = torch.stack(frames, dim=0)
        return (batch,)


NODE_CLASS_MAPPINGS = {"H3LoadFrameDir": H3LoadFrameDir}
NODE_DISPLAY_NAME_MAPPINGS = {"H3LoadFrameDir": "H3 Load Frame Directory"}
