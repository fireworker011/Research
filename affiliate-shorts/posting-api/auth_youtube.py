"""Authorize one Google account and store its YouTube refresh token.

This does not upload a video. Run it once per channel, in a private browser
window, while logged into that channel's Google account.
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.parse
from pathlib import Path

import posting_lib as lib

REDIRECT = "http://127.0.0.1:8765/"
PORT = 8765


def parser() -> argparse.ArgumentParser:
    tool = argparse.ArgumentParser(description="YouTubeのrefresh tokenを1チャンネル分保存する。")
    tool.add_argument("--channel", required=True)
    tool.add_argument("--with-analytics", action="store_true")
    tool.add_argument("--client-file", default="")
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


def run(args: argparse.Namespace) -> int:
    root = lib.ROOT
    channel = lib.find_channel(
        lib.load_channels(root / "channels.json"),
        "youtube",
        args.channel,
    )
    client_path = Path(args.client_file) if args.client_file else root / "secrets" / "youtube-client.json"
    client_id = ""
    client_secret = ""
    if client_path.is_file():
        client_id, client_secret = lib.google_client_fields(lib.read_json(client_path))
    client_id = client_id or os.environ.get("YOUTUBE_CLIENT_ID", "")
    client_secret = client_secret or os.environ.get("YOUTUBE_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise lib.ValidationError(
            "secrets/youtube-client.json がありません。コンソールから落としたJSONをそこに置きます。"
        )
    scopes = list(lib.YOUTUBE_SCOPES)
    if args.with_analytics:
        scopes.append(lib.YOUTUBE_ANALYTICS_SCOPE)
    state = lib.secrets.token_urlsafe(24)
    query = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": REDIRECT,
            "response_type": "code",
            "scope": " ".join(scopes),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
    )
    print("ブラウザで、このチャンネルのGoogleアカウントを選びます。")
    print(f"チャンネル: {channel.get('title')} / ログインの目印: {channel.get('login_label') or '未記入'}")
    lib.open_authorization("https://accounts.google.com/o/oauth2/v2/auth?" + query)
    result = lib.wait_for_oauth_callback(PORT, 300)
    if result.get("error"):
        raise lib.ValidationError(f"許可されませんでした: {result['error'][0]}")
    if not result.get("code"):
        raise lib.ValidationError("許可コードが返りませんでした。時間内にブラウザで許可します。")
    if result.get("state", [""])[0] != state:
        raise lib.ValidationError("state が一致しません。もう一度許可します。")
    token_url = "https://oauth2.googleapis.com/token"
    status, _, payload = lib.http_send(
        "POST",
        token_url,
        {"Content-Type": "application/x-www-form-urlencoded"},
        urllib.parse.urlencode(
            {
                "code": result["code"][0],
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": REDIRECT,
                "grant_type": "authorization_code",
            }
        ).encode(),
        60,
    )
    data = lib.parse_json(payload)
    refresh = data.get("refresh_token")
    access = data.get("access_token")
    if status != 200 or not isinstance(refresh, str) or not isinstance(access, str):
        raise lib.ApiError(lib.public_api_error(token_url, status, payload))
    channel_id, title, custom_url = lib.youtube_mine(access)
    token_path = (
        Path(args.token_file)
        if args.token_file
        else root / "tokens" / "youtube" / f"{args.channel}.json"
    )
    lib.write_secret_json(
        token_path,
        {
            "refresh_token": refresh,
            "scope": str(data.get("scope") or " ".join(scopes)),
            "channel_id": channel_id,
            "channel_title": title,
            "custom_url": custom_url,
        },
        root,
    )
    print(f"保存しました: {token_path}")
    print(f"APIのチャンネル名: {title}")
    print(f"APIのハンドル: {custom_url}")
    try:
        lib.require_channel_match(channel, title, custom_url)
    except lib.ChannelMismatch:
        print("トークンは保存済みです。channels.json を直したあとに投稿できます。", file=sys.stderr)
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
