import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "minimaxh3"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "minimaxh3" / "grokbot"))

from h3_i2v_job import (
    GROKBOT_DURATION_S,
    adopt_orphan_prompts,
    adopt_orphan_r2v_folders,
    adopt_orphan_stills,
    default_job,
    ensure_drive_tree,
    next_ready_job,
    save_job,
    validate_job,
)
from h3_i2v_runtime import generate_i2va, generate_r2v, generate_t2v
from h3_r2v_core import frames, grokbot_r2v_retry_plans, r2v_download_jobs
from h3_t2v import CANVAS_9_16, resolve_t2v_prompt, t2v_length_plans


def test_modes_default_to_10s():
    i2v = default_job(id="i2v-10")
    t2v = default_job(id="t2v-10", mode="t2v")
    r2v = default_job(id="r2v-10", mode="r2v")
    assert i2v["mode"] == "i2v"
    assert t2v["mode"] == "t2v"
    assert r2v["mode"] == "r2v"
    assert i2v["duration_s"] == GROKBOT_DURATION_S == 10
    assert t2v["duration_s"] == 10
    assert r2v["duration_s"] == 10
    assert (t2v["width"], t2v["height"]) == CANVAS_9_16
    assert validate_job(i2v) == []
    assert validate_job(t2v) == []
    assert validate_job(r2v) == []
    blob = json.dumps(i2v) + json.dumps(t2v) + json.dumps(r2v)
    assert "px.a8.net" not in blob
    assert "a8mat=" not in blob


def test_next_ready_job_does_not_steal_other_modes(tmp_path):
    root = ensure_drive_tree(tmp_path / "drive")
    i2v = default_job(id="keep-i2v", mode="i2v")
    t2v = default_job(id="keep-t2v", mode="t2v")
    f_i = root / "inbox" / i2v["id"]
    f_t = root / "inbox" / t2v["id"]
    f_i.mkdir(parents=True)
    f_t.mkdir(parents=True)
    (f_i / "source.jpg").write_bytes(b"still")
    save_job(f_i, i2v)
    save_job(f_t, t2v)
    assert next_ready_job(root, mode="t2v") == f_t
    assert next_ready_job(root, mode="i2v") == f_i
    assert next_ready_job(root, mode="r2v") is None


def test_orphan_txt_is_t2v_jpg_is_i2v(tmp_path):
    root = ensure_drive_tree(tmp_path / "drive")
    (root / "inbox" / "hook.txt").write_text("Quiet desk, navy hoodie, 広告 in the corner.\n", encoding="utf-8")
    (root / "inbox" / "face.jpg").write_bytes(b"jpg")
    made_t = adopt_orphan_prompts(root)
    made_i = adopt_orphan_stills(root)
    assert len(made_t) == 1
    assert len(made_i) == 1
    assert json.loads((made_t[0] / "job.json").read_text())["mode"] == "t2v"
    assert json.loads((made_i[0] / "job.json").read_text())["mode"] == "i2v"


def test_orphan_r2v_folder(tmp_path):
    root = ensure_drive_tree(tmp_path / "drive")
    folder = root / "inbox" / "pair-1"
    folder.mkdir(parents=True)
    (folder / "cast.jpg").write_bytes(b"still")
    (folder / "dance.mp4").write_bytes(b"mp4")
    made = adopt_orphan_r2v_folders(root)
    assert len(made) == 1
    job = json.loads((folder / "job.json").read_text())
    assert job["mode"] == "r2v"
    assert (folder / "source.jpg").is_file()
    assert (folder / "motion.mp4").is_file()
    assert validate_job(job, folder=folder) == []


def test_generate_t2v_dry_run_is_10s_without_first_frame(tmp_path):
    comfy = tmp_path / "ComfyUI"
    (comfy / "models" / "diffusion_models").mkdir(parents=True)
    result = generate_t2v(
        prompt=resolve_t2v_prompt(""),
        comfy_dir=comfy,
        width=576,
        height=1024,
        duration_s=10,
        seed=1,
        steps=4,
        use_lora=True,
        lora_strength=1.0,
        filename_prefix="video/t2v",
        dry_run=True,
    )
    g = result["graph"]
    assert g["20"]["class_type"] == "MiniMaxH3ImageToVideo"
    assert "first_frame" not in g["20"]["inputs"]
    assert g["20"]["inputs"]["length"] == frames(10)
    assert result["plan"]["duration_s"] == 10
    assert t2v_length_plans(10) == [10.0, 5.0]


