"""Stub-based check of 0001-face-pass-mode.patch against the real planner.py and executor.py.

Usage: python check_face_pass.py <path to extensions/sd-diff-set>

Every module except planner.py, executor.py and regions.py is replaced by a small stub, so this
needs no GPU, no weights and no other factory file. It does not replace the factory's own unittest.
"""
import enum, importlib, sys, tempfile, types, unittest
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(sys.argv.pop(1))  # extensions/sd-diff-set

class DiffSetError(Exception):
    def __init__(self, code, message):
        super().__init__(message); self.code = code; self.message = message

class Strategy(enum.Enum): INPAINT = 1; COPY_BASE = 2
class MaskSource(enum.Enum): MANUAL = 1; BRUSH = 2; ADETAILER = 3
class Fallback(enum.Enum): BASE = 1; FAIL = 2
class Area(enum.Enum): ONLY_MASKED = "only_masked"

@dataclass
class Mask: source: object = MaskSource.MANUAL; adetailer_model: str | None = None
@dataclass
class Variant:
    id: str; strategy: object = Strategy.INPAINT; prompt_add: str = "x"; prompt_remove: tuple = ()
    negative_add: str = ""; negative_remove: tuple = (); face_prompt_add: str = ""; face_prompt_remove: tuple = ()
    face_negative_add: str = ""; face_negative_remove: tuple = (); init_from: str = "base"
    init_from_category: str = ""; init_from_variant: str = ""; fallback: object = Fallback.FAIL
    mask_source: object = None; denoise: float = 0.6
@dataclass
class Preset:
    id: str; label: str; order: int; variants: tuple; adult_only: bool = False; mask: Mask = field(default_factory=Mask)
    inpaint_area: object = Area.ONLY_MASKED; inpaint_full_res_padding: int = 32; mask_blur: int = 0
    inpainting_fill: int = 1; soft_inpainting: bool = False; controlnet: tuple = ()

def mod(name, **attrs):
    m = types.ModuleType(name); m.__dict__.update(attrs); sys.modules[name] = m; return m

pkg = types.ModuleType("sd_diff_set"); pkg.__path__ = [str(ROOT / "sd_diff_set")]; sys.modules["sd_diff_set"] = pkg
FACE_ERR = {"raise": None}
mod("sd_diff_set.errors", DiffSetError=DiffSetError)
mod("sd_diff_set.preset", Strategy=Strategy, MaskSource=MaskSource, Fallback=Fallback, Preset=Preset,
    VariantSpec=Variant, describe_strategy=lambda s: "inpaint" if s is Strategy.INPAINT else "copy_base")
mod("sd_diff_set.prompt_edit", edit_prompt=lambda p, add, rm: p + (", " + add if add else ""),
    dynamic_prompt_warning=lambda p: "", split_tags=lambda t: [x.strip() for x in t.split(",") if x.strip()])
mod("sd_diff_set.never", never=lambda v: (_ for _ in ()).throw(AssertionError(v)))
mod("sd_diff_set.router", blocked_token=lambda p: None, fluid_has_color=lambda p: True)
mod("sd_diff_set.settings", cloth_detect_enabled=lambda: False)
mod("sd_diff_set.naming", output_filename=lambda stem, i, c, v: f"{stem}_{i:03d}_diff-{c}-{v}.png", sanitize_stem=lambda s: s)
mod("sd_diff_set.cloth_detect", resolve_cloth_model=lambda: Path("x"), detect_cloth_mask=MagicMock())
mod("sd_diff_set.controlnet_units", build_units=lambda *a, **k: ([], []))
detect_calls = []
def detect_mask(image, model, dest):
    detect_calls.append(model)
    if FACE_ERR["raise"]:
        raise DiffSetError(FACE_ERR["raise"], "no face")
    Path(dest).write_bytes(b"mask"); return Path(dest)
mod("sd_diff_set.detectors", resolve_face_model=lambda m: Path(m), resolve_foot_model=lambda m: Path(m),
    resolve_hand_model=lambda m: Path(m), detect_mask=detect_mask, _clamp=MagicMock(), _raster_union=MagicMock(), _resolve_local_weight=lambda a, b: Path(a))
mod("sd_diff_set.masks", mask_source_name=lambda s: "manual", resolve_manual_mask=lambda *a: None, SMALL_HAND_MASK=0.2,
    dilate_mask=MagicMock(), intersect_masks=MagicMock(), resize_mask_nearest=MagicMock(), white_ratio=MagicMock())
