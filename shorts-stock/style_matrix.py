"""Style signatures for pet, konkatsu, and beauty.

The matrix is STYLE-VARIATION.md. Comparison is inside one channel.
A new video may share at most 2 axes with the previous video and at most 3
with any of the last 5, and must not match any earlier signature exactly.
The thumbnail must differ from the previous video in at least 2 of C, P, T.
Length stays on the script. The last frame may be held for at most 1.5 seconds.
"""

from __future__ import annotations

import csv
import json
import random
import subprocess
import sys
from pathlib import Path

from pack_meta import STOCK, iter_packs

LOG_PATH = STOCK / "style-log.csv"
AXES = ("C", "P", "T", "F", "H", "M", "B", "L", "A")
LOG_FIELDS = (
    "date",
    "line",
    "video_id",
    "status",
    "signature",
    "thumb_signature",
    "shared_axes_with_prev",
    "shared_axes_max_last5",
    "bgm_track",
    "length_sec",
    "irasutoya_count",
    "credit_ok",
    "notes",
)
CREDIT = "VOICEVOX:冥鳴ひまり"

# Published pet #01 and #02. Same template, grey then white. Do not restyle them.
PUBLISHED = {
    "2026-10-12/pet/01-gray-sofa-rug": {
        "video_id": "01",
        "signature": "pet:C1-P1-T3-F1-H2-M3-B1-L1-A1",
        "notes": "公開済み。ソファ側・暖色・文字なし・無音の動き・3カット・BGMなし・12秒・灰猫。",
    },
    "2026-10-12/pet/02-white-sofa-rug": {
        "video_id": "02",
        "signature": "pet:C1-P1-T3-F1-H2-M3-B1-L1-A2",
        "notes": "公開済み。#01 と同じ型で白猫だけ違う。作り直さない。",
    },
}

LABELS = {
    "pet": {
        "C": "C1 ソファ側の固定 / C2 床目線ローアングル / C3 見守りカメラ俯瞰 / C4 窓辺の逆光 / C5 寄りのクローズアップ / C6 引きの部屋全体",
        "P": "P1 グレー×暖色の部屋 / P2 白×木目 / P3 夕方オレンジ / P4 朝の青白 / P5 夜の間接照明 / P6 モノトーン",
        "T": "T1 下中央 / T2 上左 / T3 なし（声のみ） / T4 右縦 / T5 最後だけ中央 / T6 手書きメモ風",
        "F": "F1 丸ゴシック / F2 明朝 / F3 手書き風 / F4 細ゴシック / F5 太ゴシック白縁 / F6 タイプライター風",
        "H": "H1 さっきまでの場所 / H2 無音で動きから / H3 質問 / H4 暗転から / H5 音から / H6 結末を先に",
        "M": "M1 ワンカット長回し / M2 2カット / M3 3–4カット / M4 前半速く後半は静止 / M5 早送りのあと静止 / M6 冒頭を静止",
        "B": "B1 なし / B2 オルゴール / B3 環境音 / B4 ピアノ / B5 ローファイ / B6 ギター",
        "L": "L1 8–12秒 / L2 13–18秒 / L3 19–25秒 / L4 26–35秒 / L5 36–50秒",
        "A": "A1 灰猫1匹 / A2 白猫1匹 / A3 2匹 / A4 猫+小物主役 / A5 猫+人の手 / A6 部屋の物→猫登場",
    },
    "konkatsu": {
        "C": "C1 手元の寄り / C2 画面を大きめ / C3 机の対面側 / C4 下を空けた配置 / C5 左右に分ける / C6 余白の多い枠",
        "P": "P1 ピンク×白 / P2 ベージュ×茶 / P3 ネイビー×白 / P4 ミント×グレー / P5 夜の紫 / P6 くすみ赤",
        "T": "T1 上帯 / T2 下帯 / T3 吹き出し位置 / T4 右縦 / T5 中央大 / T6 左寄せ",
        "F": "F1 丸ゴ / F2 明朝 / F3 手書き / F4 太ゴ / F5 細ゴ / F6 ポップ",
        "H": "H1 セリフ / H2 質問 / H3 短い間 / H4 暗転から / H5 物音から / H6 結末を先に",
        "M": "M1 長回し / M2 2カット / M3 3カット / M4 前半速く後半は静止 / M5 早送りのあと静止 / M6 冒頭を静止",
        "B": "B1 なし / B2 ピアノ / B3 ローファイ / B4 ジャズ / B5 アコギ / B6 環境音",
        "L": "L1 15–20秒 / L2 21–30秒 / L3 31–40秒 / L4 41–50秒 / L5 51–60秒",
        "A": "A1 人物1 / A2 人物2 / A3 画面UI中心 / A4 手元と小物 / A5 文字のみ / A6 背景写真+人物",
    },
    "beauty": {
        "C": "C1 棚の正面 / C2 手元アップ / C3 上からの余白 / C4 俯瞰の余白 / C5 中央を大きく / C6 洗面台の引き",
        "P": "P1 夜の紺×暖色灯 / P2 白×ベージュ / P3 くすみピンク / P4 グリーン×木 / P5 モノクロ+暖色 / P6 朝の自然光",
        "T": "T1 上 / T2 下 / T3 品の横 / T4 右縦 / T5 中央1語 / T6 なし",
        "F": "F1 明朝 / F2 細ゴ / F3 手書き / F4 丸ゴ / F5 太ゴ / F6 等幅",
        "H": "H1 短い間 / H2 手順の頭 / H3 結末を先に / H4 音から / H5 暗転から / H6 無言の棚",
        "M": "M1 長回し / M2 2カット / M3 3カット / M4 前半速く後半は静止 / M5 早送りのあと静止 / M6 冒頭を静止",
        "B": "B1 なし / B2 ローファイ / B3 ピアノ / B4 環境音 / B5 アンビエント / B6 アコギ",
        "L": "L1 15–20秒 / L2 21–30秒 / L3 31–40秒 / L4 41–50秒 / L5 51–60秒",
        "A": "A1 商品のみ / A2 手+商品 / A3 棚全体 / A4 図解 / A5 文字カード / A6 背景+図",
    },
}

