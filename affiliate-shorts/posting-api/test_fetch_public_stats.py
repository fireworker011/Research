"""公開URLの数字取り。ネットワークには出ない。"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import fetch_public_stats as stats

JST = timezone(timedelta(hours=9))
NOW = datetime(2026, 10, 27, 7, 5, 9, tzinfo=JST)
URL = "https://www.youtube.com/shorts/abcdefghijk"
HEADER = (
    "# 結果ログ\n"
    "\n"
    "| 公開日 | ジャンル | 台本ファイル | 媒体 | 再生数 | 平均視聴維持 | いいね | 測った日 | ひとこと |\n"
    "|---|---|---|---|---|---|---|---|---|\n"
)
EXPECTED = (
    f"| 2026-10-26 | ペット | pet-06.md | YouTube Shorts | 17 | 取得不可 | 3 "
    f"| 2026-10-27 07:05:09 JST | {URL} |"
)


def _forbid_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("ネットワークに出た")

    monkeypatch.setattr(stats.subprocess, "run", fail)


def _csv(path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def _success_runner(_url: str) -> stats.CommandResult:
    return stats.CommandResult(0, '{"view_count": 17, "like_count": 3}\n', "")


def test_dry_run_does_not_write_and_write_appends_one_row(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _forbid_network(monkeypatch)
    csv_path = tmp_path / "urls.csv"
    results_path = tmp_path / "results.md"
    missing_path = tmp_path / "missing.md"
    _csv(
        csv_path,
        "公開日,ジャンル,台本ファイル,媒体,URL\n"
        f"2026-10-26,ペット,pet-06.md,YouTube Shorts,{URL}\n",
    )
    results_path.write_text(HEADER, encoding="utf-8")
    before = results_path.read_bytes()

    dry = stats.main(
        ["--csv", str(csv_path), "--results", str(results_path), "--dry-run"],
        runner=_success_runner,
        now=NOW,
    )
    assert dry == 0
    assert results_path.read_bytes() == before
    dry_missing = stats.main(
        ["--csv", str(csv_path), "--results", str(missing_path)],
        runner=_success_runner,
        now=NOW,
    )
    assert dry_missing == 0
    assert not missing_path.exists()

    code = stats.main(
        ["--csv", str(csv_path), "--results", str(results_path), "--write"],
        runner=_success_runner,
        now=NOW,
    )
    assert code == 0
    text = results_path.read_text(encoding="utf-8")
    assert text.startswith(HEADER)
    data_rows = [line for line in text.splitlines() if line.startswith("| 2026-10-26 |")]
    assert data_rows == [EXPECTED]
    cells = stats.split_cells(data_rows[0])
    assert cells is not None
    assert cells[4] == "17"
    assert cells[5] == "取得不可"
    assert cells[6] == "3"
    assert cells[7] == "2026-10-27 07:05:09 JST"
    assert cells[8] == URL


def test_fetch_failure_records_unavailable_and_stderr(
    tmp_path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _forbid_network(monkeypatch)
    csv_path = tmp_path / "urls.csv"
    results_path = tmp_path / "results.md"
    _csv(
        csv_path,
        "公開日,ジャンル,台本ファイル,媒体,URL\n"
        "2026-10-26,金メモ,kane-11.md,TikTok,https://www.tiktok.com/@example/video/1234567890\n",
    )

    def fail(_url: str) -> stats.CommandResult:
        return stats.CommandResult(1, "", "ERROR: Video unavailable")

    code = stats.main(
        ["--csv", str(csv_path), "--results", str(results_path), "--write"],
        runner=fail,
        now=NOW,
    )
    assert code == 0
    text = results_path.read_text(encoding="utf-8")
    data_rows = [line for line in text.splitlines() if line.startswith("| 2026-10-26 |")]
    assert len(data_rows) == 1
    cells = stats.split_cells(data_rows[0])
    assert cells is not None
    assert cells[4] == "取得不可"
    assert cells[5] == "取得不可"
    assert cells[6] == "取得不可"
    assert "17" not in text
    captured = capsys.readouterr()
    assert "Video unavailable" in captured.err
    assert "平均視聴維持: 公開ページでは取れない" in captured.err
    assert "推定" not in text


def test_same_url_same_day_is_not_appended_twice(
    tmp_path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _forbid_network(monkeypatch)
    csv_path = tmp_path / "urls.csv"
    results_path = tmp_path / "results.md"
    _csv(
        csv_path,
        "公開日,ジャンル,台本ファイル,媒体,URL\n"
        f"2026-10-26,ペット,pet-06.md,YouTube Shorts,{URL}\n",
    )
    calls = {"count": 0}

    def counting(_url: str) -> stats.CommandResult:
        calls["count"] += 1
        if calls["count"] > 1:
            return stats.CommandResult(0, '{"view_count": 99, "like_count": 1}\n', "")
        return _success_runner(_url)

    first = stats.main(
        ["--csv", str(csv_path), "--results", str(results_path), "--write"],
        runner=counting,
        now=NOW,
    )
    assert first == 0
    after_first = results_path.read_bytes()
    later = datetime(2026, 10, 27, 18, 0, 0, tzinfo=JST)
    capsys.readouterr()

    dry = stats.main(
        ["--csv", str(csv_path), "--results", str(results_path), "--dry-run"],
        runner=counting,
        now=later,
    )
    assert dry == 0
    assert results_path.read_bytes() == after_first
    second = stats.main(
        ["--csv", str(csv_path), "--results", str(results_path), "--write"],
        runner=counting,
        now=later,
    )
    assert second == 0
    assert results_path.read_bytes() == after_first
    text = results_path.read_text(encoding="utf-8")
    assert text.count(URL) == 1
    assert "99" not in text
    assert calls["count"] == 1
    captured = capsys.readouterr()
    assert "追記しない: 同じURL・同じ日" in captured.out
