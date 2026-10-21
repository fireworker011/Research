"""Read view and engagement counts the APIs actually return.

Click counts for affiliate links are not in these APIs. The click column stays blank.
Dry-run is the default. --fetch is the call that hits the network.
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import posting_lib as lib


def parser() -> argparse.ArgumentParser:
    tool = argparse.ArgumentParser(description="再生数などを取得する。初期状態はドライラン。")
    tool.add_argument("--channel", default="")
    tool.add_argument("--platform", choices=["youtube", "tiktok"], default="")
    tool.add_argument("--video-id", action="append", default=[])
    tool.add_argument("--from-csv", default="")
    tool.add_argument("--fetch", action="store_true", help="これを付けたときだけAPIを呼ぶ")
    tool.add_argument("--analytics", action="store_true", help="YouTube Analyticsの期間内再生数")
    tool.add_argument("--start-date", default="")
    tool.add_argument("--end-date", default="")
    tool.add_argument("--token-file", default="")
    return tool


def main(argv: list[str] | None = None) -> int:
    try:
        return run(parser().parse_args(argv))
    except lib.ChannelMismatch as exc:
        print(str(exc), file=sys.stderr)
        return 4
    except lib.ValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except lib.ApiError as exc:
        print(str(exc), file=sys.stderr)
        return 5


def rows_from_csv(path: Path) -> list[tuple[str, str, str]]:
    if not path.is_file():
        raise lib.ValidationError(f"CSVがありません: {path}")
    found: list[tuple[str, str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            video_id = (row.get("video_id") or "").strip()
            if not video_id or row.get("status") not in lib.DONE_STATUSES:
                continue
            found.append((row.get("platform") or "", row.get("channel_key") or "", video_id))
    return found


def run(args: argparse.Namespace) -> int:
    root = lib.ROOT
    jobs: list[tuple[str, str, str]] = []
    if args.from_csv:
        jobs.extend(rows_from_csv(Path(args.from_csv)))
    if args.video_id:
        if not args.channel or not args.platform:
            raise lib.ValidationError("--video-id には --platform と --channel を付けます。")
        jobs.extend((args.platform, args.channel, video_id) for video_id in args.video_id)
    if not jobs:
        raise lib.ValidationError("--from-csv か --video-id を指定します。")

    end = args.end_date or (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    start = args.start_date or (datetime.now(timezone.utc).date() - timedelta(days=28)).isoformat()
    print("クリック数はこのAPIでは取れません。列は空のままです。")
    if not args.fetch:
        print("DRY-RUN APIは呼んでいません。取得は --fetch を付けたときだけです。")
        for platform, channel, video_id in jobs:
            print(f"{platform}\t{channel}\t{video_id}")
        if args.analytics:
            print(f"YouTube Analytics 期間 {start} から {end}。期間内の再生数で、累計ではありません。")
        return 0

    lib.assert_attended(True)
    grouped: dict[tuple[str, str], list[str]] = {}
    for platform, channel, video_id in jobs:
        grouped.setdefault((platform, channel), [])
        if video_id not in grouped[(platform, channel)]:
            grouped[(platform, channel)].append(video_id)

    out = root / "stats.csv"
    for (platform, channel), video_ids in grouped.items():
        if platform == "youtube":
            write_youtube(root, out, channel, video_ids, args)
        elif platform == "tiktok":
            write_tiktok(root, out, channel, video_ids, args.token_file)
        else:
            raise lib.ValidationError(f"platform が不明です: {platform}")
    print(out)
    return 0


def blank_stat(**extra: str) -> dict[str, str]:
    row = {key: "" for key in lib.STATS_COLUMNS}
    row["fetched_at"] = lib.utc_now()
    row["click_count"] = ""
    row["click_note"] = lib.CLICK_NOTE
    row.update(extra)
    return row


def write_youtube(
    root: Path,
    out: Path,
    channel: str,
    video_ids: list[str],
    args: argparse.Namespace,
) -> None:
    creds = lib.google_credentials(root, channel, args.token_file)
    access = lib.google_access_token(creds)
    scope = str((creds.get("saved") or {}).get("scope") or "")
    if args.analytics and lib.YOUTUBE_ANALYTICS_SCOPE not in scope.split():
        raise lib.ValidationError(
            "このトークンに YouTube Analytics のスコープがありません。"
            "auth_youtube.py --with-analytics で許可し直します。"
        )
    end = args.end_date or (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    start = args.start_date or (datetime.now(timezone.utc).date() - timedelta(days=28)).isoformat()
    for offset in range(0, len(video_ids), 50):
        batch = video_ids[offset : offset + 50]
        items = {str(item.get("id")): item for item in lib.youtube_videos(access, batch)}
        for video_id in batch:
            item = items.get(video_id)
            stats = (item or {}).get("statistics") or {}
            period = ""
            if args.analytics:
                period = lib.youtube_analytics(access, video_id, start, end)
            row = blank_stat(
                platform="youtube",
                channel_key=channel,
                video_id=video_id,
                url=lib.watch_url(video_id) if item else "",
                view_count=str(stats["viewCount"]) if item and "viewCount" in stats else "",
                like_count=str(stats["likeCount"]) if item and "likeCount" in stats else "",
                comment_count=str(stats["commentCount"]) if item and "commentCount" in stats else "",
                analytics_period_views=period,
                analytics_start=start if args.analytics else "",
                analytics_end=end if args.analytics else "",
            )
            if item is None:
                row["click_note"] = lib.CLICK_NOTE + " このIDは応答にありませんでした。"
            lib.append_csv(out, lib.STATS_COLUMNS, row)


def write_tiktok(root: Path, out: Path, channel: str, video_ids: list[str], token_file: str) -> None:
    creds = lib.tiktok_credentials(root, channel, token_file)
    access = lib.tiktok_access_token(root, creds)
    for offset in range(0, len(video_ids), 20):
        batch = video_ids[offset : offset + 20]
        items = {str(item.get("id")): item for item in lib.tiktok_query(access, batch)}
        for video_id in batch:
            item = items.get(video_id)
            row = blank_stat(
                platform="tiktok",
                channel_key=channel,
                video_id=video_id,
                url=str(item.get("share_url") or "") if item else "",
                view_count=str(item["view_count"]) if item and "view_count" in item else "",
                like_count=str(item["like_count"]) if item and "like_count" in item else "",
                comment_count=str(item["comment_count"]) if item and "comment_count" in item else "",
                share_count=str(item["share_count"]) if item and "share_count" in item else "",
            )
            if item is None:
                row["click_note"] = lib.CLICK_NOTE + " このIDは応答にありませんでした。"
            lib.append_csv(out, lib.STATS_COLUMNS, row)


if __name__ == "__main__":
    sys.exit(main())
