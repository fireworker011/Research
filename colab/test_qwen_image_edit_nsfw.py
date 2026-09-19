import ast
import json
import re
import sys
import types
from pathlib import Path

from PIL import Image

from qwen_image_edit_nsfw import (
    AIO_FILENAME,
    AIO_REPO_ID,
    ANAL_ANATOMY,
    ANAL_CLOSE,
    ANAL_DETAIL,
    ANAL_FRONT_LOCK,
    ANAL_FRONT_PRESETS,
    ANAL_HOLE_LOCK,
    ANAL_JOIN,
    ANAL_POSE_LABELS,
    ANAL_PRESETS,
    ANAL_REAR_LOCK,
    ANAL_REAR_PRESETS,
    CANVAS_AUTO,
    CANVAS_FIXED,
    DEFAULT_EDIT_PROMPT,
    DEFAULT_NEGATIVE,
    DEFAULT_REWRITE_PROMPT,
    DIFFUSERS_COLAB_SPEC,
    DRIVE_FREE_GIB,
    ENABLE_FP8_QUANT,
    FUTA_LOCK,
    FACE_KEEP,
    KEEP_LOCK,
    LORA_FILES,
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    PILLOW_COLAB_SPEC,
    PIPE_ID,
    REF_SOURCE_DEFAULT,
    REWRITE_MODEL,
    FECES_LOOK,
    SCAT_ACT,
    SCAT_DETAIL,
    SCAT_HOLE_LOCK,
    SCAT_LABELS,
    UNCENSOR_ANAL_TRIGGER,
    UNCENSOR_SCAT_TRIGGER,
    UNCENSOR_TRIGGER,
    SCHED_BASE_SHIFT,
    SCHED_MAX_IMAGE_SEQ_LEN,
    SEX_ACT_PRESETS,
    SEX_PRESET_DEFAULT,
    SEX_PRESETS,
    SPACE_GPU_RESIDENT_GIB,
    SPACE_SEX_PRESET_LABELS,
    STEPS,
    TORCHAO_COLAB_MIN,
    TORCHAO_COLAB_SPEC,
    TRANSFORMER_ID,
    TRUE_CFG,
    STYLE_LABELS,
    STYLE_PRESET_DEFAULT,
    STYLE_PRESETS,
    URINE_DETAIL,
    URINE_LABELS,
    UPLOAD_PHONE_HINT,
    WEIGHTS_CACHE_GIB,
    apply_futa_partner,
    apply_space_scheduler,
    apply_style,
    auto_canvas_size,
    canvas_form_options,
    classify_aio_key,
    clamp_edit_vae_area,
    compose_edit_prompt,
    disable_safety,
    drop_stale_diffusers_modules,
    drop_stale_pil_modules,
    drop_stale_torchao_modules,
    drive_space_lines,
    face_lock_image,
    force_edit_offload,
    free_cuda,
    has_leftover_man,
    infer_kwargs,
    inject_aio_state,
    is_cuda_oom,
    input_source_form_options,
    is_anal_preset,
    is_excrete_preset,
    is_photoreal_path,
    is_scat_preset,
    is_sex_act_preset,
    is_urine_preset,
    list_input_images,
    wants_anal_lock,
    wants_scat_lock,
    lock_identity_prompt,
    lora_files_for_gpu,
    lora_trigger,
    lora_skip_summary,
    lora_stack,
    parse_rewritten_prompt,
    pipe_images,
    place_edit_pipe,
    ref_source_form_options,
    refuse_photoreal,
    require_l4_or_exit,
    require_space_gpu_or_exit,
    require_pillow_colab,
    require_torchao_for_git_diffusers,
    resize_rgb,
    resolve_input_paths,
    rewrite_edit_prompt,
    run_pipe_edit,
    save_jpeg,
    space_device_mode,
    space_scheduler_config,
    split_aio_state_dict,
    tune_edit_vae,
    sex_preset_form_options,
    sex_preset_labels,
    snapped_rgb,
    snapped_size,
    style_form_options,
    style_negative,
)

ROOT = Path(__file__).resolve().parent
WRITER = ROOT / "_write_qwen_edit_nb.py"


def test_stack_is_mk1227_class():
    assert PIPE_ID == "Qwen/Qwen-Image-Edit-2511"
    assert AIO_REPO_ID == "Phr00t/Qwen-Image-Edit-Rapid-AIO"
    assert AIO_FILENAME == "v23/Qwen-Rapid-AIO-NSFW-v23.safetensors"
    assert TRANSFORMER_ID == "prithivMLmods/Qwen-Image-Edit-Rapid-AIO-V23"
    assert STEPS == 4
    assert TRUE_CFG == 1.0
    assert ENABLE_FP8_QUANT is True
    assert DEFAULT_REWRITE_PROMPT is False
    assert REWRITE_MODEL == "Qwen/Qwen2.5-VL-72B-Instruct"
    assert DEFAULT_NEGATIVE == ""
    assert TORCHAO_COLAB_SPEC == "torchao>=0.16.0"
    assert TORCHAO_COLAB_MIN == (0, 16)
    assert DIFFUSERS_COLAB_SPEC.startswith("git+https://github.com/huggingface/diffusers.git")
    assert "20cm" in FUTA_LOCK
    assert "no testicles" in FUTA_LOCK
    assert "Change clothing only" in KEEP_LOCK
    assert "Remove only the clothes" in DEFAULT_EDIT_PROMPT
    assert canvas_form_options() == [CANVAS_AUTO, CANVAS_FIXED]


