import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_i2v_phone import (
    BRANCH,
    DEFAULT_FIRST_IMAGE,
    I2V_WEIGHTS,
    TURBO_LORA_NAME,
    TURBO_LORA_URL,
    collect_output_videos,
    colab_open_url,
    default_canvas_for_vram,
    github_raw,
    gpu_ok_for_i2v,
    i2v_download_jobs,
    i2v_jobs_are_fl2va_only,
    is_auto_image_name,
    missing_weight_files,
    newest_image,
    newest_mp4,
    ref_image_url,
    stage_image_into_input,
)


def test_colab_and_raw_urls_use_working_branch():
    url = colab_open_url()
    assert "colab.research.google.com/github/fireworker011/Research/blob/" in url
    assert BRANCH in url
    assert url.endswith("minimax_h3_i2v_phone.ipynb")
    assert github_raw("colab/h3_i2v_phone.py").endswith("/colab/h3_i2v_phone.py")
    assert "coconala_creator_ref.jpg" in ref_image_url()


def test_i2v_downloads_skip_ref2va():
    jobs = i2v_download_jobs("/tmp/h3-models")
    names = [p.name for _, p in jobs]
    assert any("fl2va" in n for n in names)
    assert TURBO_LORA_NAME in names
    assert i2v_jobs_are_fl2va_only(jobs)
    assert not any("ref2va" in n or "ref2v" in n for n in names)
    assert len(I2V_WEIGHTS) == 4
    assert TURBO_LORA_URL.startswith("https://huggingface.co/lightx2v/")


def test_missing_weight_files(tmp_path):
    models = tmp_path / "models"
    assert len(missing_weight_files(models)) == 5
    dest = models / "loras" / TURBO_LORA_NAME
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"x" * 2_000_000)
    left = missing_weight_files(models)
    assert TURBO_LORA_NAME not in left
    assert len(left) == 4


def test_auto_image_and_newest(tmp_path):
    assert is_auto_image_name("")
    assert is_auto_image_name("AUTO")
    assert is_auto_image_name("最新")
    assert not is_auto_image_name(DEFAULT_FIRST_IMAGE)
    folder = tmp_path / "input"
    folder.mkdir()
    a = folder / "old.jpg"
    b = folder / "new.png"
    a.write_bytes(b"old")
    b.write_bytes(b"new")
    import os

    os.utime(a, (1, 1))
    os.utime(b, (100, 100))
    assert newest_image([folder]) == b
    staged = stage_image_into_input(b, tmp_path / "comfy-input")
    assert staged == "new.png"
    assert (tmp_path / "comfy-input" / "new.png").is_file()


def test_collect_output_videos_and_newest_mp4(tmp_path):
    out = tmp_path / "output"
    sub = out / "video"
    sub.mkdir(parents=True)
    mp4 = sub / "h3_i2va_coconala_ad_00001.mp4"
    mp4.write_bytes(b"fake")
    entry = {
        "outputs": {
            "29": {
                "videos": [
                    {"filename": mp4.name, "subfolder": "video", "type": "output"},
                ]
            }
        }
    }
    paths = collect_output_videos(entry, out)
    assert paths == [mp4]
    assert newest_mp4(out) == mp4


def test_canvas_stays_8_9_on_40gb():
    assert default_canvas_for_vram(40) == (768, 864)
    assert default_canvas_for_vram(80) == (768, 864)
    assert default_canvas_for_vram(15) == (512, 576)
    assert gpu_ok_for_i2v(40)
    assert not gpu_ok_for_i2v(8)


def _phone_nb():
    root = Path(__file__).resolve().parents[1]
    return json.loads((root / "minimax_h3_i2v_phone.ipynb").read_text(encoding="utf-8"))


def test_phone_notebook_is_three_i2v_cells():
    nb = _phone_nb()
    codes = [c for c in nb["cells"] if c["cell_type"] == "code"]
    assert len(codes) == 3
    blob = "\n".join("".join(c.get("source") or []) for c in nb["cells"])
    assert "MiniMaxH3ImageToVideo" in blob
    assert "MiniMaxH3ReferenceToVideo" not in blob
    assert "WanAnimateToVideo" not in blob
    assert "loca.lt" not in blob
    assert "ref2va" not in blob.lower()
    assert "px.a8.net" not in blob
    assert "a8mat=" not in blob
    assert "稼げる" not in blob
    assert DEFAULT_FIRST_IMAGE in blob
    assert "display(Video" in blob
    assert "MODE=both" not in blob
    for i, cell in enumerate(codes):
        src = "".join(cell.get("source") or [])
        assert not src.strip().startswith("%%")
        compile(src, f"phone_cell{i+1}.py", "exec")


def test_phone_generate_cell_keeps_i2va_invariants():
    nb = _phone_nb()
    gen = next(
        "".join(c.get("source") or [])
        for c in nb["cells"]
        if c["cell_type"] == "code" and "I2VA" in "".join(c.get("source") or [])
    )
    assert "build_i2va_graph" in gen
    assert "i2va_retry_plans" in gen
    assert "first_image" in gen
    assert "WIDTH = 768" in gen
    assert "HEIGHT = 864" in gen
    assert "DURATION_S = 10" in gen
    assert "USE_LORA = True" in gen
    assert "validate_motion_ad_prompt" in gen
    assert "is_auto_image_name" in gen
    assert 'FIRST_IMAGE = "coconala_creator_ref.jpg"' in gen