# Ranges are the matrix bands. Output length is the script plus at most MAX_HOLD
# of hold. A short script is not frozen forward into a longer band.
MAX_HOLD = 1.5
LENGTH_RANGE = {
    "pet": {
        "L1": (8.0, 12.0),
        "L2": (13.0, 18.0),
        "L3": (19.0, 25.0),
        "L4": (26.0, 35.0),
        "L5": (36.0, 50.0),
    },
    "konkatsu": {
        "L1": (15.0, 20.0),
        "L2": (21.0, 30.0),
        "L3": (31.0, 40.0),
        "L4": (41.0, 50.0),
        "L5": (51.0, 60.0),
    },
    "beauty": {
        "L1": (15.0, 20.0),
        "L2": (21.0, 30.0),
        "L3": (31.0, 40.0),
        "L4": (41.0, 50.0),
        "L5": (51.0, 60.0),
    },
}
BGM_TRACK = {
    "B1": "none",
    "B2": "musicbox",
    "B3": "room",
    "B4": "piano",
    "B5": "lofi",
    "B6": "guitar",
}
# Konkatsu and beauty use the same six beds, named per that line's B row.
BGM_TRACK_LINE = {
    "konkatsu": {"B1": "none", "B2": "piano", "B3": "lofi", "B4": "jazz", "B5": "guitar", "B6": "room"},
    "beauty": {"B1": "none", "B2": "lofi", "B3": "piano", "B4": "room", "B5": "ambient", "B6": "guitar"},
}
GRADE = {
    "P1": "eq=saturation=1.08:gamma=1.06:contrast=1.02,colorbalance=rs=0.05:gs=0.01:bs=-0.05",
    "P2": "eq=saturation=0.85:gamma=1.08:contrast=1.0,colorbalance=rs=0.04:gs=0.02:bs=-0.02",
    "P3": "eq=saturation=1.2:gamma=1.04,colorbalance=rs=0.12:gs=0.02:bs=-0.08",
    "P4": "eq=saturation=0.9:gamma=1.1,colorbalance=rs=-0.06:gs=0.0:bs=0.1",
    "P5": "eq=saturation=0.8:gamma=0.85:contrast=1.05,colorbalance=rs=0.08:gs=0.02:bs=-0.02",
    "P6": "eq=saturation=0.2:contrast=1.12:gamma=1.0",
}
WQY = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
FONTS = {
    "F1": ("/usr/share/fonts/truetype/migmix/migu-1c-regular.ttf", WQY),
    "F2": ("/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf", WQY),
    "F3": ("/usr/share/fonts/truetype/klee/KleeOne-Regular.ttf", WQY),
    "F4": ("/usr/share/fonts/opentype/mplus/Mplus1-Thin.otf", WQY),
    "F5": ("/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf", WQY),
    "F6": ("/usr/share/fonts/truetype/dotgothic16/DotGothic16-Regular.ttf", WQY),
}
LINE_ORDER = {"pet": 0, "konkatsu": 1, "beauty": 2}