def test_compose_empty_adds_futa_undress():
    out = compose_edit_prompt("")
    assert "Change clothing only" in out
    assert "Remove only the clothes" in out
    assert "20cm" in out
    assert "no testicles" in out
    assert "same face" in out.lower()
    assert "do not swap" in out.lower()
    assert "MANDATORY IDENTITY LOCK" not in out
    assert "EDIT SCOPE" not in out
    assert "not text-to-image" not in out
    assert "you may change clothing, pose" not in out.lower()
    assert "Picture 2" not in out
    assert len(out) < 900


def test_compose_keeps_user_and_still_locks():
    out = compose_edit_prompt("same green dress stairs", undress=True, futa=True)
    assert "same green dress stairs" in out
    assert "Remove only the clothes" in out
    assert "20cm" in out
    assert "do not swap" in out.lower()
    assert "MANDATORY IDENTITY LOCK" not in out
    assert "you may change clothing, pose" not in out.lower()


def test_lora_stack_undress_futa():
    names = [row[0] for row in lora_stack(True, True)]
    assert names == ["remove_clothing"]
    assert lora_stack(False, False) == []


def test_require_l4_rejects_t4():
    try:
        require_space_gpu_or_exit(15.0, "Tesla T4")
    except SystemExit as e:
        assert "A100" in str(e)
        assert "T4" in str(e)
    else:
        raise AssertionError("T4 must exit")
    require_space_gpu_or_exit(22.5, "L4")
    require_l4_or_exit(40.0, "A100")
    assert space_device_mode(24.0) == "model_cpu_offload"
    assert space_device_mode(SPACE_GPU_RESIDENT_GIB) == "cuda"
    assert space_device_mode(80.0) == "cuda"


def test_pillow_12_0_is_rejected_on_colab():
    assert PILLOW_COLAB_SPEC == "pillow==11.3.0"
    assert require_pillow_colab("11.3.0") == "11.3.0"
    try:
        require_pillow_colab("12.0.0")
    except SystemExit as e:
        assert "_Ink" in str(e)
        assert PILLOW_COLAB_SPEC in str(e)
    else:
        raise AssertionError("Pillow 12.0 must exit")
    try:
        require_pillow_colab("12.3.0")
    except SystemExit as e:
        assert "_imaging" in str(e)
        assert PILLOW_COLAB_SPEC in str(e)
    else:
        raise AssertionError("Pillow 12.3 must exit")
    saved = {
        name: mod
        for name, mod in sys.modules.items()
        if name == "PIL"
        or name.startswith("PIL.")
        or name == "torchvision"
        or name.startswith("torchvision.")
    }
    sys.modules["PIL._fake_qwen_edit"] = object()
    drop_stale_pil_modules()
    assert "PIL._fake_qwen_edit" not in sys.modules
    sys.modules.update(saved)


def test_lora_skip_summary_prefers_torchao_over_nfaa():
    out = lora_skip_summary(
        ["Found an incompatible version of torchao. Found version 0.10.0"],
        has_token=False,
    )
    assert "torchao" in out
    assert "HF_TOKEN" not in out
    nfaa = lora_skip_summary(["401 Client Error gated repo NFAA"], has_token=False)
    assert "HF_TOKEN" in nfaa
    assert "NFAA" in nfaa
    ok_token = lora_skip_summary(["weird"], has_token=True)
    assert "HF_TOKEN" not in ok_token


def test_drop_stale_torchao_modules_clears_peft_cache():
    class Dummy:
        def __init__(self):
            self.cleared = False

        def cache_clear(self):
            self.cleared = True

    dummy = Dummy()

    class Utils:
        is_torchao_available = dummy

    sys.modules["torchao"] = object()
    sys.modules["torchao.quantization"] = object()
    sys.modules["peft.import_utils"] = Utils()
    drop_stale_torchao_modules()
    assert "torchao" not in sys.modules
    assert "torchao.quantization" not in sys.modules
    assert dummy.cleared is True
    sys.modules.pop("peft.import_utils", None)


def test_require_torchao_for_git_diffusers_rejects_0_11():
    saved = {
        name: sys.modules[name]
        for name in list(sys.modules)
        if name == "torchao" or name.startswith("torchao.")
    }
    for name in list(saved):
        del sys.modules[name]
    try:
        ao = types.ModuleType("torchao")
        ao.__version__ = "0.11.0"
        quant = types.ModuleType("torchao.quantization")
        sys.modules["torchao"] = ao
        sys.modules["torchao.quantization"] = quant
        try:
            require_torchao_for_git_diffusers()
        except SystemExit as e:
            assert "FqnToConfig" in str(e) or "食い違う" in str(e)
            assert TORCHAO_COLAB_SPEC in str(e)
        else:
            raise AssertionError("torchao 0.11 without FqnToConfig must exit")
        quant.FqnToConfig = object
        try:
            require_torchao_for_git_diffusers("0.11.0")
        except SystemExit as e:
            assert "0.11.0" in str(e)
            assert "FqnToConfig" in str(e)
            assert TORCHAO_COLAB_SPEC in str(e)
        else:
            raise AssertionError("torchao 0.11 with stub FqnToConfig must exit")
        ao.__version__ = "0.16.0"
        assert require_torchao_for_git_diffusers() == "0.16.0"
    finally:
        for name in list(sys.modules):
            if name == "torchao" or name.startswith("torchao."):
                del sys.modules[name]
        sys.modules.update(saved)


