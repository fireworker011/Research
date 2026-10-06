"""Reproduce a reference account's pattern and judge A/B results.

Does not copy source dialogue or characters. Does not generate video or post.
Blank metric cells stay blank. They are not treated as zero.
"""

from __future__ import annotations

import argparse
import csv
import re
import statistics
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "reference-accounts" / "templates"
HYPOTHESES = ROOT / "reference-accounts" / "hypotheses.yaml"
RESULTS = ROOT / "reference-accounts" / "results.csv"
LOOKS = ROOT / "reference-accounts" / "looks.yaml"

_BANNED = (
    "ジュンジュン",
    "ランラン",
    "紫藤",
    "乃やこ",
    "すず丸",
    "the.care.logic",
    "pinonuts",
    "おいもナッツ",
    "そっくり",
    "本人",
    "実在",
    "有名人",
    "未成年",
    "子供",
    "子ども",
    "10代",
    "十代",
    "小学生",
    "中学生",
    "高校生",
    "幼児",
    "赤ちゃん",
    "乳児",
    "少年",
    "少女",
    "child",
    "teen",
    "toddler",
    "infant",
    "minor",
    "baby",
)
_AGE = re.compile(r"(\d+)\s*(?:歳|才)")
_PARTS = {
    "the.care.logic": ("mascot", "place", "speech"),
    "nuts0629": ("animal", "place", "speech"),
    "junjun_ranran": ("animal", "animal2", "person", "place", "speech"),
    "yako.shiawasekon": ("person", "person2", "place", "speech"),
}
_PREFIX = {
    "animal": "animal_",
    "animal2": "animal2_",
    "person": "person_",
    "person2": "person2_",
    "place": "place_",
    "mascot": "mascot_",
}
_KEYS = {
    "animal": ("species", "breed", "coat", "build", "outfit"),
    "animal2": ("species", "breed", "coat", "build", "outfit"),
    "person": ("gender", "age", "hair", "hair_color", "clothes", "build", "makeup"),
    "person2": ("gender", "age", "hair", "hair_color", "clothes", "build", "makeup"),
    "place": ("room", "style", "palette", "light"),
    "mascot": ("subject", "style", "color"),
}
_NAME = {
    "animal": "動物",
    "animal2": "動物2",
    "person": "人物",
    "person2": "人物2",
    "place": "場所",
    "mascot": "キャラ",
    "speech": "口調",
}

REQUIRED = (
    "schema",
    "handle",
    "genre",
    "reproduce",
    "characters",
    "subtitle",
    "audio",
    "hashtags",
    "cta",
    "unknowns",
)


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"YAMLがオブジェクトではない: {path}")
    return data


def templates() -> list[dict[str, Any]]:
    found = []
    for path in sorted(TEMPLATES.glob("*.yaml")):
        item = load_yaml(path)
        validate_template(item)
        found.append(item)
    return found


def template_for(handle: str) -> dict[str, Any]:
    for item in templates():
        if item["handle"] == handle:
            return item
    raise KeyError(handle)


def validate_template(item: Mapping[str, Any]) -> None:
    missing = [key for key in REQUIRED if key not in item]
    if missing:
        raise ValueError(f"{item.get('handle')} に無い欄: {missing}")
    if item["schema"] != "affi-repro-template/v1":
        raise ValueError("schema が違う")
    if not item.get("timeline") and "modes" not in item:
        raise ValueError("timeline が無い")
    if item["handle"] == "nuts0629" and "modes" not in item:
        raise ValueError("nuts0629 は modes が要る")


def _mode_block(item: Mapping[str, Any], mode: str | None) -> dict[str, Any]:
    modes = item.get("modes") or {}
    if not modes:
        return {"timeline": item["timeline"], "subtitle_mode": item["subtitle"], "audio_mode": item["audio"]}
    key = mode or item.get("default_mode")
    if key not in modes:
        raise KeyError(f"mode が無い: {key}")
    block = modes[key]
    return {"timeline": block["timeline"], "subtitle_mode": block.get("subtitle"), "audio_mode": block.get("audio"), "mode": key}


