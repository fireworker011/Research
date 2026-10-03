"""Plan a 15s short from commonalities plus a product, then enqueue one inbox job."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from minimaxh3.affi.commonalities import UNKNOWN, find_cell, load_commonalities
from minimaxh3.affi.inbox import enqueue_part, inbox_busy, resolve_ref
from minimaxh3.affi.products import PRODUCTS
from minimaxh3.affi.score import score_script
from minimaxh3.affi.script import PATTERNS, load_pattern

QUEUE_NAME = "affi-queue.json"


def plan_one(
    commonalities: Path,
    product_id: str,
    platform: str,
    *,
    ref_dir: Path | None = None,
    extra_roots: list[Path] | None = None,
) -> dict[str, Any]:
    product = PRODUCTS[product_id]
    doc = load_commonalities(commonalities)
    cell = find_cell(doc, product["genre"], platform)
    pattern_id = str(cell.get("pattern_id") or UNKNOWN)
    base = {
        "product": product_id,
        "genre": product["genre"],
        "platform": platform,
        "pattern_id": pattern_id,
        "growing_n": cell.get("growing_n", UNKNOWN),
        "struggling_n": cell.get("struggling_n", UNKNOWN),
        "landing_url": product["landing_url"],
    }
    if pattern_id == UNKNOWN:
        return {**base, "verdict": "直す", "reason": "共通点が不明", "script": None}
    if pattern_id not in PATTERNS:
        return {**base, "verdict": "直す", "reason": "型が不明", "script": None}
    spec = PATTERNS[pattern_id]
    if spec["genre"] != product["genre"] or spec["product"] != product_id:
        return {**base, "verdict": "直す", "reason": "ジャンルが一致しない", "script": None}
    script = load_pattern(pattern_id)
    scored = score_script(script, product)
    missing = []
    for part in script["parts"]:
        kind = str(part.get("ref") or "")
        if kind and resolve_ref(kind, ref_dir, extra_roots) is None:
            missing.append(kind)
    if missing and scored["verdict"] == "使える":
        scored = {
            **scored,
            "verdict": "直す",
            "reason": "参照画像が無い: " + ",".join(missing),
        }
    return {**base, **scored, "script": script}


def run_batch(
    commonalities: Path,
    product_id: str,
    platform: str,
    count: int,
    drive: Path,
    *,
    ref_dir: Path | None = None,
    extra_roots: list[Path] | None = None,
) -> dict[str, Any]:
    if count < 1:
        raise ValueError("count は 1 以上")
    ids = _product_ids(product_id, count)
    plans = [
        plan_one(commonalities, pid, platform, ref_dir=ref_dir, extra_roots=extra_roots)
        for pid in ids
    ]
    queue = _load_queue(drive)
    known = {item["short_id"] for item in queue}
    added = 0
    for index, item in enumerate(plans, start=1):
        if item["verdict"] != "使える" or item["script"] is None:
            continue
        short_id = f"{item['product']}-{index}"
        if short_id in known:
            continue
        for part_index, part in enumerate(item["script"]["parts"]):
            queue.append(
                {
                    "short_id": short_id,
                    "product": item["product"],
                    "pattern_id": item["pattern_id"],
                    "part_index": part_index,
                    "part": part,
                    "script": {
                        "hook": item["script"]["hook"],
                        "beats": item["script"]["beats"],
                        "title": item["script"]["title"],
                        "description": item["script"]["description"],
                    },
                }
            )
        known.add(short_id)
        added += 1
    dropped = None
    if queue and not inbox_busy(drive):
        head = queue.pop(0)
        dropped = enqueue_part(
            drive,
            short_id=head["short_id"],
            product_id=head["product"],
            pattern_id=head["pattern_id"],
            part_index=head["part_index"],
            part=head["part"],
            script=head["script"],
            ref_dir=ref_dir,
            extra_roots=extra_roots,
        )
        if not dropped.get("enqueued"):
            queue.insert(0, head)
    _save_queue(drive, queue)
    public = []
    for item in plans:
        public.append(
            {
                "product": item["product"],
                "platform": item["platform"],
                "pattern_id": item["pattern_id"],
                "verdict": item["verdict"],
                "reason": item["reason"],
                "total": item.get("total"),
                "axes": item.get("axes"),
                "growing_n": item["growing_n"],
                "struggling_n": item["struggling_n"],
                "landing_url": item["landing_url"],
            }
        )
    return {
        "plans": public,
        "queued_parts": len(queue) + (1 if dropped and dropped.get("enqueued") else 0),
        "waiting_parts": len(queue),
        "inbox": dropped,
    }


def _product_ids(product_id: str, count: int) -> list[str]:
    if product_id == "all":
        order = ("kanetora", "orbis", "furbo")
        return [order[i % len(order)] for i in range(count)]
    if product_id not in PRODUCTS:
        raise ValueError(product_id)
    return [product_id] * count


def _load_queue(drive: Path) -> list[dict[str, Any]]:
    path = drive / QUEUE_NAME
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("affi-queue.json は配列")
    return data


def _save_queue(drive: Path, queue: list[dict[str, Any]]) -> None:
    drive.mkdir(parents=True, exist_ok=True)
    (drive / QUEUE_NAME).write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
