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
    assert ids == ["thumbinbutt-h3", "penis-lora-h3", "synth-pussy-h3"]
    assert [row["role"] for row in data["stack"]] == ["act", "helper", "helper"]
    assert data["stack"][0]["strength_model"] == 0.85
    assert data["stack"][1]["strength_model"] == 0.7
    assert data["stack"][2]["strength_model"] == 0.55
    assert "anal-penetration-coachbate" not in ids
    assert "hmnsfw-aio-v25" not in ids
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
    assert [row["id"] for row in data["stack"]] == ["thumbinbutt-h3", "penis-lora-h3", "synth-pussy-h3"]
    assert "Picture 1" not in data["prompt"]
    assert "first_frame" not in data["prompt"].lower()


def test_situations_switch_loras_by_profile_and_mode():
    anal_t2v = [r["id"] for r in select_loras(profile_name="anal_penetration", mode="t2v")["stack"]]
    close_t2v = [r["id"] for r in select_loras(profile_name="anal_closeup", mode="t2v")["stack"]]
    oral_t2v = select_loras(profile_name="oral", mode="t2v")
    futa_t2v = [r["id"] for r in select_loras(profile_name="futa_blowjob", mode="t2v")["stack"]]
    general = select_loras(profile_name="general_sex", mode="t2v")
    preview = select_loras(profile_name="preview", mode="t2v")
    assert anal_t2v == ["thumbinbutt-h3", "penis-lora-h3", "synth-pussy-h3"]
    assert close_t2v == ["synth-pussy-h3", "larry-v4", "cinema-dy"]
    assert [r["id"] for r in oral_t2v["stack"]] == ["blowjob-h3", "penis-lora-h3", "larry-v4"]
    assert oral_t2v["stack"][0]["strength_model"] == 0.75
    assert oral_t2v["stack"][2]["strength_model"] == 0.7
    assert oral_t2v["sampler"]["steps"] == 8
    assert oral_t2v["turbo"] is True
    assert futa_t2v == ["blowjob-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"]
    assert "futa-h3-v51" not in futa_t2v
    assert [r["id"] for r in general["stack"]] == ["hmnsfw-aio-v25", "larry-v4"]
    assert general["stack"][0]["strength_model"] == 0.8
    assert general["stack"][1]["strength_model"] == 0.5
    assert general["sampler"]["steps"] == 12
    assert general["sampler"]["sampler_name"] == "euler"
    assert general["sampler"]["scheduler"] == "simple"
    riding = select_loras(profile_name="riding", mode="t2v")
    assert [r["id"] for r in riding["stack"]] == ["cowgirl-position-h3", "penis-lora-h3", "synth-pussy-h3"]
    assert riding["sampler"]["steps"] == 12
    assert riding["turbo"] is False
    assert "hmnsfw-aio-v25" not in [r["id"] for r in riding["stack"]]
    assert preview["sampler"]["steps"] == 4
    assert preview["stack"][1]["strength_model"] == 1.0
    listed = list_situations()
    ids = {row["id"] for row in listed["situations"]}
    assert {
        "anal_penetration",
        "anal_closeup",
        "anal_fingering",
        "oral",
        "futa_blowjob",
        "futa_sex",
        "futa_anal",
        "general_sex",
        "preview",
        "sfw_daily",
        "sfw_preview",
        "sfw_audio",
        "lesbian_cunnilingus",
        "pussy_spread",
        "lesbian_spread",
        "riding",
        "doggy",
        "missionary_pov",
        "after_ejaculation",
        "facial",
        "creampie",
        "oral_creampie",
        "fingering",
        "masturbation",
        "footjob",
        "remote_orgasm",
    } <= ids
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
    assert "kiss" not in low
    assert "girl-next-door" in low
    assert "fully nude" in low
    assert "adult man" not in low
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
    assert [row["id"] for row in data["stack"]] == ["thumbinbutt-h3", "penis-lora-h3", "synth-pussy-h3"]


