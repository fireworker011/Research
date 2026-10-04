import importlib.util
import io
import json
import sys
from pathlib import Path

if importlib.util.find_spec("PIL") is not None:
    from PIL import Image
else:
    Image = None

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "minimaxh3" / "grokbot"))

from h3_colab_cli import orchestrate_commands
from h3_i2v_job import (
    DEFAULT_IMAGINE_PROMPT,
    SCHEMA,
    default_job,
    identity_still_bytes,
    resample_motion_24,
    vertical_r2v_canvas,
    ensure_drive_tree,
    forbidden_hits,
    load_job,
    move_job,
    next_bot_job,
    next_ready_job,
    save_job,
    set_status,
    stage_motion,
    stage_picture1,
    validate_job,
)
from h3_imagine import edit_payload, parse_image_url
from h3_i2v_runtime import generate_i2va
from h3_motion_graphics import resolve_motion_prompt, validate_motion_ad_prompt


def test_default_job_is_homage_and_clean():
    job = default_job(id="abc-001")
    assert job["schema"] == SCHEMA
    assert validate_job(job) == []
    assert "px.a8.net" not in json.dumps(job)
    p = resolve_motion_prompt(job["prompt"], duration_s=10)
    assert validate_motion_ad_prompt(p) == []
    assert "hoodie" in p.lower()
    assert job["imagine"]["model"] == "grok-imagine-image-2.0"
    assert "URL" in DEFAULT_IMAGINE_PROMPT or "url" in DEFAULT_IMAGINE_PROMPT.lower() or "No extra" in DEFAULT_IMAGINE_PROMPT


def test_job_rejects_affiliate_and_income():
    job = default_job(id="bad-1")
    job["prompt"] = "https://px.a8.net/svt/ejp?a8mat=x 稼げる"
    errs = validate_job(job)
    assert any("forbidden" in e for e in errs)
    assert forbidden_hits("月収100万") == ["月収"]


def test_status_and_inbox_queue(tmp_path):
    root = ensure_drive_tree(tmp_path / "drive")
    job = default_job(id="job-a")
    folder = root / "inbox" / job["id"]
    folder.mkdir(parents=True)
    (folder / "source.jpg").write_bytes(b"fake-jpeg")
    save_job(folder, job)
    assert next_ready_job(root) == folder
    set_status(job, "enhancing")
    set_status(job, "queued")
    save_job(folder, job)
    moved = move_job(folder, "queued", root)
    assert moved == root / "queued" / "job-a"
    assert load_job(moved)["status"] == "queued"


def test_move_job_parks_leftover_same_name(tmp_path):
    root = ensure_drive_tree(tmp_path / "drive")
    leftover = root / "running" / "dance-01"
    leftover.mkdir(parents=True)
    (leftover / "job.json").write_text("{}", encoding="utf-8")
    folder = root / "queued" / "dance-01"
    folder.mkdir()
    (folder / "job.json").write_text('{"id":"dance-01"}', encoding="utf-8")
    moved = move_job(folder, "running", root)
    assert moved == root / "running" / "dance-01"
    assert json.loads((moved / "job.json").read_text(encoding="utf-8"))["id"] == "dance-01"
    parked = list((root / "running").glob("dance-01.stopped-*"))
    assert len(parked) == 1
    assert parked[0].is_dir()


def test_stuck_running_job_in_queued_is_picked(tmp_path):
    root = ensure_drive_tree(tmp_path / "drive")
    leftover = root / "running" / "dance-01"
    leftover.mkdir(parents=True)
    old = default_job(id="dance-01", mode="r2v")
    old["status"] = "running"
    save_job(leftover, old)
    stuck = root / "queued" / "dance-01"
    stuck.mkdir()
    (stuck / "source.jpg").write_bytes(b"fake-jpeg")
    (stuck / "motion.mp4").write_bytes(b"fake-mp4")
    job = default_job(id="dance-01", mode="r2v")
    job["status"] = "running"
    save_job(stuck, job)
    assert next_bot_job(root, "r2v") == stuck


def test_newest_failed_job_is_retried(tmp_path):
    root = ensure_drive_tree(tmp_path / "drive")
    folder = root / "failed" / "dance-01"
    folder.mkdir(parents=True)
    job = default_job(id="dance-01", mode="r2v")
    job["status"] = "failed"
    job["error"] = "mp4 missing"
    save_job(folder, job)
    assert next_bot_job(root, "r2v") == folder


def test_stage_picture1_and_8_9(tmp_path):
    folder = tmp_path / "job"
    inp = tmp_path / "input"
    folder.mkdir()
    src = folder / "source.jpg"
    src.write_bytes(b"x" * 100)
    job = default_job(id="pic1")
    name = stage_picture1(folder, src, job, inp)
    assert name == "pic1.jpg"
    assert (folder / "picture1.jpg").is_file()
    assert (inp / "pic1.jpg").is_file()
    job["width"] = 1000
    assert any("8:9" in e or "multiples" in e for e in validate_job(job))


def test_imagine_payload_is_edit_not_secret(tmp_path):
    img = tmp_path / "source.jpg"
    img.write_bytes(b"\xff\xd8\xff" + b"x" * 50)
    payload = edit_payload(prompt=DEFAULT_IMAGINE_PROMPT, image_path=img)
    blob = json.dumps(payload)
    assert payload["model"] == "grok-imagine-image-2.0"
    assert payload["image"]["type"] == "image_url"
    assert "XAI_API_KEY" not in blob
    assert "Bearer" not in blob
    assert parse_image_url({"data": [{"url": "https://example.com/a.jpg"}]}) == "https://example.com/a.jpg"