def test_drop_stale_diffusers_modules_clears_pipeline_cache():
    saved = {
        name: sys.modules[name]
        for name in list(sys.modules)
        if name == "diffusers" or name.startswith("diffusers.")
    }
    sys.modules["diffusers"] = object()
    sys.modules["diffusers.pipelines"] = object()
    drop_stale_diffusers_modules()
    assert "diffusers" not in sys.modules
    assert "diffusers.pipelines" not in sys.modules
    sys.modules.update(saved)


def test_resize_and_jpeg(tmp_path):
    im = Image.new("RGB", (1008, 1792), (10, 20, 30))
    out = resize_rgb(im, 576, 1024)
    assert out.size == (576, 1024)
    assert snapped_size(577, 1025) == (576, 1024)
    dest = save_jpeg(out, tmp_path / "x.jpg")
    assert dest.is_file()


def test_disable_safety_and_infer_kwargs():
    class Fake:
        safety_checker = object()
        requires_safety_checker = True

    pipe = disable_safety(Fake())
    assert pipe.safety_checker is None
    assert pipe.requires_safety_checker is False
    kw = infer_kwargs("hello", true_cfg=1.0)
    assert kw["num_inference_steps"] == 4
    assert kw["true_cfg_scale"] == 1.0
    assert kw["height"] == DEFAULT_HEIGHT
    assert kw["width"] == DEFAULT_WIDTH
    assert "negative_prompt" not in kw
    assert kw["guidance_scale"] == 1.0
    assert kw["generator"] is None
    auto = infer_kwargs("hello", size_auto=True)
    assert "height" not in auto
    assert "width" not in auto
    guided = infer_kwargs("hello", true_cfg=4.0, guidance=1.5, negative="bad")
    assert guided["negative_prompt"] == "bad"
    assert guided["guidance_scale"] == 1.5
    sized = infer_kwargs("hello", height=1024, width=576)
    assert sized["height"] == 1024
    assert sized["width"] == 576

    class FakeGen:
        def __init__(self, device=None):
            self.device = device

        def manual_seed(self, seed):
            self.seed = seed
            return self

    class FakeTorch:
        Generator = FakeGen

    seeded = infer_kwargs("hello", seed=7, torch_module=FakeTorch)
    assert seeded["generator"].device == "cpu"
    assert seeded["generator"].seed == 7


def test_tune_edit_vae_skips_missing_slicing():
    class TilingOnly:
        def enable_tiling(self, **kwargs):
            self.tiled = kwargs or True

    class Both:
        def enable_tiling(self):
            self.tiled = True

        def enable_slicing(self):
            self.sliced = True

    class Pipe:
        def __init__(self, vae):
            self.vae = vae

    tiling = TilingOnly()
    tune_edit_vae(Pipe(tiling))
    assert tiling.tiled == {"tile_sample_min_width": 256, "tile_sample_min_height": 256}

    both = Both()
    tune_edit_vae(Pipe(both))
    assert both.tiled is True
    assert both.sliced is True

    class NoVae:
        pass

    tune_edit_vae(NoVae())
    tune_edit_vae(Pipe(None))


def test_force_edit_offload_resets_to_cpu():
    calls: list[object] = []

    class Pipe:
        def maybe_free_model_hooks(self):
            calls.append("free")

        def to(self, dev):
            calls.append(("to", dev))
            return self

        def enable_attention_slicing(self):
            calls.append("slice")

        def enable_model_cpu_offload(self):
            calls.append("model")

        def enable_sequential_cpu_offload(self):
            calls.append("seq")

    assert force_edit_offload(Pipe()) == "model_cpu_offload"
    assert "free" in calls
    assert ("to", "cpu") in calls
    assert "model" in calls
    assert "seq" not in calls
    calls.clear()
    assert force_edit_offload(Pipe(), sequential=False) == "model_cpu_offload"
    assert "model" in calls
    calls.clear()
    assert force_edit_offload(Pipe(), sequential=True) == "sequential_cpu_offload"
    assert "seq" in calls
    assert is_cuda_oom(RuntimeError("CUDA out of memory. Tried to allocate"))
    assert not is_cuda_oom(RuntimeError("nope"))

    class Boom:
        def __init__(self):
            self.n = 0

        def __call__(self, **kwargs):
            self.n += 1
            if self.n == 1:
                raise RuntimeError("CUDA out of memory. Tried to allocate 108.00 MiB")

            class Out:
                images = ["ok"]

            return Out()

    class FakeCuda:
        @staticmethod
        def empty_cache():
            return None

    class FakeTorch:
        cuda = FakeCuda

    boom = Boom()
    assert run_pipe_edit(boom, ["im"], {"prompt": "x"}, FakeTorch) == "ok"
    assert boom.n == 2

    class Already:
        _qwen_edit_offload = "sequential_cpu_offload"

        def __init__(self):
            self.n = 0

        def __call__(self, **kwargs):
            self.n += 1
            raise RuntimeError("CUDA out of memory. Tried to allocate 108.00 MiB")

    already = Already()
    try:
        run_pipe_edit(already, ["im"], {"prompt": "x"}, FakeTorch)
        raise AssertionError("expected oom")
    except RuntimeError as err:
        assert "out of memory" in str(err).lower()
    assert already.n == 1


def test_lora_files_skip_uncensor_on_l4():
    assert "qwen_uncensor" not in lora_files_for_gpu(24.0)
    assert "remove_clothing" in lora_files_for_gpu(24.0)
    assert "CockQwen_v3" in lora_files_for_gpu(24.0)
    assert "qwen_uncensor" in lora_files_for_gpu(40.0)
    assert "qwen_uncensor" in lora_files_for_gpu()


