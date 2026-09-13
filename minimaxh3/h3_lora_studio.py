"""Colab helper for stacking MiniMax H3 LoRAs.

SFW: turbo + one quality LoRA. Adult T2V/I2V: concept (Mystic XXX) + act + helpers 0-2 + optional thin turbo.
Futa blowjob may use two helpers plus thin Larry 6step. Futa sex/anal/riding/doggy stay turbo off.
Cinema replaces helper. Anal sex / urine drink / scat act (penis + synth, no ThumbInButt) stay turbo off. Pose LoRAs replace AIO; do not stack both.
Larry and LightX2V never stack. Adults 21+ only. Never print API keys.
Fal H3 Max cannot take LoRAs — this is local Comfy FL2VA only.
Studio T2V/I2V unet is H3 Eros Max TURBO-hybrid beta5 int8 (baked turbo). Official FL2VA stays on phone I2V/T2V. Ref2VA stays official. Mystic XXX v4 is FL2VA-only; do not load the Ref2VA file.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

STUDIO_ROOT = Path(__file__).resolve().parents[1] / "h3-lora-studio"
if not STUDIO_ROOT.is_dir():
    STUDIO_ROOT = Path("/content/h3-lora-studio")
_SCRIPTS = STUDIO_ROOT / "scripts"
if _SCRIPTS.is_dir() and str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
_COLAB_R2V = Path(__file__).resolve().parents[1] / "colab"
if _COLAB_R2V.is_dir() and str(_COLAB_R2V) not in sys.path:
    sys.path.insert(0, str(_COLAB_R2V))
# Colab ② writes this file first, then h3_r2v_core.py. Import must not fail.
try:
    from h3_r2v_core import (
        FL2VA_MAX_CLIP_S,
        cap_duration_for_vram,
        cap_fl2va_clip_s,
        finalize_prompt as r2v_finalize_prompt,
        rewrite_take_seconds,
    )
except ImportError:
    r2v_finalize_prompt = None
    FL2VA_MAX_CLIP_S = 10.0

    def cap_duration_for_vram(
        duration_s: float,
        *,
        vram_gb: float,
        n_images: int,
        has_video: bool,
        ref_image_size: str,
    ) -> float:
        d = float(duration_s)
        if not has_video:
            return min(d, FL2VA_MAX_CLIP_S)
        return min(d, 15.0)

    def cap_fl2va_clip_s(duration_s: float) -> float:
        try:
            d = float(duration_s)
        except (TypeError, ValueError):
            d = FL2VA_MAX_CLIP_S
        if d < 1:
            d = 1.0
        return min(d, FL2VA_MAX_CLIP_S)

    def rewrite_take_seconds(prompt: str, duration_s: float) -> str:
        n = int(round(float(duration_s)))
        return re.sub(
            r"\b(\d+(?:\.\d+)?)-second(?: take)?\b",
            lambda m: f"{n}-second take" if m.group(0).endswith("take") else f"{n}-second",
            str(prompt or ""),
        )

try:
    from h3_i2v_phone import i2v_download_jobs
except ImportError:
    def i2v_download_jobs(drive_models: Path | str) -> list[tuple[str, Path]]:
        del drive_models
        return []

OPTIONAL_IDS = {
    "astro-nsfw-h3": 0.35,
    "tiddies-realism-slider": 1.2,
    "h3-realism-people": 1.0,
    "photoreal-h3-still": 1.0,
}

SITUATION_DOWNLOAD = {
    "redo": [],
    "vanilla": [],
    "sfw_daily": ["mystic-xxx-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"],
    "sfw_preview": ["mystic-xxx-h3", "penis-lora-h3", "synth-pussy-h3", "minimax-h3-turbo-fl2v-4step"],
    "sfw_audio": ["mystic-xxx-h3", "penis-lora-h3", "synth-pussy-h3", "minimax-h3-turbo-fl2v-8step"],
    "sfw_r2v": ["minimax-h3-turbo-ref2v-4step", "cinema-dy"],
    "anal_closeup": ["mystic-xxx-h3", "synth-pussy-h3", "larry-v4"],
    "anal_fingering": ["mystic-xxx-h3", "thumbinbutt-h3", "synth-pussy-h3", "larry-v4"],
    "anal_penetration": ["mystic-xxx-h3", "penis-lora-h3", "synth-pussy-h3"],
    "lesbian_cunnilingus": ["mystic-xxx-h3", "lesbian-cunnilingus-h3", "synth-pussy-h3", "larry-v4"],
    "pussy_spread": ["mystic-xxx-h3", "pussy-spread-h3", "synth-pussy-h3", "larry-v4"],
    "lesbian_spread": ["mystic-xxx-h3", "lesbian-cunnilingus-h3", "pussy-spread-h3", "larry-v4"],
    "futa_blowjob": ["mystic-xxx-h3", "blowjob-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"],
    "futa_sex": ["mystic-xxx-h3", "hmnsfw-aio-v25", "penis-lora-h3", "synth-pussy-h3"],
    "futa_anal": ["mystic-xxx-h3", "penis-lora-h3", "synth-pussy-h3"],
    "urine_drink": ["mystic-xxx-h3", "penis-lora-h3", "synth-pussy-h3"],
    "urine_pee": ["mystic-xxx-h3", "penis-lora-h3", "synth-pussy-h3"],
    "scat_act": ["mystic-xxx-h3", "penis-lora-h3", "synth-pussy-h3"],
    "oral": ["mystic-xxx-h3", "blowjob-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"],
    "general_sex": ["mystic-xxx-h3", "hmnsfw-aio-v25", "penis-lora-h3", "synth-pussy-h3"],
    "preview": ["mystic-xxx-h3", "hmnsfw-aio-v25", "synth-pussy-h3", "minimax-h3-turbo-fl2v-4step"],
    "riding": ["mystic-xxx-h3", "cowgirl-position-h3", "riding-pose-i2v", "penis-lora-h3", "synth-pussy-h3"],
    "doggy": ["mystic-xxx-h3", "doggy-h3", "penis-lora-h3", "synth-pussy-h3"],
    "missionary_pov": ["mystic-xxx-h3", "missionary-pov-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"],
    "after_ejaculation": ["mystic-xxx-h3", "hmcumshot-v2", "penis-lora-h3", "synth-pussy-h3", "larry-v4"],
    "facial": ["mystic-xxx-h3", "facial-cumshot-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"],
    "creampie": ["mystic-xxx-h3", "final-thrust-h3", "penis-lora-h3", "synth-pussy-h3"],
    "oral_creampie": ["mystic-xxx-h3", "cumouf-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"],
    "fingering": ["mystic-xxx-h3", "fingering-h3", "synth-pussy-h3", "larry-v4"],
    "masturbation": ["mystic-xxx-h3", "hmmasturbation-h3", "synth-pussy-h3", "larry-v4"],
    "footjob": ["mystic-xxx-h3", "footjob-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"],
    "remote_orgasm": ["mystic-xxx-h3", "remote-orgasm-h3", "synth-pussy-h3", "larry-v4"],
    "futa_visible": ["mystic-xxx-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4", "cinema-dy"],
    "futa_masturbation": ["mystic-xxx-h3", "hmmasturbation-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"],
    "cunnilingus_futa": ["mystic-xxx-h3", "lesbian-cunnilingus-h3", "synth-pussy-h3", "penis-lora-h3", "larry-v4"],
    "homecoming-90s": [
        "mystic-xxx-h3",
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "lesbian-cunnilingus-h3",
        "synth-pussy-h3",
        "hmmasturbation-h3",
        "cumouf-h3",
    ],
    "dishes-90s": [
        "mystic-xxx-h3",
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "commute-120s": [
        "mystic-xxx-h3",
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "synth-pussy-h3",
    ],
    "lecture-120s": [
        "mystic-xxx-h3",
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "hmmasturbation-h3",
        "lesbian-cunnilingus-h3",
        "synth-pussy-h3",
        "cumouf-h3",
    ],
    "rooftop-100s": [
        "mystic-xxx-h3",
        "penis-lora-h3",
        "cinema-dy",
        "larry-v4",
        "hmnsfw-aio-v25",
        "synth-pussy-h3",
    ],
    "okaeri-120s": [
        "mystic-xxx-h3",
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "bath-120s": [
        "mystic-xxx-h3",
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "dinner-120s": [
        "mystic-xxx-h3",
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "futon-120s": [
        "mystic-xxx-h3",
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "sunday-120s": [
        "mystic-xxx-h3",
        "penis-lora-h3",
        "cinema-dy",
        "hmnsfw-aio-v25",
        "synth-pussy-h3",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
    ],
    "engawa-120s": [
        "mystic-xxx-h3",
        "penis-lora-h3",
        "cinema-dy",
        "hmnsfw-aio-v25",
        "synth-pussy-h3",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
    ],
    "sales-visit-60s": [
        "mystic-xxx-h3",
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "checkup-100s": [
        "mystic-xxx-h3",
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "clinic-75s": [
        "mystic-xxx-h3",
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "last-stop-40s": [
        "mystic-xxx-h3",
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "last-train-120s": [
        "mystic-xxx-h3",
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "semen-bath-70s": [
        "mystic-xxx-h3",
        "penis-lora-h3",
        "cinema-dy",
        "larry-v4",
        "synth-pussy-h3",
        "hmcumshot-v2",
    ],
    "meat-wall-85s": [
        "mystic-xxx-h3",
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "meat-wall-cesspit-70s": [
        "mystic-xxx-h3",
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    # 建前パック (10s × N, 9:16). Talk = futa_visible, jupo = oral, in-mouth = oral_creampie,
    # cunnilingus = cunnilingus_futa, already-in sex = futa_sex / doggy. 飲尿は使わない（ジュボ）。
    "cafe-100s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "blowjob-h3", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "train-sales-80s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "blowjob-h3", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "red-light-50s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "blowjob-h3", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "yoga-50s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "doggy-h3", "synth-pussy-h3", "larry-v4"],
    "back-wash-60s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "lesbian-cunnilingus-h3", "synth-pussy-h3", "blowjob-h3", "larry-v4"],
    "karaoke-50s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "blowjob-h3", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "laundromat-50s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "hmnsfw-aio-v25", "synth-pussy-h3", "larry-v4"],
    "lecture-desk-50s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "blowjob-h3", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "camp-50s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "lesbian-cunnilingus-h3", "synth-pussy-h3", "larry-v4"],
    "fireworks-50s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "hmnsfw-aio-v25", "synth-pussy-h3", "larry-v4"],
    # 物語の追加 (10s × 2, 9:16). Talk = futa_visible, in-mouth = oral_creampie,
    # already-in sex = futa_sex, cunnilingus = cunnilingus_futa.
    "manhole-30s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "roof-ac-30s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "hmnsfw-aio-v25", "synth-pussy-h3", "larry-v4"],
    "tetrapod-30s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "locker-30s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "crossing-30s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "lookout-30s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "lesbian-cunnilingus-h3", "synth-pussy-h3", "larry-v4"],
    "factory-30s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "hmnsfw-aio-v25", "synth-pussy-h3", "larry-v4"],
    "gas-station-30s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "tunnel-phone-30s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "riverbank-30s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "hachiko-30s": ["mystic-xxx-h3", "penis-lora-h3", "cinema-dy", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "shorts-immoral": [
        "blowjob-h3",
        "synth-pussy-h3",
        "minimax-h3-turbo-ref2v-4step",
        "aftermidnight-ref2va",
    ],
}

SITUATION_JA = {
    "普通（エロなし）": "vanilla",
    "日常（エロ汎用）": "sfw_daily",
    "日常（速い＋綺麗）": "sfw_daily",
    "最速プレビュー（エロ汎用）": "sfw_preview",
    "最速プレビュー（エロなし）": "sfw_preview",
    "最速プレビュー": "sfw_preview",
    "音も残す（エロ汎用）": "sfw_audio",
    "音も残す（エロなし）": "sfw_audio",
    "音も残す": "sfw_audio",
    "アナル挿入（画質）": "anal_penetration",
    "アナル挿入": "anal_penetration",
    "アナル舐め・指": "anal_closeup",
    "穴アップ（舐め・指）": "anal_closeup",
    "アナル指入れ": "anal_fingering",
    "アナル指いれ": "anal_fingering",
    "レズビアンクンニ": "lesbian_cunnilingus",
    "性器を広げる": "pussy_spread",
    "レズ＋広げる": "lesbian_spread",
    "フェラ": "oral",
    "フェラ（女体）": "oral",
    "ふたなりフェラ": "futa_blowjob",
    "ふたなりフェラ（どの構図）": "futa_blowjob",
    "セックス（女体）": "futa_sex",
    "ふたなりセックス": "futa_sex",
    "アナルセックス（女体）": "futa_anal",
    "ふたなりアナル": "futa_anal",
    "アナルセックス": "futa_anal",
    "アナルどの構図": "futa_anal",
    "飲尿": "urine_drink",
    "飲尿（どの構図）": "urine_drink",
    "放尿": "urine_pee",
    "放尿（性器から）": "urine_pee",
    "小便": "urine_pee",
    "脱糞": "scat_act",
    "脱糞（どの構図）": "scat_act",
    "騎乗位（女体）": "riding",
    "騎乗位": "riding",
    "後背位（女体）": "doggy",
    "後背位": "doggy",
    "正常位POV（女体）": "missionary_pov",
    "正常位POV": "missionary_pov",
    "後射精（女体）": "after_ejaculation",
    "後射精": "after_ejaculation",
    "顔射（女体）": "facial",
    "顔射": "facial",
    "中出し（女体）": "creampie",
    "中出し": "creampie",
    "膣中出し": "creampie",
    "口内射精（女体）": "oral_creampie",
    "口内射精": "oral_creampie",
    "口内": "oral_creampie",
    "指入れ": "fingering",
    "オナニー": "masturbation",
    "足コキ": "footjob",
    "絶頂": "remote_orgasm",
    "汎用エロ": "general_sex",
    "汎用エロ（女体）": "general_sex",
    "試し打ち": "preview",
    "帰宅120秒（専用）": "homecoming-90s",
    "帰宅90秒（専用）": "homecoming-90s",
    "洗い物120秒（専用）": "dishes-90s",
    "洗い物90秒（専用）": "dishes-90s",
    "登校120秒（専用）": "commute-120s",
    "朝〜正門120秒（専用）": "commute-120s",
    "授業120秒（専用）": "lecture-120s",
    "授業〜昼120秒（専用）": "lecture-120s",
    "屋上〜下校（専用）": "rooftop-100s",
    "屋上100秒（専用）": "rooftop-100s",
    "おかえり120秒（専用）": "okaeri-120s",
    "玄関おかえり（専用）": "okaeri-120s",
    "玄関120秒（専用）": "okaeri-120s",
    "風呂120秒（専用）": "bath-120s",
    "夜風呂（専用）": "bath-120s",
    "風呂夜（専用）": "bath-120s",
    "食卓120秒（専用）": "dinner-120s",
    "ご飯120秒（専用）": "dinner-120s",
    "食卓ご飯（専用）": "dinner-120s",
    "布団120秒（専用）": "futon-120s",
    "和室120秒（専用）": "futon-120s",
    "夜布団（専用）": "futon-120s",
    "休日120秒（専用）": "sunday-120s",
    "日曜120秒（専用）": "sunday-120s",
    "休日午前（専用）": "sunday-120s",
    "縁側120秒（専用）": "engawa-120s",
    "休日午後（専用）": "engawa-120s",
    "縁側二回戦（専用）": "engawa-120s",
    "訪問販売60秒（つなぐ）": "sales-visit-60s",
    "訪問販売（つなぐ）": "sales-visit-60s",
    "定期検診100秒（つなぐ）": "checkup-100s",
    "定期検診（つなぐ）": "checkup-100s",
    "検診100秒（つなぐ）": "checkup-100s",
    "ケンシン": "clinic-75s",
    "医院ケンシン": "clinic-75s",
    "終点40秒（つなぐ）": "last-stop-40s",
    "終点（つなぐ）": "last-stop-40s",
    "終電": "last-train-120s",
    "終電120秒": "last-train-120s",
    "ザーメン風呂": "semen-bath-70s",
    "ザーメンフロ": "semen-bath-70s",
    "ニクカベ": "meat-wall-85s",
    "肉壁": "meat-wall-85s",
    "肉壁のザーメン風呂": "meat-wall-85s",
    "ニクカベ風呂": "meat-wall-85s",
    "ニクカベ肥溜め": "meat-wall-cesspit-70s",
    "肉壁肥溜め": "meat-wall-cesspit-70s",
    "ニクヘキ肥溜め": "meat-wall-cesspit-70s",
    "sales-visit-60s": "sales-visit-60s",
    "checkup-100s": "checkup-100s",
    "clinic-75s": "clinic-75s",
    "last-stop-40s": "last-stop-40s",
    "last-train-120s": "last-train-120s",
    "semen-bath-70s": "semen-bath-70s",
    "meat-wall-85s": "meat-wall-85s",
    "meat-wall-cesspit-70s": "meat-wall-cesspit-70s",
    "cafe-100s": "cafe-100s",
    "train-sales-80s": "train-sales-80s",
    "red-light-50s": "red-light-50s",
    "yoga-50s": "yoga-50s",
    "back-wash-60s": "back-wash-60s",
    "karaoke-50s": "karaoke-50s",
    "laundromat-50s": "laundromat-50s",
    "lecture-desk-50s": "lecture-desk-50s",
    "camp-50s": "camp-50s",
    "fireworks-50s": "fireworks-50s",
    "ハイスイコウ": "manhole-30s",
    "屋上クーラー": "roof-ac-30s",
    "ハマのテトラ": "tetrapod-30s",
    "廃校ロッカー": "locker-30s",
    "ドウロのど真ん中": "crossing-30s",
    "ガケの展望台": "lookout-30s",
    "コウジョウあと": "factory-30s",
    "ガソリンスタンド跡": "gas-station-30s",
    "トンネル非常電話": "tunnel-phone-30s",
    "川原のゴミ": "riverbank-30s",
    "ハチコウ": "hachiko-30s",
    "渋谷ハチコウ": "hachiko-30s",
    "ハチコウ前": "hachiko-30s",
    "manhole-30s": "manhole-30s",
    "roof-ac-30s": "roof-ac-30s",
    "tetrapod-30s": "tetrapod-30s",
    "locker-30s": "locker-30s",
    "crossing-30s": "crossing-30s",
    "lookout-30s": "lookout-30s",
    "factory-30s": "factory-30s",
    "gas-station-30s": "gas-station-30s",
    "tunnel-phone-30s": "tunnel-phone-30s",
    "riverbank-30s": "riverbank-30s",
    "hachiko-30s": "hachiko-30s",
    "homecoming-90s": "homecoming-90s",
    "dishes-90s": "dishes-90s",
    "commute-120s": "commute-120s",
    "lecture-120s": "lecture-120s",
    "rooftop-100s": "rooftop-100s",
    "okaeri-120s": "okaeri-120s",
    "bath-120s": "bath-120s",
    "dinner-120s": "dinner-120s",
    "futon-120s": "futon-120s",
    "sunday-120s": "sunday-120s",
    "engawa-120s": "engawa-120s",
    "短編集（参照）": "shorts-immoral",
    "shorts-immoral": "shorts-immoral",
    "生成し直し": "redo",
    "redo": "redo",
    "futa_visible": "futa_visible",
    "futa_masturbation": "futa_masturbation",
    "cunnilingus_futa": "cunnilingus_futa",
    "vanilla": "vanilla",
    "sfw_daily": "sfw_daily",
    "sfw_preview": "sfw_preview",
    "sfw_audio": "sfw_audio",
    "sfw_r2v": "sfw_r2v",
    "anal_closeup": "anal_closeup",
    "anal_fingering": "anal_fingering",
    "anal_penetration": "anal_penetration",
    "lesbian_cunnilingus": "lesbian_cunnilingus",
    "pussy_spread": "pussy_spread",
    "lesbian_spread": "lesbian_spread",
    "futa_blowjob": "futa_blowjob",
    "futa_sex": "futa_sex",
    "futa_anal": "futa_anal",
    "urine_drink": "urine_drink",
    "urine_pee": "urine_pee",
    "scat_act": "scat_act",
    "oral": "oral",
    "general_sex": "general_sex",
    "preview": "preview",
    "riding": "riding",
    "doggy": "doggy",
    "missionary_pov": "missionary_pov",
    "after_ejaculation": "after_ejaculation",
    "facial": "facial",
    "creampie": "creampie",
    "oral_creampie": "oral_creampie",
    "fingering": "fingering",
    "masturbation": "masturbation",
    "footjob": "footjob",
    "remote_orgasm": "remote_orgasm",
}

MODE_JA = {
    "テキストから（写真なし）": "t2v",
    "写真から（1枚必要）": "i2v",
    "t2v": "t2v",
    "i2v": "i2v",
}

SITUATION_HELP = {
    "vanilla": "専用 I2V / T2V ノートと同じ。LightX2V 4step だけ。画質 LoRA なし。Mystic なし。",
    "sfw_daily": "日常エロ汎用。解剖 Mystic 0.5 + 竿 0.45 + 穴の見え方 0.4 + Larry 1.0 / 8step。玉なし＋マンコあり。シネマなし。フェラ／騎乗などの行為 LoRA は載せない。",
    "sfw_preview": "日常エロ汎用の最速プレビュー。解剖 Mystic 0.5 + 竿 0.45 + 穴 0.4 + LightX2V 4step。玉なし＋マンコあり。行為 LoRA なし。当たりは日常で焼き直す。",
    "sfw_audio": "日常エロ汎用で音を残して速く。解剖 Mystic 0.5 + 竿 0.45 + 穴 0.4 + LightX2V 8step。玉なし＋マンコあり。行為 LoRA なし。歌・日本語は日常（Larry）の方が安定。",
    "sfw_r2v": "顔固定 R2V。LightX2V Ref2VA 4step + シネマ 0.5。Mystic なし。FL2VA 用 Turbo は積まない。このノートでは選ばない。",
    "anal_closeup": "アナル舐め・指（女体）。解剖 0.5 + 穴の見え方 0.5 + Larry 0.5。シネマなし。女同士。男なし。動きの本線はアナル指入れ。",
    "anal_fingering": "アナル指入れ。女1人。解剖 0.5 + ThumbInButt 0.55 + 穴の見え方 0.4 + Larry 0.5 / 8step。男なし。自分の右親指。後ろから、穴が膣より上に見える構図。指入れ（膣）・アナルセックスとは別。写真からが本線。",
    "anal_penetration": "アナル挿入（画質）。穴のアップ。解剖 0.5 + 竿 0.45 + 穴の見え方 0.4。ThumbInButt なし（四つん這い固定を外した）。Turbo なし・8step。挿入側はふたなり。男なし。体位欄で構図。",
    "lesbian_cunnilingus": "レズクンニ。女同士。解剖 0.5 + クンニ 0.55 + 穴の見え方 0.4 + Larry 0.5。男なし。",
    "pussy_spread": "性器を広げる。女1人。解剖 0.5 + 広げる 0.5 + 穴の見え方 0.4 + Larry 0.5。男なし。",
    "lesbian_spread": "レズ＋広げる。女同士。解剖 0.5 + クンニ 0.55 + 広げる 0.45 + Larry 0.5。男なし。",
    "futa_blowjob": "ふたなりフェラ（汎用）。解剖 0.5 + フェラ 0.55 + 竿 0.45 + 穴の見え方 0.4 + Larry 0.5 / 6step。空欄は第三者の2ショットで根元まで。場所・座りは文章欄。体位欄は無視。POVにしない。男なし。変身 LoRA は足さない。",
    "futa_sex": "セックス（女体）。解剖 0.5 + 総合えっち 0.55 + 竿 0.45 + 穴の見え方 0.4 / 8step。Turbo なし。ふたなり＋女。男なし。体位欄が騎乗／後背／POVならその LoRA に切替。空欄は全裸のごく普通の若い成人女性。",
    "futa_anal": "アナルセックス（女体）。解剖 0.5 + 竿 0.45 + 穴の見え方 0.4。ThumbInButt なし（四つん這い固定を外した）。Turbo なし・8step。ふたなり＋女。男なし。体位欄で立ち・騎乗・後背・横。手は腰。",
    "urine_drink": "飲尿（どの構図）。解剖 0.5 + 竿 0.45 + 穴の見え方 0.4。行為 LoRA なし。Turbo なし・8step。亀頭先の尿道口から黄色い水を飲む。男なし。体位欄で構図。既存話のジュボには戻さない。",
    "urine_pee": "放尿（性器から）。解剖 0.5 + 竿 0.45 + 穴の見え方 0.4。行為 LoRA なし。Turbo なし・8step。黄色い水が亀頭先の尿道口から画面内で出る。マンコや肛門から出さない。男なし。体位欄で構図。",
    "scat_act": "脱糞（どの構図）。解剖 0.5 + 竿 0.45 + 穴の見え方 0.4。行為 LoRA なし。Turbo なし・8step。今、肛門から出している動き。肥溜めの塗れとは別。男なし。体位欄で構図。医院・終電には足さない。",
    "oral": "フェラ（女体）。解剖 0.5 + フェラ 0.6 + 竿 0.45 + 穴の見え方 0.4 + Larry 0.5 / 8step。受けはふたなり（竿＋根元のマンコ、玉なし）。男なし。変身 LoRA は足さない。",
    "general_sex": "汎用エロ（女体）。解剖 0.5 + AIO 0.55 + 竿 0.45 + 穴の見え方 0.4 / 8step。Turbo なし。ふたなり＋女。男なし。",
    "preview": "試し打ち（女体）。解剖 0.5 + AIO 0.5 + 穴の見え方 0.4 + LightX2V 4step。ふたなり＋女。男なし。",
    "riding": "騎乗位（女体）。解剖 0.5。写真から（I2V）は騎乗POV 0.45。テキストから（T2V）は cowgirl 0.55。竿 0.45 + 穴の見え方 0.4 / 8step。Turbo なし。AIO は積まない。男なし。",
    "doggy": "後背位（女体）。解剖 0.5 + 後背位 LoRA 0.55 + 竿 0.45 + 穴の見え方 0.4 / 8step。Turbo なし。男なし。",
    "missionary_pov": "正常位POV（女体）。解剖 0.5 + POV挿入 0.55 + 竿 0.45 + 穴の見え方 0.4 + Larry 0.5 / 8step。男なし。横はセックス（女体）。",
    "after_ejaculation": "後射精（女体）。解剖 0.5 + 射精 LoRA 0.55 + 竿 0.45 + 穴の見え方 0.4 + Larry 0.5 / 8step。ふたなり。男なし。絶頂・顔射・中出しとは別。",
    "facial": "顔射（女体）。解剖 0.5 + 顔射 LoRA 0.55 + 竿 0.45 + 穴の見え方 0.4 + Larry 0.5 / 8step。ふたなり＋女。男なし。後射精・絶頂・口内とは別。写真からが本線。",
    "creampie": "中出し（女体）。解剖 0.5 + Final Thrust 0.55 + 竿 0.45 + 穴の見え方 0.4 / 8step。Turbo なし。膣の中に出す。ふたなり＋女。男なし。後射精・顔射・口内とは別。写真からが本線。",
    "oral_creampie": "口内射精（女体）。解剖 0.5 + CUMOUF 0.4 + 竿 0.45 + 穴の見え方 0.4 + Larry 0.5 / 8step。口の中で出す。ふたなり（竿＋根元のマンコ）＋女。男なし。顔射・フェラ本線とは別。写真からが本線（口が付いた途中の写真）。",
    "fingering": "指入れ。女1人。解剖 0.5 + 指 LoRA 0.55 + 穴の見え方 0.4 + Larry 0.5 / 8step。男なし。膣。アナルはアナル指入れ。",
    "masturbation": "オナニー。女1人。解剖 0.5 + 潮吹き 0.55 + 穴の見え方 0.4 + Larry 0.5 / 8step。男なし。",
    "footjob": "足コキ（女体）。解剖 0.5 + Type D 0.55 + 竿 0.45 + 穴の見え方 0.4 + Larry 0.5 / 8step。ふたなり＋女。男なし。",
    "remote_orgasm": "絶頂。女1人。解剖 0.5 + 反応 LoRA 0.55 + 穴の見え方 0.4 + Larry 0.5 / 8step。男なし。射精ではない。",
    "futa_visible": "歩行・会話。竿は出す。行為 LoRA なし。歩く・キス・テレビの本は解剖 0.5 + 竿 0.45 + 穴の見え方 0.4 + Larry 0.6 / 8step。セリフ（「」）の本だけ Turbo を外して res_multistep 12step。男なし。",
    "futa_masturbation": "ふたなりオナニー。解剖 0.5 + 潮吹き LoRA + 竿 + 穴の見え方 + Larry 8step。根元のマンコが見える寄り。男なし。",
    "cunnilingus_futa": "クンニ。竿は使わず垂らす。解剖 0.5 + クンニ + 穴 + 竿薄め + Larry。フェラ LoRA は積まない。男なし。",
    "homecoming-90s": "帰宅120秒。10秒×12本。1本1場所1動作。セリフは口元が見える本だけ（リップシンク）。行為は口元・舌・竿の寄り。歩く本に行為部品なし。写真は input/homecoming-90s の 01〜12。",
    "dishes-90s": "洗い物120秒。10秒×12本。サヤカはシンク固定。レイは椅子で竿。アヤは床で口。セリフは口元の本だけ。フェラは口元の寄り。口内は CUMOUF。写真は input/dishes-90s の 01〜12。",
    "commute-120s": "登校第1話。朝〜大学正門。10秒×12本＝120秒。16:9。1本1場所。セリフは口元3本（いってらっしゃい／おくれるよ／ほしい。話し言葉、漢字なし）。フェラは玄関と路地の寄り。授業は授業120秒。今の準備はテキストから（写真なし）。Drive の input/commute-120s は任意。③をテキストからにすると試験jpgは使わない。",
    "lecture-120s": "授業第2話。授業〜昼。10秒×10本＝100秒。16:9。家とサヤカなし。机のシコはオナニー寄り。クンニは寄り1本。根元はフェラ。口内は CUMOUF。セリフは口元の「まだひるだよ」だけ。セックスは屋上〜下校。写真は input/lecture-120s の 01〜10（16:9。無い本はテキストから）。",
    "rooftop-100s": "屋上第3話。屋上挿入〜家の門。10秒×10本＝100秒。16:9。1本1場所。セリフは口元の2本だけ。セックスは AIO 横クローズ。歩く本にセックス部品なし。玄関はおかえり120秒。サヤカなし。写真は input/rooftop-100s の 01〜10（16:9）。",
    "okaeri-120s": "おかえり第4話。家の門〜玄関ジュボ〜廊下。10秒×12本＝120秒。16:9。屋上の続き。セリフは口元3本（ただいま／おかえり／てあらって。デザートいれておいたよ。話し言葉、漢字なし）。フェラは玄関の寄り。口内は CUMOUF。夜風呂は風呂120秒。写真は input/okaeri-120s の 01〜12（16:9。無い本はテキストから）。",
    "bath-120s": "風呂第5話。夜の風呂。10秒×12本＝120秒。16:9。日常は支度と洗体。非日常は洗い場で根元まで。セリフは口元3本（さきにあらってて／おふろだとよけいムクってる／あがったらごはんね。話し言葉、漢字なし）。フェラは洗い場の寄り。口内は CUMOUF。ご飯〜食卓は食卓120秒。写真は input/bath-120s の 01〜12（16:9。無い本はテキストから）。",
    "dinner-120s": "食卓第6話。風呂上がりから食卓。10秒×12本＝120秒。16:9。日常は配膳と食事。非日常はテーブルの下で根元まで。セリフは口元3本（たべなさい／ごはんのとちゅうなのに／うえもちゃんとたべなさい。話し言葉、漢字なし）。フェラはテーブル下の寄り。口内は CUMOUF。夜の布団は布団120秒。写真は input/dinner-120s の 01〜12（16:9。無い本はテキストから）。",
    "futon-120s": "布団第7話。食卓から布団。10秒×12本＝120秒。16:9。日常は片付けと布団。非日常は横になったまま根元まで。セリフは口元2本（ねるまえなのに／でんき、けしたよ。話し言葉、漢字なし）。フェラは布団の寄り。口内は CUMOUF。仰向けの口にセックスやアナルは入れない。休日午前は休日120秒。写真は input/futon-120s の 01〜12（16:9。無い本はテキストから）。",
    "sunday-120s": "休日第8話。休日午前。家から出ない。10秒×12本＝120秒。16:9。日常は二度寝・テレビ・洗濯。非日常はソファでもう入っている、抜いたあと根元まで。セリフは口元2本（やすみなのにアサからムクってる／ひるごはん、まだだよ。話し言葉、漢字なし）。セックスは AIO 横クローズ。フェラは床の寄り。口内は CUMOUF。アナルは入れない。午後の縁側は縁側120秒。写真は input/sunday-120s の 01〜12（16:9。無い本はテキストから）。",
    "engawa-120s": "縁側第9話。休日午後。縁側と二回戦。竿役はマドカ。10秒×12本＝120秒。16:9。日常は昼残り・縁側・庭の風。非日常は縁側でもう入っている、抜いたあとアヤがマドカを根元まで。セリフは口元2本（ひるからもムクってる／さらあらっとくから。話し言葉、漢字なし）。セックスは AIO 横クローズ。フェラは縁側の寄り。口内は CUMOUF。レイは入れない。アナルは入れない。写真は input/engawa-120s の 01〜12（16:9。無い本はテキストから）。",
    "sales-visit-60s": "訪問販売。ミルク売り。キャップのみ。ミルクは持たない。対面20秒。8本＝80秒。9:16。玄関。1本目: 販売員が画面左手・玄関扉の前に一人で立つ→チャイム→右側の扉が開いてアヤが右から入る。ハンバイにきましたのあとアヤが笑顔で20cmを軽く扱きながらあ、おっきいオチンチン。10-20は扱きながらおそかったねー／シコシコしてたらおそく。20-30はカチカチ／まちくたびれのあと扱きながら熱烈ベロチュー。30-40はキスをやめてあつい／サービス（恍惚）。40-50はえーありがとうー／じゃあ、いっただきまーすで跪いてジュボ。50-60は無言ジュボ。口はアヤ22ミニ・竿なし。販売員は5人目25・短め黒髪・中乳・ふたなり20cm・金玉なし・竿の根元にマンコ。口内は粘る白液を残して見せる。台詞は1本2行まで。行為は無言・寄り。hmmotion なし。",
    "checkup-100s": "定期検診。対面30秒。9本＝90秒。9:16。診察室ではない。家の玄関。1本目: 医師が画面左手・玄関扉の前に一人で立つ→チャイム＋こんにちは→右側の扉が開いてレイが右からはい。入ったあと短いフレンチキスとハグですぐ離れる。10-20はテイキケンシンにきました／あ、ヨロシクオネガイします！、そのあと恍惚の軽いキスですぐ離れる。20-30はふふ、オチンチンかたくておっきい！（妖艶に微笑んで軽くチンチンにキス）／では、シツレイして、いっぱいさわっちゃいますね！。そのあとベロチューとジュボは無言10秒。キスは両手で胸。クチとムネはぬるぬるでモンダイない。カクニンはカチカチおくまで、立ちの口パクのみ。最後はモンダイありすぎ、おくちにだされすぎのあと立ち上がって精液口移し濃厚ディープキス。医師32・結い髪・中乳・竿なし・聴診器。レイ24・20cm 立ち。台詞は1本2行まで。hmmotion なし。",
    "clinic-75s": "ケンシン。医院にアヤが来る。10本＝100秒。9:16。医師32・結い髪・中乳・聴診器・ふたなり20cm玉なしマンコあり。口はアヤ22ミニ・竿なし。医師の椅子はパイプ椅子。1本目: 女医は画面左手・パイプ椅子でまた開いてシコシコ無表情。アヤは右から入る。「オチンチンおっきい」のあと短い立ちキス、右のパイプ椅子におすわり（女医は立つ）。10-20は問診（キョウはどうしました？／サイキンおマンコがウズウズして、、、。余りは触って待つ）。20-30はそれはタイヘンですね！じゃあ、みていきますね、と妖艶に微笑んで立ち上がり、胸を触りながらディープキス。終わりは口を開けて先端から手の幅。しゃがみジュボ（アヤはマンコをこすりながら）。ガマンできないで押し倒し（女医は仰向けで超気持ちよさそう）、仰向けのままジュボしまくる→口内→仰向けのまま口移し→ゲンキ。セックスなし。騎乗なし。押し倒したあと女医はずっと仰向け。hmmotion なし。台詞: ヨロシクオネガイします！あ、オチンチンおっきい！／どうぞおすわりください／キョウはどうしました？／サイキンおマンコがウズウズして、、、／それはタイヘンですね！じゃあ、みていきますね／もう、ガマンできない！／ゲンキになりましたね／ありがとうございます。",
    "last-stop-40s": "終点40秒（つなぐ）。10秒×4本。9:16 576×1024。名前付きの「つなぐ」パック。最後のコマから I2V。車掌29・短髪・中乳・竿なし・ホイッスル。レイは座席で寝たまま立たない。普通の声では起きない。起こしのあと跪いて咥える（竿舐め禁止）。ジュボで起きる。口内 CUMOUF のあと車掌に戻る。台詞: しゅうてんです、おきてください／おきましたか？おきゃくさん、しゅうてんだからおりてください。hmmotion なし。",
    "last-train-120s": "終電。終点の延長。10本＝100秒。15秒禁止（VRAMで画面が小さくなる）。9:16。車掌とレイの2人だけ。車掌29・短髪・中乳・竿なし・ホイッスル。レイ24は車内では座席のまま立たない。20cm玉なしマンコあり。声かけは座っているレイに身体も顔も向ける。ジュボは10+10＝20秒で奥まで（竿舐め禁止）。口内のあと同じ目線で口移しで起こす。起きてから2人で電車の外の空の駅ホームへ。ホームで濃厚キス→ピロートーク→レイ立ち・車掌ひざまづきジュボ→口内→立ち上がって抱擁と口移しベロチュー。セックスなし。騎乗なし。台詞: しゅうてんです、おきてください／んっ、おくちにだしてもらって、からだがあつい、、、／おくち、あったかい、、、もっとして、、、。行為も10秒。hmmotion なし。既存の終点はそのまま。",
    "semen-bath-70s": "ザーメン風呂。5本＝50秒。9:16。家の小さいおフロ。アヤ22ミニ・竿なしが湯船。レイ24・20cmが立って重油級の白いドロッドロを溜める。湯ではなく白い粘液がお風呂。口移しなし。挿入なし。ジュボなし。hmmotion なし。台詞: ザーメンフロにして／いっぱいだすね。",
    "meat-wall-85s": "ニクカベ。巨大生物の体内のザーメン風呂。コンクリートに肉を貼った部屋ではない。おフロは生体の窪み。7本＝70秒。9:16。茶色い粘液は壁から、全身・顔・髪・チンチン・マンコに付く。白は風呂。廃油やヘドロの粘度だが色は不透明な白（茶色・黒のタールにしない）。水ではなくベトベトで肌に付く。混ざるが消えない。歩行の床は弾力。足は沈まない。レイは毎本フタナリ勃起20cm（画面下段、女体のみにしない）。竿は液から生えない。アヤ22ミニ・竿なし。歩行10秒はうわぁ＋手繋ぎ＋軽いフレンチキス（咥え・ジュボではない）。台詞10秒、ジュボ10・口内10は無言。ジュボは浸かり深さ判定なし（自然と根元まで）。口内のあとアヤが立ち上がって口移し。hmmotion なし。家のザーメン風呂とは別。台詞: うわぁ。。。すごいところだね。。。／あ、おフロ。。。でもこれって／ザーメンの、、、おフロ、、、すごいニオイ、、、／ザーメンのおフロ。。。あったかーい／もうガマンできない！おチンチンジュボジュボするの！／レイのザーメンおいしかった！",
    "meat-wall-cesspit-70s": "ニクカベ肥溜め。ニクカベの別バージョン。巨大生物の体内。7本＝70秒。9:16。冒頭は2人とも頭から足先まで白い廃油級ザーメンまみれ→大きな肥溜めを発見→肩までうんこの中。頭から足先まで濃い茶色の糞まみれ。アヤとレイのキス→ジュボするの→無言ジュボ→無言口内→おいしかった＋立ち上がって口移し。ジュボは浸かり深さ判定なし。レイは毎本フタナリ勃起20cm。アヤ22ミニ・竿なし。hmmotion なし。素のニクカベ（白いおフロ）とは別。台詞: うわぁ。。。あんなにおおきいコエダメだね。。。しろいのがからだじゅうについてる、、、あたままで、あしさきまで／このニオイ、、、アタマおかしくなりそう、、、こんなにこくて、うんこのニオイ、いきもできない、、、アタマおかしくなりそう、、、／んっ、キスして、、、あたまおかしくなりそう、、、こんなこえだめのなかで、あたままでうんこまみれなのに、キスして、、、／もうガマンできない！おチンチンジュボジュボするの！こんなこえだめのなかでも、れいのおチンチン、おくまでジュボジュボするの！／レイのザーメンおいしかった！こんなにこくてしろいの、おくまでだしてもらって、あたまおかしくなりそう、、、",
    "cafe-100s": "カフェ100秒。10秒×10本。9:16。建前は最後まで落とさない: おミズ＝ジュボ、ミルク＝ジュボと口内。客はアヤ22ミニ・竿なし。店員25・低いお団子・中乳・ふたなり20cm・トレイだけ。コーヒーは本物を置いたまま終わる。台詞は話し言葉（漢字なし）（1本に2行まで）。行為は無言・寄り。最後はベロチューと抱擁。",
    "train-sales-80s": "車内販売80秒。10秒×8本。9:16。建前: おチャ＝ジュボ、ミルクコーヒー＝ジュボと口内。客はレイ24（受け・自分の20cmは使わない）。販売員26・短め黒髪・中乳・ふたなり20cm・ワゴンだけ。台詞は話し言葉（漢字なし）。行為は無言・寄り。",
    "red-light-50s": "赤信号50秒。10秒×5本。9:16。建前: 信号待ちとナビ。運転はレイ24（20cm・両手はハンドル）、口はアヤ22。ジュボと口内だけ。放尿なし。車は動かない。台詞は話し言葉（漢字なし）。",
    "yoga-50s": "ヨガ50秒。10秒×5本。9:16。建前: コツバンを落とす。講師29・お団子・中乳・ふたなり20cm。生徒はアヤ22。四つん這いで最初から入っている（後背位 LoRA）。ジュボなし・放尿なし。台詞は話し言葉（漢字なし）。",
    "back-wash-60s": "背中流し60秒。10秒×6本。9:16。建前: 上から下へ洗う。洗うのはサヤカ39（竿なし）。洗われるのはマドカ22（20cm）。背中→マドカのマンコ舐め（竿は使わない）→アガリユ＝ジュボ（根元まで）。台詞は話し言葉（漢字なし）。",
    "karaoke-50s": "カラオケ50秒。10秒×5本。9:16。建前: サビ待ちと点数。歌うのはマドカ22（20cm・マイク）。口はアヤ22。歌のあいだジュボ、最後の音で口内。放尿なし。台詞は話し言葉（漢字なし）。",
    "laundromat-50s": "コインランドリー50秒。10秒×5本。9:16。建前: あと何分。竿はレイ24、受けはアヤ22。洗濯機の上でもう入っている（AIO 横クローズ）。ジュボなし・放尿なし。台詞は話し言葉（漢字なし）。",
    "lecture-desk-50s": "講義机50秒。10秒×5本。9:16。建前: 板書とノート。先生36・眼鏡・結い髪・中乳・ふたなり20cm・チョークだけ。アヤ22が教卓の下でジュボ→口内。上の声は授業。放尿なし。台詞は話し言葉（漢字なし）。授業120秒（専用）とは別。",
    "camp-50s": "キャンプ50秒。10秒×5本。9:16。建前: 虫よけ。レイ24がアヤ22のマンコを舐めるだけ。レイの20cmは画面にあっても使わない。ジュボなし・放尿なし。台詞は話し言葉（漢字なし）。",
    "fireworks-50s": "花火50秒。10秒×5本。9:16。建前: 上を見る。竿はマドカ22、受けはサヤカ39。立ったまま後ろから入っている。顔は花火のまま。ジュボなし・放尿なし。台詞は話し言葉（漢字なし）。",
    "manhole-30s": "物語の追加。ハイスイコウ。10秒×2＝20秒。9:16。アヤ22ミニ・竿なし＋レイ24・20cm。1本目はフタの会話のあと、口を開けて先端から手の幅。2本目は無言で根元までジュボ→口内。口内のあとはジュボ側が同じ目線に立ち上がって濃厚キス口移し。hmmotion なし。",
    "roof-ac-30s": "物語の追加。屋上クーラー。10秒×2＝20秒。9:16。サヤカ39・竿なし＋マドカ22・20cm。1本目はクーラーの会話のあと、受け入れる立ち・挿入寸前（先端から手の幅、未挿入）。2本目は無言でもう入っている立ち（AIO・hmmotion 先頭）→中に出して腿に残る。口移しなし。",
    "tetrapod-30s": "物語の追加。ハマのテトラ。10秒×2＝20秒。9:16。アヤ＋レイ。1本目は風の会話のあと、跪いて口を開けて先端から手の幅。2本目は無言ジュボ→口内。ジュボ側が同じ目線に立ち上がって濃厚キス口移し。hmmotion なし。",
    "locker-30s": "物語の追加。廃校ロッカー。10秒×2＝20秒。9:16。アヤ＋マドカ。1本目はカギの会話とベロチューのあと、跪いて口を開けて先端から手の幅。2本目は無言ジュボ→口内。ジュボ側が同じ目線に立ち上がって濃厚キス口移し。hmmotion なし。",
    "crossing-30s": "物語の追加。ドウロのど真ん中。10秒×2＝20秒。9:16。サヤカ＋レイ。1本目は信号の会話のあと、跪いて口を開けて先端から手の幅。2本目は無言ジュボ→口内。ジュボ側が同じ目線に立ち上がって濃厚キス口移し。hmmotion なし。",
    "lookout-30s": "物語の追加。ガケの展望台。10秒×2＝20秒。9:16。アヤ＋レイ。1本目は霧の会話のあと、アヤ仰向け・膝を開いて舐め寸前。2本目は無言クンニ（竿は使わない）。ジュボなし・口移しなし。hmmotion なし。",
    "factory-30s": "物語の追加。コウジョウあと。10秒×2＝20秒。9:16。サヤカ＋マドカ。1本目はサビの会話のあと、受け入れる立ち・挿入寸前（先端から手の幅、未挿入）。2本目は無言でもう入っている立ち→中に出して腿に残る。口移しなし。hmmotion 先頭。",
    "gas-station-30s": "物語の追加。ガソリンスタンド跡。10秒×2＝20秒。9:16。アヤ＋レイ。1本目はミズの会話のあと、口を開けて先端から手の幅で止まる（飲まない）。2本目は無言ジュボ→口内。ジュボ側が同じ目線に立ち上がって濃厚キス口移し。hmmotion なし。",
    "tunnel-phone-30s": "物語の追加。トンネル非常電話。10秒×2＝20秒。9:16。アヤ＋レイ。1本目は電話の会話のあと、受話器を持ったまま跪いて口を開けて先端から手の幅。2本目は受話器を持ったまま口だけで根元まで→口内。手は竿に触れない。ジュボ側が同じ目線に立ち上がって濃厚キス口移し。hmmotion なし。",
    "riverbank-30s": "物語の追加。川原のゴミ。10秒×2＝20秒。9:16。サヤカ＋マドカ。1本目はフクロの会話のあと、跪いて口を開けて先端から手の幅。2本目は無言ジュボ→口内。ジュボ側が同じ目線に立ち上がって濃厚キス口移し。hmmotion なし。",
    "hachiko-30s": "物語の追加。ハチコウ。10秒×2＝20秒（15秒禁止）。9:16。夜の渋谷ハチコウ前。レイ24・20cmが画面左手で立ってフルボッキをシコシコ。アヤ22ミニ・竿なしが右から現れてキス→口を開けて先端から手の幅。2本目は無言で根元まで濃厚ジュボ→口内。口が半分も保てず顔にすごい量。ジュボ側が同じ目線に立ち上がって濃厚キス口移し。hmmotion なし。",
    "shorts-immoral": "短編集（参照）。10秒完結の超濃厚日常インモラルを複数本。メイン4人のうち竿役（レイ／マドカ）とハメ役（アヤ／サヤカ）の2人。つなぎなし。各本は input/cast/ の人物写真を R2V 参照（最初のコマではない）。画面は本ごと（フェラ9:16寄り、挿入は16:9または立ち9:16）。文と部品は自動。FL2VA の竿は載せない。穴（synth-pussy）は載せる（竿役以外に竿が付くのを防ぐ）。",
    "redo": "生成し直し。壊れた本から作り直す。作り直しの物語と開始の本（1始まり）を③で指定。開始より前の本は output に残っている動画をストックして連結する。開始の本は前の本の最後のコマ（起点画像）から I2V。専用で作っていても途中からならつなぐ。",
}

LORA_JA = {
    "mystic-xxx-h3": "解剖（Mystic）",
    "synth-pussy-h3": "穴の見え方",
    "lesbian-cunnilingus-h3": "レズクンニ",
    "pussy-spread-h3": "性器を広げる",
    "anal-penetration-coachbate": "アナル挿入（CoachBate・有料・未使用）",
    "hmnsfw-aio-v25": "総合えっち",
    "futa-h3-v51": "ふたなり",
    "penis-lora-h3": "竿",
    "blowjob-h3": "フェラ",
    "riding-pose-i2v": "騎乗POV（I2V）",
    "cowgirl-position-h3": "騎乗",
    "doggy-h3": "後背位",
    "missionary-pov-h3": "正常位POV",
    "hmcumshot-v2": "射精",
    "facial-cumshot-h3": "顔射",
    "final-thrust-h3": "中出し",
    "cumouf-h3": "口内射精",
    "fingering-h3": "指入れ",
    "thumbinbutt-h3": "アナル挿入の動き（ThumbInButt）",
    "hmmasturbation-h3": "オナニー",
    "footjob-h3": "足コキ",
    "remote-orgasm-h3": "絶頂",
    "h3-realism-people": "肌のリアルさ",
    "tiddies-realism-slider": "胸の大きさ",
    "larry-v4": "Larry v4",
    "cinema-dy": "シネマ質感",
    "astro-cinema-h3": "映画レンズ",
    "minimax-h3-turbo-fl2v-4step": "LightX2V 4step",
    "minimax-h3-turbo-fl2v-8step": "LightX2V 8step",
    "minimax-h3-turbo-ref2v-4step": "LightX2V Ref2VA",
    "aftermidnight-ref2va": "AfterMidnight（R2V行為）",
    "photoreal-h3-still": "静止画用の写実",
}

SFW_SITUATIONS = {"sfw_daily", "sfw_preview", "sfw_audio", "sfw_r2v"}
# Dedicated stories: hard cuts by default. ③ can replay them as a last-frame chain (STORY_PLAY_*).
STORY_ORDER = (
    "homecoming-90s",
    "dishes-90s",
    "commute-120s",
    "lecture-120s",
    "rooftop-100s",
    "okaeri-120s",
    "bath-120s",
    "dinner-120s",
    "futon-120s",
    "sunday-120s",
    "engawa-120s",
)
STORY_IDS = set(STORY_ORDER)
# Named chain packs. Not stories (is_story False). Never added to STORY_IDS.
# The JSON on disk is seamless (last-frame I2V); ③ replays each pack in the same
# three plays as the dedicated stories (専用 / つなぐ / つなぐ修).
CHAIN_PACK_ORDER = (
    "sales-visit-60s",
    "checkup-100s",
    "clinic-75s",
    "last-stop-40s",
    "last-train-120s",
    "semen-bath-70s",
    "meat-wall-85s",
    "meat-wall-cesspit-70s",
    "cafe-100s",
    "train-sales-80s",
    "red-light-50s",
    "yoga-50s",
    "back-wash-60s",
    "karaoke-50s",
    "laundromat-50s",
    "lecture-desk-50s",
    "camp-50s",
    "fireworks-50s",
    "manhole-30s",
    "roof-ac-30s",
    "tetrapod-30s",
    "locker-30s",
    "crossing-30s",
    "lookout-30s",
    "factory-30s",
    "gas-station-30s",
    "tunnel-phone-30s",
    "riverbank-30s",
    "hachiko-30s",
)
CHAIN_PACK_IDS = set(CHAIN_PACK_ORDER)
# 物語の追加: 10秒×2＝20秒。台詞は1本目（futa_visible）だけ。行為は無言。
ADDON_PACK_ORDER = (
    "manhole-30s",
    "roof-ac-30s",
    "tetrapod-30s",
    "locker-30s",
    "crossing-30s",
    "lookout-30s",
    "factory-30s",
    "gas-station-30s",
    "tunnel-phone-30s",
    "riverbank-30s",
    "hachiko-30s",
)
ADDON_PACK_IDS = frozenset(ADDON_PACK_ORDER)
# 15s independent dirty shorts. Not a story (is_story False). Not a chain pack.
ANTHOLOGY_IDS = ("shorts-immoral",)
ANTHOLOGY_ID_SET = set(ANTHOLOGY_IDS)
ANTHOLOGY_LABEL = "短編集（参照）"
REDO_LABEL = "生成し直し"
# Legacy long labels of the first three packs. They keep the old behaviour
# (last-frame chain, clip 1 rewritten as a long take) = つなぐ修.
CHAIN_PACK_TITLE_JA = {
    "sales-visit-60s": "訪問販売60秒（つなぐ）",
    "checkup-100s": "定期検診100秒（つなぐ）",
    "last-stop-40s": "終点40秒（つなぐ）",
}
STORY_CANVAS = (576, 1024)
STORY_CANVAS_16_9 = (1024, 576)
CANVAS_9_16 = {"width": 576, "height": 1024, "aspect": "9:16"}
CANVAS_16_9 = {"width": 1024, "height": 576, "aspect": "16:9"}
SHORTS_SHAFT = frozenset({"rei", "madoka"})
SHORTS_RECEIVER = frozenset({"aya", "sayaka"})
SHORTS_MAIN4 = ("Aya", "Rei", "Madoka", "Sayaka")

STORY_PLAY_DEDICATED = "dedicated"
STORY_PLAY_CHAIN = "chain"
STORY_PLAY_CHAIN_REWRITE = "chain_rewrite"
STORY_PLAY_REF_CHAIN = "ref_chain"
STORY_PLAY_REF_CHAIN_REWRITE = "ref_chain_rewrite"
STORY_PLAYS = (
    STORY_PLAY_DEDICATED,
    STORY_PLAY_CHAIN,
    STORY_PLAY_CHAIN_REWRITE,
    STORY_PLAY_REF_CHAIN,
    STORY_PLAY_REF_CHAIN_REWRITE,
)
STORY_TITLE_JA = {
    "homecoming-90s": "帰宅",
    "dishes-90s": "洗い物",
    "commute-120s": "登校",
    "lecture-120s": "授業",
    "rooftop-100s": "屋上",
    "okaeri-120s": "おかえり",
    "bath-120s": "風呂",
    "dinner-120s": "食卓",
    "futon-120s": "布団",
    "sunday-120s": "休日",
    "engawa-120s": "縁側",
    "sales-visit-60s": "訪問販売",
    "checkup-100s": "定期検診",
    "clinic-75s": "ケンシン",
    "last-stop-40s": "終点",
    "last-train-120s": "終電",
    "semen-bath-70s": "ザーメン風呂",
    "meat-wall-85s": "ニクカベ",
    "meat-wall-cesspit-70s": "ニクカベ肥溜め",
    "cafe-100s": "カフェ",
    "train-sales-80s": "車内販売",
    "red-light-50s": "赤信号",
    "yoga-50s": "ヨガ",
    "back-wash-60s": "背中流し",
    "karaoke-50s": "カラオケ",
    "laundromat-50s": "ランドリー",
    "lecture-desk-50s": "講義机",
    "camp-50s": "キャンプ",
    "fireworks-50s": "花火",
    "manhole-30s": "ハイスイコウ",
    "roof-ac-30s": "屋上クーラー",
    "tetrapod-30s": "ハマのテトラ",
    "locker-30s": "廃校ロッカー",
    "crossing-30s": "ドウロのど真ん中",
    "lookout-30s": "ガケの展望台",
    "factory-30s": "コウジョウあと",
    "gas-station-30s": "ガソリンスタンド跡",
    "tunnel-phone-30s": "トンネル非常電話",
    "riverbank-30s": "川原のゴミ",
    "hachiko-30s": "ハチコウ",
}
STORY_PLAY_JA = {
    STORY_PLAY_DEDICATED: "専用",
    STORY_PLAY_CHAIN: "つなぐ",
    STORY_PLAY_CHAIN_REWRITE: "つなぐ修",
    STORY_PLAY_REF_CHAIN: "参照つなぐ",
    STORY_PLAY_REF_CHAIN_REWRITE: "参照つなぐ修",
}
STORY_PLAY_HELP_JA = {
    STORY_PLAY_DEDICATED: "カット。JSON のまま。最後のコマからは続けない",
    STORY_PLAY_CHAIN: "つなぐ・文そのまま。最後のコマから I2V。1本目の文は直さない",
    STORY_PLAY_CHAIN_REWRITE: "つなぐ・1本目を長回しに直す。最後のコマから I2V。③オンなら最後の本だけ合わせる",
    STORY_PLAY_REF_CHAIN: "参照つなぐ。1本目は input/cast/ を R2V 参照（最初のコマではない）。文はそのまま。2本目以降は最後のコマから I2V",
    STORY_PLAY_REF_CHAIN_REWRITE: "参照つなぐ修。1本目は R2V 参照＋長回しに直す。2本目以降は最後のコマから I2V。③オンなら最後の本だけ合わせる",
}
_STORY_PLAY_LABELS: dict[str, tuple[str, str]] = {}


def story_play_label(story_id: str, play: str) -> str:
    return f"{STORY_TITLE_JA[story_id]}（{STORY_PLAY_JA[play]}）"


def story_play_labels() -> list[str]:
    """③ dropdown rows: 11 stories × 5 plays, story order, 専用 → つなぐ → つなぐ修 → 参照つなぐ → 参照つなぐ修."""
    out: list[str] = []
    for sid in STORY_ORDER:
        for play in STORY_PLAYS:
            out.append(story_play_label(sid, play))
    return out


def chain_pack_labels() -> list[str]:
    """③ dropdown rows after the stories: every pack × 5 plays, pack order."""
    out: list[str] = []
    for pid in CHAIN_PACK_ORDER:
        for play in STORY_PLAYS:
            out.append(story_play_label(pid, play))
    return out


def chain_pack_legacy_labels() -> list[str]:
    return [CHAIN_PACK_TITLE_JA[pid] for pid in CHAIN_PACK_ORDER if pid in CHAIN_PACK_TITLE_JA]


def _register_story_play_labels() -> None:
    """{短名}（専用|つなぐ|つなぐ修|参照つなぐ|参照つなぐ修） → id + play for stories and packs.

    Long legacy 「〜（専用）」 story labels stay dedicated. Long legacy pack labels
    (「訪問販売60秒（つなぐ）」 etc.) keep their old behaviour: つなぐ修.
    """
    for sid in STORY_ORDER + CHAIN_PACK_ORDER:
        for play in STORY_PLAYS:
            label = story_play_label(sid, play)
            SITUATION_JA.setdefault(label, sid)
            _STORY_PLAY_LABELS[label] = (sid, play)
    for label, sid in list(SITUATION_JA.items()):
        if label in _STORY_PLAY_LABELS:
            continue
        if sid in STORY_IDS:
            _STORY_PLAY_LABELS[label] = (sid, STORY_PLAY_DEDICATED)
        elif sid in CHAIN_PACK_IDS:
            _STORY_PLAY_LABELS[label] = (sid, STORY_PLAY_CHAIN_REWRITE)


_register_story_play_labels()


def resolve_situation(name: str) -> str:
    key = str(name or "").strip()
    if key in SITUATION_JA:
        return SITUATION_JA[key]
    raise SystemExit(
        "シーンの名前が分かりません。フォームのリストから選んでください。"
        f" 入力: {name}"
    )


def resolve_mode(name: str) -> str:
    key = str(name or "").strip()
    if key in MODE_JA:
        return MODE_JA[key]
    raise SystemExit("作り方は「テキストから（写真なし）」か「写真から（1枚必要）」を選んでください。")


def friendly_lora(lora_id: str) -> str:
    return LORA_JA.get(str(lora_id), str(lora_id))


def is_vanilla(situation: str) -> bool:
    return resolve_situation(situation) == "vanilla"


def is_story(situation: str) -> bool:
    try:
        return resolve_situation(situation) in STORY_IDS
    except SystemExit:
        return str(situation or "").strip() in STORY_IDS


def is_chain_pack(situation: str) -> bool:
    """Named last-frame chain pack (訪問販売 / 定期検診 / ケンシン / 終点 / 終電 / ザーメン風呂 / ニクカベ / 建前 / 物語の追加). Not a story."""
    try:
        return resolve_situation(situation) in CHAIN_PACK_IDS
    except SystemExit:
        return str(situation or "").strip() in CHAIN_PACK_IDS


def is_anthology(situation: str) -> bool:
    """15s independent shorts (短編集). Not a story, not a named pack."""
    try:
        return resolve_situation(situation) in ANTHOLOGY_ID_SET
    except SystemExit:
        return str(situation or "").strip() in ANTHOLOGY_ID_SET


def resolve_story_play(situation: str) -> str:
    """dedicated | chain | chain_rewrite | ref_chain | ref_chain_rewrite."""
    key = str(situation or "").strip()
    hit = _STORY_PLAY_LABELS.get(key)
    if hit is not None:
        return hit[1]
    # 「参照つなぐ」 contains 「つなぐ」 — check the longer suffixes first.
    if key.endswith("（参照つなぐ修）"):
        return STORY_PLAY_REF_CHAIN_REWRITE
    if key.endswith("（参照つなぐ）"):
        return STORY_PLAY_REF_CHAIN
    if key.endswith("（つなぐ修）"):
        return STORY_PLAY_CHAIN_REWRITE
    if key.endswith("（つなぐ）"):
        return STORY_PLAY_CHAIN
    return STORY_PLAY_DEDICATED


def apply_story_play(story: dict[str, Any], play: str) -> dict[str, Any]:
    """Copy of the story JSON with the ③ play applied. The JSON on disk is never edited.

    dedicated: seamless False, rewrite_chain_prompts False, every clip start still_or_t2v.
    chain: seamless True, rewrite False, clip 2+ start continue (prompts untouched).
    chain_rewrite: seamless True, rewrite True, clip 2+ start continue.
    ref_chain / ref_chain_rewrite: same as chain / chain_rewrite, but clip 1 is R2V from
    Drive input/cast/ identity stills when a main-cast person is visible at t=0
    (use_cast_ref). Visit openings (resident HIDDEN at the start) fall through to T2V
    so those stills do not spawn a second body. Clip 2+ stays last-frame I2V.
    ③「テキストから」は無視する.
    """
    mode = str(play or STORY_PLAY_DEDICATED).strip()
    if mode not in STORY_PLAYS:
        raise SystemExit(f"再生の種類が分かりません: {play}")
    out = json.loads(json.dumps(story))
    clips = [dict(c) for c in (out.get("clips") or [])]
    use_cast = mode in (STORY_PLAY_REF_CHAIN, STORY_PLAY_REF_CHAIN_REWRITE)
    rewrite = mode in (STORY_PLAY_CHAIN_REWRITE, STORY_PLAY_REF_CHAIN_REWRITE)
    chained = mode != STORY_PLAY_DEDICATED
    if not chained:
        out["seamless"] = False
        out["rewrite_chain_prompts"] = False
        for clip in clips:
            clip["start"] = "still_or_t2v"
    else:
        out["seamless"] = True
        out["rewrite_chain_prompts"] = rewrite
        for i, clip in enumerate(clips):
            clip["start"] = "still_or_t2v" if i == 0 else "continue"
    out["play"] = mode
    out["use_cast_ref"] = use_cast
    out["clips"] = clips
    return out


def is_redo(situation: str) -> bool:
    """③「生成し直し」。既存の物語／パックを途中の本から I2V し直す。"""
    key = str(situation or "").strip()
    if key == REDO_LABEL:
        return True
    try:
        return resolve_situation(key) == "redo"
    except SystemExit:
        return False


def redo_story_labels() -> list[str]:
    """③「作り直しの物語」の候補。専用11話と名前付きパックの5再生。短編集はつながない。"""
    return story_play_labels() + chain_pack_labels()


def parse_redo_start(raw: Any, clip_count: int = 0) -> int:
    """1始まりの開始本。範囲外は 1..clip_count に丸める。"""
    try:
        n = int(float(str(raw).strip()))
    except (TypeError, ValueError):
        n = 1
    if n < 1:
        n = 1
    limit = int(clip_count or 0)
    if limit > 0 and n > limit:
        n = limit
    return n


def redo_start_frame_name(start_1based: int) -> str | None:
    """N本目の起点は、N-1本目の最後のコマ = h3_chain_{N-2}.png。1本目はなし。"""
    start = parse_redo_start(start_1based)
    if start <= 1:
        return None
    return f"h3_chain_{start - 2}.png"


def find_existing_story_clip(
    out_dir: Path | str,
    story_id: str,
    clip_index: int,
) -> Path | None:
    """output にある h3_{id}_p{index}*.mp4。stock コピーは見ない。新しい方を返す。"""
    root = Path(out_dir)
    if not root.is_dir():
        return None
    key = f"h3_{story_id}_p{int(clip_index)}"
    hits: list[Path] = []
    for path in root.rglob("*.mp4"):
        if key not in path.name:
            continue
        if "stock" in {part.lower() for part in path.parts}:
            continue
        hits.append(path)
    hits.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[0] if hits else None


def stock_completed_clips(
    *,
    out_dir: Path | str,
    input_dir: Path | str,
    story_id: str,
    start_1based: int,
    stamp: str | None = None,
) -> dict[str, Any]:
    """開始本より前の動画と最後のコマを output/stock/<id>/<stamp>/ にコピーする。"""
    start = parse_redo_start(start_1based)
    if start <= 1:
        return {"dir": None, "clips": [], "frames": []}
    when = stamp or time.strftime("%Y%m%d-%H%M%S")
    dest = Path(out_dir) / "stock" / str(story_id) / when
    dest.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    frames: list[Path] = []
    missing: list[int] = []
    for i in range(start - 1):
        src = find_existing_story_clip(out_dir, story_id, i)
        if src is None:
            missing.append(i + 1)
            continue
        target = dest / src.name
        shutil.copy2(src, target)
        copied.append(target)
        frame_src = Path(input_dir) / f"h3_chain_{i}.png"
        if frame_src.is_file() and frame_src.stat().st_size >= 100:
            frame_dst = dest / frame_src.name
            shutil.copy2(frame_src, frame_dst)
            frames.append(frame_dst)
    if missing:
        raise SystemExit(
            "生成し直しの前の本が output にありません: "
            + "、".join(f"{n}本目" for n in missing)
            + "。先に途中まで作ってから、③で生成し直しを選んでください。"
        )
    return {"dir": dest, "clips": copied, "frames": frames}


def ensure_redo_start_frame(
    input_dir: Path | str,
    out_dir: Path | str,
    story_id: str,
    start_1based: int,
) -> Path:
    """開始本の起点画像。無ければ直前の動画から最後のコマを抜く。"""
    name = redo_start_frame_name(start_1based)
    if name is None:
        raise SystemExit("1本目から作り直すときは起点画像は使いません。")
    dest = Path(input_dir) / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size >= 100:
        return dest
    prev = find_existing_story_clip(out_dir, story_id, int(start_1based) - 2)
    if prev is None:
        raise SystemExit(
            f"{int(start_1based)}本目の起点画像（{name}）がありません。"
            f"{int(start_1based) - 1}本目の動画か最後のコマを置いてから、③をもう一度。"
        )
    return extract_last_frame(prev, dest)


def apply_redo_play(story: dict[str, Any], play: str, start_1based: int) -> dict[str, Any]:
    """途中から作り直す再生。2本目以降の開始なら専用でも last-frame I2V（つなぐ・文そのまま）。"""
    clips = list(story.get("clips") or [])
    start = parse_redo_start(start_1based, len(clips))
    source = str(play or STORY_PLAY_DEDICATED).strip()
    if start <= 1:
        out = apply_story_play(story, source)
    else:
        out = apply_story_play(story, STORY_PLAY_CHAIN)
        out["use_cast_ref"] = False
        out["rewrite_chain_prompts"] = False
    out["redo"] = True
    out["redo_start"] = start
    out["redo_source_play"] = source
    return out


def story_rewrite_chain_prompts(story: dict[str, Any]) -> bool:
    """Packs without the key keep the current behaviour: seamless → rewrite clip 1 as one long take."""
    if "rewrite_chain_prompts" in story:
        return bool(story.get("rewrite_chain_prompts"))
    return bool(story.get("seamless"))


CAST_STILL_STEMS: dict[str, dict[str, tuple[str, ...]]] = {
    "sayaka": {"bust": ("sayaka-bust", "sayaka_bust"), "full": ("sayaka-full", "sayaka_full")},
    "rei": {"bust": ("rei-bust", "rei_bust"), "full": ("rei-full", "rei_full")},
    "aya": {"bust": ("aya-bust", "aya_bust"), "full": ("aya-full", "aya_full")},
    "madoka": {"bust": ("madoka-bust", "madoka_bust"), "full": ("madoka-full", "madoka_full")},
}
CAST_STILL_EXTS = (".jpg", ".jpeg", ".png", ".webp")
CAST_STILL_PEOPLE = ("aya", "sayaka", "rei", "madoka")
EXPECTED_CAST_FILES = (
    "sayaka-bust",
    "sayaka-full",
    "rei-bust",
    "rei-full",
    "aya-bust",
    "aya-full",
    "madoka-bust",
    "madoka-full",
)


def find_cast_file(cast_dir: Path | str, person: str, kind: str) -> Path | None:
    root = Path(cast_dir)
    if not root.is_dir():
        return None
    stems = CAST_STILL_STEMS.get(str(person).lower(), {}).get(str(kind).lower()) or ()
    files = {fn.lower(): root / fn for fn in os.listdir(root)}
    for stem in stems:
        for ext in CAST_STILL_EXTS:
            hit = files.get((stem + ext).lower())
            if hit is not None and hit.is_file():
                return hit
    return None


_WHO_BLOCK_RE = re.compile(
    r"(?m)^WHO:\s*\n(.*?)(?=\n(?:subject_definitions:|environment:|HARD LOCK:|CAMERA:|\Z))",
    re.S,
)
_HIDDEN_WHO_HINT_RE = re.compile(
    r"NOT IN FRAME|NOT IN THIS STORY|OFF SCREEN|HIDDEN at the start|"
    r"not visible at the start|not in frame yet|behind the CLOSED door",
    re.I,
)


def who_hidden_at_start(prompt: str) -> set[str]:
    """WHO names who must not appear in frame 1 (behind a closed door, not in frame yet)."""
    hidden: set[str] = set()
    text = str(prompt or "")
    match = _WHO_BLOCK_RE.search(text)
    block = match.group(1) if match else ""
    for line in block.split("\n"):
        line = line.strip()
        if " = " not in line:
            continue
        name, rest = line.split("=", 1)
        if _HIDDEN_WHO_HINT_RE.search(rest):
            hidden.add(name.strip().lower())
    return hidden


def clip_cast_people(clip: dict[str, Any]) -> list[str]:
    """Main-cast people visible at t=0. Hidden / not-in-frame names are dropped."""
    hidden = who_hidden_at_start(str(clip.get("prompt") or ""))
    named = [str(n).strip().lower() for n in (clip.get("names") or []) if str(n).strip()]
    out: list[str] = []
    for n in named:
        if n in CAST_STILL_STEMS and n not in out and n not in hidden:
            out.append(n)
    if out:
        return out
    prompt = str(clip.get("prompt") or "")
    for n in CAST_STILL_PEOPLE:
        if n in hidden:
            continue
        if re.search(rf"\b{n}\b", prompt, re.I) and n not in out:
            out.append(n)
    return out


def pick_cast_lead(clip: dict[str, Any]) -> tuple[str, str]:
    """(person, bust|full) for the first identity still. R2V uses bust+full, not I2V Picture 1."""
    people = clip_cast_people(clip)
    prompt = str(clip.get("prompt") or "")
    sit = str(clip.get("situation") or "").strip()
    lip = "LIP SYNC" in prompt or bool(spoken_lines(prompt))
    if lip:
        for n in ("aya", "sayaka", "rei", "madoka"):
            if n in people:
                return n, "bust"
        return "aya", "bust"
    if sit in {"oral", "oral_creampie", "cunnilingus_futa"}:
        for n in ("aya", "sayaka", "rei", "madoka"):
            if n in people:
                return n, "bust"
        return "aya", "bust"
    if sit in {"futa_sex", "doggy", "futa_masturbation"}:
        for n in ("rei", "madoka", "aya", "sayaka"):
            if n in people:
                return n, "full"
        return "rei", "full"
    for n in ("rei", "aya", "madoka", "sayaka"):
        if n in people:
            return n, "full"
    return "rei", "full"


def pick_cast_stills(clip: dict[str, Any], cast_dir: Path | str, *, max_stills: int = 4) -> list[Path]:
    """Bust + full identity stills for people in the clip. Cap 4. Missing files abort."""
    root = Path(cast_dir)
    wanted = "、".join(EXPECTED_CAST_FILES)
    if not root.is_dir():
        raise SystemExit(
            "参照モードは Drive の input/cast/ に4人の上半身・全身（8枚）が必要です。"
            f" 置く名前: {wanted}（jpg / jpeg / png / webp）"
        )
    people = clip_cast_people(clip)
    if not people:
        return []
    lead_person, lead_kind = pick_cast_lead(clip)
    ordered: list[str] = []
    for n in [lead_person, *people]:
        if n not in ordered:
            ordered.append(n)
    pairs: list[tuple[str, str]] = []
    for person in ordered:
        kinds = (lead_kind, "full" if lead_kind != "full" else "bust") if person == lead_person else ("bust", "full")
        for kind in kinds:
            pairs.append((person, kind))
            if len(pairs) >= max_stills:
                break
        if len(pairs) >= max_stills:
            break
    paths: list[Path] = []
    missing: list[str] = []
    for person, kind in pairs:
        still = find_cast_file(root, person, kind)
        if still is None:
            missing.append(f"{person}-{kind}")
        else:
            paths.append(still)
    if missing or not paths:
        all_missing = [
            name
            for name in EXPECTED_CAST_FILES
            if find_cast_file(root, *name.rsplit("-", 1)) is None
        ]
        raise SystemExit(
            "参照モードの人物写真が足りません。"
            f" この本は {lead_person}-{lead_kind} が必要です。"
            f" 置く名前: {wanted}。"
            + (f" 足りない: {'、'.join(all_missing or missing)}" if (all_missing or missing) else "")
        )
    return paths


def pick_cast_still(clip: dict[str, Any], cast_dir: Path | str) -> Path:
    paths = pick_cast_stills(clip, cast_dir)
    if not paths:
        raise SystemExit("参照モード: 開始時に見えるメインキャストがいません。")
    return paths[0]


def lock_r2v_cast_prompt(prompt: str, still_paths: list[Path], *, duration_s: float = 10.0) -> str:
    """Identity ROLE LOCK for Ref2VA. Never the I2V 'first frame is Picture 1' header."""
    body = str(prompt or "").strip()
    body = re.sub(
        r"^For the target video, at 0\.00 seconds into the target video,\s*"
        r"<Picture 1> \(from \[Shot 1\]\) is fully referenced\.\s*",
        "",
        body,
        count=1,
        flags=re.I,
    ).strip()
    img_names = [Path(p).name for p in still_paths]
    extra = (
        "Identity stills are references only, not the first frame of a clip. "
        "Invent cinematic motion consistent with the stills. "
        "Do not freeze on a portrait pose."
    )
    finalize = r2v_finalize_prompt
    if finalize is None:
        # ② imported us before h3_r2v_core.py existed. Load it now.
        from h3_r2v_core import finalize_prompt as finalize
    locked = finalize(body, img_names, [], float(duration_s), inject_role_lock=True)
    if extra.lower() not in locked.lower():
        locked = f"{locked}\n\n{extra}"
    return locked


def explain_choice(situation: str, mode: str) -> str:
    if is_redo(situation):
        return (
            f"シーン: {situation}\n"
            "作り方: 途中の本から、前の本の最後のコマ（起点画像）で I2V し直す\n"
            f"説明: {SITUATION_HELP['redo']}\n"
            "作り直しの物語と開始の本を③で指定。開始より前の本はストックして連結します。"
        )
    sid = resolve_situation(situation)
    mid = resolve_mode(mode)
    how = "テキストから動画（写真は使いません）" if mid == "t2v" else "写真1枚から動画（Drive の input に jpg）"
    play_now = ""
    try:
        play_now = resolve_story_play(situation) if sid in STORY_IDS or sid in CHAIN_PACK_IDS else ""
    except Exception:
        play_now = ""
    if sid in ANTHOLOGY_ID_SET:
        how = "人物写真を参照して動画（R2V。1枚を最初のコマにはしない）"
    elif play_now in {STORY_PLAY_REF_CHAIN, STORY_PLAY_REF_CHAIN_REWRITE}:
        how = "1本目は人物写真を参照（R2V）。2本目以降は最後のコマから I2V"
    if sid == "vanilla":
        return (
            f"シーン: {situation}\n"
            f"作り方: {how}\n"
            f"説明: {SITUATION_HELP[sid]}\n"
            "えっち用の部品は使いません。速いモード（Turbo）を使います。"
        )
    parts = "、".join(friendly_lora(x) for x in SITUATION_DOWNLOAD[sid])
    cap = (
        "重ね上限は 解剖(Mystic 0.5) + 竿 + 穴 + Turbo。シネマなし。体位・フェラなどの行為 LoRA は載せない。玉なし＋マンコあり。"
        if sid in {"sfw_daily", "sfw_preview", "sfw_audio"}
        else (
            "重ね上限は Turbo1 + 画質1。エロ用は入れません。"
            if sid in SFW_SITUATIONS
            else "重ね上限は 行為1 + 解剖0〜1 + ヘルパー0〜2 + Turbo0〜1。Fal には載せません。"
        )
    )
    play_line = ""
    if sid in STORY_IDS:
        play = resolve_story_play(situation)
        play_line = f"再生: {STORY_PLAY_JA[play]}（{STORY_PLAY_HELP_JA[play]}）\n"
    elif sid in CHAIN_PACK_IDS:
        play = resolve_story_play(situation)
        play_line = f"再生: {STORY_PLAY_JA[play]}（{STORY_PLAY_HELP_JA[play]}）。名前付きパック。専用ストーリーではありません\n"
    elif sid in ANTHOLOGY_ID_SET:
        play_line = "再生: 短編集（参照）。10秒完結×複数。つなぎなし。人物写真を R2V 参照\n"
    return (
        f"シーン: {situation}\n"
        f"作り方: {how}\n"
        f"説明: {SITUATION_HELP[sid]}\n"
        + play_line
        + f"使う部品: {parts}\n"
        + cap
    )


def friendly_select_error(exc: BaseException) -> str | None:
    """Japanese hint for leftover photo prompts / 'no child' false positives."""
    msg = str(exc)
    low = msg.lower()
    if "picture 1" in low or "first_frame" in low:
        return (
            "テキストから作るときは、写真用の文が文章欄に残っています。"
            "欄を空にするとこのシーンのおすすめ文になります。"
        )
    if "forbidden subject" in low:
        return (
            "未成年の表現は作れません。出演者は 21歳以上にしてください。"
            "child / teen / loli や 15 years old / 15歳 は通りません。"
            "空欄にするとおすすめ文を使います。no child のような禁止の意味は大丈夫です。"
        )
    if "stack_plan" in low and "needs an id" in low:
        return (
            "部品の読み込みが古いです。ランタイムを再起動して①→②→③の順、"
            "または②をもう一度実行してから③。"
        )
    return None


def comfy_fail_detail(payload: Any) -> str:
    """Short Comfy execution error. Never dump the full graph."""
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload.strip()[:800]
    if isinstance(payload, (list, tuple)) and payload:
        if str(payload[0]) == "execution_error" and len(payload) > 1 and isinstance(payload[1], dict):
            info = payload[1]
            msg = str(info.get("exception_message") or info.get("exception_type") or "").strip()
            ntype = str(info.get("node_type") or "").strip()
            blob = f"{ntype}: {msg}".strip(": ")
            return (blob or str(payload))[:800]
        return str(payload)[:800]
    if isinstance(payload, dict):
        st = payload.get("status") or {}
        for row in st.get("messages") or []:
            detail = comfy_fail_detail(row)
            if detail:
                return detail
        if st.get("status_str") == "error":
            return str(st.get("messages") or st)[:800]
    return str(payload)[:800]


def format_job_fail(mode: str, payload: Any) -> str:
    """T2V must not tell the user to check an input jpg."""
    detail = comfy_fail_detail(payload)
    if str(mode).lower() == "t2v":
        base = "テキストから作れませんでした。写真は不要です。秒数を 10 にするか、画面を小さくして③をもう一度。"
    else:
        base = "写真から作れませんでした。Drive の input の jpg を確認してください。"
    if detail:
        return f"{base}\n{detail}"
    return base


def civitai_token(form_value: str = "") -> str:
    """Read Civitai API key. Form paste first, then Colab secret, then env. Never print it."""
    pasted = str(form_value or "").strip()
    if pasted:
        return pasted
    for getter in (_colab_userdata_token, lambda: os.environ.get("CIVITAI_API_TOKEN") or ""):
        try:
            raw = getter()
        except Exception:
            raw = ""
        token = str(raw or "").strip()
        if token:
            return token
    return ""


def _colab_userdata_token() -> str:
    from google.colab import userdata  # type: ignore

    return str(userdata.get("CIVITAI_API_TOKEN") or "")


def missing_civitai_files(
    jobs: list[tuple[str, Path, dict[str, Any]]],
    *,
    min_bytes: int = 1_000_000,
) -> list[str]:
    names: list[str] = []
    for _url, dest, row in jobs:
        if str(row.get("source") or "") != "civitai":
            continue
        if dest.is_file() and dest.stat().st_size > min_bytes:
            continue
        names.append(dest.name)
    return names


DOWNLOAD_UA = "Mozilla/5.0 (compatible; h3-lora-studio/1.0)"
# Drive FUSE: reading 16 bytes of a GB file can stream the whole object. Trust size.
SKIP_WITHOUT_HEADER = 5 * 1024 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


_DOWNLOAD_OPENER = urllib.request.build_opener(_NoRedirect)


def civitai_token_help() -> str:
    return (
        "Civitai の API キーが空です。シークレットは使わなくて大丈夫です。\n"
        "1. https://civitai.com/user/account を開く（ログイン）\n"
        "2. 下のほうの API Keys → Add API key → 作った文字列をコピー\n"
        "3. ②セルの「CivitaiのAPIキー」欄に貼る\n"
        "4. ②をもう一度実行\n"
        "キー自体は画面に出しません。ノートを保存・共有する前に欄を空に戻してください。"
    )


def load_catalog(studio_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(studio_root or STUDIO_ROOT)
    path = root / "catalog" / "loras.json"
    return json.loads(path.read_text(encoding="utf-8"))


def catalog_by_id(catalog: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    data = catalog or load_catalog()
    return {str(row["id"]): row for row in data.get("loras") or [] if row.get("id")}


def civitai_download_url(row: dict[str, Any]) -> str:
    version = int(row["civitai_version_id"])
    file_id = int(row["civitai_file_id"])
    return f"https://civitai.com/api/download/models/{version}?fileId={file_id}"


def civitai_download_fallbacks(row: dict[str, Any]) -> list[str]:
    version = int(row["civitai_version_id"])
    primary = civitai_download_url(row)
    typed = f"https://civitai.com/api/download/models/{version}?type=Model&format=SafeTensor"
    bare = f"https://civitai.com/api/download/models/{version}"
    out: list[str] = []
    for url in (primary, typed, bare):
        if url not in out:
            out.append(url)
    return out


def looks_like_safetensors(path: Path, *, min_bytes: int = 1_000_000) -> bool:
    """Reject HTML/JSON error bodies that Civitai sometimes returns as HTTP 200."""
    if not path.is_file() or path.stat().st_size < min_bytes:
        return False
    head = path.read_bytes()[:16]
    if len(head) < 9:
        return False
    header_len = int.from_bytes(head[:8], "little")
    if header_len < 2 or header_len > 100_000_000:
        return False
    return head[8:9] == b"{"


def already_have_weight(path: Path, *, min_bytes: int = 1_000_000) -> bool:
    """Skip without reading GB files from Google Drive."""
    if not path.is_file():
        return False
    size = path.stat().st_size
    if size < min_bytes:
        return False
    if size >= SKIP_WITHOUT_HEADER:
        return True
    return looks_like_safetensors(path, min_bytes=min_bytes)


# Studio T2V/I2V unet. Author default: TURBO-hybrid int8. HF name keeps "turbo" so we can skip Larry/LightX2V.
EROS_HF_REPO = "TenStrip/10Eros-Max"
EROS_FL2VA_NAME = "10Eros_Max_h3_TURBO-hybrid_beta5_int8.safetensors"
EROS_FL2VA_URL = f"https://huggingface.co/{EROS_HF_REPO}/resolve/main/{EROS_FL2VA_NAME}"
OFFICIAL_FL2VA_NAME = "minimax_h3_fl2va_pruned_int8_convrot.safetensors"
BAKED_TURBO_LORA_IDS = frozenset(
    {
        "larry-v4",
        "minimax-h3-turbo-fl2v-4step",
        "minimax-h3-turbo-fl2v-8step",
    }
)


def is_eros_unet(name: str) -> bool:
    """True for H3 Eros Max diffusion UNets. Not Ref2VA. Not LTX 10Eros."""
    n = str(name or "").lower().replace("-", "_")
    if "ref2va" in n or "ref2v" in n or "ltx" in n:
        return False
    if "h3" not in n:
        return False
    return "10eros" in n or "h3erosmax" in n or "eros_max" in n


def is_eros_turbo_hybrid_unet(name: str) -> bool:
    """TURBO-hybrid has distilled turbo baked in. Do not stack Larry / LightX2V FL2VA.

    HF TURBO-hybrid names include ``turbo``. Civitai ``h3ErosMax_beta5_*`` omits it;
    studio default is still TURBO-hybrid. The non-turbo HF sibling is ``..._h3_hybrid_...``.
    """
    n = str(name or "").lower().replace("-", "_")
    if not is_eros_unet(name):
        return False
    if "turbo" in n:
        return True
    if "_hybrid_" in n or n.endswith("_hybrid") or "_hybrid." in n:
        return False
    return True


def is_official_h3_fl2va_name(name: str) -> bool:
    n = str(name or "").lower()
    if not n.endswith(".safetensors") or n.endswith(".part"):
        return False
    if is_eros_unet(name) or is_ref2v_weight(name):
        return False
    return "fl2va" in n


def is_studio_fl2va_unet(name: str) -> bool:
    """Official FL2VA or Eros Max FL-compatible UNet. Name only."""
    n = str(name or "").lower()
    if not n.endswith(".safetensors") or n.endswith(".part"):
        return False
    if is_ref2v_weight(name):
        return False
    return "fl2va" in n or is_eros_unet(name)


def iter_studio_unets(root: Path | str) -> list[Path]:
    folder = Path(root)
    if not folder.is_dir():
        return []
    out: list[Path] = []
    try:
        for path in folder.iterdir():
            if not path.is_file():
                continue
            if is_studio_fl2va_unet(path.name):
                out.append(path)
    except OSError:
        return []
    out.sort(key=lambda p: p.name.lower())
    return out


def pick_studio_unet(root: Path | str, *, default: str = EROS_FL2VA_NAME) -> str:
    """Prefer Eros TURBO-hybrid, then any Eros, then official FL2VA."""
    files = iter_studio_unets(root)
    turbo = [p for p in files if is_eros_turbo_hybrid_unet(p.name)]
    if turbo:
        return turbo[0].name
    eros = [p for p in files if is_eros_unet(p.name)]
    if eros:
        return eros[0].name
    if files:
        return files[0].name
    return str(default or EROS_FL2VA_NAME)


def has_fl2va_weight(root: Path | str) -> bool:
    """True if a studio T2V/I2V UNet sits in this folder. Name only — do not open GB files."""
    return bool(iter_studio_unets(root))


def has_eros_unet(root: Path | str) -> bool:
    """True if an H3 Eros Max UNet is in this folder. Official FL2VA does not count."""
    return any(is_eros_unet(p.name) for p in iter_studio_unets(root))


def studio_colab_dest(rel: str, *, content_root: Path | str = "/content") -> Path:
    """helpers land in /content/*.py. Studio JSON stays under /content/h3-lora-studio/."""
    root = Path(content_root)
    text = str(rel or "").replace("\\", "/").lstrip("/")
    if text.startswith("colab/"):
        return root / Path(text).name
    return root / text


def github_member_rel(name: str) -> str:
    """Strip the GitHub archive's top folder: Research-branch/colab/foo.py → colab/foo.py."""
    text = str(name or "").replace("\\", "/").strip()
    if not text or text.endswith("/"):
        return ""
    if "/" not in text:
        return ""
    return text.split("/", 1)[1]


def unpack_github_archive(
    src: Path | str,
    rels: list[str],
    dest_for_rel,
) -> list[str]:
    """Copy listed paths out of a GitHub branch tarball. Returns rels that were missing."""
    wanted = [str(r).replace("\\", "/") for r in rels]
    wanted_set = set(wanted)
    found: set[str] = set()
    with tarfile.open(src, mode="r:gz") as tar:
        for member in tar:
            if not member.isfile():
                continue
            rel = github_member_rel(member.name)
            if rel not in wanted_set:
                continue
            extracted = tar.extractfile(member)
            if extracted is None:
                continue
            data = extracted.read()
            if len(data) < 20:
                continue
            dest = Path(dest_for_rel(rel))
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            found.add(rel)
    return [r for r in wanted if r not in found]


def fetch_github_files_raw(
    branch: str,
    rels: list[str],
    dest_for_rel,
    *,
    repo: str = "fireworker011/Research",
    workers: int = 8,
) -> list[str]:
    """Threaded raw.githubusercontent.com fallback. Returns still-missing rels."""
    failed: list[str] = []

    def one(rel: str) -> str | None:
        dest = Path(dest_for_rel(rel))
        dest.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/{rel}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "h3-lora-studio",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            dest.write_bytes(resp.read())
        if dest.is_file() and dest.stat().st_size > 20:
            return None
        return rel

    if not rels:
        return []
    pool_n = max(1, min(int(workers), 8))
    with ThreadPoolExecutor(max_workers=pool_n) as pool:
        futs = {pool.submit(one, rel): rel for rel in rels}
        for fut in as_completed(futs):
            rel = futs[fut]
            try:
                miss = fut.result()
            except Exception:
                miss = rel
            if miss:
                failed.append(rel)
                print("ファイル取得に失敗:", rel)
    return failed


def ensure_select_loras_on_path(
    *,
    content_root: Path | str = "/content",
    drive_root: Path | str | None = None,
    branch: str = "",
    repo: str = "fireworker011/Research",
) -> Path:
    """③ imports `select_loras` from /content. Copy from scripts/Drive, or fetch, if ② left it only under scripts/."""
    root = Path(content_root)
    dest = root / "select_loras.py"
    scripts = root / "h3-lora-studio" / "scripts" / "select_loras.py"
    cands = [dest, scripts]
    if drive_root:
        cands.append(Path(drive_root) / "select_loras.py")

    def _ok(path: Path) -> bool:
        try:
            return (
                path.is_file()
                and path.stat().st_size > 20
                and "MAX_HELPERS" in path.read_text(encoding="utf-8")
                and "CONCEPT_LORA_ID" in path.read_text(encoding="utf-8")
            )
        except OSError:
            return False

    src = next((p for p in cands if _ok(p)), None)
    if src is None and str(branch or "").strip():
        miss = fetch_github_files_raw(
            str(branch).strip(),
            ["h3-lora-studio/scripts/select_loras.py"],
            lambda rel: dest if str(rel).endswith("select_loras.py") else root / rel,
            repo=repo,
        )
        if not miss and _ok(dest):
            src = dest
    if src is None or not _ok(src):
        raise SystemExit("部品 select_loras がありません。②をもう一度実行してから③。")
    if src.resolve() != dest.resolve():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    if _ok(dest) and not scripts.is_file():
        scripts.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dest, scripts)
    scripts_dir = str(scripts.parent)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    return dest


def fetch_github_tree(
    branch: str,
    rels: list[str],
    dest_for_rel,
    *,
    repo: str = "fireworker011/Research",
    timeout: int = 180,
) -> list[str]:
    """One GitHub tarball instead of N sequential raw GETs. Falls back to threaded GETs."""
    wanted = [str(r).replace("\\", "/") for r in rels]
    url = f"https://codeload.github.com/{repo}/tar.gz/refs/heads/{branch}"
    tmp = Path("/tmp") / f"h3-studio-{os.getpid()}.tgz"
    missing = list(wanted)
    try:
        print("説明書を一括で取っています…")
        req = urllib.request.Request(url, headers={"User-Agent": "h3-lora-studio"})
        with urllib.request.urlopen(req, timeout=timeout) as resp, open(tmp, "wb") as out:
            shutil.copyfileobj(resp, out, length=1024 * 1024)
        missing = unpack_github_archive(tmp, wanted, dest_for_rel)
    except Exception as exc:
        print("一括取得に失敗。1ファイルずつ取ります:", str(exc)[:160])
        missing = list(wanted)
    finally:
        tmp.unlink(missing_ok=True)
    if not missing:
        print("説明書:", len(wanted), "ファイル")
        return []
    print("残り", len(missing), "ファイルを個別に取ります…")
    return fetch_github_files_raw(branch, missing, dest_for_rel, repo=repo)


HOT_MODEL_SUBS = ("diffusion_models", "text_encoders", "vae", "loras")
ENGINE_MODEL_SUBS = ("diffusion_models", "text_encoders", "vae")
DRIVE_CACHE_SUBS = {
    "HF_HOME": "cache/hf",
    "HUGGINGFACE_HUB_CACHE": "cache/hf/hub",
    "HF_HUB_CACHE": "cache/hf/hub",
    "TRANSFORMERS_CACHE": "cache/hf/transformers",
    "TORCH_HOME": "cache/torch",
    "TORCHINDUCTOR_CACHE_DIR": "cache/torch/inductor",
    "TRITON_CACHE_DIR": "cache/triton",
    "PIP_CACHE_DIR": "cache/pip",
    "XDG_CACHE_HOME": "cache/xdg",
}
WARMUP_STAMP_NAME = ".h3_warmup_ok"
_COPY_CHUNK = 64 * 1024 * 1024


def is_under_drive(path: Path | str) -> bool:
    try:
        text = str(Path(path).resolve()).replace("\\", "/")
    except Exception:
        text = str(path).replace("\\", "/")
    return "/drive/MyDrive/" in text or text.startswith("/content/drive/")


def apply_drive_cache_env(drive_root: Path | str) -> dict[str, str]:
    """Keep pip / HuggingFace / torch / Triton caches on Drive. Do not fill Colab ephemeral disk."""
    root = Path(drive_root)
    applied: dict[str, str] = {}
    for key, rel in DRIVE_CACHE_SUBS.items():
        dest = root / rel
        dest.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(dest)
        applied[key] = str(dest)
    os.environ["CUDA_MODULE_LOADING"] = "EAGER"
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True,garbage_collection_threshold:0.8")
    applied["CUDA_MODULE_LOADING"] = "EAGER"
    return applied


def warmup_stamp_path(comfy_dir: Path | str) -> Path:
    return Path(comfy_dir) / WARMUP_STAMP_NAME


def clear_warmup_stamp(comfy_dir: Path | str) -> None:
    warmup_stamp_path(comfy_dir).unlink(missing_ok=True)


def model_dir_is_drive_link(comfy_dir: Path | str) -> bool:
    """True when Comfy would mmap weights through Google Drive FUSE."""
    probe = Path(comfy_dir) / "models" / "text_encoders"
    if probe.is_symlink():
        return True
    if probe.exists() and is_under_drive(probe):
        return True
    return False


def prepare_local_model_roots(comfy_dir: Path | str) -> bool:
    """Comfy model folders become real local dirs. Returns True if a Drive symlink was removed."""
    changed = False
    models = Path(comfy_dir) / "models"
    models.mkdir(parents=True, exist_ok=True)
    for sub in HOT_MODEL_SUBS:
        dest = models / sub
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
            changed = True
        elif dest.is_dir() and is_under_drive(dest):
            try:
                dest.rmdir()
            except OSError:
                pass
            changed = True
        dest.mkdir(parents=True, exist_ok=True)
    return changed


def is_ref2v_weight(name: str) -> bool:
    n = str(name or "").lower()
    return "ref2va" in n or "ref2v" in n


def _iter_drive_weights(
    drive_models: Path,
    *,
    cores_only: bool = True,
    include_ref2v: bool = False,
    lora_names: list[str] | None = None,
) -> list[tuple[str, Path]]:
    """List Drive weights to copy. Default: FL2VA + text encoder + VAE. Not every LoRA, not Ref2VA."""
    want_loras = {str(n).strip() for n in (lora_names or []) if str(n).strip()}
    if cores_only:
        subs = list(ENGINE_MODEL_SUBS)
        if want_loras:
            subs.append("loras")
    else:
        subs = list(HOT_MODEL_SUBS)
    rows: list[tuple[str, Path]] = []
    for sub in subs:
        folder = drive_models / sub
        if not folder.is_dir():
            continue
        try:
            paths = sorted(folder.iterdir())
        except OSError:
            continue
        for path in paths:
            if path.name.startswith(".") or path.suffix != ".safetensors":
                continue
            if path.name.endswith(".part"):
                continue
            if not path.is_file():
                continue
            if sub == "diffusion_models" and not include_ref2v and is_ref2v_weight(path.name):
                continue
            if (
                sub == "diffusion_models"
                and any(is_eros_unet(p.name) and not is_ref2v_weight(p.name) for p in paths)
                and is_official_h3_fl2va_name(path.name)
            ):
                continue
            if sub == "loras":
                if cores_only and want_loras and path.name not in want_loras:
                    continue
                if not include_ref2v and is_ref2v_weight(path.name):
                    continue
            rows.append((sub, path))
    return rows


def stage_weight_file(src: Path, dest: Path) -> str:
    """Sequential copy Drive → local NVMe. Resume .part. Never Path.read_bytes() on GB files."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not src.is_file():
        return "missing"
    size = src.stat().st_size
    if dest.is_symlink():
        dest.unlink()
    if dest.is_file() and dest.stat().st_size == size and size > 0 and not is_under_drive(dest):
        return "skipped"
    tmp = dest.with_name(dest.name + ".part")
    if (
        dest.is_file()
        and not dest.is_symlink()
        and dest.stat().st_size < size
        and not tmp.is_file()
    ):
        dest.rename(tmp)
    start = 0
    if tmp.is_file():
        start = tmp.stat().st_size
        if start > size:
            tmp.unlink()
            start = 0
        elif start == size and size > 0:
            tmp.replace(dest)
            return "copied"
    mode = "ab" if start else "wb"
    if start:
        print(
            f"ローカルへ続きから: {src.name} ({start / 1e9:.2f}/{size / 1e9:.2f} GB)…",
            flush=True,
        )
    else:
        print(f"ローカルへコピー中: {src.name} ({size / 1e9:.2f} GB)…", flush=True)
    copied = start
    last_print = time.time()
    try:
        with open(src, "rb") as inf, open(tmp, mode) as out:
            if start:
                inf.seek(start)
            while True:
                chunk = inf.read(_COPY_CHUNK)
                if not chunk:
                    break
                out.write(chunk)
                copied += len(chunk)
                now = time.time()
                if size and now - last_print >= 5:
                    pct = 100.0 * copied / size
                    print(
                        f"  {src.name}: {copied / 1e9:.2f}/{size / 1e9:.2f} GB ({pct:.0f}%)",
                        flush=True,
                    )
                    last_print = now
    except OSError as exc:
        print(
            f"コピーが途中で止まりました: {src.name}（{copied / 1e9:.2f} GB まで。"
            f"②か③をもう一度で続きから） {exc}",
            flush=True,
        )
        return "missing"
    if not tmp.is_file() or tmp.stat().st_size != size:
        return "missing"
    tmp.replace(dest)
    return "copied"


def stage_models_to_local(
    drive_models: Path | str,
    local_models: Path | str,
    *,
    min_free_bytes: int = 2 * 1024 ** 3,
    cores_only: bool = True,
    include_ref2v: bool = False,
    lora_names: list[str] | None = None,
) -> dict[str, Any]:
    """Drive stays the durable copy. Copy only the H3 cores by default (not every LoRA, not Ref2VA)."""
    drive_root = Path(drive_models)
    local_root = Path(local_models)
    local_root.mkdir(parents=True, exist_ok=True)
    stats: dict[str, Any] = {
        "copied": [],
        "skipped": [],
        "missing": [],
        "bytes": 0,
        "drive_direct": False,
    }
    pairs: list[tuple[Path, Path, int]] = []
    for sub, src in _iter_drive_weights(
        drive_root,
        cores_only=cores_only,
        include_ref2v=include_ref2v,
        lora_names=lora_names,
    ):
        dest = local_root / sub / src.name
        try:
            size = src.stat().st_size
        except OSError:
            stats["missing"].append(src.name)
            continue
        if (
            dest.is_file()
            and not dest.is_symlink()
            and dest.stat().st_size == size
            and size > 0
            and not is_under_drive(dest)
        ):
            stats["skipped"].append(src.name)
            continue
        pairs.append((src, dest, size))
    pairs.sort(key=lambda row: row[2])
    need = sum(row[2] for row in pairs)
    try:
        free = shutil.disk_usage(str(local_root)).free
    except OSError:
        free = 0
    if pairs and free < need + min_free_bytes:
        stats["drive_direct"] = True
        print(
            "ローカル空きが足りないので Drive 直読みにします。"
            f" 必要 {need / 1e9:.1f} GB / 空き {free / 1e9:.1f} GB"
        )
        return stats
    if pairs:
        print(
            f"ローカルへ {len(pairs)} ファイル {need / 1e9:.1f} GB。"
            "途中で止まっても②をもう一度で続きから。",
            flush=True,
        )
    for src, dest, size in pairs:
        result = stage_weight_file(src, dest)
        if result == "copied":
            stats["copied"].append(src.name)
            stats["bytes"] += size
        elif result == "skipped":
            stats["skipped"].append(src.name)
        else:
            stats["missing"].append(src.name)
    return stats


def link_model_dirs_to_drive(comfy_dir: Path | str, drive_models: Path | str) -> None:
    """Fallback only: mmap through FUSE. Prefer stage_models_to_local."""
    models = Path(comfy_dir) / "models"
    drive = Path(drive_models)
    models.mkdir(parents=True, exist_ok=True)
    for sub in HOT_MODEL_SUBS:
        dest = models / sub
        target = drive / sub
        target.mkdir(parents=True, exist_ok=True)
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        elif dest.is_dir():
            shutil.rmtree(dest)
        dest.symlink_to(target)


def build_studio_warmup_graph(
    unet: str,
    *,
    duration_s: float = 0.2,
    has_audio_decode: bool = True,
) -> dict[str, Any]:
    """1-step tiny T2V. Loads UNET + CLIP + VAE into VRAM so clip 1 is not the cold start."""
    from h3_t2v import CANVAS_9_16_MIN, build_t2v_graph

    g = build_t2v_graph(
        prompt="Vertical 9:16. An adult woman over 21 blinks once. Photoreal. No speech.",
        unet=str(unet),
        lora_name=None,
        lora_strength=0.0,
        width=int(CANVAS_9_16_MIN[0]),
        height=int(CANVAS_9_16_MIN[1]),
        duration_s=float(duration_s),
        seed=1,
        steps=1,
        filename_prefix="video/_h3_warmup",
        has_lora_loader=False,
        has_audio_decode=has_audio_decode,
    )
    if "22" in g:
        g["22"]["inputs"]["sampler_name"] = "euler"
    if "23" in g:
        g["23"]["inputs"]["scheduler"] = "simple"
        g["23"]["inputs"]["steps"] = 1
    return g


def _post_comfy_prompt(port: int, graph: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    body = {"prompt": graph, "client_id": "h3-warmup"}
    req = urllib.request.Request(
        f"http://127.0.0.1:{int(port)}/prompt",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode()), None
    except urllib.error.HTTPError as exc:
        return None, exc.read().decode(errors="replace")[:2000]
    except Exception as exc:
        return None, str(exc)


def _wait_comfy_prompt(port: int, prompt_id: str, *, timeout: float = 900) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{int(port)}/history/{prompt_id}", timeout=60
            ) as resp:
                hist = json.loads(resp.read().decode())
        except Exception:
            time.sleep(2)
            continue
        entry = hist.get(prompt_id) or {}
        st = entry.get("status") or {}
        if st.get("completed") or entry.get("outputs"):
            return st.get("status_str") != "error"
        for msg in st.get("messages") or []:
            if isinstance(msg, list) and msg and msg[0] == "execution_error":
                return False
        time.sleep(2)
    return False


def _delete_warmup_videos(comfy_dir: Path | str) -> None:
    root = Path(comfy_dir) / "output"
    if not root.is_dir():
        return
    for hit in root.rglob("*"):
        if hit.is_file() and "_h3_warmup" in hit.name:
            hit.unlink(missing_ok=True)


def warmup_h3_engine(
    comfy_dir: Path | str,
    port: int,
    unet: str,
    *,
    force: bool = False,
) -> bool:
    """Load the H3 stack onto the GPU during ②. Clip 1 then starts with VRAM already hot."""
    stamp = warmup_stamp_path(comfy_dir)
    if stamp.is_file() and not force:
        print("GPU は準備済み。土台の載せ直しは飛ばします。")
        return True
    if not str(unet or "").strip():
        return False
    print("GPU に土台を載せています（初回だけ。Drive ではなくローカルから）…")
    for duration in (0.2, 4.0):
        graph = build_studio_warmup_graph(unet, duration_s=duration, has_audio_decode=True)
        res, err = _post_comfy_prompt(int(port), graph)
        if err or not res or not res.get("prompt_id"):
            if duration == 4.0:
                print("GPU 事前載せをスキップ:", (err or "no prompt_id")[:200])
                return False
            continue
        if _wait_comfy_prompt(int(port), str(res["prompt_id"])):
            stamp.write_text("ok", encoding="utf-8")
            _delete_warmup_videos(comfy_dir)
            print("GPU 準備完了。③の1本目から本体の計算に入れます。")
            return True
        if duration == 4.0:
            print("GPU 事前載せに失敗。③の1本目で土台を載せます。")
            return False
    return False


def quote_http_url(url: str) -> str:
    """Encode non-ASCII redirect paths. Civitai 400s on Chinese filenames otherwise."""
    parts = urllib.parse.urlsplit(url)
    path = urllib.parse.quote(urllib.parse.unquote(parts.path), safe="/")
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))


def _civitai_host(netloc: str) -> bool:
    host = (netloc or "").lower().split(":")[0]
    return host == "civitai.com" or host.endswith(".civitai.com")


def open_download(url: str, headers: dict[str, str], *, timeout: int = 600):
    current = quote_http_url(url)
    hdrs = dict(headers)
    last_exc: urllib.error.HTTPError | None = None
    for _ in range(8):
        req = urllib.request.Request(current, headers=hdrs)
        try:
            return _DOWNLOAD_OPENER.open(req, timeout=timeout)
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code not in {301, 302, 303, 307, 308}:
                raise
            loc = exc.headers.get("Location") or exc.headers.get("location")
            try:
                exc.read()
            finally:
                exc.close()
            if not loc:
                raise
            current = quote_http_url(urllib.parse.urljoin(current, loc))
            if not _civitai_host(urllib.parse.urlsplit(current).netloc):
                hdrs.pop("Authorization", None)
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("download redirect failed")


def download_jobs_for(
    ids: list[str],
    lora_dir: Path | str,
    *,
    catalog: dict[str, Any] | None = None,
) -> list[tuple[str, Path, dict[str, Any]]]:
    index = catalog_by_id(catalog)
    dest_dir = Path(lora_dir)
    jobs: list[tuple[str, Path, dict[str, Any]]] = []
    seen: set[str] = set()
    for lid in ids:
        if lid in seen:
            continue
        seen.add(lid)
        row = index.get(lid)
        if row is None:
            raise SystemExit(f"unknown LoRA id: {lid}")
        dest = dest_dir / str(row["filename"])
        source = str(row.get("source") or "hf")
        if source == "civitai":
            url = civitai_download_url(row)
        elif row.get("repo") and not str(row["repo"]).startswith("civitai:"):
            url = (
                "https://huggingface.co/"
                + str(row["repo"])
                + "/resolve/main/"
                + str(row.get("file") or row["filename"])
            )
        else:
            continue
        jobs.append((url, dest, row))
    return jobs


def studio_engine_download_jobs(drive_models: Path | str) -> list[tuple[str, Path]]:
    """Studio T2V/I2V: Eros Max UNet + shared text/VAE/turbo LoRA. Not official FL2VA. Not Ref2VA."""
    root = Path(drive_models)
    jobs: list[tuple[str, Path]] = [
        (EROS_FL2VA_URL, root / "diffusion_models" / EROS_FL2VA_NAME),
    ]
    for url, dest in i2v_download_jobs(root):
        if dest.parent.name == "diffusion_models" and is_official_h3_fl2va_name(dest.name):
            continue
        jobs.append((url, dest))
    return jobs


def fetch_weight(
    url: str,
    dest: Path,
    *,
    token: str = "",
    auth: str = "",
    min_bytes: int = 1_000_000,
    fallback_urls: list[str] | None = None,
    strict: bool | None = None,
) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if already_have_weight(dest, min_bytes=min_bytes):
        print(f"skip {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
        return True
    urls = [url]
    for extra in fallback_urls or []:
        if extra and extra not in urls:
            urls.append(extra)
    if auth == "civitai":
        if "fileId=" in url:
            bare = url.split("?", 1)[0]
            if bare not in urls:
                urls.append(bare)
            typed = bare + "?type=Model&format=SafeTensor"
            if typed not in urls:
                urls.append(typed)
    must = True if strict is None else bool(strict)
    if strict is None and auth == "civitai":
        must = False
    tmp = dest.with_name(dest.name + ".part")
    last_code = None
    last_reason = "取得できない"
    for attempt, current in enumerate(urls):
        headers = {"User-Agent": DOWNLOAD_UA}
        if auth == "civitai" and token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            with open_download(current, headers, timeout=600) as resp, open(tmp, "wb") as out:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
            if looks_like_safetensors(tmp, min_bytes=min_bytes):
                last_code = None
                break
            last_reason = "LoRAとして読めない"
            if tmp.exists():
                tmp.unlink()
            if attempt + 1 < len(urls):
                print(f"取得をやり直します: {dest.name}")
                continue
        except urllib.error.HTTPError as exc:
            last_code = exc.code
            last_reason = str(exc.code)
            if tmp.exists():
                tmp.unlink()
            if exc.code in {401, 403} and must:
                raise RuntimeError(
                    f"Civitai が {exc.code} を返した: {dest.name}。\n" + civitai_token_help()
                ) from None
            if attempt + 1 < len(urls) and exc.code in {400, 401, 403, 404}:
                print(f"取得をやり直します: {dest.name}")
                continue
            if must:
                raise RuntimeError(
                    f"DL 失敗 {exc.code}: {dest.name}。"
                    " Drive の models/loras に同じファイル名で置いてから②を再実行しても大丈夫です。"
                ) from None
            break
    if looks_like_safetensors(tmp, min_bytes=min_bytes):
        tmp.replace(dest)
        print(f"saved {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
        return True
    if tmp.exists():
        tmp.unlink()
    extra = f"（{last_code}）" if last_code else f"（{last_reason}）"
    msg = (
        f"DL 失敗{extra}: {dest.name}。"
        " 今のシーンに不要ならこのまま③へ。必要なら Drive の models/loras に置いて②を再実行。"
    )
    if must:
        raise RuntimeError(msg)
    print("スキップ:", msg)
    return False


def resolve_lora_relname(lora_dir: Path | str, filename: str) -> str | None:
    """Return the Comfy lora_name (relative to models/loras) if the weight is on disk."""
    root = Path(lora_dir)
    name = str(filename or "").strip()
    if not name:
        return None
    direct = root / name
    if already_have_weight(direct):
        return name.replace("\\", "/")
    target = Path(name).name.lower()
    if not root.is_dir():
        return None
    for hit in root.rglob("*.safetensors"):
        if hit.name.lower() == target and already_have_weight(hit):
            return str(hit.relative_to(root)).replace("\\", "/")
    return None


def missing_stack_files(stack: list[dict[str, Any]], lora_dir: Path | str) -> list[str]:
    missing: list[str] = []
    for item in stack:
        name = str(item.get("filename") or "")
        if not resolve_lora_relname(lora_dir, name):
            missing.append(name or str(item.get("id") or "?"))
    return missing


def comfy_lora_basenames(obj: dict[str, Any] | None) -> set[str]:
    names: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, str):
            if node.lower().endswith(".safetensors"):
                names.add(Path(node).name.lower())
            return
        if isinstance(node, dict):
            for val in node.values():
                walk(val)
            return
        if isinstance(node, (list, tuple)):
            for val in node:
                walk(val)

    walk((obj or {}).get("LoraLoaderModelOnly") or {})
    return names


def comfy_missing_loras(stack: list[dict[str, Any]], obj: dict[str, Any] | None) -> list[str]:
    known = comfy_lora_basenames(obj)
    if not known:
        return []
    missing: list[str] = []
    for item in stack:
        name = Path(str(item.get("filename") or "")).name
        if name and name.lower() not in known:
            missing.append(name)
    return missing


ACT_FALLBACK_TO_AIO = {
    "anal-penetration-coachbate",
    "cowgirl-position-h3",
    "riding-pose-i2v",
    "doggy-h3",
    "missionary-pov-h3",
}


def apply_stack_fallbacks(
    stack: list[dict[str, Any]],
    lora_dir: Path | str,
    catalog: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    """CoachBate is often Civitai-paid. Pose LoRAs can also be missing. Use AIO so ③ still runs."""
    index = catalog_by_id(catalog)
    out: list[dict[str, Any]] = []
    replaced = False
    for item in stack:
        resolved = resolve_lora_relname(lora_dir, str(item.get("filename") or ""))
        if resolved:
            row = dict(item)
            row["filename"] = resolved
            out.append(row)
            continue
        if str(item.get("id")) not in ACT_FALLBACK_TO_AIO:
            out.append(item)
            continue
        alt = index.get("hmnsfw-aio-v25") or {}
        alt_name = resolve_lora_relname(lora_dir, str(alt.get("filename") or ""))
        if not alt_name:
            out.append(item)
            continue
        replaced = True
        out.append(
            {
                "id": "hmnsfw-aio-v25",
                "role": "act",
                "filename": alt_name,
                "strength_model": 0.75,
                "trigger": str(alt.get("trigger") or ""),
                "turbo": False,
            }
        )
    return out, replaced


def format_prompt_http_fail(err: str, stack: list[dict[str, Any]] | None = None) -> str:
    """HTTP 400 from Comfy. Do not send the user back to ② as the only hint."""
    detail = str(err or "").strip()[:800]
    names = [str(x.get("filename") or "") for x in (stack or []) if x.get("filename")]
    low = detail.lower()
    base = "エンジンがグラフを受け取りませんでした。"
    if any(key in low for key in ("lora", "not in list", "not found", "does not exist", "value not")):
        base += (
            " 部品のファイルがエンジンに見えていません。"
            " Drive の models/loras を確認するか、このセルをもう一度実行します（エンジンを再読み込みします）。"
        )
    if names:
        base += " 使うファイル: " + ", ".join(names) + "。"
    if detail:
        return base + "\n" + detail
    return base


COMFY_OBJECT_INFO_TIMEOUT = 180.0
R2V_NODE = "MiniMaxH3ReferenceToVideo"
STUDIO_OBJECT_INFO_NODES = (
    "MiniMaxH3ImageToVideo",
    "MiniMaxH3TextToVideo",
    R2V_NODE,
    "LoraLoaderModelOnly",
    "VAEDecodeAudio",
)
R2V_NODE_MISSING = (
    "短い参照動画の部品（参照ノード）がエンジンにありません。"
    "②をもう一度実行しても古い動画ソフトはそのままです。"
    "ランタイムを再起動して①→②からやり直してください。"
)
COMFY_UNREADY = (
    "動画エンジンが応答していません。①が終わっているか確認してください。"
    " 前の生成が走っているときは終わるまで待ってから③を再実行。"
    " それでもダメならランタイムを再起動して①→②→③。"
)


def _comfy_url(port: int, path: str) -> str:
    return f"http://127.0.0.1:{int(port)}{path}"


def _http_json(url: str, timeout: float) -> Any:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def comfy_alive(port: int = 8188, timeout: float = 5.0) -> bool:
    """Cheap liveness. Do not use /object_info — that dump can exceed 60s on Colab."""
    for path in ("/system_stats", "/queue"):
        try:
            _http_json(_comfy_url(port, path), timeout)
            return True
        except Exception:
            continue
    return False


def fetch_comfy_node_info(port: int, node_class: str, *, timeout: float = 45.0) -> dict[str, Any]:
    data = _http_json(_comfy_url(port, f"/object_info/{node_class}"), timeout)
    if isinstance(data, dict) and node_class in data:
        return {node_class: data[node_class]}
    if isinstance(data, dict) and "input" in data:
        return {node_class: data}
    return {}


def comfy_has_node(port: int, node_class: str, *, timeout: float = 45.0) -> bool:
    try:
        return node_class in fetch_comfy_node_info(port, node_class, timeout=timeout)
    except Exception:
        return False


def comfy_has_h3(port: int = 8188) -> bool:
    return comfy_has_node(port, "MiniMaxH3ImageToVideo")


def comfy_has_r2v(port: int = 8188) -> bool:
    return comfy_has_node(port, R2V_NODE)


def wait_comfy_ready(port: int = 8188, *, seconds: float = 180.0) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if comfy_alive(port) and comfy_has_h3(port):
            return True
        time.sleep(2)
    return False


def fetch_comfy_object_info(port: int = 8188, *, timeout: float = COMFY_OBJECT_INFO_TIMEOUT) -> dict[str, Any]:
    """Prefer per-node /object_info/{class}. Full dump is last resort (slow on Colab)."""
    if not comfy_alive(port) and not wait_comfy_ready(port, seconds=30):
        raise SystemExit(COMFY_UNREADY)
    merged: dict[str, Any] = {}
    for name in STUDIO_OBJECT_INFO_NODES:
        try:
            merged.update(fetch_comfy_node_info(port, name, timeout=45))
        except Exception:
            continue
    # I2V があっても R2V を問い合わせ済み。短編集は R2V 必須なので一覧に含める。
    if "MiniMaxH3ImageToVideo" in merged:
        return merged
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            print("エンジンの部品表を読んでいます…" if attempt == 0 else "部品表が重いので再試行します…")
            data = _http_json(_comfy_url(port, "/object_info"), timeout)
            if isinstance(data, dict) and data:
                return data
        except Exception as exc:
            last_err = exc
            time.sleep(4)
    raise SystemExit(
        "エンジンの部品表が時間内に返りませんでした。"
        " 前の生成が終わるまで待って③を再実行するか、ランタイムを再起動して①から。"
        + (f"\n{last_err}" if last_err else "")
    )


def ensure_comfy_r2v_node(
    comfy_dir: Path | str,
    *,
    port: int = 8188,
    update: bool = True,
) -> bool:
    """True if MiniMaxH3ReferenceToVideo is registered. Pull ComfyUI once if missing.

    update=False skips git fetch/restart (②の設定だけ更新)。短編集はフル②が必要。
    """
    if comfy_has_r2v(port):
        return True
    if not update:
        return False
    root = Path(comfy_dir)
    if not (root / "main.py").is_file():
        return False
    print("参照用の部品が動画ソフトに無いので、ソフトを更新します…")
    fetch = subprocess.run(
        ["git", "-C", str(root), "fetch", "--depth", "1", "origin"],
        check=False,
        capture_output=True,
        text=True,
    )
    if fetch.returncode != 0:
        print("動画ソフトの更新に失敗しました。")
        return comfy_has_r2v(port)
    subprocess.run(
        ["git", "-C", str(root), "reset", "--hard", "FETCH_HEAD"],
        check=False,
    )
    restart_studio_comfy(root, port=port)
    if not wait_comfy_ready(port, seconds=180):
        return False
    return comfy_has_r2v(port)


def ensure_r2v_in_object_info(
    obj: dict[str, Any],
    port: int,
    *,
    comfy_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Probe R2V even if the I2V-only object_info cache skipped it."""
    merged = dict(obj or {})
    if R2V_NODE in merged:
        return merged
    try:
        merged.update(fetch_comfy_node_info(port, R2V_NODE))
    except Exception:
        pass
    if R2V_NODE in merged:
        return merged
    if comfy_dir is None:
        return merged
    print("参照ノードが見えないので、動画ソフトを更新して再読み込みします…")
    if not ensure_comfy_r2v_node(comfy_dir, port=port):
        return merged
    try:
        merged.update(fetch_comfy_node_info(port, R2V_NODE))
    except Exception:
        pass
    return merged


def restart_studio_comfy(comfy_dir: Path | str, *, port: int = 8188) -> None:
    """New LoRAs are invisible until Comfy restarts."""
    clear_warmup_stamp(comfy_dir)
    subprocess.run(["fuser", "-k", f"{port}/tcp"], check=False, capture_output=True)
    time.sleep(2)
    log = Path("/content/comfyui.log")
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        log = Path(comfy_dir) / "comfyui.log"
        log.parent.mkdir(parents=True, exist_ok=True)
    log_f = open(log, "a", buffering=1)
    cmd = [
        sys.executable,
        "main.py",
        "--listen",
        "127.0.0.1",
        "--port",
        str(port),
        "--highvram",
        "--reserve-vram",
        "2",
        "--disable-auto-launch",
        "--enable-cors-header",
    ]
    subprocess.Popen(
        cmd,
        cwd=str(comfy_dir),
        stdout=log_f,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    if not wait_comfy_ready(port, seconds=180):
        raise SystemExit("エンジンの再起動に失敗しました。ランタイムを再起動して①から実行してください。")


def comfy_free(port: int = 8188) -> None:
    """Unload models after OOM or UNET switch (FL2VA↔Ref2VA). Not on LoRA stack change."""
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{int(port)}/free",
            data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=60).read()
        print("VRAM を解放しました")
        time.sleep(3)
    except Exception as exc:
        print("/free skip:", exc)


def inject_lora_stack(
    g: dict[str, Any],
    stack: list[dict[str, Any]],
    *,
    steps: int | None = None,
    sampler: dict[str, Any] | None = None,
    unet_node: str = "1",
) -> dict[str, Any]:
    """Chain LoraLoaderModelOnly. Sampler comes from the situation plan."""
    if g.get("2", {}).get("class_type") == "LoraLoaderModelOnly":
        del g["2"]
    prev = unet_node
    last = unet_node
    for i, item in enumerate(stack, start=1):
        name = str(item.get("filename") or item.get("lora_name") or "")
        if not name:
            raise ValueError("stack item needs filename")
        nid = str(200 + i)
        g[nid] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": [prev, 0],
                "lora_name": name,
                "strength_model": float(item.get("strength_model", item.get("strength", 1.0))),
            },
        }
        prev = nid
        last = nid
    model = [last, 0] if stack else [unet_node, 0]
    plan = sampler or {
        "sampler_name": "res_multistep",
        "scheduler": "beta",
        "steps": max(int(steps or 16), 16),
    }
    if "22" in g:
        g["22"]["inputs"]["sampler_name"] = str(plan.get("sampler_name") or "res_multistep")
    if "23" in g:
        g["23"]["inputs"]["model"] = model
        g["23"]["inputs"]["scheduler"] = str(plan.get("scheduler") or "beta")
        g["23"]["inputs"]["steps"] = int(plan.get("steps") or steps or 16)
    if "24" in g:
        g["24"]["inputs"]["model"] = model
    return g


def merge_optional(
    stack: list[dict[str, Any]],
    *,
    extras: list[str],
    catalog: dict[str, Any] | None = None,
    mode: str = "t2v",
) -> list[dict[str, Any]]:
    """Extras stay off. Two futa helpers are on the profile, not via extras."""
    del catalog, mode
    if extras:
        print("上級の追加部品は無視します。ふたなりの竿と穴はシーン側で既に併用しています。")
    return list(stack)


def situation_ids(situation: str) -> list[str]:
    if situation not in SITUATION_DOWNLOAD:
        raise SystemExit(f"unknown situation: {situation}")
    return list(SITUATION_DOWNLOAD[situation])


BLANK_PROMPTS = {"", "（シーン）", "(シーン)", "シーン", "scene", "auto", "おすすめ"}
I2V_CUSTOM_LOCK = (
    "For the target video, at 0.00 seconds into the target video, "
    "<Picture 1> (from [Shot 1]) is fully referenced.\n\n"
    "subject_definitions:\n"
    "<Subject 1> Adult, clearly over 21, same face body and hair as <Picture 1>.\n\n"
)


def is_blank_prompt(text: str | None) -> bool:
    return str(text or "").strip() in BLANK_PROMPTS


CHAIN_CONTINUE_LINE = (
    "Continue from this exact last frame as <Picture 1>. "
    "Do not restart the scene. Keep identity, clothes, lighting, room, and camera. "
    "Same people, same pose family, same place. No teleport, no new people, no new room. "
    "Natural ongoing motion from this last frame. No freeze frame, no jump cut, no hard cut."
)
CHAIN_OPENING_LINE = (
    "This is the opening of one continuous long take. "
    "Same room, same people, same clothes, same lighting, same camera. "
    "End this clip mid-motion in this exact place. "
    "Do not finish the scene, freeze, fade out, or walk out of frame. "
    "Later clips continue from this last frame with no cut."
)
CHAIN_EXTRA_LINE = (
    "From this exact last frame, without a cut, continue into the next beat. "
    "Same people, same clothes, same room, same camera. Do not teleport or add new people."
)
_CHAIN_META_TAKE_LINE_RE = re.compile(
    r"^New \d+-second take\.?\s*(?:Hard cut\.?\s*)?(?:Do not copy the previous clip\.?\s*)?$",
    re.I,
)
_CHAIN_CLIP_INDEX_RE = re.compile(r"^Clip \d+ of \d+\.\s*")
_CHAIN_NEW_TAKE_RE = re.compile(r"(?i)New \d+-second take\.?\s*")
_CHAIN_HARD_CUT_RE = re.compile(r"(?i)(?<!no )Hard cut\.?\s*")
_CHAIN_NO_COPY_RE = re.compile(r"(?i)Do not copy the previous clip\.?\s*")
_CHAIN_TRIGGER_LINE_RE = re.compile(
    r"^[A-Za-z][A-Za-z0-9_\-+]*(?:\s*,\s*[A-Za-z][A-Za-z0-9_\-+]*)*\s*$"
)


def strip_chain_restart_language(text: str) -> str:
    """Drop hard-cut / new-take editor lines so last-frame I2V can actually join."""
    raw = str(text or "")
    if not raw.strip():
        return ""
    out_lines: list[str] = []
    for line in raw.split("\n"):
        stripped = line.strip()
        if not stripped:
            if out_lines and out_lines[-1] != "":
                out_lines.append("")
            continue
        if _CHAIN_META_TAKE_LINE_RE.match(stripped):
            continue
        if re.match(r"(?i)^(?:hard cut|do not copy the previous clip)\.?$", stripped):
            continue
        cleaned = _CHAIN_CLIP_INDEX_RE.sub("", stripped).strip()
        cleaned = _CHAIN_NEW_TAKE_RE.sub("", cleaned)
        cleaned = _CHAIN_HARD_CUT_RE.sub("", cleaned)
        cleaned = _CHAIN_NO_COPY_RE.sub("", cleaned)
        cleaned = re.sub(r"[ \t]{2,}", " ", cleaned).strip()
        if cleaned:
            out_lines.append(cleaned)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out_lines)).strip()


def split_leading_trigger_line(text: str) -> tuple[str, str]:
    """Keep LoRA trigger tokens (PENISLORA, DY) on the first line."""
    raw = str(text or "")
    if "\n" not in raw:
        head = raw.strip()
        if head and len(head) <= 120 and _CHAIN_TRIGGER_LINE_RE.match(head):
            return head, ""
        return "", raw
    first, rest = raw.split("\n", 1)
    head = first.strip()
    if head and len(head) <= 120 and _CHAIN_TRIGGER_LINE_RE.match(head):
        return head, rest.lstrip("\n")
    return "", raw


def rewrite_chain_opening_prompt(prompt: str) -> str:
    """Clip 1 of a last-frame chain: one long take, end mid-motion, do not hard-cut."""
    text = strip_chain_restart_language(prompt)
    if not text:
        text = "Continue the same live scene."
    if CHAIN_OPENING_LINE in text:
        return text
    prefix, body = split_leading_trigger_line(text)
    body = body.strip()
    if prefix:
        if not body:
            return prefix + "\n" + CHAIN_OPENING_LINE
        return prefix + "\n" + CHAIN_OPENING_LINE + "\n\n" + body
    return CHAIN_OPENING_LINE + "\n\n" + text


def rewrite_chain_extra_prompt(prompt: str) -> str:
    """User extras are the next beat of the same take, not a new shot."""
    body = strip_chain_restart_language(prompt).strip()
    if not body:
        return ""
    if CHAIN_EXTRA_LINE in body:
        return body
    return CHAIN_EXTRA_LINE + " " + body


def next_chain_prompt(
    clip_index: int,
    *,
    first_prompt: str,
    prev_prompt: str,
    extras: list[str] | None = None,
) -> str:
    """Clip 0 uses first_prompt. Later clips use extras[n-1] if filled, else continue prev."""
    idx = int(clip_index)
    first = str(first_prompt or "")
    if idx <= 0:
        return first
    rows = [str(x or "") for x in (extras or [])]
    extra = rows[idx - 1] if idx - 1 < len(rows) else ""
    extra = strip_chain_restart_language(extra)
    if is_blank_prompt(extra):
        return continue_chain_prompt(prev_prompt or first)
    body = continue_chain_prompt(rewrite_chain_extra_prompt(extra.strip()))
    low_first = first.lower()
    if "feminine_lock:" in low_first and "feminine_lock:" not in body.lower():
        mark = low_first.find("feminine_lock:")
        body = body.rstrip() + "\n\n" + first[mark:].strip()
    return body


CHAIN_MIN_S = 16
CHAIN_MAX_S = 120
CHAIN_PRESETS = {
    "つなぐ 20秒": 20.0,
    "つなぐ 30秒": 30.0,
    "つなぐ 40秒": 40.0,
    "つなぐ 50秒": 50.0,
    "つなぐ 60秒": 60.0,
    "つなぐ 70秒": 70.0,
    "つなぐ 80秒": 80.0,
    "つなぐ 90秒": 90.0,
    "つなぐ 100秒": 100.0,
    "つなぐ 110秒": 110.0,
    "つなぐ 120秒": 120.0,
    "つなぐ 2分": 120.0,
}


def clamp_studio_duration(seconds: float, *, chain: bool = False) -> float:
    """One shot is 4–10s. Chain mode is 16–120s via 10s clips. Homage notebooks stay as they are."""
    try:
        n = int(round(float(seconds)))
    except (TypeError, ValueError):
        return 16.0 if chain else 10.0
    if chain:
        if n > CHAIN_MAX_S:
            return float(CHAIN_MAX_S)
        if n < CHAIN_MIN_S:
            return float(CHAIN_MIN_S)
        return float(n)
    if n > 10:
        return 10.0
    if n < 4:
        return 4.0
    return float(n)


def resolve_length_mode(label: str | bool) -> bool:
    key = str(label or "").strip()
    if key in CHAIN_PRESETS:
        return True
    return key.lower() in {
        "つなぐ（16〜90秒）",
        "つなぐ（秒数欄・16〜90）",
        "つなぐ（16〜120秒）",
        "つなぐ（秒数欄・16〜120）",
        "つなぐ（16〜60秒）",
        "つなぐ",
        "chain",
        "true",
        "1",
    }


def chain_preset_seconds(label: str | bool) -> float | None:
    key = str(label or "").strip()
    return CHAIN_PRESETS.get(key)


def studio_clip_plan(total_s: float, *, chain: bool = False) -> list[float]:
    """Native H3 clips. Do not generate 11s+ in one MiniMaxH3ImageToVideo pass (15s OOMs and shrinks the canvas)."""
    total = clamp_studio_duration(total_s, chain=chain)
    if not chain:
        return [total]
    clips: list[float] = []
    left = int(total)
    while left > 10:
        clips.append(10.0)
        left -= 10
    if left >= 4:
        clips.append(float(left))
    elif left > 0 and clips:
        need = 4 - left
        clips[-1] = float(max(4, int(clips[-1]) - need))
        clips.append(4.0)
    elif not clips:
        clips.append(10.0)
    return clips


def resolve_studio_length(seconds: float, length_mode: str | bool) -> tuple[float, list[float], bool]:
    chain = resolve_length_mode(length_mode)
    preset = chain_preset_seconds(length_mode)
    total = clamp_studio_duration(preset if preset is not None else seconds, chain=chain)
    clips = studio_clip_plan(total, chain=chain)
    return total, clips, chain


def continue_chain_prompt(prompt: str) -> str:
    """Clip 2+ uses the previous last frame as Picture 1. Same scene, no restart."""
    text = strip_chain_restart_language(prompt)
    if CHAIN_CONTINUE_LINE in text:
        if "Picture 1" in text:
            return text
        wrapped, _ = apply_user_prompt(text, mode="i2v", default_prompt=text)
        return wrapped
    if not text:
        text = "Continue the same live scene."
    if "Picture 1" in text:
        return CHAIN_CONTINUE_LINE + "\n\n" + text
    structured = (
        "integrated_multimodal_description:" in text.lower()
        or "subject_definitions:" in text.lower()
    )
    if structured:
        header = (
            "For the target video, at 0.00 seconds into the target video, "
            "<Picture 1> (from [Shot 1]) is fully referenced.\n\n"
        )
        return CHAIN_CONTINUE_LINE + "\n\n" + header + text
    wrapped, _ = apply_user_prompt(
        text,
        mode="i2v",
        default_prompt=text,
    )
    return CHAIN_CONTINUE_LINE + "\n\n" + wrapped


def extract_last_frame(video: Path | str, dest: Path | str) -> Path:
    """Last decoded PNG of a clip. Next I2V first_frame. No JPEG recompress."""
    src = Path(video)
    out = Path(dest)
    out.parent.mkdir(parents=True, exist_ok=True)
    ff = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
    if not src.is_file():
        raise SystemExit("つなぐ用のクリップがありません。")
    for seek in (["-sseof", "-0.05"], ["-sseof", "-1"]):
        if out.is_file():
            out.unlink()
        cmd = [ff, "-y", *seek, "-i", str(src), "-frames:v", "1", "-update", "1", str(out)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0 and out.is_file() and out.stat().st_size >= 100:
            return out
    raise SystemExit("最後のフレームを取れませんでした。秒数を 15 以下の1本にしてください。")


def concat_studio_clips(clips: list[Path], dest: Path | str) -> Path:
    """Join native clips. Prefer stream copy so H3 frames are not re-encoded."""
    out = Path(dest)
    out.parent.mkdir(parents=True, exist_ok=True)
    if not clips:
        raise SystemExit("つなぐクリップが空です。")
    if len(clips) == 1:
        if Path(clips[0]).resolve() != out.resolve():
            out.write_bytes(Path(clips[0]).read_bytes())
        return out
    ff = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
    lst = out.with_suffix(".concat.txt")
    lines = []
    for clip in clips:
        path = Path(clip).resolve()
        if not path.is_file():
            raise SystemExit("つなぐクリップが欠けています: " + path.name)
        lines.append("file '" + str(path).replace("'", "'\\''") + "'")
    lst.write_text("\n".join(lines) + "\n", encoding="utf-8")
    copy = subprocess.run(
        [ff, "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)],
        capture_output=True,
        text=True,
    )
    if copy.returncode == 0 and out.is_file() and out.stat().st_size > 1000:
        lst.unlink(missing_ok=True)
        return out
    enc_base = [ff, "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-pix_fmt", "yuv420p"]
    enc = subprocess.run(enc_base + ["-c:a", "aac", "-b:a", "192k", str(out)], capture_output=True, text=True)
    if enc.returncode != 0 or not out.is_file() or out.stat().st_size < 1000:
        enc = subprocess.run(enc_base + ["-an", str(out)], capture_output=True, text=True)
    lst.unlink(missing_ok=True)
    if enc.returncode != 0 or not out.is_file() or out.stat().st_size < 1000:
        raise SystemExit("クリップの結合に失敗しました。")
    return out


def has_i2v_lock(text: str | None) -> bool:
    raw = str(text or "")
    return "Picture 1" in raw or "first_frame" in raw.lower()


def t2v_user_text(user_text: str | None) -> str:
    """T2V ignores leftover I2V photo locks. Empty means the situation default."""
    raw = str(user_text or "").strip()
    if is_blank_prompt(raw) or has_i2v_lock(raw):
        return ""
    return raw


def apply_user_prompt(user_text: str | None, *, mode: str, default_prompt: str = "") -> tuple[str, bool]:
    """Empty → default scene. Custom I2V gets a Picture 1 lock if the user omitted it.

    T2V after I2V: leftover Picture 1 / first_frame text is dropped so switching
    作り方 does not error. The selected scene's T2V prompt is used instead.
    """
    mode_key = str(mode).lower()
    raw = t2v_user_text(user_text) if mode_key == "t2v" else str(user_text or "").strip()
    if is_blank_prompt(raw):
        return str(default_prompt or ""), False
    if mode_key == "i2v" and "Picture 1" not in raw:
        wrapped = (
            I2V_CUSTOM_LOCK
            + "integrated_multimodal_description: "
            + raw
            + " Identity of (S1) stays locked to <Picture 1>. Photoreal. No freeze frame.\n"
            "overall_soundscape: Natural ambient sound.\n"
            "All performers are consenting adults 21 years or older."
        )
        return wrapped, True
    return raw, True


def has_trigger_word(prompt: str, trigger: str) -> bool:
    """Whole-token match. 'DY' inside 'body' or 'bodies' does not count."""
    trig = str(trigger or "").strip()
    if not trig:
        return True
    pattern = r"(?<![A-Za-z0-9_])" + re.escape(trig) + r"(?![A-Za-z0-9_])"
    return re.search(pattern, str(prompt or ""), re.I) is not None


def prepend_triggers(prompt: str, stack: list[dict[str, Any]]) -> str:
    triggers = []
    for item in stack:
        trig = str(item.get("trigger") or "").strip()
        if trig and not has_trigger_word(prompt, trig) and trig not in triggers:
            triggers.append(trig)
    if not triggers:
        return prompt
    return ", ".join(triggers) + "\n" + prompt


def assert_no_secret_text(text: str) -> None:
    blob = text.lower()
    if "civitai_api_token=" in blob or "xai_api_key=" in blob:
        raise SystemExit("refusing to print API keys")


def studio_sys_path(studio_root: Path | str | None = None) -> None:
    root = Path(studio_root or STUDIO_ROOT)
    scripts = root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))


def stories_dir(studio_root: Path | str | None = None) -> Path:
    return Path(studio_root or STUDIO_ROOT) / "stories"


def lock_i2v_story_prompt(text: str, *, continue_from_last: bool) -> str:
    """Keep story structure. Do not wrap the whole block as one integrated_multimodal_description."""
    raw = str(text or "").strip()
    if continue_from_last:
        return continue_chain_prompt(raw)
    if "Picture 1" in raw:
        return raw
    header = (
        "For the target video, at 0.00 seconds into the target video, "
        "<Picture 1> (from [Shot 1]) is fully referenced.\n\n"
    )
    return header + raw


I2V_PICTURE1_HEADER = (
    "For the target video, at 0.00 seconds into the target video, "
    "<Picture 1> (from [Shot 1]) is fully referenced.\n\n"
)
FINAL_SCENE_LINE = (
    "This is the last clip. Continue from <Picture 1> without a cut, "
    "then bring this scene to its ending inside this clip: finish the action, settle, "
    "and hold the final composition. Same people, same clothes, same place, same camera. "
    "No new people, no new room, no restart."
)
FINAL_SCENE_TARGET_LINE = "Within this clip the scene arrives at:"
DEDICATED_SCENE_IMAGE_LINE = (
    "<Picture 1> is this clip's own still. This clip is its own cut. "
    "Do not continue from a previous last frame. "
    "Start from this still and play only this clip's action in this place."
)


def rewrite_final_scene_i2v_prompt(prompt: str, scene_prompt: str = "") -> str:
    """③合わせ for the LAST clip of a last-frame chain (never the first T2V→I2V join).

    The clip still starts from the previous last frame (Picture 1 lock via
    continue_chain_prompt). scene_prompt, when given, is the ③ scene the clip
    should land in; the LoRA stack for it is inferred by the caller.
    """
    body = strip_chain_restart_language(prompt)
    if FINAL_SCENE_LINE in body:
        return body if "Picture 1" in body else continue_chain_prompt(body)
    target = strip_chain_restart_language(scene_prompt)
    if target:
        target = re.sub(
            r"For the target video, at 0\.00 seconds into the target video,\s*<Picture 1> \(from \[Shot 1\]\) is fully referenced\.\s*",
            "",
            target,
        ).strip()
    prefix, rest = split_leading_trigger_line(body)
    rest = rest.strip()
    joined = I2V_PICTURE1_HEADER + FINAL_SCENE_LINE
    if rest:
        joined += "\n\n" + rest
    if target:
        joined += "\n\n" + FINAL_SCENE_TARGET_LINE + "\n" + target
    out = continue_chain_prompt(joined)
    if prefix:
        return prefix + "\n" + out
    return out


def rewrite_dedicated_scene_i2v_prompt(prompt: str) -> str:
    """③合わせ for a dedicated (cut) story clip that starts from its own still.

    Only the Picture 1 lock plus DEDICATED_SCENE_IMAGE_LINE are added. The JSON
    text and its LoRA stay. Never used on last-frame clips.
    """
    raw = str(prompt or "").strip()
    if DEDICATED_SCENE_IMAGE_LINE in raw:
        return raw
    if "Picture 1" in raw:
        if raw.startswith(I2V_PICTURE1_HEADER.strip()):
            head, _, tail = raw.partition("\n\n")
            return head + "\n\n" + DEDICATED_SCENE_IMAGE_LINE + "\n\n" + tail.lstrip("\n")
        return DEDICATED_SCENE_IMAGE_LINE + "\n\n" + raw
    prefix, body = split_leading_trigger_line(raw)
    text = I2V_PICTURE1_HEADER + DEDICATED_SCENE_IMAGE_LINE + "\n\n" + body.strip()
    return (prefix + "\n" + text) if prefix else text


def should_fit_scene_image_prompt(
    *,
    fit: bool,
    mode: str,
    clip_index: int,
    clip_count: int,
    is_story: bool = False,
    chain: bool = False,
    seamless: bool = False,
    rewrite_chain_prompts: bool = True,
) -> bool:
    """Which clip may be rewritten toward the ③ scene / its still.

    ① The first T2V→I2V join (chain, clip_index == 1) is never touched.
    ② Dedicated stories: only still-based I2V clips (prepare_story_clip decides by still).
    ③ Chains: the last clip only. chain-raw stories (rewrite off) never.
    """
    if not fit:
        return False
    if str(mode or "").lower() != "i2v":
        return False
    idx = int(clip_index)
    last = int(clip_count) - 1
    if is_story:
        if not seamless:
            return True
        if not rewrite_chain_prompts:
            return False
        return idx == last and idx > 0
    if chain:
        if idx == 1:
            return False
        return idx == last and idx > 0
    return True


def story_canvas_wh(story: dict[str, Any], clip: dict[str, Any] | None = None) -> tuple[int, int]:
    """Clip canvas wins when present so shorts can mix 9:16 oral and 16:9 sex."""
    for src in (clip, story):
        if not isinstance(src, dict):
            continue
        canvas = src.get("canvas") if isinstance(src.get("canvas"), dict) else {}
        w = int(canvas.get("width") or 0)
        h = int(canvas.get("height") or 0)
        if w >= 32 and h >= 32:
            return w, h
        aspect = str(canvas.get("aspect") or "").replace("：", ":")
        if aspect in {"16:9", "16/9"}:
            return STORY_CANVAS_16_9
        if aspect in {"9:16", "9/16"}:
            return STORY_CANVAS
    return STORY_CANVAS


ACT_SITUATIONS = frozenset({
    "oral",
    "oral_creampie",
    "cunnilingus_futa",
    "futa_sex",
    "futa_anal",
    "futa_masturbation",
    "futa_blowjob",
    "riding",
    "doggy",
    "missionary_pov",
    "creampie",
    "facial",
    "after_ejaculation",
    "fingering",
    "masturbation",
    "urine_drink",
    "urine_pee",
    "scat_act",
    "anal_penetration",
})


STORY_CANON_KEYS = (
    "subject_definitions",
    "environment",
    "integrated_multimodal_description",
    "overall_soundscape",
    "non_diegetic_music",
)
_STORY_SECTION_RE = re.compile(
    r"^(subject_definitions|environment|integrated_multimodal_description|"
    r"overall_soundscape|non_diegetic_music|WHO|HARD LOCK):\s*(.*)$"
)
_ABSENT_WHO_RE = re.compile(r"^([A-Z][a-z]+) = (?:NOT IN FRAME|NOT IN THIS STORY|OFF SCREEN)\b")
_ABSENT_DEF_RE = re.compile(r"^([A-Z][a-z]+):\s.*\bNOT IN THIS CLIP\.?\s*$")
_META_TAKE_RE = re.compile(r"^New \d+-second take\. Hard cut\. Do not copy the previous clip\.\s*$")
_CLIP_INDEX_RE = re.compile(r"^Clip \d+ of \d+\.\s*")
_CAST_STORIES_RE = re.compile(r"Same faces and bodies as the [^.]*stories\.")
CAST_LOCK_SERIES_LINE = "Same faces, hair and bodies in every clip of this series."
HMMOTION_SITUATIONS = frozenset({"futa_sex"})
STORY_CAST_NAMES = (
    "Sayaka", "Rei", "Aya", "Madoka",
    "Saleswoman", "Doctor", "Conductor",
    "Clerk", "Seller", "Instructor", "Professor",
)
STORY_CAST_DEF_RE = re.compile(r"^(" + "|".join(STORY_CAST_NAMES) + r"): Adult", re.M)
_KANJI_RE = re.compile(r"[\u4e00-\u9fff]")
_SPOKEN_RE = re.compile(r"「([^」]+)」")
_LATIN_IN_SPEECH_RE = re.compile(r"[A-Za-z\u0400-\u04FF\uac00-\ud7af]")
_JP_SCRIPT_RE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")
SPEECH_FACE_KILLER_IDS = frozenset({"cinema-dy"})
# Kept so old notebooks / cached prompts can still be stripped. Do not inject a
# new lock: H3 TTS'd both the JP 音声ルール and the ASCII "only say the line" flags.
AUDIO_LOCK_MARK = "[AUDIO-LOCK]"
_AUDIO_LOCK_LINE_RE = re.compile(r"(?:【音声ルール】|\[AUDIO-LOCK\])[^\n]*\n?")
_OLD_JP_AUDIO_LOCK_RE = re.compile(
    r"プロンプトは読まない。.*?(?:口は閉じて部屋の音だけ。|意味のわからない音は禁止。)"
)
_JP_SPEECH_ONLY_RE = re.compile(
    r"声に出していいのは日本語の台詞だけ。[^\n]*|"
    r"英語を音読しない。[^\n]*|"
    r"台詞のあとに言葉を足さない。[^\n]*|"
    r"余った秒数は無音。[^\n]*"
)
_NEXT_AFTER_SOUND_RE = re.compile(r"\n(?:non_diegetic_music|feminine_lock)\s*:")
_SOUND_SPEAKER_RE = re.compile(
    r"(?:(?:The|A|An)\s+)?[A-Z][\w'-]+\s+(?:speaks|answers),?\s*lip[- ]synced:\s*",
    re.I,
)
_SOUND_LIPSYNC_RE = re.compile(r"\blip[- ]synced:\s*", re.I)
_SOUND_THEN_QUOTE_RE = re.compile(r"」\s*then\s*「")
_SOUND_META_RES = (
    re.compile(r"\s*No other speech\.?", re.I),
    re.compile(r"\s*No spoken words\.?", re.I),
    re.compile(r"\s*No speech from the four\.?", re.I),
    re.compile(r"\s*\bNo speech\.?", re.I),
    re.compile(r"\bHigh adult (?:fe)?male voices only\.?", re.I),
    re.compile(r"\bone close high adult (?:fe)?male line,?\s*", re.I),
    re.compile(
        r"(?:^|[.,]\s*)Close high adult (?:fe)?male voices?\.?",
        re.I,
    ),
)
_SOUND_VOICE_META_RE = re.compile(
    r"(?:,\s*)?(?:under\s+)?(?:(?:a|one|two)\s+)?(?:close\s+)?(?:high\s+)?"
    r"adult\s+(?:fe)?male\s+(?:voice|voices|line)s?\b[,.]?",
    re.I,
)
_SOUND_THEN_ONLY_RE = re.compile(r"\bthen only\b[^.]*\.?", re.I)
# Default futanari = 玉なし＋マンコあり (the futa-blowjob still). Keep in sync with select_loras.lock_futa_anatomy.
FUTA_SCENE_ANATOMY = (
    "futanari: erect penis, hairless female pussy at the base of the shaft, "
    "no testicles, no scrotum. Penis plus vagina, never balls"
)
_FUTA_ANATOMY_TAIL = (
    "no testicles, no scrotum. Hairless female pussy at the base of the shaft "
    "where a scrotum would be. Penis plus vagina, never balls."
)
FUTA_ANATOMY_MARK = "FUTA ANATOMY:"
FUTA_ANATOMY_LOCK_LINE = (
    "FUTA ANATOMY: Every futanari is penis plus vagina, never balls. "
    "Erect penis, hairless female pussy at the base of the shaft where a scrotum would be. "
    "NO testicles. NO scrotum. Do not grow balls. "
    "Women marked NEVER futanari stay NO penis."
)
_NEVER_FUTA_RE = re.compile(r"(?i)never\s+futanari")
_FUTA_WORD_RE = re.compile(r"ふたなり|フタナリ|futanari", re.I)


def prompt_mentions_futa(text: str) -> bool:
    """True if the prompt asks for a futanari. Ignore NEVER-futanari markings."""
    cleaned = _NEVER_FUTA_RE.sub(" ", str(text or ""))
    return bool(_FUTA_WORD_RE.search(cleaned))


def lock_futa_anatomy(text: str) -> str:
    """Keep every futanari as penis + vagina, no balls. Do not add a penis to NEVER-futanari women."""
    raw = str(text or "")
    if not raw:
        return raw
    out = raw.replace(
        "pale shaft, pink glans, no testicles.",
        "pale shaft, pink glans, " + _FUTA_ANATOMY_TAIL,
    )
    out = out.replace(
        "futanari with a penis that hangs unused",
        FUTA_SCENE_ANATOMY + ". Her penis hangs unused",
    )
    out = out.replace(
        "futanari with a penis in the foreground",
        FUTA_SCENE_ANATOMY + ". Penis in the foreground",
    )
    out = out.replace("futanari with a penis", FUTA_SCENE_ANATOMY)
    out = out.replace(
        "never balls that hangs unused",
        "never balls. Her penis hangs unused",
    )
    out = out.replace(
        "never balls in the foreground",
        "never balls. Penis in the foreground",
    )
    return out


SHAFT_LOOK_LINE = (
    "SHAFT LOOK: Same penis every clip. When erect: 20cm, thick human girth, a clean smooth "
    "human shaft, nearly level with a gentle slight upward curve pointing forward, heavy, "
    "pale-tan shaft matching the body, flushed pink-red glans with a clear mushroom corona ridge. "
    "One piece, left-right symmetric. Same size and same shape the whole take. "
    "Not tiny, not horse-like, not a skinny stick, not a tapered spike, not a hook, "
    "not a ceiling-pointing curve, not a downward droop when erect, not twisted, not forked, "
    "not lumpy, not a mid-shaft bulge, not changing mid-clip. NO testicles, NO scrotum. "
    "Hairless female pussy at the base of the shaft. Penis plus vagina, never balls. "
    "Do not grow balls. Women marked NEVER futanari stay NO penis."
)
ORAL_EASY_SHAFT_LINE = (
    "ORAL EASY SHAFT: The erect 20cm stays a clean human penis: nearly level, gentle slight "
    "upward curve, glans pointing forward toward her mouth so she can take it in easily. "
    "The pink corona is easy to wrap her lips around. Not a sharp upward hook. "
    "Not pointing at the ceiling. Not a malformed bend."
)
ORAL_EASY_STORY_IDS = frozenset({"sales-visit-60s", "checkup-100s"})
MEAT_FUTA_LINE = (
    "FUTA LOCK: Rei is ALWAYS a clear futanari. From frame 1 of this clip she already has "
    "an erect 20cm growing from her own groin, attached to her body, visible in the LOWER "
    "THIRD of the frame, not cropped, not hidden by the tub rim, not a woman-only body. "
    "The erect 20cm STAYS hard the whole take. It does NOT go soft. It does NOT disappear. "
    "It does NOT grow out of the white bath or any liquid. It does NOT emerge from the liquid. "
    "It does NOT appear later. Aya stays NO penis, NEVER futanari."
)
MEAT_SLIME_LINE = (
    "BROWN SLIME: Thick dark-brown viscous slime already coats BOTH whole bodies: "
    "face, hair, eyebrows, lips, neck, breasts, belly, back, ass, thighs, Aya's hairless pussy, "
    "Rei's erect 20cm, and Rei's pussy at the base. It STAYS. It does not fade."
)
MEAT_CESSPIT_LINE = (
    "CESSPIT LOOK: A huge living cesspit of dense dark-brown fecal sludge, like manure paste, "
    "shoulder-deep. Thick brown feces already coats BOTH whole bodies HEAD TO TOE: face, hair, "
    "eyebrows, lips, neck, breasts, belly, back, ass, thighs, feet, Aya's hairless pussy, "
    "Rei's erect 20cm, and Rei's pussy. It STAYS. It does not fade. Not water. Not the white semen. "
    "White semen coating from before mixes with the brown and stays. Both colors remain."
)
MEAT_SEMEN_COAT_LINE = (
    "SEMEN COAT: Both bodies are already coated HEAD TO TOE in that same WHITE waste-oil sludge semen: "
    "face, hair, lips, neck, breasts, belly, back, ass, thighs, feet, pussy, and Rei's 20cm. "
    "TOO MUCH of it. Overflowing piled layers. Extra-viscous molasses-slow opaque WHITE, "
    "like industrial sludge or used engine oil turned white. It STAYS."
)
MEAT_JUPO_DEPTH_LINE = (
    "JUPO DEPTH: Ignore how deep anyone is in the liquid. Aya sucks Rei's erect 20cm to the BASE "
    "as a natural jupo. Mouth on the penis. Do not pause to measure chest, shoulder, or face vs the surface. "
    "Do not require only the lower body under. Do not refuse the suck because of the liquid. "
    "The liquid can cover whatever it covers. The blowjob still happens."
)
MEAT_WALL_IDS = frozenset({"meat-wall-85s", "meat-wall-cesspit-70s"})
SEMEN_HEAVY_OIL = (
    "WHITE industrial-sludge / waste-oil semen: the LOOK of heavy sludge or used engine oil, "
    "but the COLOR is opaque WHITE, never brown, never black, never tar-colored. "
    "heavy-oil-thick clingy viscous sticky opaque WHITE goo (opaque white liquid), "
    "paste-thick like glue, extra-viscous molasses-slow, weighty as poured heavy oil, "
    "like white sludge that slumps and barely flows. "
    "TOO MUCH of it. Overflowing. It floods. It keeps pumping. Extra pulses pile more on. "
    "It piles and pools in fat curtains and piled layers. Fat ropes sag and stretch and hang without dripping off. "
    "Fingers would pull sticky threads. A mouth cannot hold even half of it. "
    "Not watery, not milk, not a thin drip, not a teaspoon, not a thin streak, not saliva, not clear, not foam, not yogurt-thin."
)
BATH_LOOK_LINE = (
    "BATH LOOK: The bath is that same WHITE waste-oil sludge semen: "
    f"{SEMEN_HEAVY_OIL} "
    "It fills the tub deep and overflowing. Extra-viscous molasses-slow. "
    "It clings to skin in fat curtains and coats. It does not look like a water bath."
)


SEMEN_SITUATIONS = frozenset({"oral_creampie", "creampie", "facial", "after_ejaculation"})
SEMEN_LOOK_LINE = (
    "SEMEN LOOK: The semen is always that same heavy-oil-thick WHITE goo: "
    f"{SEMEN_HEAVY_OIL} "
    "Heavy volume, TOO MUCH of it, overflowing. It floods the mouth. Extra-viscous molasses-slow. "
    "The mouth cannot hold even half: a fat overflowing mouthful that spills from the corners in fat curtains, "
    "ropes down the chin, puddles on the breasts in piled layers, and still more keeps pulsing. "
    "Where it lands on face, lips, chin, breasts, belly, thighs, or skin it STAYS: it clings and coats like wet paint. "
    "It does not vanish, does not soak in, does not turn clear, does not run off like water. "
    "From the urethral opening at the glans tip leftover white goo keeps drooling slowly down the shaft "
    "in fat sheets so the penis is glossy and slick with heavy semen. It stays on the face and body after ejaculation."
)
_SEMEN_CUE_RE = re.compile(
    r"CUMOUF|climaxes IN|ejaculates IN|cums inside|cum fills|"
    r"Already a facial|Already after ejaculation|"
    r"viscous white|Thick white cum|shows the semen|The semen stays|"
    r"white semen|white liquid|white goo|white ropes|"
    r"SEMEN SHARE|mouth-to-mouth semen|sticky white",
    re.I,
)


def lock_semen_look(text: str, *, situation: str = "") -> str:
    """Every story: semen is meat-wall-thick, heavy-oil weight, opaque white."""
    raw = str(text or "")
    if not raw or "SEMEN LOOK:" in raw:
        return raw
    sit = str(situation or "").strip()
    if sit not in SEMEN_SITUATIONS and not _SEMEN_CUE_RE.search(raw):
        return raw
    return _inject_before_soundscape(raw, SEMEN_LOOK_LINE)


ORAL_SUCK_SITUATIONS = frozenset({"oral", "futa_blowjob", "oral_creampie"})
ORAL_IN_MOUTH_LINE = (
    "ORAL LOCK: Deep jupo to the BASE, not a tip suck. The whole erect 20cm is already swallowed. "
    "The glans is already fully inside the mouth, already in the throat. Lips are a tight ring at the "
    "BASE of the shaft (at the hairless pussy), not around the glans, not mid-shaft. Nose at the groin. "
    "Cheeks hollow. Throat full. Bob deep: lips stay at the base or slide a little then return to the base. "
    "This is sucking (jupo), not licking. Do not lick the side of the shaft. Do not kiss the shaft. "
    "Do not run the tongue along the shaft. Do not suck only the tip. The penis stays in the mouth "
    "to the BASE, not beside it."
)
ORAL_IN_MOUTH_SHARE_LINE = (
    ORAL_IN_MOUTH_LINE
    + " Until the last cum pulses, KEEP the lips at the BASE. Do not pull back to the glans to catch the cum. "
    "The heavy-oil-thick WHITE goo floods and pulses in the mouth and throat while she is still deep. "
    "After the last pulse only: mouth off the penis. "
    "HOLD STILL a fat overflowing mouthful she cannot hold: opaque extra-viscous molasses-slow "
    "heavy-oil-thick WHITE goo flooding the tongue, spilling in fat curtains at the lips. "
    "The woman who was sucking STANDS UP off her knees to the partner's SAME EYE LEVEL, "
    "then mouth-to-mouth semen share, wet tongue kiss: tongues wrap and tangle around that same heavy white liquid. "
    "Do not kiss from the knees. Do not lick the shaft when coming off."
)
_ORAL_SUCK_RE = re.compile(
    r"Already oral|jupo|blow job|Mouth already on|Mouth already wrapped|"
    r"takes it to the BASE|takes .+ to the BASE|sucks the |already at .+ base",
    re.I,
)
_ORAL_STAY_ON_RE = re.compile(
    r"nobody pulls off|does not pull off|do not pull off|"
    r"mouth still on|Mouth stays on",
    re.I,
)
_ORAL_PULL_OFF_RE = re.compile(r"pulls(?: her mouth)? off", re.I)
ORAL_PULL_OFF_LINE = (
    "ORAL LOCK: Start deep at the BASE, not a tip suck. At frame 1 the whole erect 20cm is still swallowed, "
    "lips a tight ring at the BASE (at the hairless pussy), glans in the throat, nose at the groin. "
    "Then the mouth slides all the way OFF the 20cm in one motion, a saliva string from the lips to the glans. "
    "Do not lick the shaft on the way off. Do not stop at the glans to suck the tip. Once off, the mouth stays off."
)


def lock_oral_in_mouth(text: str, *, situation: str = "", ending: str = "") -> str:
    """Stop H3 from turning a blowjob into tip-suck or shaft-licking. Deep to the BASE, including 口内."""
    raw = str(text or "")
    if not raw or "ORAL LOCK:" in raw:
        return raw
    sit = str(situation or "").strip()
    if sit not in ORAL_SUCK_SITUATIONS:
        return raw
    if re.search(r"urine|yellow stream|pees a |drinks the yellow", raw, re.I):
        return raw
    share_end = str(ending or "").strip() == "share"
    pulling_off = bool(_ORAL_PULL_OFF_RE.search(raw) and not _ORAL_STAY_ON_RE.search(raw))
    if sit != "oral_creampie" and not share_end and pulling_off:
        return _inject_before_soundscape(raw, ORAL_PULL_OFF_LINE)
    if share_end:
        line = ORAL_IN_MOUTH_SHARE_LINE
    elif sit == "oral_creampie":
        line = (
            ORAL_IN_MOUTH_LINE
            + " While it pulses, KEEP the lips at the BASE. Do not pull back to the glans to catch the cum. "
            "The heavy-oil-thick WHITE goo floods and pulses in the mouth and throat while she is still deep. "
            "TOO MUCH. Extra-viscous molasses-slow. A mouth cannot hold even half of it."
        )
    else:
        line = ORAL_IN_MOUTH_LINE
    return _inject_before_soundscape(raw, line)


START_CAST_LINE = (
    "START CAST: START: one woman only. LEFT side of the frame. Closed door on the RIGHT. "
    "Do not show the resident until the door opens and she ENTERS FROM THE RIGHT. Not a two-shot at t=0."
)


def lock_start_cast(text: str) -> str:
    """Visit openings must start as one person at a closed door, then the resident enters."""
    raw = str(text or "")
    if not raw or "START CAST:" in raw:
        return raw
    if not re.search(r"HIDDEN at the start", raw, re.I):
        return raw
    cut = raw.find("\noverall_soundscape:")
    if cut > 0:
        return raw[:cut].rstrip() + "\n" + START_CAST_LINE + "\n" + raw[cut:]
    return raw.rstrip() + "\n" + START_CAST_LINE


def _inject_before_soundscape(raw: str, line: str) -> str:
    text = str(raw or "")
    if not line or line in text:
        return text
    cut = text.find("\noverall_soundscape:")
    if cut > 0:
        return text[:cut].rstrip() + "\n" + line + "\n" + text[cut:]
    return text.rstrip() + "\n" + line


def ensure_futa_anatomy_line(text: str) -> str:
    raw = str(text or "")
    if not raw or FUTA_ANATOMY_MARK in raw:
        return raw
    return _inject_before_soundscape(raw, FUTA_ANATOMY_LOCK_LINE)


SEX_INSIDE_SITUATIONS = frozenset({
    "futa_sex",
    "doggy",
    "riding",
    "missionary_pov",
    "general_sex",
    "futa_anal",
    "anal_penetration",
    "creampie",
})
SEX_ANAL_SITUATIONS = frozenset({"futa_anal", "anal_penetration"})
INSIDE_PUSSY_LINE = (
    "INSIDE LOCK: The erect 20cm is already inside the pussy. The shaft is buried in the vaginal canal. "
    "The glans is in, not outside. Joining point visible: penis in pussy, not beside the labia, "
    "not between the thighs, not rubbing the slit from outside. Not a soft penis. Not a miss. "
    "Keep thrusting while it stays in. Do not pull out for this clip."
)
INSIDE_ANAL_LINE = (
    "INSIDE LOCK: The erect 20cm is already inside the anus. The shaft is buried in the anal canal. "
    "The glans is in, not outside. Joining point visible: penis in anus, not in the pussy this clip, "
    "not beside the hole, not rubbing from outside. Not a soft penis. Not a miss. "
    "Keep thrusting while it stays in. Do not pull out for this clip."
)
INSIDE_ENTRY_LINE = (
    "INSIDE LOCK: Show the entry, then it STAYS in. The erect 20cm goes into the hole on camera: "
    "glans parts the lips (or the anus), shaft sinks to the base. After it is in, keep it inside "
    "and thrust. Not beside. Not between the thighs. Not a soft penis. Not a miss."
)
_SEX_ENTRY_RE = re.compile(r"INSERTION ON CAMERA|Show the entry", re.I)
_SEX_PULL_OUT_RE = re.compile(
    r"then pulls OUT|Starts inside, then pulls|pulls OUT\.|Sex ends\.|comes apart",
    re.I,
)
_ANAL_IN_RE = re.compile(
    r"inside the anus|anal canal|anal only|buried in (her |the )?anus|"
    r"in her anus|into the anus|penis in (the )?anus",
    re.I,
)
_VAGINAL_PREF_RE = re.compile(
    r"vaginal only|no anal|not anal|never anal|do not switch to anal|"
    r"inside the pussy|inside .+ hairless pussy|vaginal canal",
    re.I,
)


def sex_inside_hole(text: str, *, situation: str = "") -> str:
    """Pussy unless this clip is actually anal-in. Do not key off the substring 'anal' alone."""
    sit = str(situation or "").strip()
    if sit in SEX_ANAL_SITUATIONS:
        return "anus"
    raw = str(text or "")
    if _VAGINAL_PREF_RE.search(raw):
        return "pussy"
    if _ANAL_IN_RE.search(raw):
        return "anus"
    return "pussy"


def lock_penis_inside(text: str, *, situation: str = "") -> str:
    """Stop H3 from showing sex beside / rubbing / not in / soft."""
    raw = str(text or "")
    if not raw or "INSIDE LOCK:" in raw:
        return raw
    sit = str(situation or "").strip()
    if sit not in SEX_INSIDE_SITUATIONS:
        return raw
    if _SEX_PULL_OUT_RE.search(raw):
        return raw
    if _SEX_ENTRY_RE.search(raw):
        line = INSIDE_ENTRY_LINE
    elif sex_inside_hole(raw, situation=sit) == "anus":
        line = INSIDE_ANAL_LINE
    else:
        line = INSIDE_PUSSY_LINE
    return _inject_before_soundscape(raw, line)


def lock_futa_shaft(text: str, *, force: bool = False) -> str:
    """Pin futa penis to erect 20cm, same shape. Still 玉なし＋マンコあり. Never add a penis to NEVER-futanari."""
    raw = str(text or "")
    if not raw or "SHAFT LOOK:" in raw:
        return raw
    has_futa = force or (
        "Clear futanari" in raw
        or "Erect 20cm" in raw
        or "erect 20cm" in raw
        or "futanari: erect" in raw.lower()
        or prompt_mentions_futa(raw)
    )
    if not has_futa:
        return raw
    return _inject_before_soundscape(raw, SHAFT_LOOK_LINE)


def lock_oral_easy_shaft(text: str, *, story_id: str = "") -> str:
    """Sales / house-call checkup: shaft angle like a clean human penis so a mouth can take it."""
    raw = str(text or "")
    sid = str(story_id or "").strip()
    if not raw or sid not in ORAL_EASY_STORY_IDS:
        return raw
    if "ORAL EASY SHAFT:" in raw:
        return raw
    if "SHAFT LOOK:" not in raw and "Clear futanari" not in raw and "erect 20cm" not in raw.lower():
        return raw
    return _inject_before_soundscape(raw, ORAL_EASY_SHAFT_LINE)


def lock_meat_wall_look(text: str, *, story_id: str = "", clip_index: int = 0, situation: str = "") -> str:
    """Meat-wall: Rei is already futa; coating stays; jupo ignores how deep they sit in the liquid."""
    raw = str(text or "")
    sid = str(story_id or "").strip()
    if not raw:
        return raw
    idx = int(clip_index or 0)
    oral = (
        str(situation or "").strip() in ORAL_SUCK_SITUATIONS
        or bool(re.search(r"Already oral|CUMOUF|jupo-jupo|takes .+ to the BASE", raw, re.I))
    )
    if sid in MEAT_WALL_IDS:
        if "FUTA LOCK:" not in raw:
            raw = _inject_before_soundscape(raw, MEAT_FUTA_LINE)
        if "SEMEN LOOK:" not in raw:
            raw = _inject_before_soundscape(raw, SEMEN_LOOK_LINE)
        if sid == "meat-wall-85s":
            if "BROWN SLIME:" not in raw:
                raw = _inject_before_soundscape(raw, MEAT_SLIME_LINE)
            if "BATH LOOK:" not in raw:
                raw = _inject_before_soundscape(raw, BATH_LOOK_LINE)
        else:
            if idx == 0:
                if "SEMEN COAT:" not in raw:
                    raw = _inject_before_soundscape(raw, MEAT_SEMEN_COAT_LINE)
            elif "CESSPIT LOOK:" not in raw:
                raw = _inject_before_soundscape(raw, MEAT_CESSPIT_LINE)
        if oral and "JUPO DEPTH:" not in raw:
            raw = _inject_before_soundscape(raw, MEAT_JUPO_DEPTH_LINE)
        return raw
    if sid == "semen-bath-70s" and "BATH LOOK:" not in raw:
        return _inject_before_soundscape(raw, BATH_LOOK_LINE)
    return raw


URINE_SITUATIONS = frozenset({"urine_drink", "urine_pee"})
URINE_LOOK_LINE = (
    "URINE LOOK: Yellow urine. When a 20cm pees, the stream comes out of the urethral "
    "opening at the glans tip (the small hole at the tip of the 20cm), the same hole semen would "
    "pulse from, not from the pussy at the base. When a woman with no penis pees, yellow from her "
    "urethral opening. Opaque yellow water, not clear, not white, not from off-screen."
)
_URINE_CUE_RE = re.compile(
    r"yellow stream|yellow urine|pees a |pees from|drinks the yellow|"
    r"urine stream|releases the stream|peeing|Urine from .+ urethra",
    re.I,
)
_URINE_NEG_RE = re.compile(r"No urine yet|No urine\.|No urine,", re.I)


def lock_urine_look(text: str, *, situation: str = "") -> str:
    """H3 skips pee unless the prompt names yellow water from the tip hole, like semen."""
    raw = str(text or "")
    if not raw or "URINE LOOK:" in raw:
        return raw
    sit = str(situation or "").strip()
    if sit not in URINE_SITUATIONS and not _URINE_CUE_RE.search(raw):
        return raw
    if _URINE_NEG_RE.search(raw) and sit not in URINE_SITUATIONS and not re.search(
        r"yellow stream|yellow urine|pees a |drinks the yellow|peeing", raw, re.I
    ):
        return raw
    return _inject_before_soundscape(raw, URINE_LOOK_LINE)


SCAT_ACT_LINE = (
    "SCAT ACT: Brown feces coming out of the anus in this clip. This is the act of "
    "defecating now, not a body already coated from before. It leaves through the anus, "
    "not the vagina, not from off-screen."
)
_SCAT_CUE_RE = re.compile(
    r"act of defecating|feces coming out|coming out of .+ anus|defecat",
    re.I,
)


def lock_scat_act(text: str, *, situation: str = "") -> str:
    """Keep scat as the act of passing, not a pre-coated cesspit look."""
    raw = str(text or "")
    if not raw or "SCAT ACT:" in raw:
        return raw
    sit = str(situation or "").strip()
    if sit != "scat_act" and not _SCAT_CUE_RE.search(raw):
        return raw
    return _inject_before_soundscape(raw, SCAT_ACT_LINE)


POSE_JA = {
    "（シーンのまま）": "",
    "シーンのまま": "",
    "": "",
    "立ち": "standing",
    "standing": "standing",
    "騎乗": "cowgirl",
    "騎乗位": "cowgirl",
    "cowgirl": "cowgirl",
    "後背": "doggy",
    "後背位": "doggy",
    "doggy": "doggy",
    "正常位": "missionary",
    "missionary": "missionary",
    "横": "side",
    "side": "side",
    "しゃがみ": "squat",
    "squat": "squat",
    "膝立ち": "kneeling",
    "kneeling": "kneeling",
    "座り": "sitting",
    "sitting": "sitting",
    "POV": "pov",
    "pov": "pov",
}
POSE_LOCK_LINE = {
    "standing": (
        "POSE LOCK: Standing on their feet, front three-quarter, medium two-shot. "
        "Hips at camera height. Not on all fours. Not cowgirl unless asked."
    ),
    "cowgirl": (
        "POSE LOCK: Cowgirl. Receiver sits on the shaft facing, knees beside the hips, "
        "riding up and down. Both faces readable. Not doggy."
    ),
    "doggy": (
        "POSE LOCK: Doggy. Receiver on all fours, shaft from behind. Hands on the hips. "
        "If anal, the anus sits above the vagina in frame."
    ),
    "missionary": (
        "POSE LOCK: Missionary. Receiver on her back, legs open, shaft from the front. "
        "Side-front camera. Not a first-person POV unless asked."
    ),
    "side": (
        "POSE LOCK: Side / spoon. Both on their sides. Joining at the hips. Medium two-shot."
    ),
    "squat": (
        "POSE LOCK: Squat. Knees bent, hips down. Front three-quarter. If defecating, "
        "the anus faces the camera."
    ),
    "kneeling": (
        "POSE LOCK: Kneeling. One or both on their knees. Front, medium two-shot."
    ),
    "sitting": (
        "POSE LOCK: Sitting. Hips on a seat or floor. Front three-quarter."
    ),
    "pov": (
        "POSE LOCK: Point-of-view from the shaft, looking down at the joining."
    ),
}
POSE_SITUATION_MAP = {
    ("futa_sex", "cowgirl"): "riding",
    ("futa_sex", "doggy"): "doggy",
    ("futa_sex", "pov"): "missionary_pov",
    ("general_sex", "cowgirl"): "riding",
    ("general_sex", "doggy"): "doggy",
    ("general_sex", "pov"): "missionary_pov",
}
AV_LOOK_SITUATIONS = frozenset({
    "futa_sex",
    "riding",
    "doggy",
    "missionary_pov",
    "general_sex",
    "futa_anal",
    "anal_penetration",
    "urine_drink",
    "urine_pee",
    "scat_act",
    "creampie",
})
AV_LOOK_LINE = (
    "AV LOOK: Live-action Japanese adult video. Photoreal skin and sweat, wet genitals, "
    "joining or stream readable like a sex-scene close. No anime. No illustration. No freeze."
)
GENITAL_PEE_LINE = (
    "GENITAL PEE: The yellow stream leaves the body from the genitals on camera. "
    "Futanari: from the urethral opening at the glans tip of the erect 20cm, the same hole "
    "semen uses. Woman with no penis: from the urethral opening above the vagina. "
    "Not from the anus. Not from the vaginal hole. Not from off-screen. Not white. Not clear water."
)


def resolve_pose(name: str) -> str:
    key = str(name or "").strip()
    if key in POSE_JA:
        return str(POSE_JA[key] or "")
    low = key.lower()
    if low in POSE_JA:
        return str(POSE_JA[low] or "")
    return ""


def apply_pose_situation(situation: str, pose: str) -> str:
    """Sex in cowgirl/doggy/POV uses the pose LoRA. Anal/urine/scat stay unlocked."""
    sit = str(situation or "").strip()
    pose_key = resolve_pose(pose) if pose else str(pose or "").strip()
    if not pose_key:
        return sit
    return POSE_SITUATION_MAP.get((sit, pose_key), sit)


ORAL_CAMERA_LINE = (
    "ORAL CAMERA: Third-person medium two-shot. Both people stay readable: the mouth "
    "from head to knees and the shaft partner from head to mid-thigh in the same frame. "
    "Face, breasts, hips, and the 20cm in the mouth all readable. Not first-person. "
    "Not from the shaft. Not from the lap. Not POV. Not a GoPro. Not a mouth-only crop. "
    "The 20cm stays small in the lower third and must NEVER fill the lens. "
    "Place, sit vs stand, and who is on a seat come from the prompt. "
    "Do not invent a toilet, a beach, Hachiko, or a named city unless the prompt names them. "
    "If no place is named, a plain indoor room."
)
ORAL_SEAT_LINE = (
    "ORAL SEAT: If the shaft partner is sitting (bench, chair, sofa, toilet, stool), they "
    "STAY seated the whole take. Hips glued to the seat. They never stand for a kiss or for jupo. "
    "The mouth comes to them. During jupo, a pleasure face is OK; hips stay on the seat. "
    "If nobody is sitting, ignore this."
)
PHONE_ORAL_WOMAN = (
    "Young adult woman, clearly over 21, fully nude, innocent girl-next-door face, "
    "ordinary everyday look, feminine body. No penis. Not a man."
)
PHONE_ORAL_FUTA = (
    "Young adult woman, clearly over 21, fully nude, innocent girl-next-door face, "
    "ordinary everyday look, feminine body, futanari: erect 20cm, pale human shaft, "
    "distinct pink glans, almost-horizontal with a slight upward curve, hairless female "
    "pussy at the base of the shaft, no testicles, no scrotum. Penis plus vagina, never balls. "
    "Not a man."
)
_ORAL_FULL_PROMPT_RE = re.compile(
    r"subject_definitions:|integrated_multimodal_description:|ORAL CAMERA:",
    re.I,
)


def lock_oral_camera(text: str, *, situation: str = "") -> str:
    """Phone ③ BJ: third-person two-shot. Blowjob LoRA otherwise falls into shaft-POV."""
    raw = str(text or "")
    sit = str(situation or "").strip()
    if not raw or sit not in ORAL_SUCK_SITUATIONS or "ORAL CAMERA:" in raw:
        return raw
    return _inject_before_soundscape(raw, ORAL_CAMERA_LINE)


def lock_oral_seat(text: str, *, situation: str = "") -> str:
    """If the prompt sits the shaft partner, keep them on that seat."""
    raw = str(text or "")
    sit = str(situation or "").strip()
    if not raw or sit not in ORAL_SUCK_SITUATIONS or "ORAL SEAT:" in raw:
        return raw
    return _inject_before_soundscape(raw, ORAL_SEAT_LINE)


def _split_leading_triggers(text: str) -> tuple[str, str]:
    lines = str(text or "").split("\n")
    i = 0
    while i < len(lines) and not str(lines[i]).strip():
        i += 1
    lead: list[str] = []
    while i < len(lines) and _CHAIN_TRIGGER_LINE_RE.match(str(lines[i]).strip() or ""):
        lead.append(str(lines[i]).strip())
        i += 1
        while i < len(lines) and not str(lines[i]).strip():
            i += 1
    rest = "\n".join(lines[i:]).strip()
    header = "\n".join(lead).strip()
    return header, rest


def wrap_phone_oral_prompt(text: str, *, situation: str = "") -> str:
    """Short 文章 becomes place/action on a generic futa BJ. Full H3 prompts stay as written."""
    original = str(text or "")
    raw = original.strip()
    sit = str(situation or "").strip()
    if not raw or sit not in ORAL_SUCK_SITUATIONS:
        return original
    if _ORAL_FULL_PROMPT_RE.search(raw):
        return original
    if _URINE_CUE_RE.search(raw) and sit in {"oral", "futa_blowjob"}:
        return original
    header, rest = _split_leading_triggers(raw)
    if not rest:
        return original
    if _ORAL_FULL_PROMPT_RE.search(rest):
        return original
    user = english_except_speech(rest)
    if sit in {"oral", "oral_creampie"}:
        s1, s2 = PHONE_ORAL_WOMAN, PHONE_ORAL_FUTA
    else:
        s1, s2 = PHONE_ORAL_FUTA, PHONE_ORAL_WOMAN
    if sit == "oral_creampie":
        action = (
            "CUMOUF. Already oral. Already at the BASE. Thick opaque WHITE goo pulses in the mouth. "
            "Not a facial."
        )
    else:
        action = (
            "Already a blow job. Already oral. Already at the BASE. Deep jupo-jupo the whole take."
        )
    body = (
        "Vertical 9:16 live-action photorealism, no anime.\n\n"
        "subject_definitions:\n"
        f"<Subject 1> {s1}\n"
        f"<Subject 2> {s2}\n\n"
        "environment: Use the place named in USER SCENE. If none, a plain indoor room. "
        "Do not invent a toilet, a beach, Hachiko, or a named city unless USER SCENE names them.\n\n"
        f"USER SCENE:\n{user}\n\n"
        "integrated_multimodal_description:\n"
        f"{action} Third-person medium two-shot of both people. Follow USER SCENE for place, "
        "who sits, who kneels, who arrives, and quoted speech. If USER SCENE already has a seat, "
        "the shaft partner stays on that seat. Hands of the mouth on thighs or own knees, "
        "NEVER on the shaft.\n\n"
        "overall_soundscape:\n"
        "Wet jupo-jupo. Pleasure breath, not words, unless USER SCENE has quoted speech.\n\n"
        "All performers are consenting adult women 21 years or older. No man appears."
    )
    if header:
        return header + "\n" + body
    return body


def apply_pose_lock(text: str, pose: str) -> str:
    raw = str(text or "")
    pose_key = resolve_pose(pose) if pose else str(pose or "").strip()
    if not raw or not pose_key:
        return raw
    line = POSE_LOCK_LINE.get(pose_key)
    if not line or "POSE LOCK:" in raw:
        return raw
    return _inject_before_soundscape(raw, line)


def lock_av_look(text: str, *, situation: str = "") -> str:
    raw = str(text or "")
    sit = str(situation or "").strip()
    if not raw or sit not in AV_LOOK_SITUATIONS or "AV LOOK:" in raw:
        return raw
    return _inject_before_soundscape(raw, AV_LOOK_LINE)


def lock_genital_pee(text: str, *, situation: str = "") -> str:
    raw = str(text or "")
    sit = str(situation or "").strip()
    if not raw or "GENITAL PEE:" in raw:
        return raw
    if sit not in URINE_SITUATIONS and not _URINE_CUE_RE.search(raw):
        return raw
    return _inject_before_soundscape(raw, GENITAL_PEE_LINE)


def apply_phone_act_locks(text: str, *, situation: str = "", pose: str = "") -> str:
    """Phone ③: pose + AV look + genital pee / anal inside / scat from the anus.

    Futa BJ / フェラ / 口内: pose field is ignored (place and sit/stand come from 文章).
    Short notes wrap onto a generic third-person two-shot already at the BASE.
    """
    sit = str(situation or "").strip()
    out = str(text or "")
    if sit in ORAL_SUCK_SITUATIONS:
        out = wrap_phone_oral_prompt(out, situation=sit)
    else:
        out = apply_pose_lock(out, pose)
    out = lock_av_look(out, situation=situation)
    out = lock_urine_look(out, situation=situation)
    out = lock_genital_pee(out, situation=situation)
    out = lock_scat_act(out, situation=situation)
    out = lock_penis_inside(out, situation=situation)
    out = lock_act_sfx(out, situation=situation)
    if sit in ORAL_SUCK_SITUATIONS:
        out = lock_oral_camera(out, situation=sit)
        out = lock_oral_seat(out, situation=sit)
        out = lock_oral_in_mouth(out, situation=sit)
        out = lock_pleasure_face(out, situation=sit)
    out = lock_futa_anatomy(out)
    force_futa = sit in {"sfw_daily", "sfw_preview", "sfw_audio"} or prompt_mentions_futa(out)
    if force_futa:
        out = ensure_futa_anatomy_line(out)
    out = lock_futa_shaft(out, force=force_futa)
    return out


SPEECH_FACE_LINE = (
    "SPEECH FACE: Not monotone. Not a recitation. The voice has feeling that matches the line. "
    "The speaking face matches: brows, eyes, cheeks, and mouth move with the emotion. "
    "Not a blank idle face. Not a news-anchor face."
)
HEAT_FACE_LINE = (
    "HEAT FACE: Midsummer heat. On the hot line, a miserably hot face: flushed, sweaty, "
    "damp bangs, squinted from the glare, panting between words, wiping sweat. "
    "Then if a cool-relief line follows, the face melts into relief. "
    "Not a cool indoor face while complaining about the heat."
)
_HEAT_COMPLAINT_RE = re.compile(r"あち[ぃい]+ー?|あっちー")


def lock_spoken_emotion(text: str) -> str:
    """Spoken clips need emotion in the voice and a matching face, not a flat reading."""
    raw = str(text or "")
    if not raw or not spoken_lines(raw):
        return raw
    out = raw
    if "SPEECH FACE:" not in out:
        out = _inject_before_soundscape(out, SPEECH_FACE_LINE)
    if "HEAT FACE:" not in out and any(_HEAT_COMPLAINT_RE.search(ln) for ln in spoken_lines(out)):
        out = _inject_before_soundscape(out, HEAT_FACE_LINE)
    return out


PLEASURE_JUPO_LINE = (
    "PLEASURE FACE: The woman being sucked looks really good, not blank. "
    "Head tipped back, mouth open, eyes half-closed, brows knit, a wrecked pleasured receiver face. "
    "Breath hitches. Small soft female moans from the receiver, quiet, not words. "
    "She is enjoying the jupo. Not a work mask. Not a straight clinical face."
)
ORGASM_FACE_LINE = (
    "ORGASM FACE: Climax face. She is coming hard. Eyes rolling or squeezed shut, mouth open, "
    "brows up, flushed, shaking through the pulses. A small cry or hitch, not extra Japanese words. "
    "Extremely good. Not a calm work face. Not a straight clinical face."
)
SEX_PLEASURE_LINE = (
    "PLEASURE FACE: Both look like it feels really good, not blank. Flushed, mouths open, "
    "brows knit, hips moving. Small soft female moans from both when it feels good, quiet, not words. "
    "Not a work mask. Not a straight clinical face."
)
PLEASURE_VOICE_LINE = (
    "PLEASURE VOICE: When it feels good, leaked female moans and wet hitching breath. "
    "Audible. Not words. Not extra Japanese dialogue. Not a scream. Not a new spoken line."
)
EROTIC_WAIT_LINE = (
    "EROTIC WAIT: Leftover / pause seconds only. Do not freeze. Do not add, skip, or replace the written beat. "
    "Same who sits, stands, walks, lies, sucks, drinks, drives, sings, writes, or is inside. "
    "If someone is already sucking, keep that mouth on the penis to the BASE. "
    "Do not pull off a suck or pull out of a hole just to wait. "
    "If the written beat already pulls off or pulls out, do that written beat. "
    "If a mouth must stay OPEN a hand's width from the tip, keep it OPEN and off. Do not kiss that mouth. "
    "If a spoken Japanese line is still going, do not cover that mouth until the line ends. "
    "If hands are on a wheel, a microphone, chalk, a tray, a door, or this clip says hands NEVER on the shaft, those hands stay there. "
    "If this clip says No kiss yet, does not kiss, or No deep kiss, leftover is a SEDUCTIVE SMILE and light self-touch only. "
    "Do not add a kiss or a French peck. Do not add the first partner peck or the first grope. "
    "If this clip says No oral yet, do not start oral. If it says Walk only, keep walking. "
    "If this clip wants a blank / poker / expressionless / clinical face, do not add a smile. "
    "Do not start oral or insertion that is not already written. "
    "Do not squat, kneel, stand up, lie down, turn a rear pose into face-to-face, or enter a tub just to wait. "
    "Not a frozen pose. "
    "Hands keep moving on the partner's body "
    "(breasts, waist, hips, the erect 20cm, or a hairless pussy) in a way that matches who is already touching what. "
    "Leftover only, after the written beat and after the last unique quoted line, "
    "and only with a free hand or a free mouth that does not change pose: "
    "kisses on the mouth and/or breasts plus skinship so the same Japanese line is not spoken twice or three times; "
    "a SEDUCTIVE SMILE if the face is allowed to change; "
    "light self-touch on her own breasts, her own hairless pussy, or her own unused erect 20cm; "
    "light partner-touch on breasts, a hairless pussy, or an unused erect 20cm when they are already close enough; "
    "a light French peck (tongue tip and lips touch a breast, a hairless pussy, or an unused 20cm, then leave at once) "
    "ONLY when both mouths are free, faces are already close enough, this clip does not forbid a kiss, "
    "and the peck does not replace a written deep kiss or mouth-to-mouth semen share. "
    "NOT oral. NOT in the mouth. NOT jupo. NOT a squat."
)
PLEASURE_VOICE_SFX = "Leaked female moans, wet hitching breath, not words."
_WALK_IDLE_RE = re.compile(
    r"\b(walks|walking|commute|on the way to school|street walk)\b",
    re.I,
)
_EROTIC_IDLE_CUE_RE = re.compile(
    r"\bkiss\b|knead|Already oral|jupo|already in|stroking the erect|"
    r"one hand stroking|idly stroking|rubs her own|masturbat|creampie|"
    r"cowgirl|straddl|hand['’]s width|mouth OPEN|"
    r"deep kiss|tongue kiss|SEDUCTIVE|erotic wait|"
    r"fingers on her clit|fingers near",
    re.I,
)
_SKIP_COMMON_WAIT_RE = re.compile(
    r"Heat and relief only|One woman only|HEAT FACE:",
    re.I,
)


def _is_walk_or_opening_idle(prompt: str) -> bool:
    """Entrance, waiting halls, and silent walks stay as written. Speech leftover is not a walk."""
    p = str(prompt or "")
    if "HIDDEN at the start" in p:
        return True
    if "Waiting only" in p:
        return True
    if _SPOKEN_RE.search(p):
        return False
    if _WALK_IDLE_RE.search(p) and not _EROTIC_IDLE_CUE_RE.search(p):
        return True
    return False


def wants_pleasure_idle(text: str, *, situation: str = "") -> bool:
    """Common leftover wait for every story. Skip openings, silent walks, heat-only solos, urine-drink."""
    sit = str(situation or "").strip()
    raw = str(text or "")
    if not raw:
        return False
    if _URINE_CUE_RE.search(raw) and sit in {"oral", "futa_blowjob"}:
        return False
    if sit in ACT_SITUATIONS:
        return True
    if sit != "futa_visible":
        return False
    if _is_walk_or_opening_idle(raw):
        return False
    if _SKIP_COMMON_WAIT_RE.search(raw):
        return False
    if _SPOKEN_RE.search(raw):
        return True
    return bool(_EROTIC_IDLE_CUE_RE.search(raw))


def _append_soundscape(raw: str, extra: str) -> str:
    text = str(raw or "")
    extra = str(extra or "").strip()
    if not extra:
        return text
    span = soundscape_bounds(text)
    if span is None:
        return text
    start, end = span
    body = text[start:end]
    if extra.lower() in body.lower():
        return text
    trimmed = body.rstrip()
    if trimmed and not trimmed.endswith((".", "!", "?")):
        trimmed += "."
    new_body = (trimmed + " " + extra).strip()
    if body.startswith("\n") or not body:
        new_body = "\n" + new_body
    if body.endswith("\n") or end < len(text):
        new_body = new_body.rstrip() + "\n"
    return text[:start] + new_body + text[end:]


def lock_pleasure_voice_and_wait(text: str, *, situation: str = "") -> str:
    """Small moans when it feels good. Leftover seconds stay erotic without rewriting the beat."""
    raw = str(text or "")
    if not raw or not wants_pleasure_idle(raw, situation=situation):
        return raw
    out = raw
    if "PLEASURE VOICE:" not in out:
        out = _inject_before_soundscape(out, PLEASURE_VOICE_LINE)
    if "EROTIC WAIT:" not in out:
        out = _inject_before_soundscape(out, EROTIC_WAIT_LINE)
    return _append_soundscape(out, PLEASURE_VOICE_SFX)


def lock_pleasure_face(text: str, *, situation: str = "") -> str:
    """Jupo receivers look pleasured; ejaculation is an イキ顔; sex is not a blank stare."""
    raw = str(text or "")
    if not raw:
        return raw
    sit = str(situation or "").strip()
    if _URINE_CUE_RE.search(raw) and sit in {"oral", "futa_blowjob"}:
        return raw
    if sit in SEMEN_SITUATIONS or sit == "oral_creampie":
        if "ORGASM FACE:" in raw:
            return raw
        return _inject_before_soundscape(raw, ORGASM_FACE_LINE)
    if sit in {"oral", "futa_blowjob"}:
        if "PLEASURE FACE:" in raw:
            return raw
        return _inject_before_soundscape(raw, PLEASURE_JUPO_LINE)
    if sit in {"futa_sex", "doggy", "riding", "cunnilingus_futa"}:
        if "PLEASURE FACE:" in raw:
            return raw
        return _inject_before_soundscape(raw, SEX_PLEASURE_LINE)
    return raw


SEMEN_SHARE_KISS = (
    # Lowercase "tongues wrap": Colab ③'s freshness gate is case-sensitive.
    "Then mouth-to-mouth semen share, a filthy deep wet kiss. tongues wrap and tangle around a fat overflowing "
    "mouthful of opaque sticky extra-viscous molasses-slow heavy-oil-thick WHITE goo, pushing it back and forth, "
    "gooey strands stretching between the tongues, coating both tongues, lips, and chins. "
    "TOO MUCH of it. It floods both mouths. The white goo STAYS on both faces in piled layers."
)
SEMEN_SHARE_LINE = (
    "SEMEN SHARE: After the last pulse, mouth off the penis. HOLD STILL: a fat overflowing mouthful she cannot hold of "
    "clingy sticky gooey opaque extra-viscous molasses-slow heavy-oil-thick WHITE goo floods the tongue, "
    "viscous, not watery, not a thin drip. "
    "The woman who was sucking STANDS UP off her knees until her eyes are at the SAME EYE LEVEL "
    "as the partner. If the partner was sitting or lying, they sit up or stand so both faces meet at equal height. "
    f"{SEMEN_SHARE_KISS} "
    "Do NOT kiss from the knees. Do NOT look up from the floor. Do NOT stay kneeling or squatting for the kiss. "
    "Do not swallow it all first. Do not add a new clip."
)
SEMEN_SHARE_BEAT = (
    "HOLD STILL: a fat overflowing mouthful she cannot hold of clingy sticky gooey opaque extra-viscous "
    "molasses-slow heavy-oil-thick WHITE goo floods the tongue, viscous, "
    "not watery. The woman who was sucking STANDS UP off her knees "
    "to the partner's SAME EYE LEVEL. If the partner was sitting or lying, they sit up or stand to meet her. "
    f"{SEMEN_SHARE_KISS} "
    "Do NOT kiss from the knees. Do not swallow it all first."
)
SEMEN_SHARE_SUPINE_BEAT = (
    "HOLD STILL: a fat overflowing mouthful she cannot hold of clingy sticky gooey opaque extra-viscous "
    "molasses-slow heavy-oil-thick WHITE goo floods the tongue, viscous, "
    "not watery. The woman who was sucking leans DOWN to the partner's mouth. "
    "The partner STAYS LYING ON THEIR BACK the whole kiss. Do NOT sit them up. Do NOT stand them up. "
    "Do NOT bring them to standing eye level. "
    f"{SEMEN_SHARE_KISS} "
    "Do not swallow it all first."
)
SEMEN_SHARE_SUPINE_LINE = (
    "SEMEN SHARE: After the last pulse, mouth off the penis. HOLD STILL: a fat overflowing mouthful she cannot hold of "
    "clingy sticky gooey opaque extra-viscous molasses-slow heavy-oil-thick WHITE goo floods the tongue, "
    "viscous, not watery, not a thin drip. "
    "The woman who was sucking leans DOWN to the partner's mouth. The partner STAYS LYING ON THEIR BACK "
    "the whole kiss. Do NOT sit them up. Do NOT stand them up. Do NOT bring them to standing eye level. "
    f"{SEMEN_SHARE_KISS} "
    "Do not swallow it all first. Do not add a new clip."
)
_SHARE_STAND_REPLACEMENTS = (
    ("they lean in and pass that same thick white liquid", "she STANDS UP to the SAME EYE LEVEL and they pass that same thick white liquid"),
    ("Then 口移し ベロチュー: they lean in", "Then she STANDS UP to the SAME EYE LEVEL for 口移し ベロチュー"),
    ("Then 口移し ベロチュー: they pass", "Then she STANDS UP to the SAME EYE LEVEL for 口移し ベロチュー: they pass"),
    ("then leans into the 口移し ベロチュー", "then meets her at the SAME EYE LEVEL for 口移し ベロチュー after she stands"),
    ("leans into the 口移し ベロチュー", "meets her at the SAME EYE LEVEL for 口移し ベロチュー after she stands"),
    ("leans down into the 口移し ベロチュー", "sits up or stands to the SAME EYE LEVEL for 口移し ベロチュー"),
    ("Then she rises just enough for 口移し", "Then she STANDS UP to the SAME EYE LEVEL for 口移し"),
    ("Then mouth-to-mouth semen share: they lean in", "Then she STANDS UP to the SAME EYE LEVEL for mouth-to-mouth semen share"),
    ("then leans into the mouth-to-mouth", "then meets her at the SAME EYE LEVEL for mouth-to-mouth after she stands"),
    ("Then she rises just enough for mouth-to-mouth", "Then she STANDS UP to the SAME EYE LEVEL for mouth-to-mouth"),
    ("then pulls OFF and rises just enough to Rei's mouth", "then pulls OFF and STANDS UP to Rei's SAME EYE LEVEL"),
    ("then pulls OFF. HOLD STILL", "then pulls OFF and STANDS UP to the SAME EYE LEVEL. HOLD STILL"),
    ("she stays squatting", "she STANDS UP to the SAME EYE LEVEL"),
    ("She stays squatting", "She STANDS UP to the SAME EYE LEVEL"),
    ("still squatting, viscous white semen", "then STANDS UP to the SAME EYE LEVEL, viscous white semen"),
    ("looks up at Rei and SPEAKS", "STANDS UP to Rei's SAME EYE LEVEL and SPEAKS"),
    ("looking up:", "standing at the SAME EYE LEVEL:"),
    ("Aya = pulls off, kneeling, white on her lips", "Aya = pulls off, STANDS UP to the SAME EYE LEVEL, white on her lips"),
    ("Aya = kneeling, mouth off, viscous white semen", "Aya = STANDS UP to the SAME EYE LEVEL, mouth off, viscous white semen"),
    ("Rei stays on her back.", "Rei sits up to the SAME EYE LEVEL."),
    ("She stays on the stool.", "She sits up on the stool so their eyes match at the SAME EYE LEVEL."),
    ("Rei stays seated.", "Rei sits up or stands so their eyes match at the SAME EYE LEVEL."),
    ("Rei remains seated.", "Rei sits up or stands so their eyes match at the SAME EYE LEVEL."),
    ("Then she stands and they fall into a deep wet tongue kiss", "Then she STANDS UP to the SAME EYE LEVEL and they fall into a deep wet kiss"),
    ("then stands into a deep wet tongue kiss", "then STANDS UP to the SAME EYE LEVEL into a deep wet kiss"),
    ("Then she STANDS UP to the SAME EYE LEVEL and they fall into a deep wet 濃厚キス", "Then she STANDS UP to the SAME EYE LEVEL and they fall into a deep wet kiss"),
)
# Geometry or act that cannot take a mouth-to-mouth share (vaginal creampie, under-desk, walk-away).
SEMEN_SHARE_SKIP = frozenset({
    "commute-120s",
    "rooftop-100s",
    "yoga-50s",
    "laundromat-50s",
    "fireworks-50s",
    "camp-50s",
    "back-wash-60s",
    "lecture-desk-50s",
    "semen-bath-70s",
})
# story_id -> (clip_index, mode). silent_next = drop blowjob LoRA. after_speech = keep the line.
# on_cumouf = last seconds of the CUMOUF clip (next speaker is a third person / driving / job).
# on_back = 口移し while the partner STAYS LYING ON THEIR BACK (do not stand them).
SEMEN_SHARE_BY_STORY: dict[str, list[tuple[int, str]]] = {
    "bath-120s": [(10, "silent_next")],
    "dinner-120s": [(10, "silent_next")],
    "futon-120s": [(10, "silent_next")],
    "okaeri-120s": [(8, "silent_next")],
    "lecture-120s": [(7, "silent_next")],
    "dishes-90s": [(11, "silent_next")],
    "cafe-100s": [(9, "after_speech")],
    "checkup-100s": [(8, "after_speech")],
    "clinic-75s": [(8, "on_back")],
    "meat-wall-85s": [(6, "after_speech")],
    "meat-wall-cesspit-70s": [(6, "after_speech")],
    "homecoming-90s": [(10, "after_speech")],
    "karaoke-50s": [(4, "after_speech")],
    "sales-visit-60s": [(7, "after_speech")],
    "train-sales-80s": [(7, "after_speech")],
    "engawa-120s": [(10, "on_cumouf")],
    "sunday-120s": [(10, "on_cumouf")],
    "last-stop-40s": [(2, "on_cumouf")],
    "last-train-120s": [(3, "on_cumouf"), (9, "silent_next")],
    "red-light-50s": [(3, "on_cumouf")],
}
_REMAINING_SILENCE_RE = re.compile(
    r"Remaining seconds, silence:.*?(?:Do not freeze\.|No freeze\.)",
    re.S,
)
_STILL_IN_MOUTH_END_RE = re.compile(r"End: still in her mouth[^.]*\.")
_MOUTH_STILL_ON_END_RE = re.compile(r"End: mouth still on[^.]*\.")


def semen_share_plan(story: dict[str, Any] | None) -> list[tuple[int, str]]:
    """Which clip gets the HOLD + 口移し ベロチュー beat. Empty = skip this story."""
    data = story or {}
    sid = str(data.get("id") or "").strip()
    if sid in SEMEN_SHARE_SKIP:
        return []
    if str(data.get("kind") or "") == "anthology":
        return [
            (i, "on_cumouf")
            for i, clip in enumerate(data.get("clips") or [])
            if str(clip.get("situation") or "") == "oral_creampie"
        ]
    if sid in ADDON_PACK_IDS or bool(data.get("addon")):
        return [
            (i, "on_cumouf")
            for i, clip in enumerate(data.get("clips") or [])
            if str(clip.get("situation") or "") == "oral_creampie"
        ]
    return list(SEMEN_SHARE_BY_STORY.get(sid, []))


def _rewrite_share_stand(raw: str) -> str:
    """Kiss is standing at equal eye level. Not from the knees looking up."""
    text = str(raw or "")
    for old, new in _SHARE_STAND_REPLACEMENTS:
        text = text.replace(old, new)
    return text


def lock_semen_share_kiss(text: str, *, supine: bool = False) -> str:
    """Idempotent marker: HOLD white, then 濃厚キス 口移し.

    Default: ジュボ側 stands to eye level. supine=True: partner STAYS LYING ON THEIR BACK.
    """
    raw = str(text or "")
    if not raw:
        return raw
    if supine:
        if "SEMEN SHARE:" in raw and "STAYS LYING" in raw:
            return raw
        if "SEMEN SHARE:" in raw:
            raw = re.sub(
                r"SEMEN SHARE:.*?(?=\n\noverall_soundscape:|\noverall_soundscape:|\Z)",
                SEMEN_SHARE_SUPINE_LINE + "\n",
                raw,
                count=1,
                flags=re.S,
            )
            return raw
        cut = raw.find("\noverall_soundscape:")
        if cut > 0:
            return raw[:cut].rstrip() + "\n" + SEMEN_SHARE_SUPINE_LINE + "\n" + raw[cut:]
        return raw.rstrip() + "\n" + SEMEN_SHARE_SUPINE_LINE
    if "SEMEN SHARE:" in raw:
        if "SAME EYE LEVEL" in raw:
            return raw
        raw = re.sub(
            r"SEMEN SHARE:.*?(?=\n\noverall_soundscape:|\noverall_soundscape:|\Z)",
            SEMEN_SHARE_LINE + "\n",
            raw,
            count=1,
            flags=re.S,
        )
        return raw
    cut = raw.find("\noverall_soundscape:")
    if cut > 0:
        return raw[:cut].rstrip() + "\n" + SEMEN_SHARE_LINE + "\n" + raw[cut:]
    return raw.rstrip() + "\n" + SEMEN_SHARE_LINE


def inject_semen_share_into_prompt(prompt: str, *, where: str) -> str:
    """Rewrite the share clip so the last seconds are HOLD white liquid + 口移し."""
    raw = str(prompt or "")
    if not raw or "SEMEN SHARE:" in raw:
        return raw
    mode = str(where or "").strip()
    share_end = (
        f"After the last pulse, mouth off. {SEMEN_SHARE_BEAT} "
        "End: standing at the SAME EYE LEVEL, tongues sharing the thick white liquid, not still on the shaft, not kneeling."
    )
    if mode == "on_back":
        if _REMAINING_SILENCE_RE.search(raw):
            raw = _REMAINING_SILENCE_RE.sub(
                f"Remaining seconds, silence: mouth off the penis. {SEMEN_SHARE_SUPINE_BEAT} Do not freeze.",
                raw,
                count=1,
            )
        elif "口移し" in raw or "mouth-to-mouth" in raw.lower() or "STAYS LYING" in raw:
            return raw
        elif "\noverall_soundscape:" in raw:
            raw = raw.replace(
                "\noverall_soundscape:",
                f"\n{SEMEN_SHARE_SUPINE_BEAT}\n\noverall_soundscape:",
                1,
            )
        return raw
    raw = _rewrite_share_stand(raw)
    if mode == "after_speech":
        if _REMAINING_SILENCE_RE.search(raw):
            raw = _REMAINING_SILENCE_RE.sub(
                f"Remaining seconds, silence: mouth off the penis. {SEMEN_SHARE_BEAT} Do not freeze.",
                raw,
                count=1,
            )
        elif ("口移し" in raw or "mouth-to-mouth" in raw.lower()) and "HOLD STILL" in raw:
            return _rewrite_share_stand(raw)
        elif re.search(r"tongue kiss", raw, re.I) or "ベロチュー" in raw or "wet tongue kiss" in raw.lower():
            raw = re.sub(
                r"(deep wet tongue kiss|deep wet 濃厚キス|deep filthy wet kiss)",
                r"\1, mouth-to-mouth semen share of the thick sticky white liquid still on the tongue",
                raw,
                count=1,
                flags=re.I,
            )
            if "HOLD STILL" not in raw:
                raw = raw.replace(
                    "Then she STANDS UP to the SAME EYE LEVEL and they fall into a deep wet 濃厚キス",
                    "HOLD STILL the thick sticky white liquid on her tongue. Then she STANDS UP to the SAME EYE LEVEL and they fall into a deep wet kiss",
                    1,
                )
                raw = raw.replace(
                    "Then she STANDS UP to the SAME EYE LEVEL and they fall into a deep wet kiss",
                    "HOLD STILL the thick sticky white liquid on her tongue. Then she STANDS UP to the SAME EYE LEVEL and they fall into a deep wet kiss",
                    1,
                )
        elif "\noverall_soundscape:" in raw:
            raw = raw.replace(
                "\noverall_soundscape:",
                f"\n{SEMEN_SHARE_BEAT}\n\noverall_soundscape:",
                1,
            )
        return _rewrite_share_stand(raw)
    if mode == "on_cumouf":
        if _STILL_IN_MOUTH_END_RE.search(raw):
            raw = _STILL_IN_MOUTH_END_RE.sub(share_end, raw, count=1)
        elif _MOUTH_STILL_ON_END_RE.search(raw):
            raw = _MOUTH_STILL_ON_END_RE.sub(share_end, raw, count=1)
        else:
            raw = raw.replace("Nobody pulls off.", f"{SEMEN_SHARE_BEAT} ")
            if "口移し" not in raw and "mouth-to-mouth" not in raw.lower() and "\noverall_soundscape:" in raw:
                raw = raw.replace(
                    "\noverall_soundscape:",
                    f"\n{SEMEN_SHARE_BEAT}\n\noverall_soundscape:",
                    1,
                )
        raw = raw.replace(
            "Mouth stays on until the last frames.",
            "Mouth stays on until the last pulses, then mouth off for mouth-to-mouth semen share.",
        )
        return _rewrite_share_stand(raw)
    if mode == "silent_next":
        raw = raw.replace("Mouth stays on the penis.", "Mouth comes off the penis.")
        raw = raw.replace("Mouth stays on.", "Mouth comes off.")
        raw = raw.replace("Mouth never leaves.", "Mouth comes off.")
        raw = raw.replace("She does not pull off.", "She pulls off, then mouth-to-mouth semen share.")
        raw = raw.replace("Do not pull off.", "Pull off, then mouth-to-mouth semen share.")
        raw = raw.replace("No pull-off.", "Pull off, then mouth-to-mouth semen share.")
        raw = raw.replace("Nobody kisses.", "")
        raw = raw.replace("Do not kiss.", "")
        if _STILL_IN_MOUTH_END_RE.search(raw):
            raw = _STILL_IN_MOUTH_END_RE.sub(share_end, raw, count=1)
        elif _MOUTH_STILL_ON_END_RE.search(raw):
            raw = _MOUTH_STILL_ON_END_RE.sub(share_end, raw, count=1)
        if "口移し" not in raw and "mouth-to-mouth" not in raw.lower() and "\noverall_soundscape:" in raw:
            raw = raw.replace(
                "\noverall_soundscape:",
                f"\n{SEMEN_SHARE_BEAT}\n\noverall_soundscape:",
                1,
            )
        return _rewrite_share_stand(raw)
    return _rewrite_share_stand(raw)


def apply_semen_share_label(label: str, *, mode: str) -> str:
    text = str(label or "")
    if mode != "silent_next" or "口移し" in text:
        return text
    swapped = re.sub(r"(抜く|離さない|咥えたまま)", "口移し", text)
    return swapped if swapped != text else text + " 口移し"


def spoken_lines(prompt: str) -> list[str]:
    return _SPOKEN_RE.findall(str(prompt or ""))


def unique_spoken_lines(prompt: str) -> list[str]:
    """First-seen order. Repeats of the same 「」 do not get a second window."""
    out: list[str] = []
    for line in spoken_lines(prompt):
        if line not in out:
            out.append(line)
    return out


_SPEAK_AFTER_DOOR_RE = re.compile(r"AFTER the door opens", re.I)
_SPEAK_FIRST_RE = re.compile(r"SPEAKS first|rings the doorbell and SPEAKS", re.I)
_LINE_WINDOW_S = 1.6
_OPENING_PAD_S = 2.0
_KISS_FORBID_RE = re.compile(
    r"No kiss yet|does not kiss|No deep kiss|does not kiss this clip",
    re.I,
)
_OPEN_MOUTH_WAIT_RE = re.compile(
    r"hand['’]s width|mouth OPEN and off|keep it OPEN",
    re.I,
)
_WRITTEN_LEFTOVER_ACT_RE = re.compile(
    r"Remaining seconds[^.]*?(drops to her knees|takes the 20cm|jupo|"
    r"French kiss|SEPARATE|STANDS UP|mouth-to-mouth|light peck|light kiss|"
    r"filthy wet|kisses on the mouth|kisses on the breasts)",
    re.I,
)
LEFTOVER_KISS_BEAT = (
    "mouths closed. No more quoted speech. No replay. "
    "Leftover: kisses on the mouth and/or breasts plus skinship "
    "(hands on breasts, waist, hips). Do not say the same line again. Do not freeze."
)


def leftover_timeline_beat(text: str, *, situation: str = "") -> str:
    """Silent leftover window after unique 「」. Kiss + skinship unless the written leftover is already an act."""
    sit = str(situation or "").strip()
    raw = str(text or "")
    if sit in ACT_SITUATIONS:
        return "Do the written remaining beat. Bodies keep moving. Do not freeze."
    if _KISS_FORBID_RE.search(raw) or _OPEN_MOUTH_WAIT_RE.search(raw):
        return (
            "Do the written remaining beat. Mouths stay closed after the last unique line. "
            "No more quoted speech. No replay. Do not freeze."
        )
    if _WRITTEN_LEFTOVER_ACT_RE.search(raw):
        return (
            "Do the written remaining beat. Mouths stay closed except that written kiss or act. "
            "No more quoted speech. No replay. Do not freeze."
        )
    return LEFTOVER_KISS_BEAT


def speech_timeline_line(text: str, *, duration_s: float = 10.0, situation: str = "") -> str:
    """Pin the 10s axis. Each unique 「」 gets one window. Leftover is kiss + skinship, not a replay."""
    try:
        dur = float(duration_s or 10.0)
    except (TypeError, ValueError):
        dur = 10.0
    if dur <= 0:
        dur = 10.0
    sit = str(situation or "").strip()
    lines = unique_spoken_lines(text)
    if sit in ACT_SITUATIONS or not lines:
        return (
            f"TIMELINE: 0.0-{dur:.1f}s one unbroken take. The written beat fills the whole take. "
            "No quoted speech. No lip-sync words. No replay. Do not freeze."
        )
    opening = "HIDDEN at the start" in text
    speak_first = bool(_SPEAK_FIRST_RE.search(text))
    speak_after_door = bool(_SPEAK_AFTER_DOOR_RE.search(text))
    pad = _OPENING_PAD_S if opening and speak_after_door and not speak_first else 0.0
    chunks: list[str] = []
    t = 0.0
    if pad > 0:
        chunks.append(
            f"0.0-{pad:.1f}s written start beat only (chime / door / enter if written). "
            "No quoted speech in this window. No replay."
        )
        t = pad
    leftover_floor = 0.8
    for i, _line in enumerate(lines, start=1):
        if t >= dur:
            break
        remain_after = len(lines) - i
        latest_end = dur - leftover_floor - remain_after * _LINE_WINDOW_S
        end = min(t + _LINE_WINDOW_S, max(t + 0.8, latest_end), dur)
        if end <= t:
            end = min(t + 0.8, dur)
        ordinal = "first" if i == 1 else "second" if i == 2 else f"number {i}"
        chunks.append(
            f"{t:.1f}-{end:.1f}s {ordinal} unique quoted speech, one time only, conversational pace. "
            "That mouth moves only here. Then it closes. Do not repeat. Do not restart. "
            "Do not stretch the words to fill time."
        )
        t = end
    if t < dur:
        chunks.append(f"{t:.1f}-{dur:.1f}s {leftover_timeline_beat(text, situation=sit)}")
    return "TIMELINE: " + " ".join(chunks)


def lock_clip_timeline(text: str, *, duration_s: float = 10.0, situation: str = "") -> str:
    """Every story clip gets a second-axis. Stops H3 from replaying the same 「」 to fill 10s."""
    raw = str(text or "")
    if not raw:
        return raw
    if "TIMELINE:" in raw:
        return raw
    return _inject_before_soundscape(
        raw, speech_timeline_line(raw, duration_s=duration_s, situation=situation)
    )


def stack_signature(stack: list[dict[str, Any]] | None) -> tuple[tuple[str, float], ...]:
    """Stable id+strength fingerprint. Used to log LoRA swaps; does not dump VRAM."""
    out: list[tuple[str, float]] = []
    for row in stack or []:
        rid = str(row.get("id") or "").strip()
        if not rid:
            continue
        raw = row.get("strength_model", row.get("strength", 0.0))
        try:
            val = round(float(raw), 3)
        except (TypeError, ValueError):
            val = 0.0
        out.append((rid, val))
    return tuple(out)


def drop_baked_turbo_loras(
    stack: list[dict[str, Any]] | None,
    unet: str,
) -> list[dict[str, Any]]:
    """Eros TURBO-hybrid already has FL2VA turbo. Larry / LightX2V FL2VA would double-distill."""
    rows = [dict(x) for x in (stack or [])]
    if not is_eros_turbo_hybrid_unet(unet):
        return rows
    return [row for row in rows if str(row.get("id") or "") not in BAKED_TURBO_LORA_IDS]


def drop_speech_face_killers(
    stack: list[dict[str, Any]] | None,
    *,
    speaks: bool,
    mode: str,
) -> list[dict[str, Any]]:
    """Lip-sync + cinema DY melts the jaw. Keep penis and synth-pussy. R2V speech keeps thin cinema (it is the act)."""
    rows = [dict(x) for x in (stack or [])]
    if not speaks:
        return rows
    mode_l = str(mode or "").strip().lower()
    out: list[dict[str, Any]] = []
    for row in rows:
        rid = str(row.get("id") or "")
        if rid in SPEECH_FACE_KILLER_IDS:
            if mode_l in {"t2v", "i2v"}:
                continue
            if mode_l == "r2v":
                thin = min(float(row.get("strength_model", row.get("strength", 0.5)) or 0.5), 0.35)
                row["strength"] = thin
                row["strength_model"] = thin
        out.append(row)
    return out


def jp_outside_quotes(text: str) -> str:
    """Japanese script left after stripping 「」. A lock line must return empty."""
    return "".join(_JP_SCRIPT_RE.findall(_SPOKEN_RE.sub("", str(text or ""))))


# Longest first. Applied only outside 「」 so spoken lines stay Japanese.
_JP_PROMPT_GLOSSARY = (
    ("ドロドロの白い液体", "heavy-oil-thick gooey sticky opaque white liquid"),
    ("ドロッドロ", "heavy-oil-thick gooey"),
    ("身を胸につける", "presses her body flush against the chest"),
    ("ジュボフェラ", "deep jupo blowjob"),
    ("シコシコオナニー", "stroking the erect penis"),
    ("ハチコウ前", "in front of Hachiko"),
    ("ハチ公前", "in front of Hachiko"),
    ("黄色い水", "yellow urine"),
    ("濃厚キス", "deep filthy wet kiss"),
    ("口移し", "mouth-to-mouth semen share"),
    ("ベロチュー", "wet tongue kiss"),
    ("ジュボ側", "woman who was sucking"),
    ("イキ顔", "climax face"),
    ("画面右手", "camera right"),
    ("シコシコ", "stroking"),
    ("ハチコウ", "Hachiko"),
    ("ハチ公", "Hachiko"),
    ("洋式便座", "western toilet"),
    ("便座", "toilet seat"),
    ("ジュボ", "jupo"),
    ("昼間", "daytime"),
    ("座ったまま", "staying seated"),
    ("昼", "daytime"),
    ("全裸の女性", "nude adult women"),
    ("全裸", "fully nude"),
    ("観客", "audience"),
    ("ベンチ", "bench"),
    ("ネットリ", "clingy sticky"),
    ("ヌルヌル", "slick and slimy"),
    ("ドロドロ", "heavy-oil-thick gooey"),
    ("おフロ", "bath"),
    ("おミズ", "water-drink pretext"),
    ("オシッコ", "pee"),
    ("ハメ役", "receiver"),
    ("竿役", "shaft"),
    ("ミズ", "water"),
)


def _apply_jp_glossary(chunk: str) -> str:
    out = str(chunk or "")
    for src, dst in _JP_PROMPT_GLOSSARY:
        out = out.replace(src, dst)
    return out


def english_except_speech(prompt: str) -> str:
    """Keep 「台詞」. Turn leftover Japanese in the picture/lock text into English.

    H3 reads Japanese outside quotes as extra spoken words. Do not add a
    'don't speak English' lock (that also gets read aloud).
    """
    raw = str(prompt or "")
    if not raw:
        return raw
    out: list[str] = []
    pos = 0
    for match in _SPOKEN_RE.finditer(raw):
        out.append(_apply_jp_glossary(raw[pos:match.start()]))
        out.append(match.group(0))
        pos = match.end()
    out.append(_apply_jp_glossary(raw[pos:]))
    return "".join(out)


_LIPSYNC_JP_LINE_RE = (
    (re.compile(r"One short conversational Japanese line, natural adult voice, not recited, not stretched\.\s*"), "Mouth moves on the quoted line. "),
    (re.compile(r"Each line is conversational, not recited, not stretched\.\s*"), ""),
    (re.compile(r"Then the mouth closes\. After the (?:line|lines): silence, but bodies keep moving\.\s*"), ""),
    (re.compile(r"After the lines: silence, but bodies keep moving\.\s*"), ""),
    (
        re.compile(
            r"Mouth closes\. Remaining seconds, silence: bodies keep moving — a look, a weight shift, skin still alive\. Do not freeze\.\s*"
        ),
        "",
    ),
    (re.compile(r"One short line only\.\s*"), ""),
    (re.compile(r"speaks one short conversational line:"), "speaks:"),
    (re.compile(r"speaks one short line with a clearly moving mouth:"), "speaks:"),
    (re.compile(r"speaks one line with a clearly moving mouth:"), "speaks:"),
    (re.compile(r"Two Japanese lines\.?\s*"), ""),
    (re.compile(r"One Japanese line from \w+ only\.?\s*"), ""),
    (re.compile(r"speaks (?:her|his) Japanese line first"), "mouth moves on the quoted line first"),
    (re.compile(r"\bJapanese line\b"), "quoted line"),
)


def strip_lipsync_speech_meta(prompt: str) -> str:
    """Drop 'Japanese line' / recitation notes that H3 reads aloud. Keep 「」."""
    text = str(prompt or "")
    for rx, repl in _LIPSYNC_JP_LINE_RE:
        text = rx.sub(repl, text)
    return text


ACT_SILENCE_LINE = (
    "ACT SILENCE: No spoken Japanese. Do not add a new quoted line. "
    "Do not lip-sync words. Mouths do the act. "
    "KEEP wet sounds loud and audible: filthy jupo-jupo on the penis, wet chu kisses, "
    "saliva-lick slurp, and leaked female moans. Not words. Do not mute them."
)
ACT_SFX_LINE = (
    "ACT SFX: Keep wet sounds loud and audible: filthy jupo-jupo on the penis, "
    "wet chu kisses, saliva-lick slurp, and leaked female moans. Not words. Do not mute them."
)
ORAL_ACT_SFX = (
    "Loud wet filthy jupo-jupo on the penis, saliva slurp, leaked female moans, hitching breath."
)
CUMOUF_ACT_SFX = (
    "Wet in-mouth pulses, saliva slurp, leaked female moans, hitching breath."
)
CUNNI_ACT_SFX = (
    "Wet tongue licks on the pussy, saliva slurp, leaked female moans, hitching breath."
)
SEX_ACT_SFX = (
    "Wet filthy thrusting, leaked female moans, hitching breath."
)
URINE_ACT_SFX = (
    "Hiss of a yellow urine stream leaving the urethral opening at the glans tip. "
    "Wet splash. Not words."
)
SCAT_ACT_SFX = (
    "Wet sounds of feces leaving the anus now. Not a pre-coated body. Not words."
)
KISS_ACT_SFX = (
    "Wet chu kisses, saliva slurp, leaked female moans, hitching breath."
)
HAND_ACT_SFX = (
    "Wet stroking, leaked female moans, hitching breath."
)
PULSE_ACT_SFX = (
    "Wet pulses, leaked female moans, hitching breath."
)
_KISS_SFX_RE = re.compile(
    r"mouth-to-mouth|SEMEN SHARE|deep kiss|filthy wet kiss|tongue kiss|wet chu",
    re.I,
)


def lock_act_silent(text: str, *, situation: str = "") -> str:
    """Jupo / in-mouth / sex / cunni stay mute. Do not add 「」. Common to every story."""
    raw = str(text or "")
    sit = str(situation or "").strip()
    if not raw or sit not in ACT_SITUATIONS:
        return raw
    out = _SPOKEN_RE.sub("", raw)
    out = strip_lipsync_speech_meta(out)
    out = re.sub(r"[ \t]+\n", "\n", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    if "ACT SILENCE:" not in out:
        out = _inject_before_soundscape(out, ACT_SILENCE_LINE)
    return out


def act_sfx_extra(text: str, *, situation: str = "") -> str:
    """English wet SFX only. No 「」. Jupo / chu / saliva / leaked moans."""
    sit = str(situation or "").strip()
    raw = str(text or "")
    if sit in ACT_SITUATIONS:
        if sit in {"oral", "futa_blowjob"}:
            extra = ORAL_ACT_SFX
        elif sit == "oral_creampie":
            extra = CUMOUF_ACT_SFX
        elif sit == "cunnilingus_futa":
            extra = CUNNI_ACT_SFX
        elif sit in SEX_INSIDE_SITUATIONS:
            extra = SEX_ACT_SFX
        elif sit in URINE_SITUATIONS:
            extra = URINE_ACT_SFX
        elif sit == "scat_act":
            extra = SCAT_ACT_SFX
        elif sit in {"fingering", "masturbation", "futa_masturbation"}:
            extra = HAND_ACT_SFX
        elif sit in {"facial", "after_ejaculation"}:
            extra = PULSE_ACT_SFX
        else:
            extra = "Leaked female moans, hitching breath."
        if _KISS_SFX_RE.search(raw) and "chu" not in extra.lower():
            extra = extra + " " + KISS_ACT_SFX
        return extra
    if spoken_lines(raw):
        return ""
    if _KISS_SFX_RE.search(raw):
        return KISS_ACT_SFX
    return ""


def _soundscape_needs_sfx(body: str, extra: str) -> bool:
    if not extra:
        return False
    blob = str(body or "").lower()
    if extra.lower() in blob:
        return False
    tokens = []
    el = extra.lower()
    for tok in ("jupo-jupo", "chu", "saliva", "lick", "thrust", "moan"):
        if tok in el:
            tokens.append(tok)
    if tokens and all(tok in blob for tok in tokens):
        return False
    return True


def lock_act_sfx(text: str, *, situation: str = "") -> str:
    """Act clips stay wordless. Jupo / chu / saliva / leaked moans stay loud. Every story."""
    raw = str(text or "")
    sit = str(situation or "").strip()
    if not raw:
        return raw
    if _URINE_CUE_RE.search(raw) and sit in {"oral", "futa_blowjob"}:
        return raw
    extra = act_sfx_extra(raw, situation=sit)
    if not extra:
        return raw
    out = raw
    if sit not in ACT_SITUATIONS and "ACT SFX:" not in out and "KEEP wet sounds loud" not in out:
        out = _inject_before_soundscape(out, ACT_SFX_LINE)
    if _soundscape_needs_sfx(soundscape_text(out), extra):
        out = _append_soundscape(out, extra)
    return out


def strip_audio_lock(prompt: str) -> str:
    """Drop a previous audio lock (JP 音声ルール or ASCII only-say-the-line flags)."""
    text = _AUDIO_LOCK_LINE_RE.sub("", str(prompt or ""))
    text = _OLD_JP_AUDIO_LOCK_RE.sub("", text)
    text = _JP_SPEECH_ONLY_RE.sub("", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def soundscape_bounds(prompt: str) -> tuple[int, int] | None:
    """Body of overall_soundscape, after the label, until the next canonical section."""
    marker = "overall_soundscape:"
    idx = str(prompt or "").find(marker)
    if idx < 0:
        return None
    start = idx + len(marker)
    nxt = _NEXT_AFTER_SOUND_RE.search(prompt, start)
    end = nxt.start() if nxt else len(prompt)
    return start, end


def soundscape_text(prompt: str) -> str:
    span = soundscape_bounds(prompt)
    if span is None:
        return ""
    return str(prompt)[span[0] : span[1]]


def _collapse_quotes_in(chunk: str, lines: list[str] | None) -> str:
    out = str(chunk or "")
    for ln in lines or []:
        token = f"「{ln}」"
        first = out.find(token)
        if first < 0:
            continue
        out = out[: first + len(token)] + out[first + len(token) :].replace(token, "")
    return out


def collapse_spoken_quotes(text: str, lines: list[str] | None) -> str:
    """Keep one 「line」 in the picture block and one in the soundscape.

    Whole-prompt collapse used to delete the soundscape copy and leave
    'speaks, lip-synced: . No other speech' as the audio — H3 read that English.
    """
    raw = str(text or "")
    span = soundscape_bounds(raw)
    if span is None:
        return _collapse_quotes_in(raw, lines)
    start, end = span
    return (
        _collapse_quotes_in(raw[:start], lines)
        + _collapse_quotes_in(raw[start:end], lines)
        + _collapse_quotes_in(raw[end:], lines)
    )


def strip_soundscape_speech_meta(body: str) -> str:
    """Drop TTS fodder. Keep SFX and 「」. Do not write 'only say the line'."""
    text = str(body or "")
    if not text.strip():
        return text
    text = _SOUND_SPEAKER_RE.sub("", text)
    text = _SOUND_LIPSYNC_RE.sub("", text)
    text = _SOUND_THEN_QUOTE_RE.sub("」「", text)
    for rx in _SOUND_META_RES:
        text = rx.sub("", text)
    text = _SOUND_VOICE_META_RE.sub("", text)
    text = _SOUND_THEN_ONLY_RE.sub("", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\s+([.,;:])", r"\1", text)
    text = re.sub(r",\s*,+", ",", text)
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r",(?:\s*\.)+", ".", text)
    lines = [ln.strip(" ,;:-") for ln in text.split("\n")]
    return "\n".join(ln for ln in lines if ln)


def sanitize_story_soundscape(prompt: str) -> str:
    """overall_soundscape is the audio channel. Strip speech-direction English."""
    raw = str(prompt or "")
    span = soundscape_bounds(raw)
    if span is None:
        return raw
    start, end = span
    body = strip_soundscape_speech_meta(raw[start:end])
    if body and not body.startswith("\n"):
        body = "\n" + body
    if body and not body.endswith("\n") and end < len(raw):
        body += "\n"
    elif not body and end < len(raw):
        body = "\n"
    return raw[:start] + body + raw[end:]


def _put_quotes_in_soundscape(prompt: str, lines: list[str]) -> str:
    """Audio channel needs the 「」. Visemes may already have a copy in LIP SYNC."""
    wanted = [str(x).strip() for x in lines if str(x).strip()]
    if not wanted:
        return prompt
    raw = str(prompt or "")
    span = soundscape_bounds(raw)
    quotes = " ".join(f"「{ln}」" for ln in wanted if f"「{ln}」" not in soundscape_text(raw))
    if not quotes:
        return raw
    if span is None:
        return raw.rstrip() + "\n" + quotes
    start, end = span
    body = raw[start:end].rstrip()
    if body and not body.endswith("\n"):
        body += "\n"
    body = (body + quotes).rstrip() + "\n"
    if not body.startswith("\n"):
        body = "\n" + body
    return raw[:start] + body + raw[end:]


def audio_lock_line(lines: list[str] | None, *, transcript: str | None = None) -> str:
    """Retracted. The old ASCII lock (other_text: not_spoken) was spoken as dialogue."""
    return ""


def lock_spoken_japanese(prompt: str, lines: list[str] | None = None) -> str:
    """Soundscape = SFX + 「」. Do not add 'only say the line' (H3 TTS'd that).

    Collapse extras per section so the audio channel keeps its quote. Strip old
    JP/ASCII locks. Missing quotes are written into the soundscape, never a lock.
    """
    raw = str(prompt or "")
    spoken = list(lines) if lines is not None else spoken_lines(raw)
    text = strip_audio_lock(raw)
    if not spoken:
        spoken = spoken_lines(text)
    text = sanitize_story_soundscape(text)
    text = collapse_spoken_quotes(text, spoken)
    text = _put_quotes_in_soundscape(text, spoken)
    text = strip_lipsync_speech_meta(text)
    text = english_except_speech(text)
    return text


def story_cast_present(prompt: str) -> list[str]:
    """Names with a full subject_definitions line in this prompt (packs add Saleswoman / Doctor / Conductor)."""
    out: list[str] = []
    for name in STORY_CAST_DEF_RE.findall(str(prompt or "")):
        if name not in out:
            out.append(name)
    return out


def compact_story_prompt(prompt: str) -> str:
    """Trim what the model cannot use, keep every instruction it can.

    Each story clip is an independent generation, so the encoder never sees the
    previous clip or the other stories. Lines that only make sense to a human
    editor ("Do not copy the previous clip", "Clip 7 of 12", the list of other
    story names in CAST LOCK) are dropped. Full body descriptions of women who
    are NOT IN FRAME are removed: describing an absent nude woman in detail is
    the strongest pull to render her. The result is put back in the canonical
    H3 order (subject_definitions, environment, integrated_multimodal_description,
    overall_soundscape, non_diegetic_music) with WHO blocking and the HARD LOCK /
    CAMERA / LIP SYNC lines folded into the description block.
    Prompts without the five canonical keys only get the line-level cleanup.
    """
    text = str(prompt or "").strip()
    if not text:
        return text
    text = lock_futa_anatomy(text)
    preamble: list[str] = []
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw in text.split("\n"):
        line = raw.rstrip()
        match = _STORY_SECTION_RE.match(line)
        if match:
            current = match.group(1)
            sections.setdefault(current, [])
            rest = match.group(2).strip()
            if rest:
                sections[current].append(rest)
            continue
        if current is None:
            preamble.append(line)
        else:
            sections[current].append(line)

    def clean(rows: list[str]) -> list[str]:
        out: list[str] = []
        for row in rows:
            s = row.strip()
            if not s or _META_TAKE_RE.match(s):
                continue
            s = _CLIP_INDEX_RE.sub("", s).strip()
            s = _CAST_STORIES_RE.sub(CAST_LOCK_SERIES_LINE, s)
            if s:
                out.append(s)
        return out

    if not all(key in sections for key in STORY_CANON_KEYS):
        rows = clean(text.split("\n"))
        return "\n".join(rows)

    absent: list[str] = []
    who_keep: list[str] = []
    for row in clean(sections.get("WHO") or []):
        hit = _ABSENT_WHO_RE.match(row)
        if hit:
            if hit.group(1) not in absent:
                absent.append(hit.group(1))
            continue
        who_keep.append(row)
    defs_keep: list[str] = []
    for row in clean(sections.get("subject_definitions") or []):
        hit = _ABSENT_DEF_RE.match(row)
        if hit:
            if hit.group(1) not in absent:
                absent.append(hit.group(1))
            continue
        name = row.split(":", 1)[0].strip()
        if name in absent:
            continue
        defs_keep.append(row)

    out: list[str] = []
    out.extend(clean(preamble))
    out.append("")
    out.append("subject_definitions:")
    out.extend(defs_keep)
    if absent:
        out.append("Not in this clip: " + ", ".join(absent) + ".")
    out.append("")
    out.append("environment:")
    out.extend(clean(sections.get("environment") or []))
    out.append("")
    out.append("integrated_multimodal_description:")
    out.extend(who_keep)
    out.extend(clean(sections.get("integrated_multimodal_description") or []))
    out.extend(clean(sections.get("HARD LOCK") or []))
    out.append("")
    out.append("overall_soundscape:")
    sound = strip_soundscape_speech_meta("\n".join(clean(sections.get("overall_soundscape") or [])))
    if sound:
        out.append(sound)
    out.append("")
    out.append("non_diegetic_music:")
    out.extend(clean(sections.get("non_diegetic_music") or []) or ["N/A"])
    return "\n".join(out).strip()


_CAST_DEF = {
    "Aya": (
        "Aya: Adult Japanese woman, 22, second daughter, 150cm, petite adult, narrow cinched waist, "
        "slim hips, slim thighs, slim ass, mini breasts, glossy black twintails, pretty adult face, "
        "fully nude, hairless, NO penis, NEVER futanari. Adult 22, not a child."
    ),
    "Rei": (
        "Rei: Adult Japanese woman, 24, eldest daughter, slim female body, medium breasts, "
        "long dark-brown hair, fully nude. Clear futanari. Erect 20cm, pale shaft, pink glans, "
        "no testicles, no scrotum. Hairless female pussy at the base of the shaft where a scrotum "
        "would be. Penis plus vagina, never balls."
    ),
    "Madoka": (
        "Madoka: Adult Japanese woman, 22, third daughter, slim body, flat breasts, slim waist, "
        "slim thighs, short wavy chestnut hair, different face from Rei, fully nude. Clear futanari. "
        "Erect 20cm, pale shaft, pink glans, no testicles, no scrotum. Hairless female pussy at the "
        "base of the shaft where a scrotum would be. Penis plus vagina, never balls."
    ),
    "Sayaka": (
        "Sayaka: Adult Japanese woman, 39, mother, slim mature female body, medium breasts, "
        "long black hair tied back, fully nude, hairless, NO penis, NEVER futanari."
    ),
    "Saleswoman": (
        "Saleswoman: Adult Japanese woman, 25, door-to-door water saleswoman, short black bob hair, "
        "medium breasts, slim waist, fully nude except a small name badge on a neck strap. "
        "Clear futanari. Erect 20cm, pale shaft, pink glans, no testicles, no scrotum. "
        "Hairless female pussy at the base of the shaft where a scrotum would be. "
        "Penis plus vagina, never balls."
    ),
    "Instructor": (
        "Instructor: Adult Japanese woman, 29, yoga instructor, slim toned female body, medium breasts, "
        "long black hair in a bun, fully nude. Clear futanari. Erect 20cm, pale shaft, pink glans, "
        "no testicles, no scrotum. Hairless female pussy at the base of the shaft where a scrotum "
        "would be. Penis plus vagina, never balls."
    ),
}


_SHORTS_CAM_ORAL_STAND = (
    "medium-close two-shot. Show the kneeling mouth from head to knees and the standing shaft "
    "from head to mid-thigh in the same 9:16 frame. Face, breasts, hips, and the 20cm in the mouth "
    "all readable. Not a mouth-only crop. Not a street-wide shot that shrinks faces."
)
_SHORTS_CAM_ORAL_TABLE = (
    "medium-close two-shot under the table. Show the kneeling mouth from head to knees and the "
    "sitting hips-to-knees with the 20cm in the mouth. Face, breasts, and shaft readable. "
    "Not a mouth-only crop. Not a room-wide."
)
_SHORTS_CAM_CUNNI = (
    "close-up on the tongue on the hairless pussy at the base of the unused 20cm. Extreme close. "
    "Show the hips, unused shaft, and the licking face. Do not pull back to a street-wide full-body."
)
_SHORTS_CAM_SEX_169 = (
    "16:9 two-shot. Full bodies from head to feet fit in the 16:9 frame. Joining point stays readable "
    "at the hips. Do not crop to genitals only."
)
_SHORTS_CAM_SEX_916_STAND = (
    "9:16 two-shot. Full bodies from head to feet stacked in the 9:16 frame. "
    "Joining point stays readable at hip height. Do not crop to genitals only."
)


def _anthology_prompt(
    *,
    prefix: str,
    who: str,
    present: tuple[str, ...],
    environment: str,
    lock: str,
    camera: str,
    action: str,
    sound: str,
    canvas: dict[str, Any],
) -> str:
    defs = "\n".join(_CAST_DEF[n] for n in present)
    w, h = story_canvas_wh({"canvas": canvas})
    if w >= h:
        frame = f"Widescreen 16:9 {w}x{h}"
        cam_tag = "16:9"
    else:
        frame = f"Vertical 9:16 {w}x{h}"
        cam_tag = "9:16"
    absent = [n for n in SHORTS_MAIN4 if n not in present]
    who_full = who.rstrip()
    if absent:
        who_full += "\n" + "\n".join(f"{n} = NOT IN FRAME." for n in absent)
    body = (
        f"{frame}. ONE UNBROKEN 10-second take. The camera never cuts.\n"
        f"{prefix}\n\n"
        "WHO:\n"
        f"{who_full}\n\n"
        "subject_definitions:\n"
        f"{defs}\n\n"
        "environment:\n"
        f"{environment}\n\n"
        "HARD LOCK:\n"
        f"{lock}\n"
        f"CAMERA: {cam_tag} {camera}\n"
        "No men. No feces. All performers are consenting adult women 22 years or older. Nobody under 22.\n"
        "CAST LOCK: Same faces, hair and bodies in every clip of this series. "
        "Do not redesign hair or breasts. Aya never grows a penis. Sayaka never grows a penis.\n\n"
        "integrated_multimodal_description:\n"
        f"{action}\n\n"
        "overall_soundscape:\n"
        f"{sound}\n\n"
        "non_diegetic_music:\n"
        "N/A"
    )
    return lock_semen_look(lock_futa_shaft(lock_futa_anatomy(body)))


def generate_immoral_shorts() -> dict[str, Any]:
    """12 independent 10s dirty daily shorts. Prompts and LoRA situations are built here, no LLM."""
    specs = (
        {
            "id": "s01-genkan-bj",
            "label": "玄関・サヤカがレイをジュボ",
            "situation": "oral",
            "names": ["sayaka", "rei"],
            "present": ("Sayaka", "Rei"),
            "canvas": CANVAS_9_16,
            "prefix": "Already oral. Mouth already on. Already kneeling.",
            "who": (
                "Sayaka = kneeling in the genkan. She is the mouth (ハメ役). Mother, 39. Medium breasts. "
                "NO penis. Hands on Rei's waist, NEVER on any penis. Thick saliva already on her chin and breasts.\n"
                "Rei = STANDS in the genkan. She is the shaft (竿役). Eldest daughter. Filthy pleasured face "
                "because her mother's mouth is already at the base of her 20cm."
            ),
            "environment": (
                "Daytime genkan of a two-story Japanese house, front door half-open, shoes kicked aside. "
                "Tile and the open street are only background."
            ),
            "lock": (
                "Already on. Mother sucks her daughter's 20cm to the BASE the whole 10-second take. "
                "Filthy sloppy jupo. Drool ropes. No climax. No speech."
            ),
            "camera": _SHORTS_CAM_ORAL_STAND,
            "action": (
                "Already on. Sayaka's mouth is already at Rei's base in the open genkan, like this is everyday. "
                "Deep filthy jupo-jupo the whole 10-second take. Thick saliva ropes swing from her lips onto "
                "her breasts. Rei's unused pussy at the base of the shaft is wet against Sayaka's nose. "
                "Rei's head tips back, hips dirty. End: mouth still at the base, still medium-close two-shot."
            ),
            "sound": "Deep filthy jupo-jupo, wet saliva, Rei's shaky breath, a distant street.",
        },
        {
            "id": "s02-sink-mouth",
            "label": "シンク・アヤがレイの口内",
            "situation": "oral_creampie",
            "names": ["aya", "rei"],
            "present": ("Aya", "Rei"),
            "canvas": CANVAS_9_16,
            "prefix": "Already oral. Mouth already wrapped around the shaft. Already kneeling by the sink.",
            "who": (
                "Aya = kneeling at the kitchen sink. She is the mouth (ハメ役). Lips wrapped tight around "
                "Rei's 20cm. Mini breasts. NO penis. Chin already shiny with spit.\n"
                "Rei = stands at the sink. She is the shaft (竿役). Holds deep and cums inside Aya's mouth. "
                "イキ顔, coming hard, eyes half-closed, mouth open."
            ),
            "environment": (
                "Kitchen sink, daytime, dirty dishes piled, water still running. The sink is only background."
            ),
            "lock": (
                "CUMOUF. Viscous sticky white liquid (ドロドロの白い液体) floods Aya's mouth and runs out the side "
                "onto her mini breasts. Opaque white liquid, not clear. Inside the mouth. Not a facial. No speech."
            ),
            "camera": _SHORTS_CAM_ORAL_STAND,
            "action": (
                "Aya's lips stay wrapped around Rei's 20cm at the sink. Rei grips the counter and cums hard "
                "inside her little sister's mouth. Viscous sticky white liquid (ドロドロの白い液体) floods the mouth, "
                "overflows down the shaft as thick opaque white gooey strands onto Aya's chin and mini breasts. "
                "Messy swallows, more white liquid leaking than she can keep. "
                "After the last pulse: mouth off. HOLD STILL a fat overflowing mouthful she cannot hold of "
                "clingy sticky extra-viscous molasses-slow opaque white liquid flooding the tongue, viscous (ドロドロ). "
                "TOO MUCH. It floods. Overflow spills in fat curtains onto chin, lips, and breasts and STAYS in piled layers. "
                "The glans tip keeps drooling white liquid so the shaft is ヌルヌル. "
                "The woman who was sucking STANDS UP to the partner's SAME EYE LEVEL. "
                f"{SEMEN_SHARE_KISS} "
                "Do not kiss from the knees. End: standing at the SAME EYE LEVEL, tongues wrapping the heavy white liquid, not still on the shaft."
            ),
            "sound": "Wet swallows, a pulse, cum overflow, Rei's shaky breath, running water.",
        },
        {
            "id": "s03-alley-base",
            "label": "路地・アヤがレイを根元",
            "situation": "oral",
            "names": ["aya", "rei"],
            "present": ("Aya", "Rei"),
            "canvas": CANVAS_9_16,
            "prefix": "Already oral. Mouth already on. Already kneeling in the alley.",
            "who": (
                "Aya = kneeling on the alley concrete. She is the mouth (ハメ役). Mini breasts. NO penis. "
                "Hands on Rei's waist. Spit already pooling between her knees.\n"
                "Rei = STANDS against the alley wall. She is the shaft (竿役). Receiver, filthy pleasured face, "
                "head back, eyes half-closed, enjoying the jupo."
            ),
            "environment": (
                "Narrow residential alley, daytime shade, anyone could pass. Wall and concrete are only background."
            ),
            "lock": "Already on. Aya takes Rei to the BASE. Filthy outdoor jupo. Saliva on the concrete. No climax. No speech. Nobody walks away.",
            "camera": _SHORTS_CAM_ORAL_STAND,
            "action": (
                "Already on. Aya's mouth is already a ring around Rei's shaft at the base, deep filthy jupo-jupo the whole "
                "10-second take. Thick saliva strings drop onto the concrete between her knees. Rei's unused pussy "
                "is wet at Aya's nose. Rei's knees soften, hips dirty. End: mouth still at the base."
            ),
            "sound": "Deep filthy jupo-jupo, saliva hitting concrete, a distant bicycle, Rei's breath.",
        },
        {
            "id": "s04-toilet-cunni",
            "label": "トイレ・サヤカがレイのマンコ舐め",
            "situation": "cunnilingus_futa",
            "names": ["sayaka", "rei"],
            "present": ("Sayaka", "Rei"),
            "canvas": CANVAS_9_16,
            "prefix": "Already oral on the pussy, not the penis. Already kneeling.",
            "who": (
                "Sayaka = kneeling in the home toilet. She is the mouth (ハメ役). Tongue on Rei's hairless pussy "
                "at the base of the unused 20cm. Medium breasts. NO penis. Chin wet.\n"
                "Rei = sits on the toilet lid. She is the shaft (竿役) but the 20cm hangs unused forward. "
                "Receiver of cunnilingus. Filthy pleasured face."
            ),
            "environment": "Home western toilet, door ajar, warm interior light. Extreme close on the tongue and pussy.",
            "lock": "Cunnilingus only. Not oral on the penis. The 20cm hangs unused. Close-up. No speech. No insertion.",
            "camera": _SHORTS_CAM_CUNNI,
            "action": (
                "Sayaka licks her daughter's hairless pussy at the base of the unused 20cm the whole 10-second take. "
                "The penis hangs unused in the upper frame, not in the mouth, already shiny. Sayaka's tongue is messy, "
                "wet, greedy. Rei's thighs tremble, juices on Sayaka's chin. End: tongue still on the pussy, 20cm still unused."
            ),
            "sound": "Wet filthy licking, Rei's high breath, a toilet-room echo.",
        },
        {
            "id": "s05-rooftop-in",
            "label": "屋上・レイがアヤに挿入",
            "situation": "futa_sex",
            "names": ["rei", "aya"],
            "present": ("Aya", "Rei"),
            "canvas": CANVAS_9_16,
            "prefix": "Already having sex. Already in from the first frame.",
            "who": (
                "Rei = STANDS on the rooftop. She is the shaft (竿役). Already inside Aya. Hands on Aya's ass.\n"
                "Aya = standing, one leg hooked on Rei's hip, receiving (ハメ役). Mini breasts. NO penis. "
                "Juices already on her thighs."
            ),
            "environment": (
                "University rooftop at noon, fence behind them, city only background. Two standing bodies fill 9:16."
            ),
            "lock": "ALREADY IN. Standing vaginal. Joining point visible. They move. Sweat. No speech. Do not show the entry. Do not pull out.",
            "camera": _SHORTS_CAM_SEX_916_STAND,
            "action": (
                "Already in. Rei's 20cm is already buried in Aya's hairless pussy standing at the rooftop fence. "
                "They fuck the whole 10-second take, dirty noon sweat, juices running down Aya's standing thigh. "
                "The joining point stays readable at hip height. Aya's mouth hangs open with a moan, not speaking words. "
                "End: still inside, still moving, both full bodies still in frame."
            ),
            "sound": "Wet filthy thrusting, Aya's female moan, rooftop wind.",
        },
        {
            "id": "s06-bath-bj",
            "label": "洗い場・サヤカがマドカをジュボ",
            "situation": "oral",
            "names": ["sayaka", "madoka"],
            "present": ("Sayaka", "Madoka"),
            "canvas": CANVAS_9_16,
            "prefix": "Already oral. Mouth already on. Already kneeling on the bath tiles.",
            "who": (
                "Sayaka = kneeling in the wash place. She is the mouth (ハメ役). Wet medium breasts. NO penis. "
                "Hands on Madoka's waist. Water and spit mixed on her chest.\n"
                "Madoka = STANDS under the shower. She is the shaft (竿役). Wet 20cm. Filthy pleasured face."
            ),
            "environment": "Japanese bath wash place, wet tile, shower running. Steam. Tile is only background.",
            "lock": "Already on. Mother sucks her third daughter's 20cm to the BASE under the shower. Filthy wet jupo. No climax. No speech.",
            "camera": _SHORTS_CAM_ORAL_STAND,
            "action": (
                "Already on. Water runs over Sayaka's tied hair while her mouth stays at Madoka's base. "
                "Deep filthy jupo-jupo the whole 10-second take. Spit and shower water rope off her lips onto "
                "her breasts. Madoka's unused pussy is wet at Sayaka's nose. End: mouth still at the base, still medium-close two-shot."
            ),
            "sound": "Shower, filthy jupo-jupo, Madoka's breath.",
        },
        {
            "id": "s07-table-mouth",
            "label": "食卓下・アヤがマドカの口内",
            "situation": "oral_creampie",
            "names": ["aya", "madoka"],
            "present": ("Aya", "Madoka"),
            "canvas": CANVAS_9_16,
            "prefix": "Already oral under the table. Mouth already wrapped around the shaft.",
            "who": (
                "Aya = under the dining table on her knees. She is the mouth (ハメ役). Lips wrapped tight around "
                "Madoka's 20cm. Mini breasts. NO penis.\n"
                "Madoka = sits at the table. She is the shaft (竿役). Holds deep and cums inside Aya's mouth "
                "while dinner is still on the table. イキ顔, coming hard, eyes half-closed."
            ),
            "environment": "Japanese dining table, evening, bowls still out. Tight under the table. Dishes only background.",
            "lock": (
                "CUMOUF under the table during dinner. Viscous sticky white liquid (ドロドロの白い液体) floods Aya's mouth. "
                "Opaque white liquid, not clear. Inside the mouth. Not a facial. No speech."
            ),
            "camera": _SHORTS_CAM_ORAL_TABLE,
            "action": (
                "Under the family table Aya's lips stay wrapped around Madoka's 20cm. Madoka cums inside her sister's "
                "mouth while the dinner bowls sit above. Viscous sticky white liquid (ドロドロの白い液体) floods the mouth "
                "and runs down the shaft onto the tatami edge as thick opaque white gooey strands. Messy swallows. "
                "After the last pulse: mouth off. HOLD STILL a fat overflowing mouthful she cannot hold of "
                "clingy sticky extra-viscous molasses-slow opaque white liquid flooding the tongue, viscous (ドロドロ). "
                "TOO MUCH. It floods. Overflow spills in fat curtains onto chin, lips, and breasts and STAYS in piled layers. "
                "The glans tip keeps drooling white liquid so the shaft is ヌルヌル. "
                "The woman who was sucking STANDS UP to the partner's SAME EYE LEVEL. "
                f"{SEMEN_SHARE_KISS} "
                "Do not kiss from the knees. End: standing at the SAME EYE LEVEL, tongues wrapping the heavy white liquid, not still on the shaft."
            ),
            "sound": "Wet swallows, a chair creak, Madoka's breath, a bowl clink.",
        },
        {
            "id": "s08-futon-in",
            "label": "布団・レイがサヤカに挿入",
            "situation": "futa_sex",
            "names": ["rei", "sayaka"],
            "present": ("Sayaka", "Rei"),
            "canvas": CANVAS_16_9,
            "prefix": "Already having sex. Already in from the first frame.",
            "who": (
                "Rei = on the futon. She is the shaft (竿役). Already inside her mother. Hands on Sayaka's waist.\n"
                "Sayaka = on her back on the futon, receiving (ハメ役). Medium breasts. NO penis. "
                "Sweaty, already used, juices on her thighs."
            ),
            "environment": "Japanese bedroom futon at night, blanket kicked off. Two full bodies fit in 16:9. Room is only background.",
            "lock": "ALREADY IN. Vaginal only. Joining point visible. They move. Sweaty dirty futon. No speech. Do not pull out.",
            "camera": _SHORTS_CAM_SEX_169,
            "action": (
                "Already in. Rei's 20cm is already buried in Sayaka's hairless pussy on the futon. Mother and eldest "
                "daughter fuck the whole 10-second take. Sweat, wet slaps, juices on the sheet. The joining point stays "
                "readable at the hips. Both full bodies stay in the 16:9 frame. End: still inside, still moving."
            ),
            "sound": "Wet filthy thrusting, futon rustle, Sayaka's female moan.",
        },
        {
            "id": "s09-sofa-in",
            "label": "ソファ・レイがアヤに挿入",
            "situation": "futa_sex",
            "names": ["rei", "aya"],
            "present": ("Aya", "Rei"),
            "canvas": CANVAS_16_9,
            "prefix": "Already having sex. Sofa vaginal. Already in from the first frame.",
            "who": (
                "Rei = SEATED CENTER sofa. She is the shaft (竿役). Already inside Aya. Holds Aya's waist.\n"
                "Aya = already straddling Rei on the sofa, receiving (ハメ役). Mini breasts. NO penis. "
                "Juices already on Rei's lap."
            ),
            "environment": "Living-room sofa, afternoon light, TV on ignored. Two full bodies fit in 16:9.",
            "lock": "ALREADY IN. Vaginal only. Joining point visible. They move. Messy sofa. No speech. Do not pull out.",
            "camera": _SHORTS_CAM_SEX_169,
            "action": (
                "Already in. Rei's 20cm is already buried in Aya's hairless pussy on the sofa. Sisters fuck the whole "
                "10-second take. Wet slaps, juices on the cushion, Aya's mini breasts bouncing. The joining point stays "
                "readable. Both full bodies stay in the 16:9 frame. End: still inside, still moving."
            ),
            "sound": "Wet filthy thrusting, Aya's female moan, TV far.",
        },
        {
            "id": "s10-engawa-in",
            "label": "縁側・マドカがアヤに挿入",
            "situation": "futa_sex",
            "names": ["madoka", "aya"],
            "present": ("Aya", "Madoka"),
            "canvas": CANVAS_16_9,
            "prefix": "Already having sex. Already in from the first frame.",
            "who": (
                "Madoka = already inside Aya on the engawa. She is the shaft (竿役). Hands on Aya's waist.\n"
                "Aya = receiving on the engawa (ハメ役), mini breasts. NO penis. Sweat, juices on the wood."
            ),
            "environment": "Wooden engawa, afternoon garden light. Two full bodies fit in 16:9. Garden is only background.",
            "lock": "ALREADY IN. Vaginal only. Joining point visible. Madoka's 20cm. No speech. Rei is not in this clip.",
            "camera": _SHORTS_CAM_SEX_169,
            "action": (
                "Already in. Madoka's 20cm is already buried in Aya's hairless pussy on the engawa, anyone in the garden "
                "could see. They fuck the whole 10-second take. Sweat, wet slaps on wood, juices dripping. The joining "
                "point stays readable. Both full bodies stay in the 16:9 frame. End: still inside, still moving."
            ),
            "sound": "Wet filthy thrusting, cicadas far, Aya's female moan.",
        },
        {
            "id": "s11-kitchen-doggy",
            "label": "台所・マドカがサヤカに後背",
            "situation": "doggy",
            "names": ["madoka", "sayaka"],
            "present": ("Sayaka", "Madoka"),
            "canvas": CANVAS_16_9,
            "prefix": "Already having sex. Already in from the first frame.",
            "who": (
                "Madoka = kneeling behind Sayaka on the kitchen floor. She is the shaft (竿役). ALREADY INSIDE "
                "Sayaka's hairless pussy from the first frame. Hands on Sayaka's waist.\n"
                "Sayaka = on all fours on the kitchen floor, receiving (ハメ役). Medium breasts hanging. NO penis. "
                "Cooking abandoned."
            ),
            "environment": "Home kitchen floor, pots on the stove ignored. Two full bodies fit in 16:9. Kitchen is only background.",
            "lock": "ALREADY IN from behind. Joining point visible. Doggy. Vaginal only. No speech. Do not show the entry.",
            "camera": _SHORTS_CAM_SEX_169,
            "action": (
                "Already in. Madoka's 20cm is already buried in her mother's hairless pussy from behind on the kitchen "
                "floor. Filthy doggy the whole 10-second take. Wet slaps, hanging breasts, juices on the tile. The joining "
                "point stays readable. Both full bodies stay in the 16:9 frame. End: still joined, still moving."
            ),
            "sound": "Wet filthy thrusting, Sayaka's female moan, a pot lid far.",
        },
        {
            "id": "s12-hall-stand",
            "label": "廊下・マドカがサヤカに立ち挿入",
            "situation": "futa_sex",
            "names": ["madoka", "sayaka"],
            "present": ("Sayaka", "Madoka"),
            "canvas": CANVAS_9_16,
            "prefix": "Already having sex. Already in from the first frame.",
            "who": (
                "Madoka = STANDS in the hallway. She is the shaft (竿役). Already inside Sayaka against the wall. "
                "Hands on Sayaka's ass.\n"
                "Sayaka = standing, back to the wall, one leg up, receiving (ハメ役). Medium breasts. NO penis. "
                "Anyone could walk the hall."
            ),
            "environment": "Narrow house hallway, afternoon. Two standing bodies fill 9:16. Doors are only background.",
            "lock": "ALREADY IN. Standing vaginal. Joining point visible. They move. No speech. Do not show the entry. Do not pull out.",
            "camera": _SHORTS_CAM_SEX_916_STAND,
            "action": (
                "Already in. Madoka's 20cm is already buried in Sayaka's hairless pussy standing against the hallway wall. "
                "They fuck the whole 10-second take, dirty and hurried, juices on Sayaka's standing thigh. The joining "
                "point stays readable at hip height. Both full bodies stay in the 9:16 frame. End: still inside, still moving."
            ),
            "sound": "Wet filthy thrusting, Sayaka's female moan, a floor creak.",
        },
    )
    clips: list[dict[str, Any]] = []
    for spec in specs:
        canvas = dict(spec["canvas"])
        prompt = _anthology_prompt(
            prefix=str(spec["prefix"]),
            who=str(spec["who"]),
            present=tuple(spec["present"]),
            environment=str(spec["environment"]),
            lock=str(spec["lock"]),
            camera=str(spec["camera"]),
            action=str(spec["action"]),
            sound=str(spec["sound"]),
            canvas=canvas,
        )
        if spec["situation"] == "futa_sex" and not prompt.startswith("hmmotion"):
            prompt = "hmmotion, PENISLORA\n" + prompt
        prompt = lock_urine_look(prompt)
        prompt = lock_scat_act(prompt, situation=str(spec["situation"]))
        sit = str(spec["situation"])
        prompt = lock_oral_in_mouth(
            prompt,
            situation=sit,
            ending="share" if sit == "oral_creampie" else "",
        )
        prompt = lock_pleasure_face(prompt, situation=sit)
        prompt = lock_penis_inside(prompt, situation=sit)
        prompt = lock_pleasure_voice_and_wait(prompt, situation=sit)
        if sit == "oral_creampie":
            prompt = lock_semen_share_kiss(inject_semen_share_into_prompt(prompt, where="on_cumouf"))
        clips.append(
            {
                "id": spec["id"],
                "label": spec["label"],
                "situation": spec["situation"],
                "names": list(spec["names"]),
                "canvas": canvas,
                "start": "still_or_t2v",
                "duration_s": 10,
                "prompt": prompt,
            }
        )
    return {
        "schema": "h3-lora-studio-story/v1",
        "id": "shorts-immoral",
        "kind": "anthology",
        "title_ja": "短編集（参照）",
        "adults_only": True,
        "min_age": 22,
        "duration_s": 10 * len(clips),
        "clip_s": 10,
        "seamless": False,
        "use_cast_ref": True,
        "spoken_no_kanji": True,
        "canvas": dict(CANVAS_9_16),
        "stills_dir": "cast",
        "comment_ja": (
            "10秒完結の超濃厚日常インモラル×12。メイン4人のうち竿役（レイ／マドカ）とハメ役（アヤ／サヤカ）の2人。"
            "つなぎなし。各本は input/cast/ の人物写真を R2V 参照。フェラは 9:16 寄り（blowjob LoRA）、"
            "挿入は 16:9 か立ち 9:16。部品は situation から自動。FL2VA の竿は載せない。穴（synth-pussy）は載せる。"
        ),
        "download": list(SITUATION_DOWNLOAD["shorts-immoral"]),
        "clips": clips,
    }

def semen_share_follow_errors(story: dict[str, Any]) -> list[str]:
    """口移し is standing at equal eye level, unless the partner stays on their back."""
    errors: list[str] = []
    clips = list(story.get("clips") or [])
    for i, mode in semen_share_plan(story):
        if i < 0 or i >= len(clips):
            continue
        n = i + 1
        prompt = str(clips[i].get("prompt") or "")
        locked = lock_semen_share_kiss(
            inject_semen_share_into_prompt(prompt, where=mode),
            supine=(mode == "on_back"),
        )
        low = locked.lower()
        if mode == "on_back":
            if "stays lying" not in locked and "lying on their back" not in low:
                errors.append(f"clip {n}: 口移し must keep the partner lying on their back")
            if "leans down" not in low and "lean down" not in low:
                errors.append(f"clip {n}: 口移し must lean down to the partner on their back")
            if "stands up" in low or "same eye level" in low:
                errors.append(f"clip {n}: 口移し must not stand the partner up")
            continue
        if "stands up" not in low and "stand up" not in low:
            errors.append(f"clip {n}: 口移し must have the sucking woman stand up")
        if "eye level" not in low:
            errors.append(f"clip {n}: 口移し must meet at the same eye level")
        if "they lean in" in low:
            errors.append(f"clip {n}: 口移し must not kiss by leaning in from the knees")
    return errors


def validate_story_follow(story: dict[str, Any]) -> list[str]:
    """H3 following: every clip is 10s (15s OOM). One place, act cameras, lip-sync only on speaking face clips. Act clips (jupo / in-mouth / sex / cunni) stay mute. Addon act clips need a pose-prep leftover on the previous clip."""
    errors: list[str] = []
    clips = list(story.get("clips") or [])
    anthology = str(story.get("kind") or "") == "anthology"
    clip_s = float(story.get("clip_s") or 10.0)
    # 建前 packs carry one short exchange (2 speakers) in a 10s face clip. Default stays 1.
    spoken_max = max(1, min(2, int(story.get("spoken_max") or 1)))
    for i, clip in enumerate(clips):
        n = i + 1
        duration = float(clip.get("duration_s") or clip_s)
        prompt = str(clip.get("prompt") or "")
        situation = str(clip.get("situation") or "").strip()
        lines = spoken_lines(prompt)
        if abs(duration - 10.0) > 0.01:
            errors.append(f"clip {n}: duration_s must be 10 for H3 following (got {duration:g})")
        if anthology:
            if "10-second take" not in prompt and "10-second" not in prompt:
                errors.append(f"clip {n}: anthology clips must be a 10-second take")
        if "15-second take" in prompt or "15-second" in prompt:
            errors.append(f"clip {n}: use a 10-second take, not 15")
        for spoken in lines:
            if _KANJI_RE.search(spoken):
                errors.append(f"clip {n}: write the spoken line in kana (no kanji): 「{spoken}」")
                break
            if _LATIN_IN_SPEECH_RE.search(spoken):
                errors.append(f"clip {n}: spoken line must be Japanese only (no Latin letters): 「{spoken}」")
                break
        if "Clear futanari" in prompt and "Penis plus vagina, never balls" not in prompt:
            errors.append(f"clip {n}: futanari must be penis plus vagina, no balls")
        if "Clear futanari" in prompt and "no scrotum" not in prompt:
            errors.append(f"clip {n}: futanari must have no scrotum")
        prompt_l = prompt.lower()
        has_hmmotion = "hmmotion" in prompt_l
        if situation in HMMOTION_SITUATIONS and not prompt.startswith("hmmotion"):
            errors.append(f"clip {n}: {situation} prompt must start with hmmotion")
        if situation not in HMMOTION_SITUATIONS and has_hmmotion:
            errors.append(f"clip {n}: hmmotion is only for the AIO sex clip, not {situation}")
        if situation in ACT_SITUATIONS:
            if lines:
                errors.append(f"clip {n}: act situation {situation} must not speak")
            if "LIP SYNC" in prompt:
                errors.append(f"clip {n}: act situation {situation} must not lip-sync")
            if situation in {"oral", "oral_creampie", "cunnilingus_futa"} and "Full bodies from head to feet" in prompt:
                errors.append(f"clip {n}: oral/cunni clip must not be a full-body wide")
            if situation in {"oral", "oral_creampie"} and "close" not in prompt_l and "medium-close" not in prompt_l:
                errors.append(f"clip {n}: oral camera must be close or medium-close")
            if situation == "cunnilingus_futa" and "close-up" not in prompt_l and "extreme close" not in prompt_l:
                errors.append(f"clip {n}: cunnilingus camera must be a close-up")
            if situation in SEX_INSIDE_SITUATIONS and "joining" not in prompt_l and "already in" not in prompt_l and "already joined" not in prompt_l and "show the entry" not in prompt_l and "insertion on camera" not in prompt_l:
                errors.append(f"clip {n}: sex clip must already be in / show the joining point")
            if situation == "futa_masturbation" and "strok" not in prompt_l and "pump" not in prompt_l and "lap" not in prompt_l:
                errors.append(f"clip {n}: masturbation clip needs a lap/hand camera")
            if situation in SEMEN_SITUATIONS:
                look = lock_semen_look(prompt, situation=situation)
                look_l = look.lower()
                if "white liquid" not in look_l and "white goo" not in look_l:
                    errors.append(f"clip {n}: ejaculation must name a white liquid")
                if "viscous" not in look_l and "sticky" not in look_l and "ドロドロ" not in look:
                    errors.append(f"clip {n}: ejaculation must be viscous / ドロドロ")
                if "heavy-oil" not in look_l:
                    errors.append(f"clip {n}: semen must be heavy-oil thick, same as the meat-wall bath")
                if "floods" not in look_l:
                    errors.append(f"clip {n}: semen must flood / overflow, not a teaspoon")
                if "molasses" not in look_l:
                    errors.append(f"clip {n}: semen must be molasses-slow extra-viscous ドロドロ")
            if situation in {"oral", "oral_creampie", "futa_blowjob"}:
                urine = bool(re.search(r"urine|yellow stream|pees a |drinks the yellow", prompt, re.I))
                if not urine:
                    oral = lock_oral_in_mouth(prompt, situation=situation)
                    if "ORAL LOCK:" in oral and "to the BASE" not in oral and "at the BASE" not in oral:
                        errors.append(f"clip {n}: jupo / 口内 must be deep to the BASE, not a tip suck")
        if lines:
            if situation != "futa_visible":
                errors.append(f"clip {n}: spoken lines only on futa_visible face clips")
            if "LIP SYNC" not in prompt:
                errors.append(f"clip {n}: spoken line needs LIP SYNC on a visible mouth")
            if "Full bodies from head to feet" in prompt:
                errors.append(f"clip {n}: lip-sync clip must not be a full-body wide")
            unique = set(lines)
            if len(unique) > spoken_max:
                what = "one spoken line only" if spoken_max == 1 else f"at most {spoken_max} spoken lines"
                errors.append(f"clip {n}: {what}, got {sorted(unique)}")
    errors.extend(addon_pose_prep_errors(story))
    errors.extend(semen_share_follow_errors(story))
    return errors


def addon_pose_prep_errors(story: dict[str, Any]) -> list[str]:
    """Addon clip before an act must end insertion-imminent / mouth-open / knees-open.

    Last-frame I2V continues from clip 1. Sex/oral/cunni clips are already in, so the
    previous clip must freeze at a hand's width in the accepting pose. Single-clip
    stubs used in unit tests are skipped.
    """
    errors: list[str] = []
    addon = str(story.get("id") or "") in ADDON_PACK_IDS or bool(story.get("addon"))
    if not addon:
        return errors
    clips = list(story.get("clips") or [])
    if len(clips) < 2:
        return errors
    for i in range(len(clips) - 1):
        nxt = str(clips[i + 1].get("situation") or "").strip()
        prompt = str(clips[i].get("prompt") or "")
        p = prompt.lower()
        n = i + 1
        if nxt in {"futa_sex", "doggy"}:
            if "already in" in p or "already inside" in p:
                errors.append(f"clip {n}: sex setup clip must not already be inside")
            if "hand's width" not in p:
                errors.append(f"clip {n}: sex setup clip must end a hand's width from insertion")
            if "not in" not in p:
                errors.append(f"clip {n}: sex setup clip must say NOT in")
            if not any(k in p for k in ("accepting", "hips back", "knees apart")):
                errors.append(f"clip {n}: sex setup clip must end in an accepting pose")
        elif nxt in {"oral", "oral_creampie"}:
            if "already oral" in p or "already at the base" in p:
                errors.append(f"clip {n}: oral setup clip must not already be sucking")
            if "hand's width" not in p:
                errors.append(f"clip {n}: oral setup clip must end a hand's width from the lips")
            if "mouth open" not in p and "opens her mouth" not in p and "open mouth" not in p:
                errors.append(f"clip {n}: oral setup clip must end with mouth open")
        elif nxt == "cunnilingus_futa":
            if "already cunnilingus" in p or "already licking" in p:
                errors.append(f"clip {n}: cunni setup clip must not already be licking")
            if "knees open" not in p:
                errors.append(f"clip {n}: cunni setup clip must end with knees open")
            if "not licking" not in p and "nobody licks" not in p:
                errors.append(f"clip {n}: cunni setup clip must say not licking yet")
    return errors


def load_story(story_id: str, *, studio_root: Path | str | None = None) -> dict[str, Any]:
    sid = str(story_id or "").strip()
    if sid in SITUATION_JA:
        sid = SITUATION_JA[sid]
    if sid in ANTHOLOGY_ID_SET:
        data = generate_immoral_shorts()
        n = len(data.get("clips") or [])
        if n < 8 or n > 16:
            raise SystemExit("短編集は 8〜16本です。")
        clip_s = float(data.get("clip_s") or 10)
        if abs(clip_s - 10.0) > 0.01:
            raise SystemExit("短編集の1本は 10秒です。")
        clip_durs = [float(c.get("duration_s") or clip_s) for c in data["clips"]]
        duration = float(data.get("duration_s") or 0)
        if duration > 240:
            raise SystemExit("短編集は 240秒までです。")
        if abs(duration - sum(clip_durs)) > 0.51:
            raise SystemExit("短編集の秒数と本数が合いません。")
        if int(data.get("min_age") or 0) < 21:
            raise SystemExit("短編集は 21歳以上のみです。")
        follow_errors = validate_story_follow(data)
        if follow_errors:
            raise SystemExit("短編集の追従ルール: " + " / ".join(follow_errors))
        return data
    path = stories_dir(studio_root) / f"{sid}.json"
    if not path.is_file():
        raise SystemExit(f"専用ストーリーがありません: {sid}")
    data = json.loads(path.read_text(encoding="utf-8"))
    clips = data.get("clips") or []
    n = len(clips)
    clip_s = float(data.get("clip_s") or 10)
    chain_pack = sid in CHAIN_PACK_IDS or str(data.get("kind") or "") == "chain"
    addon = sid in ADDON_PACK_IDS or bool(data.get("addon"))
    if addon:
        if n != 2:
            raise SystemExit("物語の追加は 2本です。")
        if not data.get("seamless"):
            raise SystemExit("物語の追加は seamless: true です。")
        if abs(clip_s - 10.0) > 0.01:
            raise SystemExit("物語の追加の1本は 10秒です。")
    elif chain_pack:
        if n < 4 or n > 12:
            raise SystemExit("つなぐパックは 4〜12本です。")
        if not data.get("seamless"):
            raise SystemExit("つなぐパックは seamless: true です。")
    elif n < 8 or n > 12:
        raise SystemExit("専用ストーリーは 8〜12本です。")
    if abs(clip_s - 10.0) > 0.01:
        raise SystemExit("専用ストーリーの1本は 10秒です。")
    clip_durs = [float(c.get("duration_s") or clip_s) for c in clips]
    for d in clip_durs:
        if abs(d - 10.0) > 0.01:
            raise SystemExit("専用ストーリーの1本は 10秒です。")
    if addon and any(abs(d - 10.0) > 0.01 for d in clip_durs):
        raise SystemExit("物語の追加の1本は 10秒です。")
    if int(data.get("min_age") or 0) < 21:
        raise SystemExit("専用ストーリーは 21歳以上のみです。")
    duration = float(data.get("duration_s") or 0)
    if duration > 120:
        raise SystemExit("専用ストーリーは 120秒までです。")
    if addon and abs(duration - 20.0) > 0.51:
        raise SystemExit("物語の追加は 20秒です。")
    if abs(duration - sum(clip_durs)) > 0.51:
        raise SystemExit("専用ストーリーの秒数と本数が合いません。")
    follow_errors = validate_story_follow(data)
    if follow_errors:
        raise SystemExit("専用ストーリーの追従ルール: " + " / ".join(follow_errors))
    return data


def story_stills_dir(drive_input: Path | str, story: dict[str, Any]) -> Path:
    root = Path(drive_input)
    sub = str(story.get("stills_dir") or story.get("id") or "story")
    return root / sub


def resolve_story_still(
    clip: dict[str, Any],
    stills_dir: Path,
    *,
    clip_index: int,
    override: Path | str | None = None,
) -> Path | None:
    if clip_index == 0 and override:
        ov = Path(override)
        if ov.is_file():
            return ov
    name = str(clip.get("still") or "").strip()
    if not name:
        return None
    for cand in (
        stills_dir / name,
        stills_dir.parent / name,
        Path(name),
    ):
        if cand.is_file():
            return cand
    return None


def prepare_story_clip(
    story: dict[str, Any],
    index: int,
    *,
    last_frame: str | None = None,
    stills_dir: Path | None = None,
    studio_root: Path | str | None = None,
    catalog_path: Path | None = None,
    forbidden_path: Path | str | None = None,
    clip0_override: Path | str | None = None,
    prev_situation: str | None = None,
    prev_stack: list[dict[str, Any]] | None = None,
    force_t2v: bool = False,
    fit_scene: bool = False,
    cast_dir: Path | str | None = None,
) -> dict[str, Any]:
    """One story clip. Matching LoRA per act.

    Dedicated (seamless False): hard cut. Photo if present, else T2V. Never the last frame.
    Chain (seamless True, via apply_story_play or a named pack): clip 2+ is I2V from
    last_frame. Clip 1 gets the long-take opening wrap only when rewrite_chain_prompts.
    Ref chain: clip 1 is R2V from Drive input/cast/ identity stills when a main-cast
    person is visible at t=0 (use_cast_ref). Visit openings (resident hidden at the
    start) fall through to T2V so those stills do not spawn a second body.
    Ignore ③テキストから. Clip 2+ stays last-frame I2V on FL2VA.
    Anthology: every clip is R2V from cast stills. No last-frame chain.

    force_t2v: Colab ③「テキストから」は Drive に試験 jpg があっても使わない（最後のコマは使う）。
    参照モードでは force_t2v を無視して人物写真を R2V 参照する。
    fit_scene: ③合わせ. Dedicated still I2V → rewrite_dedicated_scene_i2v_prompt.
    chain_rewrite last clip → rewrite_final_scene_i2v_prompt. chain-raw: nothing.
    """
    clips = list(story.get("clips") or [])
    if index < 0 or index >= len(clips):
        raise SystemExit(f"クリップ番号が範囲外です: {index}")
    clip = clips[index]
    situation = str(clip.get("situation") or "").strip()
    label = str(clip.get("label") or f"clip {index + 1}")
    share_modes = {i: mode for i, mode in semen_share_plan(story)}
    share_mode = share_modes.get(index)
    raw_prompt = compact_story_prompt(str(clip.get("prompt") or ""))
    raw_prompt = lock_act_silent(raw_prompt, situation=situation)
    raw_prompt = lock_futa_shaft(raw_prompt)
    raw_prompt = lock_oral_easy_shaft(raw_prompt, story_id=str(story.get("id") or ""))
    raw_prompt = lock_start_cast(raw_prompt)
    raw_prompt = lock_semen_look(raw_prompt, situation=situation)
    raw_prompt = lock_meat_wall_look(
        raw_prompt,
        story_id=str(story.get("id") or ""),
        clip_index=index,
        situation=situation,
    )
    raw_prompt = lock_urine_look(raw_prompt, situation=situation)
    raw_prompt = lock_scat_act(raw_prompt, situation=situation)
    raw_prompt = lock_spoken_emotion(raw_prompt)
    if share_mode == "on_cumouf":
        raw_prompt = lock_oral_in_mouth(raw_prompt, situation=situation, ending="share")
        raw_prompt = lock_semen_share_kiss(inject_semen_share_into_prompt(raw_prompt, where="on_cumouf"))
        raw_prompt = lock_pleasure_face(raw_prompt, situation="oral_creampie")
        raw_prompt = lock_semen_look(raw_prompt, situation="oral_creampie")
    elif share_mode in {"silent_next", "after_speech", "on_back"}:
        raw_prompt = lock_semen_share_kiss(
            inject_semen_share_into_prompt(raw_prompt, where=share_mode),
            supine=(share_mode == "on_back"),
        )
        raw_prompt = lock_semen_look(raw_prompt, situation="oral_creampie")
        if share_mode == "silent_next":
            situation = "futa_visible"
            label = apply_semen_share_label(label, mode=share_mode)
    else:
        raw_prompt = lock_oral_in_mouth(raw_prompt, situation=situation)
        raw_prompt = lock_pleasure_face(raw_prompt, situation=situation)
    raw_prompt = lock_penis_inside(raw_prompt, situation=situation)
    raw_prompt = lock_pleasure_voice_and_wait(raw_prompt, situation=situation)
    raw_prompt = lock_act_sfx(raw_prompt, situation=situation)
    duration_s = float(clip.get("duration_s") or story.get("clip_s") or 10)
    raw_prompt = lock_clip_timeline(raw_prompt, duration_s=duration_s, situation=situation)
    speaks = bool(spoken_lines(raw_prompt))
    start = str(clip.get("start") or "still_or_t2v").strip()
    seamless = bool(story.get("seamless"))
    rewrite_chain = story_rewrite_chain_prompts(story)
    is_last = index == len(clips) - 1
    anthology = str(story.get("kind") or "") == "anthology"
    use_cast = bool(story.get("use_cast_ref")) or anthology
    # Dedicated JSON keeps start: still_or_t2v on every clip, so the chain plays
    # decide by seamless + last_frame, not by start.
    use_last = bool(seamless and last_frame and index > 0 and not anthology)
    still_dir = Path(stills_dir) if stills_dir is not None else Path(".")
    still_path = None
    still_paths: list[Path] = []
    first_kind_cast = False
    if use_cast and not use_last:
        if clip_cast_people(clip):
            still_paths = pick_cast_stills(clip, cast_dir or still_dir)
            if still_paths:
                still_path = still_paths[0]
                first_kind_cast = True
    elif not force_t2v and not use_last:
        still_path = resolve_story_still(clip, still_dir, clip_index=index, override=clip0_override)
    missing_still = None
    want_still = (not use_cast) and (not force_t2v) and (not use_last) and (start == "still_or_t2v" or bool(clip.get("still")))
    if want_still and still_path is None:
        missing_still = str(clip.get("still") or "") or None
    if use_last:
        mode = "i2v"
        if fit_scene and rewrite_chain and is_last:
            prompt = rewrite_final_scene_i2v_prompt(raw_prompt)
        else:
            prompt = lock_i2v_story_prompt(raw_prompt, continue_from_last=True)
        first_kind = "last_frame"
    elif first_kind_cast:
        mode = "r2v"
        prompt = lock_r2v_cast_prompt(raw_prompt, still_paths, duration_s=duration_s)
        first_kind = "cast"
    elif still_path is not None:
        mode = "i2v"
        if fit_scene and not seamless and not use_cast:
            prompt = rewrite_dedicated_scene_i2v_prompt(raw_prompt)
        else:
            prompt = lock_i2v_story_prompt(raw_prompt, continue_from_last=False)
        first_kind = "still"
    else:
        mode = "t2v"
        prompt, _ = apply_user_prompt(raw_prompt, mode="t2v", default_prompt=raw_prompt)
        first_kind = "t2v"
    # chain-raw (rewrite off) sends the compacted JSON text as is.
    if index == 0 and seamless and rewrite_chain:
        prompt = rewrite_chain_opening_prompt(prompt)

    studio_sys_path(studio_root)
    from select_loras import select_loras

    root = Path(studio_root or STUDIO_ROOT)
    cat = Path(catalog_path) if catalog_path else root / "catalog" / "loras.json"
    profiles = root / "profiles"
    # Lip-sync clips keep the full-step path: distilled turbo steps blur audio timing.
    turbo_override = False if speaks else None
    try:
        cfg = select_loras(
            profile_name=situation,
            mode=mode,
            prompt_arg=prompt,
            catalog_path=cat,
            profiles_dir=profiles,
            turbo_override=turbo_override,
            extra_forbidden=None,
            forbidden_path=forbidden_path,
        )
    except TypeError:
        cfg = select_loras(
            profile_name=situation,
            mode=mode,
            prompt_arg=prompt,
            catalog_path=cat,
            profiles_dir=profiles,
            turbo_override=turbo_override,
        )
    stack = drop_speech_face_killers(list(cfg.get("stack") or []), speaks=speaks, mode=mode)
    if isinstance(cfg, dict):
        cfg = dict(cfg)
        cfg["stack"] = stack
    prompt = prepend_triggers(str(cfg.get("prompt") or prompt), stack)
    prompt = lock_spoken_japanese(prompt, spoken_lines(raw_prompt))
    if prev_stack is not None:
        stack_changed = stack_signature(prev_stack) != stack_signature(stack)
    else:
        stack_changed = bool(prev_situation) and prev_situation != situation
    width, height = story_canvas_wh(story, clip)
    return {
        "index": index,
        "label": label,
        "situation": situation,
        "mode": mode,
        "prompt": prompt,
        "stack": stack,
        "sampler": cfg.get("sampler") or {},
        "cfg": cfg,
        "still_path": still_path,
        "still_paths": still_paths,
        "first_kind": first_kind,
        "missing_still": missing_still,
        "stack_changed": stack_changed,
        "width": width,
        "height": height,
        "duration_s": duration_s,
        "turbo": bool(cfg.get("turbo")),
        "seamless": seamless,
        "rewrite_chain_prompts": rewrite_chain,
        "fit_scene": bool(
            fit_scene
            and (
                (use_last and rewrite_chain and is_last)
                or (still_path is not None and not seamless and not use_cast)
            )
        ),
    }
