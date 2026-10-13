"""Write shorts-stock/IMAGINE-QUEUE.md from the pack files.

The queue is the shots that are not generated yet. 2026-10-12 pet 01–10
are already generated and composited, so they stay out. Order is 婚活,
then 美容, then the remaining pet packs. Both unfinished lines come first.
"""

from __future__ import annotations

from pack_meta import STOCK, iter_packs

OUT = STOCK / "IMAGINE-QUEUE.md"
QUEUE_LINES = ("konkatsu", "beauty", "pet")
EXCLUDED = {("2026-10-12", "pet")}


def save_name(pack: dict, shot: dict) -> str:
    stem = shot["file"].rsplit("/", 1)[-1].removesuffix(".mp4")
    return f"{pack['line']}-{pack['slug']}-{stem}.mp4"


def queue_packs(packs: list[dict]) -> list[dict]:
    selected: list[dict] = []
    for line_id in QUEUE_LINES:
        group = [
            pack
            for pack in packs
            if pack["line"] == line_id and (pack["date"], pack["line"]) not in EXCLUDED
        ]
        group.sort(key=lambda pack: (pack["date"], pack["slug"]))
        selected.extend(group)
    names = [save_name(pack, shot) for pack in selected for shot in pack["shots"]]
    if len(names) != len(set(names)):
        raise SystemExit("保存名が重複している")
    return selected


def main() -> None:
    packs = queue_packs(iter_packs())
    shot_count = sum(len(pack["shots"]) for pack in packs)
    lines: list[str] = [
        "# Imagine 待ち行列",
        "",
        "使い順は婚活、美容、ペット。各ラインは日付の古い順、パックは 01 から。",
        "2026-10-12 のペット 01–10 は Imagine 済みで結合済みなので、この待ち行列には入れない。",
        "プロンプトは各 `IMAGINE.md` のショット用 text ブロックをそのまま写した。声のブロックはショットではないので入れていない。",
        "",
        f"未生成のパック {len(packs)} 本、ショット {shot_count} 本。",
        "",
        "「ファイル」は `finish.sh` が読むパス。`imagine/shot-01.mp4` から順に置く。",
        "「保存名」は Grok Build がダウンロードして Drive に上げる名前。`<line>-<pack>-<shot>.mp4`。pack はフォルダ名、shot は `shot-01` のようにファイルの幹。",
        "アプリの秒数が 6 秒刻みしか無いときは、6 秒で書き出し、同じ保存名のまま置く。`finish.sh` は各ファイルの頭から、ここに書いた秒だけを使う。声の長さに合わせて絵を切り直さない。",
        "ショットの中で音楽とせりふは生成しない。声と BGM は `finish.sh` が後から乗せる。",
        "",
        "## 一覧",
        "",
        "| 順 | 保存名 | ファイル | 長さ | 動作 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for index, pack in enumerate(packs, start=1):
        for shot in pack["shots"]:
            path = f"shorts-stock/{pack['rel']}/{shot['file']}"
            lines.append(
                f"| {index}-{shot['index']} | `{save_name(pack, shot)}` | `{path}` | {shot['length_sec']}秒 | {shot['action']} |"
            )
    lines.append("")
    lines.append("## プロンプト")
    lines.append("")
    current_label = None
    for index, pack in enumerate(packs, start=1):
        if pack["line_label"] != current_label:
            current_label = pack["line_label"]
            lines.append(f"## {current_label}")
            lines.append("")
        lines.append(f"### {index}. `{pack['rel']}`")
        lines.append("")
        lines.append(f"絵の合計: {pack['picture_sec']}秒。ショット {len(pack['shots'])} 本。")
        lines.append("")
        for shot in pack["shots"]:
            path = f"shorts-stock/{pack['rel']}/{shot['file']}"
            lines.append(
                f"#### {shot['file']}（{shot['length_sec']}秒、{shot['start_sec']}–{shot['end_sec']}秒）"
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
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT} packs={len(packs)} shots={shot_count}")


if __name__ == "__main__":
    main()