def test_clamp_edit_vae_area_patches_loaded_module():
    class FakeMod:
        VAE_IMAGE_SIZE = 1024 * 1024

    sys.modules["diffusers.pipelines.qwenimage.pipeline_qwenimage_edit_plus"] = FakeMod
    try:
        assert clamp_edit_vae_area(None, 576, 1024) == 1024 * 1024
        assert FakeMod.VAE_IMAGE_SIZE == 1024 * 1024
    finally:
        del sys.modules["diffusers.pipelines.qwenimage.pipeline_qwenimage_edit_plus"]
    free_cuda()


def test_sex_preset_labels_match_space_ui():
    labels = sex_preset_labels()
    assert labels[:12] == list(SPACE_SEX_PRESET_LABELS)
    assert labels[12:17] == list(ANAL_POSE_LABELS)
    assert labels[17:20] == list(URINE_LABELS)
    assert labels[20:] == list(SCAT_LABELS)
    opts = sex_preset_form_options()
    assert opts[0] == SEX_PRESET_DEFAULT
    assert opts[1:] == labels
    assert set(SEX_ACT_PRESETS) <= set(labels)
    assert ANAL_PRESETS <= SEX_ACT_PRESETS
    assert "Qwen4Play_v2" in LORA_FILES


def test_futa_partner_rewrites_sex_acts_and_drops_man():
    man = re.compile(r"\b(?:man|man's|men|male pov)\b", re.I)
    subject_lock = "standing in front of the crotch"
    for label in (
        "フェラチオの視点",
        "宣教師",
        "カウガール",
        "乳房プレイ",
        "フェイシャル",
    ):
        assert is_sex_act_preset(label)
        raw = SEX_PRESETS[label]
        out = apply_futa_partner(raw)
        assert man.search(raw), label
        assert man.search(out) is None, (label, out)
        assert "futanari" in out.lower()
        assert "Not a man. The penis is a futanari" not in out
        composed = compose_edit_prompt("", preset=label, futa=True)
        assert not has_leftover_man(composed), label
        assert subject_lock not in composed
        if "penis" in raw.lower():
            assert "20cm" in composed
        else:
            assert "futanari" in composed.lower()
    lift_raw = SEX_PRESETS["肛門リフト"]
    assert man.search(lift_raw) is None
    assert "futanari" in lift_raw.lower()
    assert "anus" in lift_raw.lower()
    assert "not the upper front hole" in lift_raw.lower()
    lift = compose_edit_prompt("", preset="肛門リフト", futa=True)
    assert not has_leftover_man(lift)
    assert ANAL_FRONT_LOCK in lift


def test_compose_sex_act_strings():
    oral = compose_edit_prompt("", preset="フェラチオの視点")
    assert "oral sex" in oral.lower()
    assert "futanari POV" in oral
    mission = compose_edit_prompt("", preset="宣教師")
    assert "inserted" in mission.lower()
    assert "vagina" in mission.lower()
    cow = compose_edit_prompt("", preset="カウガール")
    assert "Cowgirl" in cow
    assert "futanari POV" in cow
    anal = compose_edit_prompt("", preset="肛門リフト")
    assert "anus" in anal.lower()
    assert "futanari" in anal.lower()
    bikini = compose_edit_prompt("", preset="ビキニ", undress=True, futa=True)
    assert "string bikini" in bikini
    assert "Remove only the clothes" not in bikini
    assert "20cm" not in bikini


def test_anal_pose_presets_are_futa_detailed():
    pose = {
        "アナルバック": ("doggy", "all fours"),
        "アナル立ちバック": ("standing",),
        "アナル正常位": ("missionary", "anus"),
        "アナル騎乗位": ("anal riding",),
        "アナル座位": ("lap", "seated"),
    }
    assert ANAL_REAR_PRESETS | ANAL_FRONT_PRESETS == ANAL_PRESETS
    assert ANAL_DETAIL == f"{ANAL_HOLE_LOCK} {ANAL_ANATOMY} {ANAL_JOIN}"
    for label, needles in pose.items():
        assert is_anal_preset(label)
        assert is_sex_act_preset(label)
        assert wants_anal_lock("", label)
        out = compose_edit_prompt("", preset=label, futa=True)
        assert not has_leftover_man(out), label
        assert "20cm" in out
        assert "pussy" in out.lower()
        assert "anus" in out.lower()
        assert "no testicles" in out.lower()
        assert "anal ring" in out.lower()
        assert "ANAL HOLE LOCK" in out
        assert "never vaginal" in out.lower()
        assert "unused pussy" in out.lower()
        assert ANAL_HOLE_LOCK in out
        assert ANAL_ANATOMY in out
        assert ANAL_JOIN in out
        assert ANAL_CLOSE in out
        assert out.lower().index("keep the exact same face") < out.index("ANAL HOLE LOCK")
        blob = out.lower()
        assert any(n in blob for n in needles), (label, out)
        assert out.index("ANAL HOLE LOCK") < blob.index(needles[0])
        names = [row[0] for row in lora_stack(True, True, preset=label)]
        assert names == ["qwen_uncensor", "CockQwen_v3"], label
        assert "Qwen4Play_v2" not in names
        trig = lora_stack(True, True, preset=label)[0][2]
        assert trig == UNCENSOR_ANAL_TRIGGER
        assert "vagina" not in trig
        if label in ANAL_REAR_PRESETS:
            assert ANAL_REAR_LOCK in out
            assert "UPPER hole" in out
        if label in ANAL_FRONT_PRESETS:
            assert ANAL_FRONT_LOCK in out
            assert "LOWER hole" in out
        assert "cowgirl" not in blob
    miss = compose_edit_prompt("", preset="アナル正常位")
    assert "not vaginal" in miss.lower() or "anal missionary" in miss.lower()
    lift = compose_edit_prompt("", preset="肛門リフト", futa=True)
    assert ANAL_HOLE_LOCK in lift
    assert ANAL_FRONT_LOCK in lift
    assert not has_leftover_man(lift)
    lift_names = [row[0] for row in lora_stack(True, True, preset="肛門リフト")]
    assert lift_names == ["qwen_uncensor", "CockQwen_v3"]
    custom = compose_edit_prompt("アナルでバックして", futa=True)
    assert ANAL_HOLE_LOCK in custom
    assert ANAL_JOIN in custom
    assert FUTA_LOCK not in custom
    cow_anal = [row[0] for row in lora_stack(True, True, preset="カウガール", extra="アナル")]
    assert "Qwen4Play_v2" not in cow_anal