def test_generate_r2v_dry_run_keeps_video_and_tries_10s(tmp_path):
    comfy = tmp_path / "ComfyUI"
    (comfy / "models" / "diffusion_models").mkdir(parents=True)
    (comfy / "models" / "loras").mkdir(parents=True)
    prompt = (
        "ROLE LOCK (mandatory):\n"
        "REFERENCE VIDEO = MOTION ONLY.\n"
        "Identity for character 1 is locked to <Picture 1> (picture1.jpg).\n"
        "MOTION ONLY from <Video 1> (motion.mp4): body action, camera, timing.\n"
    )
    result = generate_r2v(
        img_names=["picture1.jpg"],
        vid_names=["motion.mp4"],
        prompt=prompt,
        comfy_dir=comfy,
        width=768,
        height=864,
        duration_s=10,
        seed=1,
        steps=4,
        use_lora=True,
        lora_strength=1.0,
        filename_prefix="video/r2v",
        dry_run=True,
        vram_gb=39.5,
    )
    g = result["graph"]
    assert g["20"]["class_type"] == "MiniMaxH3ReferenceToVideo"
    assert "ref_videos.ref_video_0" in g["20"]["inputs"]
    assert g["190"]["class_type"] == "VHS_LoadVideo"
    assert result["plan"]["duration_s"] == 10
    plans = grokbot_r2v_retry_plans(
        duration_s=10, width=768, height=864, n_images=1, vram_gb=39.5
    )
    assert plans[0]["duration_s"] == 10
    names = " ".join(p.name.lower() for _u, p in r2v_download_jobs("/tmp/r2v-models"))
    assert "ref2va" in names
    assert "ref2v_turbo" in names or "ref2v" in names
    assert "fl2va" not in names


def test_generate_i2v_still_requires_first_frame(tmp_path):
    from h3_motion_graphics import resolve_motion_prompt

    comfy = tmp_path / "ComfyUI"
    (comfy / "models" / "diffusion_models").mkdir(parents=True)
    prompt = resolve_motion_prompt("", duration_s=10)
    result = generate_i2va(
        first_image="picture1.jpg",
        prompt=prompt,
        comfy_dir=comfy,
        width=768,
        height=864,
        duration_s=10,
        seed=1,
        steps=4,
        use_lora=True,
        lora_strength=1.0,
        filename_prefix="video/i2v",
        dry_run=True,
    )
    assert "first_frame" in result["graph"]["20"]["inputs"]


def test_drop_and_run_each_mode_dry(tmp_path):
    import drop_job
    import run_i2v
    import run_r2v
    import run_t2v

    drive = tmp_path / "minimax-h3-comfyui"
    img = tmp_path / "draft.jpg"
    img.write_bytes(b"draft")
    vid = tmp_path / "motion.mp4"
    vid.write_bytes(b"fake-mp4")
    prompt = tmp_path / "p.txt"
    prompt.write_text("Vertical 9:16 photoreal desk scene. 広告. No URL.\n", encoding="utf-8")

    assert drop_job.main(["--drive", str(drive), "--mode", "t2v", "--prompt-file", str(prompt)]) == 0
    assert drop_job.main(["--drive", str(drive), "--mode", "i2v", "--image", str(img), "--no-imagine"]) == 0
    assert drop_job.main(
        ["--drive", str(drive), "--mode", "r2v", "--image", str(img), "--video", str(vid), "--no-imagine"]
    ) == 0

    assert run_t2v.run(["--drive", str(drive), "--dry-run"]) == 0
    assert run_i2v.run(["--drive", str(drive), "--dry-run"]) == 0
    assert run_r2v.run(["--drive", str(drive), "--dry-run"]) == 0
    queued = list((drive / "queued").iterdir())
    assert len(queued) == 3
    modes = {json.loads((p / "job.json").read_text())["mode"] for p in queued}
    assert modes == {"t2v", "i2v", "r2v"}
    r2v_folder = next(p for p in queued if json.loads((p / "job.json").read_text())["mode"] == "r2v")
    assert (r2v_folder / "motion.mp4").is_file()
    t2v_job = json.loads(
        next(p for p in queued if json.loads((p / "job.json").read_text())["mode"] == "t2v").joinpath("job.json").read_text()
    )
    assert t2v_job["duration_s"] == 10
    assert t2v_job["status"] == "queued"


def test_idle_when_wrong_mode_inbox(tmp_path):
    import run_t2v

    root = ensure_drive_tree(tmp_path / "drive")
    (root / "inbox" / "only.jpg").write_bytes(b"x")
    adopt_orphan_stills(root)
    assert run_t2v.run(["--drive", str(root), "--dry-run"]) == 0
    assert not (root / "queued").exists() or not any((root / "queued").iterdir())


