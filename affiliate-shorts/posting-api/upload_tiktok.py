"""Upload one mp4 to a TikTok account listed in channels.json.

Dry-run is the default. --publish sends the file.
--inbox sends a draft (video.upload). Without it, Direct Post (video.publish) is used.
TikTok has no scheduled-publish field.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import posting_lib as lib


def parser() -> argparse.ArgumentParser:
    tool = argparse.ArgumentParser(description="TikTokへ1本上げる。初期状態はドライラン。")
    tool.add_argument("--channel", required=True, help="channels.json の key")
    tool.add_argument("--video", required=True, help="mp4 のパス")
    tool.add_argument("--title", required=True)
    tool.add_argument("--description", default=None)
    tool.add_argument("--description-file", default=None)
    tool.add_argument("--privacy", required=True, choices=sorted(lib.TIKTOK_PRIVACY))
    tool.add_argument("--schedule", default="", help="TikTokでは使えません")
    tool.add_argument("--a8", action="store_true")
    tool.add_argument("--synthetic-media", action="store_true", help="AI生成なら付ける。is_aigc になる")
    tool.add_argument("--inbox", action="store_true", help="下書きを受信箱へ送る")
    tool.add_argument("--publish", action="store_true", help="これを付けたときだけ送信する")
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
    lib.reject_tiktok_schedule(args.schedule)
    description = lib.resolve_description(args.description, args.description_file)
    caption = lib.tiktok_caption(args.title, description)
    lib.assert_disclosure(caption, args.a8)
    lib.assert_no_affiliate_url(args.title, description)
    warning = lib.link_warning(args.title, description)
    video = Path(args.video)
    size = lib.assert_video_file(video)
    chunk_size, chunk_count, slices = lib.tiktok_chunk_plan(size)
    channels = lib.load_channels(
        Path(args.channels_file) if args.channels_file else root / "channels.json"
    )
    channel = lib.find_channel(channels, "tiktok", args.channel)
    digest = lib.sha256_file(video)
    privacy_level = lib.TIKTOK_PRIVACY[args.privacy]
    plan = {
        "dry_run": not args.publish,
        "platform": "tiktok",
        "channel": args.channel,
        "login_label": channel.get("login_label") or "",
        "mode": "inbox" if args.inbox else "direct",
        "caption": caption,
        "privacy_level": privacy_level if not args.inbox else "",
        "brand_content_toggle": bool(args.a8),
        "is_aigc": bool(args.synthetic_media),
        "bytes": size,
        "chunk_size": chunk_size,
        "total_chunk_count": chunk_count,
        "sha256": digest,
        "link_warning": warning,
        "note": (
            "inboxではキャプション、公開範囲、AI表示をAPIで付けられません。アプリの受信箱で入れます。"
            if args.inbox
            else ""
        ),
    }
    if not args.publish:
        print("DRY-RUN 投稿していません。本番は --publish を付けたときだけです。")
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    lib.assert_attended(True)
    posted = root / "posted.csv"
    if not args.allow_duplicate and lib.already_posted(posted, "tiktok", args.channel, digest):
        raise lib.ValidationError("同じファイルは既に posted.csv にあります。やり直すなら --allow-duplicate。")
    creds = lib.tiktok_credentials(root, args.channel, args.token_file)
    access = lib.tiktok_access_token(root, creds)
    open_id, display_name = lib.tiktok_user(access)
    lib.require_channel_match(channel, display_name, "")

    if args.inbox:
        init = lib.tiktok_init(
            access,
            "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/",
            {
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": size,
                    "chunk_size": chunk_size,
                    "total_chunk_count": chunk_count,
                }
            },
        )
    else:
        creator = lib.tiktok_creator(access)
        options = creator.get("privacy_level_options") or []
        if privacy_level not in options:
            raise lib.ValidationError(
                f"このアカウントに {privacy_level} は選べません。選べる値: {', '.join(map(str, options))}。"
                "審査前は SELF_ONLY だけのことが多いです。代替は --inbox です。"
            )
        init = lib.tiktok_init(
            access,
            "https://open.tiktokapis.com/v2/post/publish/video/init/",
            {
                "post_info": {
                    "title": caption,
                    "privacy_level": privacy_level,
                    "disable_duet": bool(creator.get("duet_disabled")),
                    "disable_stitch": bool(creator.get("stitch_disabled")),
                    "disable_comment": bool(creator.get("comment_disabled")),
                    "brand_content_toggle": bool(args.a8),
                    "brand_organic_toggle": False,
                    "is_aigc": bool(args.synthetic_media),
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": size,
                    "chunk_size": chunk_size,
                    "total_chunk_count": chunk_count,
                },
            },
        )

    publish_id = str(init["publish_id"])
    upload_url = str(init.get("upload_url") or "")
    if not upload_url:
        raise lib.ApiError("TikTokの応答に upload_url がありません。")
    lib.tiktok_put(upload_url, video, slices)
    state = lib.poll_tiktok(access, publish_id)
    remote_status = str(state.get("status") or "")
    video_ids = lib.tiktok_post_ids(state)
    video_id = video_ids[0] if video_ids else ""
    url = ""
    if video_id:
        try:
            found = lib.tiktok_query(access, [video_id])
        except lib.ApiError:
            found = []
        for item in found:
            if str(item.get("id")) == video_id and item.get("share_url"):
                url = str(item["share_url"])
    if remote_status == "FAILED":
        record_status = "failed"
    elif args.inbox or remote_status == "SEND_TO_USER_INBOX":
        record_status = "inbox_sent"
    elif remote_status == "PUBLISH_COMPLETE":
        record_status = "publish_complete"
    else:
        record_status = remote_status or "processing"
    note_parts = [warning]
    if args.inbox:
        note_parts.append("TikTokアプリの受信箱から投稿を完了します。キャプションはそこで入れます。")
    if args.a8 and args.inbox:
        note_parts.append("アプリの説明に「アフィリエイト広告を含みます」を入れます。")
    note_parts.append(f"tiktok_status={remote_status} open_id={open_id}")
    lib.append_csv(
        posted,
        lib.POSTED_COLUMNS,
        {
            "recorded_at": lib.utc_now(),
            "platform": "tiktok",
            "channel_key": args.channel,
            "mode": "inbox" if args.inbox else "direct",
            "video_id": video_id,
            "publish_id": publish_id,
            "url": url,
            "privacy": args.privacy,
            "scheduled_at": "",
            "title": args.title,
            "a8": "yes" if args.a8 else "no",
            "status": record_status,
            "file_sha256": digest,
            "note": " ".join(part for part in note_parts if part),
        },
    )
    if record_status == "failed":
        raise lib.ApiError(f"TikTokが失敗を返しました。publish_id={publish_id}")
    print(url or publish_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