def test_urine_and_scat_are_detailed_and_keep_face():
    for label in URINE_LABELS:
        assert is_urine_preset(label)
        assert is_excrete_preset(label)
        out = compose_edit_prompt("", preset=label, futa=True)
        assert "do not swap" in out.lower()
        assert "identical face" in out.lower()
        assert URINE_DETAIL in out
        assert "urethral opening" in out.lower()
        assert "yellow" in out.lower()
        assert "glans tip" in out.lower()
        assert "not from the pussy" in out.lower()
        assert not has_leftover_man(out), label
        names = [row[0] for row in lora_stack(True, True, preset=label)]
        assert names == ["qwen_uncensor", "CockQwen_v3"]
        assert "Qwen4Play_v2" not in names
    reward = compose_edit_prompt("", preset="ご褒美小便")
    assert "face" in reward.lower()
    assert "semen" in reward.lower()
    assert SCAT_DETAIL == f"{SCAT_HOLE_LOCK} {SCAT_ACT} {FECES_LOOK}"
    for label in SCAT_LABELS:
        assert is_scat_preset(label)
        assert wants_scat_lock("", label)
        out = compose_edit_prompt("", preset=label, futa=True)
        assert "do not swap" in out.lower()
        assert SCAT_HOLE_LOCK in out
        assert SCAT_ACT in out
        assert FECES_LOOK in out
        assert "SCAT HOLE LOCK" in out
        assert "anus" in out.lower()
        assert "stool log" in out.lower() or "sausage" in out.lower() or "turd" in out.lower()
        assert "front hole" in out.lower()
        assert "unused" in out.lower() or "front hole" in out.lower()
        assert "chocolate" in out.lower()
        assert "FECES LOOK" in out
        assert "cylindrical" in out.lower()
        assert "jelly" in out.lower()
        assert "turd" in out.lower()
        assert "coffee" in out.lower() or "soil" in out.lower()
        assert "two finger" in out.lower()
        assert out.index("SCAT HOLE LOCK") < out.lower().index("turd")
        assert not has_leftover_man(out), label
        names = [row[0] for row in lora_stack(True, True, preset=label)]
        assert names == ["qwen_uncensor", "CockQwen_v3"]
        trig = lora_stack(True, True, preset=label)[0][2]
        assert trig == UNCENSOR_SCAT_TRIGGER
        assert "vagina" not in trig
    cow_trig = lora_stack(True, True, preset="カウガール")[0][2]
    assert cow_trig == UNCENSOR_TRIGGER
    assert "vagina" in cow_trig
    assert lora_trigger("qwen_uncensor", "アナルバック") == UNCENSOR_ANAL_TRIGGER
    custom_scat = compose_edit_prompt("脱糞して", futa=True)
    assert SCAT_HOLE_LOCK in custom_scat
    assert FECES_LOOK in custom_scat
    assert FUTA_LOCK not in custom_scat


def test_lora_stack_sex_uses_qwen4play():
    names = [row[0] for row in lora_stack(True, True, preset="カウガール")]
    assert names == ["qwen_uncensor", "Qwen4Play_v2", "CockQwen_v3"]
    names = [row[0] for row in lora_stack(True, False, preset="フェラチオの視点")]
    assert names == ["qwen_uncensor", "Qwen4Play_v2"]
    assert lora_stack(True, True, preset="ビキニ") == []
    names = [row[0] for row in lora_stack(True, True)]
    assert names == ["remove_clothing"]