def parse_signature(signature: str) -> dict[str, str]:
    body = signature.split(":", 1)[1]
    parts = body.split("-")
    if len(parts) != 9:
        raise SystemExit(f"署名の軸が9個ではない: {signature}")
    codes = {}
    for part, axis in zip(parts, AXES):
        if not part.startswith(axis):
            raise SystemExit(f"署名の順が違う: {signature}")
        codes[axis] = part
    return codes


def format_signature(line: str, codes: dict[str, str]) -> str:
    return line + ":" + "-".join(codes[axis] for axis in AXES)


def thumb_signature(codes: dict[str, str]) -> str:
    return "thumb:" + "-".join(codes[axis] for axis in ("C", "P", "T", "F"))


def shared_axes(left: str, right: str) -> int:
    a = parse_signature(left)
    b = parse_signature(right)
    return sum(a[axis] == b[axis] for axis in AXES)


def thumb_cpt_differ(left: str, right: str) -> int:
    a = parse_signature(left)
    b = parse_signature(right)
    return sum(a[axis] != b[axis] for axis in ("C", "P", "T"))


def qa_against(signature: str, history: list[str]) -> tuple[bool, str]:
    if signature in history:
        return False, "過去の署名と完全一致"
    if not history:
        return True, ""
    prev = history[-1]
    if shared_axes(signature, prev) > 2:
        return False, f"直前と {shared_axes(signature, prev)} 軸が同じ"
    if thumb_cpt_differ(signature, prev) < 2:
        return False, "サムネの構図・配色・文字位置が直前と2つ未満しか違わない"
    for old in history[-5:]:
        if signature == old:
            return False, "直近5本と完全一致"
        if shared_axes(signature, old) > 3:
            return False, f"直近5本と {shared_axes(signature, old)} 軸が同じ"
    return True, ""


def asset_code(pack: dict) -> str:
    slug = pack["slug"]
    if pack["line"] == "pet":
        if "white" in slug:
            return "A2"
        if "chair" in slug:
            return "A6"
        return "A1"
    if pack["line"] == "konkatsu":
        # Hands and objects only. No face, no second person, no readable UI.
        return "A4"
    if pack["line"] == "beauty":
        return "A2"
    raise SystemExit(f"ラインが違う: {pack['line']}")


def pace(codes: dict[str, str], script_sec: float) -> tuple[float, float]:
    """Speed and opening hold. Restoring a sped picture to the script stays within the hold budget."""
    speed = 1.0
    start_hold = 0.5 if codes["M"] == "M6" else 0.0
    if codes["M"] == "M4":
        speed = 0.7
    elif codes["M"] == "M5":
        speed = 0.75
    if start_hold > MAX_HOLD:
        start_hold = MAX_HOLD
    budget = MAX_HOLD - start_hold
    if script_sec > 0 and speed < 1.0:
        speed = max(speed, 1.0 - budget / float(script_sec))
    return speed, start_hold


def natural_length(script_sec: float, codes: dict[str, str]) -> float:
    _speed, start_hold = pace(codes, script_sec)
    return float(script_sec) + start_hold


def length_target(line: str, script_sec: float, codes: dict[str, str]) -> float | None:
    """Natural duration when this L code matches it. Never freezes forward into a longer band."""
    target = natural_length(script_sec, codes)
    script = float(script_sec)
    if target - script > MAX_HOLD + 1e-6:
        return None
    lo, hi = LENGTH_RANGE[line][codes["L"]]
    if lo - 1e-6 <= script <= hi + 1e-6 and target <= script + MAX_HOLD + 1e-6:
        return target
    if lo - 1e-6 <= target <= hi + 1e-6:
        return target
    # Shorter than every band. L1 is the label, and the picture stays on the script.
    if codes["L"] == "L1" and target < lo:
        return target
    return None


