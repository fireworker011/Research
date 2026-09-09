"""Colab helper for stacking MiniMax H3 LoRAs.

SFW: turbo + one quality LoRA. Adult: act + optional helper + optional thin turbo.
Futa blowjob may use two helpers plus thin Larry 6step. Futa sex/anal/riding/doggy stay turbo off.
Cinema replaces helper. Anal sex (ThumbInButt + penis + synth) stays turbo off. Pose LoRAs replace AIO; do not stack both.
Larry and LightX2V never stack. Adults 21+ only. Never print API keys.
Fal H3 Max cannot take LoRAs — this is local Comfy FL2VA only.
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

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
_COLAB_R2V = Path(__file__).resolve().parents[1] / "colab"
if _COLAB_R2V.is_dir() and str(_COLAB_R2V) not in sys.path:
    sys.path.insert(0, str(_COLAB_R2V))
# Colab ② writes this file first, then h3_r2v_core.py. Import must not fail.
try:
    from h3_r2v_core import finalize_prompt as r2v_finalize_prompt
except ImportError:
    r2v_finalize_prompt = None

OPTIONAL_IDS = {
    "astro-nsfw-h3": 0.35,
    "tiddies-realism-slider": 1.2,
    "h3-realism-people": 1.0,
    "photoreal-h3-still": 1.0,
}

SITUATION_DOWNLOAD = {
    "vanilla": [],
    "sfw_daily": ["larry-v4", "cinema-dy"],
    "sfw_preview": ["minimax-h3-turbo-fl2v-4step", "cinema-dy"],
    "sfw_audio": ["minimax-h3-turbo-fl2v-8step", "cinema-dy"],
    "sfw_r2v": ["minimax-h3-turbo-ref2v-4step", "cinema-dy"],
    "anal_closeup": ["synth-pussy-h3", "larry-v4", "cinema-dy"],
    "anal_fingering": ["thumbinbutt-h3", "synth-pussy-h3", "larry-v4"],
    "anal_penetration": ["thumbinbutt-h3", "penis-lora-h3", "synth-pussy-h3"],
    "lesbian_cunnilingus": ["lesbian-cunnilingus-h3", "synth-pussy-h3", "larry-v4"],
    "pussy_spread": ["pussy-spread-h3", "synth-pussy-h3", "larry-v4"],
    "lesbian_spread": ["lesbian-cunnilingus-h3", "pussy-spread-h3", "larry-v4"],
    "futa_blowjob": ["blowjob-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"],
    "futa_sex": ["hmnsfw-aio-v25", "penis-lora-h3", "synth-pussy-h3"],
    "futa_anal": ["thumbinbutt-h3", "penis-lora-h3", "synth-pussy-h3"],
    "oral": ["blowjob-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"],
    "general_sex": ["hmnsfw-aio-v25", "penis-lora-h3", "synth-pussy-h3"],
    "preview": ["hmnsfw-aio-v25", "synth-pussy-h3", "minimax-h3-turbo-fl2v-4step"],
    "riding": ["cowgirl-position-h3", "penis-lora-h3", "synth-pussy-h3"],
    "doggy": ["doggy-h3", "penis-lora-h3", "synth-pussy-h3"],
    "missionary_pov": ["missionary-pov-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"],
    "after_ejaculation": ["hmcumshot-v2", "penis-lora-h3", "synth-pussy-h3", "larry-v4"],
    "facial": ["facial-cumshot-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"],
    "creampie": ["final-thrust-h3", "penis-lora-h3", "synth-pussy-h3"],
    "oral_creampie": ["cumouf-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"],
    "fingering": ["fingering-h3", "synth-pussy-h3", "larry-v4"],
    "masturbation": ["hmmasturbation-h3", "synth-pussy-h3", "larry-v4"],
    "footjob": ["footjob-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"],
    "remote_orgasm": ["remote-orgasm-h3", "synth-pussy-h3", "larry-v4"],
    "futa_visible": ["penis-lora-h3", "synth-pussy-h3", "larry-v4", "cinema-dy"],
    "futa_masturbation": ["hmmasturbation-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"],
    "cunnilingus_futa": ["lesbian-cunnilingus-h3", "synth-pussy-h3", "penis-lora-h3", "larry-v4"],
    "homecoming-90s": [
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
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "commute-120s": [
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "synth-pussy-h3",
    ],
    "lecture-120s": [
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
        "penis-lora-h3",
        "cinema-dy",
        "larry-v4",
        "hmnsfw-aio-v25",
        "synth-pussy-h3",
    ],
    "okaeri-120s": [
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "bath-120s": [
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "dinner-120s": [
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "futon-120s": [
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "sunday-120s": [
        "penis-lora-h3",
        "cinema-dy",
        "hmnsfw-aio-v25",
        "synth-pussy-h3",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
    ],
    "engawa-120s": [
        "penis-lora-h3",
        "cinema-dy",
        "hmnsfw-aio-v25",
        "synth-pussy-h3",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
    ],
    "sales-visit-60s": [
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "checkup-100s": [
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "clinic-75s": [
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "last-stop-40s": [
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    "last-train-120s": [
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
        "cowgirl-position-h3",
        "hmcumshot-v2",
    ],
    "semen-bath-70s": [
        "penis-lora-h3",
        "cinema-dy",
        "larry-v4",
        "synth-pussy-h3",
        "hmcumshot-v2",
    ],
    "meat-wall-85s": [
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ],
    # 建前パック (10s × N, 9:16). Talk = futa_visible, jupo = oral, in-mouth = oral_creampie,
    # pee-as-drink = oral, cunnilingus = cunnilingus_futa, already-in sex = futa_sex / doggy.
    "cafe-100s": ["penis-lora-h3", "cinema-dy", "blowjob-h3", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "train-sales-80s": ["penis-lora-h3", "cinema-dy", "blowjob-h3", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "red-light-50s": ["penis-lora-h3", "cinema-dy", "blowjob-h3", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "yoga-50s": ["penis-lora-h3", "cinema-dy", "doggy-h3", "synth-pussy-h3", "larry-v4"],
    "back-wash-60s": ["penis-lora-h3", "cinema-dy", "lesbian-cunnilingus-h3", "synth-pussy-h3", "blowjob-h3", "larry-v4"],
    "karaoke-50s": ["penis-lora-h3", "cinema-dy", "blowjob-h3", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "laundromat-50s": ["penis-lora-h3", "cinema-dy", "hmnsfw-aio-v25", "synth-pussy-h3", "larry-v4"],
    "lecture-desk-50s": ["penis-lora-h3", "cinema-dy", "blowjob-h3", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "camp-50s": ["penis-lora-h3", "cinema-dy", "lesbian-cunnilingus-h3", "synth-pussy-h3", "larry-v4"],
    "fireworks-50s": ["penis-lora-h3", "cinema-dy", "hmnsfw-aio-v25", "synth-pussy-h3", "larry-v4"],
    # 物語の追加 (15s × 2, 9:16). Talk = futa_visible, in-mouth = oral_creampie,
    # already-in sex = futa_sex, cunnilingus = cunnilingus_futa.
    "manhole-30s": ["penis-lora-h3", "cinema-dy", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "roof-ac-30s": ["penis-lora-h3", "cinema-dy", "hmnsfw-aio-v25", "synth-pussy-h3", "larry-v4"],
    "tetrapod-30s": ["penis-lora-h3", "cinema-dy", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "locker-30s": ["penis-lora-h3", "cinema-dy", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "crossing-30s": ["penis-lora-h3", "cinema-dy", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "lookout-30s": ["penis-lora-h3", "cinema-dy", "lesbian-cunnilingus-h3", "synth-pussy-h3", "larry-v4"],
    "factory-30s": ["penis-lora-h3", "cinema-dy", "hmnsfw-aio-v25", "synth-pussy-h3", "larry-v4"],
    "gas-station-30s": ["penis-lora-h3", "cinema-dy", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "tunnel-phone-30s": ["penis-lora-h3", "cinema-dy", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "riverbank-30s": ["penis-lora-h3", "cinema-dy", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    "shorts-immoral": [
        "blowjob-h3",
        "synth-pussy-h3",
        "minimax-h3-turbo-ref2v-4step",
        "aftermidnight-ref2va",
    ],
}

SITUATION_JA = {
    "普通（エロなし）": "vanilla",
    "日常（速い＋綺麗）": "sfw_daily",
    "最速プレビュー（エロなし）": "sfw_preview",
    "音も残す（エロなし）": "sfw_audio",
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
    "セックス（女体）": "futa_sex",
    "ふたなりセックス": "futa_sex",
    "アナルセックス（女体）": "futa_anal",
    "ふたなりアナル": "futa_anal",
    "アナルセックス": "futa_anal",
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
    "sales-visit-60s": "sales-visit-60s",
    "checkup-100s": "checkup-100s",
    "clinic-75s": "clinic-75s",
    "last-stop-40s": "last-stop-40s",
    "last-train-120s": "last-train-120s",
    "semen-bath-70s": "semen-bath-70s",
    "meat-wall-85s": "meat-wall-85s",
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
    "vanilla": "専用 I2V / T2V ノートと同じ。LightX2V 4step だけ。画質 LoRA なし。",
    "sfw_daily": "日常・会話・商品・風景。Larry v4 1.0 + シネマ 0.65 / 8step。エロ用は入れない。",
    "sfw_preview": "エロなしの最速プレビュー。LightX2V 4step 1.0 + シネマ 0.4。当たりは日常で焼き直す。",
    "sfw_audio": "音を残して速く。LightX2V 8step 1.0 + シネマ 0.4。歌・日本語は日常（Larry）の方が安定。",
    "sfw_r2v": "顔固定 R2V。LightX2V Ref2VA 4step + シネマ 0.5。FL2VA 用 Turbo は積まない。このノートでは選ばない。",
    "anal_closeup": "アナル舐め・指（女体）。穴の見え方 0.7 + Larry 0.5 + シネマ 0.4。女同士。男なし。動きの本線はアナル指入れ。",
    "anal_fingering": "アナル指入れ。女1人。ThumbInButt 0.85 + 穴の見え方 0.55 + Larry 0.5 / 8step。男なし。自分の右親指。後ろから、穴が膣より上に見える構図。指入れ（膣）・アナルセックスとは別。写真からが本線。",
    "anal_penetration": "アナル挿入（画質）。穴のアップ。ThumbInButt 0.85 + 竿 0.7 + 穴の見え方 0.55。Turbo なし・16step。挿入側はふたなり。男なし。写真からが本線（後ろから、穴が見える写真）。",
    "lesbian_cunnilingus": "レズクンニ。女同士。クンニ 0.8 + 穴の見え方 0.55 + Larry 0.5。男なし。",
    "pussy_spread": "性器を広げる。女1人。広げる 0.75 + 穴の見え方 0.55 + Larry 0.5。男なし。",
    "lesbian_spread": "レズ＋広げる。女同士。クンニ 0.8 + 広げる 0.6 + Larry 0.5。男なし。",
    "futa_blowjob": "ふたなりフェラ。フェラ + 竿 0.7 + 穴の見え方 0.55 + Larry 0.5 / 6step。空欄は全裸のごく普通の若い成人女性。男なし。変身 LoRA は足さない。",
    "futa_sex": "セックス（女体）。総合えっち 0.8 + 竿 0.7 + 穴の見え方 0.55 / 12step。Turbo なし。ふたなり＋女。男なし。空欄は全裸のごく普通の若い成人女性。描写は文章欄で足す。",
    "futa_anal": "アナルセックス（女体）。ThumbInButt 0.85 + 竿 0.7 + 穴の見え方 0.55。Turbo なし・12step。ふたなり＋女。男なし。後ろから、穴が膣より上に見える構図。手は腰。写真からが本線。",
    "oral": "フェラ（女体）。フェラ 0.8 + 竿 0.7 + 穴の見え方 0.55 + Larry 0.5 / 8step。受けはふたなり（竿＋根元のマンコ、玉なし）。男なし。変身 LoRA は足さない。",
    "general_sex": "汎用エロ（女体）。AIO 0.8 + 竿 0.7 + 穴の見え方 0.55 / 12step。Turbo なし。ふたなり＋女。男なし。",
    "preview": "試し打ち（女体）。AIO 0.7 + 穴の見え方 0.55 + LightX2V 4step。ふたなり＋女。男なし。",
    "riding": "騎乗位（女体）。騎乗 LoRA 0.8 + 竿 0.7 + 穴の見え方 0.55 / 12step。Turbo なし。AIO は積まない。男なし。",
    "doggy": "後背位（女体）。後背位 LoRA 0.8 + 竿 0.7 + 穴の見え方 0.55 / 12step。Turbo なし。男なし。",
    "missionary_pov": "正常位POV（女体）。POV挿入 0.85 + 竿 0.7 + 穴の見え方 0.55 + Larry 0.5 / 8step。男なし。横はセックス（女体）。",
    "after_ejaculation": "後射精（女体）。射精 LoRA 0.9 + 竿 0.7 + 穴の見え方 0.55 + Larry 0.5 / 8step。ふたなり。男なし。絶頂・顔射・中出しとは別。",
    "facial": "顔射（女体）。顔射 LoRA 0.8 + 竿 0.7 + 穴の見え方 0.55 + Larry 0.5 / 8step。ふたなり＋女。男なし。後射精・絶頂・口内とは別。写真からが本線。",
    "creampie": "中出し（女体）。Final Thrust 0.85 + 竿 0.7 + 穴の見え方 0.55 / 12step。Turbo なし。膣の中に出す。ふたなり＋女。男なし。後射精・顔射・口内とは別。写真からが本線。",
    "oral_creampie": "口内射精（女体）。CUMOUF 0.5 + 竿 0.7 + 穴の見え方 0.55 + Larry 0.5 / 8step。口の中で出す。ふたなり（竿＋根元のマンコ）＋女。男なし。顔射・フェラ本線とは別。写真からが本線（口が付いた途中の写真）。",
    "fingering": "指入れ。女1人。指 LoRA 0.85 + 穴の見え方 0.55 + Larry 0.5 / 8step。男なし。膣。アナルはアナル指入れ。",
    "masturbation": "オナニー。女1人。潮吹き 0.8 + 穴の見え方 0.55 + Larry 0.5 / 12step。男なし。",
    "footjob": "足コキ（女体）。Type D 0.85 + 竿 0.7 + 穴の見え方 0.55 + Larry 0.5 / 8step。ふたなり＋女。男なし。",
    "remote_orgasm": "絶頂。女1人。反応 LoRA 0.8 + 穴の見え方 0.55 + Larry 0.5 / 8step。男なし。射精ではない。",
    "futa_visible": "歩行・会話。竿は出す。行為 LoRA なし。歩く・キス・テレビの本は竿 0.7 + 穴の見え方 0.55 + Larry 0.6 / 8step。セリフ（「」）の本だけ Turbo を外して res_multistep 12step。男なし。",
    "futa_masturbation": "ふたなりオナニー。潮吹き LoRA + 竿 + 穴の見え方 + Larry 12step。根元のマンコが見える寄り。男なし。",
    "cunnilingus_futa": "クンニ。竿は使わず垂らす。クンニ + 穴 + 竿薄め + Larry。フェラ LoRA は積まない。男なし。",
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
    "sales-visit-60s": "訪問販売。対面20秒。8本＝85秒。9:16。玄関。口はアヤ22ミニ・竿なし。販売員は5人目25・短め黒髪・中乳・ふたなり20cm・金玉なし・竿の根元にマンコ。跪き済みではやく。おミズ＝放尿を飲み干してからジュボ15秒。口内は粘る白液を残して見せる。セリフ: こんにちは。おミズ、とどけにきました／おそいわよ／はやくおミズちょうだい／あー、しみる／ありがとうございました。行為は無言・寄り。hmmotion なし。",
    "checkup-100s": "定期検診。対面30秒。9本＝100秒。9:16。診察室ではない。家の玄関。医師32・結い髪・中乳・竿なし・聴診器。レイ24・20cm 立ち。セリフ10秒、ベロチューとジュボは無言15秒。キスは両手で胸。カクニンは立ちの口パクのみ。台詞: こんにちは。テイキケンシンにきました／あ…はい、ヨロシクオネガイします／では、シツレイします／クチとムネはモンダイないですね／では、つぎはおチンチンのカクニンをします／モンダイありますね。hmmotion なし。",
    "clinic-75s": "ケンシン。医院にアヤが来る。6本＝75秒。9:16。医師32・結い髪・中乳・聴診器・ふたなり20cm玉なしマンコあり。口はアヤ22ミニ・竿なし。1本目: 女医は画面左手・また開いてシコシコ無表情。アヤは右から入る。「オチンチンおっきい」のあと女医が立ち上がり、お互い立ったまま短いキス。それから笑顔で、画面右手の目の前の椅子にどうぞおすわりください。女医は立ったまま。3本目のおクチキスもお互い立つ（身を胸につける。胸は揉まない）。台詞10秒・2行まで。ジュボ15・口内15は無言。ゲンキは口パク10秒。口内のあとジュボ側が同じ目線に立ち上がって口移し。hmmotion なし。",
    "last-stop-40s": "終点40秒（つなぐ）。10秒×4本。9:16 576×1024。名前付きの「つなぐ」パック。最後のコマから I2V。車掌29・短髪・中乳・竿なし・ホイッスル。レイは座席で寝たまま立たない。普通の声では起きない。起こしのあと跪いて咥える（竿舐め禁止）。ジュボで起きる。口内 CUMOUF のあと車掌に戻る。台詞: しゅうてんです、おきてください／おきましたか？おきゃくさん、しゅうてんだからおりてください。hmmotion なし。",
    "last-train-120s": "終電。終点の延長。9本＝120秒。9:16。車掌29・短髪・中乳・竿なし・ホイッスル。レイ24は座席のまま立たない。20cm玉なしマンコあり。ジュボ30秒で奥まで（竿舐め禁止）。口内のあと同じ目線で口移し。レイがまた寝ようとする。台詞: しゅうてんです、おきてください／まだおきないんですか！／しょうがないですね。座ったまま騎乗→中に出す→抜くとドロドロが車掌のマンコから流れ出る。hmmotion なし。既存の終点はそのまま。",
    "semen-bath-70s": "ザーメン風呂。5本＝70秒。9:16。家の小さいおフロ。アヤ22ミニ・竿なしが湯船。レイ24・20cmが立ってドロドロの白い液体を溜める。湯ではなく白い粘液がお風呂。口移しなし。挿入なし。ジュボなし。hmmotion なし。台詞: ザーメンフロにして／いっぱいだすね。",
    "meat-wall-85s": "ニクカベ。巨大生物の体内のザーメン風呂。コンクリートに肉を貼った部屋ではない。おフロは生体の窪み。7本＝85秒。9:16。茶色い粘液は壁から、全身・顔・髪・チンチン・マンコに付く。白は風呂。水ではなくベトベトで肌に付く。混ざるが消えない。顔は液面より上。歩行の床は弾力。足は沈まない。レイは1本目からフタナリ勃起20cm。竿は風呂から生えない。アヤ22ミニ・竿なし。歩行15秒、台詞10秒、ジュボ15・口内15は無言。全部飲む。口移しなし。hmmotion なし。家のザーメン風呂とは別。台詞: あ、おフロ。。。でもこれって／ザーメンの、、、おフロ、、、すごいニオイ、、、／ザーメンのおフロ。。。あったかーい／もうガマンできない！おチンチンジュボジュボするの！／レイのザーメンおいしかった！",
    "cafe-100s": "カフェ100秒。10秒×10本。9:16。建前は最後まで落とさない: おミズ＝放尿、ミルク＝ジュボと口内。客はアヤ22ミニ・竿なし。店員25・低いお団子・中乳・ふたなり20cm・トレイだけ。コーヒーは本物を置いたまま終わる。台詞は話し言葉（漢字なし）（1本に2行まで）。行為は無言・寄り。最後はベロチューと抱擁。",
    "train-sales-80s": "車内販売80秒。10秒×8本。9:16。建前: おチャ＝放尿、ミルクコーヒー＝ジュボと口内。客はレイ24（受け・自分の20cmは使わない）。販売員26・短め黒髪・中乳・ふたなり20cm・ワゴンだけ。台詞は話し言葉（漢字なし）。行為は無言・寄り。",
    "red-light-50s": "赤信号50秒。10秒×5本。9:16。建前: 信号待ちとナビ。運転はレイ24（20cm・両手はハンドル）、口はアヤ22。ジュボと口内だけ。放尿なし。車は動かない。台詞は話し言葉（漢字なし）。",
    "yoga-50s": "ヨガ50秒。10秒×5本。9:16。建前: コツバンを落とす。講師29・お団子・中乳・ふたなり20cm。生徒はアヤ22。四つん這いで最初から入っている（後背位 LoRA）。ジュボなし・放尿なし。台詞は話し言葉（漢字なし）。",
    "back-wash-60s": "背中流し60秒。10秒×6本。9:16。建前: 上から下へ洗う。洗うのはサヤカ39（竿なし）。洗われるのはマドカ22（20cm）。背中→マドカのマンコ舐め（竿は使わない）→アガリユ＝放尿。ジュボなし。台詞は話し言葉（漢字なし）。",
    "karaoke-50s": "カラオケ50秒。10秒×5本。9:16。建前: サビ待ちと点数。歌うのはマドカ22（20cm・マイク）。口はアヤ22。歌のあいだジュボ、最後の音で口内。放尿なし。台詞は話し言葉（漢字なし）。",
    "laundromat-50s": "コインランドリー50秒。10秒×5本。9:16。建前: あと何分。竿はレイ24、受けはアヤ22。洗濯機の上でもう入っている（AIO 横クローズ）。ジュボなし・放尿なし。台詞は話し言葉（漢字なし）。",
    "lecture-desk-50s": "講義机50秒。10秒×5本。9:16。建前: 板書とノート。先生36・眼鏡・結い髪・中乳・ふたなり20cm・チョークだけ。アヤ22が教卓の下でジュボ→口内。上の声は授業。放尿なし。台詞は話し言葉（漢字なし）。授業120秒（専用）とは別。",
    "camp-50s": "キャンプ50秒。10秒×5本。9:16。建前: 虫よけ。レイ24がアヤ22のマンコを舐めるだけ。レイの20cmは画面にあっても使わない。ジュボなし・放尿なし。台詞は話し言葉（漢字なし）。",
    "fireworks-50s": "花火50秒。10秒×5本。9:16。建前: 上を見る。竿はマドカ22、受けはサヤカ39。立ったまま後ろから入っている。顔は花火のまま。ジュボなし・放尿なし。台詞は話し言葉（漢字なし）。",
    "manhole-30s": "物語の追加。ハイスイコウ。15秒×2＝30秒。9:16。アヤ22ミニ・竿なし＋レイ24・20cm。1本目はフタの会話のあと、口を開けて先端から手の幅。2本目は無言で根元までジュボ→口内。口内のあとはジュボ側が同じ目線に立ち上がって濃厚キス口移し。hmmotion なし。",
    "roof-ac-30s": "物語の追加。屋上クーラー。15秒×2＝30秒。9:16。サヤカ39・竿なし＋マドカ22・20cm。1本目はクーラーの会話のあと、受け入れる立ち・挿入寸前（先端から手の幅、未挿入）。2本目は無言でもう入っている立ち（AIO・hmmotion 先頭）→中に出して腿に残る。口移しなし。",
    "tetrapod-30s": "物語の追加。ハマのテトラ。15秒×2＝30秒。9:16。アヤ＋レイ。1本目は風の会話のあと、跪いて口を開けて先端から手の幅。2本目は無言ジュボ→口内。ジュボ側が同じ目線に立ち上がって濃厚キス口移し。hmmotion なし。",
    "locker-30s": "物語の追加。廃校ロッカー。15秒×2＝30秒。9:16。アヤ＋マドカ。1本目はカギの会話とベロチューのあと、跪いて口を開けて先端から手の幅。2本目は無言ジュボ→口内。ジュボ側が同じ目線に立ち上がって濃厚キス口移し。hmmotion なし。",
    "crossing-30s": "物語の追加。ドウロのど真ん中。15秒×2＝30秒。9:16。サヤカ＋レイ。1本目は信号の会話のあと、跪いて口を開けて先端から手の幅。2本目は無言ジュボ→口内。ジュボ側が同じ目線に立ち上がって濃厚キス口移し。hmmotion なし。",
    "lookout-30s": "物語の追加。ガケの展望台。15秒×2＝30秒。9:16。アヤ＋レイ。1本目は霧の会話のあと、アヤ仰向け・膝を開いて舐め寸前。2本目は無言クンニ（竿は使わない）。ジュボなし・口移しなし。hmmotion なし。",
    "factory-30s": "物語の追加。コウジョウあと。15秒×2＝30秒。9:16。サヤカ＋マドカ。1本目はサビの会話のあと、受け入れる立ち・挿入寸前（先端から手の幅、未挿入）。2本目は無言でもう入っている立ち→中に出して腿に残る。口移しなし。hmmotion 先頭。",
    "gas-station-30s": "物語の追加。ガソリンスタンド跡。15秒×2＝30秒。9:16。アヤ＋レイ。1本目はミズの会話のあと亀頭先の黄色い水を飲み、口を開けて先端から手の幅で止まる。2本目は無言ジュボ→口内。ジュボ側が同じ目線に立ち上がって濃厚キス口移し。hmmotion なし。",
    "tunnel-phone-30s": "物語の追加。トンネル非常電話。15秒×2＝30秒。9:16。アヤ＋レイ。1本目は電話の会話のあと、受話器を持ったまま跪いて口を開けて先端から手の幅。2本目は受話器を持ったまま口だけで根元まで→口内。手は竿に触れない。ジュボ側が同じ目線に立ち上がって濃厚キス口移し。hmmotion なし。",
    "riverbank-30s": "物語の追加。川原のゴミ。15秒×2＝30秒。9:16。サヤカ＋マドカ。1本目はフクロの会話のあと、跪いて口を開けて先端から手の幅。2本目は無言ジュボ→口内。ジュボ側が同じ目線に立ち上がって濃厚キス口移し。hmmotion なし。",
    "shorts-immoral": "短編集（参照）。15秒完結の超濃厚日常インモラルを複数本。メイン4人のうち竿役（レイ／マドカ）とハメ役（アヤ／サヤカ）の2人。つなぎなし。各本は input/cast/ の人物写真を R2V 参照（最初のコマではない）。画面は本ごと（フェラ9:16寄り、挿入は16:9または立ち9:16）。文と部品は自動。FL2VA の竿は載せない。穴（synth-pussy）は載せる（竿役以外に竿が付くのを防ぐ）。",
}

LORA_JA = {
    "synth-pussy-h3": "穴の見え方",
    "lesbian-cunnilingus-h3": "レズクンニ",
    "pussy-spread-h3": "性器を広げる",
    "anal-penetration-coachbate": "アナル挿入（CoachBate・有料・未使用）",
    "hmnsfw-aio-v25": "総合えっち",
    "futa-h3-v51": "ふたなり",
    "penis-lora-h3": "竿",
    "blowjob-h3": "フェラ",
    "riding-pose-i2v": "騎乗のポーズ（I2V専用・未使用）",
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
)
CHAIN_PACK_IDS = set(CHAIN_PACK_ORDER)
# 物語の追加: 15秒×2＝30秒。台詞は1本目（futa_visible）だけ。行為は無言。
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
)
ADDON_PACK_IDS = frozenset(ADDON_PACK_ORDER)
# 15s independent dirty shorts. Not a story (is_story False). Not a chain pack.
ANTHOLOGY_IDS = ("shorts-immoral",)
ANTHOLOGY_ID_SET = set(ANTHOLOGY_IDS)
ANTHOLOGY_LABEL = "短編集（参照）"
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
        "重ね上限は Turbo1 + 画質1。エロ用は入れません。"
        if sid in SFW_SITUATIONS
        else "重ね上限は 行為1 + ヘルパー0〜2 + Turbo0〜1。Fal には載せません。"
    )
    play_line = ""
    if sid in STORY_IDS:
        play = resolve_story_play(situation)
        play_line = f"再生: {STORY_PLAY_JA[play]}（{STORY_PLAY_HELP_JA[play]}）\n"
    elif sid in CHAIN_PACK_IDS:
        play = resolve_story_play(situation)
        play_line = f"再生: {STORY_PLAY_JA[play]}（{STORY_PLAY_HELP_JA[play]}）。名前付きパック。専用ストーリーではありません\n"
    elif sid in ANTHOLOGY_ID_SET:
        play_line = "再生: 短編集（参照）。15秒完結×複数。つなぎなし。人物写真を R2V 参照\n"
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


def has_fl2va_weight(root: Path | str) -> bool:
    """True if a FL2VA safetensors sits in this folder. Name only — do not open GB files."""
    folder = Path(root)
    if not folder.is_dir():
        return False
    try:
        for path in folder.iterdir():
            name = path.name.lower()
            if "fl2va" in name and name.endswith(".safetensors") and not name.endswith(".part"):
                return True
    except OSError:
        return False
    return False


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
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
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
    """One shot is 4–15s. Chain mode is 16–120s via 10s clips. Homage notebooks stay as they are."""
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
    if n > 15:
        return 15.0
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
    """Native H3 clips. Do not generate 16s+ in one MiniMaxH3ImageToVideo pass."""
    total = clamp_studio_duration(total_s, chain=chain)
    if not chain:
        return [total]
    clips: list[float] = []
    left = int(total)
    while left > 15:
        clips.append(10.0)
        left -= 10
    if left >= 4:
        clips.append(float(left))
    elif clips:
        clips[-1] = float(int(clips[-1]) + left)
    else:
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
    "SHAFT LOOK: Same penis every clip. When erect: 20cm, thick human girth, straight, heavy, "
    "pale-tan shaft, flushed pink-red glans with a clear corona. Same size and same shape "
    "the whole take. Not tiny, not horse-like, not a skinny stick, not a tapered spike, "
    "not a hook, not changing mid-clip. NO testicles, NO scrotum. Hairless female pussy "
    "at the base of the shaft. Penis plus vagina, never balls. Do not grow balls. "
    "Women marked NEVER futanari stay NO penis."
)
MEAT_FUTA_LINE = (
    "FUTA LOCK: Rei is already a clear futanari from frame 1. The erect 20cm is already "
    "growing from her own groin, attached to her body, visible. It does NOT grow out of "
    "the white bath. It does NOT emerge from the liquid. It does NOT appear later. "
    "Aya stays NO penis, NEVER futanari."
)
MEAT_SLIME_LINE = (
    "BROWN SLIME: Thick dark-brown viscous slime already coats BOTH whole bodies: "
    "face, hair, eyebrows, lips, neck, breasts, belly, back, ass, thighs, Aya's hairless pussy, "
    "Rei's erect 20cm, and Rei's pussy at the base. It STAYS. It does not fade."
)
BATH_LOOK_LINE = (
    "BATH LOOK: The bath is paste-thick opaque gooey sticky white semen, like glue or fresh rice paste, "
    "not water, not milk, not thin white bathwater. It clings to skin in strings and coats. "
    "Fingers would pull sticky threads. It does not look like a water bath."
)


SEMEN_SITUATIONS = frozenset({"oral_creampie", "creampie", "facial", "after_ejaculation"})
SEMEN_LOOK_LINE = (
    "SEMEN LOOK: The semen is a heavy clingy viscous sticky white liquid, paste-thick like glue. "
    "Heavy volume, a lot of it, opaque milk-white, thick gooey ropes that stretch. "
    "Not watery, not clear, not saliva, not a thin drip, not milk, not bathwater. "
    "Where it lands on face, lips, chin, breasts, belly, thighs, or skin it STAYS: it clings and coats like wet paint. "
    "It does not vanish, does not soak in, does not turn clear, does not run off like water. "
    "From the urethral opening at the glans tip leftover white liquid keeps drooling down the shaft "
    "so the penis is glossy and slick with semen. It stays on the face and body after ejaculation."
)
_SEMEN_CUE_RE = re.compile(
    r"CUMOUF|climaxes IN|ejaculates IN|cums inside|cum fills|"
    r"Already a facial|Already after ejaculation|"
    r"viscous white|Thick white cum|shows the semen|The semen stays|"
    r"white semen|white liquid",
    re.I,
)


def lock_semen_look(text: str, *, situation: str = "") -> str:
    """H3 skips semen unless the prompt names a viscous white liquid."""
    raw = str(text or "")
    if not raw or "SEMEN LOOK:" in raw:
        return raw
    sit = str(situation or "").strip()
    if sit not in SEMEN_SITUATIONS and not _SEMEN_CUE_RE.search(raw):
        return raw
    cut = raw.find("\noverall_soundscape:")
    if cut > 0:
        return raw[:cut].rstrip() + "\n" + SEMEN_LOOK_LINE + "\n" + raw[cut:]
    return raw.rstrip() + "\n" + SEMEN_LOOK_LINE


ORAL_SUCK_SITUATIONS = frozenset({"oral", "futa_blowjob", "oral_creampie"})
ORAL_IN_MOUTH_LINE = (
    "ORAL LOCK: The glans is already fully inside the mouth. Lips are a tight ring around the shaft. "
    "Cheeks hollow. This is sucking (jupo), not licking. Do not lick the side of the shaft. "
    "Do not kiss the shaft. Do not run the tongue along the shaft. The penis stays in the mouth, not beside it."
)
ORAL_IN_MOUTH_SHARE_LINE = (
    ORAL_IN_MOUTH_LINE
    + " Until the last cum pulses, stay like that. After the last pulse only: mouth off the penis. "
    "HOLD STILL a heavy clingy sticky pool of opaque white liquid on the tongue. "
    "The woman who was sucking STANDS UP off her knees to the partner's SAME EYE LEVEL, "
    "then mouth-to-mouth semen share, wet tongue kiss: tongues wrap and tangle around that same heavy white liquid. "
    "Do not kiss from the knees. Do not lick the shaft when coming off."
)
_ORAL_SUCK_RE = re.compile(
    r"Already oral|jupo|blow job|Mouth already on|Mouth already wrapped|"
    r"takes it to the BASE|takes .+ to the BASE|sucks the |already at .+ base",
    re.I,
)


def lock_oral_in_mouth(text: str, *, situation: str = "", ending: str = "") -> str:
    """Stop H3 from turning a blowjob into shaft-licking."""
    raw = str(text or "")
    if not raw or "ORAL LOCK:" in raw:
        return raw
    sit = str(situation or "").strip()
    if sit not in ORAL_SUCK_SITUATIONS:
        return raw
    if re.search(r"urine|yellow stream|pees a |drinks the yellow", raw, re.I):
        return raw
    share_end = str(ending or "").strip() == "share"
    if not share_end and re.search(r"pulls OFF|pulls her mouth off", raw, re.I):
        return raw
    if sit in {"oral", "futa_blowjob"} and not _ORAL_SUCK_RE.search(raw):
        return raw
    line = ORAL_IN_MOUTH_SHARE_LINE if share_end else ORAL_IN_MOUTH_LINE
    cut = raw.find("\noverall_soundscape:")
    if cut > 0:
        return raw[:cut].rstrip() + "\n" + line + "\n" + raw[cut:]
    return raw.rstrip() + "\n" + line


START_CAST_LINE = (
    "START CAST: START: one woman only. Closed door. Do not show the resident "
    "until the door opens and she ENTERS FRAME. Not a two-shot at t=0."
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
    cut = text.find("\noverall_soundscape:")
    if cut > 0:
        return text[:cut].rstrip() + "\n" + line + "\n" + text[cut:]
    return text.rstrip() + "\n" + line


def lock_futa_shaft(text: str) -> str:
    """Pin futa penis to erect 20cm, same shape. Still 玉なし＋マンコあり. Never add a penis to NEVER-futanari."""
    raw = str(text or "")
    if not raw or "SHAFT LOOK:" in raw:
        return raw
    has_futa = (
        "Clear futanari" in raw
        or "Erect 20cm" in raw
        or "erect 20cm" in raw
        or "futanari: erect" in raw.lower()
    )
    if not has_futa:
        return raw
    return _inject_before_soundscape(raw, SHAFT_LOOK_LINE)


def lock_meat_wall_look(text: str, *, story_id: str = "", clip_index: int = 0) -> str:
    """Meat-wall: Rei is already futa; brown slime is whole-body; bath is glue-thick."""
    raw = str(text or "")
    sid = str(story_id or "").strip()
    if not raw:
        return raw
    if sid == "meat-wall-85s":
        if "FUTA LOCK:" not in raw:
            raw = _inject_before_soundscape(raw, MEAT_FUTA_LINE)
        if "BROWN SLIME:" not in raw:
            raw = _inject_before_soundscape(raw, MEAT_SLIME_LINE)
        if "BATH LOOK:" not in raw:
            raw = _inject_before_soundscape(raw, BATH_LOOK_LINE)
        return raw
    if sid == "semen-bath-70s" and "BATH LOOK:" not in raw:
        return _inject_before_soundscape(raw, BATH_LOOK_LINE)
    return raw


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


def lock_urine_look(text: str) -> str:
    """H3 skips pee unless the prompt names yellow water from the tip hole, like semen."""
    raw = str(text or "")
    if not raw or "URINE LOOK:" in raw:
        return raw
    if not _URINE_CUE_RE.search(raw):
        return raw
    if _URINE_NEG_RE.search(raw) and not re.search(
        r"yellow stream|yellow urine|pees a |drinks the yellow|peeing", raw, re.I
    ):
        return raw
    return _inject_before_soundscape(raw, URINE_LOOK_LINE)


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
    "Breath hitches. She is enjoying the jupo. Not a work mask. Not a straight clinical face."
)
ORGASM_FACE_LINE = (
    "ORGASM FACE: Climax face. She is coming hard. Eyes rolling or squeezed shut, mouth open, "
    "brows up, flushed, shaking through the pulses. Extremely good. Not a calm work face. "
    "Not a straight clinical face."
)
SEX_PLEASURE_LINE = (
    "PLEASURE FACE: Both look like it feels really good, not blank. Flushed, mouths open, "
    "brows knit, hips moving. Not a work mask. Not a straight clinical face."
)


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
    "Then mouth-to-mouth semen share, a filthy deep wet kiss. tongues wrap and tangle around a heavy pool of "
    "opaque sticky white liquid, pushing it back and forth, gooey strands stretching "
    "between the tongues, coating both tongues, lips, and chins. The white liquid STAYS on both faces."
)
SEMEN_SHARE_LINE = (
    "SEMEN SHARE: After the last pulse, mouth off the penis. HOLD STILL: a heavy clingy sticky gooey pool of "
    "opaque white liquid sits on the tongue, viscous, not watery, not a thin drip. "
    "The woman who was sucking STANDS UP off her knees until her eyes are at the SAME EYE LEVEL "
    "as the partner. If the partner was sitting or lying, they sit up or stand so both faces meet at equal height. "
    f"{SEMEN_SHARE_KISS} "
    "Do NOT kiss from the knees. Do NOT look up from the floor. Do NOT stay kneeling or squatting for the kiss. "
    "Do not swallow it all first. Do not add a new clip."
)
SEMEN_SHARE_BEAT = (
    "HOLD STILL: a heavy clingy sticky gooey pool of opaque white liquid sits on the tongue, viscous, "
    "not watery. The woman who was sucking STANDS UP off her knees "
    "to the partner's SAME EYE LEVEL. If the partner was sitting or lying, they sit up or stand to meet her. "
    f"{SEMEN_SHARE_KISS} "
    "Do NOT kiss from the knees. Do not swallow it all first."
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
    "meat-wall-85s",
})
# story_id -> (clip_index, mode). silent_next = drop blowjob LoRA. after_speech = keep the line.
# on_cumouf = last seconds of the CUMOUF clip (next speaker is a third person / driving / job).
SEMEN_SHARE_BY_STORY: dict[str, list[tuple[int, str]]] = {
    "bath-120s": [(10, "silent_next")],
    "dinner-120s": [(10, "silent_next")],
    "futon-120s": [(10, "silent_next")],
    "okaeri-120s": [(8, "silent_next")],
    "lecture-120s": [(7, "silent_next")],
    "dishes-90s": [(11, "silent_next")],
    "cafe-100s": [(9, "after_speech")],
    "checkup-100s": [(8, "after_speech")],
    "clinic-75s": [(4, "on_cumouf")],
    "homecoming-90s": [(10, "after_speech")],
    "karaoke-50s": [(4, "after_speech")],
    "sales-visit-60s": [(7, "after_speech")],
    "train-sales-80s": [(7, "after_speech")],
    "engawa-120s": [(10, "on_cumouf")],
    "sunday-120s": [(10, "on_cumouf")],
    "last-stop-40s": [(2, "on_cumouf")],
    "last-train-120s": [(3, "on_cumouf")],
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


def lock_semen_share_kiss(text: str) -> str:
    """Idempotent marker: HOLD white, ジュボ側 stands to eye level, then 濃厚キス 口移し."""
    raw = str(text or "")
    if not raw:
        return raw
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
    """Rewrite the share clip so the last seconds are HOLD white liquid + stand-to-eye-level 口移し."""
    raw = str(prompt or "")
    if not raw or "SEMEN SHARE:" in raw:
        return raw
    mode = str(where or "").strip()
    share_end = (
        f"After the last pulse, mouth off. {SEMEN_SHARE_BEAT} "
        "End: standing at the SAME EYE LEVEL, tongues sharing the thick white liquid, not still on the shaft, not kneeling."
    )
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
    ("ドロドロの白い液体", "thick gooey sticky white liquid"),
    ("身を胸につける", "presses her body flush against the chest"),
    ("シコシコオナニー", "stroking the erect penis"),
    ("黄色い水", "yellow urine"),
    ("濃厚キス", "deep filthy wet kiss"),
    ("口移し", "mouth-to-mouth semen share"),
    ("ベロチュー", "wet tongue kiss"),
    ("ジュボ側", "woman who was sucking"),
    ("イキ顔", "climax face"),
    ("画面右手", "camera right"),
    ("シコシコ", "stroking"),
    ("ネットリ", "clingy sticky"),
    ("ヌルヌル", "slick and slimy"),
    ("ドロドロ", "thick gooey"),
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
        f"{frame}. ONE UNBROKEN 15-second take. The camera never cuts.\n"
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
    """12 independent 15s dirty daily shorts. Prompts and LoRA situations are built here, no LLM."""
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
                "Already on. Mother sucks her daughter's 20cm to the BASE the whole 15-second take. "
                "Filthy sloppy jupo. Drool ropes. No climax. No speech."
            ),
            "camera": _SHORTS_CAM_ORAL_STAND,
            "action": (
                "Already on. Sayaka's mouth is already at Rei's base in the open genkan, like this is everyday. "
                "Deep filthy jupo-jupo the whole 15-second take. Thick saliva ropes swing from her lips onto "
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
                "After the last pulse: mouth off. HOLD STILL a heavy ネットリ sticky pool of opaque white liquid "
                "on the tongue, viscous (ドロドロ). Overflow clings to chin, lips, and breasts and STAYS. "
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
                "15-second take. Thick saliva strings drop onto the concrete between her knees. Rei's unused pussy "
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
                "Sayaka licks her daughter's hairless pussy at the base of the unused 20cm the whole 15-second take. "
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
                "They fuck the whole 15-second take, dirty noon sweat, juices running down Aya's standing thigh. "
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
                "Deep filthy jupo-jupo the whole 15-second take. Spit and shower water rope off her lips onto "
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
                "After the last pulse: mouth off. HOLD STILL a heavy ネットリ sticky pool of opaque white liquid "
                "on the tongue, viscous (ドロドロ). Overflow clings to chin, lips, and breasts and STAYS. "
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
                "daughter fuck the whole 15-second take. Sweat, wet slaps, juices on the sheet. The joining point stays "
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
                "15-second take. Wet slaps, juices on the cushion, Aya's mini breasts bouncing. The joining point stays "
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
                "could see. They fuck the whole 15-second take. Sweat, wet slaps on wood, juices dripping. The joining "
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
                "floor. Filthy doggy the whole 15-second take. Wet slaps, hanging breasts, juices on the tile. The joining "
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
                "They fuck the whole 15-second take, dirty and hurried, juices on Sayaka's standing thigh. The joining "
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
        prompt = lock_pleasure_face(prompt, situation=str(spec["situation"]))
        if spec["situation"] == "oral_creampie":
            prompt = lock_semen_share_kiss(inject_semen_share_into_prompt(prompt, where="on_cumouf"))
        clips.append(
            {
                "id": spec["id"],
                "label": spec["label"],
                "situation": spec["situation"],
                "names": list(spec["names"]),
                "canvas": canvas,
                "start": "still_or_t2v",
                "duration_s": 15,
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
        "duration_s": 15 * len(clips),
        "clip_s": 15,
        "seamless": False,
        "use_cast_ref": True,
        "spoken_no_kanji": True,
        "canvas": dict(CANVAS_9_16),
        "stills_dir": "cast",
        "comment_ja": (
            "15秒完結の超濃厚日常インモラル×12。メイン4人のうち竿役（レイ／マドカ）とハメ役（アヤ／サヤカ）の2人。"
            "つなぎなし。各本は input/cast/ の人物写真を R2V 参照。フェラは 9:16 寄り（blowjob LoRA）、"
            "挿入は 16:9 か立ち 9:16。部品は situation から自動。FL2VA の竿は載せない。穴（synth-pussy）は載せる。"
        ),
        "download": list(SITUATION_DOWNLOAD["shorts-immoral"]),
        "clips": clips,
    }

def semen_share_follow_errors(story: dict[str, Any]) -> list[str]:
    """口移し is standing at equal eye level, not a kneeling look-up kiss."""
    errors: list[str] = []
    clips = list(story.get("clips") or [])
    for i, mode in semen_share_plan(story):
        if i < 0 or i >= len(clips):
            continue
        n = i + 1
        prompt = str(clips[i].get("prompt") or "")
        locked = lock_semen_share_kiss(inject_semen_share_into_prompt(prompt, where=mode))
        low = locked.lower()
        if "stands up" not in low and "stand up" not in low:
            errors.append(f"clip {n}: 口移し must have the sucking woman stand up")
        if "eye level" not in low:
            errors.append(f"clip {n}: 口移し must meet at the same eye level")
        if "they lean in" in low:
            errors.append(f"clip {n}: 口移し must not kiss by leaning in from the knees")
    return errors


def validate_story_follow(story: dict[str, Any]) -> list[str]:
    """H3 following: 10s speech / 15s silent acts / 15s anthology. One place, act cameras, lip-sync only on speaking face clips. Addon act clips need a pose-prep leftover on the previous clip."""
    errors: list[str] = []
    clips = list(story.get("clips") or [])
    anthology = str(story.get("kind") or "") == "anthology"
    clip_s = float(story.get("clip_s") or (15.0 if anthology else 10.0))
    # 建前 packs carry one short exchange (2 speakers) in a 10s face clip. Default stays 1.
    spoken_max = max(1, min(2, int(story.get("spoken_max") or 1)))
    for i, clip in enumerate(clips):
        n = i + 1
        duration = float(clip.get("duration_s") or clip_s)
        prompt = str(clip.get("prompt") or "")
        situation = str(clip.get("situation") or "").strip()
        lines = spoken_lines(prompt)
        if anthology:
            if abs(duration - 15.0) > 0.01:
                errors.append(f"clip {n}: duration_s must be 15 for H3 following (got {duration:g})")
            if "15-second take" not in prompt and "15-second" not in prompt:
                errors.append(f"clip {n}: anthology clips must be a 15-second take")
        else:
            if abs(duration - 10.0) > 0.01 and abs(duration - 15.0) > 0.01:
                errors.append(f"clip {n}: duration_s must be 10 or 15 for H3 following (got {duration:g})")
            if abs(duration - 15.0) < 0.01:
                addon = str(story.get("id") or "") in ADDON_PACK_IDS or bool(story.get("addon"))
                if lines and not (addon and situation == "futa_visible"):
                    errors.append(f"clip {n}: spoken clips stay 10s (leftover seconds fill with extra speech)")
                if "15-second take" not in prompt and "15-second" not in prompt:
                    errors.append(f"clip {n}: 15s clip must be a 15-second take")
                if "10-second take" in prompt:
                    errors.append(f"clip {n}: 15s clip must not say 10-second take")
            elif "15-second take" in prompt or "15-second" in prompt:
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
            if situation in {"oral", "oral_creampie", "cunnilingus_futa"} and "Full bodies from head to feet" in prompt:
                errors.append(f"clip {n}: oral/cunni clip must not be a full-body wide")
            if situation in {"oral", "oral_creampie"} and "close" not in prompt_l and "medium-close" not in prompt_l:
                errors.append(f"clip {n}: oral camera must be close or medium-close")
            if situation == "cunnilingus_futa" and "close-up" not in prompt_l and "extreme close" not in prompt_l:
                errors.append(f"clip {n}: cunnilingus camera must be a close-up")
            if situation in {"futa_sex", "doggy", "riding"} and "joining" not in prompt_l and "already in" not in prompt_l and "already joined" not in prompt_l:
                errors.append(f"clip {n}: sex clip must already be in / show the joining point")
            if situation == "futa_masturbation" and "strok" not in prompt_l and "pump" not in prompt_l and "lap" not in prompt_l:
                errors.append(f"clip {n}: masturbation clip needs a lap/hand camera")
            if situation in SEMEN_SITUATIONS:
                look = lock_semen_look(prompt, situation=situation)
                look_l = look.lower()
                if "white liquid" not in look_l:
                    errors.append(f"clip {n}: ejaculation must name a white liquid")
                if "viscous" not in look_l and "sticky" not in look_l and "ドロドロ" not in look:
                    errors.append(f"clip {n}: ejaculation must be viscous / ドロドロ")
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
        clip_s = float(data.get("clip_s") or 15)
        if abs(clip_s - 15.0) > 0.01:
            raise SystemExit("短編集の1本は 15秒です。")
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
        if abs(clip_s - 15.0) > 0.01:
            raise SystemExit("物語の追加の1本は 15秒です。")
    elif chain_pack:
        if n < 4 or n > 12:
            raise SystemExit("つなぐパックは 4〜12本です。")
        if not data.get("seamless"):
            raise SystemExit("つなぐパックは seamless: true です。")
    elif n < 8 or n > 12:
        raise SystemExit("専用ストーリーは 8〜12本です。")
    if abs(clip_s - 10.0) > 0.01 and abs(clip_s - 15.0) > 0.01:
        raise SystemExit("専用ストーリーの1本は 10秒または 15秒です。")
    clip_durs = [float(c.get("duration_s") or clip_s) for c in clips]
    for d in clip_durs:
        if abs(d - 10.0) > 0.01 and abs(d - 15.0) > 0.01:
            raise SystemExit("専用ストーリーの1本は 10秒または 15秒です。")
    if addon and any(abs(d - 15.0) > 0.01 for d in clip_durs):
        raise SystemExit("物語の追加の1本は 15秒です。")
    if int(data.get("min_age") or 0) < 21:
        raise SystemExit("専用ストーリーは 21歳以上のみです。")
    duration = float(data.get("duration_s") or 0)
    if duration > 120:
        raise SystemExit("専用ストーリーは 120秒までです。")
    if addon and abs(duration - 30.0) > 0.51:
        raise SystemExit("物語の追加は 30秒です。")
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
    raw_prompt = lock_futa_shaft(raw_prompt)
    raw_prompt = lock_start_cast(raw_prompt)
    raw_prompt = lock_semen_look(raw_prompt, situation=situation)
    raw_prompt = lock_meat_wall_look(raw_prompt, story_id=str(story.get("id") or ""), clip_index=index)
    raw_prompt = lock_urine_look(raw_prompt)
    raw_prompt = lock_spoken_emotion(raw_prompt)
    if share_mode == "on_cumouf":
        raw_prompt = lock_oral_in_mouth(raw_prompt, situation=situation, ending="share")
        raw_prompt = lock_semen_share_kiss(inject_semen_share_into_prompt(raw_prompt, where="on_cumouf"))
        raw_prompt = lock_pleasure_face(raw_prompt, situation="oral_creampie")
    elif share_mode in {"silent_next", "after_speech"}:
        raw_prompt = lock_semen_share_kiss(inject_semen_share_into_prompt(raw_prompt, where=share_mode))
        if share_mode == "silent_next":
            situation = "futa_visible"
            label = apply_semen_share_label(label, mode=share_mode)
    else:
        raw_prompt = lock_oral_in_mouth(raw_prompt, situation=situation)
        raw_prompt = lock_pleasure_face(raw_prompt, situation=situation)
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
    duration_s = float(clip.get("duration_s") or story.get("clip_s") or 10)
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