def test_style_presets_lock_medium():
    assert style_form_options() == [STYLE_PRESET_DEFAULT, *STYLE_LABELS]
    assert STYLE_LABELS == ("アニメ絵", "リアル", "3D", "漫画")
    assert "アニメ絵" in STYLE_PRESETS
    keep = compose_edit_prompt("")
    assert "keep the exact same art medium" in keep.lower()
    anime = compose_edit_prompt("", preset="服を脱ぐ", style="アニメ絵")
    assert "2D Japanese anime" in anime
    assert "Do not convert" in anime
    assert "Realistic nude body" not in anime
    undress_keep = compose_edit_prompt("", preset="服を脱ぐ")
    assert "Realistic nude body" not in undress_keep
    assert "do not swap" in undress_keep.lower()
    doggy = compose_edit_prompt("", preset="アナルバック")
    assert "do not swap" in doggy.lower()
    assert "identical face" in doggy.lower()
    assert "keep the exact same art medium" in doggy.lower()
    assert "input photo" not in doggy.lower()
    assert "phone-camera" not in doggy.lower()
    assert "original photo" not in doggy.lower()
    medium = STYLE_PRESETS[STYLE_PRESET_DEFAULT]
    assert doggy.lower().index("keep the exact same face") < doggy.lower().index(medium.lower())
    assert doggy.lower().index(medium.lower()) < doggy.index("ANAL HOLE LOCK")
    assert doggy.lower().endswith(medium.lower())
    lift = compose_edit_prompt("", preset="肛門リフト")
    assert "phone-camera" not in lift.lower()
    assert "natural indoor lighting" not in lift.lower()
    cow = compose_edit_prompt("", preset="カウガール")
    assert "input photo" not in cow.lower()
    assert "the photo" not in cow.lower()
    anime_anal = compose_edit_prompt("", preset="アナルバック", style="アニメ絵")
    assert "2D Japanese anime" in anime_anal
    assert "input photo" not in anime_anal.lower()
    real = compose_edit_prompt("", style="リアル")
    assert "photorealistic" in real.lower()
    cgi = compose_edit_prompt("", preset="アナルバック", style="3D")
    assert "3D CGI" in cgi
    assert "20cm" in cgi
    manga = compose_edit_prompt("", style="漫画")
    assert "manga" in manga.lower()
    assert "screentone" in manga.lower()
    assert "photorealistic" in style_negative("アニメ絵")
    assert "anime" in style_negative("リアル")
    try:
        apply_style("x", "油絵")
    except SystemExit as e:
        assert "unknown style" in str(e)
    else:
        raise AssertionError("bad style must exit")


def test_i2i_ref_and_drive_inputs(tmp_path):
    assert DRIVE_FREE_GIB == 2
    assert WEIGHTS_CACHE_GIB == 70
    blob = "\n".join(drive_space_lines())
    assert "i2i" in blob
    assert "2GB" in blob
    assert "21GB" in blob
    assert "Drive には載せない" in blob
    assert "A100" in blob
    assert "Phr00t" in blob
    assert input_source_form_options()[0] == "Drive input"
    assert REF_SOURCE_DEFAULT in ref_source_form_options()
    single = compose_edit_prompt("")
    assert "do not swap" in single.lower()
    assert "not text-to-image" not in single
    refed = compose_edit_prompt("", has_ref=True)
    assert "Picture 2" in refed
    assert "face lock of the same person" in refed
    assert "art medium" in refed.lower()
    assert not has_leftover_man(refed)
    doggy = compose_edit_prompt("", preset="アナルバック", has_ref=True)
    assert "Picture 2" in doggy
    assert "do not swap" in doggy.lower()
    assert is_photoreal_path("08-indoor-photoreal.jpg")
    assert is_photoreal_path("実写-shirt.png")
    assert not is_photoreal_path("01-stairs-harbor.jpg")
    try:
        refuse_photoreal("08-indoor-photoreal.jpg")
    except SystemExit as e:
        assert "実写の他人は入れるな" in str(e)
    else:
        raise AssertionError("photoreal must exit")
    ok = tmp_path / "01-stairs.png"
    ref = tmp_path / "face-lock.png"
    bad = tmp_path / "08-indoor-photoreal.jpg"
    Image.new("RGB", (64, 64), (1, 2, 3)).save(ok)
    Image.new("RGB", (80, 120), (4, 5, 6)).save(ref)
    Image.new("RGB", (32, 32), (7, 8, 9)).save(bad)
    (tmp_path / "notes.txt").write_text("nope", encoding="utf-8")
    kept, skipped = list_input_images(tmp_path, skip_name="face-lock.png")
    assert kept == [ok]
    assert skipped == [bad]
    src = Image.new("RGB", (1008, 1792), (10, 20, 30))
    face = Image.new("RGB", (640, 640), (40, 50, 60))
    canvas = resize_rgb(src, 576, 1024)
    locked = snapped_rgb(face)
    assert canvas.size == (576, 1024)
    assert locked.size == (640, 640)
    assert pipe_images(canvas) == [canvas]
    assert pipe_images(canvas, locked) == [canvas, locked]
    assert "スマホ" in UPLOAD_PHONE_HINT
    assert "Drive input" in UPLOAD_PHONE_HINT
    one, _ = resolve_input_paths(tmp_path, want_name="01-stairs.png", skip_name="face-lock.png")
    assert one == [ok]
    by_stem, _ = resolve_input_paths(tmp_path, want_name="01-stairs")
    assert by_stem == [ok]
    try:
        resolve_input_paths(tmp_path, want_name="missing.jpg")
    except SystemExit as e:
        assert "無い" in str(e)
        assert "01-stairs.png" in str(e)
    else:
        raise AssertionError("missing drive file must exit")


