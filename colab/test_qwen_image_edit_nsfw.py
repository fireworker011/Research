import ast
import json
import re
import sys
from pathlib import Path

from PIL import Image

from qwen_image_edit_nsfw import (
    ANAL_DETAIL,
    ANAL_POSE_LABELS,
    ANAL_PRESETS,
    DEFAULT_EDIT_PROMPT,
    DRIVE_FREE_GIB,
    FUTA_LOCK,
    KEEP_LOCK,
    LORA_FILES,
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    PILLOW_COLAB_SPEC,
    PIPE_ID,
    REF_SOURCE_DEFAULT,
    SCAT_DETAIL,
    SCAT_LABELS,
    SEX_ACT_PRESETS,
    SEX_PRESET_DEFAULT,
    SEX_PRESETS,
    SPACE_SEX_PRESET_LABELS,
    STEPS,
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
    apply_style,
    clamp_edit_vae_area,
    compose_edit_prompt,
    disable_safety,
    drop_stale_pil_modules,
    drop_stale_torchao_modules,
    drive_space_lines,
    force_edit_offload,
    free_cuda,
    has_leftover_man,
    infer_kwargs,
    is_cuda_oom,
    input_source_form_options,
    is_anal_preset,
    is_excrete_preset,
    is_photoreal_path,
    is_scat_preset,
    is_sex_act_preset,
    is_urine_preset,
    list_input_images,
    lora_files_for_gpu,
    lora_skip_summary,
    lora_stack,
    pipe_images,
    ref_source_form_options,
    refuse_photoreal,
    require_l4_or_exit,
    require_pillow_colab,
    resize_rgb,
    resolve_input_paths,
    run_pipe_edit,
    save_jpeg,
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
    assert TRANSFORMER_ID == "prithivMLmods/Qwen-Image-Edit-Rapid-AIO-V23"
    assert STEPS == 4
    assert TRUE_CFG == 1.0
    assert "20cm" in FUTA_LOCK
    assert "no testicles" in FUTA_LOCK
    assert "Change clothing only" in KEEP_LOCK
    assert "Remove only the clothes" in DEFAULT_EDIT_PROMPT


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
        require_l4_or_exit(15.0, "Tesla T4")
    except SystemExit as e:
        assert "L4" in str(e)
    else:
        raise AssertionError("T4 must exit")
    require_l4_or_exit(22.5, "L4")


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

    assert force_edit_offload(Pipe()) == "sequential_cpu_offload"
    assert "free" in calls
    assert ("to", "cpu") in calls
    assert "seq" in calls
    assert "model" not in calls
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
        "肛門リフト",
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
        "アナル騎乗位": ("cowgirl",),
        "アナル座位": ("lap", "seated"),
    }
    for label, needles in pose.items():
        assert is_anal_preset(label)
        assert is_sex_act_preset(label)
        out = compose_edit_prompt("", preset=label, futa=True)
        assert not has_leftover_man(out), label
        assert "20cm" in out
        assert "pussy" in out.lower()
        assert "anus" in out.lower()
        assert "no testicles" in out.lower()
        assert "anal ring" in out.lower()
        assert ANAL_DETAIL in out
        blob = out.lower()
        assert any(n in blob for n in needles), (label, out)
        names = [row[0] for row in lora_stack(True, True, preset=label)]
        assert names == ["qwen_uncensor", "Qwen4Play_v2", "CockQwen_v3"]
    miss = compose_edit_prompt("", preset="アナル正常位")
    assert "not vaginal" in miss.lower() or "anal missionary" in miss.lower()
    lift = compose_edit_prompt("", preset="肛門リフト", futa=True)
    assert ANAL_DETAIL in lift
    assert not has_leftover_man(lift)


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
    for label in SCAT_LABELS:
        assert is_scat_preset(label)
        out = compose_edit_prompt("", preset=label, futa=True)
        assert "do not swap" in out.lower()
        assert SCAT_DETAIL in out
        assert "anus" in out.lower()
        assert "stool log" in out.lower() or "sausage" in out.lower()
        assert "not the vagina" in out.lower() or "not from the vagina" in out.lower()
        assert "jelly" in out.lower()
        assert not has_leftover_man(out), label
        names = [row[0] for row in lora_stack(True, True, preset=label)]
        assert names == ["qwen_uncensor", "CockQwen_v3"]


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
    assert WEIGHTS_CACHE_GIB == 40
    blob = "\n".join(drive_space_lines())
    assert "i2i" in blob
    assert "2GB" in blob
    assert "21GB" in blob
    assert "Drive には載せない" in blob
    assert input_source_form_options()[0] == "Drive input"
    assert REF_SOURCE_DEFAULT in ref_source_form_options()
    single = compose_edit_prompt("")
    assert "do not swap" in single.lower()
    assert "not text-to-image" not in single
    refed = compose_edit_prompt("", has_ref=True)
    assert "Picture 2" in refed
    assert "face and art-medium lock" in refed
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


def test_writer_notebook_is_separate_l4_nsfw():
    ast.parse((ROOT / "qwen_image_edit_nsfw.py").read_text(encoding="utf-8"))
    ast.parse(WRITER.read_text(encoding="utf-8"))
    src = WRITER.read_text(encoding="utf-8")
    assert "prithivMLmods/Qwen-Image-Edit-Rapid-AIO-V23" in src
    assert "Qwen/Qwen-Image-Edit-2511" in src
    assert '"gpuType": "L4"' in src
    assert "disable_safety" in src
    assert "from h3_lora_studio" not in src
    assert "import h3_lora_studio" not in src
    assert "minimax_h3_lora_studio" in src  # link only
    assert "同時に動かさない" in src
    assert "qwen-image-edit-nsfw/output" in src
    nb_path = ROOT.parent / "qwen_image_edit_nsfw.ipynb"
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    assert nb["metadata"]["colab"]["gpuType"] == "L4"
    joined = "".join("".join(c["source"]) for c in nb["cells"])
    assert "完全クローンではない" in joined
    assert "Rapid-AIO-V23" in joined
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
    assert "preset=クイックプロンプト" in src
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
    assert 'device="cpu"' in src
    assert "①と②を実行" in joined
    assert "すべてのセルを実行" not in joined
    assert "lora_skip_summary" in src
    assert "uninstall\", \"-y\", \"torchao\"" in src or '"torchao"' in src
    assert "drop_stale_torchao_modules" in src
    assert "force_edit_offload" in src
    assert "run_pipe_edit" in src
    assert "VRAM_OFFLOAD_GIB" in src
    assert src.index("pipe.load_lora_weights") < src.index("force_edit_offload(pipe")
    assert "sequential=True" in src
    assert "lora_files_for_gpu" in src
    assert "clamp_edit_vae_area" in src
    assert "height=h" in src
    assert "width=w" in src
    assert "0/4" in src
    assert "入力ファイル名" in src
    assert "PCから選ぶ" in src
    assert "KeyboardInterrupt" in src
    assert "UPLOAD_PHONE_HINT" in src
    assert "スマホ" in joined
    assert "resolve_input_paths" in src
    assert "w, h = DEFAULT_WIDTH, DEFAULT_HEIGHT" in src
    assert "WIDTH = 576" not in src
    assert "canvas" in src
