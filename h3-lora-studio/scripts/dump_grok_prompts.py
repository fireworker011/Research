#!/usr/bin/env python3
"""Write a Grok-readable pack of every GitHub prompt this H3 erotic lane uses.

Independent H3 lane only. Does not touch HQ dumps (G_hq_boot / hq-instruct / G_hq_admin).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
COLAB = ROOT / "colab"
STUDIO = ROOT / "h3-lora-studio"
INDEX_PATH = STUDIO / "GROK_PROMPTS.md"
DUMP_PATH = STUDIO / "dump" / "G_h3_prompts.txt"
BODY_LOCK_PATH = ROOT / "prompts" / "h3-body-lock.md"

if str(COLAB) not in sys.path:
    sys.path.insert(0, str(COLAB))

from h3_lora_studio import (  # noqa: E402
    ANAL_PATTERN_ORDER,
    CHAIN_PACK_ORDER,
    STORY_ORDER,
    STUDIO_FETCH_BRANCH,
    STUDIO_REV,
    generate_anal_pattern,
    generate_immoral_shorts,
    load_story,
)
import h3_lora_studio as studio  # noqa: E402
from h3_t2v import DEFAULT_T2V_PROMPT, DEFAULT_T2V_PROMPT_16_9  # noqa: E402

REPO_BLOB = f"https://github.com/fireworker011/Research/blob/{STUDIO_FETCH_BRANCH}"
REPO_RAW = f"https://raw.githubusercontent.com/fireworker011/Research/{STUDIO_FETCH_BRANCH}"

LOCK_NAME_SUFFIXES = (
    "_LINE",
    "_LOCK",
    "_LOOK",
    "_SFX",
    "_BEAT",
    "_MARK",
    "_KISS",
)
LOCK_DICTS = ("POSE_LOCK_LINE", "SITUATION_HELP")
EXTRA_LOCK_NAMES = (
    "SEMEN_HEAVY_OIL",
    "PHONE_ORAL_WOMAN",
    "PHONE_ORAL_FUTA",
    "FUTA_SCENE_ANATOMY",
    "I2V_PICTURE1_HEADER",
)
SKIP_HQ = (
    "dump/G_hq_boot.txt",
    "dump/G_hq_admin.txt",
    "dump/G_hq_human_sitting.txt",
    "affiliate-engine/docs/grok-bots/hq-instruct.js",
)
NOT_THIS_LANE = (
    "minimaxh3/coconala_h3_i2va_prompt.txt",
    "colab/h3_t2v.py DEFAULT_T2V_PROMPT (ココナラ homage / 空欄のエロなし既定)",
)


def blob(rel: str) -> str:
    return f"{REPO_BLOB}/{rel}"


def raw(rel: str) -> str:
    return f"{REPO_RAW}/{rel}"


def collect_lock_strings() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for name in sorted(dir(studio)):
        if name.startswith("_"):
            continue
        if not name.endswith(LOCK_NAME_SUFFIXES):
            continue
        val = getattr(studio, name)
        if isinstance(val, str) and val.strip():
            out.append((name, val.strip()))
    seen = {name for name, _ in out}
    for name in EXTRA_LOCK_NAMES:
        if name in seen:
            continue
        val = getattr(studio, name, None)
        if isinstance(val, str) and val.strip():
            out.append((name, val.strip()))
    out.sort(key=lambda row: row[0])
    return out


def collect_lock_dicts() -> list[tuple[str, dict[str, str]]]:
    out: list[tuple[str, dict[str, str]]] = []
    for name in LOCK_DICTS:
        val = getattr(studio, name, None)
        if isinstance(val, dict):
            out.append((name, {str(k): str(v) for k, v in val.items()}))
    return out


def story_files() -> list[Path]:
    return sorted((STUDIO / "stories").glob("*.json"))


def profile_files() -> list[Path]:
    return sorted((STUDIO / "profiles").glob("*.json"))


def render_index() -> str:
    stories = story_files()
    profiles = profile_files()
    lines = [
        "# Grok 用：このエロ動画レーンの GitHub プロンプト",
        "",
        "独立 H3 レーン。Naomiichi。質問しない。",
        f"版 `{STUDIO_REV}`。枝 `{STUDIO_FETCH_BRANCH}`。",
        "",
        "**全文はこれを開け:** [`h3-lora-studio/dump/G_h3_prompts.txt`](dump/G_h3_prompts.txt)",
        "",
        "HQ dump（`G_hq_boot` / `hq-instruct` / `G_hq_admin`）は触るな。Threads の schedule を戻すな。",
        "",
        "再生成:",
        "",
        "```bash",
        "python h3-lora-studio/scripts/dump_grok_prompts.py --write",
        "python h3-lora-studio/scripts/dump_grok_prompts.py --check",
        "```",
        "",
        "## 何が載るか",
        "",
        "Colab ③が H3 に渡す文の **GitHub 上の出所**。実行時に `prepare_story_clip` がロックを足す。",
        "ロック定数も GitHub（`colab/h3_lora_studio.py`）にあるので全文ダンプに入れる。",
        "",
        "| 出所 | 役割 | GitHub |",
        "|---|---|---|",
        f"| `prompts/h3-body-lock.md` | アナル穴ロック（人間向け。英語は py と同期） | [blob]({blob('prompts/h3-body-lock.md')}) |",
        f"| `h3-lora-studio/stories/*.json` | 物語クリップの `prompt`（{len(stories)} 話） | [stories]({blob('h3-lora-studio/stories')}) |",
        f"| `h3-lora-studio/profiles/*.json` | ③の行為シーン既定 `scenes.t2v` / `scenes.i2v`（{len(profiles)}） | [profiles]({blob('h3-lora-studio/profiles')}) |",
        f"| `colab/h3_lora_studio.py` | 注入ロック・`SITUATION_HELP`・③アナル三択・短編集 | [blob]({blob('colab/h3_lora_studio.py')}) |",
        f"| `minimaxh3/h3_lora_studio.py` | 上の写し | [blob]({blob('minimaxh3/h3_lora_studio.py')}) |",
        "",
        "## 物語 JSON（クリップ本文）",
        "",
    ]
    ordered = list(STORY_ORDER) + [s for s in CHAIN_PACK_ORDER if s not in STORY_ORDER]
    seen: set[str] = set()
    for sid in ordered:
        path = STUDIO / "stories" / f"{sid}.json"
        if not path.is_file():
            continue
        seen.add(sid)
        rel = f"h3-lora-studio/stories/{sid}.json"
        lines.append(f"- `{sid}` — [blob]({blob(rel)}) · [raw]({raw(rel)})")
    extra = [p.stem for p in stories if p.stem not in seen]
    for sid in extra:
        rel = f"h3-lora-studio/stories/{sid}.json"
        lines.append(f"- `{sid}` — [blob]({blob(rel)}) · [raw]({raw(rel)})")
    lines += [
        "",
        "## ③がコードで組む文（JSON ではない）",
        "",
        "- `anal-p1-oral` / `anal-p2-bj-anal` / `anal-p3-meet-anal` → `generate_anal_pattern()`",
        "- `shorts-immoral` → `generate_immoral_shorts()`",
        "",
        "全文はダンプの GENERATED 節。",
        "",
        "## 使わない（このエロ動画の本線ではない）",
        "",
    ]
    for item in NOT_THIS_LANE:
        lines.append(f"- `{item}`")
    lines.append("")
    lines.append("## 開けるな（本線 HQ）")
    lines.append("")
    for item in SKIP_HQ:
        lines.append(f"- `{item}`")
    lines += [
        "",
        "## シーン既定（profiles）",
        "",
    ]
    for path in profiles:
        rel = f"h3-lora-studio/profiles/{path.name}"
        lines.append(f"- `{path.stem}` — [blob]({blob(rel)})")
    lines.append("")
    return "\n".join(lines)


def _rule(title: str) -> str:
    bar = "=" * 16
    return f"\n{bar} {title} {bar}\n"


def render_dump() -> str:
    chunks: list[str] = [
        "H3 erotic lane — all GitHub prompts for Grok.",
        f"rev={STUDIO_REV} branch={STUDIO_FETCH_BRANCH}",
        "Independent H3. Do not open HQ dumps. Do not restore Threads schedules.",
        "Regenerate: python h3-lora-studio/scripts/dump_grok_prompts.py --write",
        _rule("INDEX"),
        "Open h3-lora-studio/GROK_PROMPTS.md for URLs.",
        _rule("FILE prompts/h3-body-lock.md"),
        BODY_LOCK_PATH.read_text(encoding="utf-8").rstrip() + "\n",
    ]

    chunks.append(_rule("ENGINE LOCK STRINGS colab/h3_lora_studio.py"))
    for name, val in collect_lock_strings():
        chunks.append(f"----- {name} -----\n{val}\n")

    chunks.append(_rule("ENGINE LOCK DICTS"))
    for name, mapping in collect_lock_dicts():
        chunks.append(f"----- {name} -----")
        for key in sorted(mapping):
            chunks.append(f"[{name}.{key}]\n{mapping[key]}\n")

    chunks.append(_rule("NOT THIS LANE: colab/h3_t2v.py empty-prompt SFW defaults"))
    chunks.append(f"----- DEFAULT_T2V_PROMPT -----\n{DEFAULT_T2V_PROMPT}")
    chunks.append(f"----- DEFAULT_T2V_PROMPT_16_9 -----\n{DEFAULT_T2V_PROMPT_16_9}")

    chunks.append(_rule("PROFILES h3-lora-studio/profiles/*.json scenes"))
    for path in profile_files():
        data = json.loads(path.read_text(encoding="utf-8"))
        scenes = data.get("scenes") or {}
        if not scenes:
            continue
        rel = f"h3-lora-studio/profiles/{path.name}"
        chunks.append(f"##### FILE {rel} id={data.get('id') or path.stem}")
        for mode in ("t2v", "i2v", "r2v"):
            text = scenes.get(mode)
            if text:
                chunks.append(f"----- {path.stem} scenes.{mode} -----\n{str(text).rstrip()}\n")

    chunks.append(_rule("STORIES h3-lora-studio/stories/*.json clip.prompt"))
    ordered_ids = list(STORY_ORDER) + list(CHAIN_PACK_ORDER)
    dumped: set[str] = set()
    for sid in ordered_ids:
        path = STUDIO / "stories" / f"{sid}.json"
        if not path.is_file() or sid in dumped:
            continue
        dumped.add(sid)
        chunks.append(_story_dump(path))
    for path in story_files():
        if path.stem not in dumped:
            chunks.append(_story_dump(path))

    chunks.append(_rule("GENERATED anal patterns generate_anal_pattern()"))
    for pid in ANAL_PATTERN_ORDER:
        story = generate_anal_pattern(pid, pose="standing", scene="")
        chunks.append(
            f"##### GENERATED {pid} title={story.get('title_ja') or ''} pose=standing"
        )
        chunks.extend(_clip_dumps(story.get("clips") or [], prefix=pid))

    chunks.append(_rule("GENERATED anthology generate_immoral_shorts()"))
    shorts = generate_immoral_shorts()
    chunks.append(
        f"##### GENERATED shorts-immoral clips={len(shorts.get('clips') or [])}"
    )
    chunks.extend(_clip_dumps(shorts.get("clips") or [], prefix="shorts-immoral"))

    chunks.append(_rule("LOAD_STORY RAW PROMPTS (same as JSON; sanity)"))
    for sid in list(STORY_ORDER) + list(CHAIN_PACK_ORDER):
        path = STUDIO / "stories" / f"{sid}.json"
        if not path.is_file():
            continue
        story = load_story(sid)
        n = len(story.get("clips") or [])
        chunks.append(f"[load_story {sid}] clips={n} duration_s={story.get('duration_s')}")

    text = "\n".join(chunks).rstrip() + "\n"
    if "civitai_api_token=" in text.lower() or "xai_api_key=" in text.lower():
        raise SystemExit("refusing to write API keys into the Grok dump")
    return text


def _story_dump(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    rel = f"h3-lora-studio/stories/{path.name}"
    head = (
        f"##### FILE {rel}\n"
        f"id={data.get('id')} title={data.get('title_ja') or ''} "
        f"duration_s={data.get('duration_s')} clips={len(data.get('clips') or [])}\n"
        f"blob={blob(rel)}\n"
        f"raw={raw(rel)}\n"
    )
    return head + "\n".join(_clip_dumps(data.get("clips") or [], prefix=str(data.get("id") or path.stem)))


def _clip_dumps(clips: list[dict[str, Any]], *, prefix: str) -> list[str]:
    out: list[str] = []
    for i, clip in enumerate(clips):
        cid = str(clip.get("id") or f"c{i + 1}")
        label = str(clip.get("label") or "")
        sit = str(clip.get("situation") or "")
        prompt = str(clip.get("prompt") or "").rstrip()
        out.append(
            f"----- {prefix} clip={cid} i={i} situation={sit} label={label} -----\n"
            f"{prompt}\n"
        )
    return out


def write_pack() -> tuple[Path, Path]:
    INDEX_PATH.write_text(render_index(), encoding="utf-8")
    DUMP_PATH.parent.mkdir(parents=True, exist_ok=True)
    DUMP_PATH.write_text(render_dump(), encoding="utf-8")
    return INDEX_PATH, DUMP_PATH


def check_pack() -> None:
    want_index = render_index()
    want_dump = render_dump()
    have_index = INDEX_PATH.read_text(encoding="utf-8") if INDEX_PATH.is_file() else ""
    have_dump = DUMP_PATH.read_text(encoding="utf-8") if DUMP_PATH.is_file() else ""
    errors: list[str] = []
    if have_index != want_index:
        errors.append(f"stale {INDEX_PATH.relative_to(ROOT)}")
    if have_dump != want_dump:
        errors.append(f"stale {DUMP_PATH.relative_to(ROOT)}")
    missing = [
        p.name
        for p in story_files()
        if p.stem not in want_index or p.stem not in want_dump
    ]
    if missing:
        errors.append("stories missing from pack: " + ", ".join(missing))
    if "ANAL HOLE LOCK" not in want_dump:
        errors.append("dump missing ANAL HOLE LOCK")
    if errors:
        raise SystemExit("dump_grok_prompts --check failed: " + " / ".join(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write index + dump")
    parser.add_argument("--check", action="store_true", help="fail if committed pack is stale")
    args = parser.parse_args(argv)
    if args.check and not args.write:
        check_pack()
        print("ok", INDEX_PATH.relative_to(ROOT), DUMP_PATH.relative_to(ROOT))
        return 0
    index, dump = write_pack()
    print("wrote", index.relative_to(ROOT), dump.stat().st_size, "bytes dump")
    if args.check:
        check_pack()
        print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
