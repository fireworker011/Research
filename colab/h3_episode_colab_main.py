#!/usr/bin/env python3
"""Headless Colab entry for one-click H3 episodes.

Env:
  H3_EPISODE          slug under Drive episodes/ (default bandai-district)
  H3_DRIVE_ROOT       Grokbot root; only its models/ is read (default /content/drive/MyDrive/minimax-h3-comfyui)
  H3_EPISODES_ROOT    override for <root>/episodes
  H3_COMFY_DIR        default /content/ComfyUI
  H3_EPISODE_PRESET   fast | preview | daily (overrides episode.json)
  H3_EPISODE_FRESH=1  re-render beats that already have raw/<beat>.mp4
  H3_DRY_RUN=1        no ComfyUI; synthetic clips through the real HUD/stitch path
  H3_HELPER_BRANCH    GitHub branch for episode.json / stills bootstrap
  H3_KEEP_RUNTIME=1   do not unassign the Colab runtime at the end

Never touches inbox/queued/output of the Grokbot root.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, "/content")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_episode import (
    DRIVE_ROOT_DEFAULT,
    EpisodeError,
    assert_not_production_root,
    bootstrap_episode,
    episode_root,
    load_episode,
    run_episode,
)
from h3_i2v_runtime import maybe_unassign


def main() -> int:
    slug = (os.environ.get("H3_EPISODE") or "bandai-district").strip()
    main_root = Path(os.environ.get("H3_DRIVE_ROOT") or DRIVE_ROOT_DEFAULT)
    root = episode_root(slug, main_root)
    assert_not_production_root(root, main_root)
    dry = os.environ.get("H3_DRY_RUN") == "1"
    try:
        fetched = bootstrap_episode(slug, root, branch=os.environ.get("H3_HELPER_BRANCH") or None)
        if fetched:
            print("bootstrapped from GitHub:", fetched)
        ep = load_episode(root / "episode.json")
        final = run_episode(
            ep,
            root,
            models_root=main_root / "models",
            comfy_dir=os.environ.get("H3_COMFY_DIR") or None,
            dry_run=dry,
            fresh=os.environ.get("H3_EPISODE_FRESH") == "1",
            preset_override=(os.environ.get("H3_EPISODE_PRESET") or "").strip() or None,
        )
        print("DONE", slug, final)
        return 0
    except EpisodeError as e:
        print("EPISODE FAILED:", e)
        return 1
    finally:
        if not dry:
            maybe_unassign()


if __name__ == "__main__":
    raise SystemExit(main())
