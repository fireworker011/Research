#!/usr/bin/env python3
"""
YouTube Data API OAuth 2.0 セットアップヘルパー

使い方:
  python setup/youtube_oauth.py setup career   # 転職ジャンル用の認証を初回設定
  python setup/youtube_oauth.py check          # 認証ファイルの存在確認

【Google Cloud Console での事前作業】
1. https://console.cloud.google.com にアクセス
2. 左上「プロジェクトを選択」→「新しいプロジェクト」
   プロジェクト名: sns-affiliate-bot → 作成
3. 「APIとサービス」→「ライブラリ」→「YouTube Data API v3」→「有効にする」
4. 「APIとサービス」→「OAuth同意画面」
   - ユーザーの種類: 外部 → 作成
   - アプリ名: sns-affiliate-bot
   - サポートメール: 自分のメールアドレス
   - スコープ: 「スコープを追加」→ YouTube.upload を追加
   - テストユーザー: 自分のGoogleアカウントを追加
   → 保存して次へ（最後まで）
5. 「認証情報」→「認証情報を作成」→「OAuthクライアントID」
   - アプリの種類: デスクトップアプリ
   - 名前: sns-affiliate-bot-desktop
   → 作成
6. 「JSONをダウンロード」ボタンをクリック
7. ダウンロードしたファイルを以下にコピー:
   config/credentials/youtube_career.json
8. python setup/youtube_oauth.py setup career を実行
"""

import json
import os
import sys
from pathlib import Path


def cmd_setup(niche_id: str):
    creds_file = Path(f"config/credentials/youtube_{niche_id}.json")

    if not creds_file.exists():
        print(f"❌ 認証情報ファイルが見つかりません: {creds_file}")
        print("""
【手順】
1. https://console.cloud.google.com → 認証情報
2. OAuthクライアントID（デスクトップアプリ）を作成
3. JSONをダウンロード
4. ダウンロードしたファイルを以下に配置:
   sns-affiliate-bot/config/credentials/youtube_career.json
5. 再度このスクリプトを実行: python setup/youtube_oauth.py setup career
""")
        return

    print(f"認証情報ファイル確認: {creds_file} ✅")
    print("\nYouTube APIの認証を開始します（ブラウザが開きます）...")

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        import pickle
    except ImportError:
        print("❌ 必要なパッケージが不足しています。以下を実行してください:")
        print("  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return

    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    token_file = Path(f"config/credentials/youtube_{niche_id}_token.pickle")

    creds = None
    if token_file.exists():
        with open(token_file, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            print("✅ トークンを自動更新しました。")
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
            creds = flow.run_local_server(port=0)
            print("\n✅ 認証成功！")

        with open(token_file, "wb") as f:
            import pickle
            pickle.dump(creds, f)
        print(f"認証情報を保存しました: {token_file}")

    from googleapiclient.discovery import build
    youtube = build("youtube", "v3", credentials=creds)
    resp = youtube.channels().list(part="snippet", mine=True).execute()
    if resp.get("items"):
        channel = resp["items"][0]["snippet"]
        channel_id = resp["items"][0]["id"]
        print(f"\n接続成功:")
        print(f"  チャンネル名: {channel['title']}")
        print(f"  チャンネルID: {channel_id}")

        from dotenv import load_dotenv
        load_dotenv()
        _update_env(f"YOUTUBE_{niche_id.upper()}_CHANNEL_ID", channel_id)
        print(f"\n✅ .env に YOUTUBE_{niche_id.upper()}_CHANNEL_ID を保存しました。")
        print(f"\n次のステップ: python main.py check で全体の設定を確認してください。")
    else:
        print("⚠️  YouTubeチャンネルが見つかりませんでした。Googleアカウントを確認してください。")


def cmd_check():
    creds_dir = Path("config/credentials")
    niches = ["career", "beauty", "finance", "vod", "education"]
    print("=== YouTube 認証状態 ===\n")
    for niche in niches:
        creds = creds_dir / f"youtube_{niche}.json"
        token = creds_dir / f"youtube_{niche}_token.pickle"
        if creds.exists() and token.exists():
            status = "✅ 認証済み"
        elif creds.exists():
            status = "⚠️  client_secret あり / 認証未実行"
        else:
            status = "❌ 未設定"
        print(f"  {niche:12s}: {status}")
    print()


def _update_env(key: str, value: str):
    env_file = Path(".env")
    if not env_file.exists():
        env_file.write_text(f"{key}={value}\n", encoding="utf-8")
        return
    lines = env_file.read_text(encoding="utf-8").splitlines()
    updated = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            updated = True
            break
    if not updated:
        lines.append(f"{key}={value}")
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "setup" and len(sys.argv) >= 3:
        cmd_setup(sys.argv[2])
    elif cmd == "check":
        cmd_check()
    else:
        print(__doc__)
