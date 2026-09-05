import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "select_loras.py"
sys.path.insert(0, str(SCRIPT.parent))

from select_loras import (  # noqa: E402
    SelectError,
    apply_feminine_lock,
    forbidden_hits,
    list_situations,
    load_forbidden,
    select_loras,
    strip_male_subjects,
)


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
    assert [r["id"] for r in general["stack"]] == ["hmnsfw-aio-v25", "larry-v4"]
    assert general["stack"][0]["strength_model"] == 0.8
    assert general["stack"][1]["strength_model"] == 0.5
    assert general["sampler"]["steps"] == 12
    assert general["sampler"]["sampler_name"] == "euler"
    assert general["sampler"]["scheduler"] == "simple"
    riding = select_loras(profile_name="riding", mode="t2v")
    assert [r["id"] for r in riding["stack"]] == ["hmnsfw-aio-v25", "larry-v4"]
    assert riding["sampler"]["steps"] == 12
    assert preview["sampler"]["steps"] == 4
    assert preview["stack"][1]["strength_model"] == 1.0
    listed = list_situations()
    ids = {row["id"] for row in listed["situations"]}
    assert {"anal_penetration", "anal_closeup", "oral", "futa_blowjob", "futa_sex", "futa_anal", "general_sex", "preview", "sfw_daily", "sfw_preview", "sfw_audio", "lesbian_cunnilingus", "pussy_spread", "lesbian_spread"} <= ids
    oral = next(row for row in listed["situations"] if row["id"] == "oral")
    assert oral["enabled"]["t2v"] == ["blowjob-h3", "penis-lora-h3", "larry-v4"]
    assert oral["turbo"] is True
    anal = next(row for row in listed["situations"] if row["id"] == "anal_penetration")
    assert anal["turbo"] is False
    daily = next(row for row in listed["situations"] if row["id"] == "sfw_daily")
    assert daily["nsfw"] is False
    assert daily["enabled"]["t2v"] == ["larry-v4", "cinema-dy"]


def test_lesbian_and_spread_stacks():
    les = select_loras(profile_name="lesbian_cunnilingus", mode="t2v")
    assert [r["id"] for r in les["stack"]] == ["lesbian-cunnilingus-h3", "synth-pussy-h3", "larry-v4"]
    assert [r["role"] for r in les["stack"]] == ["act", "helper", "turbo"]
    assert [r["strength_model"] for r in les["stack"]] == [0.8, 0.55, 0.5]
    assert "Picture 1" not in les["prompt"]
    low = les["prompt"].lower()
    assert "kiss" in low and "lick" in low and "sweat" in low
    assert "over 21" in low
    assert "15 years" not in low
    unload = {r["id"] for r in les["unload"]}
    assert "pussy-spread-h3" in unload
    assert "cinema-dy" in unload
    spread = select_loras(profile_name="pussy_spread", mode="i2v")
    assert [r["id"] for r in spread["stack"]] == ["pussy-spread-h3", "synth-pussy-h3", "larry-v4"]
    assert [r["strength_model"] for r in spread["stack"]] == [0.75, 0.55, 0.5]
    assert "<Picture 1>" in spread["prompt"]
    combo = select_loras(profile_name="lesbian_spread", mode="t2v")
    assert [r["id"] for r in combo["stack"]] == ["lesbian-cunnilingus-h3", "pussy-spread-h3", "larry-v4"]
    assert "synth-pussy-h3" not in [r["id"] for r in combo["stack"]]
    assert combo["sampler"]["steps"] == 8
    catalog = json.loads((ROOT / "catalog" / "loras.json").read_text(encoding="utf-8"))
    by_id = {row["id"]: row for row in catalog["loras"]}
    assert by_id["synth-pussy-h3"]["civitai_version_id"] == 3204862
    assert by_id["lesbian-cunnilingus-h3"]["civitai_version_id"] == 3282598
    assert by_id["pussy-spread-h3"]["civitai_version_id"] == 3261512
    assert by_id["lesbian-cunnilingus-h3"]["trigger"] == ""
    assert by_id["pussy-spread-h3"]["trigger"] == ""


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


