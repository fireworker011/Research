import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "minimaxh3" / "grokbot"))

from h3_colab_cli import orchestrate_commands
from h3_i2v_job import (
    DEFAULT_IMAGINE_PROMPT,
    SCHEMA,
    default_job,
    ensure_drive_tree,
    forbidden_hits,
    load_job,
    move_job,
    next_ready_job,
    save_job,
    set_status,
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
    assert job["backend"] == "fal-max"
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


def test_fal_i2v_payload_keeps_prompt_and_hides_key(tmp_path):
    from h3_fal_max import i2v_payload, is_fal_backend, payload_log, resolve_backend

    img = tmp_path / "p.jpg"
    img.write_bytes(b"\xff\xd8\xff" + b"x" * 50)
    payload = i2v_payload(prompt="hoodie desk cyan UI 広告", image_path=img, duration_s=10)
    blob = json.dumps(payload)
    assert payload["duration"] == 10
    assert payload["prompt_expansion_mode"] == "disabled"
    assert payload["resolution"] == "768P"
    assert payload["image_url"].startswith("data:image/jpeg;base64,")
    assert "FAL_KEY" not in blob
    assert "px.a8.net" not in blob
    assert i2v_payload(prompt="x", image_path=img, duration_s=3)["duration"] == 5
    assert i2v_payload(prompt="x", image_path=img, duration_s=99)["duration"] == 15
    assert payload_log(payload)["image_url"].startswith("data-uri:")
    assert is_fal_backend(resolve_backend("", {"backend": "fal-max"}))
    assert resolve_backend("", None) == "fal-max"
    assert resolve_backend("colab", {"backend": "fal-max"}) == "colab"


def test_fal_generate_i2v_mocked(tmp_path, monkeypatch):
    from h3_fal_max import generate_i2v

    img = tmp_path / "p.jpg"
    img.write_bytes(b"\xff\xd8\xff" + b"x" * 50)
    dest = tmp_path / "out.mp4"
    captured = {}

    def opener(req, timeout=None):
        captured["url"] = req.full_url
        captured["auth"] = req.get_header("Authorization")
        captured["body"] = json.loads(req.data.decode())

        class R:
            def read(self):
                return json.dumps({"video": {"url": "https://cdn.example/v.mp4"}}).encode()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return R()

    monkeypatch.setattr("h3_fal_max.download_to", lambda url, dest: dest.write_bytes(b"m" * 2000) or dest)
    generate_i2v(img, dest, prompt="hoodie 広告", key="test-key", opener=opener)
    assert captured["url"].endswith("/minimax/h3-max/image-to-video")
    assert captured["auth"] == "Key test-key"
    assert captured["body"]["prompt_expansion_mode"] == "disabled"
    assert captured["body"]["duration"] == 10
    assert dest.is_file()


def test_drop_and_grokbot_dry_run(tmp_path, capsys):
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
    assert job["backend"] == "fal-max"
    rc = run_i2v.run(["--drive", str(drive), "--dry-run", "--out", str(tmp_path / "out.mp4")])
    assert rc == 0
    done = drive / "done" / inbox.name
    assert (done / "job.json").is_file()
    saved = json.loads((done / "job.json").read_text())
    assert saved["status"] == "done"
    assert saved["backend"] == "fal-max"
    assert (done / "picture1.jpg").is_file()
    assert (drive / "output" / f"{saved['id']}.mp4").is_file()
    assert (tmp_path / "out.mp4").is_file()
    out = capsys.readouterr().out
    assert "fal.run/minimax/h3-max/image-to-video" in out
    assert "colab new" not in out
    assert "FAL_KEY" not in json.dumps(saved)


def test_colab_backend_dry_run_prints_colab(tmp_path, capsys):
    drive = tmp_path / "minimax-h3-comfyui"
    img = tmp_path / "draft.jpg"
    img.write_bytes(b"draft")
    import drop_job
    import run_i2v

    assert drop_job.main(["--drive", str(drive), "--image", str(img), "--slug", "coconala", "--no-imagine"]) == 0
    inbox = next((drive / "inbox").iterdir())
    rc = run_i2v.run(["--drive", str(drive), "--dry-run", "--backend", "colab"])
    assert rc == 0
    queued = drive / "queued" / inbox.name
    assert (queued / "job.json").is_file()
    assert json.loads((queued / "job.json").read_text())["status"] == "queued"
    out = capsys.readouterr().out
    assert "colab" in out
    assert "dry-run colab commands" in out


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
    assert len([p for p in (root / "done").iterdir() if p.is_dir()]) == 2
    assert not list((root / "queued").iterdir())
    assert run_i2v.run(["--drive", str(root), "--dry-run"]) == 0
    skill = Path(__file__).resolve().parents[1] / ".cursor" / "skills" / "h3-i2v-grokbot" / "SKILL.md"
    assert "一度きり" in skill.read_text(encoding="utf-8")
    assert "idle" in skill.read_text(encoding="utf-8")


def test_example_job_file_has_no_secrets():
    path = Path(__file__).resolve().parents[1] / "minimaxh3" / "grokbot" / "job.example.json"
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    assert data["schema"] == SCHEMA
    assert data["backend"] == "fal-max"
    assert "XAI" not in raw
    assert "FAL_KEY" not in raw
    assert "px.a8.net" not in raw
    assert validate_job(data) == []
    skill = Path(__file__).resolve().parents[1] / ".cursor" / "skills" / "h3-i2v-grokbot" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "fal-max" in text
    assert "FAL_KEY" in text
    assert "colab stop" in text
    assert "I2VA" in text
    assert "px.a8.net" in text or "アフィ" in text