def test_skills_and_docs_name_three_agents():
    root = Path(__file__).resolve().parents[1]
    i2v = (root / ".cursor" / "skills" / "h3-i2v-grokbot" / "SKILL.md").read_text(encoding="utf-8")
    t2v = (root / ".cursor" / "skills" / "h3-t2v-grokbot" / "SKILL.md").read_text(encoding="utf-8")
    r2v = (root / ".cursor" / "skills" / "h3-r2v-grokbot" / "SKILL.md").read_text(encoding="utf-8")
    docs = (root / "minimaxh3" / "GROKBOT.md").read_text(encoding="utf-8")
    assert "run_i2v.py" in i2v and "I2VA" in i2v
    assert "run_t2v.py" in t2v and "first_frame" in t2v
    assert "run_r2v.py" in r2v and "ref2va" in r2v
    assert "ponz" in r2v.lower()
    assert "run_t2v.py" in docs and "run_r2v.py" in docs
    assert "minimax_h3_t2v_bot.ipynb" in docs
    assert "minimax_h3_i2v_bot.ipynb" in docs
    assert "minimax_h3_r2v_bot.ipynb" in docs
    for text in (i2v, t2v, r2v, docs):
        assert "px.a8.net" not in text
        assert "colab stop" in text or "stop" in text
        assert "投稿" in text
    for name in ("job.example.json", "job.t2v.example.json", "job.r2v.example.json"):
        raw = (root / "minimaxh3" / "grokbot" / name).read_text(encoding="utf-8")
        data = json.loads(raw)
        assert data["duration_s"] == 10
        assert "XAI" not in raw
        assert "px.a8.net" not in raw
        assert validate_job(data) == []


def test_bot_colabs_are_one_cell_and_mode_locked():
    from h3_i2v_phone import bot_colab_url

    root = Path(__file__).resolve().parents[1]
    for mode, needle in (
        ("t2v", "first_frame"),
        ("i2v", "first_frame"),
        ("r2v", "ref2va"),
    ):
        url = bot_colab_url(mode)
        assert url.endswith(f"minimax_h3_{mode}_bot.ipynb")
        assert "cursor/minimax-h3-motion-identity-e959" in url
        nb = json.loads((root / f"minimax_h3_{mode}_bot.ipynb").read_text(encoding="utf-8"))
        codes = [c for c in nb["cells"] if c["cell_type"] == "code"]
        assert len(codes) == 1
        src = "".join(codes[0].get("source") or [])
        compile(src, f"{mode}_bot.py", "exec")
        assert f'MODE = "{mode}"' in src
        assert "H3_BOT_IDLE_OK" in src
        assert "bot_prepare" in src
        assert "px.a8.net" not in src
        blob = "\n".join("".join(c.get("source") or []) for c in nb["cells"])
        assert "10秒" in blob or "10" in blob
        if mode == "t2v":
            assert "first_frame" in blob
        if mode == "r2v":
            assert "ref2va" in blob.lower() or "ref2va" in blob
        assert (root / "minimaxh3" / f"minimax_h3_{mode}_bot.ipynb").is_file()


def test_bot_prepare_queues_and_idles(tmp_path, monkeypatch):
    import os
    from h3_colab_main import bot_prepare, main

    root = ensure_drive_tree(tmp_path / "drive")
    monkeypatch.setenv("H3_DRIVE_ROOT", str(root))
    monkeypatch.setenv("H3_BOT_IDLE_OK", "1")
    monkeypatch.setenv("H3_DRY_RUN", "1")
    monkeypatch.setenv("H3_JOB_MODE", "t2v")
    bot_prepare("t2v", root)
    assert main() == 0
    (root / "inbox" / "hook.txt").write_text("Quiet desk, navy hoodie, 広告 in the corner.\n", encoding="utf-8")
    (root / "inbox" / "face.jpg").write_bytes(b"jpg")
    bot_prepare("t2v", root)
    queued = list((root / "queued").iterdir()) if (root / "queued").exists() else []
    assert len(queued) == 1
    job = json.loads((queued[0] / "job.json").read_text(encoding="utf-8"))
    assert job["mode"] == "t2v"
    assert job["status"] == "queued"
    assert job["duration_s"] == 10
    bot_prepare("i2v", root)
    i2v_q = [p for p in (root / "queued").iterdir() if json.loads((p / "job.json").read_text())["mode"] == "i2v"]
    assert len(i2v_q) == 1
    assert (i2v_q[0] / "picture1.jpg").is_file()