def delivered_length(line: str, script_sec: float, codes: dict[str, str]) -> float:
    target = length_target(line, script_sec, codes)
    if target is None:
        raise SystemExit(f"{codes['L']} は台本 {script_sec:g} 秒に合わない")
    return target


def label_of(line: str, code: str) -> str:
    axis = code[0]
    row = LABELS[line][axis]
    for piece in row.split(" / "):
        if piece.startswith(code + " "):
            return piece
    return code


def reachable_lengths(line: str, script_sec: float, codes: dict[str, str]) -> list[tuple[str, float]]:
    found = []
    for code in ("L1", "L2", "L3", "L4", "L5"):
        trial = dict(codes)
        trial["L"] = code
        target = length_target(line, script_sec, trial)
        if target is not None:
            found.append((code, target))
    found.sort(key=lambda item: (item[1] - float(script_sec), item[0]))
    return found


def length_notes(line: str, script_sec: float, target: float) -> str:
    base = "未公開。直前は共有軸2まで、直近5本は3まで。完全一致は不可。"
    lo = LENGTH_RANGE[line]["L1"][0]
    if target + 1e-6 < lo:
        return base + " 台本が最短の帯より短いので、長さは台本のまま。止め足しは1.5秒まで。"
    hold = target - float(script_sec)
    if hold > 0.05:
        return base + " 止め足しは1.5秒まで。"
    return base + " 止め足しはしない。"


def pick_signature(index: int, line: str, script_sec: float, fixed_a: str, history: list[str]) -> tuple[str, float]:
    rng = random.Random(2003 + index * 19)
    for _attempt in range(30000):
        codes = {axis: f"{axis}{rng.randint(1, 6)}" for axis in "CPTFHMB"}
        codes["A"] = fixed_a
        reachable = reachable_lengths(line, script_sec, codes)
        if reachable:
            length_code, target = rng.choice(reachable)
            codes["L"] = length_code
        else:
            codes["L"] = "L1"
            target = natural_length(script_sec, codes)
        signature = format_signature(line, codes)
        ok, _reason = qa_against(signature, history)
        if ok:
            return signature, target
    raise SystemExit(f"署名が見つからない: {line} index={index}")


def _accept(line: str, script_sec: float, codes: dict[str, str], history: list[str]) -> tuple[str, float] | None:
    try:
        target = delivered_length(line, script_sec, codes)
    except SystemExit:
        return None
    signature = format_signature(line, codes)
    if qa_against(signature, history)[0]:
        return signature, target
    return None


def repair_signature(line: str, script_sec: float, signature: str, history: list[str]) -> tuple[str, float] | None:
    """Change L first. Then the fewest other axes, leaving the thumbnail alone when that passes."""
    codes = parse_signature(signature)
    lengths = [code for code, _target in reachable_lengths(line, script_sec, codes)]
    if not lengths:
        return None
    for length_code in lengths:
        trial = dict(codes)
        trial["L"] = length_code
        hit = _accept(line, script_sec, trial, history)
        if hit is not None:
            return hit
    edit_order = ("H", "M", "B", "T", "F", "P", "C")
    base = lengths[0]
    for axis in edit_order:
        for number in range(1, 7):
            trial = dict(codes)
            trial["L"] = base
            trial[axis] = f"{axis}{number}"
            hit = _accept(line, script_sec, trial, history)
            if hit is not None:
                return hit
    for index, first in enumerate(edit_order):
        for second in edit_order[index + 1 :]:
            for number_a in range(1, 7):
                for number_b in range(1, 7):
                    trial = dict(codes)
                    trial["L"] = base
                    trial[first] = f"{first}{number_a}"
                    trial[second] = f"{second}{number_b}"
                    hit = _accept(line, script_sec, trial, history)
                    if hit is not None:
                        return hit
    return None


def title_of(pack_dir: Path) -> str:
    script = (pack_dir / "SCRIPT.md").read_text().splitlines()
    for line in script:
        if line.startswith("# "):
            return line[2:].strip()
    return pack_dir.name