def test_futa_sex_and_anal_stay_feminine():
    sex = select_loras(profile_name="futa_sex", mode="t2v", prompt_arg="（シーン）")
    assert [r["id"] for r in sex["stack"]] == ["hmnsfw-aio-v25", "penis-lora-h3", "synth-pussy-h3"]
    assert [r["role"] for r in sex["stack"]] == ["act", "helper", "helper"]
    assert sex["stack"][0]["strength_model"] == 0.8
    assert sex["stack"][1]["strength_model"] == 0.7
    assert sex["stack"][2]["strength_model"] == 0.55
    assert sex["turbo"] is False
    assert sex["sampler"]["steps"] == 12
    assert sex["sampler"]["sampler_name"] == "euler"
    assert sex["sampler"]["scheduler"] == "simple"
    assert "futa-h3-v51" not in [r["id"] for r in sex["stack"]]
    assert "larry-v4" not in [r["id"] for r in sex["stack"]]
    low = sex["prompt"].lower()
    assert "adult woman" in low
    assert "no man" in low
    assert "no muscle" in low
    assert "feminine_lock:" in low
    assert "adult man" not in low
    assert "man" in sex["negative"].lower()
    assert "Picture 1" not in sex["prompt"]
    assert "girl-next-door" in low
    assert "fully nude" in low
    assert "futanari" in low
    anal = select_loras(profile_name="futa_anal", mode="i2v", prompt_arg="（シーン）")
    assert [r["id"] for r in anal["stack"]] == ["thumbinbutt-h3", "penis-lora-h3", "synth-pussy-h3"]
    assert [r["role"] for r in anal["stack"]] == ["act", "helper", "helper"]
    assert [r["strength_model"] for r in anal["stack"]] == [0.85, 0.7, 0.55]
    assert anal["stack"][0]["trigger"] == "thum1n8utt"
    assert anal["turbo"] is False
    assert anal["sampler"]["steps"] == 12
    assert anal["sampler"]["sampler_name"] == "euler"
    assert "<Picture 1>" in anal["prompt"]
    alow = anal["prompt"].lower()
    assert alow.startswith("thum1n8utt, penislora")
    assert "inserts her penis in (s1)'s anus" in alow
    assert "causing (s1) to moan with pleasure" in alow
    assert "anus sits above her vagina" in alow
    assert "hands of (s2) stay on (s1)'s hips" in alow
    assert "not pov" in alow
    assert "adult man" not in alow
    assert "the man" not in alow
    assert " his " not in alow
    assert "thumb" not in alow
    assert "anus" in alow
    assert "vulva" not in alow
    assert "futanari" in alow
    aneg = anal["negative"].lower()
    assert "thumb in anus" in aneg
    assert "hand near anus" in aneg
    assert "vaginal penetration" in aneg
    assert "man" in aneg
    unload_anal = {r["id"] for r in anal["unload"]}
    assert "anal-penetration-coachbate" in unload_anal
    assert "hmnsfw-aio-v25" in unload_anal
    assert "fingering-h3" in unload_anal
    assert "doggy-h3" in unload_anal
    assert "larry-v4" in unload_anal
    anal_t2v = select_loras(profile_name="futa_anal", mode="t2v", prompt_arg="（シーン）")
    assert "Picture 1" not in anal_t2v["prompt"]
    assert "inserts her penis in (s1)'s anus" in anal_t2v["prompt"].lower()
    close = select_loras(profile_name="anal_penetration", mode="i2v", prompt_arg="（シーン）")
    assert close["sampler"]["sampler_name"] == "res_multistep"
    assert close["sampler"]["steps"] == 16
    clow = close["prompt"].lower()
    assert clow.startswith("thum1n8utt, penislora")
    assert "close-up on (s1)'s anus" in clow
    assert "inserts her penis in (s1)'s anus" in clow
    assert "thumb" not in clow
    assert "the man" not in clow
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
    assert [r["id"] for r in bj["stack"]] == ["blowjob-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"]
    assert [r["role"] for r in bj["stack"]] == ["act", "helper", "helper", "turbo"]
    assert bj["stack"][1]["strength_model"] == 0.7
    assert bj["stack"][2]["strength_model"] == 0.55
    assert bj["stack"][3]["strength_model"] == 0.5
    assert bj["turbo"] is True
    assert bj["sampler"]["steps"] == 6
    blow = bj["prompt"].lower()
    assert "adult woman" in blow
    assert "adult man" not in blow
    assert "bl0w_j0b" in blow
    assert "penislora" in blow
    assert "vulva" not in blow
    assert "complete futanari" not in blow
    try:
        select_loras(profile_name="futa_anal", mode="i2v", turbo_override=True)
    except SelectError as exc:
        assert "turbo" in str(exc).lower() or "CoachBate" in str(exc)
    else:
        raise AssertionError("expected SelectError")
    rewritten = strip_male_subjects("Adult man lying on his back. A man waits. The male character uses his penis.")
    assert "adult man" not in rewritten.lower()
    assert "male character" not in rewritten.lower()
    assert "his penis" not in rewritten.lower()
    assert "her penis" in rewritten.lower()
    assert "adult man" not in rewritten.lower()
    locked, neg = apply_feminine_lock("Two adults over 21.", "child", {"feminine_lock": True})
    assert "feminine_lock:" in locked.lower()
    assert "no man" in locked.lower()
    assert "male body" in neg.lower()


