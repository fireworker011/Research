"""公開動画のURLから再生数といいね数を取る。

ログインもAPIトークンも使わない。yt-dlp は --skip-download でメタデータだけ見る。
既定は --dry-run（表示だけ）。results.md に足すのは --write のときだけ。
取れなかった数は推定せず「取得不可」。理由は標準エラーへ出す。
平均視聴維持は公開ページに無いので、常に「取得不可」。
同じURLを同じ日（測った日のJSTの日付）に二度は足さない。
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

JST = timezone(timedelta(hours=9))
UNAVAILABLE = "取得不可"
CSV_FIELDS = ("公開日", "ジャンル", "台本ファイル", "媒体", "URL")
TABLE_COLUMNS = (
    "公開日",
    "ジャンル",
    "台本ファイル",
    "媒体",
    "再生数",
    "平均視聴維持",
    "いいね",
    "測った日",
    "ひとこと",
)
RESULTS_HEADER = (
    "# 結果ログ\n"
    "\n"
    "| 公開日 | ジャンル | 台本ファイル | 媒体 | 再生数 | 平均視聴維持 | いいね | 測った日 | ひとこと |\n"
    "|---|---|---|---|---|---|---|---|---|\n"
)
YTDLP_ARGS = [
    "--ignore-config",
    "--no-cache-dir",
    "--skip-download",
    "--dump-single-json",
    "--no-warnings",
    "--no-playlist",
]
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com"}
TIKTOK_HOSTS = {"tiktok.com", "www.tiktok.com", "m.tiktok.com", "vm.tiktok.com", "vt.tiktok.com"}
Runner = Callable[[str], "CommandResult"]


class ValidationError(Exception):
    """入力の形が違う。ファイルは変えない。"""


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class InputRow:
    published: str
    genre: str
    script: str
    medium: str
    url: str


@dataclass(frozen=True)
class Counts:
    views: str
    likes: str
    reasons: tuple[str, ...]


def parser() -> argparse.ArgumentParser:
    tool = argparse.ArgumentParser(
        description="公開URLの再生数といいね数を results.md の表に足す。既定はドライラン。"
    )
    tool.add_argument("--csv", required=True, help="公開日,ジャンル,台本ファイル,媒体,URL")
    tool.add_argument("--results", default="results.md", help="追記先。既定は ./results.md")
    mode = tool.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="既定。表示だけ。ファイルは変えない")
    mode.add_argument("--write", action="store_true", help="results.md に1本1行を追記する")
    return tool


def main(
    argv: list[str] | None = None,
    runner: Runner | None = None,
    now: datetime | None = None,
) -> int:
    try:
        args = parser().parse_args(argv)
        return run(args, runner or default_runner, now or datetime.now(JST))
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 2


def run(args: argparse.Namespace, runner: Runner, now: datetime) -> int:
    if now.tzinfo is None:
        raise ValidationError("測った日にはタイムゾーンが要る")
    rows = load_csv(Path(args.csv))
    results_path = Path(args.results)
    stamp = now.astimezone(JST).strftime("%Y-%m-%d %H:%M:%S JST")
    day = stamp[:10]
    existing = results_path.read_text(encoding="utf-8") if results_path.is_file() else ""
    if args.write and existing and not _has_table_header(existing):
        raise ValidationError(f"表の見出しがありません: {results_path}")

    seen = _recorded_urls(existing, day)
    lines: list[str] = []
    for row in rows:
        if row.url in seen:
            print(f"追記しない: 同じURL・同じ日 {row.url} {day}")
            continue
        counts = fetch_counts(row.url, runner)
        for reason in counts.reasons:
            print(reason, file=sys.stderr)
        line = format_line(row, counts, stamp)
        print(line)
        lines.append(line)
        seen.add(row.url)

    if not args.write:
        print("DRY-RUN ファイルは変更していません。")
        return 0
    if lines:
        _append_lines(results_path, existing, lines)
    return 0


def load_csv(path: Path) -> list[InputRow]:
    if not path.is_file():
        raise ValidationError(f"CSVがありません: {path}")
    rows: list[InputRow] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        missing = [name for name in CSV_FIELDS if name not in fields]
        if missing:
            raise ValidationError("CSVの列が足りません: " + ",".join(missing))
        for index, raw in enumerate(reader, start=2):
            url = (raw.get("URL") or "").strip()
            published = (raw.get("公開日") or "").strip()
            genre = (raw.get("ジャンル") or "").strip()
            script = (raw.get("台本ファイル") or "").strip()
            medium = (raw.get("媒体") or "").strip()
            if not any((url, published, genre, script, medium)):
                continue
            if not url:
                raise ValidationError(f"{path} の {index} 行目にURLがありません")
            if any(char in url for char in "|\r\n"):
                raise ValidationError(f"{path} の {index} 行目のURLに改行または縦棒があります")
            rows.append(InputRow(published, genre, script, medium, url))
    if not rows:
        raise ValidationError(f"CSVに行がありません: {path}")
    return rows


def fetch_counts(url: str, runner: Runner) -> Counts:
    kind = url_kind(url)
    retention = f"平均視聴維持: 公開ページでは取れない ({url})"
    if kind is None:
        reason = f"再生数といいね: YouTube Shorts でも TikTok でもないURL ({url})"
        return Counts(UNAVAILABLE, UNAVAILABLE, (reason, retention))
    try:
        result = runner(url)
    except FileNotFoundError:
        reason = f"再生数といいね: yt-dlp コマンドが無い ({url})"
        return Counts(UNAVAILABLE, UNAVAILABLE, (reason, retention))
    except subprocess.TimeoutExpired:
        reason = f"再生数といいね: yt-dlp が時間内に終わらなかった ({url})"
        return Counts(UNAVAILABLE, UNAVAILABLE, (reason, retention))
    if result.returncode != 0:
        detail = _short_error(result.stderr)
        reason = f"再生数といいね: yt-dlp が終了コード {result.returncode} ({url})"
        if detail:
            reason = f"{reason} {detail}"
        return Counts(UNAVAILABLE, UNAVAILABLE, (reason, retention))
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        reason = f"再生数といいね: yt-dlp の出力がJSONではない ({url})"
        return Counts(UNAVAILABLE, UNAVAILABLE, (reason, retention))
    if not isinstance(payload, dict):
        reason = f"再生数といいね: yt-dlp のJSONがオブジェクトではない ({url})"
        return Counts(UNAVAILABLE, UNAVAILABLE, (reason, retention))
    views, view_reason = _count_field(payload, "view_count", "再生数", url)
    likes, like_reason = _count_field(payload, "like_count", "いいね", url)
    reasons = [reason for reason in (view_reason, like_reason, retention) if reason]
    return Counts(views, likes, tuple(reasons))


def url_kind(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None
    if parsed.username or parsed.password:
        return None
    host = (parsed.hostname or "").lower()
    path = parsed.path or ""
    if host in YOUTUBE_HOSTS and path.startswith("/shorts/"):
        return "youtube"
    if host in TIKTOK_HOSTS and path not in ("", "/"):
        return "tiktok"
    return None


def default_runner(url: str) -> CommandResult:
    completed = subprocess.run(
        ["yt-dlp", *YTDLP_ARGS, "--", url],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def format_line(row: InputRow, counts: Counts, stamp: str) -> str:
    cells = [
        row.published,
        row.genre,
        row.script,
        row.medium,
        counts.views,
        UNAVAILABLE,
        counts.likes,
        stamp,
        row.url,
    ]
    return "| " + " | ".join(_cell(value) for value in cells) + " |"


def split_cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    body = stripped[1:]
    if body.endswith("|"):
        body = body[:-1]
    cells: list[str] = []
    buf: list[str] = []
    escaped = False
    for char in body:
        if escaped:
            buf.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "|":
            cells.append("".join(buf).strip())
            buf = []
            continue
        buf.append(char)
    cells.append("".join(buf).strip())
    return cells


def _count_field(payload: dict[str, object], key: str, label: str, url: str) -> tuple[str, str | None]:
    if key not in payload or payload[key] is None:
        return UNAVAILABLE, f"{label}: {key} が応答に無い ({url})"
    value = payload[key]
    if isinstance(value, bool) or not isinstance(value, int):
        return UNAVAILABLE, f"{label}: {key} が整数ではない ({url})"
    if value < 0:
        return UNAVAILABLE, f"{label}: {key} が負の数 ({url})"
    return str(value), None


def _short_error(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""
    return lines[-1][:300]


def _cell(value: str) -> str:
    cleaned = value.replace("\r", " ").replace("\n", " ").strip()
    return cleaned.replace("|", "\\|")


def _has_table_header(text: str) -> bool:
    for line in text.splitlines():
        cells = split_cells(line)
        if cells is None:
            continue
        if cells[: len(TABLE_COLUMNS)] == list(TABLE_COLUMNS):
            return True
    return False


def _recorded_urls(text: str, day: str) -> set[str]:
    found: set[str] = set()
    comment_index = TABLE_COLUMNS.index("ひとこと")
    measured_index = TABLE_COLUMNS.index("測った日")
    for line in text.splitlines():
        cells = split_cells(line)
        if cells is None or len(cells) <= comment_index:
            continue
        if cells[0] == "公開日":
            continue
        measured = cells[measured_index]
        if not measured.startswith(day):
            continue
        url = cells[comment_index]
        if url:
            found.add(url)
    return found


def _append_lines(path: Path, existing: str, lines: list[str]) -> None:
    block = "".join(line + "\n" for line in lines)
    if not existing.strip():
        path.write_text(RESULTS_HEADER + block, encoding="utf-8")
        return
    prefix = existing if existing.endswith("\n") else existing + "\n"
    path.write_text(prefix + block, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
