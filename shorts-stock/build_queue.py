"""Write shorts-stock/IMAGINE-QUEUE.md from the pack files."""

from __future__ import annotations

from pack_meta import STOCK, iter_packs

OUT = STOCK / "IMAGINE-QUEUE.md"


def main() -> None:
    packs = iter_packs()
    shot_count = sum(len(pack["shots"]) for pack in packs)
    lines: list[str] = [
        "# Imagine 待ち行列",
        "",
        "使い順はペット、婚活、美容。各ラインは 2026-10-12 の 01 から、続いて 2026-10-13 の 01 から。",
        "プロンプトは各 `IMAGINE.md` のショット用 text ブロックをそのまま写した。声のブロックはショットではないので入れていない。",
        "",
        f"パック {len(packs)} 本、ショット {shot_count} 本。",
        "",
        "ファイルは下のパスに置く。`finish.sh` がその名前で読む。",
        "アプリの秒数が 6 秒刻みしか無いときは、6 秒で書き出し、同じファイル名のまま置く。`finish.sh` は各ファイルの頭から、ここに書いた秒だけを使う。声の長さに合わせて絵を切り直さない。",
        "ショットの中で音楽とせりふは生成しない。声と BGM は `finish.sh` が後から乗せる。",
        "",
        "## 一覧",
        "",
        "| 順 | ファイル | 長さ | 動作 |",
        "| --- | --- | --- | --- |",
    ]
    for pack in packs:
        for shot in pack["shots"]:
            path = f"shorts-stock/{pack['rel']}/{shot['file']}"
            lines.append(
                f"| {pack['order']}-{shot['index']} | `{path}` | {shot['length_sec']}秒 | {shot['action']} |"
            )
    lines.append("")
    lines.append("## プロンプト")
    lines.append("")
    current_label = None
    for pack in packs:
        if pack["line_label"] != current_label:
            current_label = pack["line_label"]
            lines.append(f"## {current_label}")
            lines.append("")
        lines.append(f"### {pack['order']}. `{pack['rel']}`")
        lines.append("")
        lines.append(f"絵の合計: {pack['picture_sec']}秒。ショット {len(pack['shots'])} 本。")
        lines.append("")
        for shot in pack["shots"]:
            path = f"shorts-stock/{pack['rel']}/{shot['file']}"
            lines.append(f"#### {shot['file']}（{shot['length_sec']}秒、{shot['start_sec']}–{shot['end_sec']}秒）")
            lines.append("")
            lines.append(f"動作: {shot['action']}")
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
