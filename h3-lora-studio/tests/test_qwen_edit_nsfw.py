import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "h3-lora-studio" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from qwen_edit_nsfw import (  # noqa: E402
    API_NAME,
    DEFAULT_MANIFEST,
    DEFAULT_NEG,
    GUIDANCE,
    PORTRAIT,
    SPACES,
    STEPS,
    ZEROGPU_BUDGET,
    assert_out_outside_repo,
    crotch_only_prompt,
    infer_payload,
    infer_with_fallback,
    is_photoreal_path,
    is_quota_error,
    load_manifest,
    parse_mode,
    plan_frame,
    prompt_for,
    result_image_path,
    space_queue,
    target_wh,
    undress_futa_prompt,
)


def test_recipe_matches_proven_call():
    assert SPACES[0] == "Mk1227/Qwen-Image-Edit-NSFW"
    assert "ayooo123/Qwen-Image-Edit-NSFWpyyy" in SPACES
    assert "Cengizl/Qwen-Image-Edit-NSFW" in SPACES
    assert "metaloz/Qwen-Image-Edit-NSFWoz" in SPACES
    assert API_NAME == "/infer"
    assert PORTRAIT == (576, 1024)
    assert STEPS == 4
    assert GUIDANCE == 1.0
    assert ZEROGPU_BUDGET == 80


def test_target_wh_follows_source_aspect():
    assert target_wh((1008, 1792)) == (576, 1024)
    assert target_wh((1792, 1008)) == (1024, 576)


def test_quota_and_photoreal_guards():
    assert is_quota_error(RuntimeError("No GPU after 60s"))
    assert is_quota_error(RuntimeError("ZeroGPU runs limit"))
    assert not is_quota_error(TypeError("unexpected kw"))
    assert is_photoreal_path(Path("08-indoor-photoreal.jpg"))
    assert is_photoreal_path(Path("実写-shirt.jpg"))
    assert not is_photoreal_path(Path("01-stairs-harbor.jpg"))


def test_repo_jpeg_is_refused(tmp_path):
    with pytest.raises(SystemExit, match="JPGをリポジトリに入れるな"):
        assert_out_outside_repo(ROOT / "h3-lora-studio" / "oops.jpg")
    assert_out_outside_repo(tmp_path / "ok.jpg")


def test_prompts_keep_identity_and_futa_lock():
    undress = undress_futa_prompt("sage green sundress", "stone stairs, ocean")
    assert "Remove only the sage green sundress" in undress
    assert "stone stairs, ocean" in undress
    assert "20 centimeter" in undress
    assert "No testicles" in undress
    assert "over 21" in undress
    crotch = crotch_only_prompt("same high ponytail")
    assert "Only change the crotch" in crotch
    assert "same high ponytail" in crotch
    assert prompt_for("copy") == ""
    assert prompt_for("skip_photoreal") == ""
    with pytest.raises(ValueError, match="unhandled mode"):
        prompt_for("vaginal")  # type: ignore[arg-type]


def test_infer_payload_shape():
    payload = infer_payload(
        Path("/tmp/in.jpg"),
        "PROMPT",
        file_wrapper=lambda path: f"FILE:{path}",
    )
    assert payload["api_name"] == "/infer"
    assert payload["width"] == 576
    assert payload["height"] == 1024
    assert payload["num_inference_steps"] == 4
    assert payload["true_guidance_scale"] == 1.0
    assert payload["rewrite_prompt"] is False
    assert payload["zerogpu_budget"] == 80
    assert payload["images"][0]["image"] == "FILE:/tmp/in.jpg"
    assert payload["images"][0]["caption"] is None
    assert "testicles" in payload["negative_prompt"]


def test_space_fallback_skips_quota_then_succeeds():
    calls: list[str] = []

    class _Client:
        def __init__(self, space: str) -> None:
            self.space = space

        def predict(self, **_kwargs: object) -> list[list[dict[str, str]]]:
            calls.append(self.space)
            if self.space == SPACES[0]:
                raise RuntimeError("ZeroGPU runs limit")
            return [[{"image": "/tmp/out.webp"}]]

    space, result = infer_with_fallback(
        {"prompt": "x"},
        client_factory=lambda name: _Client(name),
    )
    assert calls[0] == SPACES[0]
    assert space == SPACES[1]
    assert result_image_path(result) == Path("/tmp/out.webp")


def test_space_queue_prefers_clone():
    queue = space_queue("metaloz/Qwen-Image-Edit-NSFWoz")
    assert queue[0] == "metaloz/Qwen-Image-Edit-NSFWoz"
    assert SPACES[0] in queue
    assert len(queue) == len(SPACES)


def test_manifest_plan_matches_shipped_frames():
    manifest = load_manifest(DEFAULT_MANIFEST)
    assert DEFAULT_MANIFEST.is_file()
    plans = [plan_frame(frame) for frame in manifest["frames"]]
    by_id = {row["id"]: row for row in plans}
    assert by_id["01"]["mode"] == "undress_futa"
    assert "sage green sundress" in by_id["01"]["prompt"]
    assert by_id["04"]["mode"] == "copy"
    assert by_id["04"]["prompt"] == ""
    assert by_id["08"]["mode"] == "skip_photoreal"
    assert by_id["08"]["photoreal"] is True
    assert DEFAULT_NEG in by_id["07"]["negative_prompt"]
    assert parse_mode("crotch_only") == "crotch_only"
    with pytest.raises(SystemExit, match="unknown mode"):
        parse_mode("explode")


def test_cli_check_and_plan(tmp_path):
    import subprocess

    script = SCRIPT_DIR / "qwen_edit_nsfw.py"
    check = subprocess.run(
        [sys.executable, str(script), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert check.returncode == 0, check.stdout + check.stderr
    assert "Mk1227/Qwen-Image-Edit-NSFW" in check.stdout
    plan = subprocess.run(
        [sys.executable, str(script), "--plan", "--manifest", str(DEFAULT_MANIFEST)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert plan.returncode == 0, plan.stdout + plan.stderr
    rows = [json.loads(line) for line in plan.stdout.splitlines() if line.strip()]
    assert [row["id"] for row in rows] == ["01", "02", "03", "04", "05", "06", "07", "08"]
    assert rows[-1]["mode"] == "skip_photoreal"

    refuse = subprocess.run(
        [
            sys.executable,
            str(script),
            "--in",
            str(tmp_path / "08-photoreal.jpg"),
            "--out",
            str(tmp_path / "nope.jpg"),
            "--photoreal",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert refuse.returncode != 0
    assert "実写の他人を全裸化するな" in refuse.stderr
