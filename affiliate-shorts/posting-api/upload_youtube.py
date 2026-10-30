"""Upload one mp4 to a YouTube channel listed in channels.json.

Dry-run is the default. Adding --publish is the only way to upload.
Run it by hand. Do not put it on a schedule or in GitHub Actions.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import posting_lib as lib


def parser() -> argparse.ArgumentParser:
    tool = argparse.ArgumentParser(description="YouTubeへ1本上げる。初期状態はドライラン。")
    tool.add_argument("--channel", required=True, help="channels.json の key")
    tool.add_argument("--video", required=True, help="mp4 のパス")
    tool.add_argument("--title", required=True)
    tool.add_argument("--description", default=None)
    tool.add_argument("--description-file", default=None)
    tool.add_argument("--privacy", required=True, choices=sorted(lib.YOUTUBE_PRIVACY))
    tool.add_argument("--schedule", default="", help="例: 2026-10-22T21:00:00+09:00")
    tool.add_argument("--category-id", required=True, help="videoCategories.list の数字")
    tool.add_argument("--language", default="ja")
    kids = tool.add_mutually_exclusive_group(required=True)
    kids.add_argument("--made-for-kids", action="store_true")
    kids.add_argument("--not-made-for-kids", action="store_true")
    tool.add_argument("--synthetic-media", action="store_true")
    tool.add_argument("--a8", action="store_true", help="説明にアフィリエイト開示が必須")
    tool.add_argument("--no-notify", action="store_true")
    tool.add_argument("--publish", action="store_true", help="これを付けたときだけ投稿する")
    tool.add_argument("--client-file", default="", help="client_secret のJSONファイル")
    tool.add_argument("--client-dir", default="", help="このフォルダ内の client_secret_*.json を1つだけ使う")
    tool.add_argument("--token-file", default="")
    tool.add_argument("--allow-duplicate", action="store_true")
    tool.add_argument("--channels-file", default="")
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


def run(args: argparse.Namespace) -> int:
    root = lib.ROOT
    description = lib.resolve_description(args.description, args.description_file)
    lib.assert_youtube_text(args.title, description)
    lib.assert_disclosure(description, args.a8)
    lib.assert_no_affiliate_url(args.title, description)
    warning = lib.link_warning(args.title, description)
    privacy_status, publish_at, schedule_note = lib.youtube_status(args.privacy, args.schedule)
    video = Path(args.video)
    size = lib.assert_video_file(video)
    body, part = lib.build_youtube_body(
        title=args.title,
        description=description,
        category_id=args.category_id,
        language=args.language,
        privacy_status=privacy_status,
        publish_at=publish_at,
        made_for_kids=args.made_for_kids,
        synthetic=args.synthetic_media,
        a8=args.a8,
    )
    channels = lib.load_channels(
        Path(args.channels_file) if args.channels_file else root / "channels.json"
    )
    channel = lib.find_channel(channels, "youtube", args.channel)
    digest = lib.sha256_file(video)
    plan = {
        "dry_run": not args.publish,
        "platform": "youtube",
        "channel": args.channel,
        "login_label": channel.get("login_label") or "",
        "title": args.title,
        "privacy_argument": args.privacy,
        "privacy_sent": privacy_status,
        "publish_at": publish_at or "",
        "category_id": args.category_id,
        "made_for_kids": args.made_for_kids,
        "a8": args.a8,
        "paid_product_placement": args.a8,
        "synthetic_media": args.synthetic_media,
        "bytes": size,
        "sha256": digest,
        "note": schedule_note,
        "link_warning": warning,
    }
    if not args.publish:
        print("DRY-RUN 投稿していません。本番は --publish を付けたときだけです。")
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    lib.assert_attended(True)
    posted = root / "posted.csv"
    if not args.allow_duplicate and lib.already_posted(posted, "youtube", args.channel, digest):
        raise lib.ValidationError("同じファイルは既に posted.csv にあります。やり直すなら --allow-duplicate。")
    creds = lib.google_credentials(
        root,
        args.channel,
        args.token_file,
        channel=channel,
        client_file=args.client_file,
        client_dir=args.client_dir,
    )
    access = lib.google_access_token(creds)
    channel_id, actual_title, custom_url = lib.youtube_mine(access)
    lib.require_channel_match(channel, actual_title, custom_url)
    uploaded = lib.youtube_insert(
        access,
        video,
        body,
        part,
        notify=not args.no_notify,
    )
    video_id = str(uploaded["id"])
    url = lib.watch_url(video_id)
    status = "scheduled" if publish_at else "uploaded"
    lib.append_csv(
        posted,
        lib.POSTED_COLUMNS,
        {
            "recorded_at": lib.utc_now(),
            "platform": "youtube",
            "channel_key": args.channel,
            "mode": "publish",
            "video_id": video_id,
            "publish_id": "",
            "url": url,
            "privacy": args.privacy,
            "scheduled_at": publish_at or "",
            "title": args.title,
            "a8": "yes" if args.a8 else "no",
            "status": status,
            "file_sha256": digest,
            "note": " ".join(part for part in (schedule_note, warning, f"youtube_channel={channel_id}") if part),
        },
    )
    print(url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