def test_empty_adult_prompts_are_girl_next_door_no_men():
    general = select_loras(profile_name="general_sex", mode="t2v", prompt_arg="（シーン）")
    glow = general["prompt"].lower()
    assert "girl-next-door" in glow
    assert "fully nude" in glow
    assert "futanari" in glow
    assert "adult man" not in glow
    assert "feminine_lock:" in glow
    assert general["sampler"]["steps"] == 12
    i2v = select_loras(profile_name="general_sex", mode="i2v", prompt_arg="（シーン）")
    assert "<Picture 1>" in i2v["prompt"]
    assert "adult man" not in i2v["prompt"].lower()
    ride = select_loras(profile_name="riding", mode="t2v", prompt_arg="（シーン）")
    rlow = ride["prompt"].lower()
    assert "cowgirl" in rlow
    assert "girl-next-door" in rlow
    assert "adult man" not in rlow
    assert ride["sampler"]["steps"] == 12
    assert "Picture 1" not in ride["prompt"]
    assert ride["turbo"] is False
    assert [r["id"] for r in ride["stack"]] == ["cowgirl-position-h3", "penis-lora-h3", "synth-pussy-h3"]
    unload_ride = {r["id"] for r in ride["unload"]}
    assert "hmnsfw-aio-v25" in unload_ride
    assert "riding-pose-i2v" in unload_ride
    assert "larry-v4" in unload_ride
    oral = select_loras(profile_name="oral", mode="t2v", prompt_arg="（シーン）")
    olow = oral["prompt"].lower()
    assert "adult man" not in olow
    assert "futanari" in olow
    assert "bl0w_j0b" in olow
    preview = select_loras(profile_name="preview", mode="t2v", prompt_arg="（シーン）")
    assert "adult man" not in preview["prompt"].lower()
    assert "futanari" in preview["prompt"].lower()
    anal = select_loras(profile_name="anal_penetration", mode="t2v", prompt_arg="（シーン）")
    assert "adult man" not in anal["prompt"].lower()
    assert "futanari" in anal["prompt"].lower()
    close = select_loras(profile_name="anal_closeup", mode="t2v", prompt_arg="（シーン）")
    assert "adult man" not in close["prompt"].lower()
    assert "futanari" not in close["prompt"].lower()
    for name in (
        "futa_sex",
        "futa_anal",
        "futa_blowjob",
        "riding",
        "doggy",
        "missionary_pov",
        "after_ejaculation",
        "facial",
        "creampie",
        "oral_creampie",
        "footjob",
        "fingering",
        "anal_fingering",
        "masturbation",
        "remote_orgasm",
        "pussy_spread",
        "lesbian_cunnilingus",
        "lesbian_spread",
    ):
        row = select_loras(profile_name=name, mode="t2v", prompt_arg="（シーン）")
        low = row["prompt"].lower()
        assert "adult man" not in low, name
        assert "girl-next-door" in low, name
        assert "fully nude" in low, name
        assert "over 21" in low, name
        assert "feminine_lock:" in low, name
        assert "Picture 1" not in row["prompt"], name


