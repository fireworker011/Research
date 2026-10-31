"""Queue C1..C4 on a ComfyUI that is already running. Does not start it."""

from __future__ import annotations

import json
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping

from wan_vace.controls import control_paths, load_control
from wan_vace.drive_models import present_filenames
from wan_vace.guides import write_guides
from wan_vace.prompts import load_prompts, with_face_lock
from wan_vace.workflow import BuiltPrompt, JobOptions, build_prompt


class QueueError(RuntimeError):
    """ComfyUI rejected a cut or never finished it."""


def post_prompt(base_url: str, prompt: Mapping[str, Any], opener: Any = urllib.request.urlopen) -> str:
    payload = json.dumps({"prompt": prompt}).encode("utf-8")
    request = urllib.request.Request(
        base_url.rstrip("/") + "/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with opener(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:2000]
        raise QueueError(f"Comfy が投入を受けなかった: {detail}") from exc
    if body.get("node_errors"):
        raise QueueError(f"Comfy がノードを拒否した: {body['node_errors']}")
    prompt_id = body.get("prompt_id")
    if not prompt_id:
        raise QueueError("Comfy が prompt_id を返さなかった")
    return str(prompt_id)


def finished_history(body: Mapping[str, Any], prompt_id: str) -> dict[str, Any] | None:
    item = body.get(prompt_id)
    if not isinstance(item, Mapping):
        return None
    status = item.get("status") or {}
    if status.get("status_str") == "error":
        raise QueueError(f"Comfy が失敗した: {status}")
    if status.get("completed"):
        return dict(item)
    return None


def history_mp4(item: Mapping[str, Any], output_root: Path) -> Path | None:
    outputs = item.get("outputs") or {}
    if not isinstance(outputs, Mapping):
        return None
    for node in outputs.values():
        if not isinstance(node, Mapping):
            continue
        for value in node.values():
            if not isinstance(value, list):
                continue
            for entry in value:
                if not isinstance(entry, Mapping):
                    continue
                full = entry.get("fullpath")
                if full and str(full).endswith(".mp4") and Path(str(full)).is_file():
                    return Path(str(full))
                name = str(entry.get("filename") or "")
                if name.endswith(".mp4"):
                    path = output_root / str(entry.get("subfolder") or "") / name
                    if path.is_file():
                        return path
    return None


def _wait(base_url: str, prompt_id: str, timeout_s: float, opener: Any) -> dict[str, Any]:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with opener(urllib.request.Request(f"{base_url.rstrip('/')}/history/{prompt_id}"), timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
        except Exception:
            time.sleep(15)
            continue
        item = finished_history(body, prompt_id)
        if item is not None:
            return item
        time.sleep(15)
    raise QueueError("待ち時間を超えた。/content/comfyui.log を見る。")


def prepare_cut(
    script_path: Path,
    control_path: Path,
    work_dir: Path,
    face_name: str | None,
    options: JobOptions,
    present: set[str],
    plate_dir: str | None,
) -> BuiltPrompt:
    control = load_control(control_path)
    prompts = load_prompts(script_path)
    cut_prompt = with_face_lock(prompts[control.cut], options.face_consistency)
    pose_dir = work_dir / control.cut / "pose"
    depth_dir = work_dir / control.cut / "depth"
    write_guides(control, pose_dir, depth_dir, options.width, options.height)
    return build_prompt(
        control,
        cut_prompt,
        pose_dir=str(pose_dir),
        depth_dir=str(depth_dir),
        face_image=face_name if cut_prompt.uses_sakura else None,
        options=options,
        present_files=present,
        plate_dir=plate_dir,
    )


def queue_cuts(
    base_url: str,
    script_path: Path,
    control_dir: Path,
    face_ref: Path | None,
    work_dir: Path,
    comfy_output: Path,
    comfy_input: Path,
    drive_out: Path,
    drive_models: Path,
    options: JobOptions,
    plate_dir: str | None = None,
    timeout_s: float = 3 * 60 * 60,
    opener: Any = urllib.request.urlopen,
) -> list[Path]:
    prompts = load_prompts(script_path)
    needs_face = any(item.uses_sakura for item in prompts.values())
    face_name = None
    if needs_face:
        if face_ref is None or not Path(face_ref).is_file():
            raise QueueError(f"サクラの顔画像が無い: {face_ref}")
        comfy_input.mkdir(parents=True, exist_ok=True)
        face_name = Path(face_ref).name
        shutil.copy2(face_ref, comfy_input / face_name)
    present = present_filenames(drive_models)
    if options.rife and not (Path(drive_models) / "rife" / "rife47.pth").is_file():
        raise QueueError("RIFE の重みが Drive の models/rife に無い。CPU ノートで落とす。")
    drive_out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for control_path in control_paths(control_dir):
        built = prepare_cut(script_path, control_path, work_dir, face_name, options, present, plate_dir)
        for note in built.notes:
            print(note, flush=True)
        print(f"queue {control_path.stem} frames={built.frames} fps={built.fps}", flush=True)
        prompt_id = post_prompt(base_url, built.prompt, opener=opener)
        print("prompt_id", prompt_id, flush=True)
        item = _wait(base_url, prompt_id, timeout_s, opener)
        saved = history_mp4(item, comfy_output)
        if saved is None:
            raise QueueError(f"{control_path.stem} の mp4 が履歴に無い")
        cut_id = load_control(control_path).cut
        target = drive_out / f"{cut_id}.mp4"
        shutil.copy2(saved, target)
        sidecar = drive_out / f"{cut_id}.job.json"
        sidecar.write_text(
            json.dumps(
                {
                    "cut": cut_id,
                    "frames": built.frames,
                    "fps": built.fps,
                    "unet": options.unet_name,
                    "steps": options.steps,
                    "cfg": options.cfg,
                    "shift": options.shift,
                    "distill": options.distill,
                    "source": saved.name,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print("WROTE", target, flush=True)
        written.append(target)
    return written
