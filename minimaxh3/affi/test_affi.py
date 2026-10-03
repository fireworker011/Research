"""CPU tests. The 2026-10-03 runs are the inputs. Nothing is generated or posted."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "colab"))
sys.path.insert(0, str(ROOT / "minimaxh3" / "grokbot"))

from h3_affi_prompt import validate_affi_prompt  # noqa: E402
from minimaxh3.affi.commonalities import load_commonalities  # noqa: E402
from minimaxh3.affi.inbox import remember_output, resolve_ref  # noqa: E402
from minimaxh3.affi.package import write_waiting  # noqa: E402
from minimaxh3.affi.pipeline import plan_one, run_batch  # noqa: E402
from minimaxh3.affi.products import PRODUCTS  # noqa: E402
from minimaxh3.affi.score import score_script  # noqa: E402
from minimaxh3.affi.script import load_pattern  # noqa: E402

READY = ROOT / "minimaxh3" / "affi" / "fixtures" / "commonalities-ready.yaml"
BLANK = ROOT / "research" / "affi" / "commonalities.yaml"
PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
    b"\x00\x00\x00\x03\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _refs(tmp: Path) -> Path:
    folder = tmp / "refs"
    folder.mkdir()
    (folder / "sakura-ref.jpg").write_bytes(PNG)
    (folder / "dog-ref.jpg").write_bytes(PNG)
    return folder


def test_repo_refs_resolve_without_a_new_face() -> None:
    dog = resolve_ref("dog", None)
    sakura = resolve_ref("sakura", None)
    assert dog is not None and dog.name == "dog-ref.jpg"
    assert sakura is not None
    assert sakura.name in {"sakura-ref.jpg", "sakura_916.jpg"}


def test_blank_report_stays_unknown_and_does_not_enqueue(tmp_path: Path) -> None:
    doc = load_commonalities(BLANK)
    assert all(cell["pattern_id"] == "不明" for cell in doc["cells"])
    assert all(cell["growing_n"] == "不明" for cell in doc["cells"])
    assert len(doc["cells"]) == 9
    refs = _refs(tmp_path)
    plan = plan_one(BLANK, "kanetora", "youtube", ref_dir=refs, extra_roots=[])
    assert plan["verdict"] == "直す"
    assert plan["reason"] == "共通点が不明"
    assert plan["growing_n"] == "不明"
    result = run_batch(BLANK, "all", "youtube", 3, tmp_path / "drive", ref_dir=refs, extra_roots=[])
    assert result["inbox"] is None
    assert not list((tmp_path / "drive" / "inbox").glob("*")) if (tmp_path / "drive" / "inbox").exists() else True


def test_three_runs_score_usable_and_one_inbox_job(tmp_path: Path) -> None:
    refs = _refs(tmp_path)
    for product_id, pattern_id in (
        ("kanetora", "introduce"),
        ("orbis", "buy_before"),
        ("furbo", "missing_on_camera"),
    ):
        script = load_pattern(pattern_id)
        scored = score_script(script, PRODUCTS[product_id])
        assert scored["verdict"] == "使える", scored
        assert scored["total"] == 80
        assert set(scored["axes"]) == {"最初3秒", "テンポ", "見やすさ", "プロフィール誘導", "リスク"}
    drive = tmp_path / "drive"
    result = run_batch(READY, "all", "youtube", 3, drive, ref_dir=refs, extra_roots=[])
    assert [item["verdict"] for item in result["plans"]] == ["使える", "使える", "使える"]
    assert result["inbox"]["enqueued"] is True
    assert result["waiting_parts"] == 5
    inbox = list((drive / "inbox").iterdir())
    assert len(inbox) == 1
    job = json.loads((inbox[0] / "job.json").read_text(encoding="utf-8"))
    assert job["schema"] == "h3-i2v-job/v1"
    assert job["prompt_kind"] == "affi-fl2va"
    assert job["imagine"]["enabled"] is False
    assert job["created_by"] == "affi-shorts"
    assert job["width"] == 768 and job["height"] == 1344
    assert "http" not in json.dumps(job)
    assert validate_affi_prompt(job["prompt"]) == []
    again = run_batch(READY, "all", "youtube", 3, drive, ref_dir=refs, extra_roots=[])
    assert again["inbox"] is None or again["inbox"].get("enqueued") is False
    assert len(list((drive / "inbox").iterdir())) == 1


def test_forbidden_line_is_discarded() -> None:
    script = load_pattern("introduce")
    script["beats"][0]["spoken"] = "これは必ず治る。"
    scored = score_script(script, PRODUCTS["kanetora"])
    assert scored["verdict"] == "捨てる"
    assert scored["axes"]["リスク"] == 0


def test_missing_ref_does_not_enter_inbox(tmp_path: Path) -> None:
    plan = plan_one(READY, "orbis", "youtube", ref_dir=tmp_path / "empty", extra_roots=[])
    assert plan["verdict"] == "直す"
    assert "sakura-ref.jpg" in plan["reason"] or "sakura" in plan["reason"]
    result = run_batch(
        READY, "orbis", "youtube", 1, tmp_path / "drive", ref_dir=tmp_path / "empty", extra_roots=[]
    )
    assert result["inbox"] is None


def test_tiktok_cell_stays_unknown() -> None:
    plan = plan_one(READY, "kanetora", "tiktok", extra_roots=[])
    assert plan["verdict"] == "直す"
    assert plan["pattern_id"] == "不明"


def test_i2v_prepare_accepts_affi_prompt(tmp_path: Path) -> None:
    from engine import prepare_i2v

    refs = _refs(tmp_path)
    drive = tmp_path / "drive"
    result = run_batch(READY, "orbis", "youtube", 1, drive, ref_dir=refs, extra_roots=[])
    assert result["inbox"]["mode"] == "i2v"
    folder = Path(result["inbox"]["folder"])
    job = json.loads((folder / "job.json").read_text(encoding="utf-8"))
    prepare_i2v(folder, job, drive, dry_run=True)
    saved = json.loads((folder / "job.json").read_text(encoding="utf-8"))
    assert saved["status"] == "queued"
    assert "Picture 1" in saved["prompt"]
    assert "hoodie" not in saved["prompt"].lower()
    assert (folder / "source.jpg").is_file()


def test_package_writes_disclosure_and_does_not_post(tmp_path: Path) -> None:
    refs = _refs(tmp_path)
    drive = tmp_path / "drive"
    first = run_batch(READY, "kanetora", "youtube", 1, drive, ref_dir=refs, extra_roots=[])
    _finish(Path(first["inbox"]["folder"]), tmp_path / "a.mp4")
    second = run_batch(READY, "kanetora", "youtube", 1, drive, ref_dir=refs, extra_roots=[])
    assert second["inbox"]["mode"] == "i2v"
    _finish(Path(second["inbox"]["folder"]), tmp_path / "b.mp4")
    wrote = write_waiting(drive, tmp_path / "waiting")
    assert len(wrote) == 1
    desc = (wrote[0] / "description.txt").read_text(encoding="utf-8")
    assert desc.startswith("アフィリエイト広告を含みます #PR")
    assert "AI" in desc
    voice = (wrote[0] / "voice.txt").read_text(encoding="utf-8")
    assert "Achernar" in voice
    assert "H3の声: 使わない" in voice
    assert "プロフィール" in (wrote[0] / "subtitles.srt").read_text(encoding="utf-8")
    assert (wrote[0] / "POST.txt").read_text(encoding="utf-8").startswith("投稿は人間が押す")
    assert (wrote[0] / "part-6s.mp4").is_file()
    assert (wrote[0] / "part-9s.mp4").is_file()


def _finish(folder: Path, mp4: Path) -> None:
    mp4.write_bytes(b"mp4")
    dest = folder.parents[1] / "done" / folder.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(folder), str(dest))
    remember_output(dest, mp4)