def test_pose_aftercare_and_solo_act_stacks():
    catalog = json.loads((ROOT / "catalog" / "loras.json").read_text(encoding="utf-8"))
    by_id = {row["id"]: row for row in catalog["loras"]}
    for lid in (
        "cowgirl-position-h3",
        "doggy-h3",
        "missionary-pov-h3",
        "hmcumshot-v2",
        "fingering-h3",
        "thumbinbutt-h3",
        "hmmasturbation-h3",
        "footjob-h3",
        "remote-orgasm-h3",
    ):
        row = by_id[lid]
        assert "t2v" in row["modes"]
        assert "i2v" in row["modes"]
        assert row["arch"] == "fl2va"
        assert row["adult"] is True
        assert row["source"] == "civitai"
        assert row["civitai_file_id"]
    facial_row = by_id["facial-cumshot-h3"]
    assert "t2v" in facial_row["modes"]
    assert "i2v" in facial_row["modes"]
    assert facial_row["arch"] == "fl2va"
    assert facial_row["adult"] is True
    assert facial_row["source"] == "hf"
    assert facial_row["trigger"] == "cmst"
    assert facial_row["repo"] == "EllaPriest45/MinimaxH3_Actions"
    assert by_id["riding-pose-i2v"]["modes"] == ["i2v"]

    doggy = select_loras(profile_name="doggy", mode="t2v", prompt_arg="（シーン）")
    assert [r["id"] for r in doggy["stack"]] == ["doggy-h3", "penis-lora-h3", "synth-pussy-h3"]
    assert [r["role"] for r in doggy["stack"]] == ["act", "helper", "helper"]
    assert doggy["turbo"] is False
    assert doggy["sampler"]["steps"] == 12
    assert "h-zshr" in doggy["prompt"].lower()
    assert "Picture 1" not in doggy["prompt"]
    assert "hmnsfw-aio-v25" not in [r["id"] for r in doggy["stack"]]
    doggy_i2v = select_loras(profile_name="doggy", mode="i2v", prompt_arg="（シーン）")
    assert "<Picture 1>" in doggy_i2v["prompt"]

    pov = select_loras(profile_name="missionary_pov", mode="t2v", prompt_arg="（シーン）")
    assert [r["id"] for r in pov["stack"]] == ["missionary-pov-h3", "penis-lora-h3", "larry-v4"]
    assert pov["turbo"] is True
    assert pov["sampler"]["steps"] == 8
    assert "synth-pussy-h3" not in [r["id"] for r in pov["stack"]]
    assert "hmnsfw-aio-v25" not in [r["id"] for r in pov["stack"]]
    assert "pov" in pov["prompt"].lower()
    assert "Picture 1" not in pov["prompt"]

    after = select_loras(profile_name="after_ejaculation", mode="t2v", prompt_arg="（シーン）")
    assert [r["id"] for r in after["stack"]] == ["hmcumshot-v2", "penis-lora-h3", "larry-v4"]
    assert after["stack"][0]["trigger"] == "cumshot"
    assert after["sampler"]["steps"] == 8
    assert "cumshot" in after["prompt"].lower()
    assert "remote-orgasm-h3" not in [r["id"] for r in after["stack"]]
    assert "hmnsfw-aio-v25" not in [r["id"] for r in after["stack"]]
    unload_after = {r["id"] for r in after["unload"]}
    assert "remote-orgasm-h3" in unload_after
    assert "facial-cumshot-h3" in unload_after

    facial = select_loras(profile_name="facial", mode="t2v", prompt_arg="（シーン）")
    assert [r["id"] for r in facial["stack"]] == ["facial-cumshot-h3", "penis-lora-h3", "larry-v4"]
    assert facial["stack"][0]["trigger"] == "cmst"
    assert facial["sampler"]["steps"] == 8
    assert facial["turbo"] is True
    assert "cmst" in facial["prompt"].lower()
    assert "hmcumshot-v2" not in [r["id"] for r in facial["stack"]]
    assert "remote-orgasm-h3" not in [r["id"] for r in facial["stack"]]
    assert "hmnsfw-aio-v25" not in [r["id"] for r in facial["stack"]]
    assert "adult man" not in facial["prompt"].lower()
    assert "Picture 1" not in facial["prompt"]
    unload_facial = {r["id"] for r in facial["unload"]}
    assert "hmcumshot-v2" in unload_facial
    assert "remote-orgasm-h3" in unload_facial
    facial_i2v = select_loras(profile_name="facial", mode="i2v", prompt_arg="（シーン）")
    assert "<Picture 1>" in facial_i2v["prompt"]
    assert "looking up" in facial_i2v["prompt"].lower()

    cream_row = by_id["final-thrust-h3"]
    assert cream_row["civitai_model_id"] == 2891879
    assert cream_row["civitai_file_id"] == 3157295
    assert cream_row["filename"] == "H3_FinalThrust.safetensors"
    assert cream_row["trigger"] == ""
    assert "t2v" in cream_row["modes"]
    cumouf_row = by_id["cumouf-h3"]
    assert cumouf_row["civitai_model_id"] == 2846978
    assert cumouf_row["civitai_file_id"] == 3105419
    assert cumouf_row["trigger"] == "CUMOUF"
    assert cumouf_row["default_strength"] == 0.5

    cream = select_loras(profile_name="creampie", mode="t2v", prompt_arg="（シーン）")
    assert [r["id"] for r in cream["stack"]] == ["final-thrust-h3", "penis-lora-h3", "synth-pussy-h3"]
    assert cream["turbo"] is False
    assert cream["sampler"]["steps"] == 12
    clow = cream["prompt"].lower()
    assert "cums inside of her" in clow
    assert "powerful, intense thrusts with her penis" in clow
    assert "futanari" in clow
    assert "adult man" not in clow
    assert "the man" not in clow
    assert "male character" not in clow
    assert " his " not in clow
    assert "Picture 1" not in cream["prompt"]
    assert "hmcumshot-v2" not in [r["id"] for r in cream["stack"]]
    assert "facial-cumshot-h3" not in [r["id"] for r in cream["stack"]]
    assert "cumouf-h3" not in [r["id"] for r in cream["stack"]]
    unload_c = {r["id"] for r in cream["unload"]}
    assert "hmcumshot-v2" in unload_c
    assert "facial-cumshot-h3" in unload_c
    assert "cumouf-h3" in unload_c
    cream_i2v = select_loras(profile_name="creampie", mode="i2v", prompt_arg="（シーン）")
    assert "<Picture 1>" in cream_i2v["prompt"]
    assert "male character" not in cream_i2v["prompt"].lower()

    oral_c = select_loras(profile_name="oral_creampie", mode="t2v", prompt_arg="（シーン）")
    assert [r["id"] for r in oral_c["stack"]] == ["cumouf-h3", "penis-lora-h3", "larry-v4"]
    assert oral_c["stack"][0]["trigger"] == "CUMOUF"
    assert oral_c["stack"][0]["strength_model"] == 0.5
    assert oral_c["turbo"] is True
    assert oral_c["sampler"]["steps"] == 8
    olow = oral_c["prompt"].lower()
    assert olow.startswith("cumouf")
    assert "fills (s1)'s mouth" in olow or "fills (s1)'s mouth" in oral_c["prompt"].lower()
    assert "inside the mouth" in olow
    assert "not a facial" in olow
    assert "futanari" in olow
    assert "adult man" not in olow
    assert "the man" not in olow
    assert "male character" not in olow
    assert " his " not in olow
    assert "blowjob-h3" not in [r["id"] for r in oral_c["stack"]]
    assert "facial-cumshot-h3" not in [r["id"] for r in oral_c["stack"]]
    assert "final-thrust-h3" not in [r["id"] for r in oral_c["stack"]]
    unload_o = {r["id"] for r in oral_c["unload"]}
    assert "blowjob-h3" in unload_o
    assert "facial-cumshot-h3" in unload_o
    assert "final-thrust-h3" in unload_o
    oral_c_i2v = select_loras(profile_name="oral_creampie", mode="i2v", prompt_arg="（シーン）")
    assert "<Picture 1>" in oral_c_i2v["prompt"]
    assert "wrapped around" in oral_c_i2v["prompt"].lower()

    custom_male = select_loras(
        profile_name="creampie",
        mode="t2v",
        prompt_arg="CUMOUF. The male character inserts his penis and cums inside. All performers are 21.",
    )
    cm = custom_male["prompt"].lower()
    assert "male character" not in cm
    assert "his penis" not in cm
    assert "her penis" in cm

    fingering = select_loras(profile_name="fingering", mode="t2v", prompt_arg="（シーン）")
    assert [r["id"] for r in fingering["stack"]] == ["fingering-h3", "synth-pussy-h3", "larry-v4"]
    assert fingering["sampler"]["steps"] == 8
    assert "hmmasturbation-h3" not in [r["id"] for r in fingering["stack"]]
    assert "penis-lora-h3" not in [r["id"] for r in fingering["stack"]]
    assert "Picture 1" not in fingering["prompt"]
    unload_f = {r["id"] for r in fingering["unload"]}
    assert "hmmasturbation-h3" in unload_f
    assert "thumbinbutt-h3" in unload_f

    anal_finger = select_loras(profile_name="anal_fingering", mode="t2v", prompt_arg="（シーン）")
    assert [r["id"] for r in anal_finger["stack"]] == ["thumbinbutt-h3", "synth-pussy-h3", "larry-v4"]
    assert anal_finger["stack"][0]["trigger"] == "thum1n8utt"
    assert anal_finger["sampler"]["steps"] == 8
    assert anal_finger["turbo"] is True
    assert "thum1n8utt" in anal_finger["prompt"].lower()
    assert "rub around her anus in a circular motion then inserts her right thumb in her anus" in anal_finger["prompt"].lower()
    assert "anus sits above her vagina" in anal_finger["prompt"].lower()
    assert "no penis" in anal_finger["prompt"].lower()
    assert "adult man" not in anal_finger["prompt"].lower()
    assert "the man" not in anal_finger["prompt"].lower()
    assert " his " not in anal_finger["prompt"].lower()
    assert "Picture 1" not in anal_finger["prompt"]
    assert "fingering-h3" not in [r["id"] for r in anal_finger["stack"]]
    assert "anal-penetration-coachbate" not in [r["id"] for r in anal_finger["stack"]]
    assert "hmnsfw-aio-v25" not in [r["id"] for r in anal_finger["stack"]]
    assert "penis-lora-h3" not in [r["id"] for r in anal_finger["stack"]]
    unload_af = {r["id"] for r in anal_finger["unload"]}
    assert "fingering-h3" in unload_af
    assert "anal-penetration-coachbate" in unload_af
    assert "hmmasturbation-h3" in unload_af
    anal_finger_i2v = select_loras(profile_name="anal_fingering", mode="i2v", prompt_arg="（シーン）")
    assert "<Picture 1>" in anal_finger_i2v["prompt"]
    assert "thum1n8utt" in anal_finger_i2v["prompt"].lower()
    assert "adult man" not in anal_finger_i2v["prompt"].lower()

    thumb_row = by_id["thumbinbutt-h3"]
    assert "t2v" in thumb_row["modes"]
    assert "i2v" in thumb_row["modes"]
    assert thumb_row["arch"] == "fl2va"
    assert thumb_row["adult"] is True
    assert thumb_row["source"] == "civitai"
    assert thumb_row["trigger"] == "thum1n8utt"
    assert thumb_row["civitai_model_id"] == 2904444
    assert thumb_row["civitai_version_id"] == 3284492
    assert thumb_row["civitai_file_id"] == 3168734
    assert thumb_row["filename"] == "H3_ThumbInButt.safetensors"
    assert " " not in thumb_row["filename"]

    solo = select_loras(profile_name="masturbation", mode="t2v", prompt_arg="（シーン）")
    assert [r["id"] for r in solo["stack"]] == ["hmmasturbation-h3", "synth-pussy-h3", "larry-v4"]
    assert solo["sampler"]["steps"] == 12
    assert "hmmasturbation" in solo["prompt"].lower()
    assert "fingering-h3" not in [r["id"] for r in solo["stack"]]
    unload_m = {r["id"] for r in solo["unload"]}
    assert "fingering-h3" in unload_m
    assert "thumbinbutt-h3" in unload_m

    foot = select_loras(profile_name="footjob", mode="t2v", prompt_arg="（シーン）")
    assert [r["id"] for r in foot["stack"]] == ["footjob-h3", "penis-lora-h3", "larry-v4"]
    assert foot["stack"][0]["trigger"] == "fj."
    assert "fj." in foot["prompt"]
    assert foot["sampler"]["steps"] == 8

    orgasm = select_loras(profile_name="remote_orgasm", mode="t2v", prompt_arg="（シーン）")
    assert [r["id"] for r in orgasm["stack"]] == ["remote-orgasm-h3", "synth-pussy-h3", "larry-v4"]
    assert orgasm["stack"][0]["trigger"] == "Remoteorgasm"
    assert "remoteorgasm" in orgasm["prompt"].lower()
    assert "hmcumshot-v2" not in [r["id"] for r in orgasm["stack"]]
    assert orgasm["sampler"]["steps"] == 8

    sex = select_loras(profile_name="futa_sex", mode="t2v")
    sex_ids = [r["id"] for r in sex["stack"]]
    assert sex_ids == ["hmnsfw-aio-v25", "penis-lora-h3", "synth-pussy-h3"]
    assert "cowgirl-position-h3" not in sex_ids
    assert "doggy-h3" not in sex_ids


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