def ensure_credit(path: Path) -> None:
    text = path.read_text()
    text = text.replace(CREDIT + "\n## YouTube\n", "## YouTube\n")
    needle = "映像はAIで生成しています。\n"
    if needle in text and needle + CREDIT not in text:
        text = text.replace(needle, needle + CREDIT + "\n", 1)
    lines = text.splitlines(keepends=True)
    seen_caption = False
    caption_has = False
    for line in lines:
        if line.startswith("キャプション"):
            seen_caption = True
        elif seen_caption and line.startswith("## "):
            break
        elif seen_caption and line.startswith(CREDIT):
            caption_has = True
            break
    if not caption_has:
        rebuilt: list[str] = []
        seen_caption = False
        for line in lines:
            if line.startswith("キャプション"):
                seen_caption = True
            if seen_caption and line.startswith("#") and not line.startswith("##"):
                rebuilt.append(CREDIT + "\n")
                seen_caption = False
            rebuilt.append(line)
        lines = rebuilt
    text = "".join(lines)
    if text.count(CREDIT) < 2:
        raise SystemExit(f"クレジットが説明とキャプションに無い: {path}")
    path.write_text(text)


def credit_ok(pack_dir: Path) -> bool:
    post = pack_dir / "POST.md"
    return post.is_file() and CREDIT in post.read_text()


def style_markdown(pack: dict, signature: str, target: float, status: str, notes: str) -> str:
    codes = parse_signature(signature)
    rows = ["# スタイル", ""]
    rows.append(f"署名: `{signature}`")
    rows.append(f"サムネ: `{thumb_signature(codes)}`")
    rows.append(f"状態: {status}")
    rows.append(f"絵の目標: {target:g}秒。止め足しは1.5秒まで。帯まで届かないときは台本の長さのまま。声の長さには合わせない。")
    rows.append(f"クレジット: {CREDIT}")
    rows.append("")
    rows.append("| 軸 | 値 |")
    rows.append("| --- | --- |")
    for axis in AXES:
        rows.append(f"| {axis} | {label_of(pack['line'], codes[axis])} |")
    rows.append("")
    rows.append(notes)
    rows.append("")
    rows.append("画面の文字はサムネだけ。本編には焼かない。顔、読めるUI、ビフォーアフターは足さない。")
    rows.append("")
    return "\n".join(rows)


def channel_packs() -> dict[str, list[dict]]:
    grouped = {"pet": [], "konkatsu": [], "beauty": []}
    for pack in iter_packs():
        if pack["line"] in grouped:
            grouped[pack["line"]].append(pack)
    for line in grouped:
        grouped[line].sort(key=lambda pack: (pack["date"], pack["slug"]))
    return grouped


def resolve_signature(index: int, pack: dict, history: list[str]) -> tuple[str, float, str, str]:
    """Keep a signature that already fits. Re-pick only when its length band does not."""
    script_sec = float(pack["picture_sec"])
    published = PUBLISHED.get(pack["rel"])
    if published:
        signature = published["signature"]
        return signature, delivered_length(pack["line"], script_sec, parse_signature(signature)), "published", published["notes"]
    fixed_a = asset_code(pack)
    style_path = pack["dir"] / "STYLE.md"
    old = load_style_signature(pack["dir"]) if style_path.is_file() else ""
    if old and parse_signature(old)["A"] == fixed_a:
        repaired = repair_signature(pack["line"], script_sec, old, history)
        if repaired is not None:
            signature, target = repaired
            return signature, target, "ready", length_notes(pack["line"], script_sec, target)
    signature, target = pick_signature(index, pack["line"], script_sec, fixed_a, history)
    return signature, target, "ready", length_notes(pack["line"], script_sec, target)


