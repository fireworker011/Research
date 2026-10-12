"""Shot sheet for one source video. Structure stays. Four slots stay empty.

Person, animals, lines, and place are the only fields a later script may
replace. Source lines stay on the sheet as evidence and are kept out of the
prompt. This module does not render video and does not post.
"""

from __future__ import annotations

import argparse
import copy
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

import affi_reference as ref

ROOT = Path(__file__).resolve().parent
PACK_PATH = ROOT / "reference-accounts" / "source" / "repro" / "junjun_825k.yaml"
SHEET_PATH = ROOT / "reference-accounts" / "source" / "repro" / "junjun_825k.md"
INDEX_PATH = ROOT / "stories" / "INDEX.md"
LOCKED_SHEET = "71.552秒"
# Phone menu name. The file stays pet_sheet.yaml.
_PACK_ALIAS = {"給水": "pet_sheet"}

SLOT = "入力"
ROLES = ("guest", "retort", "polite", "owner", "indoor_pair")
ROLE_JA = {
    "guest": "客",
    "retort": "ツッコミ",
    "polite": "丁寧",
    "owner": "飼い主",
    "indoor_pair": "室内の2匹",
}
ANIMAL_SLOTS = ("guest", "retort", "polite")
# Locked picture and camera must not name the source cast.
_LOCKED_BANNED = (
    "カラス",
    "猫",
    "女性",
    "リン",
    "ジュン",
    "ランラン",
    "ポテチ",
    "カルビー",
    "junjun",
)
_NORM = re.compile(r"[\s、。！？!?・,.\-「」『』]")
_PACK_TAIL = re.compile(r"(stories/[^/?#\s]+\.ya?ml)")
_LINES_TAIL = re.compile(r"(stories/[^/?#\s]+\.txt)")


def _num(value: float) -> str:
    text = f"{float(value):.3f}".rstrip("0").rstrip(".")
    return text or "0"


def _norm(text: str) -> str:
    return _NORM.sub("", str(text or ""))


# A slot that says the role is not in this story.
NOT_SHOWN = "出さない"
_CJK = re.compile(r"[ぁ-んァ-ヶー一-龥々〆]")
_AGE_WORDS = {20: "twenties", 30: "thirties", 40: "forties", 50: "fifties", 60: "sixties"}
# (Japanese, English, where). "head" is the noun, "pre" goes before it, "post" after it.
_SLOT_WORDS: tuple[tuple[str, str, str], ...] = (
    ("スコティッシュフォールド", "Scottish Fold cat", "head"),
    ("マンチカン", "Munchkin cat", "head"),
    ("トイプードル", "toy poodle", "head"),
    ("プードル", "poodle", "head"),
    ("ビーグル", "beagle", "head"),
    ("チワワ", "Chihuahua", "head"),
    ("柴犬", "Shiba Inu", "head"),
    ("柴", "Shiba Inu", "head"),
    ("ハムスター", "hamster", "head"),
    ("うさぎ", "rabbit", "head"),
    ("小鳥", "small bird", "head"),
    ("子猫", "kitten", "head"),
    ("子犬", "puppy", "head"),
    ("猫", "cat", "head"),
    ("犬", "dog", "head"),
    ("鳥", "bird", "head"),
    ("動物", "animal", "head"),
    ("獣", "beast", "head"),
    ("女性", "woman", "head"),
    ("男性", "man", "head"),
    ("人", "person", "head"),
    ("リビング", "living room", "head"),
    ("キッチン", "kitchen", "head"),
    ("台所", "kitchen", "head"),
    ("寝室", "bedroom", "head"),
    ("玄関", "entryway", "head"),
    ("カフェ", "cafe", "head"),
    ("部屋", "room", "head"),
    ("公園", "park", "head"),
    ("ベランダ", "balcony", "head"),
    ("庭", "yard", "head"),
    ("グレー一色", "solid grey", "pre"),
    ("グレー", "grey", "pre"),
    ("灰色", "grey", "pre"),
    ("白い", "white", "pre"),
    ("白", "white", "pre"),
    ("黒い", "black", "pre"),
    ("黒", "black", "pre"),
    ("茶色い", "brown", "pre"),
    ("茶色", "brown", "pre"),
    ("クリーム色", "cream", "pre"),
    ("クリーム", "cream", "pre"),
    ("三毛", "calico", "pre"),
    ("茶トラ", "orange tabby", "pre"),
    ("キジトラ", "brown tabby", "pre"),
    ("サバトラ", "silver tabby", "pre"),
    ("短い足", "short-legged", "pre"),
    ("長毛", "long-haired", "pre"),
    ("短毛", "short-haired", "pre"),
    ("小さい", "small", "pre"),
    ("小さな", "small", "pre"),
    ("大きい", "large", "pre"),
    ("大きな", "large", "pre"),
    ("小柄", "small", "pre"),
    ("太い", "stout", "pre"),
    ("細い", "slender", "pre"),
    ("短い", "short", "pre"),
    ("成人", "adult", "pre"),
    ("大人", "adult", "pre"),
    ("別", "different", "pre"),
    *(
        (f"{age}代{part}", f"in their {span}{_AGE_WORDS[age]}", "post")
        for age in _AGE_WORDS
        for part, span in (("前半", "early "), ("後半", "late "), ("", ""))
    ),
    ("真夏", "in midsummer", "post"),
    ("夏", "in summer", "post"),
    ("昼", "in daylight", "post"),
    ("朝", "in the morning", "post"),
    ("夕方", "in the early evening", "post"),
    ("夜", "at night", "post"),
)
# Sentences that describe a filled slot but are not one noun.
_SLOT_SENTENCES = {
    "ゆるい部屋着": "wearing loose loungewear",
    "髪はひとつ結び": "with hair tied back",
    "空の水入れと小さなビニールプール": "with an empty water bowl and a small vinyl pool",
    "ソファの薄い毛布": "with a thin blanket on the sofa",
    "床におやつ皿": "with a treat dish on the floor",
}
_SLOT_GLUE = "の、 　"


def _article(phrase: str) -> str:
    return ("an " if phrase[:1].lower() in "aeiou" else "a ") + phrase


def _noun_phrase(sentence: str) -> tuple[str, str]:
    """One Japanese noun with its modifiers. Returns (with article, with "the")."""
    words = sorted(_SLOT_WORDS, key=lambda item: len(item[0]), reverse=True)
    pre: list[str] = []
    post: list[str] = []
    heads: list[str] = []
    unknown: list[str] = []
    at = 0
    while at < len(sentence):
        if sentence[at] in _SLOT_GLUE:
            at += 1
            continue
        hit = next((item for item in words if sentence.startswith(item[0], at)), None)
        if hit is None:
            start = at
            while at < len(sentence) and sentence[at] not in _SLOT_GLUE and not any(
                sentence.startswith(item[0], at) for item in words
            ):
                at += 1
            unknown.append(sentence[start:at])
            continue
        japanese, english, where = hit
        {"pre": pre, "post": post, "head": heads}[where].append(english)
        at += len(japanese)
    if unknown:
        raise ValueError("「" + "」「".join(unknown) + "」")
    if len(heads) != 1:
        raise ValueError(f"「{sentence}」")
    core = " ".join([*pre, heads[0]])
    full = " ".join([core, *post])
    return _article(full), f"the {core}"


def slot_english(text: str) -> tuple[str, str]:
    """English for one filled slot: (description, name inside the shots).

    Text without Japanese is kept as typed. Japanese is read from the word and
    sentence tables above. A word that is not listed raises, so the bake stops
    instead of handing Japanese to H3.
    """
    raw = str(text or "").strip()
    if not _CJK.search(raw):
        full = raw.rstrip(" .")
        bare = re.sub(r"^(?:a|an|the)\s+", "", full, flags=re.IGNORECASE)
        short = bool(bare) and len(bare.split()) <= 6 and not re.search(r"[,;:]", bare)
        return full, f"the {bare}" if short else ""
    sentences = [part.strip() for part in re.split(r"[。．.]", raw) if part.strip()]
    parts: list[str] = []
    name = ""
    for index, sentence in enumerate(sentences):
        fixed = _SLOT_SENTENCES.get(sentence)
        if fixed is not None:
            parts.append(fixed)
            continue
        described, called = _noun_phrase(sentence)
        if index == 0:
            parts.append(described)
            name = called
        else:
            parts.append(f"with {described}")
    return ", ".join(parts), name


def _existing(text: str) -> Path | None:
    """A file at the written path, under this folder, or by its name in stories/."""
    chosen = Path(text)
    if chosen.is_file():
        return chosen
    alt = ROOT / text
    if alt.is_file():
        return alt
    name = Path(text.split("?")[0].split("#")[0]).name
    if name:
        story = ROOT / "stories" / name
        if story.is_file():
            return story
    return None


def story_index() -> list[dict[str, str]]:
    """Rows of stories/INDEX.md. The Colab 構成 menu is these names."""
    if not INDEX_PATH.is_file():
        return []
    rows: list[dict[str, str]] = []
    for line in INDEX_PATH.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        name = cells[0]
        if not name or name == "名前" or set(name) <= set("-: "):
            continue
        rows.append(
            {
                "name": name,
                "summary": cells[1],
                "duration": cells[2],
                "cast": cells[3],
                "pattern": cells[4],
                "baked": cells[5],
            }
        )
    return rows


