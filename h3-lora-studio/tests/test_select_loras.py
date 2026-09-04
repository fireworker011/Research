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
    assert ids == ["anal-penetration-coachbate", "synth-pussy-h3"]
    assert [row["role"] for row in data["stack"]] == ["act", "helper"]
    assert data["stack"][0]["strength_model"] == 0.85
    assert data["stack"][1]["strength_model"] == 0.55
    unload_ids = {row["id"] for row in data["unload"]}
    assert "minimax-h3-turbo-fl2v-4step" in unload_ids
    assert "larry-v4" in unload_ids
    assert "aftermidnight-ref2va" in unload_ids
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
    assert "minimax_h3_fl2v_turbo" not in json.dumps(data["comfy"]["lora_nodes"])


def test_anal_penetration_t2v_has_no_first_frame():
    data = select_loras(profile_name="anal_penetration", mode="t2v", prompt_arg="（シーン）")
    assert data["mode"] == "t2v"
    assert data["turbo"] is False
    assert data["first_frame_required"] is False
    assert data["canvas"]["aspect"] == "9:16"
    assert [row["id"] for row in data["stack"]] == ["anal-penetration-coachbate", "synth-pussy-h3"]
    assert "Picture 1" not in data["prompt"]
    assert "first_frame" not in data["prompt"].lower()


def test_situations_switch_loras_by_profile_and_mode():
    anal_t2v = [r["id"] for r in select_loras(profile_name="anal_penetration", mode="t2v")["stack"]]
    close_t2v = [r["id"] for r in select_loras(profile_name="anal_closeup", mode="t2v")["stack"]]
    oral_t2v = select_loras(profile_name="oral", mode="t2v")
    futa_t2v = [r["id"] for r in select_loras(profile_name="futa_blowjob", mode="t2v")["stack"]]
    general = select_loras(profile_name="general_sex", mode="t2v")
    preview = select_loras(profile_name="preview", mode="t2v")
    assert anal_t2v == ["anal-penetration-coachbate", "synth-pussy-h3"]
    assert close_t2v == ["synth-pussy-h3", "larry-v4", "cinema-dy"]
    assert [r["id"] for r in oral_t2v["stack"]] == ["blowjob-h3", "penis-lora-h3", "larry-v4"]
    assert oral_t2v["stack"][0]["strength_model"] == 0.75
    assert oral_t2v["stack"][2]["strength_model"] == 0.7
    assert oral_t2v["sampler"]["steps"] == 8
    assert oral_t2v["turbo"] is True
    assert futa_t2v == ["blowjob-h3", "penis-lora-h3", "larry-v4"]
    assert "futa-h3-v51" not in futa_t2v
    assert [r["id"] for r in general["stack"]] == ["hmnsfw-aio-v25", "minimax-h3-turbo-fl2v-4step"]
    assert general["stack"][1]["strength_model"] == 0.5
    assert general["sampler"]["steps"] == 12
    assert preview["sampler"]["steps"] == 4
    assert preview["stack"][1]["strength_model"] == 1.0
    listed = list_situations()
    ids = {row["id"] for row in listed["situations"]}
    assert {"anal_penetration", "anal_closeup", "oral", "futa_blowjob", "general_sex", "preview", "sfw_daily", "sfw_preview", "sfw_audio"} <= ids
    oral = next(row for row in listed["situations"] if row["id"] == "oral")
    assert oral["enabled"]["t2v"] == ["blowjob-h3", "penis-lora-h3", "larry-v4"]
    assert oral["turbo"] is True
    anal = next(row for row in listed["situations"] if row["id"] == "anal_penetration")
    assert anal["turbo"] is False
    daily = next(row for row in listed["situations"] if row["id"] == "sfw_daily")
    assert daily["nsfw"] is False
    assert daily["enabled"]["t2v"] == ["larry-v4", "cinema-dy"]


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
    assert [row["id"] for row in data["stack"]] == ["anal-penetration-coachbate", "synth-pussy-h3"]


def test_refuses_turbo_override():
    try:
        select_loras(
            profile_name="anal_penetration",
            mode="i2v",
            turbo_override=True,
        )
    except SelectError as exc:
        assert "turbo" in str(exc).lower() or "CoachBate" in str(exc)
    else:
        raise AssertionError("expected SelectError")