def test_futa_sex_and_anal_stay_feminine():
    sex = select_loras(profile_name="futa_sex", mode="t2v", prompt_arg="（シーン）")
    assert [r["id"] for r in sex["stack"]] == ["hmnsfw-aio-v25", "penis-lora-h3", "larry-v4"]
    assert [r["role"] for r in sex["stack"]] == ["act", "helper", "turbo"]
    assert sex["stack"][0]["strength_model"] == 0.8
    assert sex["stack"][2]["strength_model"] == 0.5
    assert sex["sampler"]["steps"] == 12
    assert sex["sampler"]["sampler_name"] == "euler"
    assert sex["sampler"]["scheduler"] == "simple"
    assert "futa-h3-v51" not in [r["id"] for r in sex["stack"]]
    low = sex["prompt"].lower()
    assert "adult woman" in low
    assert "no man" in low
    assert "no muscle" in low
    assert "feminine_lock:" in low
    assert "adult man" not in low
    assert "man" in sex["negative"].lower()
    assert "Picture 1" not in sex["prompt"]
    assert "penetrat" in low
    assert "vagina" in low
    assert "rhythm" in low
    assert "implied" not in low
    anal = select_loras(profile_name="futa_anal", mode="i2v", prompt_arg="（シーン）")
    assert [r["id"] for r in anal["stack"]] == ["anal-penetration-coachbate", "penis-lora-h3"]
    assert anal["turbo"] is False
    assert anal["sampler"]["steps"] >= 16
    assert "<Picture 1>" in anal["prompt"]
    assert "adult man" not in anal["prompt"].lower()
    assert "anus" in anal["prompt"].lower()
    custom = select_loras(
        profile_name="futa_sex",
        mode="t2v",
        prompt_arg="An adult man and a muscular man have sex in a bedroom. All performers are 21.",
    )
    clow = custom["prompt"].lower()
    assert "adult man" not in clow
    assert "muscular man" not in clow
    assert "feminine" in clow
    assert "no man" in clow
    bj = select_loras(profile_name="futa_blowjob", mode="t2v")
    assert "adult woman" in bj["prompt"].lower()
    assert "adult man" not in bj["prompt"].lower()
    try:
        select_loras(profile_name="futa_anal", mode="i2v", turbo_override=True)
    except SelectError as exc:
        assert "turbo" in str(exc).lower() or "CoachBate" in str(exc)
    else:
        raise AssertionError("expected SelectError")
    rewritten = strip_male_subjects("Adult man lying on his back. A man waits.")
    assert "adult man" not in rewritten.lower()
    locked, neg = apply_feminine_lock("Two adults over 21.", "child", {"feminine_lock": True})
    assert "feminine_lock:" in locked.lower()
    assert "no man" in locked.lower()
    assert "male body" in neg.lower()


def test_aio_sex_prompts_show_penetration_not_implied():
    general = select_loras(profile_name="general_sex", mode="t2v", prompt_arg="（シーン）")
    glow = general["prompt"].lower()
    assert "implied" not in glow
    assert "penetrat" in glow
    assert "vagina" in glow
    assert "rhythm" in glow
    assert "missionary" in glow
    assert general["sampler"]["steps"] == 12
    i2v = select_loras(profile_name="general_sex", mode="i2v", prompt_arg="（シーン）")
    assert "<Picture 1>" in i2v["prompt"]
    assert "implied" not in i2v["prompt"].lower()
    ride = select_loras(profile_name="riding", mode="t2v", prompt_arg="（シーン）")
    rlow = ride["prompt"].lower()
    assert "cowgirl" in rlow
    assert "penetrat" in rlow
    assert ride["sampler"]["steps"] == 12


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