def test_anal_profiles_refuse_turbo_in_stack(tmp_path: Path):
    catalog = json.loads((ROOT / "catalog" / "loras.json").read_text(encoding="utf-8"))
    cat_path = tmp_path / "loras.json"
    cat_path.write_text(json.dumps(catalog), encoding="utf-8")
    for name in ("futa_anal", "anal_penetration"):
        profile = json.loads((ROOT / "profiles" / f"{name}.json").read_text(encoding="utf-8"))
        profile["stack_plan"]["turbo"] = {"id": "larry-v4", "strength": 0.5}
        profile["disabled"] = [x for x in profile["disabled"] if x != "larry-v4"]
        (tmp_path / f"{name}.json").write_text(json.dumps(profile), encoding="utf-8")
        try:
            select_loras(profile_name=name, mode="i2v", catalog_path=cat_path, profiles_dir=tmp_path)
        except SelectError as exc:
            assert "turbo off" in str(exc).lower(), name
        else:
            raise AssertionError(f"expected SelectError for {name}")


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


def test_refuses_three_helpers(tmp_path: Path):
    catalog = json.loads((ROOT / "catalog" / "loras.json").read_text(encoding="utf-8"))
    cat_path = tmp_path / "loras.json"
    cat_path.write_text(json.dumps(catalog), encoding="utf-8")
    profile = json.loads((ROOT / "profiles" / "futa_blowjob.json").read_text(encoding="utf-8"))
    profile["stack_plan"]["helper"] = [
        {"id": "penis-lora-h3", "strength": 0.7},
        {"id": "synth-pussy-h3", "strength": 0.55},
        {"id": "pussy-spread-h3", "strength": 0.6},
    ]
    profile["disabled"] = [x for x in profile["disabled"] if x != "pussy-spread-h3"]
    (tmp_path / "futa_blowjob.json").write_text(json.dumps(profile), encoding="utf-8")
    try:
        select_loras(profile_name="futa_blowjob", mode="t2v", catalog_path=cat_path, profiles_dir=tmp_path)
    except SelectError as exc:
        assert "helper" in str(exc).lower()
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
