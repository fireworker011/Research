"""スタイル署名。量産に見えないよう、9軸の組を動画ごとに変える。

連続する2本の共有軸は最大2。直近5本との共有は最大3。完全一致は不可。
公開済み5本は常に比較対象で、各軸の共有は最大2（はっきり違える）。
サムネは直前および公開済みと、C・P・T のうち2つ以上が違うこと。
"""

from __future__ import annotations

import csv
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path

from irasutoya_short.constants import FPS

AXES = ("C", "P", "T", "F", "H", "M", "B", "L", "A")
LAST5 = 5
MAX_SHARED_PREV = 2
MAX_SHARED_LAST5 = 3
MAX_SHARED_PUBLISHED = 2

LENGTHS = {
    "L1": (15.0, 20.0),
    "L2": (21.0, 30.0),
    "L3": (31.0, 40.0),
    "L4": (41.0, 50.0),
    "L5": (51.0, 60.0),
}

BGM_TRACK = {
    "B1": "none",
    "B2": "piano",
    "B3": "lofi",
    "B4": "xylophone",
    "B5": "guitar",
    "B6": "ambience",
}

# ラベルは STYLE-VARIATION.md の選択肢と同じ。
MATRIX: dict[str, dict[str, dict[str, str]]] = {
    "kane": {
        "C": {
            "C1": "中央1人+下テロップ",
            "C2": "左右2人の対話",
            "C3": "明細・書類アップ+人物小",
            "C4": "ランキング縦リスト",
            "C5": "Q&A 2分割",
            "C6": "4コマ風の枠",
        },
        "P": {
            "P1": "白×紺",
            "P2": "クリーム×赤",
            "P3": "ミント×黒",
            "P4": "黄×濃グレー",
            "P5": "薄紫×白",
            "P6": "夜の紺×金",
        },
        "T": {
            "T1": "上部帯",
            "T2": "下部帯",
            "T3": "左縦書き",
            "T4": "吹き出し",
            "T5": "中央大きく1語",
            "T6": "右下付箋風",
        },
        "F": {
            "F1": "ゴシック太",
            "F2": "丸ゴシック",
            "F3": "明朝",
            "F4": "手書き風",
            "F5": "角ゴ細+太の強調",
            "F6": "ポップ体",
        },
        "H": {
            "H1": "質問から",
            "H2": "数字から",
            "H3": "失敗の結果から",
            "H4": "セリフから",
            "H5": "「あるある」宣言",
            "H6": "無音の書類アップから",
        },
        "M": {
            "M1": "1.5秒カット",
            "M2": "2.5秒",
            "M3": "4秒ゆっくり",
            "M4": "前半速く後半遅く",
            "M5": "一定+最後に溜め",
            "M6": "静止多めの紙芝居",
        },
        "B": {
            "B1": "なし（声のみ）",
            "B2": "軽いピアノ",
            "B3": "ローファイ",
            "B4": "木琴系コミカル",
            "B5": "アコギ",
            "B6": "環境音のみ",
        },
        "L": {
            "L1": "15–20秒",
            "L2": "21–30秒",
            "L3": "31–40秒",
            "L4": "41–50秒",
            "L5": "51–60秒",
        },
        "A": {
            "A1": "人物2+小物3",
            "A2": "人物1+書類多め",
            "A3": "小物中心（人物最小）",
            "A4": "人物3以上の群像",
            "A5": "背景写真風+イラスト少",
            "A6": "図形・表中心（イラスト5枚以下）",
        },
    },
    "pet": {
        "C": {
            "C1": "ソファ側の固定",
            "C2": "床目線ローアングル",
            "C3": "見守りカメラ俯瞰",
            "C4": "窓辺の逆光",
            "C5": "寄りのクローズアップ",
            "C6": "引きの部屋全体",
        },
        "P": {
            "P1": "グレー×暖色の部屋",
            "P2": "白×木目",
            "P3": "夕方オレンジ",
            "P4": "朝の青白",
            "P5": "夜の間接照明",
            "P6": "モノトーン",
        },
        "T": {
            "T1": "下中央",
            "T2": "上左",
            "T3": "なし（声のみ）",
            "T4": "右縦",
            "T5": "最後だけ中央",
            "T6": "手書きメモ風",
        },
        "F": {
            "F1": "丸ゴシック",
            "F2": "明朝",
            "F3": "手書き風",
            "F4": "細ゴシック",
            "F5": "太ゴシック白縁",
            "F6": "タイプライター風",
        },
        "H": {
            "H1": "「さっきまで○○にいた」",
            "H2": "無音で動きから",
            "H3": "質問",
            "H4": "時刻表示から",
            "H5": "音（鳴き声・物音）から",
            "H6": "結末を先に",
        },
        "M": {
            "M1": "ワンカット長回し",
            "M2": "2カット",
            "M3": "3–4カット",
            "M4": "スロー挿入",
            "M5": "早送り→通常",
            "M6": "静止画→動画",
        },
        "B": {
            "B1": "なし",
            "B2": "オルゴール",
            "B3": "環境音（雨・時計）",
            "B4": "ピアノ",
            "B5": "ローファイ",
            "B6": "ギター",
        },
        "L": {
            "L1": "8–12秒",
            "L2": "13–18秒",
            "L3": "19–25秒",
            "L4": "26–35秒",
            "L5": "36–50秒",
        },
        "A": {
            "A1": "灰猫1匹",
            "A2": "白猫1匹",
            "A3": "2匹",
            "A4": "猫+小物主役",
            "A5": "猫+人の手",
            "A6": "部屋の物→猫登場",
        },
    },
    "konkatsu": {
        "C": {
            "C1": "1人語り",
            "C2": "LINE画面風",
            "C3": "カフェ対面",
            "C4": "チェックリスト",
            "C5": "before/after 2分割",
            "C6": "日記ページ",
        },
        "P": {
            "P1": "ピンク×白",
            "P2": "ベージュ×茶",
            "P3": "ネイビー×白",
            "P4": "ミント×グレー",
            "P5": "夜の紫",
            "P6": "くすみ赤",
        },
        "T": {
            "T1": "上帯",
            "T2": "下帯",
            "T3": "吹き出し",
            "T4": "チャット欄",
            "T5": "中央大",
            "T6": "左寄せ",
        },
        "F": {
            "F1": "丸ゴ",
            "F2": "明朝",
            "F3": "手書き",
            "F4": "太ゴ",
            "F5": "細ゴ",
            "F6": "ポップ",
        },
        "H": {
            "H1": "セリフ",
            "H2": "質問",
            "H3": "数字",
            "H4": "失敗談の結末",
            "H5": "「あるある」",
            "H6": "メッセージ着信音",
        },
        "M": {
            "M1": "1.5秒",
            "M2": "2.5秒",
            "M3": "4秒",
            "M4": "速→遅",
            "M5": "チャット送り",
            "M6": "紙芝居",
        },
        "B": {
            "B1": "なし",
            "B2": "ピアノ",
            "B3": "ローファイ",
            "B4": "ジャズ",
            "B5": "アコギ",
            "B6": "環境音",
        },
        "L": {
            "L1": "15–20",
            "L2": "21–30",
            "L3": "31–40",
            "L4": "41–50",
            "L5": "51–60秒",
        },
        "A": {
            "A1": "人物1",
            "A2": "人物2",
            "A3": "画面UI中心",
            "A4": "小物中心",
            "A5": "文字のみ",
            "A6": "背景写真+人物",
        },
    },
    "beauty": {
        "C": {
            "C1": "棚の正面",
            "C2": "手元アップ",
            "C3": "鏡越し",
            "C4": "フラットレイ俯瞰",
            "C5": "3品並べ比較",
            "C6": "洗面台の引き",
        },
        "P": {
            "P1": "夜の紺×暖色灯",
            "P2": "白×ベージュ",
            "P3": "くすみピンク",
            "P4": "グリーン×木",
            "P5": "モノクロ+1色",
            "P6": "朝の自然光",
        },
        "T": {
            "T1": "上",
            "T2": "下",
            "T3": "品名ラベル風",
            "T4": "右縦",
            "T5": "中央1語",
            "T6": "なし",
        },
        "F": {
            "F1": "明朝",
            "F2": "細ゴ",
            "F3": "手書き",
            "F4": "丸ゴ",
            "F5": "太ゴ",
            "F6": "英字セリフ+和文",
        },
        "H": {
            "H1": "悩みの質問",
            "H2": "手順1から",
            "H3": "結果から",
            "H4": "音（ポンプ・蓋）",
            "H5": "数字",
            "H6": "無言の棚",
        },
        "M": {
            "M1": "1.5秒",
            "M2": "3秒",
            "M3": "長回し",
            "M4": "速→遅",
            "M5": "手順ごと区切り",
            "M6": "スロー多め",
        },
        "B": {
            "B1": "なし",
            "B2": "ローファイ",
            "B3": "ピアノ",
            "B4": "環境音",
            "B5": "アンビエント",
            "B6": "アコギ",
        },
        "L": {
            "L1": "15–20",
            "L2": "21–30",
            "L3": "31–40",
            "L4": "41–50",
            "L5": "51–60秒",
        },
        "A": {
            "A1": "商品のみ",
            "A2": "手+商品",
            "A3": "棚全体",
            "A4": "イラスト図解",
            "A5": "文字カード",
            "A6": "実写風背景+図",
        },
    },
    "bousai": {
        "C": {
            "C1": "地図・図解",
            "C2": "チェックリスト",
            "C3": "部屋の中の再現",
            "C4": "Q&A",
            "C5": "時系列タイムライン",
            "C6": "持ち物の並べ",
        },
        "P": {
            "P1": "白×オレンジ",
            "P2": "紺×黄",
            "P3": "グレー×赤",
            "P4": "緑×白",
            "P5": "黒×黄",
            "P6": "水色×紺",
        },
        "T": {
            "T1": "上帯",
            "T2": "下帯",
            "T3": "左リスト",
            "T4": "中央大",
            "T5": "吹き出し",
            "T6": "ラベル",
        },
        "F": {
            "F1": "太ゴ",
            "F2": "丸ゴ",
            "F3": "UD ゴシック",
            "F4": "明朝",
            "F5": "角ゴ細+太",
            "F6": "手書き",
        },
        "H": {
            "H1": "質問",
            "H2": "数字",
            "H3": "「その時」の状況",
            "H4": "警報音風の効果音（控えめ）",
            "H5": "よくある誤解",
            "H6": "持ち物の1つから",
        },
        "M": {
            "M1": "1.5秒",
            "M2": "2.5秒",
            "M3": "4秒",
            "M4": "速→遅",
            "M5": "リスト送り",
            "M6": "紙芝居",
        },
        "B": {
            "B1": "なし",
            "B2": "落ち着いたピアノ",
            "B3": "アンビエント",
            "B4": "環境音",
            "B5": "軽いシンセ",
            "B6": "アコギ",
        },
        "L": {
            "L1": "15–20",
            "L2": "21–30",
            "L3": "31–40",
            "L4": "41–50",
            "L5": "51–60秒",
        },
        "A": {
            "A1": "図解中心",
            "A2": "人物+図解",
            "A3": "物の写真風",
            "A4": "地図",
            "A5": "文字カード",
            "A6": "イラスト（いらすとや ≤20枚）",
        },
    },
}

