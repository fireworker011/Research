"""Write an H3 bake job from a genre table or a reference cut sheet.

Seconds, cuts, and subtitles stay on the template. Motion, voice, mouth,
captions, and music come from that same template. This module does not
render an mp4 and does not post. Spoken lines that are still the placeholder
stay missing. They are not filled in here.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import affi_av
import affi_genre_templates as genre
import affi_reference as ref
import affi_speech

_RUNNER = Path(__file__).resolve().parents[2] / "h3-runner"
if (_RUNNER / "h3_runner").is_dir():
    sys.path.insert(0, str(_RUNNER))

try:
    from h3_runner.official import (
        MAX_DURATION_S,
        MIN_DURATION_S,
        VIDEO_FLOW_SHIFT,
        DEFAULT_STEPS,
        diffusers_accepts,
        frames_for_seconds,
    )
    from h3_runner.weights import missing_folders
except ImportError:
    # The reference Colab downloads this folder without h3-runner.
    # These match h3_runner/official.py: fps 24, 17*n+5, aligned duration in [5, 15].
    MIN_DURATION_S = 5.0
    MAX_DURATION_S = 15.0
    VIDEO_FLOW_SHIFT = 12.0
    DEFAULT_STEPS = 50
    missing_folders = None

    def frames_for_seconds(duration_s: float) -> int:
        return int(round(float(duration_s) * 24))

    def _align_num_frames(num_frames: int) -> int:
        frames = int(num_frames)
        while frames % 17 != 5:
            frames += 1
        return frames

    def diffusers_accepts(num_frames: int) -> bool:
        aligned = _align_num_frames(num_frames) / 24
        return MIN_DURATION_S <= aligned <= MAX_DURATION_S


SCHEMA = "affi-bake-job/v1"
PLACEHOLDER_LINE = "台詞は入力"
PLACEHOLDER_THEME = "テーマは入力"

# Same map as affi_genre_templates.REFERENCE_HANDLES.
# Kept here so the reference Colab does not have to download the genre module.
GENRE_HANDLES = {
    "美容スキンケア": "the.care.logic",
    "ドッグフード": "nuts0629",
    "見守りカメラ": "junjun_ranran",
    "婚活": "yako.shiawasekon",
}

# Colab のドロップダウンに出す文。話が先、ハンドルは後ろ。
ACCOUNT_CHOICES = (
    ("美容：材料のキャラ（the.care.logic）", "the.care.logic"),
    ("ドッグフード：犬（nuts0629）", "nuts0629"),
    ("見守り：猫2匹の言い合い（junjun_ranran）", "junjun_ranran"),
    ("婚活：男女の会話（yako.shiawasekon）", "yako.shiawasekon"),
)
# 型の文。新しい台詞は足さない。秒数はテンプレのまま。
STORIES = {
    "the.care.logic": "材料のキャラが1体で悩み、対処して、笑顔で終わる。30秒を10秒ずつ3つ。",
    "nuts0629": "同じ犬。インタビューは人がマイクを向ける8秒。咀嚼は8秒を4回。ダンスは全身で10秒。会話は吹き出し。",
    "junjun_ranran": "猫が2匹で言い合い、最後に人が少し出る。45秒。見守りカメラの映像ではない。",
    "yako.shiawasekon": "成人の男女が会話して、最後に関係が変わる。60秒。",
}
FEASIBILITY_FOR = {
    "nuts0629": "F3",
    "junjun_ranran": "F2",
    "yako.shiawasekon": "F1",
}
DOG_PATTERNS = (
    ("インタビュー（既定）", "interview"),
    ("咀嚼", "asmr"),
    ("ダンス", "dance"),
    ("会話", "talk"),
)
_MODE_JA = {mode: label.split("（")[0] for label, mode in DOG_PATTERNS}
FILL_CHOICES = (
    ("テンプレ", "template"),
    ("オマージュ", "homage"),
    ("元の型のまま", "source"),
)
TASK_CHOICES = (
    ("表を見る", "table"),
    ("話でジョブを書く", "job"),
    ("自分の文で1本", "i2v"),
    ("元動画を再現", "repro"),
)
NOTEBOOK_URL = (
    "https://colab.research.google.com/github/fireworker011/Research/"
    "blob/cursor/affi-template-bake-44d6/research/affi-templates/affi.ipynb"
)
# Short fills for the form. The source account's face, lines, and song titles stay out.
_FILL_NOTE = "型の絵とカメラ。元の顔、元の台詞、曲名は入れない。"
_FILLS: dict[tuple[str, str | None], dict[str, dict[str, Any]]] = {
    ("the.care.logic", None): {
        "template": {
            "theme": "夕方の乾燥",
            "subject_en": "Evening dryness. The character worries, handles the tea leaves, then smiles.",
            "lines": ("乾燥が気になる", "茶葉をなでる", "おちついた"),
        },
        "homage": {
            "theme": "1体の悩み",
            "subject_en": "One character only. A close view of the worry, then the remedy, then a smile. No title card.",
            "lines": ("これはいや", "こうする", "よくなった"),
        },
        "source": {
            "theme": "悩み、対処、笑顔",
            "subject_en": "A close view of one worried character, then the character handles the material, then the character smiles.",
            "lines": ("困った", "手当てする", "笑った"),
        },
    },
    ("nuts0629", "interview"): {
        "template": {
            "theme": "ごはんの時間",
            "subject_en": "Mealtime. An adult asks the dog which food, and the dog answers.",
            "lines": ("ごはんはどれ", "これにする"),
        },
        "homage": {
            "theme": "同じ子の食いしん坊",
            "subject_en": "The same dog wants food. The bag and the product name stay out of this moment.",
            "lines": ("まだ", "うん"),
        },
        "source": {
            "theme": "質問と返事",
            "subject_en": "One continuous shot. An adult holds a microphone toward the dog, then the dog answers in close view.",
            "lines": ("今日の気分は", "げんき"),
        },
    },
    ("nuts0629", "asmr"): {
        "template": {
            "theme": "パンをかじる",
            "subject_en": "A hand offers plain bread and the dog bites.",
            "lines": (),
        },
        "homage": {
            "theme": "同じ子がかじる",
            "subject_en": "The same dog bites. The product bag stays out of frame.",
            "lines": (),
        },
        "source": {
            "theme": "手から食べ物",
            "subject_en": "The food changes. A hand offers it and the dog bites.",
            "lines": (),
        },
    },
    ("nuts0629", "dance"): {
        "template": {
            "theme": "全身のダンス",
            "subject_en": "The same dog dances with the whole body in a plain costume. No song title.",
            "lines": (),
        },
        "homage": {
            "theme": "同じ子のダンス",
            "subject_en": "The same costumed dog dances in one shot. The song is not copied.",
            "lines": (),
        },
        "source": {
            "theme": "固定カメラのダンス",
            "subject_en": "One continuous whole-body dance. The camera is fixed and the background is out of focus.",
            "lines": (),
        },
    },
    ("nuts0629", "talk"): {
        "template": {
            "theme": "短い掛け合い",
            "subject_en": "Two of the same dog stand side by side and trade one short line.",
            "lines": ("どっちが先",),
        },
        "homage": {
            "theme": "同じ子が2匹",
            "subject_en": "The same dog twice, almost still, with one short exchange. The product stays out.",
            "lines": ("まだ食べる",),
        },
        "source": {
            "theme": "並んだ2匹",
            "subject_en": "Two of the same dog stand side by side and stay almost still.",
            "lines": ("となりにいる",),
        },
    },
    ("junjun_ranran", None): {
        "template": {
            "theme": "部屋の言い合い",
            "subject_en": "Two cats argue in one room, then the mood ends on a smile.",
            "lines": ("それはちがう", "そうですか", "まあいいか"),
        },
        "homage": {
            "theme": "小さな不一致",
            "subject_en": "A small mismatch between the two cats. The owner is not the center.",
            "lines": ("またそれ", "すみません", "よし"),
        },
        "source": {
            "theme": "寄りからオチ",
            "subject_en": "A close view of a conflict, one spoken line per shot, ending on a smile.",
            "lines": ("なんで", "だって", "笑った"),
        },
    },
    ("yako.shiawasekon", None): {
        "template": {
            "theme": "カフェで会う",
            "subject_en": "An adult woman and an adult man talk in a cafe.",
            "lines": ("ここで会うね", "ずれてたね", "手をつなごう"),
        },
        "homage": {
            "theme": "関係が変わる",
            "subject_en": "The pair talks, and the relationship changes on the last line.",
            "lines": ("元気", "最近どう", "一緒に帰ろう"),
        },
        "source": {
            "theme": "会話だけ",
            "subject_en": "Adults talking with no narration. The last gesture changes the relationship.",
            "lines": ("今夜はここ", "わかった", "行こう"),
        },
    },
}


def resolve_fill(label: str) -> str:
    """Map the content menu to template, homage, or source."""
    fills = {text: fill for text, fill in FILL_CHOICES}
    fills.update({fill: fill for _text, fill in FILL_CHOICES})
    found = fills.get(label)
    if found is None:
        raise KeyError(f"中身が無い: {label}")
    return found


def pack_for(handle: str, mode: str | None, fill: str) -> dict[str, Any]:
    key_mode = mode if handle == "nuts0629" else None
    if handle == "nuts0629" and key_mode is None:
        key_mode = "interview"
    try:
        pack = _FILLS[(handle, key_mode)][fill]
    except KeyError as exc:
        raise KeyError(f"中身が無い: {handle} {key_mode} {fill}") from exc
    return {
        "id": fill,
        "label": next(text for text, key in FILL_CHOICES if key == fill),
        "theme": pack["theme"],
        "subject_en": pack["subject_en"],
        "lines": tuple(pack["lines"]),
        "note": _FILL_NOTE,
    }


def resolve_task(label: str) -> str:
    """Map the one menu to table, job, i2v, or repro."""
    tasks = {text: task for text, task in TASK_CHOICES}
    tasks.update({task: task for _text, task in TASK_CHOICES})
    found = tasks.get(label)
    if found is None:
        raise KeyError(f"やることが無い: {label}")
    return found


def look_is_for(handle: str, look: Mapping[str, Any] | None) -> bool:
    """True when this look dict was built for this story."""
    if not look:
        return False
    keys = set(look)
    if handle == "the.care.logic":
        return "mascot_subject" in keys
    if handle == "nuts0629":
        return "animal_species" in keys and "animal2_species" not in keys
    if handle == "junjun_ranran":
        return "animal2_species" in keys
    if handle == "yako.shiawasekon":
        return "person2_gender" in keys and "animal_species" not in keys
    return False


def next_step(task: str) -> str:
    """The one cell to run after the choice form."""
    kind = resolve_task(task)
    if kind == "table":
        return "次は「実行」だけ押してください。4ジャンルの表が出ます。動画にはなりません。"
    if kind == "job":
        return (
            "次は「実行」を押してください。"
            "見た目を変えるときだけ、その前に、話の名前が同じ見た目のセルを1つ押してください。"
            "変えないときは初期値です。"
            "ready と出たら、一番下の「焼く」です。"
        )
    if kind == "i2v":
        return "次は「実行」を押してください。ready と出たら、一番下の「焼く」です。"
    if kind == "repro":
        return (
            "次は「実行」を押してください。"
            "ready と出たら、一番下の「焼く」です。"
            "元動画は 5〜15 秒の範囲に分かれます。"
            "最初の1本だけがオンのときは、その最初の範囲だけです。"
        )
    raise RuntimeError(f"やることが無い: {kind}")


def _comment_is_header(body: str) -> bool:
    return body.startswith(("status=", "mp4 ", "I2V", "T2V", "Ref2VA"))


def commands_to_run(path: Path, *, first_only: bool) -> tuple[list[str], str]:
    """Commands from a written job. A message means do not start them."""
    if not path.is_file():
        return [], "先に「実行」を押してください。"
    text = path.read_text(encoding="utf-8")
    if "status=blocked" in text:
        reasons = [
            line[2:].strip()
            for line in text.splitlines()
            if line.startswith("# ") and not _comment_is_header(line[2:].strip())
        ]
        detail = "\n".join(f"- {reason}" for reason in reasons if reason)
        return [], "止まっているので焼かない。\n" + detail
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
    if not lines:
        return [], "焼くコマンドが無い。"
    if first_only:
        rest = len(lines) - 1
        note = "最初の1本だけ焼きます。" if rest == 0 else f"最初の1本だけ焼きます。残りは {rest} 本です。"
        return lines[:1], note
    return lines, f"{len(lines)} 本焼きます。"


DRIVE_BAKE = Path("/content/drive/MyDrive/affi-bake")


def run_logged(argv: list[str], cwd: Path) -> int:
    """Run a command and print its output. Colab hides a child process's own output."""
    proc = subprocess.Popen(
        argv,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    if proc.stdout is None:
        return proc.wait()
    for line in proc.stdout:
        print(line, end="", flush=True)
    return proc.wait()


def publish_job_dir(local_dir: Path, *, drive_root: Path | None = None) -> Path:
    """Copy a finished job, including mp4 files, onto the mounted Drive."""
    local_dir = Path(local_dir)
    root = Path(drive_root) if drive_root is not None else DRIVE_BAKE
    parts = local_dir.parts
    if "affi-bake" in parts:
        tail = parts[parts.index("affi-bake") + 1 :]
        dest = root.joinpath(*tail) if tail else root / local_dir.name
    else:
        dest = root / local_dir.name
    copied = False
    for path in local_dir.rglob("*"):
        if not path.is_file():
            continue
        target = dest / path.relative_to(local_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied = True
    if not copied:
        dest.mkdir(parents=True, exist_ok=True)
    return dest


def commands_file(
    task: str,
    *,
    handle: str | None = None,
    mode: str | None = None,
    out_dir: str | Path | None = None,
) -> Path | None:
    """Path of commands.txt for the choice that 「実行」 just wrote."""
    kind = resolve_task(task)
    root = Path(out_dir) if out_dir is not None else _bake_root()
    if kind == "table":
        return None
    if kind == "i2v":
        return root / "i2v" / "commands.txt"
    if kind == "repro":
        return root / "repro" / "commands.txt"
    if kind == "job":
        if not handle:
            return None
        folder = handle if not mode else f"{handle}-{mode}"
        return root / folder / "commands.txt"
    raise RuntimeError(f"やることが無い: {kind}")


def missing_weight_files(cache: str | Path, task: str = "") -> list[str]:
    """Files the bake needs before it starts. A source-video job uses transformer_ref and no FL2V LoRA."""
    root = Path(cache)
    kind = ""
    if task:
        try:
            kind = resolve_task(task)
        except KeyError:
            kind = ""
    if kind == "repro":
        local = root / "MiniMax-H3"
        if missing_folders is not None:
            return [str(local / name) for name in missing_folders(local, ["ref2va"])]
        missing = []
        marker = local / "modular_model_index.json"
        if not marker.is_file():
            missing.append(str(marker))
        if not (local / "transformer_ref").is_dir():
            missing.append(str(local / "transformer_ref"))
        return missing
    missing = []
    marker = root / "MiniMax-H3" / "modular_model_index.json"
    if not marker.is_file():
        missing.append(str(marker))
    loras = root / "loras"
    for filename in (affi_av.TURBO_FILENAME, affi_av.REPAIR_FILENAME):
        path = loras / filename
        if not path.is_file():
            missing.append(str(path))
    return missing


def prepare_command(command: str, cache: str | Path) -> str:
    """The same argv, plus a weight download that exits before generation."""
    parts = shlex.split(command)
    if "--prepare-weights" not in parts:
        parts.append("--prepare-weights")
    if "--cache-dir" not in parts:
        parts.extend(["--cache-dir", str(cache)])
    return " ".join(shlex.quote(part) for part in parts)


def _runner_root() -> Path | None:
    here = Path.cwd()
    for candidate in [here, *here.parents]:
        if (candidate / "h3-runner" / "run_h3.py").is_file():
            return candidate
    return None


def run_choice(
    task: str,
    *,
    handle: str | None = None,
    mode: str | None = None,
    fill_label: str = "テンプレ",
    lines_text: str = "",
    image: str = "",
    look: Mapping[str, Any] | None = None,
    prompt: str = "",
    video: str = "",
    duration_s: float | str = 10,
    aspect: str = "9:16",
    bake_here: bool = False,
    data_dir: str | Path | None = None,
    out_dir: str | Path | None = None,
    table_out: str | Path | None = None,
    strong_min: int = 10,
    compare_min: int = 3,
    thin_below: int = 10,
    min_gap_pt: int = 10,
) -> str:
    """Run the one selected action. A job or an I2V command is written. mp4 is not rendered unless bake_here."""
    kind = resolve_task(task)
    if kind == "table":
        return _run_table(
            data_dir,
            table_out,
            strong_min=strong_min,
            compare_min=compare_min,
            thin_below=thin_below,
            min_gap_pt=min_gap_pt,
        )
    if kind == "job":
        return _run_job(handle, mode, fill_label, lines_text, image, look, out_dir)
    if kind == "i2v":
        return _run_i2v(image, prompt, duration_s, aspect, bake_here, out_dir)
    if kind == "repro":
        return _run_repro(video, image, aspect, out_dir)
    raise RuntimeError(f"やることが無い: {kind}")


def _run_table(
    data_dir: str | Path | None,
    table_out: str | Path | None,
    *,
    strong_min: int,
    compare_min: int,
    thin_below: int,
    min_gap_pt: int,
) -> str:
    if data_dir is None or not Path(data_dir).is_dir():
        return "表の調査データが無い。先に「読み込み」を実行してください。"
    built = genre.load_snapshot(
        Path(data_dir),
        genre.Thresholds(
            strong_min=strong_min,
            compare_min=compare_min,
            thin_below=thin_below,
            min_gap_pt=min_gap_pt,
        ),
    )
    if table_out is not None:
        genre.write_outputs(built, Path(table_out))
    parts = [
        "## 表",
        "",
        "左がジャンル。冒頭は最初の3秒、主役は画面の中心。",
        f"強い＝両方{strong_min}件以上。弱い＝件数が少ない。比較不能＝片方が{compare_min}件未満。",
        "ドッグフードと見守りは、表の次の「オマージュ」を先に使う。",
        "ジョブはここでは書きません。ジョブは「選ぶ」で「話でジョブを書く」です。",
        "",
        genre.render_compare(built),
    ]
    for item in built.genres:
        parts.append(genre.render_genre(item))
    parts.append("動画は作っていない。投稿していない。")
    return "\n".join(parts)


def _run_job(
    handle: str | None,
    mode: str | None,
    fill_label: str,
    lines_text: str,
    image: str,
    look: Mapping[str, Any] | None,
    out_dir: str | Path | None,
) -> str:
    if not handle:
        return "先に「選ぶ」を実行してください。"
    if look_is_for(handle, look):
        picked = dict(look or {})
        look_note = "この話の見た目を使います。"
    else:
        picked = default_look(handle)
        look_note = "見た目は初期値です。変えるときは、話の名前が同じ見た目のセルを先に実行してから、もう一度「実行」してください。"
    picked["ref_image"] = image.strip()
    typed = [line.strip() for line in lines_text.splitlines() if line.strip()]
    try:
        shown = ref.look_block(handle, picked)["ja"]
        job = bake_reference(
            handle,
            mode=mode,
            fill=resolve_fill(fill_label),
            lines=typed or None,
            look=picked,
            image=image.strip() or None,
        )
    except ValueError as exc:
        return f"止まった: {exc}"
    root = Path(out_dir) if out_dir is not None else _bake_root()
    folder = handle if not mode else f"{handle}-{mode}"
    path = write_job(job, root / folder)
    lines = [
        describe_account(handle, mode),
        "---",
        shown,
        look_note,
        f"{job['fill']['label']} {job['theme']}",
        job["fill"]["note"],
    ]
    for cut in job["cuts"]:
        if cut["needs_line"]:
            lines.append(f"{cut['id']} {cut['line']}")
    lines.append(
        f"{job['status']} {job['task']} 型の秒 {job['duration_s']} カット {len(job['cuts'])} 生成 {len(job['clips'])}"
    )
    lines.extend(f"- {reason}" for reason in job["blocked"])
    lines.append(str(path))
    perf = job["performance"]
    lines.append(perf["motion"]["template_coverage"])
    lines.append(perf["motion"]["source_video"])
    lines.append(perf["lipsync"]["summary"])
    lines.append(perf["captions"]["summary"])
    lines.append(perf["bgm"]["summary"])
    lines.append("LoRA " + " / ".join(f"{row['file']} {row['scale']}" for row in perf["lora"]))
    lines.append("mp4 は焼いていない。投稿していない。")
    lines.append("---")
    lines.append(story_check(handle, mode))
    return "\n".join(lines)


def _run_i2v(
    image: str,
    prompt: str,
    duration_s: float | str,
    aspect: str,
    bake_here: bool,
    out_dir: str | Path | None,
) -> str:
    try:
        job = plan_i2v(
            image=image.strip() or None,
            prompt=prompt,
            duration_s=duration_s,
            aspect=aspect,
        )
    except ValueError as exc:
        return f"止まった: {exc}"
    root = Path(out_dir) if out_dir is not None else _bake_root()
    path = write_i2v(job, root / "i2v")
    lines = [
        "手入力で T2V" if job["task"] == "t2va" else "手入力で I2V",
        f"{job['status']} 秒 {job['duration_s']} {path}",
    ]
    lines.extend(f"- {reason}" for reason in job["blocked"])
    lines.append(job["commands"][-1])
    ran = False
    if bake_here:
        if job["status"] != "ready":
            lines.append("止まっているので焼かない。")
        else:
            found = _runner_root()
            if found is None:
                lines.append("h3-runner がこのランタイムに無い。コマンドは書いた。ここでは焼かない。")
            else:
                completed = subprocess.run(job["argv"], cwd=found)
                ran = completed.returncode == 0
                lines.append(f"終了コード {completed.returncode}")
    if not ran:
        lines.append("mp4 は焼いていない。投稿していない。")
    return "\n".join(lines)


def _run_repro(
    video: str,
    image: str,
    aspect: str,
    out_dir: str | Path | None,
    duration_s: float | None = None,
) -> str:
    try:
        job = plan_reproduce(
            video=video,
            image=image.strip() or None,
            aspect=aspect,
            duration_s=duration_s,
        )
    except ValueError as exc:
        return f"止まった: {exc}"
    root = Path(out_dir) if out_dir is not None else _bake_root()
    path = write_reproduce(job, root / "repro")
    lines = [
        "元動画を Ref2VA で再現するジョブです。",
        f"秒 {job.get('duration_s', '')} 範囲 {len(job['clips'])} {job['status']}",
        "参照動画がカメラ、カット、声、曲を持つ。",
        "FL2VA の Turbo は載せない。",
        "カットの切り替え時刻はプロンプトに書いていない。切り替えは元動画が持つ。",
        "読めたせりふは口がその文だけを作る。読めなければ文は足さない。話者は1人として並べる。",
    ]
    speech_note = str(job.get("speech_note") or "").strip()
    if speech_note:
        lines.append(speech_note)
    lines.append("元動画の一致率は測っていない。")
    lines.extend(f"- {reason}" for reason in job["blocked"])
    if job["commands"]:
        lines.append(job["commands"][-1])
    lines.append(str(path))
    lines.append("mp4 は焼いていない。投稿していない。")
    return "\n".join(lines)


def _bake_root() -> Path:
    if Path("/content").is_dir():
        return Path("/content/affi-bake")
    return Path("affi-bake")


def resolve_account(label: str, dog_pattern: str = "インタビュー（既定）") -> tuple[str, str | None]:
    """Map the Colab menu to one handle. Dog-food patterns apply only to nuts0629."""
    handles = {text: handle for text, handle in ACCOUNT_CHOICES}
    handles.update({handle: handle for _text, handle in ACCOUNT_CHOICES})
    handle = handles.get(label)
    if handle is None:
        raise KeyError(f"アカウントが無い: {label}")
    if handle != "nuts0629":
        return handle, None
    modes = {text: mode for text, mode in DOG_PATTERNS}
    mode = modes.get(dog_pattern)
    if mode is None:
        raise KeyError(f"ドッグフードの型が無い: {dog_pattern}")
    return handle, mode


def describe_account(handle: str, mode: str | None = None) -> str:
    """One account, in Japanese, before any other sheet."""
    item = ref.template_for(handle)
    view = _mode_view(item, mode)
    beats = _expand_beats(view["timeline"], int(view["repeat"]))
    cut_sum = round(sum(float(beat["end_s"]) - float(beat["start_s"]) for beat in beats), 3)
    pattern = _MODE_JA.get(view["mode"] or "", "切り替えはない")
    sections = "、".join(title for title, _fields in STORY_FORMS[handle])
    lines = [
        "再現するのはこの1件です。",
        f"話: {STORIES[handle]}",
        f"ジャンル: {item['genre']}",
        f"アカウント: {handle}",
        f"型: {pattern}",
        f"秒: {_num(float(view['duration_s']))}",
        f"画面: {view['canvas']}",
        f"選ぶ欄: {sections}",
    ]
    if abs(cut_sum - float(view["duration_s"])) > 0.051:
        lines.append(
            f"カットの合計は {_num(cut_sum)} 秒。型は {_num(float(view['duration_s']))} 秒。足りない秒は足さない。"
        )
    if handle != "nuts0629":
        lines.append("型の切り替えはドッグフードだけ。このアカウントでは使わない。")
    return "\n".join(lines)


def _accepts(duration_s: float) -> bool:
    return bool(diffusers_accepts(frames_for_seconds(duration_s)))


def _num(value: float) -> str:
    return f"{float(value):.3f}".rstrip("0").rstrip(".")


def _needs_line(speech: str) -> bool:
    return str(speech or "").strip() not in {"", "なし", "無し"}


def _aspect(canvas: str) -> tuple[str, int, int]:
    raw = str(canvas).lower().replace("×", "x")
    width_s, height_s = raw.split("x")
    width, height = int(width_s), int(height_s)
    if height >= width:
        return "9:16", 1080, 1920
    return "16:9", 1920, 1080


def _mode_view(item: Mapping[str, Any], mode: str | None) -> dict[str, Any]:
    modes = item.get("modes") or {}
    if not modes:
        return {
            "mode": None,
            "timeline": list(item["timeline"]),
            "duration_s": float(item["duration_s"]),
            "canvas": str(item["canvas"]),
            "subtitle": item.get("subtitle"),
            "repeat": 1,
            "cuts": item.get("cuts"),
            "audio": item.get("audio"),
        }
    key = mode or item.get("default_mode")
    if not key or key not in modes:
        raise KeyError(f"mode が無い: {key}")
    block = modes[key]
    return {
        "mode": key,
        "timeline": list(block["timeline"]),
        "duration_s": float(block["duration_s"]),
        "canvas": str(block.get("canvas") or item.get("canvas")),
        "subtitle": block.get("subtitle"),
        "repeat": int(block.get("repeat") or 1),
        "cuts": block.get("cuts"),
        "audio": block.get("audio"),
    }


def _expand_beats(timeline: Sequence[Mapping[str, Any]], repeat: int) -> list[dict[str, Any]]:
    beats = [dict(beat) for beat in timeline if not beat.get("optional")]
    if repeat < 1:
        raise ValueError(f"repeat が 0 以下: {repeat}")
    if repeat == 1 or not beats:
        return beats
    span = float(beats[-1]["end_s"]) - float(beats[0]["start_s"])
    if span <= 0:
        raise ValueError("繰り返すカットの長さが 0")
    expanded: list[dict[str, Any]] = []
    for cycle in range(repeat):
        offset = cycle * span
        for beat in beats:
            row = dict(beat)
            row["start_s"] = float(beat["start_s"]) + offset
            row["end_s"] = float(beat["end_s"]) + offset
            row["id"] = f"{beat['id']}-{cycle + 1}"
            expanded.append(row)
    return expanded


def split_trim(total: float) -> list[float]:
    """Cut lengths that sum to ``total`` and that H3 can generate.

    A piece shorter than 5 seconds stays that long in the edit. The generator
    request is raised to 5 seconds and trimmed back. A piece H3 cannot take
    as one request is split into equal pieces inside 5–15 seconds.
    """
    total_ms = int(round(float(total) * 1000))
    if total_ms <= 0:
        raise ValueError(f"カットの長さが 0 以下: {total}")
    seconds = total_ms / 1000
    if seconds < MIN_DURATION_S or (seconds <= MAX_DURATION_S and _accepts(seconds)):
        return [seconds]
    count = 2
    while count <= 24:
        if seconds / count < MIN_DURATION_S - 1e-9:
            break
        each = total_ms // count
        parts_ms = [each] * count
        parts_ms[-1] += total_ms - each * count
        parts = [ms / 1000 for ms in parts_ms]
        if all(MIN_DURATION_S <= part <= MAX_DURATION_S and _accepts(part) for part in parts):
            return parts
        count += 1
    raise ValueError(f"H3 の 5〜15 秒に分けられない: {seconds}秒")


def _request_seconds(trim_s: float) -> float:
    if trim_s < MIN_DURATION_S:
        return float(MIN_DURATION_S)
    return float(trim_s)


def _one_take(cuts: Any, duration_s: float, beat_sum: float) -> bool:
    if cuts not in (0, "0"):
        return False
    if abs(beat_sum - duration_s) > 0.051:
        return False
    return MIN_DURATION_S <= duration_s <= MAX_DURATION_S and _accepts(duration_s)


def _subtitle_text(style: str, line: str, needs_line: bool) -> str:
    if style == "字幕なし":
        return "字幕なし"
    if needs_line and line and line != PLACEHOLDER_LINE:
        return line
    return style


def bake_reference(
    handle: str,
    *,
    mode: str | None = None,
    theme: str = PLACEHOLDER_THEME,
    lines: Sequence[str] | None = None,
    look: Mapping[str, Any] | None = None,
    image: str | None = None,
    fill: str | None = None,
) -> dict[str, Any]:
    """One job. The template's timeline is the cut list. H3 only packs generation."""
    item = ref.template_for(handle)
    chosen = pack_for(handle, mode, fill) if fill else None
    if chosen and (theme or "").strip() in {"", PLACEHOLDER_THEME}:
        theme = chosen["theme"]
    if chosen and lines is None:
        lines = list(chosen["lines"])
    subject_en = chosen["subject_en"] if chosen else ""
    theme_text = (theme or "").strip() or PLACEHOLDER_THEME
    ref.reject_likeness(theme_text)
    for line in lines or []:
        ref.reject_likeness(line)
    view = _mode_view(item, mode)
    locked = ref.look_block(handle, default_look(handle) if look is None else look)
    beats = _expand_beats(view["timeline"], int(view["repeat"]))
    spoken = [str(line).strip() for line in (lines or [])]
    style = ref._subtitle_line(item, view["subtitle"])
    cuts: list[dict[str, Any]] = []
    for index, beat in enumerate(beats):
        line = spoken[index] if index < len(spoken) and spoken[index] else PLACEHOLDER_LINE
        needs = _needs_line(str(beat.get("speech") or ""))
        start_s = float(beat["start_s"])
        end_s = float(beat["end_s"])
        cuts.append(
            {
                "id": str(beat["id"]),
                "start_s": start_s,
                "end_s": end_s,
                "duration_s": round(end_s - start_s, 3),
                "picture": beat.get("picture"),
                "camera": beat.get("camera"),
                "speech": beat.get("speech"),
                "line": line,
                "needs_line": needs,
                "subtitle": _subtitle_text(style, line, needs),
            }
        )
    duration_s = float(view["duration_s"])
    cut_sum = round(sum(cut["duration_s"] for cut in cuts), 3)
    blocked: list[str] = []
    if abs(cut_sum - duration_s) > 0.051:
        blocked.append(
            f"カットの合計 { _num(cut_sum) } 秒と型の { _num(duration_s) } 秒が違う。足りない秒は足さない。"
        )
    aspect, delivery_w, delivery_h = _aspect(view["canvas"])
    image_text = (image or "").strip()
    still_missing = bool(image_text) and not Path(image_text).is_file()
    task = "fl2va" if image_text else "t2va"
    clips: list[dict[str, Any]] = []
    if not any(reason.startswith("カットの合計") for reason in blocked):
        if _one_take(view["cuts"], duration_s, cut_sum):
            groups = [(cuts, duration_s)]
        else:
            groups = [([cut], float(cut["duration_s"])) for cut in cuts]
        serial = 1
        for group, group_duration in groups:
            cursor = float(group[0]["start_s"])
            cut_ids = [cut["id"] for cut in group]
            pieces = split_trim(group_duration)
            for part_index, trim_s in enumerate(pieces):
                request_s = _request_seconds(trim_s)
                if not _accepts(request_s):
                    raise ValueError(f"H3 が受け取れない秒数: {request_s}")
                built = affi_av.clip_prompt(
                    handle=handle,
                    shots=group,
                    look_en=locked["en"],
                    request_s=request_s,
                    part_index=part_index,
                    part_count=len(pieces),
                    audio=view["audio"],
                    subject_en=subject_en,
                    frames=task == "fl2va",
                )
                clip_id = f"{serial:02d}-" + "-".join(cut_ids)
                end_s = round(cursor + trim_s, 3)
                clips.append(
                    {
                        "id": clip_id,
                        "cut_ids": cut_ids,
                        "trim_s": trim_s,
                        "request_s": request_s,
                        "prompt_name": f"{clip_id}.txt",
                        "prompt": built["prompt"],
                        "motion_ja": built["motion_ja"],
                        "spoken": built["spoken"],
                        "part_index": part_index,
                        "part_count": len(pieces),
                        "start_s": round(cursor, 3),
                        "end_s": end_s,
                    }
                )
                cursor = end_s
                serial += 1
    performance = affi_av.performance(
        handle,
        list(item.get("characters") or []),
        cuts,
        clips,
        view["audio"],
        burn=style != "字幕なし",
    )
    if theme_text == PLACEHOLDER_THEME:
        blocked.append("テーマは入力のまま")
    for cut in cuts:
        if cut["needs_line"] and cut["line"] == PLACEHOLDER_LINE:
            blocked.append(f"{cut['id']} の台詞は入力のまま")
    if still_missing:
        blocked.append("静止画のファイルが無い。場所を直すか、欄を空にする。")
    trim_sum = round(sum(clip["trim_s"] for clip in clips), 3)
    if clips and abs(trim_sum - duration_s) > 0.051:
        raise ValueError(f"書き出し {trim_sum} 秒が型の {duration_s} 秒と違う")
    return {
        "schema": SCHEMA,
        "source": "reference",
        "task": task,
        "handle": handle,
        "genre": item["genre"],
        "mode": view["mode"],
        "theme": theme_text,
        "subject_en": subject_en,
        "fill": None
        if chosen is None
        else {"id": chosen["id"], "label": chosen["label"], "note": chosen["note"]},
        "duration_s": duration_s,
        "canvas": view["canvas"],
        "aspect": aspect,
        "delivery_width": delivery_w,
        "delivery_height": delivery_h,
        "look": {"ja": locked["ja"], "en": locked["en"], "ref_image": locked["ref_image"]},
        "cuts": cuts,
        "clips": clips,
        "performance": performance,
        "join": {
            "delivery": "delivery.mp4",
            "width": delivery_w,
            "height": delivery_h,
            "parts": [{"file": f"clips/{clip['id']}.mp4", "trim_s": clip["trim_s"]} for clip in clips],
        },
        "audio": view["audio"],
        "image": image_text,
        "status": "blocked" if blocked else "ready",
        "blocked": blocked,
        "generates_video": False,
        "posts": False,
        "seconds_from": "reference-template",
        "commands": [],
    }


def bake_genre(genre: str, **kwargs: Any) -> dict[str, Any]:
    handle = GENRE_HANDLES.get(genre)
    if handle is None:
        raise KeyError(f"ジャンルが無い: {genre}")
    job = bake_reference(handle, **kwargs)
    job["source"] = "genre"
    if job["genre"] != genre:
        job["blocked"].append("参照アカウントのジャンル名と表のジャンル名が違う")
        job["status"] = "blocked"
    return job


def annotate_table(
    job: dict[str, Any],
    *,
    duration_band: str | None,
    opening_type: str | None,
    main_subject: str | None,
    face_shown: str | None,
    basis: str | None,
    account_confidence: str | None,
    homage: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach the genre table. Do not change seconds, cuts, or subtitles."""
    table: dict[str, Any] = {
        "duration_band": duration_band,
        "opening_type": opening_type,
        "main_subject": main_subject,
        "face_shown": face_shown,
        "basis": basis,
        "account_confidence": account_confidence,
    }
    if homage:
        table["first_3_seconds"] = homage.get("first_3_seconds")
        table["borrow"] = list(homage.get("borrow") or [])
        table["do_not_copy"] = list(homage.get("do_not_copy") or [])
    job["source"] = "genre"
    job["genre_table"] = table
    job["seconds_from"] = "reference-template"
    return job


def _argv(
    *,
    task: str,
    prompt_file: Path,
    duration_s: float,
    aspect: str,
    out_path: Path,
    image: str,
) -> list[str]:
    args = [
        "python3",
        "h3-runner/run_h3.py",
        "--task",
        task,
        "--prompt-file",
        str(prompt_file),
        "--duration",
        _num(float(duration_s)),
        "--aspect",
        aspect,
        "--seed",
        "0",
        "--out",
        str(out_path),
    ]
    if image:
        args.extend(["--image", image])
    args.extend(affi_av.lora_cli())
    return args


def _command(job_dir: Path, clip: Mapping[str, Any], image: str, aspect: str, task: str) -> str:
    args = _argv(
        task=task,
        prompt_file=job_dir / "prompts" / str(clip["prompt_name"]),
        duration_s=float(clip["request_s"]),
        aspect=aspect,
        out_path=job_dir / "clips" / f"{clip['id']}.mp4",
        image="" if task == "t2va" else image,
    )
    return " ".join(shlex.quote(part) for part in args)


def write_job(job: dict[str, Any], folder: str | Path) -> Path:
    """Write job.json, prompts, and the H3 commands. Do not run them."""
    job_dir = Path(folder)
    prompt_dir = job_dir / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    for clip in job["clips"]:
        (prompt_dir / str(clip["prompt_name"])).write_text(str(clip["prompt"]), encoding="utf-8")
    commands = [
        "# mp4 は焼かない。投稿しない。ready のとき、Research のルートで次を実行する。",
        f"# status={job['status']}",
    ]
    if job["blocked"]:
        commands.extend(f"# {reason}" for reason in job["blocked"])
    task = str(job.get("task") or "fl2va")
    commands.extend(
        _command(job_dir, clip, str(job.get("image") or ""), str(job["aspect"]), task) for clip in job["clips"]
    )
    job["commands"] = commands
    path = job_dir / "job.json"
    path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (job_dir / "commands.txt").write_text("\n".join(commands) + "\n", encoding="utf-8")
    subtitles = [
        {"id": cut["id"], "start_s": cut["start_s"], "end_s": cut["end_s"], "text": cut["subtitle"]}
        for cut in job["cuts"]
    ]
    (job_dir / "subtitles.json").write_text(
        json.dumps(subtitles, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    captions = (job.get("performance") or {}).get("captions", {}).get("rows", [])
    (job_dir / "captions.json").write_text(
        json.dumps(captions, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def i2v_second_choices() -> list[str]:
    """Durations the local H3 pipeline accepts, as Colab menu labels."""
    labels = []
    for seconds in (5, 6, 8, 10, 12, 14):
        if _accepts(float(seconds)):
            labels.append(str(seconds))
    if not labels:
        raise ValueError("I2V に使える秒が無い")
    return labels


def plan_i2v(
    *,
    image: str | None,
    prompt: str,
    duration_s: float | str = 10,
    aspect: str = "9:16",
) -> dict[str, Any]:
    """One hand-written clip. Empty image is T2VA. A file is I2VA. Does not render."""
    seconds = float(duration_s)
    if aspect not in {"9:16", "16:9"}:
        raise ValueError(f"画面が無い: {aspect}")
    if not _accepts(seconds):
        raise ValueError(f"H3 が受け取れない秒数: {seconds}")
    image_text = (image or "").strip()
    raw = str(prompt or "").strip()
    task = "t2va" if not image_text else "i2va"
    blocked: list[str] = []
    prepared = ""
    if not raw:
        blocked.append("プロンプトが空")
    else:
        ref.reject_likeness(raw)
        prepared = affi_av.t2v_prompt(raw) if task == "t2va" else affi_av.i2v_prompt(raw)
    if image_text and not Path(image_text).is_file():
        blocked.append("静止画のファイルが無い。場所を直すか、欄を空にする。")
    width, height = (1080, 1920) if aspect == "9:16" else (1920, 1080)
    return {
        "schema": "affi-i2v-job/v1",
        "source": "i2v",
        "task": task,
        "prompt": prepared,
        "duration_s": seconds,
        "aspect": aspect,
        "delivery_width": width,
        "delivery_height": height,
        "image": image_text,
        "status": "blocked" if blocked else "ready",
        "blocked": blocked,
        "generates_video": False,
        "posts": False,
        "commands": [],
        "argv": [],
    }


def write_i2v(job: dict[str, Any], folder: str | Path) -> Path:
    """Write the hand prompt and the T2VA or I2VA command. Do not run it."""
    job_dir = Path(folder)
    job_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = job_dir / "prompt.txt"
    prompt_path.write_text(str(job.get("prompt") or ""), encoding="utf-8")
    out_path = job_dir / "clip.mp4"
    task = str(job.get("task") or "i2va")
    argv = _argv(
        task=task,
        prompt_file=prompt_path,
        duration_s=float(job["duration_s"]),
        aspect=str(job["aspect"]),
        out_path=out_path,
        image="" if task == "t2va" else str(job.get("image") or ""),
    )
    label = "T2V" if task == "t2va" else "I2V"
    commands = [
        f"# {label}。プロンプトは手入力。mp4 は下の「焼く」で焼く。投稿しない。",
        f"# status={job['status']}",
    ]
    if job["blocked"]:
        commands.extend(f"# {reason}" for reason in job["blocked"])
    commands.append(" ".join(shlex.quote(part) for part in argv))
    job["commands"] = commands
    job["argv"] = argv
    path = job_dir / "job.json"
    saved = dict(job)
    saved["argv"] = []
    path.write_text(json.dumps(saved, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (job_dir / "commands.txt").write_text("\n".join(commands) + "\n", encoding="utf-8")
    return path


def source_spans(duration_s: float) -> list[tuple[float, float]]:
    """Ranges that cover ``duration_s`` and that H3 can generate. A file under 5 seconds does not split."""
    if float(duration_s) < MIN_DURATION_S:
        raise ValueError("元動画が5秒未満。H3 は5秒から。")
    parts = split_trim(duration_s)
    spans: list[tuple[float, float]] = []
    cursor_ms = 0
    total_ms = int(round(float(duration_s) * 1000))
    for part in parts:
        part_ms = int(round(float(part) * 1000))
        end_ms = min(total_ms, cursor_ms + part_ms)
        spans.append((cursor_ms / 1000, end_ms / 1000))
        cursor_ms = end_ms
    if spans and cursor_ms != total_ms:
        start, _end = spans[-1]
        spans[-1] = (start, total_ms / 1000)
    return spans


_DROPPED_SPEECH = "実在や未成年の指定はせりふから外した。"


def _kept_speech(raw: list) -> tuple[list[dict], bool]:
    """Finished lines that can be spoken. A banned line is dropped and not rewritten."""
    kept: list[dict] = []
    dropped = False
    for row in raw:
        if not isinstance(row, dict):
            continue
        text = affi_speech.finish_sentence(str(row.get("text") or ""))
        if not text:
            continue
        try:
            ref.reject_likeness(text)
        except ValueError:
            dropped = True
            continue
        try:
            start_s = float(row["start_s"])
            end_s = float(row["end_s"])
        except (KeyError, TypeError, ValueError):
            continue
        if end_s <= start_s:
            continue
        kept.append({"start_s": start_s, "end_s": end_s, "text": text})
    kept.sort(key=lambda item: (item["start_s"], item["end_s"]))
    return kept, dropped


def _load_repro_speech(
    path_text: str,
    speech: list | None,
    *,
    readable: bool,
) -> tuple[list[dict], str, bool]:
    """Absolute lines, a note, and whether the words were actually read.

    ``speech`` is a measured read, including an empty list for silence.
    A missing read does not invent a line.
    """
    if speech is not None:
        raw = list(speech)
        known = True
        note = "発話は無い。口は言葉を作らない。" if not raw else "せりふは渡された。口はその文だけを作る。"
    elif readable and path_text and Path(path_text).is_file():
        raw, note, known = affi_speech.read_source_speech(Path(path_text))
    else:
        return [], "", False
    kept, dropped = _kept_speech(raw)
    if dropped and not kept:
        note = f"{_DROPPED_SPEECH} 残ったせりふは無い。口は言葉を作らない。"
    elif dropped:
        note = f"{note} {_DROPPED_SPEECH}".strip()
    return kept, note, known


def _mouth_sentences(lines: list[dict], speech_known: bool) -> str:
    """Mouth text for one slice. Words stay inside ``<d>``. No camera cut is invented."""
    spoken: list[str] = []
    for line in lines:
        tag = affi_speech.dialogue_tag(str(line.get("text") or ""))
        if not tag:
            continue
        start = float(line["start_s"])
        if start < 0.05:
            when = "From the start of this shot"
        else:
            when = f"At {affi_speech.stamp(start)} into this shot"
        spoken.append(
            f"{when}, one on-screen mouth (S1) says: {tag} "
            "The mouth forms that one line and no other words."
        )
    if spoken:
        return (
            "One on-screen mouth (S1) speaks, in the order heard. "
            "The camera does not cut because a line starts. "
            + " ".join(spoken)
            + " When a line ends, the mouth closes until the next line."
        )
    if speech_known:
        return "No one speaks. Mouths do not form words."
    return (
        "The on-screen mouth shapes the words heard in the soundtrack of <Video 1> "
        "and closes when that soundtrack has no speech."
    )


def reproduce_prompt(
    *,
    has_image: bool,
    lines: list[dict] | None = None,
    speech_known: bool = False,
) -> str:
    """Six Ref2VA sections. Cut times stay in the file. Spoken words are the ones already read."""
    if has_image:
        subjects = (
            "<Picture 1> is the identity still. Appearance follows this still.\n"
            "<Video 1> is the source slice. Camera, cuts, timing, action, speech, and music follow this slice."
        )
        summary = (
            "[reference generation + video editing + audio reuse] "
            "The target video keeps the appearance of <Picture 1> and plays <Video 1> as the source slice plays, soundtrack included."
        )
        retention = (
            "<Picture 1> (appearance): fully_preserved - the visible identity follows the still.\n"
            "<Video 1> (camera, cuts, timing, speech, and music): fully_preserved - "
            "the slice's camera, cuts, speech, and music stay as heard and seen in the file."
        )
        opening = "The visible identity follows <Picture 1>. The motion follows <Video 1>.\n"
    else:
        subjects = (
            "<Video 1> is the source slice, from its first frame through its last frame. "
            "It supplies the camera, the cuts, the timing, the visible action, and the soundtrack."
        )
        summary = (
            "[video editing + audio reuse] "
            "The target video is <Video 1> played as the source slice plays, including its soundtrack."
        )
        retention = (
            "<Video 1> (camera, cuts, timing, speech, and music): fully_preserved - "
            "the slice is kept as it plays, including every cut inside the file and the soundtrack heard in the file."
        )
        opening = ""
    detail = (
        f"{opening}"
        "The target video follows <Video 1> from its first frame to its last frame.\n"
        "[Shot 1] Framing, subject placement, lighting, and action match <Video 1>. "
        "When <Video 1> cuts, the target video cuts at that same moment to the same framing. "
        "Speech stays in the language heard in <Video 1> and is not rewritten. "
        f"{_mouth_sentences(list(lines or []), speech_known)}"
    )
    sound = "The ambience and physical sounds are the soundtrack of <Video 1>, kept as heard."
    music = (
        "Audience-only music is the soundtrack of <Video 1>, kept as heard, "
        "including its instruments, tempo, and level."
    )
    return (
        f"subject_definitions:\n{subjects}\n\n"
        f"summary:\n{summary}\n\n"
        f"retention_analysis:\n{retention}\n\n"
        f"detailed_description:\n{detail}\n\n"
        f"overall_soundscape:\n{sound}\n\n"
        f"non_diegetic_music:\n{music}\n"
    )


def probe_duration_s(path: Path) -> float:
    """Seconds from ffprobe. A missing reading is an error, not a guessed length."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe が無い")
    try:
        text = subprocess.check_output(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nw=1:nk=1",
                str(path),
            ],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=60,
        )
    except subprocess.CalledProcessError as exc:
        detail = (exc.stdout or "").strip() or "ffprobe が失敗した"
        raise RuntimeError(detail) from exc
    try:
        seconds = float(text.strip())
    except ValueError as exc:
        raise RuntimeError(f"秒数が読めない: {text!r}") from exc
    if seconds <= 0:
        raise RuntimeError(f"秒数が 0: {seconds}")
    return seconds


def plan_reproduce(
    *,
    video: str,
    image: str | None = None,
    aspect: str = "9:16",
    duration_s: float | None = None,
    speech: list | None = None,
) -> dict[str, Any]:
    """One Ref2VA job per legal slice of the source file. Does not render.

    ``duration_s`` is only for a caller that already measured the file.
    When it is omitted, the seconds come from ffprobe.
    ``speech`` is a measured read in absolute source time. An empty list means
    silence. When it is omitted, the words come from the file or its sidecar.
    """
    if aspect not in {"9:16", "16:9"}:
        raise ValueError(f"画面が無い: {aspect}")
    path_text = (video or "").strip()
    image_text = (image or "").strip()
    blocked: list[str] = []
    measured: float | None = None
    if not path_text:
        blocked.append("元動画の場所が空")
    elif not Path(path_text).is_file():
        blocked.append("元動画のファイルが無い。場所を直す。")
    elif duration_s is None:
        try:
            measured = probe_duration_s(Path(path_text))
        except (OSError, subprocess.SubprocessError, RuntimeError, ValueError) as exc:
            blocked.append(f"秒数が測れない。{exc}")
    else:
        measured = float(duration_s)
    if image_text and not Path(image_text).is_file():
        blocked.append("静止画のファイルが無い。場所を直すか、欄を空にする。")
    spans: list[tuple[float, float]] = []
    if measured is not None and not any(reason.startswith("秒数が測れない") for reason in blocked):
        if measured < MIN_DURATION_S:
            blocked.append("元動画が5秒未満。H3 は5秒から。")
        else:
            try:
                spans = source_spans(measured)
            except ValueError as exc:
                blocked.append(str(exc))
    if blocked:
        spans = []
    speech_lines, speech_note, speech_known = _load_repro_speech(
        path_text,
        speech,
        readable=not blocked,
    )
    has_image = bool(image_text) and not blocked
    width, height = (1920, 1080) if aspect == "16:9" else (1080, 1920)
    clips = []
    for index, (start_s, end_s) in enumerate(spans, start=1):
        trim_s = round(end_s - start_s, 3)
        slice_lines = affi_speech.lines_in_span(speech_lines, start_s, end_s)
        prompt = reproduce_prompt(has_image=has_image, lines=slice_lines, speech_known=speech_known)
        ref.reject_likeness(prompt)
        clips.append(
            {
                "id": f"{index:02d}",
                "prompt_name": f"{index:02d}.txt",
                "prompt": prompt,
                "start_s": start_s,
                "end_s": end_s,
                "trim_s": trim_s,
                "request_s": _request_seconds(trim_s),
            }
        )
    return {
        "schema": "affi-repro-job/v1",
        "source": "repro",
        "task": "ref2va",
        "video": path_text,
        "image": image_text,
        "duration_s": measured,
        "aspect": aspect,
        "delivery_width": width,
        "delivery_height": height,
        "steps": DEFAULT_STEPS,
        "video_shift": VIDEO_FLOW_SHIFT,
        "speech": speech_lines,
        "speech_note": speech_note,
        "speech_known": speech_known,
        "clips": clips,
        "status": "blocked" if blocked else "ready",
        "blocked": blocked,
        "generates_video": False,
        "posts": False,
        "commands": [],
        "note": "参照動画がカメラ、カット、声、曲を持つ。FL2VA の LoRA は載せない。元動画の一致率は測っていない。",
    }


def _repro_argv(job_dir: Path, clip: Mapping[str, Any], job: Mapping[str, Any]) -> list[str]:
    args = [
        "python3",
        "h3-runner/run_h3.py",
        "--task",
        "ref2va",
        "--prompt-file",
        str(job_dir / "prompts" / str(clip["prompt_name"])),
        "--video",
        str(job["video"]),
        "--video-start",
        _num(float(clip["start_s"])),
        "--video-end",
        _num(float(clip["end_s"])),
        "--duration",
        _num(float(clip["request_s"])),
        "--aspect",
        str(job["aspect"]),
        "--seed",
        "0",
        "--steps",
        str(int(job["steps"])),
        "--video-shift",
        _num(float(job["video_shift"])),
        "--out",
        str(job_dir / "clips" / f"{clip['id']}.mp4"),
    ]
    image = str(job.get("image") or "")
    if image:
        args.extend(["--image", image])
    return args


def delivery_join_argv(
    parts: list[tuple[Path, float]],
    out_path: Path,
    *,
    width: int,
    height: int,
) -> list[str]:
    """Trim each slice back to the source range and concatenate. Same shape as h3_runner.ffmpeg_join."""
    if not parts:
        raise ValueError("concat needs at least one clip")
    inputs: list[str] = []
    filters: list[str] = []
    for index, (path, seconds) in enumerate(parts):
        if seconds <= 0:
            raise ValueError(f"trim seconds must be positive, got {seconds}")
        inputs.extend(["-i", str(path)])
        filters.append(
            f"[{index}:v]trim=duration={seconds:.3f},setpts=PTS-STARTPTS,"
            f"scale={width}:{height}:flags=lanczos,setsar=1[v{index}]"
        )
        filters.append(f"[{index}:a]atrim=duration={seconds:.3f},asetpts=PTS-STARTPTS[a{index}]")
    count = len(parts)
    paired = "".join(f"[v{index}][a{index}]" for index in range(count))
    filters.append(f"{paired}concat=n={count}:v=1:a=1[v][a]")
    return [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-r",
        "24",
        "-c:a",
        "aac",
        "-ar",
        "32000",
        "-ac",
        "2",
        str(out_path),
    ]


def join_line(job_dir: Path) -> str | None:
    """The ffmpeg line written beside a source-video job. None when there is nothing to join."""
    path = Path(job_dir) / "join.txt"
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        body = line.strip()
        if body and not body.startswith("#"):
            return body
    return None


def write_reproduce(job: dict[str, Any], folder: str | Path) -> Path:
    """Write prompts and Ref2VA commands. Do not run them and do not attach FL2V LoRA."""
    job_dir = Path(folder)
    prompt_dir = job_dir / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    for clip in job["clips"]:
        (prompt_dir / str(clip["prompt_name"])).write_text(str(clip["prompt"]), encoding="utf-8")
    commands = [
        "# Ref2VA。元動画の範囲を参照にする。FL2VA の LoRA は載せない。mp4 は下の「焼く」で焼く。投稿しない。",
        f"# status={job['status']}",
    ]
    if job["blocked"]:
        commands.extend(f"# {reason}" for reason in job["blocked"])
    argv_rows = [_repro_argv(job_dir, clip, job) for clip in job["clips"]]
    commands.extend(" ".join(shlex.quote(part) for part in argv) for argv in argv_rows)
    job["commands"] = commands
    path = job_dir / "job.json"
    path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (job_dir / "commands.txt").write_text("\n".join(commands) + "\n", encoding="utf-8")
    captions = [
        {
            "start_s": float(line["start_s"]),
            "end_s": float(line["end_s"]),
            "text": str(line["text"]),
            "burn": False,
        }
        for line in job.get("speech") or []
    ]
    (job_dir / "captions.json").write_text(
        json.dumps(captions, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if job["status"] == "ready" and job["clips"]:
        parts = [
            (job_dir / "clips" / f"{clip['id']}.mp4", float(clip["trim_s"]))
            for clip in job["clips"]
        ]
        join_argv = delivery_join_argv(
            parts,
            job_dir / "source.mp4",
            width=int(job["delivery_width"]),
            height=int(job["delivery_height"]),
        )
        join_text = " ".join(shlex.quote(part) for part in join_argv)
        (job_dir / "join.txt").write_text(
            "# 全部の mp4 ができたあと。最初の1本だけのときは実行しない。\n" + join_text + "\n",
            encoding="utf-8",
        )
    return path


def _place(room: str, style: str, palette: str, light: str) -> tuple[tuple[str, str, str], ...]:
    return (
        ("部屋", "place_room", room),
        ("雰囲気", "place_style", style),
        ("色味", "place_palette", palette),
        ("光", "place_light", light),
    )


def _person(
    prefix: str,
    key_prefix: str,
    gender: str,
    age: str,
    hair: str,
    color: str,
    clothes: str,
    build: str,
    makeup: str,
) -> tuple[tuple[str, str, str], ...]:
    return (
        (f"{prefix}の性別", f"{key_prefix}gender", gender),
        (f"{prefix}の年代", f"{key_prefix}age", age),
        (f"{prefix}の髪型", f"{key_prefix}hair", hair),
        (f"{prefix}の髪色", f"{key_prefix}hair_color", color),
        (f"{prefix}の服", f"{key_prefix}clothes", clothes),
        (f"{prefix}の体", f"{key_prefix}build", build),
        (f"{prefix}の表情", f"{key_prefix}makeup", makeup),
    )


def _animal(
    prefix: str,
    breed_label: str,
    key_prefix: str,
    species: str,
    breed: str,
    coat: str,
    build: str,
    outfit: str,
) -> tuple[tuple[str, str, str], ...]:
    return (
        (f"{prefix}の種類", f"{key_prefix}species", species),
        (breed_label, f"{key_prefix}breed", breed),
        (f"{prefix}の毛", f"{key_prefix}coat", coat),
        (f"{prefix}の体", f"{key_prefix}build", build),
        (f"{prefix}の衣装", f"{key_prefix}outfit", outfit),
    )


# (見出し, ((欄の名前, lookのキー, 初期値), ...))
# 初期値は元アカウントの見た目ではない。その話に置いたときの仮。
STORY_FORMS: dict[str, tuple[tuple[str, tuple[tuple[str, str, str], ...]], ...]] = {
    "the.care.logic": (
        (
            "材料のキャラ",
            (
                ("材料", "mascot_subject", "茶葉"),
                ("作り", "mascot_style", "粘土"),
                ("キャラの色", "mascot_color", "生成り"),
            ),
        ),
        ("場所", _place("リビング", "北欧", "白と木", "昼の自然光")),
        ("口調", (("口調", "speech", "標準語"),)),
    ),
    "nuts0629": (
        (
            "犬（会話の2匹もこの見た目）",
            _animal("犬", "犬種", "animal_", "犬", "柴", "黒の短毛", "小柄", "無地の首輪"),
        ),
        ("場所", _place("リビング", "北欧", "白と木", "昼の自然光")),
        ("口調", (("口調", "speech", "標準語"),)),
    ),
    "junjun_ranran": (
        (
            "1匹目の猫",
            _animal("一匹目", "一匹目の猫種", "animal_", "猫", "マンチカン", "グレー一色", "普通", "何も着けない"),
        ),
        (
            "2匹目の猫",
            _animal(
                "二匹目",
                "二匹目の猫種",
                "animal2_",
                "猫",
                "スコティッシュフォールド",
                "白の短毛",
                "小柄",
                "何も着けない",
            ),
        ),
        ("最後に少し出る人", _person("人", "person_", "女性", "40代", "ショート", "黒", "無地のニット", "普通", "ほぼ無し")),
        ("場所", _place("リビング", "北欧", "白と木", "昼の自然光")),
        ("口調（2匹共通）", (("口調", "speech", "標準語"),)),
    ),
    "yako.shiawasekon": (
        ("女性", _person("女性", "person_", "女性", "30代", "ショート", "黒", "無地のニット", "普通", "ほぼ無し")),
        ("男性", _person("男性", "person2_", "男性", "30代", "ショート", "黒", "シャツ", "普通", "ほぼ無し")),
        ("場所", _place("カフェ", "モダン", "生成り", "暖かい室内灯")),
        ("口調", (("口調", "speech", "標準語"),)),
    ),
}


def _form_keys() -> dict[str, str]:
    found: dict[str, str] = {}
    for sections in STORY_FORMS.values():
        for _title, fields in sections:
            for label, key, _default in fields:
                previous = found.get(label)
                if previous is not None and previous != key:
                    raise RuntimeError(f"見た目の欄が衝突: {label}")
                found[label] = key
    return found


FORM_KEYS = _form_keys()

_FORM_TITLE = {
    "the.care.logic": "美容：材料のキャラの見た目",
    "nuts0629": "ドッグフード：犬の見た目",
    "junjun_ranran": "見守り：猫2匹の見た目",
    "yako.shiawasekon": "婚活：男女の見た目",
}
_FORM_NOTE = {
    "the.care.logic": "迷ったら初期値のまま。この話を選んだときだけ使います。",
    "nuts0629": "人の顔はここでは選びません。迷ったら初期値のまま。この話を選んだときだけ使います。",
    "junjun_ranran": "迷ったら初期値のまま（猫が2匹）。この話を選んだときだけ使います。",
    "yako.shiawasekon": "初期値は成人の2人です。元のアカウントの人ではありません。この話を選んだときだけ使います。",
}


def default_look(handle: str) -> dict[str, str]:
    """The story form's initial values. Used when a job does not pass a look."""
    return look_from_form(
        {
            label: default
            for _title, fields in STORY_FORMS[handle]
            for label, _key, default in fields
        }
    )


def look_from_form(fields: Mapping[str, str]) -> dict[str, str]:
    """Map one story's Japanese form labels onto look keys.

    A value that is not in the dropdown is the free-text choice for that field.
    """
    unknown = [label for label in fields if label not in FORM_KEYS]
    if unknown:
        raise KeyError("見た目の欄が無い: " + "、".join(unknown))
    out: dict[str, str] = {}
    for label, value in fields.items():
        key = FORM_KEYS[label]
        text = str(value).strip()
        options = _options_for(key)
        other = str(ref.catalog()["other_label"])
        if text in options and text != other:
            out[key] = text
            continue
        if not text or text == other:
            raise ValueError(f"{label} は一覧から選ぶか、一覧に無い短い文をその欄に書く")
        out[key] = other
        out[f"{key}_text"] = text
    return out


def form_status(selected: str | None, expected: str) -> str:
    """Empty when this form belongs to the selected story."""
    if not selected:
        return "先に上の「選ぶ」を実行してください。"
    if selected == expected:
        return ""
    label = next(text for text, handle in ACCOUNT_CHOICES if handle == selected)
    return f"今の話は「{label}」です。{STORIES[selected]} この欄は使いません。"


def story_check(handle: str, mode: str | None = None) -> str:
    """The selected story's feasibility ask and hypotheses. No other account."""
    lines = [describe_account(handle, mode), "---"]
    fid = FEASIBILITY_FOR.get(handle)
    if fid is None:
        lines.append("この話の制作可否テストは無い。仮説の数字は投稿したあとに入る。")
    else:
        item = next(row for row in ref.feasibility() if row["id"] == fid)
        lines.append(f"この話で先に確かめること: {item['id']} {item['title']}")
        lines.append(str(item["ask"]))
        lines.append("これは焼くジョブではない。")
    lines.append("---")
    lines.append("この話の仮説")
    verdicts = {row["id"]: row for row in ref.judge()}
    found = False
    for spec in ref.hypotheses():
        if spec["handle"] != handle:
            continue
        found = True
        row = verdicts[spec["id"]]
        lines.append(f"{spec['id']} {spec['title']}（{spec['a_label']} / {spec['b_label']}）: {row['verdict']}")
        lines.append(row["detail"])
    if not found:
        lines.append("仮説は無い。")
    return "\n".join(lines)


def _options_for(key: str) -> list[str]:
    field_id = ref._field_id(key)
    return [str(opt["label"]) for opt in ref.catalog()["fields"][field_id]["options"]]


def _py(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _param_list(options: Sequence[str]) -> str:
    return "[" + ", ".join(_py(opt) for opt in options) + "]"


def story_form_cell(handle: str) -> str:
    """One Colab form. The label is the Japanese variable name. Code sets look only for this handle."""
    lines = [
        f"#@title {_FORM_TITLE[handle]} {{ display-mode: \"form\" }}",
        f"#@markdown {STORIES[handle]}{_FORM_NOTE[handle]}",
        "#@markdown 一覧に無い見た目は、その欄に短い文を直接書く。人物は成人のみ。実在の人や元のアカウントに似せる文は書けません。",
        "",
    ]
    pairs: list[str] = []
    for title, fields in STORY_FORMS[handle]:
        lines.append(f"#@markdown {title}")
        for label, key, default in fields:
            options = _options_for(key)
            if default not in options:
                raise ValueError(f"初期値が選択肢に無い: {label} / {default}")
            if not label.isidentifier():
                raise ValueError(f"欄の名前が変数にできない: {label}")
            lines.append(f"{label} = {_py(default)} #@param {_param_list(options)} {{allow-input: true}}")
            pairs.append(label)
        lines.append("")
    lines.append("import affi_bake")
    lines.append("")
    lines.append('task = globals().get("何をする", "話でジョブを書く")')
    lines.append('if task != "話でジョブを書く":')
    lines.append('    print("今は見た目を使いません。「選ぶ」が「話でジョブを書く」のときだけ、このセルを実行します。")')
    lines.append("else:")
    lines.append(f'    note = affi_bake.form_status(globals().get("HANDLE"), {_py(handle)})')
    lines.append("    if note:")
    lines.append("        print(note)")
    lines.append("    else:")
    lines.append("        look = affi_bake.look_from_form({")
    for label in pairs:
        lines.append(f"            {_py(label)}: {label},")
    lines.append("        })")
    lines.append('        print("この話の見た目を使います。")')
    lines.append("        print(affi_bake.STORIES[HANDLE])")
    return "\n".join(lines) + "\n"


def choice_cell() -> str:
    """The one form. Story, fill, still, and the hand-written I2V fields live here."""
    labels = [text for text, _handle in ACCOUNT_CHOICES]
    patterns = [text for text, _mode in DOG_PATTERNS]
    tasks = [text for text, _task in TASK_CHOICES]
    fills = [text for text, _fill in FILL_CHOICES]
    seconds = i2v_second_choices()
    default_second = "10" if "10" in seconds else seconds[0]
    aspects = ["9:16", "16:9"]
    return "\n".join(
        [
            '#@title 選ぶ { display-mode: "form" }',
            "#@markdown やりたいことを1つ選んで、このセルを実行する。上の「すべてのセルを実行」は押さない。",
            f"何をする = {_py(tasks[1])} #@param {_param_list(tasks)}",
            "#@markdown 話でジョブを書くときだけ、下の話・型・中身・台詞を使う。表を見る、自分の文、元動画を再現では無視する。",
            f"話 = {_py(labels[1])} #@param {_param_list(labels)}",
            "#@markdown ドッグフードだけ下を使う。インタビューは人がマイクを向ける8秒。咀嚼は8秒を4回。ダンスは全身で10秒。会話は吹き出し。ほかの話では無視する。",
            f"ドッグフードの型 = {_py(patterns[0])} #@param {_param_list(patterns)}",
            "#@markdown 中身。テンプレは用意した短い場面。オマージュは同じ絵の順で、別の短い台詞。元の型のままは型の絵とカメラ。元の顔、元の台詞、曲名は入らない。",
            f"中身 = {_py(fills[0])} #@param {_param_list(fills)}",
            "#@markdown 台詞を置き換えるときだけ書く。空なら、中身の台詞を使う。1行が1カット。",
            '台詞 = "" #@param {type:"raw"}',
            "#@markdown 静止画は空でよい。話と自分の文では、空なら文章から焼く。ファイルを書くと、その画像が最初のコマになる。元動画を再現では、空のままが元の見た目。ファイルを書くと、見た目だけその画像になる。",
            '静止画 = "" #@param {type:"string"}',
            "#@markdown 元動画を再現するときだけ、mp4 の場所を書く。空なら動かない。カメラ、カット、声、曲は、そのファイルが持つ。読めたせりふは口がその文だけを作る。FL2VA の Turbo は載せない。",
            '元動画 = "" #@param {type:"string"}',
            "#@markdown 自分の文で1本のときだけ、下を使う。静止画が空なら T2V。ファイルがあれば I2V。",
            f"秒 = {_py(default_second)} #@param {_param_list(seconds)}",
            f"画面 = {_py(aspects[0])} #@param {_param_list(aspects)}",
            'プロンプト = "" #@param {type:"raw"}',
            "",
            "import affi_bake",
            "",
            "HANDLE, MODE = affi_bake.resolve_account(話, ドッグフードの型)",
            "print(affi_bake.next_step(何をする))",
            'if 何をする == "話でジョブを書く":',
            "    print(affi_bake.describe_account(HANDLE, MODE))",
            "",
        ]
    )


def run_cell() -> str:
    """One run cell. The choice above decides table, one job, or a hand-written I2V command."""
    return "\n".join(
        [
            '#@title 実行 { display-mode: "form" }',
            "#@markdown 「選ぶ」のあと、このセルを実行する。表なら表。話ならジョブ。自分の文なら手入力。元動画なら Ref2VA の範囲。静止画が空なら、話と自分の文は T2V。",
            "#@markdown このセルは焼かない。ready と出たら、一番下の「焼く」を押す。投稿しない。",
            "",
            "import shutil",
            "import subprocess",
            "import sys",
            "import affi_bake",
            "from pathlib import Path",
            "",
            "try:",
            "    from IPython.display import Markdown, display",
            "except ImportError:",
            "    Markdown = None",
            "    display = None",
            "",
            'if "何をする" not in globals():',
            '    print("先に上の「選ぶ」を実行してください。")',
            "else:",
            '    out = Path("/content/affi-bake") if Path("/content").is_dir() else Path("affi-bake")',
            '    if 何をする == "元動画を再現" and Path("/content").is_dir():',
            '        if shutil.which("ffprobe") is None:',
            '            subprocess.check_call(["apt-get", "update", "-qq"])',
            '            subprocess.check_call(["apt-get", "install", "-y", "-qq", "ffmpeg"])',
            "        try:",
            "            import faster_whisper",
            "        except ImportError:",
            "            try:",
            '                subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "faster-whisper"])',
            "            except Exception as exc:",
            '                print("せりふの読み取りは入れられなかった。口は参照の音声に合わせる。", exc)',
            "    text = affi_bake.run_choice(",
            "        何をする,",
            '        handle=globals().get("HANDLE"),',
            '        mode=globals().get("MODE"),',
            '        fill_label=globals().get("中身", "テンプレ"),',
            '        lines_text=globals().get("台詞", ""),',
            '        image=globals().get("静止画", ""),',
            '        look=globals().get("look"),',
            '        prompt=globals().get("プロンプト", ""),',
            '        video=globals().get("元動画", ""),',
            '        duration_s=globals().get("秒", "10"),',
            '        aspect=globals().get("画面", "9:16"),',
            "        bake_here=False,",
            '        data_dir=globals().get("DATA_DIR"),',
            "        out_dir=out,",
            '        table_out=globals().get("TABLE_OUT"),',
            '        strong_min=int(globals().get("STRONG_MIN", 10)),',
            '        compare_min=int(globals().get("COMPARE_MIN", 3)),',
            '        thin_below=int(globals().get("THIN_BELOW", 10)),',
            '        min_gap_pt=int(globals().get("MIN_GAP_PT", 10)),',
            "    )",
            '    if 何をする == "表を見る" and display is not None and Markdown is not None:',
            "        display(Markdown(text))",
            "    else:",
            "        print(text)",
            "",
        ]
    )


def bake_cell() -> str:
    """One bake switch. Off by default, so Run all does not start a GPU job."""
    return """#@title 焼く { display-mode: "form" }
#@markdown ready のあと、焼くにチェックを入れてこのセルを押す。別のノートは開かない。投稿しない。
#@markdown 最初の1本だけがオンのときは1クリップ。口と声を見てからオフにして続き。
#@markdown 重みが無いとき落とすは、マイドライブに MiniMax-H3 が無いときだけ。プレビューは 144.1GB。オフなら落とさない。
焼く = False #@param {type:"boolean"}
最初の1本だけ = True #@param {type:"boolean"}
重みが無いとき落とす = False #@param {type:"boolean"}

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import affi_bake

if not 焼く:
    print("焼くにチェックを入れて、このセルをもう一度押してください。今は焼きません。")
else:
    task = globals().get("何をする")
    if not task:
        print("先に「選ぶ」と「実行」を押してください。")
    elif affi_bake.resolve_task(task) == "table":
        print("表は動画になりません。話か自分の文を選んで、「実行」のあと、もう一度ここを押してください。")
    else:
        try:
            import torch
        except ImportError:
            torch = None
        if torch is None or not torch.cuda.is_available():
            print("GPU がオフです。ランタイムを GPU にして、読み込みからやり直してください。途中で切り替えると、ここまでのファイルが消えます。")
        else:
            props = torch.cuda.get_device_properties(0)
            vram = props.total_memory / 1024 ** 3
            print(f"GPU: {props.name}  VRAM: {vram:.1f} GB")
            if vram < 24:
                print("VRAM が 24GB 未満です。G4 に変えて、読み込みからやり直してください。")
            else:
                on_colab = Path("/content").is_dir()
                if on_colab:
                    from google.colab import drive, userdata

                    drive.mount("/content/drive")
                    print("今マウントしたアカウントのマイドライブに保存します。")
                    root = Path("/content/Research")
                    branch = "cursor/affi-template-bake-44d6"
                    repo = "https://github.com/fireworker011/Research.git"
                    script = root / "h3-runner" / "run_h3.py"
                    if not script.is_file():
                        if root.exists():
                            raise SystemExit(f"{root} があるが {script} が無い。このフォルダを消してやり直す。")
                        subprocess.check_call(["git", "clone", "--depth", "1", "--branch", branch, repo, str(root)])
                    else:
                        subprocess.check_call(["git", "-C", str(root), "fetch", "--depth", "1", "origin", branch])
                        subprocess.check_call(["git", "-C", str(root), "checkout", branch])
                        subprocess.check_call(["git", "-C", str(root), "pull", "--ff-only", "origin", branch])
                    sys.path.insert(0, str(root / "h3-runner"))
                    sys.path.insert(0, str(root / "research" / "affi-templates"))
                    import importlib

                    importlib.reload(affi_bake)
                else:
                    userdata = None
                    found = affi_bake._runner_root()
                    if found is None:
                        raise SystemExit("h3-runner が無い。Colab の GPU でこのセルを押してください。")
                    root = found
                cache = Path("/content/drive/MyDrive/h3-weights") if on_colab else Path("hf-cache")
                os.environ["H3_HF_CACHE"] = str(cache)
                if shutil.which("ffmpeg") is None:
                    subprocess.check_call(["apt-get", "update", "-qq"])
                    subprocess.check_call(["apt-get", "install", "-y", "-qq", "ffmpeg"])
                need = False
                try:
                    import av
                    import diffusers
                    import imageio
                    import soundfile
                    from torchao.quantization import FqnToConfig
                except Exception:
                    need = True
                if need:
                    pkgs = [
                        "git+https://github.com/huggingface/diffusers.git@5ff8e59ff9fe81c6e2df4fb4c6ea0d97a5df5ab2",
                        "transformers>=4.45.0",
                        "accelerate>=0.34.0",
                        "safetensors>=0.4.3",
                        "huggingface_hub>=0.25.0",
                        "av>=11.0.0",
                        "imageio>=2.34.0",
                        "imageio-ffmpeg>=0.5.0",
                        "soundfile>=0.12.0",
                    ]
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "--upgrade-strategy", "only-if-needed", *pkgs])
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "torchao==0.18.0"])
                    from torchao.quantization import FqnToConfig
                print("パッケージは揃っています", "ffmpeg", shutil.which("ffmpeg"))
                missing = affi_bake.missing_weight_files(cache, task)
                if missing and not 重みが無いとき落とす:
                    print("重みが無いので焼きません。落とすときは「重みが無いとき落とす」を入れて、もう一度押してください。")
                    for item in missing:
                        print(item)
                else:
                    path = affi_bake.commands_file(
                        task,
                        handle=globals().get("HANDLE"),
                        mode=globals().get("MODE"),
                        out_dir=Path("/content/affi-bake") if on_colab else Path("affi-bake"),
                    )
                    if path is None:
                        print("先に「選ぶ」を押してください。")
                    else:
                        lines, note = affi_bake.commands_to_run(path, first_only=bool(最初の1本だけ))
                        print(note)
                        if lines and missing:
                            token = ""
                            if userdata is not None:
                                try:
                                    token = userdata.get("HF_TOKEN") or ""
                                except Exception:
                                    token = ""
                            if token:
                                os.environ["HF_TOKEN"] = token
                                os.environ["HUGGING_FACE_HUB_TOKEN"] = token
                                print("HF_TOKEN を読みました（値は表示しません）")
                            prep = affi_bake.prepare_command(lines[0], cache)
                            code = affi_bake.run_logged(shlex.split(prep), root)
                            print(f"重みの終了コード {code}")
                            if code != 0:
                                print("失敗。重みは揃っていません。mp4 は出来ていません。")
                                lines = []
                            else:
                                sys.path.insert(0, str(root / "h3-runner"))
                                if affi_bake.resolve_task(task) != "repro":
                                    from h3_runner.loras import prepare_fast_loras

                                    prepare_fast_loras(cache / "loras")
                        made = False
                        finished = True
                        for line in lines:
                            print(line)
                            code = affi_bake.run_logged(shlex.split(line), root)
                            print(f"終了コード {code}")
                            if code != 0:
                                print("失敗。mp4 は出来ていません。")
                                argv = shlex.split(line)
                                if "--out" in argv:
                                    err = Path(argv[argv.index("--out") + 1]).with_suffix(".error.txt")
                                if err.is_file():
                                    print(err.read_text(encoding="utf-8"))
                                finished = False
                                break
                            argv = shlex.split(line)
                            if "--out" not in argv:
                                continue
                            local_out = Path(argv[argv.index("--out") + 1])
                            if not local_out.is_file():
                                request = local_out.with_suffix(".request.json")
                                if request.is_file():
                                    print("mp4 は出ていない。あるのは", request)
                                else:
                                    print("mp4 は出ていない。", local_out)
                                continue
                            print("書いた", local_out, local_out.stat().st_size, "bytes")
                            made = True
                            if on_colab:
                                try:
                                    saved = affi_bake.publish_job_dir(path.parent)
                                except Exception as exc:
                                    print("マイドライブへのコピーに失敗した", exc)
                                else:
                                    print("マイドライブにコピーした", saved)
                                    for item in saved.rglob("*.mp4"):
                                        print("mp4", item, item.stat().st_size, "bytes")
                        if made and finished and not 最初の1本だけ:
                            join = affi_bake.join_line(path.parent)
                            if join:
                                print(join)
                                code = affi_bake.run_logged(shlex.split(join), root)
                                print(f"つなぎの終了コード {code}")
                        if made:
                            print("投稿していない。")
"""


def _intro() -> str:
    picks = {
        "the.care.logic": "見た目を変えるときは材料・場所・口調。",
        "nuts0629": "見た目を変えるときは犬・場所・口調。型を選ぶのはこの話だけ。",
        "junjun_ranran": "見た目を変えるときは猫2匹・人・場所・口調。",
        "yako.shiawasekon": "見た目を変えるときは女性・男性・場所・口調。",
    }
    blocks = [
        "# このノートだけ",
        "",
        "開くのはこのページだけです。ほかのノートは開かない。",
        "",
        "表は動画になりません。動画は一番下の **焼く** です。投稿しません。",
        "",
        "## 押す順番",
        "",
        "ランタイムは最初から **GPU** にします。途中で変えない。変えると、ここまでのファイルが消えます。",
        "",
        "1. **読み込み**",
        "2. **選ぶ** で、やりたいことを1つ選んで実行",
        "3. **実行**",
        "4. **焼く**（ready のあと。焼くにチェックを入れて押す。最初は1本だけ。mp4 はマイドライブの affi-bake に残る）",
        "",
        "見た目を変えるときだけ、2と3のあいだに、話の名前が同じ見た目のセルを1つ実行します。変えないときは飛ばします。初期値です。",
        "",
        "上のメニューの「すべてのセルを実行」は押しません。焼くはオフのままなので、全部実行しても動画は始まりません。",
        "",
        "## 選び方",
        "",
        "**表を見る**",
        "",
        "美容、ドッグフード、見守りカメラ、婚活の作り方の表が出ます。ジョブは書きません。",
        "",
        "**話でジョブを書く**",
        "",
        "話を1つ選びます。ドッグフードだけ、インタビュー・咀嚼・ダンス・会話も選びます。",
        "",
        "中身を1つ選びます。テーマは書きません。台詞は入っています。",
        "",
        "- **テンプレ** … 用意してある短い場面と台詞",
        "- **オマージュ** … 同じ絵とカメラの順で、別の短い台詞",
        "- **元の型のまま** … 型の絵とカメラの順。短い新しい台詞。元の顔、元の台詞、曲名は入りません",
        "",
        "静止画は空でよいです。空なら文章から焼きます。ファイルを書くと、その画像が最初のコマになります。台詞を変えたいときだけ、台詞の欄に1行ずつ書きます。",
        "",
        "**自分の文で1本**",
        "",
        "プロンプトを自分で書きます。秒と画面も「選ぶ」で選びます。静止画が空なら T2V、ファイルがあれば手入力で I2V です。「実行」が ready と出たら、一番下の「焼く」です。",
        "",
        "**元動画を再現**",
        "",
        "元の mp4 の場所を「元動画」に書きます。Ref2VA がそのファイルを参照にします。カメラ、カット、声、曲はファイルが持ちます。H3 は 5〜15 秒なので、長い動画は範囲に分かれます。",
        "FL2VA の Turbo は載せません。重みは transformer_ref です。静止画は空のままが、元の見た目です。",
        "カットの切り替え時刻はプロンプトに写しません。切り替えは元動画が持ちます。",
        "音声から読めたせりふだけを、口がその文だけ作ります。読めないときは口が参照の音声に合わせ、文は足しません。話者の切り分けはしません。一致率は測っていません。",
        "",
        "## 4つの話",
        "",
    ]
    for index, (label, handle) in enumerate(ACCOUNT_CHOICES, start=1):
        blocks.append(f"{index}. **{label.split('（')[0]}**（{handle}）")
        blocks.append(f"   {STORIES[handle]}{picks[handle]}")
        blocks.append("")
    blocks.extend(
        [
            "一覧に無い見た目は、その欄に短い文を直接書く。人物は成人のみ。実在の人や、元のアカウントの人・動物に似せる文は、そこで止まります。",
            "",
            "秒数・カット・字幕は型のままです。",
            "",
            "Checkpoint は MiniMax-H3。話のジョブと手入力は、FL2VA の Turbo と、動作のつながりを使います。",
            "元動画の再現は Ref2VA です。同じ Turbo は載せません。",
            "",
        ]
    )
    return "\n".join(blocks)


def _loader_cell() -> str:
    files = [
        "affi_genre_templates.py",
        "affi_reference.py",
        "affi_av.py",
        "affi_speech.py",
        "affi_bake.py",
        "reference-accounts/hypotheses.yaml",
        "reference-accounts/results.csv",
        "reference-accounts/looks.yaml",
        "reference-accounts/templates/the.care.logic.yaml",
        "reference-accounts/templates/nuts0629.yaml",
        "reference-accounts/templates/junjun_ranran.yaml",
        "reference-accounts/templates/yako.shiawasekon.yaml",
    ]
    listed = "\n".join(f'        "{rel}",' for rel in files)
    return "\n".join(
        [
            '#@title 読み込み { display-mode: "form" }',
            "#@markdown 最初にこのセルを実行する。調査日は 2026-10-07。初めてなら変えない。",
            'DATE = "2026-10-07"  #@param {type:"string"}',
            "",
            "from pathlib import Path",
            "import sys",
            "import urllib.request",
            "",
            'BRANCH = "cursor/affi-template-bake-44d6"',
            'REPO = "fireworker011/Research"',
            'RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/research/affi-templates"',
            "STRONG_MIN = 10",
            "COMPARE_MIN = 3",
            "THIN_BELOW = 10",
            "MIN_GAP_PT = 10",
            'LOCAL = Path("research/affi-templates")',
            'if not (LOCAL / "affi_bake.py").is_file():',
            "    here = Path.cwd()",
            "    for candidate in [here, *here.parents]:",
            '        if (candidate / "research/affi-templates/affi_bake.py").is_file():',
            '            LOCAL = candidate / "research/affi-templates"',
            "            break",
            'if not (LOCAL / "affi_bake.py").is_file():',
            '    LOCAL = Path("/content/affi-templates") if Path("/content").is_dir() else Path(".affi-templates-download")',
            "    files = [",
            listed,
            '        f"data/{DATE}/accounts.csv",',
            "    ]",
            "    for rel in files:",
            "        dest = LOCAL / rel",
            "        dest.parent.mkdir(parents=True, exist_ok=True)",
            "        urllib.request.urlretrieve(f\"{RAW}/{rel}\", dest)",
            '        print("取りました", rel)',
            "    try:",
            '        urllib.request.urlretrieve(f"{RAW}/data/{DATE}/videos.csv", LOCAL / "data" / DATE / "videos.csv")',
            "    except Exception:",
            '        print("動画一覧は無し。アカウント一覧だけで計算する。")',
            "sys.path.insert(0, str(LOCAL))",
            "import affi_reference as ref",
            "ref.ROOT = LOCAL",
            'ref.TEMPLATES = LOCAL / "reference-accounts" / "templates"',
            'ref.HYPOTHESES = LOCAL / "reference-accounts" / "hypotheses.yaml"',
            'ref.RESULTS = LOCAL / "reference-accounts" / "results.csv"',
            'ref.LOOKS = LOCAL / "reference-accounts" / "looks.yaml"',
            'DATA_DIR = LOCAL / "data" / DATE',
            'TABLE_OUT = LOCAL / "templates"',
            'print("読みました", LOCAL)',
            'print("次は「選ぶ」を実行してください。")',
            "",
        ]
    )


def _nb_lines(source: str) -> list[str]:
    if not source.endswith("\n"):
        source += "\n"
    return [line + "\n" for line in source.split("\n")[:-1]]


def _nb_cell(kind: str, source: str, cell_id: str, *, form: bool = False) -> dict[str, Any]:
    meta: dict[str, Any] = {"id": cell_id}
    if form:
        meta["cellView"] = "form"
    cell: dict[str, Any] = {"cell_type": kind, "metadata": meta, "source": _nb_lines(source)}
    if kind == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    return cell


def reference_notebook() -> dict[str, Any]:
    """The one Colab. A table, one story job, or a hand-written I2V command."""
    cells = [
        _nb_cell("markdown", _intro(), "intro"),
        _nb_cell("code", _loader_cell(), "load", form=True),
        _nb_cell("code", choice_cell(), "pick", form=True),
        _nb_cell(
            "markdown",
            "\n".join(
                [
                    "# 見た目を変えるときだけ",
                    "",
                    "「選ぶ」が **話でジョブを書く** のときだけ使います。見出しが今の話と同じセルを1つ実行します。",
                    "",
                    "迷ったら、この4つは実行しません。初期値を使います。初期値は元のアカウントの顔ではありません。",
                    "",
                    "ほかの話のセルを実行しても、見た目は入りません。",
                    "",
                ]
            ),
            "look-note",
        ),
    ]
    ids = {
        "the.care.logic": "look-care",
        "nuts0629": "look-dog",
        "junjun_ranran": "look-cats",
        "yako.shiawasekon": "look-drama",
    }
    for _label, handle in ACCOUNT_CHOICES:
        cells.append(_nb_cell("code", story_form_cell(handle), ids[handle], form=True))
    cells.append(
        _nb_cell(
            "markdown",
            "\n".join(
                [
                    "# 実行",
                    "",
                    "「選ぶ」のあと、このセルだけ実行します。",
                    "",
                    "- 表を見る … 4ジャンルの表。ジョブは書きません。動画にもなりません",
                    "- 話でジョブを書く … 選んだ1件のジョブ。静止画が空なら T2V。ファイルがあればその画像が最初のコマ",
                    "- 自分の文で1本 … 手入力。静止画が空なら T2V、ファイルがあれば I2V。ここでは焼きません",
                    "- 元動画を再現 … 元の mp4 を Ref2VA の参照にする。5〜15 秒の範囲に分ける。読めたせりふは口がその文だけを作る。FL2VA の Turbo は載せない。ここでは焼きません",
                    "",
                ]
            ),
            "run-note",
        )
    )
    cells.append(_nb_cell("code", run_cell(), "run", form=True))
    cells.append(
        _nb_cell(
            "markdown",
            "\n".join(
                [
                    "# 焼く",
                    "",
                    "別のノートは開かない。最初にランタイムを GPU にする。途中で変えない。",
                    "",
                    "上の「実行」が ready になってから、焼くにチェックを入れてこのセルを押す。",
                    "",
                    "最初の1本だけがオンのときは1クリップです。口と声を見てから、オフにして続きを焼きます。",
                    "",
                    "焼いた mp4 は、Colab のディスクに書いてから、そのときマウントしたアカウントのマイドライブ `affi-bake` にコピーします。",
                    "マイドライブへ直接 mp4 を開くと、小さな json だけ残って終了コード 1 になります。",
                    "json と同じフォルダの `clips` に mp4 が入ります。json だけなら動画はまだ出ていません。",
                    "失敗したときは、その場に理由が出て、`clips` に `.error.txt` が残ります。`request.json` は動画ではありません。",
                    "ランタイムを切っても、コピーした mp4 は残ります。",
                    "",
                    "重みはマイドライブの `h3-weights` です。",
                    "無いときだけ「重みが無いとき落とす」を入れます。話と手入力のプレビューは 144.1GB です。オフなら落としません。",
                    "元動画の再現は `transformer_ref` を使います。FL2VA/ と Ref2VA/ の単一ファイルは落としません。",
                    "範囲が2つ以上で、最初の1本だけをオフにしたとき、焼き終わった mp4 をつなぎます。",
                    "",
                    "投稿しません。",
                    "",
                ]
            ),
            "bake-note",
        )
    )
    cells.append(_nb_cell("code", bake_cell(), "bake", form=True))
    cells.append(
        _nb_cell(
            "markdown",
            "\n".join(
                [
                    "# 投稿したあとの数字",
                    "",
                    "今は飛ばします。",
                    "",
                    "`research/affi-templates/reference-accounts/results.csv` に1行足す。空欄は0にしない。未入力のままにする。",
                    "",
                    "- `hypothesis_id` … H1-1 のような番号",
                    "- `variant` … A か B",
                    "- `views` … 72時間後の再生",
                    "- `two_sec_hold_pct` … 2秒視聴のパーセント",
                    "- `diagnosis_signups` … 婚活の診断申込。無い仮説は空欄",
                    "",
                    "本数が足りないと「本数不足」。基準を超えると A か B が出る。A/Bで変えるのは仮説の1項目だけ。見た目は両版で同じにする。",
                    "",
                ]
            ),
            "numbers",
        )
    )
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
            "colab": {"name": "affi", "provenance": []},
        },
        "cells": cells,
    }


def moved_notebook() -> dict[str, Any]:
    """Old Colab paths. They only point at the one notebook."""
    text = "\n".join(
        [
            "# このノートは移しました",
            "",
            "開くのは次の1ページだけです。",
            "",
            NOTEBOOK_URL,
            "",
        ]
    )
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
            "colab": {"name": "affi-moved", "provenance": []},
        },
        "cells": [_nb_cell("markdown", text, "moved")],
    }



def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="型から H3 の焼くジョブを書く。mp4 は焼かない。投稿しない。")
    parser.add_argument("cmd", choices=["reference", "genre"])
    parser.add_argument("--handle", default="")
    parser.add_argument("--genre", default="")
    parser.add_argument("--mode", default="")
    parser.add_argument("--theme", default=PLACEHOLDER_THEME)
    parser.add_argument("--lines", default="")
    parser.add_argument("--image", default="")
    parser.add_argument("--look", default="")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    look = ref.load_look(Path(args.look)) if args.look else None
    lines = args.lines.splitlines()
    mode = args.mode or None
    image = args.image or None
    if args.cmd == "reference":
        if not args.handle:
            raise SystemExit("reference には --handle が要る")
        job = bake_reference(args.handle, mode=mode, theme=args.theme, lines=lines, look=look, image=image)
    else:
        if not args.genre:
            raise SystemExit("genre には --genre が要る")
        job = bake_genre(args.genre, mode=mode, theme=args.theme, lines=lines, look=look, image=image)
    path = write_job(job, Path(args.out))
    print(job["status"])
    for reason in job["blocked"]:
        print(reason)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
