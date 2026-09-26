#!/usr/bin/env python3
"""Colab entry for the Wan 2.2 hospital episode. The human runs this. It does not run on import.

Output root is OneDrive (WAN_ONEDRIVE_ROOT). Google Drive is rejected.
H3 notebooks stay as they are. This file only draws with Wan.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, "/content")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_episode import EpisodeError, load_episode
from h3_episode_packs import canonical_episode
from wan_colab_setup import start_wan_comfy
from wan_episode import episode_work_root, onedrive_root, run_wan_episode


def main() -> int:
    raw_slug = (os.environ.get("WAN_EPISODE") or "hospital-exit-adult").strip()
    slug = canonical_episode(raw_slug) or raw_slug
    root = episode_work_root(slug, onedrive_root())
    script = Path(os.environ.get("WAN_EPISODE_JSON") or "")
    if not script.is_file():
        script = Path(__file__).resolve().parents[1] / "minimaxh3" / "episodes" / slug / "episode.json"
    if not script.is_file():
        print("EPISODE FAILED: episode.json not found", script)
        return 1
    try:
        ep = load_episode(script)
        comfy = os.environ.get("WAN_COMFY_DIR") or "/content/ComfyUI"
        if os.environ.get("WAN_DRY_RUN") != "1":
            start_wan_comfy(Path(comfy))
        final = run_wan_episode(
            ep,
            root,
            loras_dir=onedrive_root() / "models" / "loras",
            comfy_dir=os.environ.get("WAN_COMFY_DIR") or None,
            dry_run=os.environ.get("WAN_DRY_RUN") == "1",
            fresh=os.environ.get("WAN_EPISODE_FRESH") == "1",
            preset_override=(os.environ.get("WAN_EPISODE_PRESET") or "").strip() or None,
            camera_pack_override=(os.environ.get("WAN_EPISODE_CAMERA") or "").strip() or None,
            connect_override=(os.environ.get("WAN_EPISODE_CONNECT") or "").strip() or None,
            end_connect_override=(os.environ.get("WAN_EPISODE_END_CONNECT") or "").strip() or None,
            story_override=(os.environ.get("WAN_EPISODE_STORY") or "").strip() or None,
            invite_pose_override=(os.environ.get("WAN_EPISODE_INVITE_POSE") or "").strip() or None,
            toilet_override=(os.environ.get("WAN_EPISODE_TOILET") or "").strip() or None,
            gin_override=(os.environ.get("WAN_EPISODE_GIN") or "").strip() or None,
            tsuno_override=(os.environ.get("WAN_EPISODE_TSUNO") or "").strip() or None,
            dog_override=(os.environ.get("WAN_EPISODE_DOG") or "").strip() or None,
            species_override=(os.environ.get("WAN_EPISODE_SPECIES") or "").strip() or None,
            appear_override=(os.environ.get("WAN_EPISODE_APPEAR") or "").strip() or None,
            scenes_override=(os.environ.get("WAN_EPISODE_SCENES") or "").strip() or None,
        )
    except EpisodeError as exc:
        print("EPISODE FAILED:", exc)
        return 1
    print("DONE", slug, final)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