# 公開済み金メモは実ファイルの絵と尺から読む。クリームの事務所、中央の会社員、下テロップ、
# ゴシック、木琴、21–30秒、会社員6人。カットの中央値は約1.5秒。フックだけ違う。
# ペットの2本はこのリポジトリに動画が無い。比較枠として予約し、実測ではない。
PUBLISHED_ROWS = (
    {
        "date": "2026-10-14",
        "line": "kane",
        "video_id": "01",
        "status": "published",
        "signature": "kane:C1-P2-T2-F1-H3-M1-B4-L2-A4",
        "length_sec": "22.00",
        "irasutoya_count": "6",
        "bgm_track": "xylophone",
        "credit_ok": "no",
        "notes": "公開済み。再書き出ししない。イラストクレジットは当時なし。カット中央値約1.5秒",
    },
    {
        "date": "2026-10-14",
        "line": "kane",
        "video_id": "13",
        "status": "published",
        "signature": "kane:C1-P2-T2-F1-H1-M1-B4-L2-A4",
        "length_sec": "23.92",
        "irasutoya_count": "6",
        "bgm_track": "xylophone",
        "credit_ok": "no",
        "notes": "公開済み。再書き出ししない。フックは質問",
    },
    {
        "date": "2026-10-14",
        "line": "kane",
        "video_id": "14",
        "status": "published",
        "signature": "kane:C1-P2-T2-F1-H3-M1-B4-L2-A4",
        "length_sec": "23.75",
        "irasutoya_count": "6",
        "bgm_track": "xylophone",
        "credit_ok": "no",
        "notes": "公開済み。再書き出ししない。#01と同じ構図",
    },
    {
        "date": "2026-10-14",
        "line": "pet",
        "video_id": "01",
        "status": "published",
        "signature": "pet:C6-P5-T5-F6-H6-M6-B6-L5-A5",
        "length_sec": "",
        "irasutoya_count": "",
        "bgm_track": "",
        "credit_ok": "unknown",
        "notes": "比較枠の予約。動画ファイルはリポジトリに無いので実測ではない",
    },
    {
        "date": "2026-10-14",
        "line": "pet",
        "video_id": "02",
        "status": "published",
        "signature": "pet:C5-P6-T6-F4-H4-M5-B5-L4-A6",
        "length_sec": "",
        "irasutoya_count": "",
        "bgm_track": "",
        "credit_ok": "unknown",
        "notes": "比較枠の予約。動画ファイルはリポジトリに無いので実測ではない",
    },
)

