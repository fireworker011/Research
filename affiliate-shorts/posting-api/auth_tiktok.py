"""Authorize one TikTok account and store its refresh token.

This does not upload a video. Add the account as a sandbox target user first,
then run this once per account.
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.parse
from pathlib import Path

import posting_lib as lib

REDIRECT = "http://127.0.0.1:8766/tiktok/callback"
PORT = 8766


def parser() -> argparse.ArgumentParser:
    tool = argparse.ArgumentParser(description="TikTokのrefresh tokenを1アカウント分保存する。")
    tool.add_argument("--channel", required=True)
    tool.add_argument(
        "--scopes",
        default="",
        help="カンマ区切り。空なら user.info.basic,video.list,video.publish,video.upload",
    )
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
    channel = lib.find_channel(lib.load_channels(root / "channels.json"), "tiktok", args.channel)
    client_path = Path(args.client_file) if args.client_file else root / "secrets" / "tiktok-client.json"
    client_key = ""
    client_secret = ""
    if client_path.is_file():
        client = lib.read_json(client_path)
        client_key = str(client.get("client_key") or "")
        client_secret = str(client.get("client_secret") or "")
    client_key = client_key or os.environ.get("TIKTOK_CLIENT_KEY", "")
    client_secret = client_secret or os.environ.get("TIKTOK_CLIENT_SECRET", "")
    if not client_key or not client_secret:
        raise lib.ValidationError(
            "secrets/tiktok-client.json がありません。client_key と client_secret をそこに置きます。"
        )
    scopes = [item.strip() for item in args.scopes.split(",") if item.strip()] or list(lib.TIKTOK_SCOPES)
    state = lib.secrets.token_urlsafe(24)
    verifier, challenge = lib.pkce_pair()
    query = urllib.parse.urlencode(
        {
            "client_key": client_key,
            "scope": ",".join(scopes),
            "redirect_uri": REDIRECT,
            "state": state,
            "response_type": "code",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )
    print("ブラウザで、このTikTokアカウントにログインして許可します。")
    print(f"チャンネル: {channel.get('title')} / ログインの目印: {channel.get('login_label') or '未記入'}")
    lib.open_authorization("https://www.tiktok.com/v2/auth/authorize/?" + query)
    result = lib.wait_for_oauth_callback(PORT, 300)
    if result.get("error"):
        raise lib.ValidationError(f"許可されませんでした: {result['error'][0]}")
    if not result.get("code"):
        raise lib.ValidationError("許可コードが返りませんでした。時間内にブラウザで許可します。")
    if result.get("state", [""])[0] != state:
        raise lib.ValidationError("state が一致しません。もう一度許可します。")
    token_url = "https://open.tiktokapis.com/v2/oauth/token/"
    status, _, payload = lib.http_send(
        "POST",
        token_url,
        {"Content-Type": "application/x-www-form-urlencoded"},
        lib.tiktok_form(
            {
                "client_key": client_key,
                "client_secret": client_secret,
                "code": result["code"][0],
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT,
                "code_verifier": verifier,
            }
        ),
        60,
    )
    data = lib.parse_json(payload)
    refresh = data.get("refresh_token")
    access = data.get("access_token")
    if status != 200 or not isinstance(refresh, str) or not isinstance(access, str):
        raise lib.ApiError(lib.public_api_error(token_url, status, payload))
    open_id = str(data.get("open_id") or "")
    display_name = ""
    info_error: lib.ApiError | None = None
    try:
        info_id, display_name = lib.tiktok_user(access)
        if info_id:
            open_id = info_id
    except lib.ApiError as exc:
        info_error = exc
    token_path = (
        Path(args.token_file) if args.token_file else root / "tokens" / "tiktok" / f"{args.channel}.json"
    )
    lib.write_secret_json(
        token_path,
        {
            "refresh_token": refresh,
            "open_id": open_id,
            "scope": str(data.get("scope") or ",".join(scopes)),
            "display_name": display_name,
        },
        root,
    )
    print(f"保存しました: {token_path}")
    if info_error is not None:
        raise info_error
    print(f"APIの表示名: {display_name}")
    try:
        lib.require_channel_match(channel, display_name, "")
    except lib.ChannelMismatch:
        print("トークンは保存済みです。channels.json の title を表示名に直してから投稿できます。", file=sys.stderr)
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
