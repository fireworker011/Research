"""Build small neutral projects in a temp folder."""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

SCENES = """category,subcategory,pose,diff_stage,positive_prompt,negative_prompt
sprite,idle,standing,01,"solo, 1girl, standing, {red hair|blue hair|green hair}, portrait composition","low quality"
sprite,wave,standing,02,"solo, 1girl, waving, {red hair|blue hair|green hair}, portrait composition","low quality"
lantern,dim,holding,01,"solo, 1girl, holding lantern, looking at viewer, portrait composition","low quality"
lantern,bright,holding,02,"solo, 1girl, holding lantern, looking at viewer, portrait composition","low quality"
lantern,flare,holding,03,"solo, 1girl, holding lantern, looking at viewer, portrait composition","low quality"
sprite,sheet,multi,sheet,"1girl, character sheet, portrait composition","low quality"
"""

CHAINS = """chains:
  lantern_light:
    category: lantern
    base: 4
    route_tags: [glow]
    stage_order: [dim, bright, flare]
    scenes: {3: dim, 4: bright, 5: flare}
    needs_face_visible: true
"""

LORAS = """loras:
  red hair: {file: red_hair_lora, weight: 0.8}
"""

PROJECT = """schema: 1
project: demo
paths:
  out_root: out
  scenes_csv: scenes.csv
  chains: chains.yaml
  loras: loras.yaml
  negatives: negatives.yaml
columns:
  section: category
  positive: positive_prompt
  negative: negative_prompt
  id_columns: [pose, diff_stage]
trials:
  count: 3
  order: trial_major
batch:
  max_jobs: 50
face_visible_hints: [looking at viewer]
safety:
  adult_confirmed_by: ""
  adult_confirmed_on: ""
cutout:
  templates:
    ps1: 'tool cutout --input {input}'
    sh: 'tool cutout --input {input}'
backend:
  name: import_only
  options:
    source_dir: incoming
"""


def make_project(root: Path, *, project: str = PROJECT, scenes: str = SCENES, chains: str = CHAINS) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "project.yaml").write_text(textwrap.dedent(project), encoding="utf-8")
    (root / "scenes.csv").write_text(scenes, encoding="utf-8")
    (root / "chains.yaml").write_text(chains, encoding="utf-8")
    (root / "loras.yaml").write_text(LORAS, encoding="utf-8")
    (root / "negatives.yaml").write_text("always: [watermark]\nby_section: {}\n", encoding="utf-8")
    return root


def write_image(path: Path, color: tuple[int, int, int, int] = (200, 30, 30, 255), size: tuple[int, int] = (32, 48)) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", size, color).save(path)
    return path