LOG_HEADER = (
    "date,line,video_id,status,signature,thumb_signature,"
    "shared_axes_with_prev,shared_axes_max_last5,bgm_track,length_sec,"
    "irasutoya_count,credit_ok,notes"
)


@dataclass(frozen=True)
class Signature:
    line: str
    C: str
    P: str
    T: str
    F: str
    H: str
    M: str
    B: str
    L: str
    A: str

    def text(self) -> str:
        body = "-".join(getattr(self, name) for name in AXES)
        return f"{self.line}:{body}"

    def thumb(self) -> str:
        return f"thumb:{self.C}-{self.P}-{self.T}-{self.F}"

    def axes(self) -> dict[str, str]:
        data = {name: getattr(self, name) for name in AXES}
        data["line"] = self.line
        return data


def parse_signature(text: str) -> Signature:
    if ":" not in text:
        raise ValueError(f"署名にラインがありません: {text}")
    line, body = text.split(":", 1)
    parts = body.split("-")
    if line not in MATRIX:
        raise ValueError(f"未知のライン: {line}")
    if len(parts) != len(AXES):
        raise ValueError(f"軸が9つではありません: {text}")
    values: dict[str, str] = {}
    for axis, part in zip(AXES, parts):
        if part not in MATRIX[line][axis]:
            raise ValueError(f"{line} に {part} はありません")
        values[axis] = part
    return Signature(line, **values)


