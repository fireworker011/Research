#!/usr/bin/env python3
"""ルール帯と扉番号の重なり、仮置き、誘導カードの画面文言を検査する。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import render_frames


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_CARD = ("プロフ", "ゼロ円", "0円", "http://", "https://", "第五則")


def load_job(name: str) -> dict:
    return json.loads((ROOT / "jobs-v3" / name).read_text(encoding="utf-8"))


def card_mask(card: dict) -> np.ndarray:
    overlay = Image.new("RGBA", (render_frames.WIDTH, render_frames.HEIGHT), (0, 0, 0, 0))
    render_frames.draw_top_card(render_frames.ImageDraw.Draw(overlay), card)
    return np.asarray(overlay.getchannel("A")) > 0


def number_mask(job: dict, segment: dict, drift_step: int) -> np.ndarray:
    plain = dict(segment)
    plain["top_card"] = None
    item = {"kind": "segment", "segment_id": plain.get("id"), "segment": plain}
    ctx = {"shift": (0, 0), "progress": 0.45, "phase": 0.45}
    render_frames.SUPPRESS_DOOR_NUMBER = False
    with_number = render_frames.render_frame(job, item, plain, ctx, drift_step, show_pr=False)
    render_frames.SUPPRESS_DOOR_NUMBER = True
    without = render_frames.render_frame(job, item, plain, ctx, drift_step, show_pr=False)
    render_frames.SUPPRESS_DOOR_NUMBER = False
    delta = np.abs(np.asarray(with_number).astype(np.int16) - np.asarray(without).astype(np.int16)).sum(axis=2)
    return delta > 18


def source_boxes(job: dict, segment: dict) -> list[tuple[int, int, int, int]]:
    item = {"kind": "segment", "segment_id": segment.get("id"), "segment": segment}
    render_frames.DOOR_NUMBER_BOXES.clear()
    render_frames.paint_scene(job, item, segment, {"shift": (0, 0), "progress": 0.45, "phase": 0.45})
    return list(render_frames.DOOR_NUMBER_BOXES)


def closest_step(boxes: list[tuple[int, int, int, int]], ink: tuple[int, int, int, int]) -> tuple[int, int]:
    worst_step = 1
    worst_gap = 10**9
    worst_area = 0
    for step in range(0, 480):
        for box in boxes:
            mapped = render_frames.map_source_box(box, step)
            if mapped is None:
                continue
            area = render_frames.box_overlap_px(mapped, ink)
            if area > worst_area:
                worst_area = area
                worst_step = step
            # 縦方向のすき間。負なら重なっている。
            gap = mapped[1] - ink[3]
            if mapped[3] < ink[1]:
                gap = ink[1] - mapped[3]
            if area == 0 and gap < worst_gap:
                worst_gap = gap
                if worst_area == 0:
                    worst_step = step
    return worst_step, worst_area


def main() -> int:
    failed = False
    jobs = {
        "day2": load_job("episode_day2.json"),
        "day3": load_job("episode_day3.json"),
    }
    for name, job in jobs.items():
        cards = [seg["top_card"] for seg in job["segments"] if seg.get("top_card")]
        inks = []
        for card in cards:
            overlay = Image.new("RGBA", (render_frames.WIDTH, render_frames.HEIGHT), (0, 0, 0, 0))
            render_frames.draw_top_card(render_frames.ImageDraw.Draw(overlay), card)
            bbox = overlay.getchannel("A").getbbox()
            if bbox is not None:
                inks.append((card, bbox))
        max_bbox = 0
        max_px = 0
        min_gap = 10**9
        for segment in job["segments"]:
            boxes = source_boxes(job, segment)
            if segment.get("scene") == "room_stickman" and boxes:
                print(f"FAIL {name} seg {segment.get('id')} room still draws 705")
                failed = True
            if not boxes or not inks:
                continue
            for _card, ink in inks:
                for step in range(0, 480):
                    for box in boxes:
                        mapped = render_frames.map_source_box(box, step)
                        if mapped is None:
                            continue
                        area = render_frames.box_overlap_px(mapped, ink)
                        max_bbox = max(max_bbox, area)
                        dx = 0
                        if mapped[2] < ink[0]:
                            dx = ink[0] - mapped[2]
                        elif ink[2] < mapped[0]:
                            dx = mapped[0] - ink[2]
                        dy = 0
                        if mapped[3] < ink[1]:
                            dy = ink[1] - mapped[3]
                        elif ink[3] < mapped[1]:
                            dy = mapped[1] - ink[3]
                        if dx and dy:
                            gap = int((dx * dx + dy * dy) ** 0.5)
                        else:
                            gap = dx + dy
                        min_gap = min(min_gap, gap)
            step, area = closest_step(boxes, inks[0][1])
            px = int((number_mask(job, segment, step) & card_mask(inks[0][0])).sum())
            max_px = max(max_px, px)
            if area or px:
                print(f"FAIL {name} seg {segment.get('id')} drift {step} bbox={area} px={px}")
                failed = True
        if max_bbox or (min_gap < 8 and min_gap < 10**8):
            print(f"FAIL {name} bbox={max_bbox} min_gap={min_gap}")
            failed = True
        print(f"{name} rule_overlap bbox={max_bbox}px pixel={max_px}px min_gap={min_gap}px")

    try:
        render_frames.paint_scene(
            jobs["day2"],
            {"kind": "segment"},
            {"id": 0, "scene": "missing_asset", "scene_params": {}},
            {"shift": (0, 0), "progress": 0, "phase": 0},
        )
    except SystemExit as exc:
        text = str(exc)
        if "仮置きは出しません" not in text:
            print(f"FAIL missing asset message: {text}")
            failed = True
        else:
            print("missing_asset FAIL-stop PASS")
    else:
        print("FAIL missing asset did not stop")
        failed = True

    try:
        render_frames.paint_breaker({"use_placeholder": True}, {"shift": (0, 0), "phase": 0}, {"id": 0})
    except SystemExit as exc:
        if "仮置きは出しません" not in str(exc):
            print(f"FAIL placeholder message: {exc}")
            failed = True
        else:
            print("placeholder FAIL-stop PASS")
    else:
        print("FAIL placeholder did not stop")
        failed = True

    heard = None
    for segment in jobs["day2"]["segments"]:
        if segment.get("scene") == "breaker_panel" and (segment.get("scene_params") or {}).get("heard_only"):
            heard = segment
            break
    if heard is None:
        print("FAIL heard_only segment missing")
        failed = True
    else:
        image = render_frames.render_frame(
            jobs["day2"],
            {"kind": "segment", "segment": heard},
            heard,
            {"shift": (0, 0), "progress": 0.4, "phase": 0.4},
            3,
            show_pr=False,
        )
        arr = np.asarray(image)
        green = (
            (np.abs(arr[:, :, 0].astype(np.int16) - 70) <= 8)
            & (np.abs(arr[:, :, 1].astype(np.int16) - 210) <= 8)
            & (np.abs(arr[:, :, 2].astype(np.int16) - 120) <= 8)
        )
        print(f"green_rect_pixels={int(green.sum())}")
        if int(green.sum()) > 200:
            print("FAIL green rounded rect pixels remain")
            failed = True

    blob = json.dumps(jobs["day3"], ensure_ascii=False)
    for word in FORBIDDEN_CARD:
        if word in blob:
            # ナレーションの Audible は残す。禁止は画面に出す条件・URL・旧呼称。
            print(f"FAIL day3 text contains {word}")
            failed = True
    narration = jobs["day3"]["promo_outro"].get("narration") or ""
    if narration != "夜中の確認癖を断つなら Audible。":
        print(f"FAIL promo narration changed: {narration}")
        failed = True
    if jobs["day3"]["segments"][10]["subtitle"] != "ルール5。配電箱へ触れるな。":
        print("FAIL rule subtitle")
        failed = True
    else:
        print("rule_name PASS")

    if failed:
        print("FAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
