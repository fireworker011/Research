"""吹き出し型の絵は Grok Imagine に作らせる。ここはボットへの指示だけ。"""

from __future__ import annotations

from pathlib import Path


HERO = "30代前半の日本人男性会社員。短めの黒髪、白シャツ、紺のネクタイ、眼鏡なし。"
RIVAL = "主人公とは別の会社員。少し年上で、得意げな顔。紙の文字は読めない落書きにする。"


def attach_imagine(scenes: list[dict]) -> None:
    for scene in scenes:
        if scene.get("role") == "credit" or "bubble" not in scene:
            continue
        scene["imagine"] = imagine_prompt(scene)


def imagine_prompt(scene: dict) -> str:
    bubble = scene.get("bubble") or {}
    side = str(bubble.get("side") or "right")
    kind = str(bubble.get("kind") or "caption")
    who = ""
    if scene.get("characters"):
        who = str(scene["characters"][0].get("who") or "")
    if who == "rival":
        person = RIVAL
        place = "人物は画面の右寄り。左側は背景だけ。"
    elif kind == "speech":
        person = "主人公は毎回同じ顔。" + HERO
        place = "人物は中央の下半分。頭の上は空ける。あとから吹き出しを乗せる。"
    elif side == "right":
        person = "主人公は毎回同じ顔。" + HERO
        place = "人物は左寄り。右側は背景だけ。あとから縦書きの枠を乗せる。"
    else:
        person = "主人公は毎回同じ顔。" + HERO
        place = "人物は右寄り。左側は背景だけ。あとから縦書きの枠を乗せる。"
    text = str(scene.get("text") or "").strip()
    return (
        "16:9の一枚絵。落ち着いたアニメ塗り。"
        "文字、数字、ロゴ、吹き出し、枠、透かしは描かない。"
        f"{person}{place}"
        f"場面: {_staging(text)}"
        f"内容: {text}"
    )


def _staging(text: str) -> str:
    if "5分前" in text or "下書きのまま" in text:
        return "会議直前のオフィス。時計はあるが数字は描かない。机に未送信のメモ。焦った顔。"
    if "書き直" in text:
        return "同じメモを何度も書き直した紙が机に重なる。まだ送っていない。"
    if "整えてから" in text:
        return "送信の直前で指を止め、小さくつぶやいている。"
    if "殴り書き" in text or "隣の席" in text:
        return "雑なメモ1枚で先に返事をもらった、となりの席。"
    if "違った" in text:
        return "自分の席で、何が違ったのかを考えている。"
    if "原因" in text or "粗さ" in text:
        return "整えた原稿の束を見て、遅れの原因に気づいた顔。"
    if "整え" in text:
        return "直しすぎて送れなかった、と悟っている。"
    if "どうする" in text:
        return "こちらを見て、静かに問いかける。"
    return "その内容のオフィスの一場面。"


def write_bot_order(title: str, scenes: list[dict], dest: Path) -> Path:
    """Imagine ボットが Grok Imagine に渡す指示。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "Imagine ボットへ。下の順で Grok Imagine に絵を作らせてください。",
        "投稿しない。Cursor は受け取った絵を枠と声に載せるだけ。",
        "1枚目を主人公の顔の基準にして、続きはその顔を参照する。隣の席のカットだけ別人。",
        "文字は入れない。吹き出しも枠も入れない。ファイル名は指定どおり。16:9。",
        f"題: {title}",
        "",
    ]
    for scene in scenes:
        prompt = scene.get("imagine")
        if not prompt:
            continue
        lines.append(f"## scene_{int(scene['id']):02d}.png")
        lines.append(prompt)
        lines.append("")
    dest.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return dest


def find_plates(images: Path, scenes: list[dict]) -> tuple[dict[int, Path], list[str]]:
    found: dict[int, Path] = {}
    missing: list[str] = []
    for scene in scenes:
        if scene.get("role") == "credit" or "imagine" not in scene:
            continue
        name = f"scene_{int(scene['id']):02d}"
        plate = _one_plate(images, name)
        if plate is None:
            missing.append(name)
        else:
            found[int(scene["id"])] = plate
    return found, missing


def _one_plate(images: Path, name: str) -> Path | None:
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        cand = images / f"{name}{ext}"
        if cand.is_file():
            return cand
    return None