def assign_all(log_path: Path = LOG_PATH) -> list[dict]:
    grouped = channel_packs()
    rows: list[dict] = []
    for line, packs in grouped.items():
        history: list[str] = []
        for index, pack in enumerate(packs):
            script_sec = float(pack["picture_sec"])
            signature, target, status, notes = resolve_signature(index, pack, history)
            video_id = PUBLISHED[pack["rel"]]["video_id"] if pack["rel"] in PUBLISHED else f"{index + 1:02d}"
            history.append(signature)
            codes = parse_signature(signature)
            prev_share: str | int = "-"
            last_share: str | int = "-"
            if index:
                prev_share = shared_axes(signature, history[-2])
                last_share = max(shared_axes(signature, old) for old in history[-6:-1])
            if not credit_ok(pack["dir"]):
                raise SystemExit(f"クレジットが無い: {pack['rel']}")
            old_signature = ""
            style_path = pack["dir"] / "STYLE.md"
            if style_path.is_file():
                old_signature = load_style_signature(pack["dir"])
            style_path.write_text(style_markdown(pack, signature, target, status, notes))
            if status != "published" and thumb_signature(parse_signature(old_signature or signature)) != thumb_signature(codes):
                _write_thumb(pack["dir"], line, codes, title_of(pack["dir"]))
            bgm_names = BGM_TRACK_LINE.get(line, BGM_TRACK)
            rows.append(
                {
                    "date": pack["date"],
                    "line": line,
                    "video_id": video_id,
                    "status": status,
                    "signature": signature,
                    "thumb_signature": thumb_signature(codes),
                    "shared_axes_with_prev": prev_share,
                    "shared_axes_max_last5": last_share,
                    "bgm_track": bgm_names[codes["B"]],
                    "length_sec": f"{target:.3f}".rstrip("0").rstrip("."),
                    "irasutoya_count": 0,
                    "credit_ok": "yes",
                    "notes": notes,
                    "rel": pack["rel"],
                    "target_sec": target,
                }
            )
    write_log(rows, log_path)
    return rows


def write_log(rows: list[dict], log_path: Path) -> None:
    ordered = sorted(rows, key=lambda row: (LINE_ORDER[row["line"]], row["video_id"]))
    with log_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LOG_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in ordered:
            writer.writerow({key: row[key] for key in LOG_FIELDS})


def read_log(log_path: Path) -> list[dict]:
    with log_path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def check_log(log_path: Path = LOG_PATH) -> None:
    rows = read_log(log_path)
    packs_by_id: dict[str, dict[str, dict]] = {}
    for line, packs in channel_packs().items():
        packs_by_id[line] = {f"{index + 1:02d}": pack for index, pack in enumerate(packs)}
    by_line: dict[str, list[dict]] = {}
    for row in rows:
        by_line.setdefault(row["line"], []).append(row)
    for line, group in by_line.items():
        group.sort(key=lambda row: row["video_id"])
        history: list[str] = []
        for row in group:
            signature = row["signature"]
            if row["status"] != "published":
                ok, reason = qa_against(signature, history)
                if not ok:
                    raise SystemExit(f"{line} {row['video_id']}: {reason}")
                if row["shared_axes_with_prev"] != "-" and int(row["shared_axes_with_prev"]) > 2:
                    raise SystemExit(f"{line} {row['video_id']}: ログの直前共有が3以上")
                if row["shared_axes_max_last5"] != "-" and int(row["shared_axes_max_last5"]) > 3:
                    raise SystemExit(f"{line} {row['video_id']}: ログの直近5本共有が4以上")
                pack = packs_by_id[line][row["video_id"]]
                script_sec = float(pack["picture_sec"])
                expected = delivered_length(line, script_sec, parse_signature(signature))
                logged = float(row["length_sec"])
                if abs(logged - expected) > 0.05:
                    raise SystemExit(f"{line} {row['video_id']}: 長さ {logged} が台本 {script_sec} の目標 {expected} と違う")
                if logged - script_sec > MAX_HOLD + 0.05 or script_sec - logged > 0.05:
                    raise SystemExit(f"{line} {row['video_id']}: 止め足しが1.5秒を超える")
            if row["credit_ok"] != "yes":
                raise SystemExit(f"{line} {row['video_id']}: クレジット")
            if int(row["irasutoya_count"]) > 20:
                raise SystemExit(f"{line} {row['video_id']}: いらすとやが20枚を超える")
            history.append(signature)
        if len(history) != len(set(history)):
            raise SystemExit(f"{line}: 署名が重複")
    published = [row for row in rows if row["status"] == "published"]
    if [row["video_id"] for row in published] != ["01", "02"]:
        raise SystemExit("公開済みはペット #01 と #02 だけ")
    print(f"style-log ok rows={len(rows)}")


def load_style_signature(pack_dir: Path) -> str:
    for line in (pack_dir / "STYLE.md").read_text().splitlines():
        if line.startswith("署名: `") and line.endswith("`"):
            return line.removeprefix("署名: `").removesuffix("`")
    raise SystemExit(f"署名が無い: {pack_dir}")