def test_colab_orchestration_always_stops():
    cmds = orchestrate_commands("/tmp/h3_i2v_colab_main.py", gpu="A100", name="h3-i2v")
    assert cmds[0][:3] == ["new", "-s", "h3-i2v"]
    assert "--gpu" in cmds[0] and "A100" in cmds[0]
    assert cmds[1][0] == "drivemount"
    assert cmds[2][0] == "exec" and cmds[2][-1].endswith("h3_i2v_colab_main.py")
    assert cmds[-1] == ["stop", "-s", "h3-i2v"]


def test_generate_i2va_dry_run(tmp_path):
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
        filename_prefix="video/test",
        dry_run=True,
    )
    assert result["dry_run"] is True
    assert result["graph"]["20"]["class_type"] == "MiniMaxH3ImageToVideo"
    assert "first_frame" in result["graph"]["20"]["inputs"]


def test_drop_and_grokbot_dry_run(tmp_path):
    drive = tmp_path / "minimax-h3-comfyui"
    img = tmp_path / "draft.jpg"
    img.write_bytes(b"draft")
    import drop_job
    import run_i2v

    assert drop_job.main(["--drive", str(drive), "--image", str(img), "--slug", "coconala", "--no-imagine"]) == 0
    inbox = next((drive / "inbox").iterdir())
    assert (inbox / "job.json").is_file()
    job = json.loads((inbox / "job.json").read_text())
    assert job["status"] == "ready"
    assert job["imagine"]["enabled"] is False
    rc = run_i2v.run(["--drive", str(drive), "--dry-run", "--out", str(tmp_path / "out.mp4")])
    assert rc == 0
    queued = drive / "queued" / inbox.name
    assert (queued / "job.json").is_file()
    assert json.loads((queued / "job.json").read_text())["status"] == "queued"
    assert (queued / "picture1.jpg").is_file()


def test_orphan_still_and_idle_and_watch(tmp_path):
    from h3_i2v_job import adopt_orphan_stills, ensure_drive_tree
    import run_i2v

    root = ensure_drive_tree(tmp_path / "drive")
    (root / "inbox" / "a.jpg").write_bytes(b"a")
    made = adopt_orphan_stills(root)
    assert len(made) == 1
    assert not (root / "inbox" / "a.jpg").exists()
    (root / "inbox" / "b.jpg").write_bytes(b"b")
    assert run_i2v.run(["--drive", str(root), "--dry-run", "--watch", "--max-jobs", "2", "--interval", "1"]) == 0
    assert len(list((root / "queued").iterdir())) == 2
    assert run_i2v.run(["--drive", str(root), "--dry-run"]) == 0
    skill = Path(__file__).resolve().parents[1] / ".cursor" / "skills" / "h3-i2v-grokbot" / "SKILL.md"
    assert "一度きり" in skill.read_text(encoding="utf-8")
    assert "idle" in skill.read_text(encoding="utf-8")


def test_example_job_file_has_no_secrets():
    path = Path(__file__).resolve().parents[1] / "minimaxh3" / "grokbot" / "job.example.json"
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    assert data["schema"] == SCHEMA
    assert "XAI" not in raw
    assert "px.a8.net" not in raw
    assert validate_job(data) == []
    skill = Path(__file__).resolve().parents[1] / ".cursor" / "skills" / "h3-i2v-grokbot" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "colab stop" in text
    assert "I2VA" in text
    assert "px.a8.net" in text or "アフィ" in text


def test_turnaround_sheet_keeps_the_front_panel_only() -> None:
    if Image is None:
        return
    image = Image.new("RGB", (300, 100), (255, 0, 0))
    for x in range(100, 200):
        for y in range(100):
            image.putpixel((x, y), (0, 255, 0))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    panel = Image.open(io.BytesIO(identity_still_bytes(buf.getvalue())))
    assert panel.size == (100, 100)
    red, green, _blue = panel.getpixel((10, 10))
    assert red > green + 40


def test_square_still_is_not_cropped() -> None:
    if Image is None:
        return
    image = Image.new("RGB", (80, 100), (1, 2, 3))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    raw = buf.getvalue()
    assert identity_still_bytes(raw) == raw


def test_stage_motion_keeps_bytes_when_resample_fails(tmp_path: Path) -> None:
    folder = tmp_path / "job"
    folder.mkdir()
    src = folder / "clip.mov"
    src.write_bytes(b"not-a-video")
    job = {"id": "dance-01"}
    name = stage_motion(folder, src, job, tmp_path / "input")
    assert name == "dance-01.mp4"
    assert (folder / "motion.mp4").read_bytes() == b"not-a-video"
    assert (tmp_path / "input" / name).read_bytes() == b"not-a-video"


def test_old_square_r2v_canvas_becomes_vertical() -> None:
    assert vertical_r2v_canvas(768, 864, 95) == (768, 1344)
    assert vertical_r2v_canvas(768, 864, 40) == (576, 1024)
    assert vertical_r2v_canvas(576, 1024, 95) == (576, 1024)
