"""Chains: one base image and an ordered set of dependent stages.

A chain is backend neutral. ``category`` is an opaque label handed to the
backend. ``stage_order`` lists stages in dependency order. The stages a job
asks for are the prefix up to the last stage any scene needs, because a later
stage cannot run without the earlier ones.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scene_trials.errors import ConfigError
from scene_trials.project import load_yaml_file
from scene_trials.scenes import Scene, find_scene

_CHAIN_KEYS = frozenset({"category", "base", "route_tags", "stage_order", "scenes", "needs_face_visible"})


@dataclass(frozen=True)
class ChainSpec:
    chain_id: str
    category: str
    base_ref: object
    route_tags: tuple[str, ...]
    stage_order: tuple[str, ...]
    scene_refs: tuple[tuple[object, str], ...]
    needs_face_visible: bool


@dataclass(frozen=True)
class ResolvedChain:
    chain_id: str
    category: str
    base: Scene
    route_tags: tuple[str, ...]
    stages: tuple[str, ...]
    scene_stages: tuple[tuple[str, str], ...]
    needs_face_visible: bool

    def stage_for(self, scene_id: str) -> str | None:
        for found, stage in self.scene_stages:
            if found == scene_id:
                return stage
        return None


def load_chain_specs(path: Path | None) -> list[ChainSpec]:
    if path is None:
        return []
    if not path.is_file():
        raise ConfigError("chains_missing", f"{path} does not exist")
    raw = load_yaml_file(path)
    chains = raw.get("chains") or {}
    if not isinstance(chains, dict):
        raise ConfigError("yaml_shape", "chains.yaml `chains` must be a mapping")
    specs: list[ChainSpec] = []
    for chain_id, body in chains.items():
        if not isinstance(body, dict):
            raise ConfigError("yaml_shape", f"chain {chain_id} must be a mapping")
        unknown = set(body) - _CHAIN_KEYS
        if unknown:
            raise ConfigError("unknown_key", f"chain {chain_id} has unknown keys: {sorted(unknown)}")
        order = body.get("stage_order")
        scenes = body.get("scenes")
        if not isinstance(order, list) or not order:
            raise ConfigError("missing_key", f"chain {chain_id} needs a non-empty stage_order")
        if not isinstance(scenes, dict) or not scenes:
            raise ConfigError("missing_key", f"chain {chain_id} needs a non-empty scenes mapping")
        if "base" not in body or "category" not in body:
            raise ConfigError("missing_key", f"chain {chain_id} needs `base` and `category`")
        specs.append(
            ChainSpec(
                chain_id=str(chain_id),
                category=str(body["category"]),
                base_ref=body["base"],
                route_tags=tuple(str(tag) for tag in body.get("route_tags", ())),
                stage_order=tuple(str(stage) for stage in order),
                scene_refs=tuple((ref, str(stage)) for ref, stage in scenes.items()),
                needs_face_visible=bool(body.get("needs_face_visible", False)),
            )
        )
    return specs


def resolve_chains(specs: list[ChainSpec], scenes: list[Scene]) -> list[ResolvedChain]:
    resolved: list[ResolvedChain] = []
    claimed: dict[str, str] = {}
    for spec in specs:
        if len(set(spec.stage_order)) != len(spec.stage_order):
            raise ConfigError("chain_stage_dup", f"chain {spec.chain_id} repeats a stage in stage_order")
        base = find_scene(scenes, spec.base_ref)
        pairs: list[tuple[str, str]] = []
        for ref, stage in spec.scene_refs:
            scene = find_scene(scenes, ref)
            if stage not in spec.stage_order:
                raise ConfigError(
                    "chain_stage_unknown",
                    f"chain {spec.chain_id}: scene {scene.scene_id} wants stage {stage!r}, "
                    f"which is not in stage_order {list(spec.stage_order)}",
                )
            if scene.scene_id in claimed:
                raise ConfigError(
                    "chain_scene_shared",
                    f"scene {scene.scene_id} is in chains {claimed[scene.scene_id]} and {spec.chain_id}",
                )
            claimed[scene.scene_id] = spec.chain_id
            pairs.append((scene.scene_id, stage))
        if base.scene_id not in {scene_id for scene_id, _ in pairs}:
            raise ConfigError(
                "chain_base_not_member",
                f"chain {spec.chain_id}: base scene {base.scene_id} must also be listed in scenes",
            )
        last = max(spec.stage_order.index(stage) for _, stage in pairs)
        resolved.append(
            ResolvedChain(
                chain_id=spec.chain_id,
                category=spec.category,
                base=base,
                route_tags=spec.route_tags,
                stages=spec.stage_order[: last + 1],
                scene_stages=tuple(pairs),
                needs_face_visible=spec.needs_face_visible,
            )
        )
    return resolved