def font_file(code: str) -> str:
    for path in FONTS[code[:2] if code.startswith("F") else code]:
        if Path(path).is_file():
            return path
    raise SystemExit(f"フォントが無い: {code}")


def geometry(code: str) -> str:
    if code == "C3":
        return "scale=1000:1780:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:48:color=0x141820"
    if code == "C6":
        return "scale=900:1600:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x2a241c"
    zoom = {"C1": (1.12, "0.50", "0.28"), "C2": (1.18, "0.50", "0.78"), "C4": (1.24, "0.18", "0.45"), "C5": (1.48, "0.50", "0.50")}
    z, x, y = zoom[code]
    width = int(round(1080 * z))
    height = int(round(1920 * z))
    return f"scale={width}:{height},crop=1080:1920:(in_w-1080)*{x}:(in_h-1920)*{y}"


def grade_for(line: str, code: str) -> str:
    # One grade table. Line palettes differ by which P code was chosen, not by a second secret grade.
    return GRADE[code]


def video_filter(codes: dict[str, str], script_sec: float, target: float) -> str:
    speed, start_hold = pace(codes, script_sec)
    played = float(script_sec) * speed
    end_hold = float(target) - played - start_hold
    if end_hold < -0.05 or start_hold + end_hold > MAX_HOLD + 0.05:
        raise SystemExit(f"止め足しが1.5秒を超える: start={start_hold:.3f} end={end_hold:.3f} target={target}")
    end_hold = max(0.0, end_hold)
    parts = [
        geometry(codes["C"]),
        grade_for("", codes["P"]),
        f"setpts=PTS*{speed}",
        f"tpad=start_mode=clone:start_duration={start_hold:.3f}:stop_mode=clone:stop_duration={end_hold:.3f}",
        f"trim=duration={target:.3f}",
        "setpts=PTS-STARTPTS",
        "fps=30",
        "format=yuv420p",
    ]
    if codes["H"] == "H4":
        parts.append("fade=t=in:st=0:d=0.45")
    return ",".join(parts)


def bgm_lavfi(codes: dict[str, str], target: float) -> str | None:
    kind = codes["B"]
    if kind == "B1":
        return None
    beds = {
        "B2": "sine=frequency=784:sample_rate=48000,tremolo=f=6:d=0.7,volume=0.3",
        "B3": "anoisesrc=color=pink:sample_rate=48000:amplitude=0.2,highpass=f=500,lowpass=f=2500",
        "B4": "sine=frequency=262:sample_rate=48000,tremolo=f=2:d=0.4,volume=0.25",
        "B5": "anoisesrc=color=brown:sample_rate=48000:amplitude=0.25,lowpass=f=700",
        "B6": "sine=frequency=196:sample_rate=48000,tremolo=f=3:d=0.85,volume=0.28",
    }
    return beds[kind] + f",atrim=0:{target:.3f}"


def plan(pack_dir: Path, script_sec: float) -> dict:
    signature = load_style_signature(pack_dir)
    codes = parse_signature(signature)
    line = signature.split(":", 1)[0]
    target = delivered_length(line, float(script_sec), codes)
    rel = pack_dir.resolve().relative_to(STOCK.resolve()).as_posix()
    # rel is date/line/slug
    history = []
    if LOG_PATH.is_file():
        line = rel.split("/")[1]
        video_id = None
        for row in read_log(LOG_PATH):
            if row["signature"] == signature and row["line"] == line:
                video_id = row["video_id"]
        for row in read_log(LOG_PATH):
            if row["line"] != line:
                continue
            if video_id is not None and row["video_id"] >= video_id:
                continue
            history.append(row["signature"])
        if rel not in PUBLISHED:
            ok, reason = qa_against(signature, history)
            if not ok:
                raise SystemExit(f"スタイルQA: {rel}: {reason}")
    if not credit_ok(pack_dir):
        raise SystemExit(f"クレジットが無い: {rel}")
    return {
        "signature": signature,
        "thumb_signature": thumb_signature(codes),
        "target_sec": target,
        "vf": video_filter(codes, float(script_sec), target),
        "bgm_lavfi": bgm_lavfi(codes, target),
        "bgm_code": codes["B"],
        "hook": codes["H"],
        "credit": CREDIT,
    }


