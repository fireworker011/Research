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
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

STUDIO_ROOT = Path(__file__).resolve().parents[1] / "h3-lora-studio"
if not STUDIO_ROOT.is_dir():
    STUDIO_ROOT = Path("/content/h3-lora-studio")

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
    "oral": ["blowjob-h3", "penis-lora-h3", "larry-v4"],
    "general_sex": ["hmnsfw-aio-v25", "larry-v4"],
    "preview": ["hmnsfw-aio-v25", "minimax-h3-turbo-fl2v-4step"],
    "riding": ["cowgirl-position-h3", "penis-lora-h3", "synth-pussy-h3"],
    "doggy": ["doggy-h3", "penis-lora-h3", "synth-pussy-h3"],
    "missionary_pov": ["missionary-pov-h3", "penis-lora-h3", "larry-v4"],
    "after_ejaculation": ["hmcumshot-v2", "penis-lora-h3", "larry-v4"],
    "facial": ["facial-cumshot-h3", "penis-lora-h3", "larry-v4"],
    "creampie": ["final-thrust-h3", "penis-lora-h3", "synth-pussy-h3"],
    "oral_creampie": ["cumouf-h3", "penis-lora-h3", "larry-v4"],
    "fingering": ["fingering-h3", "synth-pussy-h3", "larry-v4"],
    "masturbation": ["hmmasturbation-h3", "synth-pussy-h3", "larry-v4"],
    "footjob": ["footjob-h3", "penis-lora-h3", "larry-v4"],
    "remote_orgasm": ["remote-orgasm-h3", "synth-pussy-h3", "larry-v4"],
    "futa_visible": ["penis-lora-h3", "cinema-dy"],
    "futa_masturbation": ["hmmasturbation-h3", "penis-lora-h3", "larry-v4"],
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
    ],
    "commute-120s": [
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
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
        "hmnsfw-aio-v25",
        "synth-pussy-h3",
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
    "homecoming-90s": "homecoming-90s",
    "dishes-90s": "dishes-90s",
    "commute-120s": "commute-120s",
    "lecture-120s": "lecture-120s",
    "rooftop-100s": "rooftop-100s",
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
    "oral": "フェラ（女体）。フェラ 0.75 + 竿 0.7 + Larry 0.7。受けはふたなり。男なし。",
    "general_sex": "汎用エロ（女体）。AIO 0.8 + Larry 0.5 / 12step。ふたなり＋女。男なし。",
    "preview": "試し打ち（女体）。AIO 0.7 + LightX2V 4step。ふたなり＋女。男なし。",
    "riding": "騎乗位（女体）。騎乗 LoRA 0.8 + 竿 0.7 + 穴の見え方 0.55 / 12step。Turbo なし。AIO は積まない。男なし。",
    "doggy": "後背位（女体）。後背位 LoRA 0.8 + 竿 0.7 + 穴の見え方 0.55 / 12step。Turbo なし。男なし。",
    "missionary_pov": "正常位POV（女体）。POV挿入 0.85 + 竿 0.7 + Larry 0.5 / 8step。男なし。横はセックス（女体）。",
    "after_ejaculation": "後射精（女体）。射精 LoRA 0.9 + 竿 0.7 + Larry 0.5 / 8step。ふたなり。男なし。絶頂・顔射・中出しとは別。",
    "facial": "顔射（女体）。顔射 LoRA 0.8 + 竿 0.7 + Larry 0.5 / 8step。ふたなり＋女。男なし。後射精・絶頂・口内とは別。写真からが本線。",
    "creampie": "中出し（女体）。Final Thrust 0.85 + 竿 0.7 + 穴の見え方 0.55 / 12step。Turbo なし。膣の中に出す。ふたなり＋女。男なし。後射精・顔射・口内とは別。写真からが本線。",
    "oral_creampie": "口内射精（女体）。CUMOUF 0.5 + 竿 0.7 + Larry 0.5 / 8step。口の中で出す。ふたなり＋女。男なし。顔射・フェラ本線とは別。写真からが本線（口が付いた途中の写真）。",
    "fingering": "指入れ。女1人。指 LoRA 0.85 + 穴の見え方 0.55 + Larry 0.5 / 8step。男なし。膣。アナルはアナル指入れ。",
    "masturbation": "オナニー。女1人。潮吹き 0.8 + 穴の見え方 0.55 + Larry 0.5 / 12step。男なし。",
    "footjob": "足コキ（女体）。Type D 0.85 + 竿 0.7 + Larry 0.5 / 8step。ふたなり＋女。男なし。",
    "remote_orgasm": "絶頂。女1人。反応 LoRA 0.8 + 穴の見え方 0.55 + Larry 0.5 / 8step。男なし。射精ではない。",
    "futa_visible": "歩行・会話。竿は出す。行為 LoRA なし。Turbo なし・12step。男なし。",
    "futa_masturbation": "ふたなりオナニー。潮吹き LoRA + 竿 + Larry 12step。男なし。",
    "cunnilingus_futa": "クンニ。竿は使わず垂らす。クンニ + 穴 + 竿薄め + Larry。フェラ LoRA は積まない。男なし。",
    "homecoming-90s": "120秒専用。10秒×12本のカット。クンニ LoRA は寄りの1本だけ（入室は歩行部品）。抜く・歩く・キス退出は別本。写真は input/homecoming-90s の 01〜12（11-lick.jpg は舌と穴の寄り）。",
    "dishes-90s": "洗い物120秒。サヤカはシンクで洗い続ける。レイは椅子で竿。アヤは床で口。入室と着席、キスと床降りは別本。フェラは60秒以降で口元の寄り。口内は CUMOUF。写真は input/dishes-90s の 01〜12。",
    "commute-120s": "登校第1話。朝〜大学正門。15秒×8本＝120秒。16:9 全身。サヤカは家だけ。フェラは玄関と路地の2本。授業は授業120秒。写真は input/commute-120s の 01〜08（16:9）。",
    "lecture-120s": "授業第2話。授業〜昼。15秒×8本＝120秒。16:9。家とサヤカは出さない。机のシコはオナニー部品。クンニ LoRA は寄り1本。根元はフェラ。口内は CUMOUF。昼へ歩く本は歩行。セックスは屋上〜下校。写真は input/lecture-120s の 01〜08（16:9）。",
    "rooftop-100s": "屋上第3話。屋上挿入〜家の門。10秒×10本＝100秒。1本1場所。セリフは口元の2本だけ。セックスは AIO 横クローズ。歩く本にセックス部品なし。玄関は次の話。サヤカなし。写真は input/rooftop-100s の 01〜10（16:9）。",
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
    "photoreal-h3-still": "静止画用の写実",
}