def test_writer_notebook_is_separate_a100_nsfw():
    ast.parse((ROOT / "qwen_image_edit_nsfw.py").read_text(encoding="utf-8"))
    ast.parse(WRITER.read_text(encoding="utf-8"))
    src = WRITER.read_text(encoding="utf-8")
    assert "Phr00t/Qwen-Image-Edit-Rapid-AIO" in src
    assert "Qwen-Rapid-AIO-NSFW-v23.safetensors" in src
    assert "Qwen/Qwen-Image-Edit-2511" in src
    assert '"gpuType": "A100"' in src
    assert "disable_safety" in src
    assert "from h3_lora_studio" not in src
    assert "import h3_lora_studio" not in src
    assert "minimax_h3_lora_studio" in src  # link only
    assert "同時に動かさない" in src
    assert "qwen-image-edit-nsfw/output" in src
    nb_path = ROOT.parent / "qwen_image_edit_nsfw.ipynb"
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    assert nb["metadata"]["colab"]["gpuType"] == "A100"
    joined = "".join("".join(c["source"]) for c in nb["cells"])
    assert "完全クローンではない" not in joined
    assert "Phr00t/Qwen-Image-Edit-Rapid-AIO" in joined
    assert "Qwen-Image-Edit-2511" in joined
    assert "disable_safety" in joined
    assert "files.upload" in joined
    assert "Drive input" in joined
    assert "参照画像" in joined
    assert "Picture 2" in joined
    assert "has_ref=" in src
    assert "pipe_images" in src
    assert "これは i2i" in joined
    assert "2GB" in joined
    assert "drive_space_lines" in src
    assert "PILLOW_COLAB_SPEC" in src
    assert "__PILLOW_SPEC__" in src
    assert "--no-cache-dir" in src
    assert "uninstall" in src
    assert "force-reinstall" not in src
    assert "drop_stale_pil_modules" in src
    assert '"huggingface_hub", "pillow"' not in src
    assert "pillow==11.3.0" in joined
    assert "pillow>=12.1.0" not in joined
    assert "torchao>=0.16.0" in joined
    assert "torchao==0.11.0" not in joined
    assert "FqnToConfig" in src
    assert "drop_stale_diffusers_modules" in src
    assert "require_torchao_for_git_diffusers" in src
    assert "require_torchao_for_git_diffusers" in joined
    assert 'uninstall", "-y", "torchao"' in src
    ao_at = src.find("require_torchao_for_git_diffusers")
    pipe_at = src.find("from diffusers import QwenImageEditPlusPipeline")
    assert 0 <= ao_at < pipe_at
    assert "git+https://github.com/huggingface/diffusers.git" in joined
    assert "preset=クイックプロンプト" in src
    assert "extra=PROMPT" in src
    assert "style_form_options" in src
    assert "画風" in src
    assert "画風は変換しない" in src
    assert "顔と画風の固定は必須" in src
    for label in (
        *SPACE_SEX_PRESET_LABELS,
        *ANAL_POSE_LABELS,
        *URINE_LABELS,
        *SCAT_LABELS,
        *STYLE_LABELS,
        "クイックプロンプト",
        "Qwen4Play",
        "入力のまま",
        "顔と画風の固定は必須",
        "Drive input",
        "参照画像",
        "i2i",
    ):
        assert label in joined
    assert "peft" in src
    assert "tune_edit_vae" in src
    assert "tune_edit_vae" in joined
    assert 'device_map="cuda"' not in src
    assert 'device_map="cuda"' not in joined
    assert 'hasattr(pipe, "enable_lora")' in src
    assert "①と②を実行" in joined
    assert "すべてのセルを実行" not in joined
    assert "lora_skip_summary" in src
    assert "drop_stale_torchao_modules" in src
    assert "place_edit_pipe" in src
    assert "load_aio_checkpoint" in src
    assert "quantize_transformer_fp8" in src
    assert "apply_space_scheduler" in src
    assert "rewrite_edit_prompt" in src
    assert "finalize_space_prompt" not in src
    assert "Blocked unsafe content" not in joined
    assert "auto_canvas_size" in src
    assert "run_pipe_edit" in src
    assert "VRAM_OFFLOAD_GIB" in src
    assert "sequential=True" not in src
    assert "lora_files_for_gpu" in src
    assert "clamp_edit_vae_area" in src
    assert "height=h" in src
    assert "width=w" in src
    assert "入力ファイル名" in src
    assert "PCから選ぶ" in src
    assert "KeyboardInterrupt" in src
    assert "UPLOAD_PHONE_HINT" in src
    assert "スマホ" in joined
    assert "resolve_input_paths" in src
    assert "WIDTH = 576" not in src
    assert "canvas" in src
    assert "追加LoRA" in src
    assert "プロンプトrewrite = False" in src
    assert "lock_identity_prompt" in src
    assert "style=画風" in src
    assert "pin_ends=True" in src
    assert "face_lock_image" in src
    assert "アナルは **肛門だけ**" in src or "肛門だけ" in joined
    assert "require_space_gpu_or_exit" in src


def test_aio_key_split_matches_comfy_and_diffusers():
    assert classify_aio_key("model.diffusion_model.img_in.weight") == (
        "transformer",
        "img_in.weight",
    )
    assert classify_aio_key("diffusion_model.img_in.weight") == (
        "transformer",
        "img_in.weight",
    )
    assert classify_aio_key("transformer.img_in.weight") == ("transformer", "img_in.weight")
    assert classify_aio_key("first_stage_model.decoder.conv.weight") == (
        "vae",
        "decoder.conv.weight",
    )
    assert classify_aio_key("vae.decoder.conv.weight") == ("vae", "decoder.conv.weight")
    assert classify_aio_key("conditioner.embedders.0.visual.weight") == (
        "text_encoder",
        "visual.weight",
    )
    assert classify_aio_key("text_encoder.model.norm.weight") == (
        "text_encoder",
        "model.norm.weight",
    )
    assert classify_aio_key("optimizer.step") is None
    buckets = split_aio_state_dict(
        {
            "model.diffusion_model.a": 1,
            "first_stage_model.b": 2,
            "text_encoder.c": 3,
            "noise": 4,
        }
    )
    assert buckets["transformer"] == {"a": 1}
    assert buckets["vae"] == {"b": 2}
    assert buckets["text_encoder"] == {"c": 3}

    class Mod:
        def __init__(self):
            self.loaded = None

        def load_state_dict(self, weights, strict=False):
            self.loaded = dict(weights)

            class Msg:
                missing_keys = ["x"]

            return Msg()

    class Pipe:
        transformer = Mod()
        vae = Mod()
        text_encoder = Mod()

    pipe = Pipe()
    stats = inject_aio_state(
        pipe,
        {
            "model.diffusion_model.img_in.weight": "t",
            "vae.decoder.conv.weight": "v",
        },
    )
    assert stats["transformer"] == 1
    assert stats["vae"] == 1
    assert pipe.transformer.loaded == {"img_in.weight": "t"}
    assert pipe.vae.loaded == {"decoder.conv.weight": "v"}
    assert stats["transformer_missing"] == 1


