"""口語の不満を、テンポ・テロップ・効果音の直しに変える。"""

from __future__ import annotations

import re

from irasutoya_short.constants import MAX_SCENES
from irasutoya_short.textutil import spoken, wrap_telop


def apply_note(project: dict, note: str) -> list[str]:
    """何が気に入らないか、だけを受け取る。戻り値は直した内容。"""
    settings = project["settings"]
    text = note.strip()
    changes: list[str] = []
    if any(word in text for word in ("テンポ悪い", "テンポが悪い", "長い", "だるい", "のろい", "遅い", "間がもた")):
        settings["speed"] = round(float(settings["speed"]) * 1.15, 3)
        settings["hook_speed"] = round(float(settings["hook_speed"]) * 1.12, 3)
        changes.append("テンポを上げた")
    if any(word in text for word in ("早すぎ", "早過ぎ", "せわしない", "テンポが速い", "テンポ速い")):
        settings["speed"] = round(float(settings["speed"]) * 0.88, 3)
        settings["hook_speed"] = round(float(settings["hook_speed"]) * 0.9, 3)
        changes.append("テンポを落とした")
    if any(word in text for word in ("はみ出", "見切れ", "文字が大きい", "文字がでかい")):
        settings["telop_scale"] = round(float(settings["telop_scale"]) * 0.82, 3)
        changes.append("テロップを縮小した")
    if any(word in text for word in ("文字が小さい", "読めない", "テロップが小さい")):
        settings["telop_scale"] = round(min(1.4, float(settings["telop_scale"]) * 1.15), 3)
        changes.append("テロップを大きくした")
    if any(word in text for word in ("うるさい", "SE", "効果音", "せうるさい", "音がでかい")):
        settings["sfx_gain"] = round(float(settings["sfx_gain"]) * 0.5, 3)
        changes.append("効果音を下げた")
    if any(word in text for word in ("声が小さい", "声が聞こえない", "ナレーションが小さい")):
        settings["sfx_gain"] = round(float(settings["sfx_gain"]) * 0.7, 3)
        settings["bgm_gain"] = round(float(settings["bgm_gain"]) * 0.6, 3)
        changes.append("効果音とBGMを下げて声を前に出した")
    if "BGM" in text and "うるさい" in text:
        settings["bgm_gain"] = round(float(settings["bgm_gain"]) * 0.5, 3)
        changes.append("BGMを下げた")
    if any(word in text for word in ("口が動かない", "口パク", "口ぱく")):
        settings["mouth_gain"] = round(min(1.8, float(settings["mouth_gain"]) * 1.35), 3)
        changes.append("口の開きを大きくした")
    if "ナレーション" in text or "地の文" in text:
        before = len(project["scenes"])
        project["scenes"] = split_narration(project["scenes"])
        if len(project["scenes"]) != before:
            changes.append("地の文とセリフを分けた")
    if "揺れ" in text and any(word in text for word in ("やめ", "うるさい", "ひどい", "多い")):
        for scene in project["scenes"]:
            if scene["effect"] in ("shake", "zoom_shake"):
                scene["effect"] = "zoom" if scene["effect"] == "zoom_shake" else "none"
        changes.append("画面の揺れを消した")
    if not changes:
        changes.append("直す箇所が特定できなかった。テンポ、テロップ、効果音、口パクのどれかを言ってください。")
    project.setdefault("notes", []).append({"note": text, "changes": changes})
    return changes


def split_narration(scenes: list[dict]) -> list[dict]:
    """地の文と「セリフ」が同居していたら2シーンに分ける。"""
    out: list[dict] = []
    for scene in scenes:
        match = re.search(r"「([^」]+)」", scene.get("text") or "")
        if match is None or scene["role"] in ("credit", "hook") or scene["speaker"] != "narrator":
            out.append(scene)
            continue
        quote = match.group(1).strip()
        rest = (scene["text"][: match.start()] + scene["text"][match.end() :]).strip(" 、。")
        if rest:
            narration = dict(scene)
            narration["text"] = spoken(rest)
            narration["telop"] = wrap_telop(rest, 12, 2)
            out.append(narration)
        spoken_scene = dict(scene)
        spoken_scene["speaker"] = "rival"
        spoken_scene["text"] = spoken(quote)
        spoken_scene["telop"] = wrap_telop(quote, 12, 2)
        spoken_scene["style_id"] = 11
        spoken_scene["credit"] = "VOICEVOX:玄野武宏"
        out.append(spoken_scene)
    if len(out) > MAX_SCENES:
        out = _merge_down(out, MAX_SCENES)
    for i, scene in enumerate(out, start=1):
        scene["id"] = i
    return out


def _merge_down(scenes: list[dict], limit: int) -> list[dict]:
    scenes = list(scenes)
    while len(scenes) > limit:
        candidates = [i for i, s in enumerate(scenes) if s["role"] == "develop" and i > 0]
        if not candidates:
            break
        index = min(candidates, key=lambda i: len(scenes[i]["text"]))
        prev = scenes[index - 1]
        cur = scenes[index]
        prev["text"] = spoken(prev["text"] + cur["text"])
        prev["telop"] = wrap_telop(prev["text"], 12, 2)
        scenes.pop(index)
    return scenes