def test_refuses_cinema_plus_helper(tmp_path: Path):
    catalog = json.loads((ROOT / "catalog" / "loras.json").read_text(encoding="utf-8"))
    cat_path = tmp_path / "loras.json"
    cat_path.write_text(json.dumps(catalog), encoding="utf-8")
    profile = json.loads((ROOT / "profiles" / "oral.json").read_text(encoding="utf-8"))
    profile["stack_plan"]["cinema"] = {"id": "cinema-dy", "strength": 0.4}
    (tmp_path / "oral.json").write_text(json.dumps(profile), encoding="utf-8")
    try:
        select_loras(profile_name="oral", mode="t2v", catalog_path=cat_path, profiles_dir=tmp_path)
    except SelectError as exc:
        assert "cinema" in str(exc).lower() or "helper" in str(exc).lower()
    else:
        raise AssertionError("expected SelectError")


def test_refuses_larry_plus_lightx2v(tmp_path: Path):
    catalog = json.loads((ROOT / "catalog" / "loras.json").read_text(encoding="utf-8"))
    cat_path = tmp_path / "loras.json"
    cat_path.write_text(json.dumps(catalog), encoding="utf-8")
    profile = json.loads((ROOT / "profiles" / "oral.json").read_text(encoding="utf-8"))
    profile["stack_plan"]["turbo"] = {"id": "larry-v4", "strength": 0.7}
    profile["stack_plan"]["cinema"] = {"id": "minimax-h3-turbo-fl2v-4step", "strength": 1.0}
    del profile["stack_plan"]["helper"]
    profile["disabled"] = [x for x in profile["disabled"] if x != "minimax-h3-turbo-fl2v-4step"]
    (tmp_path / "oral.json").write_text(json.dumps(profile), encoding="utf-8")
    try:
        select_loras(profile_name="oral", mode="t2v", catalog_path=cat_path, profiles_dir=tmp_path)
    except SelectError as exc:
        msg = str(exc).lower()
        assert "larry" in msg or "lightx2v" in msg or "turbo family" in msg
    else:
        raise AssertionError("expected SelectError")


def test_refuses_cinema_above_point_six(tmp_path: Path):
    catalog = json.loads((ROOT / "catalog" / "loras.json").read_text(encoding="utf-8"))
    cat_path = tmp_path / "loras.json"
    cat_path.write_text(json.dumps(catalog), encoding="utf-8")
    profile = json.loads((ROOT / "profiles" / "anal_closeup.json").read_text(encoding="utf-8"))
    profile["stack_plan"]["cinema"] = {"id": "cinema-dy", "strength": 0.7}
    (tmp_path / "anal_closeup.json").write_text(json.dumps(profile), encoding="utf-8")
    try:
        select_loras(profile_name="anal_closeup", mode="t2v", catalog_path=cat_path, profiles_dir=tmp_path)
    except SelectError as exc:
        assert "0.4" in str(exc) or "cinema" in str(exc).lower()
    else:
        raise AssertionError("expected SelectError")


def test_refuses_full_quality_stack(tmp_path: Path):
    catalog = json.loads((ROOT / "catalog" / "loras.json").read_text(encoding="utf-8"))
    cat_path = tmp_path / "loras.json"
    cat_path.write_text(json.dumps(catalog), encoding="utf-8")
    profile = json.loads((ROOT / "profiles" / "anal_penetration.json").read_text(encoding="utf-8"))
    profile["stack_plan"] = {
        "act": {"id": "anal-penetration-coachbate", "strength": 0.85},
        "helper": {"id": "synth-pussy-h3", "strength": 0.55},
        "cinema": {"id": "hmnsfw-aio-v25", "strength": 0.75},
    }
    profile["disabled"] = [x for x in profile["disabled"] if x != "hmnsfw-aio-v25"]
    (tmp_path / "anal_penetration.json").write_text(json.dumps(profile), encoding="utf-8")
    try:
        select_loras(profile_name="anal_penetration", mode="t2v", catalog_path=cat_path, profiles_dir=tmp_path)
    except SelectError as exc:
        msg = str(exc).lower()
        assert "cinema" in msg or "full stack" in msg or "helper" in msg
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
    profile["stack_plan"] = {"act": {"id": "aftermidnight-ref2va", "strength": 1.0}}
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