def test_safety_no_child_is_not_a_request():
    assert forbidden_hits("Adult woman over 21. No child. No loli.") == []
    assert forbidden_hits("not a child, not a teen") == []
    assert forbidden_hits("no child, teen, loli, shota") == []
    assert forbidden_hits("a child sits on the bed") == ["child"]
    assert "15 years old" in forbidden_hits("Adult woman, 15 years old, in a station.")
    assert "15歳" in forbidden_hits("成人女性、15歳。")
    assert any("15" in x and "yo" in x for x in forbidden_hits("cast is 15yo"))
    assert forbidden_hits("Photoreal widescreen 16:9, 1344x768, 15 seconds, 24fps.") == []
    assert forbidden_hits("Adult woman 21 years old in a station.") == []
    assert forbidden_hits("Adult woman 25 years old.") == []
    assert any("20" in x for x in forbidden_hits("Adult, 20 years old."))
    assert any("20" in x for x in forbidden_hits("age 20"))
    data = select_loras(
        profile_name="anal_closeup",
        mode="t2v",
        prompt_arg="Adult woman over 21 presents her anus. No child. A man licks then fingers the hole.",
    )
    assert data["situation"] == "anal_closeup"
    assert "anus" in data["prompt"].lower()
    try:
        select_loras(
            profile_name="anal_closeup",
            mode="t2v",
            prompt_arg="a child is in the scene",
        )
    except SelectError as exc:
        assert "child" in str(exc)
    else:
        raise AssertionError("expected SelectError")
    try:
        select_loras(
            profile_name="general_sex",
            mode="t2v",
            prompt_arg="Photoreal 16:9 adult film. One woman is 15 years old.",
        )
    except SelectError as exc:
        assert "15" in str(exc).lower() or "forbidden" in str(exc).lower()
    else:
        raise AssertionError("expected SelectError")


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


def test_forbidden_json_extra_is_editable(tmp_path: Path):
    cfg = load_forbidden()
    assert "schoolgirl" in cfg["extra"]
    assert "loli" in cfg["minors"]
    assert cfg["min_age"] == 21
    assert "px.a8.net" in cfg["commercial"]
    comment = json.loads((ROOT / "catalog" / "forbidden.json").read_text(encoding="utf-8"))["comment_ja"]
    assert "このファイル" in comment
    assert "欄でも" not in comment
    empty = tmp_path / "forbidden.json"
    empty.write_text(
        json.dumps({"schema": "h3-lora-studio-forbidden/v1", "minors": [], "extra": ["brandx"]}),
        encoding="utf-8",
    )
    assert forbidden_hits("Adult woman over 21. brandx logo.", path=empty) == ["brandx"]
    assert "loli" in forbidden_hits("loli character", path=empty)
    assert "schoolgirl" not in forbidden_hits("schoolgirl uniform, adult over 21", path=empty)
    data = select_loras(
        profile_name="anal_closeup",
        mode="t2v",
        prompt_arg="Adult woman over 21. No child. A man licks the anus.",
        extra_forbidden=["brandx"],
        forbidden_path=empty,
    )
    assert "brandx" in data["forbidden_extra"]
    try:
        select_loras(
            profile_name="anal_closeup",
            mode="t2v",
            prompt_arg="Adult woman over 21 with a brandx tattoo. Anus visible.",
            extra_forbidden=["brandx"],
            forbidden_path=empty,
        )
    except SelectError as exc:
        assert "brandx" in str(exc)
    else:
        raise AssertionError("expected SelectError")


def test_locked_minors_stay_child_terms():
    from select_loras import LOCKED_MINORS

    assert "shota" in LOCKED_MINORS
    assert "loli" in LOCKED_MINORS
    assert "child" in LOCKED_MINORS
    assert "政府" not in LOCKED_MINORS
    assert "暴力" not in LOCKED_MINORS
    catalog = json.loads((ROOT / "catalog" / "forbidden.json").read_text(encoding="utf-8"))
    assert catalog["min_age"] == 21
    assert "shota" in catalog["minors"]
    assert "政府" not in catalog["minors"]
    loras = json.loads((ROOT / "catalog" / "loras.json").read_text(encoding="utf-8"))
    coach = next(row for row in loras["loras"] if row["id"] == "anal-penetration-coachbate")
    assert coach.get("paid") is True
