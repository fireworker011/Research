"""Reproduce a reference account's pattern and judge A/B results.

Does not copy source dialogue or characters. Does not generate video or post.
Blank metric cells stay blank. They are not treated as zero.
"""

from __future__ import annotations

import argparse
import csv
import statistics
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "reference-accounts" / "templates"
HYPOTHESES = ROOT / "reference-accounts" / "hypotheses.yaml"
RESULTS = ROOT / "reference-accounts" / "results.csv"

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


def sheet(
    item: Mapping[str, Any],
    theme: str,
    lines: Sequence[str] | None = None,
    *,
    mode: str | None = None,
    variables: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """One video plan. Theme and lines replace the content. The pattern stays."""
    block = _mode_block(item, mode)
    spoken = list(lines or [])
    scenes = []
    for index, beat in enumerate(block["timeline"]):
        line = spoken[index] if index < len(spoken) and spoken[index].strip() else "台詞は入力"
        scenes.append(
            {
                "id": beat["id"],
                "start_s": beat.get("start_s"),
                "end_s": beat.get("end_s"),
                "imagine": _imagine(item, beat, theme, line),
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
    }


def _imagine(item: Mapping[str, Any], beat: Mapping[str, Any], theme: str, line: str) -> str:
    look = "。".join(str(c["look"]) for c in item["characters"])
    return (
        f"縦動画の1カット。テーマは「{theme}」。{beat.get('picture')} "
        f"見た目の固定: {look} カメラ: {beat.get('camera') or '仕様にないので不明'}。"
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


def ab_sheets(hid: str, theme: str, lines: Sequence[str] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    spec = hypothesis(hid)
    base = template_for(spec["handle"])
    left = sheet(base, theme, lines, variables={spec["change_key"]: spec["a_value"]})
    right = sheet(base, theme, lines, variables={spec["change_key"]: spec["b_value"]})
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


def feasibility_sheet(fid: str) -> str:
    item = next(row for row in feasibility() if row["id"] == fid)
    if fid == "F1":
        body = template_for("yako.shiawasekon")
        plan = sheet(body, "制作可否", ["こんにちは。今日はここまで。"])
        title = "F1 日本語の口パク"
    elif fid == "F2":
        body = template_for("junjun_ranran")
        plan = sheet(body, "同じ顔の確認", ["いち", "に"])
        title = "F2 毎回同じ顔"
    elif fid == "F3":
        body = template_for("nuts0629")
        plan = sheet(body, "ダンスの可否", mode="dance")
        title = "F3 ダンスの動き"
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
    args = parser.parse_args(argv)
    if args.cmd == "feasibility":
        for item in feasibility():
            print(feasibility_sheet(item["id"]))
            print("---")
        return 0
    if args.cmd == "ab":
        left, right = ab_sheets(args.id, args.theme)
        print(render_markdown(left, f"{args.id} A {left['variant_label']}"))
        print(render_markdown(right, f"{args.id} B {right['variant_label']}"))
        return 0
    for row in judge(Path(args.results)):
        print(f"{row['id']}: {row['verdict']}。{row['detail']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