SFW_SITUATIONS = {"sfw_daily", "sfw_preview", "sfw_audio", "sfw_r2v"}
STORY_IDS = {"homecoming-90s", "dishes-90s", "commute-120s", "lecture-120s", "rooftop-100s"}
STORY_CANVAS = (576, 1024)
STORY_CANVAS_16_9 = (1024, 576)


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


def explain_choice(situation: str, mode: str) -> str:
    sid = resolve_situation(situation)
    mid = resolve_mode(mode)
    how = "テキストから動画（写真は使いません）" if mid == "t2v" else "写真1枚から動画（Drive の input に jpg）"
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
    return (
        f"シーン: {situation}\n"
        f"作り方: {how}\n"
        f"説明: {SITUATION_HELP[sid]}\n"
        f"使う部品: {parts}\n"
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
STUDIO_OBJECT_INFO_NODES = (
    "MiniMaxH3ImageToVideo",
    "MiniMaxH3TextToVideo",
    "LoraLoaderModelOnly",
    "VAEDecodeAudio",
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


def comfy_has_h3(port: int = 8188) -> bool:
    try:
        return "MiniMaxH3ImageToVideo" in fetch_comfy_node_info(port, "MiniMaxH3ImageToVideo")
    except Exception:
        return False


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


def restart_studio_comfy(comfy_dir: Path | str, *, port: int = 8188) -> None:
    """New LoRAs are invisible until Comfy restarts."""
    subprocess.run(["fuser", "-k", f"{port}/tcp"], check=False, capture_output=True)
    time.sleep(2)
    log = Path("/content/comfyui.log")
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
    """Unload models after OOM only. Do not call between successful chain clips."""
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
    "Do not restart the scene. Keep identity, clothes, and lighting. "
    "Natural ongoing motion. No freeze frame, no jump cut."
)


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
    if is_blank_prompt(extra):
        return continue_chain_prompt(prev_prompt or first)
    body = continue_chain_prompt(extra.strip())
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
    text = str(prompt or "").strip()
    if CHAIN_CONTINUE_LINE in text:
        if "Picture 1" in text:
            return text
        wrapped, _ = apply_user_prompt(text, mode="i2v", default_prompt=text)
        return wrapped
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
        text or "Continue the same live scene.",
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


def prepend_triggers(prompt: str, stack: list[dict[str, Any]]) -> str:
    triggers = []
    low = prompt.lower()
    for item in stack:
        trig = str(item.get("trigger") or "").strip()
        if trig and trig.lower() not in low:
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


def story_canvas_wh(story: dict[str, Any]) -> tuple[int, int]:
    canvas = story.get("canvas") if isinstance(story.get("canvas"), dict) else {}
    w = int(canvas.get("width") or 0)
    h = int(canvas.get("height") or 0)
    if w >= 32 and h >= 32:
        return w, h
    aspect = str(canvas.get("aspect") or "9:16").replace("：", ":")
    if aspect in {"16:9", "16/9"}:
        return STORY_CANVAS_16_9
    return STORY_CANVAS


def load_story(story_id: str, *, studio_root: Path | str | None = None) -> dict[str, Any]:
    sid = str(story_id or "").strip()
    if sid in SITUATION_JA:
        sid = SITUATION_JA[sid]
    path = stories_dir(studio_root) / f"{sid}.json"
    if not path.is_file():
        raise SystemExit(f"専用ストーリーがありません: {sid}")
    data = json.loads(path.read_text(encoding="utf-8"))
    clips = data.get("clips") or []
    n = len(clips)
    clip_s = float(data.get("clip_s") or 10)
    if n < 8 or n > 12:
        raise SystemExit("専用ストーリーは 8〜12本です。")
    if abs(clip_s - 10.0) > 0.01 and abs(clip_s - 15.0) > 0.01:
        raise SystemExit("専用ストーリーの1本は 10秒または 15秒です。")
    clip_durs = [float(c.get("duration_s") or clip_s) for c in clips]
    for d in clip_durs:
        if abs(d - 10.0) > 0.01 and abs(d - 15.0) > 0.01:
            raise SystemExit("専用ストーリーの1本は 10秒または 15秒です。")
    if int(data.get("min_age") or 0) < 21:
        raise SystemExit("専用ストーリーは 21歳以上のみです。")
    duration = float(data.get("duration_s") or 0)
    if duration > 120:
        raise SystemExit("専用ストーリーは 120秒までです。")
    if abs(duration - sum(clip_durs)) > 0.51:
        raise SystemExit("専用ストーリーの秒数と本数が合いません。")
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
) -> dict[str, Any]:
    """One story clip. Hard cut: photo if present, else T2V. Matching LoRA per act."""
    clips = list(story.get("clips") or [])
    if index < 0 or index >= len(clips):
        raise SystemExit(f"クリップ番号が範囲外です: {index}")
    clip = clips[index]
    situation = str(clip.get("situation") or "").strip()
    raw_prompt = str(clip.get("prompt") or "").strip()
    start = str(clip.get("start") or "still_or_t2v").strip()
    seamless = bool(story.get("seamless"))
    still_dir = Path(stills_dir) if stills_dir is not None else Path(".")
    still_path = resolve_story_still(
        clip, still_dir, clip_index=index, override=clip0_override
    )
    missing_still = None
    want_still = start == "still_or_t2v" or bool(clip.get("still"))
    if want_still and still_path is None:
        missing_still = str(clip.get("still") or "") or None
    use_last = bool(seamless and start == "continue" and last_frame and still_path is None)
    if still_path is not None:
        mode = "i2v"
        prompt = lock_i2v_story_prompt(raw_prompt, continue_from_last=False)
        first_kind = "still"
    elif use_last:
        mode = "i2v"
        prompt = lock_i2v_story_prompt(raw_prompt, continue_from_last=True)
        first_kind = "last_frame"
    else:
        mode = "t2v"
        prompt, _ = apply_user_prompt(raw_prompt, mode="t2v", default_prompt=raw_prompt)
        first_kind = "t2v"

    studio_sys_path(studio_root)
    from select_loras import select_loras

    root = Path(studio_root or STUDIO_ROOT)
    cat = Path(catalog_path) if catalog_path else root / "catalog" / "loras.json"
    profiles = root / "profiles"
    try:
        cfg = select_loras(
            profile_name=situation,
            mode=mode,
            prompt_arg=prompt,
            catalog_path=cat,
            profiles_dir=profiles,
            turbo_override=None,
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
            turbo_override=None,
        )
    stack = list(cfg.get("stack") or [])
    prompt = prepend_triggers(str(cfg.get("prompt") or prompt), stack)
    width, height = story_canvas_wh(story)
    return {
        "index": index,
        "label": str(clip.get("label") or f"clip {index + 1}"),
        "situation": situation,
        "mode": mode,
        "prompt": prompt,
        "stack": stack,
        "sampler": cfg.get("sampler") or {},
        "cfg": cfg,
        "still_path": still_path,
        "first_kind": first_kind,
        "missing_still": missing_still,
        "stack_changed": bool(prev_situation) and prev_situation != situation,
        "width": width,
        "height": height,
        "duration_s": float(clip.get("duration_s") or story.get("clip_s") or 10),
        "turbo": bool(cfg.get("turbo")),
    }