def shared_axes(left: Signature, right: Signature) -> int:
    return sum(getattr(left, name) == getattr(right, name) for name in AXES)


def thumb_changes(left: Signature, right: Signature) -> int:
    return sum(getattr(left, name) != getattr(right, name) for name in ("C", "P", "T"))


def same_axes(left: Signature, right: Signature) -> bool:
    return shared_axes(left, right) == len(AXES)


def published_signatures() -> list[Signature]:
    return [parse_signature(row["signature"]) for row in PUBLISHED_ROWS]


def kane_published_history() -> list[Signature]:
    return [parse_signature(row["signature"]) for row in PUBLISHED_ROWS if row["line"] == "kane"]


def check_signature(
    candidate: Signature,
    history: list[Signature],
    published: list[Signature] | None = None,
) -> dict:
    """history は同じラインの古い順。末尾が直前の動画。"""
    published = published_signatures() if published is None else published
    errors: list[str] = []
    prev = history[-1] if history else None
    shared_prev = shared_axes(candidate, prev) if prev else 0
    if prev is not None and shared_prev > MAX_SHARED_PREV:
        errors.append("prev")
    if prev is not None and thumb_changes(candidate, prev) < 2:
        errors.append("thumb")
    shared_last5 = 0
    for old in history[-LAST5:]:
        shared = shared_axes(candidate, old)
        shared_last5 = max(shared_last5, shared)
        if shared > MAX_SHARED_LAST5:
            errors.append("last5")
        if same_axes(candidate, old):
            errors.append("exact")
    shared_published = 0
    for old in published:
        shared = shared_axes(candidate, old)
        shared_published = max(shared_published, shared)
        if shared > MAX_SHARED_PUBLISHED:
            errors.append("published")
        if same_axes(candidate, old):
            errors.append("exact")
        if thumb_changes(candidate, old) < 2:
            errors.append("thumb_published")
    for old in history:
        if same_axes(candidate, old):
            errors.append("exact")
    return {
        "ok": not errors,
        "shared_prev": shared_prev if prev is not None else None,
        "shared_last5": shared_last5,
        "shared_published": shared_published,
        "errors": errors,
    }