def render_thumbs() -> None:
    for pack in [pack for packs in channel_packs().values() for pack in packs]:
        if pack["rel"] in PUBLISHED:
            continue
        signature = load_style_signature(pack["dir"])
        codes = parse_signature(signature)
        _write_thumb(pack["dir"], pack["line"], codes, title_of(pack["dir"]))


THUMB_COLOR = {
    "P1": "0xC4B6A6",
    "P2": "0xE7D3B0",
    "P3": "0xE07040",
    "P4": "0xC5D5DE",
    "P5": "0x2A241C",
    "P6": "0xB0B0B0",
}


def _write_thumb(pack_dir: Path, line: str, codes: dict[str, str], title: str) -> None:
    text = title.replace("\n", " ")[:18]
    text_path = pack_dir / ".thumb-text.txt"
    text_off = (line == "pet" and codes["T"] == "T3") or (line == "beauty" and codes["T"] == "T6")
    if text_off:
        text_path.write_text("")
    elif codes["T"] == "T4":
        text_path.write_text("\n".join(text))
    else:
        text_path.write_text(text)
    font = font_file(codes["F"])
    border = ":borderw=8:bordercolor=white" if codes["F"] == "F5" else ":borderw=0"
    positions = {
        "T1": "x=(w-text_w)/2:y=h-text_h-180",
        "T2": "x=72:y=140",
        "T4": "x=w-text_w-90:y=(h-text_h)/2",
        "T5": "x=(w-text_w)/2:y=(h-text_h)/2",
        "T6": "x=90:y=h-text_h-320",
        "T3": "x=140:y=h*0.62",
    }
    color = THUMB_COLOR[codes["P"]]
    boxes = {
        "C1": "drawbox=x=80:y=80:w=920:h=700:color=white@0.25:t=fill",
        "C2": "drawbox=x=0:y=1100:w=1080:h=820:color=black@0.25:t=fill",
        "C3": "drawbox=x=40:y=40:w=1000:h=1840:color=white@0.2:t=24",
        "C4": "drawbox=x=0:y=0:w=280:h=1920:color=white@0.3:t=fill",
        "C5": "drawbox=x=240:y=560:w=600:h=800:color=white@0.28:t=fill",
        "C6": "drawbox=x=120:y=180:w=840:h=1560:color=black@0.35:t=18",
    }
    dest = pack_dir / "thumb.png"
    text_filter = ""
    if text_path.read_text().strip():
        text_filter = (
            f",drawtext=fontfile={font}:textfile={text_path}:fontsize=72:fontcolor=white"
            f"{border}:{positions[codes['T']]}"
        )
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-nostdin",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s=1080x1920:d=1",
            "-vf",
            boxes[codes["C"]] + text_filter,
            "-frames:v",
            "1",
            str(dest),
        ]
    )
    text_path.unlink(missing_ok=True)


def record(pack_dir: Path, measured_sec: float) -> None:
    rel = pack_dir.resolve().relative_to(STOCK.resolve()).as_posix()
    if rel in PUBLISHED:
        return
    signature = load_style_signature(pack_dir)
    rows = read_log(LOG_PATH)
    found = False
    for row in rows:
        if row["signature"] == signature:
            row["length_sec"] = f"{measured_sec:.3f}".rstrip("0").rstrip(".")
            row["status"] = "finished"
            found = True
            break
    if not found:
        raise SystemExit(f"ログに署名が無い: {signature}")
    write_log(rows, LOG_PATH)


def main(argv: list[str]) -> None:
    if len(argv) == 2 and argv[1] in ("assign", "repick"):
        rows = assign_all()
        print(f"assigned {len(rows)}")
        return
    if len(argv) == 2 and argv[1] == "check":
        check_log()
        return
    if len(argv) == 2 and argv[1] == "thumbs":
        render_thumbs()
        print("thumbs ok")
        return
    if len(argv) == 4 and argv[1] == "plan":
        payload = plan(Path(argv[2]), float(argv[3]))
        json.dump(payload, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        return
    if len(argv) == 4 and argv[1] == "record":
        record(Path(argv[2]), float(argv[3]))
        return
    raise SystemExit("usage: style_matrix.py assign|repick|check|thumbs|plan PACK_DIR SCRIPT_SEC|record PACK_DIR MEASURED_SEC")


if __name__ == "__main__":
    main(sys.argv)