mod("sd_diff_set.png_text", png_size=lambda p: (8, 8), read_mask_l=MagicMock(), read_rgb=MagicMock(), upsert_parameters=MagicMock(), write_l_png=MagicMock())
mod("sd_diff_set.infotext", Infotext=MagicMock(), format_parameters=lambda *a, **k: "params")
mod("sd_diff_set.pattern_set", ADDON_IDS=("cloth", "fluid"), PATTERN_IDS=("expr4", "fellatio", "scat", "anal", "vaginal"),
    face_denoise_for=lambda p, v: 0.55)
mod("sd_diff_set.cutout", write_transparent=lambda p: None)
mod("sd_diff_set.host", unmasked_has_stain=lambda *a: False)

planner = importlib.import_module("sd_diff_set.planner")
executor = importlib.import_module("sd_diff_set.executor")
regions = importlib.import_module("sd_diff_set.regions")

def anal_preset():
    return Preset("anal", "anal", 35, (
        Variant("imminent", face_prompt_add="half-closed eyes"),
        Variant("tip", init_from="imminent", face_prompt_add="half-closed eyes"),
        Variant("creampie", init_from="tip"),
    ), adult_only=True)

class Host(executor.GenerationHost):
    def __init__(self): self.painted = []
    def inpaint(self, job):
        self.painted.append(job.dest.name); job.dest.write_bytes(b"png")

def run(face_pass, detect_error):
    FACE_ERR["raise"] = detect_error
    plan = planner.build_plan(base_stem="b", presets=[anal_preset()], prompt="1girl", negative_prompt="",
                              seed=1, base_path=None, adult_ok=True, use_controlnet=False, face_pass=face_pass)
    tmp = Path(tempfile.mkdtemp()); base = tmp / "b.png"; base.write_bytes(b"png")
    info = MagicMock(); info.width = info.height = 8; info.seed = 1
    regions.assert_act_penis = lambda *a, **k: None
    executor.assert_act_penis = lambda *a, **k: None
    def fake_mask(item, image, out):
        path = out / "m.png"; path.write_bytes(b"m"); return path
    executor._mask_for_item = fake_mask
    host = Host()
    executor.execute(plan, base_path=base, output_dir=tmp / "out", info=info, host=host, dry_run=False, overwrite=False, use_controlnet=False)
    return plan, host

class T(unittest.TestCase):
    def test_default_is_unchanged(self):
        plan, host = run("required", None)
        by = {i.variant: i for i in plan.items}
        self.assertGreater(by["imminent"].face_denoise, 0); self.assertFalse(by["imminent"].face_optional)
        self.assertEqual(by["creampie"].face_denoise, 0)
        self.assertEqual([i.status for i in plan.items], ["ok", "ok", "ok"])
        self.assertEqual(sum(n.endswith(".face.png") for n in host.painted), 2)

    def test_required_still_stops_without_a_face(self):
        plan, _ = run("required", "mask_empty")
        by = {i.variant: i for i in plan.items}
        self.assertEqual((by["imminent"].status, by["imminent"].error_code), ("error", "mask_empty"))
        self.assertEqual(by["tip"].status, "blocked")

    def test_skip_plans_no_face_pass(self):
        plan, host = run("skip", "mask_empty")
        by = {i.variant: i for i in plan.items}
        self.assertEqual(by["imminent"].face_denoise, 0); self.assertEqual(by["imminent"].face_prompt, "")
        self.assertTrue(any("face_pass_skipped" in w for w in by["imminent"].warnings))
        self.assertEqual([i.status for i in plan.items], ["ok", "ok", "ok"])
        self.assertFalse(any(n.endswith(".face.png") for n in host.painted))

    def test_optional_continues_when_no_face_is_found(self):
        plan, host = run("optional", "mask_empty")
        by = {i.variant: i for i in plan.items}
        self.assertTrue(by["imminent"].face_optional)
        self.assertEqual([i.status for i in plan.items], ["ok", "ok", "ok"])
        self.assertTrue(any("face_pass_skipped" in w for w in by["imminent"].warnings))
        self.assertFalse(any(n.endswith(".face.png") for n in host.painted))

    def test_optional_with_a_face_still_paints_it(self):
        plan, host = run("optional", None)
        self.assertEqual(sum(n.endswith(".face.png") for n in host.painted), 2)
        self.assertFalse(any("face_pass_skipped" in w for i in plan.items for w in i.warnings))

    def test_optional_does_not_hide_other_detector_errors(self):
        plan, _ = run("optional", "mask_model_missing")
        by = {i.variant: i for i in plan.items}
        self.assertEqual((by["imminent"].status, by["imminent"].error_code), ("error", "mask_model_missing"))

    def test_bad_value_is_refused(self):
        with self.assertRaises(DiffSetError):
            planner.build_plan(base_stem="b", presets=[anal_preset()], prompt="p", negative_prompt="", seed=1,
                               base_path=None, adult_ok=True, use_controlnet=False, face_pass="maybe")

unittest.main(argv=["x"], verbosity=1)
