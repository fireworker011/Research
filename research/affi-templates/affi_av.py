"""H3 prompt for one bake clip: template motion, voice, mouth, captions, music.

The prompt follows the FL2VA guide: English picture and camera, dialogue only
inside <d>. Japanese outside that tag is left out so the model does not read
the instructions aloud. This module does not render video and does not post.
It does not add motion, lines, or a song the template does not already state.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

_CJK_RE = re.compile(r"[ぁ-んァ-ン一-龥]")

_RUNNER = Path(__file__).resolve().parents[2] / "h3-runner"
if (_RUNNER / "h3_runner").is_dir():
    sys.path.insert(0, str(_RUNNER))

try:
    from h3_runner.loras import REPAIR_FILENAME, TURBO_FILENAME
except ImportError:
    TURBO_FILENAME = "minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors"
    REPAIR_FILENAME = "Motion_Repair_V2.safetensors"

# Turbo command in h3-runner/README.md uses steps 9 (8 evaluations plus the terminal 0)
# and video shift 6. Repair 0.6 is the notebook's turbo+repair stack, without Combat.
TURBO_SCALE = 1.0
REPAIR_SCALE = 0.6
TURBO_STEPS = 9
TURBO_VIDEO_SHIFT = 6
PLACEHOLDER_LINE = "台詞は入力"
I2VA_HEADER = (
    "For the target video, at 0.00 seconds into the target video, "
    "<Picture 1> (from [Shot 1]) is fully referenced."
)

# English for the template's own picture and camera. Keyed by handle and beat id.
MOTION_EN = {
    ("the.care.logic", "problem"): (
        "A close-up of one character's face showing crying, anger, or worry. No writing.",
        "The camera holds a nearly static shot and pushes in with small amplitude at slow speed.",
    ),
    ("the.care.logic", "action"): (
        "The character handles the material, a hand pats, and a simple diagram appears. The theme changes what is handled.",
        "The camera holds a nearly static shot. A push in with small amplitude at slow speed may be added.",
    ),
    ("the.care.logic", "result"): (
        "The result. The character smiles. There is no closing card.",
        "The camera holds a nearly static shot.",
    ),
    ("nuts0629", "ask"): (
        "A bright room. An adult holds a microphone toward the dog in a wide view.",
        "The camera pulls out, then pushes in with small amplitude, inside one continuous generation.",
    ),
    ("nuts0629", "answer"): (
        "A close view of the same dog. The mouth moves.",
        "The camera pushes in with small amplitude at slow speed.",
    ),
    ("nuts0629", "bite"): (
        "The hat or the food changes. A hand offers it and the dog bites. The contents are supplied separately.",
        "The camera holds a nearly static shot.",
    ),
    ("nuts0629", "dance"): (
        "The same dog, in costume, dances with the whole body. The background is out of focus. The costume is supplied separately.",
        "The camera holds a static shot. There is no cut.",
    ),
    ("nuts0629", "bubbles"): (
        "Two of the same dog stand side by side. They are almost still.",
        "The camera holds a static shot.",
    ),
    ("junjun_ranran", "hook"): (
        "A close view. The picture shows a conflict or something wrong. No title card. The frame is not black.",
        "The camera is at a low angle and pushes in with small amplitude. The movement is small.",
    ),
    ("junjun_ranran", "argument"): (
        "One spoken line is one shot. One room.",
        "The camera pushes in with small amplitude. The framing is over the shoulder.",
    ),
    ("junjun_ranran", "punch"): (
        "The punchline. The attitude changes suddenly. It ends on a smile.",
        "The camera holds a nearly static shot.",
    ),
    ("yako.shiawasekon", "open"): (
        "An adult woman and an adult man walk or face each other. A street or a shop. Night, warm color, shallow focus.",
        "The camera is behind them or at a medium close view. One spoken line is one shot.",
    ),
    ("yako.shiawasekon", "middle"): (
        "The pair moves from missing each other to a place where the relationship changes. One spoken line is one shot.",
        "The camera holds a nearly static shot.",
    ),
    ("yako.shiawasekon", "turn"): (
        "The relationship changes on the last one or two spoken lines. It ends on a gesture such as taking hands.",
        "The camera pushes in with small amplitude at slow speed.",
    ),
}

ROLE_EN = {
    ("the.care.logic", "mascot"): "one anthropomorphic character who carries the emotion",
    ("the.care.logic", "human"): "a human who is not shown in this pattern",
    ("nuts0629", "dog"): "the same dog",
    ("nuts0629", "mic"): "an adult holding a microphone toward the dog",
    ("junjun_ranran", "tsukkomi"): "the retorting cat",
    ("junjun_ranran", "polite"): "the polite cat",
    ("junjun_ranran", "human"): "the owner, who appears briefly at the end and is not the center",
    ("yako.shiawasekon", "woman"): "an adult woman",
    ("yako.shiawasekon", "man"): "an adult man",
}

VOICE_EN = {
    ("the.care.logic", "mascot"): "a higher-pitched voice, estimated in the template, about 200 to 330 Hz",
    ("the.care.logic", "human"): "voice not specified in the template",
    ("nuts0629", "dog"): "a high voice, estimated in the template",
    ("nuts0629", "mic"): "voice not specified in the template",
    ("junjun_ranran", "tsukkomi"): "a low voice, estimated in the template, about 100 to 130 Hz",
    ("junjun_ranran", "polite"): "a calm voice, estimated in the template, about 110 to 130 Hz",
    ("junjun_ranran", "human"): "an adult woman's voice, estimated in the template, about 250 to 330 Hz",
    ("yako.shiawasekon", "woman"): "a calm adult woman's voice, estimated in the template, about 200 to 250 Hz",
    ("yako.shiawasekon", "man"): "a calm adult man's voice, estimated in the template, about 110 to 130 Hz",
}

ON_SCREEN = {
    ("the.care.logic", "problem"): ("mascot",),
    ("the.care.logic", "action"): ("mascot",),
    ("the.care.logic", "result"): ("mascot",),
    ("nuts0629", "ask"): ("dog", "mic"),
    ("nuts0629", "answer"): ("dog",),
    ("nuts0629", "bite"): ("dog",),
    ("nuts0629", "dance"): ("dog",),
    ("nuts0629", "bubbles"): ("dog",),
    ("junjun_ranran", "hook"): ("tsukkomi", "polite"),
    ("junjun_ranran", "argument"): ("tsukkomi", "polite"),
    ("junjun_ranran", "punch"): ("tsukkomi", "polite", "human"),
    ("yako.shiawasekon", "open"): ("woman", "man"),
    ("yako.shiawasekon", "middle"): ("woman", "man"),
    ("yako.shiawasekon", "turn"): ("woman", "man"),
}

# Only when the template names one speaker for that beat.
SPEAKER = {
    ("the.care.logic", "problem"): "mascot",
    ("the.care.logic", "action"): "mascot",
    ("the.care.logic", "result"): "mascot",
    ("nuts0629", "ask"): "mic",
    ("nuts0629", "answer"): "dog",
    ("nuts0629", "bubbles"): "dog",
}


def beat_key(beat_id: str) -> str:
    head, sep, tail = str(beat_id).rpartition("-")
    if sep and tail.isdigit():
        return head
    return str(beat_id)


def _pair(handle: str, beat_id: str) -> tuple[str, str]:
    key = (handle, beat_key(beat_id))
    try:
        return MOTION_EN[key]
    except KeyError as exc:
        raise KeyError(f"型の動作に英文が無い: {handle} {beat_id}") from exc


def _role(handle: str, person_id: str) -> str:
    try:
        return ROLE_EN[(handle, person_id)]
    except KeyError as exc:
        raise KeyError(f"役の英文が無い: {handle} {person_id}") from exc


def _voice(handle: str, person_id: str) -> str:
    try:
        return VOICE_EN[(handle, person_id)]
    except KeyError as exc:
        raise KeyError(f"声の英文が無い: {handle} {person_id}") from exc


def _spoken_look(look_en: str) -> str:
    """Keep the English look. Japanese notes stay on the still so they are not read aloud."""
    if not _CJK_RE.search(look_en):
        return look_en
    cleaned = _CJK_RE.sub("", look_en)
    cleaned = re.sub(r"[ ]{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.:])", r"\1", cleaned).strip()
    return cleaned + " Untranslated look notes stay on the still and are not spoken."


def _style(look_en: str) -> str:
    text = look_en.casefold()
    if "clay" in text:
        return "Claymation"
    if "watercolor" in text:
        return "Watercolor"
    if "folded-paper" in text or "folded paper" in text:
        return "Folded-paper"
    return "Live-action"


def _stamp(seconds: float) -> str:
    ms = int(round(float(seconds) * 1000))
    minutes, rem = divmod(ms, 60_000)
    sec, milli = divmod(rem, 1000)
    return f"{minutes:02d}:{sec:02d}.{milli:03d}"


def _bgm(audio: Any) -> tuple[str, str]:
    if isinstance(audio, Mapping):
        text = str(audio.get("bgm") or "")
    else:
        text = str(audio or "")
    if "曲は無し" in text or "曲なし" in text:
        return "N/A", "型は曲なし。BGMは足さない。"
    if "ピアノ" in text:
        return "Sparse piano notes at a slow tempo.", "ピアノ。曲名はコピーしない。"
    if "曲名は入力" in text or "曲のみ" in text:
        return "N/A", "曲名は入力のまま。元の曲はコピーしない。"
    if "トレンド" in text:
        return "N/A", "音源名は型が不明。元の音はコピーしない。"
    if "BGM" in text:
        return "N/A", "BGMはあると型にある。楽器は不明なので曲は足さない。"
    if "不明" in text:
        return "N/A", "BGMは型が不明。足さない。"
    return "N/A", "BGMは型に曲名が無い。足さない。"


def _soundscape(handle: str, shots: Sequence[Mapping[str, Any]]) -> str:
    bits: list[str] = []
    for shot in shots:
        key = beat_key(str(shot["id"]))
        if key == "bite" and "Mouth movement is visible." not in bits:
            bits.append("Mouth movement is visible. The template does not say whether chewing is audible.")
        if key == "ask" and "A microphone is visible." not in bits:
            bits.append("A microphone is visible.")
    if not bits:
        bits.append("Ambient sound is not specified in the template.")
    return " ".join(bits)


def _speech(handle: str, shot: Mapping[str, Any], speak: bool) -> str:
    if not speak:
        return "The spoken line is not repeated. No new action is added."
    if not shot.get("needs_line"):
        return "No one speaks. Mouths do not form words."
    line = str(shot.get("line") or "").strip()
    if not line or line == PLACEHOLDER_LINE:
        return "The spoken words are not supplied yet, so no line is spoken."
    speaker = SPEAKER.get((handle, beat_key(str(shot["id"]))))
    quoted = f"<d>[Japanese] {line}</d>"
    if speaker is None:
        return (
            f"One on-screen mouth says {quoted} exactly once. "
            "The template does not name which role speaks it. Other mouths stay closed during this line."
        )
    return (
        f"The {_role(handle, speaker)} (S1), {_voice(handle, speaker)}, says: {quoted} "
        "The mouth forms that one line and no other words."
    )


def clip_prompt(
    *,
    handle: str,
    shots: Sequence[Mapping[str, Any]],
    look_en: str,
    request_s: float,
    part_index: int,
    part_count: int,
    audio: Any,
    subject_en: str = "",
    frames: bool = True,
    music: str | None = None,
) -> dict[str, Any]:
    """One H3 prompt. frames keeps the FL2VA picture lines. Without them, this is T2VA.

    ``music`` replaces the template's music line, for an own file mixed after the join.
    """
    if not shots:
        raise ValueError("ショットが無い")
    origin = float(shots[0]["start_s"])
    style = _style(look_en)
    music_line, music_ja = _bgm(audio)
    if music is not None:
        music_line = music
    motion_ja = [
        {"id": str(shot["id"]), "picture": shot.get("picture"), "camera": shot.get("camera")}
        for shot in shots
    ]
    shot_text: list[str] = []
    spoken: list[dict[str, str]] = []
    for index, shot in enumerate(shots):
        picture_en, camera_en = _pair(handle, str(shot["id"]))
        present = ON_SCREEN[(handle, beat_key(str(shot["id"])))]
        who = ", ".join(_role(handle, person_id) for person_id in present)
        voices = "; ".join(f"{_role(handle, person_id)}: {_voice(handle, person_id)}" for person_id in present)
        speak = part_index == 0
        clause = _speech(handle, shot, speak)
        if speak and shot.get("needs_line") and str(shot.get("line") or "").strip() not in {"", PLACEHOLDER_LINE}:
            speaker = SPEAKER.get((handle, beat_key(str(shot["id"]))))
            spoken.append({"id": str(shot["id"]), "speaker": speaker or "", "text": str(shot["line"]).strip()})
        subject = f"Subject: {subject_en}. " if subject_en else ""
        body = (
            f"{style}. {subject}On screen: {who}. Voices on screen: {voices}. "
            f"{picture_en} {camera_en} {clause} "
            f"The locked look stays the same: {_spoken_look(look_en)} "
            "Do not draw writing on the picture."
        )
        if index == 0:
            shot_text.append(f"[Shot 1] {body}")
        else:
            rel = float(shot["start_s"]) - origin
            shot_text.append(f"[Shot {index + 1}] At {_stamp(rel)}, the camera cuts to a new framing. {body}")
    part = ""
    if part_count > 1:
        if part_index == 0:
            part = f" This is part 1 of {part_count} of the same shot. The action starts as written."
        else:
            part = (
                f" This is part {part_index + 1} of {part_count} of the same shot. "
                "The action continues. No new action is added."
            )
    end = f"{float(request_s):.2f}"
    last_shot = len(shots)
    sections = []
    if frames:
        sections.append(
            "How the reference pictures align with the target video — "
            "Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; "
            f"Picture 2 (from Shot {last_shot}) aligns with the {end}-second mark of the target video."
        )
    sections.extend(
        [
            "integrated_multimodal_description: " + " ".join(shot_text) + part,
            "overall_soundscape: " + _soundscape(handle, shots),
            "non_diegetic_music: " + music_line,
        ]
    )
    prompt = "\n\n".join(sections)
    return {
        "prompt": prompt + "\n",
        "motion_ja": motion_ja,
        "spoken": spoken,
        "bgm_prompt": music_line,
        "bgm_summary": music_ja,
    }


def t2v_prompt(text: str) -> str:
    """A text-only prompt. Picture-alignment lines are left out."""
    body = str(text or "").strip()
    if not body:
        raise ValueError("プロンプトが空")
    kept = [
        line
        for line in body.splitlines()
        if not line.strip().startswith("For the target video")
        and not line.strip().startswith("How the reference pictures align")
    ]
    body = "\n".join(kept).strip()
    if "integrated_multimodal_description:" in body:
        return body if body.endswith("\n") else body + "\n"
    return (
        f"integrated_multimodal_description: {body}\n\n"
        "overall_soundscape: Ambient sound is not specified.\n\n"
        "non_diegetic_music: N/A\n"
    )


def i2v_prompt(text: str) -> str:
    """Keep a hand-written I2VA prompt. Add the first-frame line only when it is missing."""
    body = str(text or "").strip()
    if not body:
        raise ValueError("プロンプトが空")
    if body.startswith(I2VA_HEADER):
        return body if body.endswith("\n") else body + "\n"
    if "integrated_multimodal_description:" in body:
        return I2VA_HEADER + "\n\n" + body + ("\n" if body.endswith("\n") else "\n")
    return (
        f"{I2VA_HEADER}\n\n"
        f"integrated_multimodal_description: {body}\n\n"
        "overall_soundscape: Ambient sound is not specified.\n\n"
        "non_diegetic_music: N/A\n"
    )


def lora_dir() -> Path:
    # Colab writes the job before Drive is mounted. Keep the Drive path anyway.
    if Path("/content").is_dir():
        return Path("/content/drive/MyDrive/h3-weights/loras")
    drive = Path("/content/drive/MyDrive/h3-weights")
    if drive.is_dir():
        return drive / "loras"
    return Path("hf-cache") / "loras"


def lora_rows() -> list[dict[str, Any]]:
    return [
        {"file": TURBO_FILENAME, "scale": TURBO_SCALE, "role": "FL2VA の 8step。声を残す"},
        {"file": REPAIR_FILENAME, "scale": REPAIR_SCALE, "role": "動作のつながり"},
    ]


def lora_cli() -> list[str]:
    folder = lora_dir()
    args = ["--steps", str(TURBO_STEPS), "--video-shift", str(TURBO_VIDEO_SHIFT)]
    for row in lora_rows():
        args.extend(["--lora", f"{folder / row['file']}:{row['scale']:.1f}"])
    return args


def _caption_span(cut: Mapping[str, Any], clips: Sequence[Mapping[str, Any]]) -> tuple[Any, Any]:
    """Keep the template clock. A split beat speaks on the first piece only."""
    cut_id = str(cut["id"])
    owners = [
        clip
        for clip in clips
        if any(str(row["id"]) == cut_id for row in clip.get("motion_ja") or [])
    ]
    speaker = next(
        (
            clip
            for clip in owners
            if any(str(row["id"]) == cut_id for row in clip.get("spoken") or [])
        ),
        None,
    )
    if speaker is not None and len(owners) > 1:
        return speaker["start_s"], speaker["end_s"]
    return cut["start_s"], cut["end_s"]


def performance(
    handle: str,
    characters: Sequence[Mapping[str, Any]],
    cuts: Sequence[Mapping[str, Any]],
    clips: Sequence[Mapping[str, Any]],
    audio: Any,
    *,
    burn: bool,
) -> dict[str, Any]:
    voices = [
        {
            "id": str(person["id"]),
            "role": str(person.get("role") or ""),
            "voice": str(person.get("voice") or ""),
            "voice_en": _voice(handle, str(person["id"])),
        }
        for person in characters
    ]
    if not clips:
        coverage = "クリップは空。カットの絵は残している。足りない秒は足さない。"
    else:
        seen = {
            (str(row["id"]), row["picture"], row["camera"])
            for clip in clips
            for row in clip.get("motion_ja") or []
        }
        missing = [
            str(cut["id"])
            for cut in cuts
            if (str(cut["id"]), cut.get("picture"), cut.get("camera")) not in seen
        ]
        if missing:
            raise ValueError("型の動作がプロンプトに無い: " + "、".join(missing))
        coverage = "型に書いてある動作は全部入っている"
    rows = []
    for cut in cuts:
        line = str(cut.get("line") or "")
        spoken = bool(cut.get("needs_line") and line and line != PLACEHOLDER_LINE)
        text = line if spoken else ""
        start_s, end_s = _caption_span(cut, clips)
        rows.append(
            {
                "id": str(cut["id"]),
                "start_s": start_s,
                "end_s": end_s,
                "text": text,
                "burn": bool(burn and text),
            }
        )
    music, music_ja = _bgm(audio)
    return {
        "motion": {
            "template_coverage": coverage,
            "source_video": "元動画の一致率は測っていない",
        },
        "voices": voices,
        "lipsync": {
            "method": "h3-one-line",
            "summary": "せりふがあるカットは、その1文だけを口が言う。同じ文は繰り返さない。",
        },
        "captions": {
            "rows": rows,
            "summary": "声と同じ文。型の位置に焼く。" if burn else "声と同じ文。型は字幕を焼かない。",
        },
        "bgm": {"prompt": music, "summary": music_ja},
        "lora": lora_rows(),
    }