def credit_lines(project: dict) -> list[str]:
    lines: list[str] = []
    for scene in project["scenes"]:
        if scene.get("role") == "credit":
            continue
        if not str(scene.get("text") or "").strip():
            continue
        credit = str(scene.get("credit") or "").strip()
        if credit and credit not in lines:
            lines.append(credit)
    lines.append("イラスト：いらすとや")
    return lines


def apply_signature(project: dict, signature: Signature) -> None:
    """台詞は変えず、見た目と尺とクレジット表示だけを署名に合わせる。"""
    project["style_signature"] = signature.text()
    project["style_axes"] = signature.axes()
    project["style_cast"] = choose_cast(list(project.get("asset_paths") or {}), signature.A)
    for scene in project["scenes"]:
        scene["lead"] = 0.0
    if signature.H == "H6":
        for scene in project["scenes"]:
            if scene.get("role") == "hook":
                scene["lead"] = 0.9
                break
    lines = credit_lines(project)
    project["credits"] = lines
    for scene in project["scenes"]:
        if scene.get("role") == "credit":
            scene["telop"] = "\n".join(lines)
            scene["text"] = ""
    settings = project.setdefault("settings", {})
    settings["bgm"] = signature.B != "B1"
    settings["bgm_kind"] = signature.B
    settings["mouth_gain"] = 0.0


def is_person(asset_id: str) -> bool:
    return asset_id.split("_", 1)[0] in {"hero", "rival", "boss"}


def choose_cast(asset_ids: list[str], asset_mix: str) -> list[str]:
    order = [
        "hero_trouble",
        "hero_tired",
        "hero_angry",
        "hero_smile",
        "rival_smug",
        "boss_angry",
        "rival_pale",
        "rival_bow",
    ]
    people = [item for item in order if item in asset_ids]
    people.extend(item for item in asset_ids if is_person(item) and item not in people)
    count = {"A1": 2, "A2": 1, "A3": 1, "A4": 3, "A5": 1, "A6": 1}[asset_mix]
    if asset_mix == "A4" and len(people) < 3:
        raise ValueError("群像にする会社員が3人いません")
    if asset_mix == "A1" and len(people) < 2:
        raise ValueError("2人にする会社員がいません")
    return people[:count]


def _base_frames(scene: dict) -> int:
    seconds = float(scene["voice_seconds"]) + float(scene.get("lead") or 0)
    if scene.get("role") == "credit":
        seconds = max(seconds, 2.0)
    return max(1, int(math.ceil(seconds * FPS - 1e-9)))


def _content_indexes(scenes: list[dict]) -> list[int]:
    indexes = [i for i, scene in enumerate(scenes) if scene.get("role") != "credit"]
    return indexes or list(range(len(scenes)))


