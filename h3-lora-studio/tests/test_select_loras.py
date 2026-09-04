import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "select_loras.py"
sys.path.insert(0, str(SCRIPT.parent))

from select_loras import SelectError, select_loras  # noqa: E402


def test_anal_penetration_i2v_stacks_enabled_only():
    data = select_loras(profile_name="anal_penetration", mode="i2v", prompt_arg="（シーン）")
    assert data["schema"] == "h3-lora-studio/v1"
    assert data["profile"] == "anal_penetration"
    assert data["mode"] == "i2v"
    assert data["turbo"] is False
    assert data["adults_only"] is True
    assert data["min_age"] >= 21
    assert data["first_frame_required"] is True
    ids = [row["id"] for row in data["stack"]]
    assert ids == ["h3-realism-people", "hmnsfw-aio-v2"]
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
    assert "r34l1sm" in data["prompt"]
    assert "anal" in data["prompt"].lower()
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


def test_cli_emits_json():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--profile", "anal_penetration", "--mode", "i2v", "--prompt", "（シーン）"],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(proc.stdout)
    assert data["turbo"] is False
    assert [row["id"] for row in data["stack"]] == ["h3-realism-people", "hmnsfw-aio-v2"]


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


def test_refuses_ref2va_on_i2v(tmp_path: Path):
    profile = json.loads((ROOT / "profiles" / "anal_penetration.json").read_text(encoding="utf-8"))
    profile["enabled"] = [{"id": "aftermidnight-ref2va", "strength": 1.0}]
    profile["disabled"] = [x for x in profile["disabled"] if x != "aftermidnight-ref2va"]
    path = tmp_path / "anal_penetration.json"
    path.write_text(json.dumps(profile), encoding="utf-8")
    try:
        select_loras(
            profile_name="anal_penetration",
            mode="i2v",
            profiles_dir=tmp_path,
        )
    except SelectError as exc:
        assert "ref2va" in str(exc)
    else:
        raise AssertionError("expected SelectError")