def test_sfw_daily_splits_turbo_and_quality():
    data = select_loras(profile_name="sfw_daily", mode="t2v", prompt_arg="（シーン）")
    assert data["nsfw"] is False
    assert data["turbo"] is True
    assert [row["id"] for row in data["stack"]] == ["larry-v4", "cinema-dy"]
    assert [row["role"] for row in data["stack"]] == ["turbo", "cinema"]
    assert data["stack"][0]["strength_model"] == 1.0
    assert data["stack"][1]["strength_model"] == 0.65
    assert data["sampler"]["sampler_name"] == "res_multistep"
    assert data["sampler"]["scheduler"] == "simple"
    assert data["sampler"]["steps"] == 8
    assert "Picture 1" not in data["prompt"]
    assert all(row.get("adult") is False for row in data["stack"])
    preview = select_loras(profile_name="sfw_preview", mode="t2v")
    assert [row["id"] for row in preview["stack"]] == ["minimax-h3-turbo-fl2v-4step", "cinema-dy"]
    assert preview["sampler"]["steps"] == 4
    audio = select_loras(profile_name="sfw_audio", mode="t2v")
    assert [row["id"] for row in audio["stack"]] == ["minimax-h3-turbo-fl2v-8step", "cinema-dy"]
    r2v = select_loras(profile_name="sfw_r2v", mode="r2v")
    assert [row["id"] for row in r2v["stack"]] == ["minimax-h3-turbo-ref2v-4step", "cinema-dy"]
    assert r2v["stack"][1]["strength_model"] == 0.5


def test_custom_prompt_replaces_scene_template():
    data = select_loras(
        profile_name="sfw_daily",
        mode="t2v",
        prompt_arg="An adult over 21 cooks quietly in a sunlit kitchen.",
    )
    assert "sunlit kitchen" in data["prompt"]
    assert "Picture 1" not in data["prompt"]
    i2v = select_loras(
        profile_name="sfw_daily",
        mode="i2v",
        prompt_arg="For the target video, <Picture 1> is fully referenced. An adult over 21 waves.",
    )
    assert "waves" in i2v["prompt"]
    assert "<Picture 1>" in i2v["prompt"]


def test_sfw_refuses_adult_lora(tmp_path: Path):
    catalog = json.loads((ROOT / "catalog" / "loras.json").read_text(encoding="utf-8"))
    cat_path = tmp_path / "loras.json"
    cat_path.write_text(json.dumps(catalog), encoding="utf-8")
    profile = json.loads((ROOT / "profiles" / "sfw_daily.json").read_text(encoding="utf-8"))
    profile["stack_plan"]["cinema"] = {"id": "hmnsfw-aio-v25", "strength": 0.7}
    profile["disabled"] = [x for x in profile["disabled"] if x != "hmnsfw-aio-v25"]
    (tmp_path / "sfw_daily.json").write_text(json.dumps(profile), encoding="utf-8")
    try:
        select_loras(profile_name="sfw_daily", mode="t2v", catalog_path=cat_path, profiles_dir=tmp_path)
    except SelectError as exc:
        assert "adult" in str(exc).lower() or "SFW" in str(exc)
    else:
        raise AssertionError("expected SelectError")


def test_sfw_allows_cinema_point_seven(tmp_path: Path):
    catalog = json.loads((ROOT / "catalog" / "loras.json").read_text(encoding="utf-8"))
    cat_path = tmp_path / "loras.json"
    cat_path.write_text(json.dumps(catalog), encoding="utf-8")
    profile = json.loads((ROOT / "profiles" / "sfw_daily.json").read_text(encoding="utf-8"))
    profile["stack_plan"]["cinema"] = {"id": "cinema-dy", "strength": 0.7}
    (tmp_path / "sfw_daily.json").write_text(json.dumps(profile), encoding="utf-8")
    data = select_loras(profile_name="sfw_daily", mode="t2v", catalog_path=cat_path, profiles_dir=tmp_path)
    assert data["stack"][1]["strength_model"] == 0.7


def test_sfw_r2v_refuses_fl2va_turbo(tmp_path: Path):
    catalog = json.loads((ROOT / "catalog" / "loras.json").read_text(encoding="utf-8"))
    cat_path = tmp_path / "loras.json"
    cat_path.write_text(json.dumps(catalog), encoding="utf-8")
    profile = json.loads((ROOT / "profiles" / "sfw_r2v.json").read_text(encoding="utf-8"))
    profile["stack_plan"]["turbo"] = {"id": "minimax-h3-turbo-fl2v-4step", "strength": 1.0}
    profile["disabled"] = [x for x in profile["disabled"] if x != "minimax-h3-turbo-fl2v-4step"]
    (tmp_path / "sfw_r2v.json").write_text(json.dumps(profile), encoding="utf-8")
    try:
        select_loras(profile_name="sfw_r2v", mode="r2v", catalog_path=cat_path, profiles_dir=tmp_path)
    except SelectError as exc:
        msg = str(exc).lower()
        assert "fl2va" in msg or "r2v" in msg
    else:
        raise AssertionError("expected SelectError")