def _desired_frames(scenes: list[dict], tempo: str, base: list[int]) -> list[int]:
    content = _content_indexes(scenes)
    half = max(1, len(content) // 2)
    fast = set(content[:half])
    hold = content[-1]
    plain = {"M1": 1.5, "M2": 2.5, "M3": 4.0, "M6": 5.0}
    frames: list[int] = []
    for index, scene in enumerate(scenes):
        if scene.get("role") == "credit":
            want = 2.2
        elif tempo == "M4":
            want = 1.45 if index in fast else 3.9
        elif tempo == "M5":
            want = 5.6 if index == hold else 2.3
        else:
            want = plain[tempo]
        frames.append(max(base[index], int(round(want * FPS))))
    return frames


def _trim_index(frames: list[int], base: list[int], scenes: list[dict], tempo: str) -> int | None:
    content = _content_indexes(scenes)
    half = max(1, len(content) // 2)
    fast = set(content[:half])
    hold = content[-1]
    best: tuple[tuple[int, int], int] | None = None
    for index, scene in enumerate(scenes):
        slack = frames[index] - base[index]
        if slack <= 0:
            continue
        if tempo == "M4":
            rank = 3 if index in fast else 1 if scene.get("role") == "credit" else 0
        elif tempo == "M5":
            rank = 0 if index == hold else 2
        elif tempo == "M6":
            rank = 2 if scene.get("role") == "credit" else 1
        else:
            rank = 1
        key = (rank, slack)
        if best is None or key > best[0]:
            best = (key, index)
    return None if best is None else best[1]


def _weights(scenes: list[dict], tempo: str) -> list[float]:
    content = _content_indexes(scenes)
    half = max(1, len(content) // 2)
    slow = set(content[half:])
    hold = content[-1]
    weights: list[float] = []
    for index, scene in enumerate(scenes):
        if scene.get("role") == "credit":
            weights.append(0.2)
        elif tempo == "M5" and index == hold:
            weights.append(4.0)
        elif tempo == "M4" and index in slow:
            weights.append(3.0)
        elif scene.get("role") == "hook" and tempo not in ("M3", "M6"):
            weights.append(0.35)
        else:
            weights.append(1.0)
    return weights


def _grow_index(weights: list[float], frames: list[int]) -> int:
    best: tuple[tuple[float, int], int] | None = None
    for index, weight in enumerate(weights):
        key = (weight, -frames[index])
        if best is None or key > best[0]:
            best = (key, index)
    if best is None:
        raise RuntimeError("伸ばすシーンがありません")
    return best[1]


def rhythm_ok(scenes: list[dict], tempo: str) -> bool:
    content = [scene for scene in scenes if scene.get("role") != "credit"] or list(scenes)
    durations = [float(scene["duration"]) for scene in content]
    mean = sum(durations) / len(durations)
    if tempo == "M1":
        return mean <= 2.05
    if tempo == "M2":
        return 1.85 <= mean <= 3.35
    if tempo == "M3":
        return mean >= 3.35
    if tempo == "M4":
        half = max(1, len(durations) // 2)
        early = sum(durations[:half]) / half
        late = sum(durations[half:]) / max(1, len(durations) - half)
        return late >= early + 0.5
    if tempo == "M5":
        return max(durations) >= mean + 0.7
    if tempo == "M6":
        holds = 0
        for scene in content:
            slack = float(scene["duration"]) - float(scene["voice_seconds"]) - float(scene.get("lead") or 0)
            if slack >= 1.0:
                holds += 1
        return mean >= 3.9 and holds >= max(1, len(content) // 3)
    raise ValueError(f"未知のテンポ: {tempo}")


def fit_scene_durations(project: dict) -> str:
    """署名の M と L にシーン尺を合わせる。声より短くはしない。"""
    axes = project["style_axes"]
    lo, hi = LENGTHS[axes["L"]]
    lo_f = int(round(lo * FPS))
    hi_f = int(round(hi * FPS))
    scenes = project["scenes"]
    base = [_base_frames(scene) for scene in scenes]
    if sum(base) > hi_f:
        return "speedup"
    frames = _desired_frames(scenes, axes["M"], base)
    guard = 0
    while sum(frames) > hi_f and guard < 20000:
        guard += 1
        index = _trim_index(frames, base, scenes, axes["M"])
        if index is None:
            return "speedup"
        frames[index] -= 1
    weights = _weights(scenes, axes["M"])
    while sum(frames) < lo_f:
        if sum(frames) >= hi_f:
            return "rhythm"
        frames[_grow_index(weights, frames)] += 1
    if not (lo_f <= sum(frames) <= hi_f):
        return "rhythm"
    if not _shape_frames(frames, base, scenes, axes["M"]):
        return "speedup"
    for scene, count in zip(scenes, frames):
        scene["duration"] = count / FPS
    if not rhythm_ok(scenes, axes["M"]):
        return "speedup"
    return "ok"


def _shape_frames(frames: list[int], base: list[int], scenes: list[dict], tempo: str) -> bool:
    """合計は変えず、速い前半や最後の溜めが残るようにコマを移す。"""
    content = _content_indexes(scenes)
    if tempo == "M4":
        half = max(1, len(content) // 2)
        early = content[:half]
        late = content[half:]
        gap = int(round(0.5 * FPS))
        for _ in range(20000):
            early_mean = sum(frames[i] for i in early) / len(early)
            late_mean = sum(frames[i] for i in late) / max(1, len(late))
            if late_mean >= early_mean + gap:
                return True
            donors = [i for i in early if frames[i] > base[i]]
            if not donors:
                return False
            donor = max(donors, key=lambda i: frames[i])
            recv = min(late, key=lambda i: frames[i])
            frames[donor] -= 1
            frames[recv] += 1
        return False
    if tempo == "M5":
        hold = content[-1]
        others = [i for i in content if i != hold]
        gap = int(round(0.7 * FPS))
        for _ in range(20000):
            mean = sum(frames[i] for i in content) / len(content)
            if frames[hold] >= mean + gap:
                return True
            donors = [i for i in others if frames[i] > base[i]]
            if not donors:
                return False
            donor = max(donors, key=lambda i: frames[i])
            frames[donor] -= 1
            frames[hold] += 1
        return False
    return True


def length_ok(seconds: float, length_code: str) -> bool:
    lo, hi = LENGTHS[length_code]
    return lo - 1e-6 <= seconds <= hi + 1e-6


def _probe(scenes: list[dict], tempo: str, length: str, hook: str) -> bool:
    for step in range(5):
        body = 1.16 ** step
        hook_scale = 1.12 ** step
        project = {
            "style_axes": {"M": tempo, "L": length, "H": hook},
            "scenes": [],
        }
        for scene in scenes:
            scale = hook_scale if scene.get("role") == "hook" else body
            project["scenes"].append(
                {
                    "role": scene.get("role"),
                    "voice_seconds": float(scene["voice_seconds"]) / scale,
                    "text": scene.get("text") or "",
                    "lead": 0.0,
                }
            )
        if hook == "H6":
            for scene in project["scenes"]:
                if scene["role"] == "hook":
                    scene["lead"] = 0.9
                    break
        status = fit_scene_durations(project)
        if status == "ok":
            return True
    return False


def feasible_pairs(job: dict) -> dict[str, list[tuple[str, str]]]:
    table: dict[str, list[tuple[str, str]]] = {}
    for hook in MATRIX["kane"]["H"]:
        pairs: list[tuple[str, str]] = []
        for tempo in MATRIX["kane"]["M"]:
            for length in MATRIX["kane"]["L"]:
                if _probe(job["scenes"], tempo, length, hook):
                    pairs.append((tempo, length))
        table[hook] = pairs
    return table


def _random_signature(rng: random.Random, job: dict, table: dict[str, list[tuple[str, str]]]) -> Signature | None:
    hooks = [hook for hook, pairs in table.items() if pairs]
    if not hooks:
        return None
    hook = rng.choice(hooks)
    pairs = table[hook]
    weights = []
    for tempo, length in pairs:
        bias = {"L1": 5, "L2": 5, "L3": 3, "L4": 2, "L5": 2}[length]
        weights.append(bias)
    tempo, length = rng.choices(pairs, weights=weights, k=1)[0]
    values = {"H": hook, "M": tempo, "L": length}
    for axis in ("C", "P", "T", "F", "B", "A"):
        values[axis] = rng.choice(list(MATRIX["kane"][axis]))
    people = int(job["people"])
    if values["A"] == "A4" and people < 3:
        values["A"] = "A2"
    if values["A"] == "A1" and people < 2:
        values["A"] = "A2"
    return Signature("kane", **values)


def assign_unpublished(jobs: list[dict], seed: int = 20261014) -> list[Signature]:
    rng = random.Random(seed)
    history = kane_published_history()
    published = published_signatures()
    assigned: list[Signature] = []
    for job in jobs:
        table = feasible_pairs(job)
        if not any(table.values()):
            raise RuntimeError(f"#{job['video_id']} は尺とテンポの組がありません")
        found: Signature | None = None
        for prefer_new_layout in (True, False):
            for _ in range(6000):
                candidate = _random_signature(rng, job, table)
                if candidate is None:
                    break
                prev = history[-1] if history else None
                if prefer_new_layout and prev is not None and candidate.C == prev.C:
                    continue
                if check_signature(candidate, history, published)["ok"]:
                    found = candidate
                    break
            if found is not None:
                break
        if found is None:
            raise RuntimeError(f"#{job['video_id']} の署名が見つかりません")
        assigned.append(found)
        history.append(found)
    return assigned


def load_jobs(root: Path) -> list[dict]:
    jobs = []
    for path in root.glob("affiliate-shorts/**/project.json"):
        number = int(path.parent.name.split("-", 1)[0])
        if number < 15 or number > 61:
            continue
        project = json.loads(path.read_text(encoding="utf-8"))
        people = [key for key in project.get("asset_paths") or {} if is_person(key)]
        scenes = []
        for scene in project["scenes"]:
            scenes.append(
                {
                    "role": scene.get("role"),
                    "voice_seconds": float(scene["voice_seconds"]),
                    "text": scene.get("text") or "",
                }
            )
        jobs.append(
            {
                "video_id": f"{number:02d}",
                "number": number,
                "folder": str(path.parent.relative_to(root)),
                "n_scenes": len(project["scenes"]),
                "people": len(people),
                "scenes": scenes,
            }
        )
    jobs.sort(key=lambda item: item["number"])
    seen = [item["number"] for item in jobs]
    if seen != list(range(15, 62)):
        raise RuntimeError(f"15から61の動画が揃っていません: {seen}")
    return jobs


def log_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_log(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = LOG_HEADER.split(",")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fields})


def seed_log_rows() -> list[dict[str, str]]:
    rows = []
    for row in PUBLISHED_ROWS:
        signature = parse_signature(row["signature"])
        rows.append(
            {
                "date": row["date"],
                "line": row["line"],
                "video_id": row["video_id"],
                "status": row["status"],
                "signature": signature.text(),
                "thumb_signature": signature.thumb(),
                "shared_axes_with_prev": "",
                "shared_axes_max_last5": "",
                "bgm_track": row["bgm_track"],
                "length_sec": row["length_sec"],
                "irasutoya_count": row["irasutoya_count"],
                "credit_ok": row["credit_ok"],
                "notes": row["notes"],
            }
        )
    return rows


def result_row(
    signature: Signature,
    video_id: str,
    *,
    shared_prev: int,
    shared_last5: int,
    length_sec: float,
    irasutoya_count: int,
    credit_ok: str,
    notes: str,
    date: str = "2026-10-14",
) -> dict[str, str]:
    if shared_prev > MAX_SHARED_PREV or shared_last5 > MAX_SHARED_LAST5:
        raise ValueError(f"#{video_id} は共有軸が上限を超えています")
    if irasutoya_count > 20:
        raise ValueError(f"#{video_id} のいらすとやが20枚を超えています")
    if signature.A == "A6" and irasutoya_count > 5:
        raise ValueError(f"#{video_id} の図形中心はイラスト5枚までです")
    if credit_ok != "yes":
        raise ValueError(f"#{video_id} のクレジットが足りません")
    return {
        "date": date,
        "line": signature.line,
        "video_id": video_id,
        "status": "unreleased",
        "signature": signature.text(),
        "thumb_signature": signature.thumb(),
        "shared_axes_with_prev": str(shared_prev),
        "shared_axes_max_last5": str(shared_last5),
        "bgm_track": BGM_TRACK[signature.B],
        "length_sec": f"{length_sec:.2f}",
        "irasutoya_count": str(irasutoya_count),
        "credit_ok": credit_ok,
        "notes": notes,
    }