def test_space_scheduler_config_is_log3_8192():
    cfg = space_scheduler_config({"shift": 9})
    assert cfg["shift"] == 1.0
    assert cfg["base_shift"] == SCHED_BASE_SHIFT
    assert cfg["max_shift"] == SCHED_BASE_SHIFT
    assert cfg["max_image_seq_len"] == SCHED_MAX_IMAGE_SEQ_LEN
    assert cfg["time_shift_type"] == "exponential"
    assert cfg["use_dynamic_shifting"] is True

    class Sched:
        def __init__(self, config=None):
            self.config = config or {}

        @classmethod
        def from_config(cls, config):
            return cls(config)

    class Pipe:
        scheduler = Sched({"foo": 1})

    out = apply_space_scheduler(Pipe(), scheduler_cls=Sched)
    assert out.config["base_shift"] == SCHED_BASE_SHIFT
    assert out.config["foo"] == 1


def test_rewrite_and_safety_prompt():
    assert parse_rewritten_prompt('{"Rewritten": "keep face, remove shirt"}') == (
        "keep face, remove shirt"
    )
    assert parse_rewritten_prompt("```json\n{\"Rewritten\": \"a\"}\n```") == "a"
    assert rewrite_edit_prompt("hello", object(), token="", enabled=True) == "hello"
    assert rewrite_edit_prompt("hello", object(), token="x", enabled=False) == "hello"

    class Choice:
        def __init__(self):
            self.message = type("M", (), {"content": '{"Rewritten": "short edit"}'})()

    class Resp:
        choices = [Choice()]

    class Client:
        def __init__(self):
            self.chat = type(
                "C",
                (),
                {"completions": type("P", (), {"create": staticmethod(lambda **k: Resp())})()},
            )()

    img = Image.new("RGB", (32, 32), (1, 2, 3))
    out = rewrite_edit_prompt(
        "hello",
        img,
        token="hf_x",
        enabled=True,
        client_factory=lambda token: Client(),
    )
    assert out == "short edit"


def test_face_lock_image_and_identity_prompt():
    portrait = Image.new("RGB", (576, 1024), (10, 20, 30))
    crop = face_lock_image(portrait)
    assert crop.size[0] <= portrait.size[0]
    assert crop.size[1] < portrait.size[1]
    assert crop.size[0] % 32 == 0
    assert crop.size[1] % 32 == 0
    close = Image.new("RGB", (1024, 1024), (1, 2, 3))
    same = face_lock_image(close)
    assert same.size == snapped_rgb(close).size
    dirty = "Generate a new image of a woman. Remove only the clothes."
    out = lock_identity_prompt(dirty, has_ref=True)
    assert "generate a new image" not in out.lower()
    assert out.lower().startswith("keep the exact same face")
    assert "Picture 2" in out
    assert "do not swap" in out.lower()
    already = lock_identity_prompt(FACE_KEEP + " Remove only the clothes.")
    assert already.lower().startswith("keep the exact same face")
    assert already.count("Do not swap to a different person") == 1
    empty = compose_edit_prompt("")
    assert empty.lower().startswith("keep the exact same face")
    assert "do not redraw the face" in FUTA_LOCK.lower()
    assert "blocked unsafe content" not in empty.lower()
    assert "blocked unsafe content" not in lock_identity_prompt(empty, has_ref=True).lower()


def test_auto_canvas_and_place_pipe():
    im = Image.new("RGB", (1008, 1792), (10, 20, 30))
    w, h = auto_canvas_size(im)
    assert w % 32 == 0
    assert h % 32 == 0
    assert max(w, h) <= 2048
    small = auto_canvas_size(Image.new("RGB", (64, 80)))
    assert min(small) >= 256
    huge = auto_canvas_size(Image.new("RGB", (4000, 2000)))
    assert max(huge) <= 2048

    calls: list[object] = []

    class Pipe:
        def to(self, dev):
            calls.append(("to", dev))
            return self

        def maybe_free_model_hooks(self):
            calls.append("free")

        def enable_attention_slicing(self):
            calls.append("slice")

        def enable_model_cpu_offload(self):
            calls.append("model")

        def enable_sequential_cpu_offload(self):
            calls.append("seq")

    assert place_edit_pipe(Pipe(), 80.0) == "cuda"
    assert ("to", "cuda") in calls
    calls.clear()
    assert place_edit_pipe(Pipe(), 24.0) == "model_cpu_offload"
    assert "model" in calls
    assert "seq" not in calls