def pack_file(raw: str | Path | None = None) -> Path | None:
    """Empty or the locked label stays the 71.552s sheet. A name in the index is that story.

    A written path, or a GitHub URL that contains ``stories/<name>.yaml``, is that file.
    """
    text = "" if raw is None else str(raw).strip()
    text = _PACK_ALIAS.get(text, text)
    if text in {"", LOCKED_SHEET}:
        return None
    for candidate in [*_PACK_TAIL.findall(text), text]:
        found = _existing(candidate)
        if found is not None and found.suffix in {".yaml", ".yml"}:
            return found
    names = {row["name"] for row in story_index()}
    if text in names:
        found = ROOT / "stories" / f"{text}.yaml"
        if found.is_file():
            return found
    raise ValueError(f"構成ファイルが無い: {text}")


def stock_lines(pack_raw: str | Path | None, lines_text: str) -> str:
    """Typed lines win. An empty field loads ``<story>_lines.txt`` only when a stock pack is chosen."""
    typed = read_lines(lines_text)
    if typed.strip():
        return typed
    path = pack_file(pack_raw)
    if path is None:
        return ""
    side = path.with_name(path.stem + "_lines.txt")
    if side.is_file():
        return side.read_text(encoding="utf-8")
    return ""


def read_lines(raw: str) -> str:
    """Caption text. A single path to a .txt file is read. Several lines stay as typed."""
    text = "" if raw is None else str(raw)
    stripped = text.strip()
    if not stripped:
        return ""
    if "\n" in text or "\r" in text:
        return text
    tails = _LINES_TAIL.findall(stripped)
    if not tails and not stripped.endswith(".txt"):
        return text
    for candidate in [*tails, stripped]:
        found = _existing(candidate)
        if found is not None and found.suffix == ".txt":
            return found.read_text(encoding="utf-8")
    raise ValueError(
        f"セリフファイルが無い: {stripped}。stories/pet_sheet_lines.txt の中身を貼るか、そのパスを書く。"
    )


