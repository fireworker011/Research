"""Write shorts-stock/IMAGINE-QUEUE.md from the pack files.

The active list is shots that are not generated yet. 2026-10-12 pet 01–10
are already generated and composited, so they stay out. Order is 婚活,
then 美容, then the remaining pet packs.

2026-10-14b is held. Those shots are written only under 「保留（未開始）」.
Naomi paused the queue: nothing in this file is a request to generate.
"""

from __future__ import annotations

from pack_meta import HELD_DATES, STOCK, iter_packs

OUT = STOCK / "IMAGINE-QUEUE.md"
QUEUE_LINES = ("konkatsu", "beauty", "pet")
EXCLUDED = {("2026-10-12", "pet")}
HELD = set(HELD_DATES)


def save_name(pack: dict, shot: dict) -> str:
    stem = shot["file"].rsplit("/", 1)[-1].removesuffix(".mp4")
    return f"{pack['line']}-{pack['slug']}-{stem}.mp4"


def queue_packs(packs: list[dict], held: bool) -> list[dict]:
    selected: list[dict] = []
    for line_id in QUEUE_LINES:
        group = [
            pack
            for pack in packs
            if pack["line"] == line_id
            and (pack["date"], pack["line"]) not in EXCLUDED
            and ((pack["date"] in HELD) if held else (pack["date"] not in HELD))
        ]
        group.sort(key=lambda pack: (pack["date"], pack["slug"]))
        selected.extend(group)
    return selected


def append_table(lines: list[str], packs: list[dict], prefix: str) -> None:
    lines.append("| 順 | 保存名 | ファイル | 長さ | 動作 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for index, pack in enumerate(packs, start=1):
        for shot in pack["shots"]:
            path = f"shorts-stock/{pack['rel']}/{shot['file']}"
            lines.append(
                f"| {prefix}{index}-{shot['index']} | `{save_name(pack, shot)}` | `{path}` | {shot['length_sec']}秒 | {shot['action']} |"
            )
    lines.append("")


def append_prompts(
    lines: list[str],
    packs: list[dict],
    prefix: str,
    label_heading: str = "##",
    pack_heading: str = "###",
    shot_heading: str = "####",
) -> None:
    current_label = None
    for index, pack in enumerate(packs, start=1):
        if pack["line_label"] != current_label:
            current_label = pack["line_label"]
            lines.append(f"{label_heading} {current_label}")
            lines.append("")
        lines.append(f"{pack_heading} {prefix}{index}. `{pack['rel']}`")
        lines.append("")
        lines.append(f"絵の合計: {pack['picture_sec']}秒。ショット {len(pack['shots'])} 本。")
        lines.append("")
        for shot in pack["shots"]:
            path = f"shorts-stock/{pack['rel']}/{shot['file']}"
            lines.append(
                f"{shot_heading} {shot['file']}（{shot['length_sec']}秒、{shot['start_sec']}–{shot['end_sec']}秒）"
            )
            lines.append("")
            lines.append(f"動作: {shot['action']}")
            lines.append("")
            lines.append(f"保存名: `{save_name(pack, shot)}`")
            lines.append("")
            lines.append(f"ファイル: `{path}`")
            lines.append("")
            lines.append("```text")
            lines.append(shot["prompt"])
            lines.append("```")
            lines.append("")


def main() -> None:
    packs = iter_packs()
    active = queue_packs(packs, held=False)
    held = queue_packs(packs, held=True)
    names = [save_name(pack, shot) for pack in active + held for shot in pack["shots"]]
    if len(names) != len(set(names)):
        raise SystemExit("保存名が重複している")
    shot_count = sum(len(pack["shots"]) for pack in active)
    held_shots = sum(len(pack["shots"]) for pack in held)
    lines: list[str] = [
        "# Imagine 待ち行列",
        "",
        "ナオミチが待ち行列を保留にした。未生成の一覧も、「保留（未開始）」も、Imagine は始めない。生成を頼まない。",
        "",
        "使い順は婚活、美容、ペット。各ラインは日付の古い順、パックは 01 から。",
        "2026-10-12 のペット 01–10 は Imagine 済みで結合済みなので、この待ち行列には入れない。",
        "2026-10-14b は下の「保留（未開始）」だけに置く。上の一覧には入れない。",
        "プロンプトは各 `IMAGINE.md` のショット用 text ブロックをそのまま写した。声のブロックはショットではないので入れていない。",
        "",
        f"未生成のパック {len(active)} 本、ショット {shot_count} 本。保留のまま。今は作らない。",
        "",
        "「ファイル」は `finish.sh` が読むパス。`imagine/shot-01.mp4` から順に置く。",
        "「保存名」は、保留が解けたときにダウンロードする名前。`<line>-<pack>-<shot>.mp4`。pack はフォルダ名、shot は `shot-01` のようにファイルの幹。",
        "アプリの秒数が 6 秒刻みしか無いときは、6 秒で書き出し、同じ保存名のまま置く。`finish.sh` は各ファイルの頭から、ここに書いた秒だけを使う。声の長さに合わせて絵を切り直さない。",
        "ショットの中で音楽とせりふは生成しない。声と BGM は `finish.sh` が後から乗せる。",
        "",
        "## 一覧",
        "",
    ]
    append_table(lines, active, "")
    lines.append("## プロンプト")
    lines.append("")
    append_prompts(lines, active, "")
    lines.append("## 保留（未開始）")
    lines.append("")
    lines.append("2026-10-14b。Imagine は始めない。生成を頼まない。投稿しない。")
    lines.append(f"パック {len(held)} 本、ショット {held_shots} 本。")
    lines.append("")
    append_table(lines, held, "保留-")
    append_prompts(lines, held, "保留-", "###", "####", "#####")
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT} active_packs={len(active)} active_shots={shot_count} held_packs={len(held)} held_shots={held_shots}")


if __name__ == "__main__":
    main()