def catalog() -> dict[str, Any]:
    data = load_yaml(LOOKS)
    if data.get("schema") != "affi-look-choices/v1":
        raise ValueError("looks の schema が違う")
    return data


def load_look(path: Path) -> dict[str, Any]:
    data = load_yaml(path)
    if data.get("schema") == "affi-look-choices/v1":
        raise ValueError("これは選択肢の一覧。選んだ結果のYAMLを渡す")
    picked = data["look"] if isinstance(data.get("look"), dict) else data
    return {key: value for key, value in picked.items() if key not in {"schema", "note"}}


def reject_likeness(text: str) -> None:
    raw = str(text or "")
    if not raw.strip():
        return
    folded = raw.casefold()
    for word in _BANNED:
        if word.casefold() in folded:
            raise ValueError(f"実在の人物や元アカウントに似せる指定はできない: {word}")
    widened = raw.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    for match in _AGE.finditer(widened):
        if int(match.group(1)) < 21:
            raise ValueError("人物は成人のみ。21歳未満の指定はできない")


def _field_id(choice_key: str) -> str:
    if choice_key.startswith("animal2_"):
        return "animal_" + choice_key[len("animal2_") :]
    if choice_key.startswith("person2_"):
        return "person_" + choice_key[len("person2_") :]
    return choice_key


def _find_option(field: Mapping[str, Any], choice: str) -> dict[str, Any] | None:
    for opt in field["options"]:
        if opt["id"] == choice or opt["label"] == choice:
            return opt
    return None


def _phrase(cat: Mapping[str, Any], choice_key: str, choices: Mapping[str, Any], custom: Mapping[str, str]) -> tuple[str, str]:
    field = cat["fields"][_field_id(choice_key)]
    choice = str(choices.get(choice_key) or "").strip()
    if not choice:
        raise ValueError(f"{field['label']} が空")
    opt = _find_option(field, choice)
    if opt is None:
        raise ValueError(f"選択肢が無い: {field['label']} / {choice}")
    if opt["id"] == "other":
        text = str(custom.get(choice_key) or "").strip()
        if not text:
            raise ValueError(f"{field['label']} のその他は文章が要る")
        reject_likeness(text)
        return text, text
    return str(opt["ja"]), str(opt["en"])


def normalize_look(look: Mapping[str, Any] | None) -> dict[str, Any]:
    cat = catalog()
    choices = dict(cat["defaults"])
    custom: dict[str, str] = {}
    ref_image = ""
    if look:
        ref_image = str(look.get("ref_image") or "").strip()
        extra = look.get("custom")
        if isinstance(extra, Mapping):
            custom.update({str(key): str(value).strip() for key, value in extra.items()})
        for key, value in look.items():
            if key in {"ref_image", "custom", "schema", "note"}:
                continue
            if str(key).endswith("_text"):
                custom[str(key)[: -len("_text")]] = str(value).strip()
                continue
            choices[str(key)] = value
    known = set(cat["defaults"])
    for key in choices:
        if key not in known:
            raise ValueError(f"見た目の欄が無い: {key}")
    reject_likeness(ref_image)
    for text in custom.values():
        reject_likeness(text)
    for key in choices:
        _phrase(cat, key, choices, custom)
    return {"choices": choices, "custom": custom, "ref_image": ref_image}