def load(path: Path | None = None) -> dict[str, Any]:
    """Read the pack and check that the shots, cuts, and slots still match."""
    data = yaml.safe_load((path or PACK_PATH).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("構成がオブジェクトではない")
    if data.get("schema") != "affi-repro-structure/v1":
        raise ValueError("構成の schema が違う")
    shots = list(data.get("shots") or [])
    captions = list(data.get("captions") or [])
    if not shots or not captions:
        raise ValueError("ショットか字幕が無い")
    duration = round(float(data["duration_s"]), 3)
    if round(float(shots[0]["start_s"]), 3) != 0:
        raise ValueError("最初のショットが 0 秒ではない")
    if round(float(shots[-1]["end_s"]), 3) != duration:
        raise ValueError("最後のショットが尺と違う")
    cuts = [round(float(item), 3) for item in data["cuts_s"]]
    edges = [round(float(shot["end_s"]), 3) for shot in shots[:-1]]
    if edges != cuts:
        raise ValueError("カットとショットの境目が違う")
    previous = 0.0
    seen_ids: set[str] = set()
    for shot in shots:
        start = round(float(shot["start_s"]), 3)
        end = round(float(shot["end_s"]), 3)
        if start != previous or end <= start:
            raise ValueError(f"ショットが連続していない: {shot['id']}")
        previous = end
        if shot["id"] in seen_ids:
            raise ValueError(f"ショット id が重複: {shot['id']}")
        seen_ids.add(shot["id"])
        for field in ("picture", "camera"):
            for word in _LOCKED_BANNED:
                if word.casefold() in str(shot.get(field) or "").casefold():
                    raise ValueError(f"固定の絵に元の名がある: {shot['id']} {word}")
    by_shot = {shot["id"]: shot for shot in shots}
    seen_caps: set[str] = set()
    for row in captions:
        if row["id"] in seen_caps:
            raise ValueError(f"字幕 id が重複: {row['id']}")
        seen_caps.add(row["id"])
        if row["role"] not in ROLES:
            raise ValueError(f"役が無い: {row['id']}")
        shot = by_shot.get(row["shot"])
        if shot is None:
            raise ValueError(f"字幕のショットが無い: {row['id']}")
        if str(row.get("line") or "") != SLOT:
            raise ValueError(f"セリフ欄が空ではない: {row['id']}")
        source = str(row.get("source_line") or "").strip()
        if not source:
            raise ValueError(f"証拠の文が無い: {row['id']}")
        start = float(shot["start_s"])
        end = float(shot["end_s"])
        for sample in row.get("seen_s") or []:
            if float(sample) < start - 0.05 or float(sample) > end + 0.05:
                raise ValueError(f"見えた秒がショットの外: {row['id']} {sample}")
    slots = data.get("slots") or {}
    if slots.get("person") != SLOT or slots.get("place") != SLOT:
        raise ValueError("人か場所が入力ではない")
    animals = slots.get("animals") or {}
    if any(animals.get(key) != SLOT for key in ANIMAL_SLOTS):
        raise ValueError("動物が入力ではない")
    check_voices(data)
    return data


def check_voices(data: Mapping[str, Any]) -> None:
    """Optional ``voices`` map. Absent keeps the shared defaults. Present voices are one each."""
    voices = data.get("voices")
    if voices is None:
        return
    if not isinstance(voices, dict):
        raise ValueError("声の対応がオブジェクトではない")
    unknown = [str(role) for role in voices if role not in ROLES]
    if unknown:
        raise ValueError("声の役が無い: " + ", ".join(unknown))
    spoken = {row["role"] for row in data.get("captions") or []}
    missing = sorted(spoken - set(voices))
    if missing:
        raise ValueError("話している役の声が無い: " + ", ".join(missing))
    heard: dict[str, str] = {}
    for role, voice in voices.items():
        text = str(voice or "").strip()
        if not text:
            raise ValueError(f"声が空: {role}")
        other = heard.get(text)
        if other is not None:
            raise ValueError(f"同じ声が2役に当たっている: {other} と {role}")
        heard[text] = str(role)


def captions_of(pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Caption rows. ``line`` is the slot. ``source_line`` is evidence."""
    rows = []
    for row in pack["captions"]:
        rows.append(
            {
                "id": row["id"],
                "shot": row["shot"],
                "role": row["role"],
                "role_ja": ROLE_JA[row["role"]],
                "seen_s": [float(item) for item in row["seen_s"]],
                "source_line": row["source_line"],
                "line": row["line"],
                "function": row.get("function") or "",
            }
        )
    return rows


def narration_of(pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Speech turns. There is no narrator apart from these lines."""
    rows = []
    for row in captions_of(pack):
        rows.append(
            {
                "id": row["id"],
                "shot": row["shot"],
                "role": row["role"],
                "role_ja": row["role_ja"],
                "register": pack["registers"][row["role"]],
                "seen_s": row["seen_s"],
                "line": row["line"],
                "function": row["function"],
            }
        )
    return rows


def fill(
    pack: Mapping[str, Any],
    *,
    person: str = "",
    animals: Mapping[str, str] | None = None,
    place: str = "",
    lines: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Replace only the four slots. Shot times, roles, and cameras stay."""
    filled = copy.deepcopy(dict(pack))
    slots = filled["slots"]
    if str(person or "").strip():
        ref.reject_likeness(person)
        slots["person"] = str(person).strip()
    given_animals = dict(animals or {})
    unknown = set(given_animals) - set(ANIMAL_SLOTS)
    if unknown:
        raise ValueError(f"動物の欄が無い: {', '.join(sorted(unknown))}")
    for key, value in given_animals.items():
        text = str(value or "").strip()
        if not text:
            continue
        ref.reject_likeness(text)
        slots["animals"][key] = text
    if str(place or "").strip():
        ref.reject_likeness(place)
        slots["place"] = str(place).strip()
    by_id = {row["id"]: row for row in filled["captions"]}
    for key, value in dict(lines or {}).items():
        if key not in by_id:
            raise ValueError(f"セリフの id が無い: {key}")
        text = str(value or "").strip()
        if not text:
            continue
        ref.reject_likeness(text)
        if _norm(text) == _norm(by_id[key]["source_line"]):
            raise ValueError(f"元のセリフは入れない: {key}")
        by_id[key]["line"] = text
    return filled


def blocked(pack: Mapping[str, Any]) -> list[str]:
    """Slots that are still empty or cannot reach H3 in English. Empty means the prompt must not invent them."""
    reasons = []
    slots = pack["slots"]
    if slots.get("person") == SLOT:
        reasons.append("人は入力のまま")
    animals = slots.get("animals") or {}
    for key in ANIMAL_SLOTS:
        if animals.get(key) == SLOT:
            reasons.append(f"{ROLE_JA[key]}の動物は入力のまま")
    if slots.get("place") == SLOT:
        reasons.append("場所は入力のまま")
    for row in pack["captions"]:
        if row.get("line") == SLOT:
            reasons.append(f"{row['id']} のセリフは入力のまま")
    reasons.extend(slot_reasons(pack))
    return reasons


def line_fit_reasons(pack: Mapping[str, Any], probe: Any) -> list[str]:
    """Stop before bake when a new line is longer than the measured speech window.

    Only packs with ``line_must_fit`` are checked. Other sheets keep their own
    cut times. ``probe(text, role)`` returns seconds, or None when it cannot
    measure. A failure is a stop, not a guessed length. Cuts are not moved.
    """
    if not pack.get("line_must_fit"):
        return []
    reasons = []
    by_shot = {shot["id"]: shot for shot in pack["shots"]}
    for row in pack["captions"]:
        text = str(row.get("line") or "").strip()
        if not text or text == SLOT:
            continue
        window = row.get("fit_s")
        if window and len(window) == 2:
            span = round(float(window[1]) - float(window[0]), 3)
        else:
            shot = by_shot[row["shot"]]
            span = round(float(shot["end_s"]) - float(shot["start_s"]), 3)
        if span <= 0:
            reasons.append(f"{row['id']} の秒が測れない")
            continue
        try:
            heard = probe(text, str(row["role"]))
        except Exception:
            heard = None
        if heard is None:
            reasons.append(f"{row['id']} の秒が測れない")
            continue
        try:
            spoken = round(float(heard), 3)
        except (TypeError, ValueError):
            reasons.append(f"{row['id']} の秒が測れない")
            continue
        if spoken > span + 0.05:
            reasons.append(f"{row['id']} は {_num(spoken)} 秒。せりふの秒は {_num(span)} 秒。カットは動かさない。")
    return reasons


def prompt_text(pack: Mapping[str, Any]) -> str:
    """English shot prompt. Evidence lines and the source cast stay out."""
    slots = pack["slots"]
    animals = slots["animals"]
    identity = {
        "guest": animals["guest"],
        "retort": animals["retort"],
        "polite": animals["polite"],
        "owner": slots["person"],
        "indoor_pair": f"{animals['retort']} and {animals['polite']}",
    }
    lines = [
        "The shot order, camera, timing, and which role speaks stay as listed.",
        f"Place: {slots['place']}.",
        "No source account name, logo, or watermark is drawn.",
        "Caption: one line, white gothic, thin shadow, lower center, no box.",
        "The words on screen are the supplied line for that turn.",
        "",
    ]
    grouped: dict[str, list] = {}
    for row in pack["captions"]:
        grouped.setdefault(row["shot"], []).append(row)
    for index, shot in enumerate(pack["shots"], start=1):
        who = ", ".join(ROLE_JA[role] for role in shot["on_screen"]) or "なし"
        lines.append(
            f"[Shot {index}] {_num(shot['start_s'])} to {_num(shot['end_s'])}. "
            f"{shot['camera']} {shot['picture']} On screen: {who}."
        )
        for row in grouped.get(shot["id"], []):
            speaker = identity[row["role"]]
            if row["line"] == SLOT:
                lines.append(f"{ROLE_JA[row['role']]} ({speaker}) speaks. The words are not supplied.")
            else:
                lines.append(f"{ROLE_JA[row['role']]} ({speaker}) says: {row['line']}")
    text = "\n".join(lines) + "\n"
    for row in pack["captions"]:
        source = str(row["source_line"])
        if len(source) >= 4 and source in text:
            raise ValueError(f"元のセリフがプロンプトに入った: {row['id']}")
        if row["line"] == SLOT and source in text:
            raise ValueError(f"元のセリフがプロンプトに入った: {row['id']}")
    for shot in pack["shots"]:
        seen = str(shot.get("source_seen") or "")
        if seen and seen in text:
            raise ValueError(f"元の画面がプロンプトに入った: {shot['id']}")
    return text


def render_markdown(pack: Mapping[str, Any]) -> str:
    """Human sheet. Evidence stays labeled. The four slots stay empty until filled."""
    reasons = blocked(pack)
    out = [
        f"# 構成 {pack['source_id']}",
        "",
        "ショット順、カメラ、秒、誰が話すか、字幕の形、オチの形は固定。",
        "変えるのは人、動物、セリフ、場所。元の動画ファイルはこのリポジトリに置かない。",
        "独立したナレーションは無い。声はせりふ。",
        "",
        "## 測り方",
        "",
        f"- 尺 {_num(pack['duration_s'])} 秒。画面 {pack['canvas']}。{pack['fps']} fps。",
        f"- カット: {pack['measure']['cuts']}",
        f"- 無音: {pack['measure']['silences']}",
        f"- 字幕: {pack['measure']['captions']}",
        f"- 曲: {pack['measure']['music']}",
        f"- 字幕の高さ: {pack['measure']['caption_y']}",
        "",
        "## 欄",
        "",
        f"- 人: {pack['slots']['person']}",
        f"- 客の動物: {pack['slots']['animals']['guest']}",
        f"- ツッコミの動物: {pack['slots']['animals']['retort']}",
        f"- 丁寧の動物: {pack['slots']['animals']['polite']}",
        f"- 場所: {pack['slots']['place']}",
        f"- セリフ: {sum(1 for row in pack['captions'] if row['line'] == SLOT)} 件が入力",
        "",
        "## 口調",
        "",
    ]
    for role in ROLES:
        out.append(f"- {ROLE_JA[role]}: {pack['registers'][role]}")
    out.extend(["", "## 字幕", ""])
    style = pack["subtitle"]
    out.append(
        f"{style['font']}。{style['edge']}。{style['lines']}行。枠は{'あり' if style['box'] else 'なし'}。"
        f"{style['place']}。{style['content']}"
    )
    mark = pack["watermark"]
    out.append(f"透かしは{mark['places']}。文字は{mark['text']}。")
    out.extend(["", "## オチの形", ""])
    out.extend(f"- {step}" for step in pack["punch"])
    out.extend(["", "## ショット", ""])
    for shot in pack["shots"]:
        who = "、".join(ROLE_JA[role] for role in shot["on_screen"]) or "なし"
        note = f" {shot['note']}" if shot.get("note") else ""
        out.append(
            f"- {shot['id']} {_num(shot['start_s'])}–{_num(shot['end_s'])}秒。"
            f"{shot['picture']} カメラ: {shot['camera']} 画面: {who}。{note}"
        )
    out.extend(
        [
            "",
            "## ナレーション",
            "",
            "語り手は置かない。下のせりふが声。見えた秒は画面文字が出ていた時刻で、発話の頭と尻ではない。",
            "",
        ]
    )
    for row in narration_of(pack):
        seen = "、".join(_num(item) for item in row["seen_s"])
        extra = f" 働き: {row['function']}。" if row["function"] else ""
        out.append(
            f"- {row['id']} {row['role_ja']}。{row['register']} ショット {row['shot']}。"
            f"見えた秒 {seen}。{extra}セリフ: {row['line']}。"
        )
    out.extend(["", "## キャプション", ""])
    for row in captions_of(pack):
        seen = "、".join(_num(item) for item in row["seen_s"])
        out.append(
            f"- {row['id']} {row['role_ja']}。見えた秒 {seen}。"
            f"出す文: {row['line']}。証拠: {row['source_line']}。"
        )
    out.extend(["", "## 未入力", ""])
    if reasons:
        out.extend(f"- {reason}" for reason in reasons)
    else:
        out.append("- なし")
    out.append("")
    return "\n".join(out)


_LINE_KEY = re.compile(r"^(c\d+)\s*[:：]?\s*(.*)$")


def _shot_edges(duration_s: float, cuts: Sequence[float] | None) -> list[float]:
    """Interior cuts become shot boundaries. None means the cuts were not measured."""
    if cuts is None:
        raise ValueError("カットが測れない")
    duration = round(float(duration_s), 3)
    if duration <= 0:
        raise ValueError("尺が測れない")
    points = [0.0]
    for raw in cuts:
        cut = round(float(raw), 3)
        if cut <= 0 or cut >= duration:
            continue
        if cut - points[-1] < 0.001:
            continue
        points.append(cut)
    if duration - points[-1] < 0.001:
        raise ValueError("カットが測れない")
    points.append(duration)
    return points


def _host_shot(shots: Sequence[Mapping[str, Any]], start: float, end: float) -> Mapping[str, Any]:
    """The shot that holds the most of this speech. Ties stay with the earlier shot."""
    best: Mapping[str, Any] | None = None
    best_span = 0.0
    for shot in shots:
        shared = min(end, float(shot["end_s"])) - max(start, float(shot["start_s"]))
        if shared > best_span:
            best_span = shared
            best = shot
    if best is None:
        raise ValueError("せりふの秒が尺の外")
    return best


def homage_pack(
    *,
    duration_s: float,
    cuts: Sequence[float] | None,
    lines: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """A sheet from measured cuts and speech times. Spoken words are not stored.

    On screen is only the speaker whose time was measured. Camera movement is
    not measured, so it is not described. The picture names no source place
    and no source face. More than five speakers stops, instead of inventing a role.
    """
    edges = _shot_edges(duration_s, cuts)
    usable: list[dict[str, Any]] = []
    for row in lines or []:
        start = round(max(0.0, float(row["start_s"])), 3)
        end = round(min(edges[-1], float(row["end_s"])), 3)
        if end - start < 0.05:
            continue
        usable.append({"start_s": start, "end_s": end, "speaker": str(row.get("speaker") or "")})
    if not usable:
        raise ValueError("せりふが読めない。文は足さない。")
    speakers: list[str] = []
    for row in usable:
        if row["speaker"] not in speakers:
            speakers.append(row["speaker"])
    if len(speakers) > len(ROLES):
        raise ValueError("話者が5役より多い。足の役は作らない。")
    role_of = {speaker: ROLES[index] for index, speaker in enumerate(speakers)}
    shots: list[dict[str, Any]] = []
    for index in range(len(edges) - 1):
        shots.append(
            {
                "id": f"s{index + 1:02d}",
                "start_s": edges[index],
                "end_s": edges[index + 1],
                "on_screen": [],
                "camera": "カメラの動きは測っていない。",
                "picture": "誰も口を開かない。背景は場所の欄。文字は無い。曲は無い。",
            }
        )
    captions: list[dict[str, Any]] = []
    for index, row in enumerate(usable, start=1):
        shot = _host_shot(shots, row["start_s"], row["end_s"])
        role = role_of[row["speaker"]]
        if role not in shot["on_screen"]:
            shot["on_screen"].append(role)
        shot["picture"] = "話している役だけ口が開閉する。ほかの口は閉じている。背景は場所の欄。文字は無い。曲は無い。"
        left = max(row["start_s"], float(shot["start_s"]))
        right = min(row["end_s"], float(shot["end_s"]))
        seen = round((left + right) / 2, 3)
        captions.append(
            {
                "id": f"c{index:02d}",
                "shot": shot["id"],
                "role": role,
                "seen_s": [seen],
                "source_line": f"e-{index:02d}",
                "line": SLOT,
                "function": "",
                "fit_s": [row["start_s"], row["end_s"]],
            }
        )
    interior = edges[1:-1]
    return {
        "schema": "affi-repro-structure/v1",
        "source_id": "homage",
        "pattern": "homage",
        "duration_s": edges[-1],
        "canvas": "1080x1920",
        "fps": "測っていない",
        "file_in_repo": False,
        "line_must_fit": True,
        "cuts_s": interior,
        "silences_s": [],
        "measure": {
            "cuts": f"カットは mp4 の画面の切り替わり。{len(interior)} か所。",
            "silences": "この入力では測っていない。",
            "captions": "せりふの秒と話者だけを測った。元の文は入れない。",
            "music": "曲は仕上げ。H3 には作らせない。",
            "caption_y": "仕様の「下から約30%」を使う。",
        },
        "change_only": ["person", "animals", "lines", "place"],
        "slots": {
            "person": SLOT,
            "animals": {"guest": SLOT, "retort": SLOT, "polite": SLOT},
            "place": SLOT,
        },
        "narration": "独立した語りは無い。声はせりふ。",
        "registers": {role: "測った話者。口調は測っていない。" for role in ROLES},
        "subtitle": {
            "font": "白ゴシック",
            "edge": "細い影",
            "lines": 1,
            "box": False,
            "place": "中央やや下",
            "content": "差し替えた文を出す。元の文は出さない。",
        },
        "watermark": {"places": "上と中段", "text": "自分のアカウント名"},
        "punch": ["オチの形は測っていない。"],
        "shots": shots,
        "captions": captions,
    }


def parse_lines(text: str, ids: Sequence[str]) -> dict[str, str]:
    """One spoken line per caption. A blank row stays empty. Evidence is not read."""
    known = list(ids)
    raw = str(text or "").splitlines()
    filled = [line.strip() for line in raw if line.strip()]
    if not filled:
        return {}
    keyed = [_LINE_KEY.match(line) for line in filled]
    if any(match and match.group(1) in known for match in keyed):
        if not all(match and match.group(1) in known for match in keyed):
            raise ValueError("セリフは c01 の形か、上から順かのどちらか")
        out: dict[str, str] = {}
        for match in keyed:
            assert match is not None
            spoken = match.group(2).strip()
            if spoken:
                out[match.group(1)] = spoken
        return out
    if len(raw) > len(known):
        raise ValueError(f"セリフが {len(known)} 件より多い")
    out = {}
    for index, line in enumerate(raw):
        spoken = line.strip()
        if spoken:
            out[known[index]] = spoken
    return out


# Longer phrases first. A hit consumes those characters so a shorter phrase cannot fire inside it.
_STATIC = "The camera holds a static shot"
_CAMERA_MOTION = (
    ("カメラの動きは測っていない", "The camera path was not measured. The camera holds a static shot."),
    ("黒で切れる", "The picture cuts to black and the camera holds that black frame."),
    ("低い位置から寄る", "The camera pushes in from a low height."),
    ("低い位置から追う", "The camera tracks the moving body from a low height."),
    ("肩越しに少し寄る", "The camera pushes in over the shoulder with small amplitude."),
    ("家の方へ少し傾く", "The camera tilts toward the house with small amplitude."),
    ("視線に合わせて横へ振る", "The camera pans sideways along the gaze."),
    ("引きながら少し下がる", "The camera pulls out and shifts back with small amplitude."),
    ("上から水面へ見下ろす", "The camera tilts down toward the water from above."),
    ("視線の先", "The camera holds a static shot where the gaze lands."),
    ("顔と前足", "The camera holds a static shot on the face and the forepaw."),
    ("前足と顔", "The camera holds a static shot on the forepaw and the face."),
    ("上から見る", "The camera tilts down from above."),
    ("下から見上げる", "The camera tilts up from below."),
    ("下から見る", "The camera tilts up from below."),
    ("顔へ少し寄る", "The camera pushes in on the face with small amplitude."),
    ("顔の寄り", "The camera holds a static shot on the face at close range."),
    ("顔へ寄る", "The camera pushes in on the face."),
    ("横から寄る", "The camera pushes in from the side."),
    ("横から追う", "The camera tracks the moving body from the side."),
    ("少し寄る", "The camera pushes in with small amplitude."),
    ("へ寄る", "The camera pushes in."),
    ("ガラス越し", "The camera holds a static shot through the glass."),
    ("網目越し", "The camera holds a static shot through the mesh."),
    ("仕切り越し", "The camera holds a static shot through the partition."),
    ("横から見る", "The camera holds a static shot from the side."),
    ("横顔", "The camera holds a static shot aimed at the side of the face."),
    ("立ち姿", "The camera holds a static shot aimed at the standing body."),
    ("背中", "The camera holds a static shot aimed at the backs."),
    ("正面", "The camera holds a static shot aimed at the front."),
    ("動きは少ない", "The camera travels only a small distance."),
    ("床の高さ", "The camera holds a static shot at floor height."),
    ("少し引く", "The camera pulls out with small amplitude."),
    ("奥に建物", "A building stays in the distance."),
    ("寄る", "The camera pushes in."),
    ("寄り", "The camera holds a static shot at close range."),
    ("引き", "The camera pulls out."),
    ("低い", "The camera holds a static shot from a low height."),
    ("同じ向き", "The facing stays the same as the earlier shot."),
    ("手すり", "A rail stays in the frame."),
)
_JAW_OPENS = "The lower jaw drops and rises, more than once."
_MOUTH_CLOSED = "The mouth stays closed. The jaw does not travel."
_MOUTH_CLOSED_THAT = "That mouth stays closed. The jaw does not travel."
_MOUTH_OPEN = "The mouth stays open. The jaw does not travel."
_MOUTH_UP = "The mouth points upward and stays open. The jaw does not travel."
_MOUTH_PAD = "The mouth keeps hold of the pad. The jaw does not travel."
_MOUTH_STICK = "The mouth keeps hold of a thin stick. The jaw does not travel."
_TEETH = "The eyelids squeeze shut and the jaw drops until the teeth show."
_CARRY_PAD = "The mouth keeps hold of a flat white pad while the legs step forward."
_STAND_DOOR = "The body stands upright in the doorway."
_LOOK_POOL = "The head turns toward the vinyl pool at the edge of the yard."
_EVERY_MOUTH = "Every mouth stays closed. Those jaws do not travel."
_OTHER_MOUTHS = "The other mouths stay closed. Those jaws do not travel."
_STAND_THEN_SIT = "The weight moves onto the hind legs and the torso rises, then the hind legs fold and the body sits."
_STAND = "The weight moves onto the hind legs and the torso rises until the body is standing."
_STAND_GRIP = (
    "The weight moves onto the hind legs and the torso rises until the body is standing, "
    "and both forepaws close around a vertical stick held in front of the chest."
)
_SIT = "The body stays seated."
_STEP_BACK = "The bodies step backward."
_MOVE_IN = "The body moves in through the opening."
_BINDABLE = frozenset(
    {_JAW_OPENS, _MOUTH_CLOSED, _MOUTH_CLOSED_THAT, _MOUTH_OPEN, _MOUTH_UP, _MOUTH_PAD, _MOUTH_STICK}
)
_PLURAL_ROLES = frozenset({"two animals"})
_ROLE_MARK = (
    ("ツッコミ役", "retort"),
    ("ツッコミ", "retort"),
    ("丁寧役", "polite one"),
    ("丁寧", "polite one"),
    ("飼い主", "person"),
    ("動物2匹", "two animals"),
    ("片方の動物", "one animal"),
    ("2匹", "two animals"),
    ("客", "guest"),
    ("犬", "dog"),
    ("人", "person"),
)
_BODY_MOTION = (
    ("口を開閉しながら", _JAW_OPENS),
    ("口が開閉する", _JAW_OPENS),
    ("口を開閉する", _JAW_OPENS),
    ("口はパッドをくわえたまま喋らない", _MOUTH_PAD),
    ("口に細い棒をくわえる", _MOUTH_STICK),
    ("ほかの口は閉じている", _OTHER_MOUTHS),
    ("誰も口を開かない", _EVERY_MOUTH),
    ("全員の口は閉じている", _EVERY_MOUTH),
    ("口が開いている", _MOUTH_OPEN),
    ("口が上を向く", _MOUTH_UP),
    ("口は喋らない", _MOUTH_CLOSED),
    ("口も閉じている", _MOUTH_CLOSED_THAT),
    ("口は閉じている", _MOUTH_CLOSED),
    ("口を閉じている", _MOUTH_CLOSED),
    ("口は閉じ", _MOUTH_CLOSED),
    ("口は無い", "No mouth is in the frame."),
    ("前足は止まったまま", "That forepaw stays still and does not travel."),
    ("前足はしまったまま", "The forepaws stay folded under the chest and do not travel."),
    ("後ろ脚で立ち、前足二本で縦の棒を胸の前で握る", _STAND_GRIP),
    ("後ろ脚で立ち、あとで座る", _STAND_THEN_SIT),
    ("後ろ脚で立つ", _STAND),
    ("後ろ脚で立ち", _STAND),
    ("背中を向けて座り、頭を向かい合わせる", "The bodies stay seated with the backs toward the lens, and the heads turn toward each other."),
    ("前足を一本口の棒へ上げて下ろす", "One forepaw rises to the thin stick at the mouth and then lowers. The stick leaves the mouth."),
    ("前足を一本、胸の前で上げたまま", "One forepaw stays raised in front of the chest."),
    ("前足二本で縦の棒を頭の横へ上げる", "Both forepaws raise the vertical stick until it is beside the head."),
    ("前足二本で縦の棒を胸の前で握る", "Both forepaws close around a vertical stick held in front of the chest."),
    ("前足で縦の棒を頭の上に横たえる", "One forepaw lays the stick across the top of the head."),
    ("片手を頭の上へ上げる", "One hand rises onto the top of the head."),
    ("まぶたをきつく閉じ、歯が見える", _TEETH),
    ("両膝を床につけ、両手を床の平たい物に置く", "Both knees stay on the floor and both hands stay on the flat object on the floor."),
    ("床を離れて前へ飛ぶ", "The body leaves the floor and travels forward through the air."),
    ("縦の棒が床へ落ちる", "The stick drops to the floor and stays there."),
    ("後ろの体はぼける", "The body stays behind and out of focus."),
    ("立ち上がる", _STAND),
    ("前足でプールの水面を叩く", "The forepaw lifts, strikes the water, and returns."),
    ("前足を体の下にしまう", "The forepaws fold back under the chest."),
    ("前足を一本上げて", "One forepaw lifts and stays raised."),
    ("二回、それからもう一回踏む", "The forepaw presses down twice, then once more."),
    ("毛布の端を少しめくる", "One paw lifts the blanket edge a short way."),
    ("白い敷きパッドをくわえて歩く", _CARRY_PAD),
    ("くわえて歩く", "The mouth keeps hold of the object while the legs step forward."),
    ("パッドが水面に落ち", "The pad drops onto the water."),
    ("水が渦を巻いてプールから無くなり", "The water turns in a vortex until the pool is empty."),
    ("底の地面がひび割れる", "The ground at the bottom splits into cracks."),
    ("芝生をプールへ走る", "The legs cycle and the body travels forward across the grass."),
    ("庭を走る", "The legs cycle and the body travels forward across the yard."),
    ("走る", "The legs cycle and the body travels forward."),
    ("画面に向かう", "The body turns to face the lens."),
    ("正面を向いて", "The body turns to face the lens."),
    ("家の方を見て", "The head turns toward the house."),
    ("庭の端のビニールプールを見る", _LOOK_POOL),
    ("ひび割れた底を見て", "The head tilts down toward the cracked ground."),
    ("踏んでいる前足を見て", "The head turns toward the forepaw that is pressing down."),
    ("自分の前足を見る", "The head turns down toward that one's own forepaw."),
    ("ツッコミの前足を見て", "The head turns toward the retort's forepaw."),
    ("水面を見て", "The head tilts down toward the water."),
    ("パッドを見て", "The head turns toward the pad."),
    ("前足を見て", "The head turns toward the forepaw."),
    ("上を見る", "The head tilts upward."),
    ("後ろから見る", "The view stays from behind the two animals."),
    ("空の水入れの横にいる", "The body stays beside the empty water bowl."),
    ("短い足の茶色い犬は床のラグで", "The short-legged brown dog stays on the floor rug."),
    ("外に小さくいる", "The body stays small in the distance outside."),
    ("戸口に小さくいる", "The body stays small in the doorway."),
    ("戸口に立って", _STAND_DOOR),
    ("手すりにいる", "The body stays at the rail."),
    ("人の顔は出さない", "The person's face stays out of frame."),
    ("並んでいる", "The bodies stay side by side."),
    ("並んで", "The bodies stay side by side."),
    ("が手前", "The body stays closer to the lens."),
    ("は端", "The body stays at the edge."),
    ("客の寄り", "The guest stays in the close framing."),
    ("が入る", _MOVE_IN),
    ("袋を持つ", "The hand keeps hold of the bag."),
    ("仕切りの向こうで", "The body stays on the far side of the partition."),
    ("前足は毛布の上", "The forepaw rests on the blanket."),
    ("丁寧役の顔", "The face stays toward the lens."),
    ("飼い主の顔", "The face stays toward the lens."),
    ("空", "The sky stays in the background."),
    ("動物2匹の横顔", "The heads stay in profile."),
    ("の背中", "The backs stay toward the lens."),
    ("飼い主の脚", "The person's legs stay in the frame."),
    ("飼い主の腕", "The person's arm stays in the frame."),
    ("植物がある", "A plant stays in the frame."),
    ("前足に粉がついている", "Powder stays on the forepaw."),
    ("粉が二つある", "Two patches of powder stay where they are."),
    ("窓の光", "Window light falls across the room."),
    ("昼のリビング", "This shot stays in the living room in daylight."),
    ("背景は場所の欄", "The background stays the place named above."),
    ("ゆるい部屋着", "The person wears loose indoor clothes."),
    ("髪はひとつ結び", "The person's hair stays tied in one knot."),
    ("屋外", "This shot stays outdoors."),
    ("室内", "This shot stays indoors."),
    ("リビング", "This shot stays in the living room."),
    ("庭", "This shot stays in the yard."),
    ("昼", "This shot stays in daylight."),
    ("座って", _SIT),
    ("座る", _SIT),
    ("黒画面", "The frame stays black."),
    ("白い敷きパッドだけが平らにある", "Only the flat white pad lies there and does not move."),
    ("平らにある", "The pad lies flat and does not move."),
    ("網目", "A mesh stays between the lens and the face."),
    ("仕切りが開く", "The partition swings open."),
    ("身を引く", _STEP_BACK),
    ("中へ入る", _MOVE_IN),
    ("小さい袋を持つ", "One hand keeps hold of a small bag."),
    ("羽が少し開く", "The wings open a little."),
    ("前足が毛布の上で止まる", "The forepaw comes down on the blanket and stays there."),
    ("踏みながら", "The forepaw keeps pressing down."),
    ("踏む", "The forepaw presses down."),
)


def _covered_phrases(text: str, table: Sequence[tuple[str, str]]) -> list[str]:
    """English for phrases already written. Unlisted words are not expanded."""
    used = [False] * len(text)
    found: list[tuple[int, str]] = []
    for phrase, english in sorted(table, key=lambda item: len(item[0]), reverse=True):
        start = 0
        while True:
            at = text.find(phrase, start)
            if at < 0:
                break
            end = at + len(phrase)
            if any(used[at:end]):
                start = at + 1
                continue
            for index in range(at, end):
                used[index] = True
            found.append((at, english))
            start = end
    found.sort()
    out: list[str] = []
    for _at, english in found:
        if english not in out:
            out.append(english)
    return out


def _clauses(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"[。．]", text) if part.strip()]


def _role_hits(clause: str, marks: Sequence[str]) -> list[str]:
    """Roles already named in this clause. 人 inside 成人 is not a role."""
    used = [False] * len(clause)
    found: list[tuple[int, str]] = []
    ordered = sorted(_ROLE_MARK, key=lambda item: len(item[0]), reverse=True)
    mark_order = sorted(marks, key=len, reverse=True)
    for word, label in ordered:
        start = 0
        while True:
            at = clause.find(word, start)
            if at < 0:
                break
            end = at + len(word)
            if any(used[at:end]):
                start = at + 1
                continue
            if word == "人" and at > 0 and clause[at - 1] not in "。、 　\n":
                start = at + 1
                continue
            mark_len = 0
            if mark_order:
                matched = next((mark for mark in mark_order if clause.startswith(mark, end)), "")
                if not matched:
                    start = at + 1
                    continue
                mark_len = len(matched)
            for index in range(at, end):
                used[index] = True
            found.append((at, label))
            start = end + mark_len
    found.sort()
    out: list[str] = []
    for _at, label in found:
        if label not in out:
            out.append(label)
    return out


# Labels from _ROLE_MARK that are one sheet role. Their cast name replaces the label.
_LABEL_ROLE = {"guest": "guest", "retort": "retort", "polite one": "polite", "person": "owner"}


def _possessive(who: Sequence[str], names: Mapping[str, str] | None = None) -> str:
    bits: list[str] = []
    for label in who:
        called = (names or {}).get(label, "")
        if called:
            bits.append(f"{called}'s")
        elif label == "two animals":
            bits.append("the two animals'")
        elif label == "one animal":
            bits.append("one animal's")
        else:
            bits.append(f"the {label}'s")
    if len(bits) == 1:
        return bits[0][0].upper() + bits[0][1:]
    head = bits[0][0].upper() + bits[0][1:]
    if len(bits) == 2:
        return f"{head} and {bits[1]}"
    return f"{head}, {', '.join(bits[1:-1])}, and {bits[-1]}"


def _bind_mouth(english: str, who: Sequence[str], names: Mapping[str, str] | None = None) -> str:
    """Keep a shut jaw from cancelling the jaw that this clause names."""
    if not who or english not in _BINDABLE:
        return english
    plural = len(who) > 1 or any(name in _PLURAL_ROLES for name in who)
    name = _possessive(who, names)
    if english == _JAW_OPENS:
        if plural:
            return f"{name} lower jaws drop and rise, more than once."
        return f"{name} lower jaw drops and rises, more than once."
    if english == _MOUTH_OPEN:
        if plural:
            return f"{name} mouths stay open. Those jaws do not travel."
        return f"{name} mouth stays open. That jaw does not travel."
    if english == _MOUTH_UP:
        if plural:
            return f"{name} mouths point upward and stay open. Those jaws do not travel."
        return f"{name} mouth points upward and stays open. That jaw does not travel."
    if english == _MOUTH_PAD:
        if plural:
            return f"{name} mouths keep hold of the pad. Those jaws do not travel."
        return f"{name} mouth keeps hold of the pad. That jaw does not travel."
    if english == _MOUTH_STICK:
        if plural:
            return f"{name} mouths keep hold of a thin stick. Those jaws do not travel."
        return f"{name} mouth keeps hold of a thin stick. That jaw does not travel."
    if plural:
        return f"{name} mouths stay closed. Those jaws do not travel."
    return f"{name} mouth stays closed. That jaw does not travel."


def _noun(single: str, plural: str, rest: str) -> tuple[str, str]:
    return (f"{{name}} {single} {rest}", f"{{name}} {plural} {rest}")


_NAMED = {
    _STAND_THEN_SIT: (
        "{name} weight moves onto the hind legs and the torso rises, then the hind legs fold and the body sits.",
        "{name} weight moves onto the hind legs and the torsos rise, then the hind legs fold and the bodies sit.",
    ),
    _STAND: _noun("weight moves onto the hind legs and the torso rises until the body is standing.", "weight moves onto the hind legs and the torsos rise until the bodies are standing.", ""),
    _STAND_GRIP: (
        "{name} weight moves onto the hind legs and the torso rises until the body is standing, and both forepaws close around a vertical stick held in front of the chest.",
        "{name} weight moves onto the hind legs and the torsos rise until the bodies are standing, and both forepaws close around a vertical stick held in front of the chest.",
    ),
    "The bodies stay seated with the backs toward the lens, and the heads turn toward each other.": (
        "{name} body stays seated with the back toward the lens, and the head turns toward the other head.",
        "{name} bodies stay seated with the backs toward the lens, and the heads turn toward each other.",
    ),
    "One forepaw rises to the thin stick at the mouth and then lowers. The stick leaves the mouth.": (
        "{name} forepaw rises to the thin stick at the mouth and then lowers. The stick leaves that mouth.",
        "{name} forepaws rise to the thin stick at the mouth and then lower. The stick leaves those mouths.",
    ),
    "One forepaw stays raised in front of the chest.": _noun(
        "forepaw stays raised in front of the chest.",
        "forepaws stay raised in front of the chest.",
        "",
    ),
    "Both forepaws raise the vertical stick until it is beside the head.": _noun(
        "forepaws raise the vertical stick until it is beside the head.",
        "forepaws raise the vertical stick until it is beside the head.",
        "",
    ),
    "Both forepaws close around a vertical stick held in front of the chest.": _noun(
        "forepaws close around a vertical stick held in front of the chest.",
        "forepaws close around a vertical stick held in front of the chest.",
        "",
    ),
    "One forepaw lays the stick across the top of the head.": _noun(
        "forepaw lays the stick across the top of the head.",
        "forepaws lay the stick across the top of the head.",
        "",
    ),
    "One hand rises onto the top of the head.": _noun(
        "hand rises onto the top of the head.",
        "hands rise onto the top of the head.",
        "",
    ),
    _TEETH: (
        "{name} eyelids squeeze shut and the jaw drops until the teeth show.",
        "{name} eyelids squeeze shut and the jaws drop until the teeth show.",
    ),
    "Both knees stay on the floor and both hands stay on the flat object on the floor.": _noun(
        "knees stay on the floor and both hands stay on the flat object on the floor.",
        "knees stay on the floor and both hands stay on the flat object on the floor.",
        "",
    ),
    "The body leaves the floor and travels forward through the air.": _noun(
        "body leaves the floor and travels forward through the air.",
        "bodies leave the floor and travel forward through the air.",
        "",
    ),
    "The body stays behind and out of focus.": _noun(
        "body stays behind and out of focus.",
        "bodies stay behind and out of focus.",
        "",
    ),
    _SIT: _noun("body stays seated.", "bodies stay seated.", ""),
    _STEP_BACK: _noun("body steps backward.", "bodies step backward.", ""),
    _MOVE_IN: _noun("body moves in through the opening.", "bodies move in through the opening.", ""),
    "The legs cycle and the body travels forward across the grass.": _noun(
        "legs cycle and the body travels forward across the grass.",
        "legs cycle and the bodies travel forward across the grass.",
        "",
    ),
    "The legs cycle and the body travels forward across the yard.": _noun(
        "legs cycle and the body travels forward across the yard.",
        "legs cycle and the bodies travel forward across the yard.",
        "",
    ),
    "The legs cycle and the body travels forward.": _noun(
        "legs cycle and the body travels forward.",
        "legs cycle and the bodies travel forward.",
        "",
    ),
    "The mouth keeps hold of the object while the legs step forward.": _noun(
        "mouth keeps hold of the object while the legs step forward.",
        "mouths keep hold of the object while the legs step forward.",
        "",
    ),
    _CARRY_PAD: _noun(
        "mouth keeps hold of a flat white pad while the legs step forward.",
        "mouths keep hold of a flat white pad while the legs step forward.",
        "",
    ),
    "The head tilts upward.": _noun("head tilts upward.", "heads tilt upward.", ""),
    "The head turns toward the house.": _noun("head turns toward the house.", "heads turn toward the house.", ""),
    _LOOK_POOL: _noun(
        "head turns toward the vinyl pool at the edge of the yard.",
        "heads turn toward the vinyl pool at the edge of the yard.",
        "",
    ),
    "The head tilts down toward the cracked ground.": _noun(
        "head tilts down toward the cracked ground.",
        "heads tilt down toward the cracked ground.",
        "",
    ),
    "The head turns toward the forepaw that is pressing down.": _noun(
        "head turns toward the forepaw that is pressing down.",
        "heads turn toward the forepaw that is pressing down.",
        "",
    ),
    "The head turns down toward that one's own forepaw.": _noun(
        "head turns down toward that one's own forepaw.",
        "heads turn down toward that one's own forepaw.",
        "",
    ),
    "The head turns toward the retort's forepaw.": _noun(
        "head turns toward the retort's forepaw.",
        "heads turn toward the retort's forepaw.",
        "",
    ),
    "The head tilts down toward the water.": _noun(
        "head tilts down toward the water.",
        "heads tilt down toward the water.",
        "",
    ),
    "The head turns toward the pad.": _noun("head turns toward the pad.", "heads turn toward the pad.", ""),
    "The head turns toward the forepaw.": _noun("head turns toward the forepaw.", "heads turn toward the forepaw.", ""),
    "The body turns to face the lens.": _noun("body turns to face the lens.", "bodies turn to face the lens.", ""),
    "The body stays beside the empty water bowl.": _noun(
        "body stays beside the empty water bowl.",
        "bodies stay beside the empty water bowl.",
        "",
    ),
    "The body stays small in the distance outside.": _noun(
        "body stays small in the distance outside.",
        "bodies stay small in the distance outside.",
        "",
    ),
    "The body stays small in the doorway.": _noun(
        "body stays small in the doorway.",
        "bodies stay small in the doorway.",
        "",
    ),
    _STAND_DOOR: _noun(
        "body stands upright in the doorway.",
        "bodies stand upright in the doorway.",
        "",
    ),
    "The body stays at the rail.": _noun("body stays at the rail.", "bodies stay at the rail.", ""),
    "The bodies stay side by side.": _noun("body stays side by side.", "bodies stay side by side.", ""),
    "The body stays closer to the lens.": _noun("body stays closer to the lens.", "bodies stay closer to the lens.", ""),
    "The body stays at the edge.": _noun("body stays at the edge.", "bodies stay at the edge.", ""),
    "The heads stay in profile.": _noun("head stays in profile.", "heads stay in profile.", ""),
    "The backs stay toward the lens.": _noun("back stays toward the lens.", "backs stay toward the lens.", ""),
    "The forepaw lifts, strikes the water, and returns.": _noun(
        "forepaw lifts, strikes the water, and returns.",
        "forepaws lift, strike the water, and return.",
        "",
    ),
    "The forepaws fold back under the chest.": _noun(
        "forepaws fold back under the chest.",
        "forepaws fold back under the chest.",
        "",
    ),
    "One forepaw lifts and stays raised.": _noun(
        "forepaw lifts and stays raised.",
        "forepaws lift and stay raised.",
        "",
    ),
    "The forepaw presses down twice, then once more.": _noun(
        "forepaw presses down twice, then once more.",
        "forepaws press down twice, then once more.",
        "",
    ),
    "One paw lifts the blanket edge a short way.": _noun(
        "paw lifts the blanket edge a short way.",
        "paws lift the blanket edge a short way.",
        "",
    ),
    "The forepaw comes down on the blanket and stays there.": _noun(
        "forepaw comes down on the blanket and stays there.",
        "forepaws come down on the blanket and stay there.",
        "",
    ),
    "The forepaw keeps pressing down.": _noun("forepaw keeps pressing down.", "forepaws keep pressing down.", ""),
    "The forepaw presses down.": _noun("forepaw presses down.", "forepaws press down.", ""),
    "That forepaw stays still and does not travel.": _noun(
        "forepaw stays still and does not travel.",
        "forepaws stay still and do not travel.",
        "",
    ),
    "The forepaws stay folded under the chest and do not travel.": _noun(
        "forepaws stay folded under the chest and do not travel.",
        "forepaws stay folded under the chest and do not travel.",
        "",
    ),
    "The wings open a little.": _noun("wings open a little.", "wings open a little.", ""),
    "One hand keeps hold of a small bag.": _noun(
        "hand keeps hold of a small bag.",
        "hands keep hold of a small bag.",
        "",
    ),
    "The hand keeps hold of the bag.": _noun("hand keeps hold of the bag.", "hands keep hold of the bag.", ""),
    "The body stays on the far side of the partition.": _noun(
        "body stays on the far side of the partition.",
        "bodies stay on the far side of the partition.",
        "",
    ),
    "The forepaw rests on the blanket.": _noun(
        "forepaw rests on the blanket.",
        "forepaws rest on the blanket.",
        "",
    ),
    "The face stays toward the lens.": _noun("face stays toward the lens.", "faces stay toward the lens.", ""),
}


def _bind_actor(english: str, who: Sequence[str], names: Mapping[str, str] | None = None) -> str:
    """A written move stays with the role named in that clause."""
    pair = _NAMED.get(english)
    if pair is None or not who:
        return english
    plural = len(who) > 1 or any(role in _PLURAL_ROLES for role in who)
    text = pair[1 if plural else 0].format(name=_possessive(who, names))
    return " ".join(text.split())


def _body_lines(
    picture: str,
    camera: str,
    timed_jaw: bool,
    names: Mapping[str, str] | None = None,
) -> list[str]:
    """Motion already written, one clause at a time, with the role that clause names."""
    last: list[str] = []
    out: list[str] = []
    for clause in _clauses(picture) + _clauses(camera):
        owners = _role_hits(clause, ("が", "は", "も", "と", "の口"))
        if owners:
            last = owners
        else:
            mentioned = _role_hits(clause, ())
            if mentioned:
                last = mentioned
        who = owners or last
        for english in _covered_phrases(clause, _BODY_MOTION):
            if timed_jaw and english == _JAW_OPENS:
                continue
            if english in _BINDABLE:
                line = _bind_mouth(english, who, names)
            else:
                line = _bind_actor(english, who, names)
            line = _rename(line, names)
            if line not in out:
                out.append(line)
    return out


def _rename(line: str, names: Mapping[str, str] | None) -> str:
    """Fixed sentences that already say "the person" use that role's cast name."""
    for label, called in (names or {}).items():
        upper = called[0].upper() + called[1:]
        line = line.replace(f"The {label}'s", f"{upper}'s").replace(f"the {label}'s", f"{called}'s")
        line = line.replace(f"The {label} ", f"{upper} ")
    return line


def _cast(pack: Mapping[str, Any]) -> dict[str, dict[str, str] | None]:
    """English for each role slot. None is a role the story does not show.

    An empty or untranslatable slot keeps an empty description, so the prompt
    falls back to the role label and never carries the Japanese text.
    """
    slots = pack["slots"]
    animals = slots.get("animals") or {}
    raw = {
        "guest": animals.get("guest"),
        "retort": animals.get("retort"),
        "polite": animals.get("polite"),
        "owner": slots.get("person"),
    }
    out: dict[str, dict[str, str] | None] = {}
    for role, value in raw.items():
        text = str(value or "").strip()
        if text == NOT_SHOWN:
            out[role] = None
            continue
        full, name = "", ""
        if text and text != SLOT:
            try:
                full, name = slot_english(text)
            except ValueError:
                full, name = "", ""
        out[role] = {"full": full, "name": name}
    names = [entry["name"] for entry in out.values() if entry and entry["name"]]
    for entry in out.values():
        if entry and entry["name"] and names.count(entry["name"]) > 1:
            entry["name"] = ""
    return out


def _label_names(cast: Mapping[str, dict[str, str] | None]) -> dict[str, str]:
    """Shot labels such as "retort" mapped to the cast name, when the slot gives one."""
    found: dict[str, str] = {}
    for label, role in _LABEL_ROLE.items():
        entry = cast.get(role)
        if entry and entry["name"]:
            found[label] = entry["name"]
    dogs = [entry["name"] for entry in cast.values() if entry and entry["name"].endswith(" dog")]
    if len(dogs) == 1:
        found["dog"] = dogs[0]
    return found


def slot_preview(pack: Mapping[str, Any]) -> list[str]:
    """What each slot becomes in the H3 prompt, one line per slot."""
    slots = pack["slots"]
    animals = slots.get("animals") or {}
    labeled = [
        ("人", slots.get("person")),
        (f"{ROLE_JA['guest']}の動物", animals.get("guest")),
        (f"{ROLE_JA['retort']}の動物", animals.get("retort")),
        (f"{ROLE_JA['polite']}の動物", animals.get("polite")),
        ("場所", slots.get("place")),
    ]
    out = []
    for label, value in labeled:
        text = str(value or "").strip()
        if not text or text == SLOT:
            shown = "入力のまま"
        elif text == NOT_SHOWN and label != "場所":
            shown = "出さない（プロンプトに入れない）"
        else:
            try:
                shown = slot_english(text)[0]
            except ValueError:
                shown = "英語にできない（止まる）"
        out.append(f"{label} → {shown}")
    return out


def slot_reasons(pack: Mapping[str, Any]) -> list[str]:
    """Filled slots that cannot go to H3 in English, and hidden roles the sheet still shows."""
    reasons: list[str] = []
    slots = pack["slots"]
    animals = slots.get("animals") or {}
    labeled = [
        ("人", slots.get("person")),
        (f"{ROLE_JA['guest']}の動物", animals.get("guest")),
        (f"{ROLE_JA['retort']}の動物", animals.get("retort")),
        (f"{ROLE_JA['polite']}の動物", animals.get("polite")),
        ("場所", slots.get("place")),
    ]
    for label, value in labeled:
        text = str(value or "").strip()
        if not text or text == SLOT or (text == NOT_SHOWN and label != "場所"):
            continue
        try:
            slot_english(text)
        except ValueError as exc:
            reasons.append(
                f"{label}「{text}」は英語にできない語がある: {exc}。英語で書けば、そのまま H3 に渡す。"
            )
    hidden = {role for role, entry in _cast(pack).items() if entry is None}
    for shot in pack["shots"]:
        shown = [role for role in shot.get("on_screen") or [] if role in hidden]
        for role in shown:
            reasons.append(f"{shot['id']} の画面に「{NOT_SHOWN}」の{ROLE_JA[role]}がいる")
    for row in pack["captions"]:
        text = str(row.get("line") or "").strip()
        if row.get("role") in hidden and text and text != SLOT:
            reasons.append(f"{row['id']} は「{NOT_SHOWN}」の{ROLE_JA[row['role']]}のせりふ")
    return reasons


_TRAVEL = ("pushes in", "pulls out", "pans ", "tilts ", "tracks ")


def _aim(tail: str) -> str:
    if tail.startswith("through "):
        return f"The lens looks {tail}."
    return f"The lens stays {tail}."


def _merge_camera(parts: Sequence[str]) -> list[str]:
    """A held frame stays one static sentence. A written move is not also called static."""
    tails: list[str] = []
    rest: list[str] = []
    for part in parts:
        if part.startswith(_STATIC):
            tail = part[len(_STATIC) :].strip(" .")
            if tail and tail not in tails:
                tails.append(tail)
            elif not tail and not tails:
                tails.append("")
        else:
            rest.append(part)
    travels = [part for part in rest if any(kind in part for kind in _TRAVEL)]
    extras = [part for part in rest if part not in travels]
    usable = [tail for tail in tails if tail]
    if travels and usable:
        moves: list[str] = []
        for move in travels:
            if usable and move.startswith("The camera pushes in") and usable[0].startswith("from "):
                moves.append(move[:-1] + " " + usable.pop(0) + ".")
            else:
                moves.append(move)
        return [_aim(tail) for tail in usable] + moves + extras
    merged: list[str] = []
    if usable:
        merged.append(f"{_STATIC} {', '.join(usable)}.")
    elif tails:
        merged.append(f"{_STATIC}.")
    merged.extend(rest)
    return merged


def _stamp(seconds: float) -> str:
    whole = max(0.0, float(seconds))
    minutes = int(whole // 60)
    rem = whole - minutes * 60
    return f"{minutes:02d}:{rem:06.3f}"


_ON_EN = {
    "guest": "the guest",
    "retort": "the retort",
    "polite": "the polite one",
    "owner": "the person",
    "indoor_pair": "the two animals",
}


def _frame_line(roles: Sequence[str], cast: Mapping[str, dict[str, str] | None] | None = None) -> str:
    names: list[str] = []
    for role in roles:
        if role not in _ON_EN:
            continue
        entry = (cast or {}).get(role)
        names.append(entry["name"] if entry and entry["name"] else _ON_EN[role])
    if not names:
        return ""
    if len(names) == 1:
        listed = names[0]
    elif len(names) == 2:
        listed = f"{names[0]} and {names[1]}"
    else:
        listed = ", ".join(names[:-1]) + f", and {names[-1]}"
    return f"In frame: {listed}."


def _measured_jaw(
    pack: Mapping[str, Any],
    shot_id: str,
    origin: float,
    stop: float,
    cast: Mapping[str, dict[str, str] | None] | None = None,
) -> list[str]:
    """Speech windows that were measured. Sheets without fit_s stay as written."""
    lines = []
    for row in pack["captions"]:
        if str(row.get("shot")) != shot_id:
            continue
        fit = row.get("fit_s")
        if not fit or len(fit) != 2:
            continue
        left = max(float(fit[0]), origin) - origin
        right = min(float(fit[1]), stop) - origin
        if right - left < 0.05:
            continue
        role = str(row.get("role"))
        entry = (cast or {}).get(role)
        who = entry["name"] if entry and entry["name"] else _ON_EN.get(role, f"the {role}")
        lines.append(
            f"From {_num(left)} to {_num(right)}, {who}'s lower jaw drops and rises. "
            "Outside that interval that jaw stays closed and does not travel."
        )
    return lines


# place_part on a shot. The key is already English; this only makes it a sentence.
_PLACE_PART = {
    "yard": "This shot stays in the yard.",
    "pool": "This shot stays at the pool.",
    "door": "This shot stays at the doorway.",
    "sofa": "This shot stays on the sofa.",
    "rug": "This shot stays on the rug.",
}


def _cast_line(roles: Sequence[str], cast: Mapping[str, dict[str, str] | None]) -> str:
    """Who is drawn in this range, in English. A role without its own name keeps its label."""
    bits: list[str] = []
    for role in roles:
        if role == "indoor_pair":
            continue
        entry = cast.get(role)
        if entry is None:
            continue
        label = _ON_EN.get(role, role)
        if entry["full"] and entry["name"]:
            bits.append(entry["full"])
        else:
            bits.append(f"{label}: {entry['full'] or 'not named'}")
    if not bits:
        return ""
    return "Cast: " + "; ".join(bits) + "."


def picture_prompt(
    pack: Mapping[str, Any],
    start_s: float,
    end_s: float,
    *,
    hold_after_s: float | None = None,
) -> str:
    """English picture for one range. Spoken lines and the source cast stay out.

    Slots go in as English, and each role is called by that English name inside
    the shots. A jaw the sheet opens is not told to stay wordless.
    ``hold_after_s`` is where the sheet's seconds end inside a longer request.
    """
    slots = pack["slots"]
    cast = _cast(pack)
    names = _label_names(cast)
    place_text = str(slots.get("place") or "").strip()
    place = "not named"
    if place_text and place_text != SLOT:
        try:
            place = slot_english(place_text)[0] or "not named"
        except ValueError:
            place = "not named"
    origin = float(start_s)
    stop = float(end_s)
    shot_no = 0
    seen_roles: list[str] = []
    jaw_moves = False
    shot_lines: list[str] = []
    for shot in pack["shots"]:
        begin = float(shot["start_s"])
        end = float(shot["end_s"])
        if end <= origin + 1e-6 or begin >= stop - 1e-6:
            continue
        left = max(begin, origin) - origin
        camera_text = str(shot.get("camera") or "")
        camera_en = _merge_camera(_covered_phrases(camera_text, _CAMERA_MOTION))
        camera_has_body = any(_covered_phrases(clause, _BODY_MOTION) for clause in _clauses(camera_text))
        if camera_text.strip() and not camera_en and not camera_has_body:
            camera_en = [f"{_STATIC}."]
        jaw = _measured_jaw(pack, str(shot["id"]), origin, stop, cast)
        picture = str(shot.get("picture") or "")
        body_en = _body_lines(picture, camera_text, timed_jaw=bool(jaw), names=names)
        if jaw or any(_JAW_OPENS in _covered_phrases(clause, _BODY_MOTION) for clause in _clauses(picture)):
            jaw_moves = True
        where = _PLACE_PART.get(str(shot.get("place_part") or ""))
        bits: list[str] = []
        for part in [*camera_en, *body_en, *jaw, *([where] if where else [])]:
            if part not in bits:
                bits.append(part)
        if not bits:
            bits = [f"{_STATIC}."]
        shot_no += 1
        motion = " ".join(bits)
        if shot_no == 1:
            line = f"[Shot 1] {motion}"
        else:
            line = f"[Shot {shot_no}] At {_stamp(left)}, the camera cuts. {motion}"
        on_screen = list(shot.get("on_screen") or [])
        frame = _frame_line(on_screen, cast)
        if frame:
            line += " " + frame
        shot_lines.append(line)
        for role in on_screen:
            if role not in seen_roles:
                seen_roles.append(role)
    quiet = "No writing. No music. No logo."
    if not jaw_moves:
        quiet = "No one speaks. " + quiet
    lines = [
        "Vertical 9:16. Live-action. The picture follows the shots below. No title card.",
        f"Place: {place}.",
    ]
    cast_line = _cast_line(seen_roles, cast)
    if cast_line:
        lines.append(cast_line)
    lines.extend(
        [
            "Adults only. Do not resemble a real person or the source account.",
            quiet,
            "",
            *shot_lines,
        ]
    )
    if hold_after_s is not None:
        lines.append(f"After {_num(hold_after_s)} seconds the same frame holds. The mouth stays still.")
    text = "\n".join(lines) + "\n"
    for row in pack["captions"]:
        source = str(row["source_line"])
        if len(source) >= 4 and source in text:
            raise ValueError(f"元のセリフがプロンプトに入った: {row['id']}")
    for shot in pack["shots"]:
        seen = str(shot.get("source_seen") or "")
        if seen and seen in text:
            raise ValueError(f"元の画面がプロンプトに入った: {shot['id']}")
    return (
        "integrated_multimodal_description: "
        + text.strip()
        + "\n\noverall_soundscape: Ambient sound was not measured.\n\nnon_diegetic_music: N/A\n"
    )


def prepare(path: Path | None = None) -> dict[str, Any]:
    """Load the pack. Slots stay empty. Nothing is rendered."""
    pack = load(path)
    return {
        "schema": "affi-repro-prep/v1",
        "source_id": pack["source_id"],
        "duration_s": pack["duration_s"],
        "shots": len(pack["shots"]),
        "captions": len(pack["captions"]),
        "narration": pack["narration"],
        "blocked": blocked(pack),
        "generates_video": False,
        "posts": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="構成シートを出す。動画は焼かない。")
    parser.add_argument("--write", action="store_true", help="同じ内容を md に書く")
    args = parser.parse_args(argv)
    pack = load()
    text = render_markdown(pack)
    if args.write:
        SHEET_PATH.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
