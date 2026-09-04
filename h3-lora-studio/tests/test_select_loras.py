import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "select_loras.py"
sys.path.insert(0, str(SCRIPT.parent))

from select_loras import SelectError, list_situations, select_loras  # noqa: E402


def test_anal_penetration_i2v_stacks_enabled_only():
    data = select_loras(profile_name="anal_penetration", mode="i2v", prompt_arg="（シーン）")
    assert data["schema"] == "h3-lora-studio/v1"
    assert data["situation"] == "anal_penetration"
    assert data["mode"] == "i2v"
    assert data["turbo"] is False
    assert data["adults_only"] is True
    assert data["min_age"] >= 21
    assert data["first_frame_required"] is True
    ids = [row["id"] for row in data["stack"]]
    assert ids == ["hmnsfw-aio-v25", "anal-penetration-coachbate"]
    unload_ids = {row["id"] for row in data["unload"]}
    assert "minimax-h3-turbo-fl2v-4step" in unload_ids
    assert "minimax-h3-turbo-fl2v-8step" in unload_ids
    assert "aftermidnight-ref2va" in unload_ids
    assert "riding-pose-i2v" in unload_ids
    for row in data["unload"]:
        assert row["action"] == "unload"
        assert row["id"] not in ids
    assert data["sampler"]["sampler_name"] == "res_multistep"
    assert data["sampler"]["scheduler"] == "beta"
    assert data["sampler"]["steps"] >= 16
    assert data["canvas"]["aspect"] == "8:9"
    assert "anus" in data["prompt"].lower()
    assert "<Picture 1>" in data["prompt"]
    dumped = json.dumps(data)
    assert "XAI_API_KEY" not in dumped
    assert "HF_TOKEN" not in dumped
    assert "sk-" not in dumped
    nodes = data["comfy"]["lora_nodes"]
    assert len(nodes) == 2
    assert nodes[0]["class_type"] == "LoraLoaderModelOnly"
    assert nodes[0]["inputs"]["model"] == ["1", 0]
    assert nodes[1]["inputs"]["model"] == [nodes[0]["id"], 0]
    assert "minimax_h3_fl2v_turbo" not in json.dumps(nodes)


def test_anal_penetration_t2v_has_no_first_frame():
    data = select_loras(profile_name="anal_penetration", mode="t2v", prompt_arg="（シーン）")
    assert data["mode"] == "t2v"
    assert data["turbo"] is False
    assert data["first_frame_required"] is False
    assert data["canvas"]["aspect"] == "9:16"
    assert data["canvas"]["width"] == 576
    assert data["canvas"]["height"] == 1024
    assert [row["id"] for row in data["stack"]] == ["hmnsfw-aio-v25", "anal-penetration-coachbate"]
    assert "Picture 1" not in data["prompt"]
    assert "first_frame" not in data["prompt"].lower()
    assert "Vertical 9:16" in data["prompt"]
    unload_ids = {row["id"] for row in data["unload"]}
    assert "minimax-h3-turbo-fl2v-4step" in unload_ids
    assert "aftermidnight-ref2va" in unload_ids
    assert "riding-pose-i2v" in unload_ids


def test_situations_switch_loras_by_profile_and_mode():
    anal_t2v = [r["id"] for r in select_loras(profile_name="anal_penetration", mode="t2v")["stack"]]
    close_t2v = [r["id"] for r in select_loras(profile_name="anal_closeup", mode="t2v")["stack"]]
    oral_t2v = [r["id"] for r in select_loras(profile_name="oral", mode="t2v")["stack"]]
    futa_t2v = [r["id"] for r in select_loras(profile_name="futa_blowjob", mode="t2v")["stack"]]
    riding_i2v = [r["id"] for r in select_loras(profile_name="riding", mode="i2v")["stack"]]
    riding_t2v = [r["id"] for r in select_loras(profile_name="riding", mode="t2v")["stack"]]
    assert anal_t2v == ["hmnsfw-aio-v25", "anal-penetration-coachbate"]
    assert close_t2v == ["synth-pussy-h3", "anal-penetration-coachbate"]
    assert oral_t2v == ["blowjob-h3", "penis-lora-h3"]
    assert futa_t2v == ["futa-h3-v51", "penis-lora-h3", "blowjob-h3"]
    assert riding_i2v == ["h3-realism-people", "riding-pose-i2v"]
    assert riding_t2v == ["hmnsfw-aio-v25"]
    assert "riding-pose-i2v" not in riding_t2v
    listed = list_situations()
    ids = {row["id"] for row in listed["situations"]}
    assert {"anal_penetration", "anal_closeup", "oral", "riding", "futa_blowjob"} <= ids
    oral = next(row for row in listed["situations"] if row["id"] == "oral")
    assert oral["enabled"]["t2v"] == ["blowjob-h3", "penis-lora-h3"]
    assert oral["turbo"] is False


def test_cli_t2v_and_list():
    t2v = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--situation",
            "anal_penetration",
            "--mode",
            "t2v",
            "--prompt",
            "（シーン）",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(t2v.stdout)
    assert data["mode"] == "t2v"
    assert data["first_frame_required"] is False
    listed = subprocess.run(
        [sys.executable, str(SCRIPT), "--list"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(listed.stdout)
    assert payload["schema"] == "h3-lora-studio-situations/v1"
    assert any(row["id"] == "anal_penetration" for row in payload["situations"])


def test_cli_emits_json():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--profile", "anal_penetration", "--mode", "i2v", "--prompt", "（シーン）"],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(proc.stdout)
    assert data["turbo"] is False
    assert [row["id"] for row in data["stack"]] == ["hmnsfw-aio-v25", "anal-penetration-coachbate"]


def test_refuses_turbo_override():
    try:
        select_loras(
            profile_name="anal_penetration",
            mode="i2v",
            turbo_override=True,
        )
    except SelectError as exc:
        assert "Turbo" in str(exc)
    else:
        raise AssertionError("expected SelectError")


def test_t2v_refuses_picture1_prompt():
    try:
        select_loras(
            profile_name="anal_penetration",
            mode="t2v",
            prompt_arg="For the target video, <Picture 1> is fully referenced.",
        )
    except SelectError as exc:
        assert "t2v" in str(exc)
    else:
        raise AssertionError("expected SelectError")


def test_refuses_ref2va_on_i2v(tmp_path: Path):
    catalog = json.loads((ROOT / "catalog" / "loras.json").read_text(encoding="utf-8"))
    catalog["always_unload"] = []
    cat_path = tmp_path / "loras.json"
    cat_path.write_text(json.dumps(catalog), encoding="utf-8")
    profile = json.loads((ROOT / "profiles" / "anal_penetration.json").read_text(encoding="utf-8"))
    profile["enabled"] = [{"id": "aftermidnight-ref2va", "strength": 1.0}]
    profile["disabled"] = [x for x in profile["disabled"] if x != "aftermidnight-ref2va"]
    path = tmp_path / "anal_penetration.json"
    path.write_text(json.dumps(profile), encoding="utf-8")
    try:
        select_loras(
            profile_name="anal_penetration",
            mode="i2v",
            catalog_path=cat_path,
            profiles_dir=tmp_path,
        )
    except SelectError as exc:
        assert "ref2va" in str(exc)
    else:
        raise AssertionError("expected SelectError")