def look_block(handle: str, look: Mapping[str, Any] | None = None) -> dict[str, str]:
    cat = catalog()
    spec = normalize_look(look)
    parts = _PARTS.get(handle)
    if not parts:
        raise KeyError(handle)
    ja_parts: list[str] = []
    en_parts: list[str] = []
    for part in parts:
        if part == "speech":
            ja, en = _phrase(cat, "speech", spec["choices"], spec["custom"])
            ja_parts.append(f"口調は{ja}")
            en_parts.append(f"speech style: {en}")
            continue
        bits_ja: list[str] = []
        bits_en: list[str] = []
        for key in _KEYS[part]:
            ja, en = _phrase(cat, _PREFIX[part] + key, spec["choices"], spec["custom"])
            bits_ja.append(ja)
            bits_en.append(en)
        ja_parts.append(f"{_NAME[part]}: " + "、".join(bits_ja))
        en_parts.append(f"{_NAME[part]}: " + ", ".join(bits_en))
    ref = spec["ref_image"] or "なし"
    ja = "。".join(ja_parts) + f"。参照画像: {ref}。人物は成人のみ。実在の人物や元アカウントには似せない。"
    en = ". ".join(en_parts) + f". reference image: {spec['ref_image'] or 'none'}. Adults only. Do not resemble a real person or the source account."
    return {"ja": ja, "en": en, "line": f"{ja} / {en}", "ref_image": spec["ref_image"]}


