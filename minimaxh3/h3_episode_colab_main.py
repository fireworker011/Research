#!/usr/bin/env python3
"""Headless Colab entry for one-click H3 episodes.

Env:
  H3_EPISODE          slug under Drive episodes/ (default bandai-district). Japanese dropdown labels are canonicalized.
  H3_DRIVE_ROOT       Grokbot root; only its models/ is read (default /content/drive/MyDrive/minimax-h3-comfyui)
  H3_EPISODES_ROOT    override for <root>/episodes
  H3_COMFY_DIR        default /content/ComfyUI
    H3_EPISODE_PRESET   speed | balance | quality（日本語: スピード / バランス / 質）
  H3_EPISODE_CAMERA   side2d | action3d（日本語: 横スク / 3Dアクション）
  H3_EPISODE_CONNECT  t2v | chain | landing（日本語: カット / 前の最終フレームから続ける / 用意した最終フレームへ着く。カットとチェーンの1本目は T2V）
  H3_EPISODE_END_CONNECT  t2v | chain | follow（日本語: シーン終わりはカット / 次のシーンへ続ける / 1番のつなぎに従う。行為のあとの歩き）
  H3_EPISODE_COMBAT   off | on（日本語: 格闘LoRAオフ / オン。オンはハイメモリ専用）
  H3_EPISODE_STORY    accept | invite | evade | fight_win | fight_lose（日本語: 受け入れる / 誘う / 回避 / 戦って勝つ / 戦って負ける。病棟の構成）
  H3_EPISODE_INVITE_POSE  all_fours | m_open | ride（日本語: 四つん這い股広げ / M字開脚仰向け / ベロチュー→じゅぼ→騎乗位。病棟の誘う）
  H3_EPISODE_TOILET   off | pee | masturbate | tentacle（日本語: 行かない / 小便 / オナニー / 触手。病棟の道中）
  H3_EPISODE_GIN      off | taken | fuck | invite_doggy（日本語: 灰色・出ない / 犯される / 犯す / 誘う後背。病棟の追加）
  H3_EPISODE_TSUNO    off | accept_stand | invite_stand（日本語: 角・出ない / 受け入れる立ちバック / 誘う立ちバック。病棟の追加）
  H3_EPISODE_APPEAR   miki,rei,kana,shino（病棟の登場。外すとその人のシーンを飛ばす）
  H3_EPISODE_SCENES   miki=evade,rei=invite_ride,...（病棟のシーンごと。inherit は 5番に従う。戦い構成は無視）
  H3_EPISODE_REI_MAST skip|stand|back（レイ脱出の合間おな）
  H3_EPISODE_REI_TOILET ta|tb|tc（レイ脱出の糞トイレ）
  H3_EPISODE_REI_BEAST accept|invite|evade（レイ脱出の敵1。立ち円口 / 仰向け股開き / 飛ばす）
  H3_EPISODE_REI_MOTH tail|mouth（レイ脱出の蛾女）
  H3_EPISODE_REI_ATTACK rei|her（レイ脱出の襲う側）
  H3_EPISODE_REI_KISS off|on（レイ脱出のキス。顔。フェラではない）
  H3_EPISODE_REI_ORAL skip|her|rei（レイ脱出の口。フェラ / クンニ）
  H3_EPISODE_REI_POSE fours|wall|straddle|supine（レイ脱出の体位は動き）
  H3_EPISODE_FRESH=1  re-render beats that already have raw/<beat>.mp4
  H3_DRY_RUN=1        no ComfyUI; synthetic clips through the real HUD/stitch path
  H3_HELPER_BRANCH    GitHub branch for episode.json / stills bootstrap
  H3_KEEP_RUNTIME=1   keep the Colab runtime (default; unassign is off)
  H3_UNASSIGN_RUNTIME=1  opt in to runtime.unassign() after the run

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
from h3_episode_packs import canonical_episode
from h3_i2v_runtime import maybe_unassign


def main() -> int:
    raw_slug = (os.environ.get("H3_EPISODE") or "bandai-district").strip()
    slug = canonical_episode(raw_slug) or raw_slug
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
            camera_pack_override=(os.environ.get("H3_EPISODE_CAMERA") or "").strip() or None,
            connect_override=(os.environ.get("H3_EPISODE_CONNECT") or "").strip() or None,
            end_connect_override=(os.environ.get("H3_EPISODE_END_CONNECT") or "").strip() or None,
            combat_override=(os.environ.get("H3_EPISODE_COMBAT") or "").strip() or None,
            story_override=(os.environ.get("H3_EPISODE_STORY") or "").strip() or None,
            invite_pose_override=(os.environ.get("H3_EPISODE_INVITE_POSE") or "").strip() or None,
            toilet_override=(os.environ.get("H3_EPISODE_TOILET") or "").strip() or None,
            gin_override=(os.environ.get("H3_EPISODE_GIN") or "").strip() or None,
            tsuno_override=(os.environ.get("H3_EPISODE_TSUNO") or "").strip() or None,
            appear_override=(os.environ.get("H3_EPISODE_APPEAR") or "").strip() or None,
            scenes_override=(os.environ.get("H3_EPISODE_SCENES") or "").strip() or None,
            rei_mast_override=(os.environ.get("H3_EPISODE_REI_MAST") or "").strip() or None,
            rei_toilet_override=(os.environ.get("H3_EPISODE_REI_TOILET") or "").strip() or None,
            rei_beast_override=(os.environ.get("H3_EPISODE_REI_BEAST") or "").strip() or None,
            rei_moth_override=(os.environ.get("H3_EPISODE_REI_MOTH") or "").strip() or None,
            rei_attack_override=(os.environ.get("H3_EPISODE_REI_ATTACK") or "").strip() or None,
            rei_kiss_override=(os.environ.get("H3_EPISODE_REI_KISS") or "").strip() or None,
            rei_oral_override=(os.environ.get("H3_EPISODE_REI_ORAL") or "").strip() or None,
            rei_pose_override=(os.environ.get("H3_EPISODE_REI_POSE") or "").strip() or None,
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
