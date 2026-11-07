"""One Ref2VA plan for the measured sword clip, with Sakura and a Japanese garden.

The third listed URL is the same Motion Repair file as the first. Combat is the
second file. This module does not download weights and does not queue Comfy.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from h3.live_remake import FPS, MODEL_FILE, STEPS, align_frames, canvas_for

# ffprobe of Drive file 1G61IM9tj4eecFi_lDntB1ux_ny0yhle8: 244 frames, 24fps, 1280x714.
SOURCE_FRAMES = 244
SOURCE_WIDTH = 1280
SOURCE_HEIGHT = 714
# The pasted prompt marks a 15s film. The file is shorter, so the marks are scaled.
SCRIPT_END_S = 15.0
SCRIPT_MARKS_S = (0.0, 1.0, 4.0, 7.0, 10.0, 12.0)

STILL_DIR = "/content/drive/MyDrive/動画倉庫/ネタBOX"
# The five attached stills, in reference order. Picture 5 keeps the costume only.
PICTURES = (
    {"label": "<Picture 1>", "role": "face", "file": "sakura-01-face.jpg"},
    {"label": "<Picture 2>", "role": "front", "file": "sakura-02-front.jpg"},
    {"label": "<Picture 3>", "role": "back", "file": "sakura-03-back.jpg"},
    {"label": "<Picture 4>", "role": "sword", "file": "sakura-04-sword.jpg"},
    {"label": "<Picture 5>", "role": "night", "file": "sakura-05-night.jpg"},
)
VIDEO = "/content/drive/MyDrive/動画倉庫/ネタBOX/QT0eqhCA1_tQ2Y-FcRGv-_mF7FksnCdXu7K8HSoIJ4s.mp4"
LORA_DIR = "/content/drive/MyDrive/minimax-h3-comfyui/models/loras"

# Strengths from colab/h3_sfw.py. Combat is 0.7 when it shares the sampler with action.
ACTION_FILE = "Motion_Repair_V2.safetensors"
ACTION_STRENGTH = 0.6
COMBAT_FILE = "H3_Combat_V2.safetensors"
COMBAT_STRENGTH = 0.7
TRIGGER = "prfight2, prfin1"


def measured_seconds() -> float:
    return SOURCE_FRAMES / FPS


def scaled_marks() -> tuple[float, ...]:
    """Pasted shot marks, scaled onto the measured frame count."""
    end = measured_seconds()
    return tuple(round(mark * end / SCRIPT_END_S, 3) for mark in SCRIPT_MARKS_S)


def lora_rows(present: Sequence[str] | None = None) -> list[dict[str, object]]:
    """The two distinct weights. A duplicated URL is not a third LoRA."""
    names = None if present is None else set(present)
    rows = [
        {"key": "action", "file": ACTION_FILE, "strength": ACTION_STRENGTH},
        {"key": "combat", "file": COMBAT_FILE, "strength": COMBAT_STRENGTH},
    ]
    for row in rows:
        row["present"] = None if names is None else row["file"] in names
    return rows


def prompt_text() -> str:
    """Ref2VA sections. Identity stays on the still. The sword and timing stay on the video."""
    marks = scaled_marks()
    end = round(measured_seconds(), 3)
    shots = (
        (
            marks[0],
            "Extreme low angle on the stone path. Within the first moment she bursts from a still stance into a fast dash. "
            "The path cracks under her feet and debris kicks outward. Hair and clothes from <Picture 1>, <Picture 2>, and <Picture 3> stream backward. "
            "She draws the tachi from <Picture 4>. The camera closes on the blade and a crimson edge lights the steel.",
        ),
        (
            marks[1],
            "The camera tracks. Close strikes pass her with no pause, then the pace doubles. She stays low and leaves afterimages. "
            "Three tachi cuts follow: a horizontal slash, an upward thrust, and a spinning cut. "
            "The blade weaves a net of red light and throws sparks.",
        ),
        (
            marks[2],
            "Wide low angle. She leaves the ground in one motion. The tachi cuts a scarlet arc and releases a cone of red sword light downward. "
            "The impact hits the stone garden. The camera shakes. The weapon remains the tachi.",
        ),
        (
            marks[3],
            "The camera circles her once, then comes close to the face in <Picture 1>. "
            "She turns, changes direction in the air, and thrusts. The tachi stays the weapon. "
            "Red sword-light afterimages cross the temple garden.",
        ),
        (
            marks[4],
            "A vertical fall stops on the impact. She blocks a heavy strike and answers with one tachi thrust. "
            "She breaks through falling wood and stone, then swings one crescent of red sword light across the garden.",
        ),
        (
            marks[5],
            f"From here to {end:.3f} seconds she lands in the garden. Dust and cherry petals move. "
            "The tachi hangs at her side with the crimson edge still lit. She looks toward the temple gate. "
            "Lanterns light, and a large shadow begins to move beyond the gate. She raises the tachi. "
            "Hair and clothes from <Picture 1>, <Picture 2>, and <Picture 3> move in the wind.",
        ),
    )
    body = " ".join(f"[Shot {index}] At {mark:.3f} seconds, {text}" for index, (mark, text) in enumerate(shots, start=1))
    definitions = "\n".join(
        [
            "<Picture 1> locks the face and hair of <Subject 1>.",
            "<Picture 2> locks the costume from the front.",
            "<Picture 3> locks the costume from behind.",
            "<Picture 4> locks the tachi and the Japanese temple.",
            "<Picture 5> is the same woman and the same costume. Its cosmic night sky is not the place.",
            f"<Video 1> is the source from 0.000 to {end:.3f} seconds. It supplies timing, camera, and the tachi motion.",
            "The figure, the white robe, the dark battlefield, and any burned-in writing in <Video 1> are not kept.",
            "<Subject 1> is the woman in <Picture 1> through <Picture 5>. Her weapon remains the tachi in <Picture 4>. Sword timing follows <Video 1>.",
        ]
    )
    retention = "\n".join(
        [
            "<Picture 1> (face and hair): fully_preserved - the face and hair stay with <Picture 1>.",
            "<Picture 2> (costume, front): fully_preserved - the clothes from the front stay with <Picture 2>.",
            "<Picture 3> (costume, back): fully_preserved - the clothes from behind stay with <Picture 3>.",
            "<Picture 4> (tachi and temple): fully_preserved - the sword and the Japanese temple stay with <Picture 4>.",
            "<Picture 5> (same costume): partially_preserved - the woman and clothes stay; the cosmic night sky does not.",
            "<Video 1> (timing, camera, and tachi): partially_preserved - timing, camera, and sword motion stay; appearance and the dark battlefield do not.",
        ]
    )
    detail = " ".join(
        [
            TRIGGER + ".",
            "No on-screen text, subtitles, logos, or watermarks.",
            "The place is the Japanese temple and garden from <Picture 2>, <Picture 3>, and <Picture 4>. The cosmic sky in <Picture 5> is not used.",
            "The weapon is a tachi in every shot.",
            body,
        ]
    )
    return "\n\n".join(
        [
            "subject_definitions:\n" + definitions,
            "summary:\n[reference generation] The measured span of <Video 1> is performed by the woman in <Picture 1> through <Picture 5> "
            "at the Japanese temple. The weapon stays the tachi in <Picture 4>. No shot is added. No dialogue.",
            "retention_analysis:\n" + retention,
            "detailed_description:\n" + detail,
            "overall_soundscape:\nSteel draws and clashes, red sword-light tearing air, and low impacts on the stone path. No music is added.",
            "non_diegetic_music:\nN/A",
        ]
    ) + "\n"


def build_plan(present: Sequence[str] | None = None) -> dict[str, object]:
    """The clip plan. ``present`` is the weight file names already in the LoRA folder."""
    width, height = canvas_for(SOURCE_WIDTH, SOURCE_HEIGHT)
    rows = lora_rows(present)
    missing = [str(row["file"]) for row in rows if row["present"] is False]
    return {
        "job": "sakura_clip",
        "task": "ref2va",
        "model_file": MODEL_FILE,
        "steps": STEPS,
        "width": width,
        "height": height,
        "fps": FPS,
        "source_frames": SOURCE_FRAMES,
        "request_frames": align_frames(SOURCE_FRAMES),
        "pictures": [
            {"label": item["label"], "role": item["role"], "path": f"{STILL_DIR}/{item['file']}"}
            for item in PICTURES
        ],
        "video": VIDEO,
        "lora_dir": LORA_DIR,
        "loras": rows,
        "missing": missing,
        "trigger": TRIGGER,
        "prompt": prompt_text(),
        "generate": False,
        "publish": False,
        "queue": False,
    }


def render(plan: Mapping[str, object]) -> str:
    """Japanese card plus the prompt. Generation stays off."""
    lines = [
        "機能: 参照動画の刀の動きを、さくらの静止画と和風の庭でやり直す",
        "状態: " + ("blocked" if plan["missing"] else "ready"),
        f"動画: {plan['video']}",
        "静止画:",
        *[f"- {item['label']} {item['role']} {item['path']}" for item in plan["pictures"]],
        f"尺: {plan['source_frames']} フレーム、要求 {plan['request_frames']} フレーム、{plan['width']}x{plan['height']}",
        f"モデル: {plan['model_file']} steps {plan['steps']}",
        "LoRA は2枚。3つ目の URL は1つ目と同じ Motion Repair。",
    ]
    for row in plan["loras"]:
        if row["present"] is False:
            state = "Drive に無い"
        elif row["present"] is True:
            state = "Drive にある"
        else:
            state = "未確認"
        lines.append(f"- {row['file']} 強さ {row['strength']} ({state})")
    for name in plan["missing"]:
        lines.append(f"止まり: {plan['lora_dir']}/{name} が無い。落とさない。")
    lines.append(f"トリガー: {plan['trigger']}")
    lines.append(str(plan["prompt"]).rstrip())
    lines.append("生成: しない")
    return "\n".join(lines) + "\n"