def sheet(
    item: Mapping[str, Any],
    theme: str,
    lines: Sequence[str] | None = None,
    *,
    mode: str | None = None,
    variables: Mapping[str, str] | None = None,
    look: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """One video plan. Theme and lines replace the content. The pattern stays."""
    block = _mode_block(item, mode)
    locked = look_block(str(item["handle"]), look)
    spoken = list(lines or [])
    scenes = []
    for index, beat in enumerate(block["timeline"]):
        line = spoken[index] if index < len(spoken) and spoken[index].strip() else "台詞は入力"
        scenes.append(
            {
                "id": beat["id"],
                "start_s": beat.get("start_s"),
                "end_s": beat.get("end_s"),
                "imagine": _imagine(beat, theme, line, locked["line"]),
                "look": locked["line"],
                "line": line,
                "subtitle": _subtitle_line(item, block["subtitle_mode"]),
                "edit": f"{beat.get('start_s')}秒から{beat.get('end_s')}秒。{beat.get('camera') or 'カメラは仕様どおり。'}",
            }
        )
    vars_out = {
        "theme": theme.strip() or "テーマは入力",
        "opening": "型の冒頭",
        "cast": "型の人数",
        "caption": "型のキャプション",
        "audio": "型の音",
        "song": "曲は入力",
        "cadence": "投稿頻度は変えない",
        "first_line": "型の最初の一言",
        "duration": "型の尺",
        "speech_style": "型の口調",
        "ending": "型の終わり",
        "title_band": "型の題帯",
        "format": "型の形式",
    }
    if variables:
        vars_out.update({key: value for key, value in variables.items()})
    return {
        "handle": item["handle"],
        "genre": item["genre"],
        "theme": vars_out["theme"],
        "mode": block.get("mode"),
        "variables": vars_out,
        "scenes": scenes,
        "caption": _caption(item, vars_out),
        "hashtags": item["hashtags"],
        "audio": block["audio_mode"],
        "cta": item["cta"],
        "unknowns": item["unknowns"],
        "reproduce": item["reproduce"],
        "look": locked,
    }


def _imagine(beat: Mapping[str, Any], theme: str, line: str, locked: str) -> str:
    return (
        f"縦動画の1カット。テーマは「{theme}」。{beat.get('picture')} "
        f"見た目の固定（全カット同じ）: {locked} "
        f"カメラ: {beat.get('camera') or '仕様にないので不明'}。"
        f"このカットの言葉の役割: {line}。元のアカウントの顔、動物、台詞文は使わない。"
        "画面の文字は、字幕欄で別に焼くもの以外は出さない。"
    )


def _subtitle_line(item: Mapping[str, Any], mode_subtitle: Any) -> str:
    if mode_subtitle in (None, "なし", False):
        sub = item.get("subtitle") or {}
        if isinstance(sub, dict) and sub.get("enabled") is False:
            return "字幕なし"
        if mode_subtitle == "なし":
            return "字幕なし"
    if isinstance(mode_subtitle, str):
        return mode_subtitle
    sub = item.get("subtitle") or {}
    if isinstance(sub, dict) and sub.get("enabled"):
        return f"{sub.get('font')}、{sub.get('edge')}、{sub.get('place')}"
    return "字幕なし"


def _caption(item: Mapping[str, Any], variables: Mapping[str, str]) -> str:
    tags = item["hashtags"]
    if isinstance(tags, dict) and tags.get("fixed"):
        body = " ".join(tags["fixed"])
    elif isinstance(tags, dict) and tags.get("stalled_pattern"):
        body = " ".join(tags["stalled_pattern"])
    else:
        body = str(tags.get("pattern") if isinstance(tags, dict) else tags)
    if variables.get("caption") and variables["caption"] not in {"型のキャプション"}:
        return variables["caption"] + "\n" + body
    return body


def render_markdown(plan: Mapping[str, Any], title: str) -> str:
    lines = [
        f"# {title}",
        "",
        plan["reproduce"],
        f"テーマ: {plan['theme']}",
        "",
        "## 見た目（全カット・全話で同じ）",
        "",
        plan["look"]["ja"],
        "",
        plan["look"]["en"],
        "",
        "A/Bではこの見た目の文を両版で同じにする。",
        "",
        "## シーン",
        "",
    ]
    for scene in plan["scenes"]:
        lines.extend(
            [
                f"### {scene['id']}（{scene['start_s']}〜{scene['end_s']}秒）",
                f"- Grok Imagine: {scene['imagine']}",
                f"- 台詞: {scene['line']}",
                f"- 字幕: {scene['subtitle']}",
                f"- 編集: {scene['edit']}",
                "",
            ]
        )
    lines.extend(
        [
            "## キャプションとハッシュタグ",
            "",
            str(plan["caption"]),
            "",
            "## 音",
            "",
            str(plan["audio"]),
            "",
            "## CTA",
            "",
            str(plan["cta"]),
            "",
            "## 不明のまま",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in plan["unknowns"])
    lines.append("")
    return "\n".join(lines)


def hypotheses() -> list[dict[str, Any]]:
    return list(load_yaml(HYPOTHESES)["items"])


def hypothesis(hid: str) -> dict[str, Any]:
    for item in hypotheses():
        if item["id"] == hid:
            return item
    raise KeyError(hid)


def ab_sheets(
    hid: str,
    theme: str,
    lines: Sequence[str] | None = None,
    look: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    spec = hypothesis(hid)
    base = template_for(spec["handle"])
    left = sheet(base, theme, lines, variables={spec["change_key"]: spec["a_value"]}, look=look)
    right = sheet(base, theme, lines, variables={spec["change_key"]: spec["b_value"]}, look=look)
    left["variant"] = "A"
    right["variant"] = "B"
    left["variant_label"] = spec["a_label"]
    right["variant_label"] = spec["b_label"]
    return left, right


def changed_keys(left: Mapping[str, Any], right: Mapping[str, Any]) -> set[str]:
    keys = set(left["variables"]) | set(right["variables"])
    return {key for key in keys if left["variables"].get(key) != right["variables"].get(key)}


def feasibility() -> list[dict[str, str]]:
    return list(load_yaml(HYPOTHESES)["feasibility"])


def feasibility_sheet(fid: str, look: Mapping[str, Any] | None = None) -> str:
    item = next(row for row in feasibility() if row["id"] == fid)
    if fid == "F1":
        body = template_for("yako.shiawasekon")
        plan = sheet(body, "制作可否", ["こんにちは。今日はここまで。"], look=look)
        title = "F1 日本語の口パク（婚活・yako.shiawasekon。焼くジョブではない）"
    elif fid == "F2":
        body = template_for("junjun_ranran")
        plan = sheet(body, "同じ顔の確認", ["いち", "に"], look=look)
        title = "F2 毎回同じ顔（見守りカメラ・junjun_ranran。焼くジョブではない）"
    elif fid == "F3":
        body = template_for("nuts0629")
        plan = sheet(body, "ダンスの可否", mode="dance", look=look)
        title = "F3 ダンスの動き（ドッグフード・nuts0629。焼くジョブではない）"
    else:
        raise KeyError(fid)
    return render_markdown(plan, title) + f"\n確かめること: {item['ask']}\n"


def _blank(value: str | None) -> bool:
    return value is None or str(value).strip() == ""


def _nums(rows: Sequence[Mapping[str, str]], name: str) -> list[float] | None:
    found = []
    for row in rows:
        raw = row.get(name)
        if _blank(raw):
            return None
        found.append(float(str(raw)))
    return found


def judge(path: Path | None = None) -> list[dict[str, Any]]:
    path = Path(path or RESULTS)
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    out = []
    for spec in hypotheses():
        group = [row for row in rows if row.get("hypothesis_id") == spec["id"]]
        left = [row for row in group if row.get("variant") == "A"]
        right = [row for row in group if row.get("variant") == "B"]
        need = int(spec["min_n_each"])
        if len(left) < need or len(right) < need:
            out.append(
                {
                    "id": spec["id"],
                    "ready": False,
                    "verdict": "本数不足",
                    "detail": f"A {len(left)}本、B {len(right)}本。必要は各{need}本。",
                }
            )
            continue
        notes = []
        blocked = False
        decisions: list[str] = []
        for metric in spec["metrics"]:
            name = metric["name"]
            rule = metric["rule"]
            a_vals = _nums(left, name)
            b_vals = _nums(right, name)
            if a_vals is None or b_vals is None:
                notes.append(f"{name} は未入力")
                if rule != "present":
                    blocked = True
                continue
            a_med = statistics.median(a_vals)
            b_med = statistics.median(b_vals)
            threshold = metric["threshold"]
            if rule == "present":
                notes.append(f"{name} の中央値 A {a_med} / B {b_med}")
            elif rule == "higher_by_points":
                gap = a_med - b_med
                notes.append(f"{name} の差 A-B = {gap}")
                need = 0 if threshold is None else float(threshold)
                if abs(gap) >= need and gap != 0:
                    decisions.append("A" if gap > 0 else "B")
                else:
                    decisions.append("")
            elif rule == "median_ratio":
                if b_med == 0 or a_med == 0:
                    notes.append(f"{name} の中央値に0がある。倍率は出さない。")
                    blocked = True
                else:
                    ratio = max(a_med, b_med) / min(a_med, b_med)
                    side = "A" if a_med >= b_med else "B"
                    notes.append(f"{name} の倍率 {ratio:.2f}（高い方は{side}）")
                    if threshold and ratio >= float(threshold):
                        decisions.append(side)
                    else:
                        decisions.append("")
            else:
                notes.append(f"{name} の規則が不明")
                blocked = True
        if blocked:
            verdict = "未入力"
        elif not decisions or any(item == "" for item in decisions):
            verdict = "基準未満"
        elif len(set(decisions)) == 1:
            verdict = f"{decisions[0]}が基準を満たした"
        else:
            verdict = "指標が分かれた"
        out.append({"id": spec["id"], "ready": True, "verdict": verdict, "detail": "。".join(notes)})
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="参考アカウントの型から制作シートと判定を出す")
    parser.add_argument("cmd", choices=["feasibility", "ab", "judge"])
    parser.add_argument("--id", default="")
    parser.add_argument("--theme", default="テーマは入力")
    parser.add_argument("--results", default=str(RESULTS))
    parser.add_argument("--look", default="")
    args = parser.parse_args(argv)
    picked = load_look(Path(args.look)) if args.look else None
    if args.cmd == "feasibility":
        for item in feasibility():
            print(feasibility_sheet(item["id"], picked))
            print("---")
        return 0
    if args.cmd == "ab":
        left, right = ab_sheets(args.id, args.theme, look=picked)
        print(render_markdown(left, f"{args.id} A {left['variant_label']}"))
        print(render_markdown(right, f"{args.id} B {right['variant_label']}"))
        return 0
    for row in judge(Path(args.results)):
        print(f"{row['id']}: {row['verdict']}。{row['detail']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
