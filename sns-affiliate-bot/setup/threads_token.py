#!/usr/bin/env python3
"""
Threads API アクセストークン取得・更新ヘルパー

使い方:
  python setup/threads_token.py setup   # 初回セットアップ（対話式）
  python setup/threads_token.py refresh # トークンを更新（有効期限延長）
  python setup/threads_token.py check   # 残り有効期限を確認

前提:
  - sns-affiliate-bot アプリを Meta for Developers で作成済み
  - Instagram プロアカウントあり
  - META_APP_ID と META_APP_SECRET を .env に設定済み
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

GRAPH_URL = "https://graph.threads.net/v1.0"
GRAPH_FB_URL = "https://graph.facebook.com/v21.0"
ENV_FILE = Path(".env")


def exchange_for_long_lived_token(short_lived_token: str) -> dict:
    """短期トークン → 長期トークン（60日）に交換する。"""
    app_id = os.getenv("META_APP_ID", "")
    app_secret = os.getenv("META_APP_SECRET", "")
    if not app_id or not app_secret:
        raise EnvironmentError(
            "META_APP_ID または META_APP_SECRET が .env に設定されていません。\n"
            "Meta for Developers のアプリ設定 → 基本設定 でアプリIDとシークレットを確認してください。"
        )
    resp = requests.get(
        f"{GRAPH_FB_URL}/oauth/access_token",
        params={
            "grant_type": "th_exchange_token",
            "client_secret": app_secret,
            "access_token": short_lived_token,
        },
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"トークン交換失敗: {resp.text}")
    return resp.json()


def refresh_long_lived_token(long_lived_token: str) -> dict:
    """長期トークンを更新する（24時間以上残っていれば実行可能）。"""
    resp = requests.get(
        f"{GRAPH_FB_URL}/refresh_access_token",
        params={
            "grant_type": "th_refresh_token",
            "access_token": long_lived_token,
        },
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"トークン更新失敗: {resp.text}")
    return resp.json()


def get_threads_user_id(access_token: str) -> str:
    """アクセストークンからThreadsのユーザーIDを取得する。"""
    resp = requests.get(
        f"{GRAPH_URL}/me",
        params={"fields": "id,username", "access_token": access_token},
        timeout=15,
    )
    if not resp.ok:
        raise RuntimeError(f"ユーザーID取得失敗: {resp.text}")
    data = resp.json()
    print(f"  Threadsユーザー名: @{data.get('username', '?')}")
    return data["id"]


def update_env(key: str, value: str):
    """既存の .env ファイルのキーを更新する（なければ末尾に追記）。"""
    if not ENV_FILE.exists():
        ENV_FILE.write_text(f"{key}={value}\n", encoding="utf-8")
        return
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    updated = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            updated = True
            break
    if not updated:
        lines.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_setup():
    """初回セットアップ: Graph API エクスプローラーで取得したトークンを長期トークンに変換して保存。"""
    print("=" * 60)
    print("Threads API 初回セットアップ")
    print("=" * 60)
    print("""
【事前準備】Meta for Developers での作業:

1. https://developers.facebook.com にアクセス
2. 「sns-affiliate-bot」アプリを開く
3. 左メニュー「アプリの役割」→「役割」→「テスター」に
   自分のInstagramアカウントを追加する

4. 「Threadsへのアクセス」ユースケースを設定:
   ダッシュボード → 「ユースケースを追加」→「Threads APIへのアクセス」→「設定」
   → permissions: threads_basic, threads_content_publish を追加

5. 「ツール」→「Graph APIエクスプローラー」を開く
6. 右上のアプリ選択で「sns-affiliate-bot」を選択
7. 「ユーザーまたはページ」ドロップダウンで自分のアカウントを選択
8. permissions に以下を追加:
   ✅ threads_basic
   ✅ threads_content_publish
9. 「アクセストークンを生成」ボタンをクリック
10. 表示されたトークンをコピー
""")
    short_token = input("コピーしたアクセストークンをここに貼り付けてください:\n> ").strip()
    if not short_token:
        print("❌ トークンが入力されていません。")
        return

    print("\n長期トークン（60日間）に変換中...")
    try:
        result = exchange_for_long_lived_token(short_token)
    except RuntimeError as e:
        print(f"❌ {e}")
        print("\n代替手順: .env に以下の値をそのまま設定してください:")
        print(f"  THREADS_CAREER_ACCESS_TOKEN={short_token}")
        print("  ※短期トークン（1〜2時間）なので早めに次のステップへ進んでください")
        return

    long_token = result.get("access_token", "")
    expires_in_sec = result.get("expires_in", 5184000)
    expires_days = expires_in_sec // 86400
    expires_date = datetime.now() + timedelta(seconds=expires_in_sec)

    print(f"\n✅ 長期トークン取得成功！（有効期限: {expires_days}日 / {expires_date.strftime('%Y-%m-%d')}まで）")

    print("\nThreadsユーザーIDを取得中...")
    try:
        user_id = get_threads_user_id(long_token)
    except RuntimeError as e:
        print(f"❌ ユーザーID取得失敗: {e}")
        user_id = input("Threads User ID を手動で入力してください:\n> ").strip()

    update_env("THREADS_CAREER_ACCESS_TOKEN", long_token)
    update_env("THREADS_CAREER_USER_ID", user_id)

    expiry_json = Path("config/token_expiry.json")
    expiry_json.parent.mkdir(exist_ok=True)
    expiry_data = {}
    if expiry_json.exists():
        try:
            expiry_data = json.loads(expiry_json.read_text())
        except Exception:
            pass
    expiry_data["threads_career"] = expires_date.isoformat()
    expiry_json.write_text(json.dumps(expiry_data, indent=2, ensure_ascii=False))

    print(f"\n✅ .env に保存しました:")
    print(f"  THREADS_CAREER_USER_ID={user_id}")
    print(f"  THREADS_CAREER_ACCESS_TOKEN={long_token[:20]}...（60日間有効）")
    print(f"\n次のステップ: python main.py check で動作確認してください。")


def cmd_refresh():
    """長期トークンを更新する（期限を60日延長）。"""
    load_dotenv()
    token = os.getenv("THREADS_CAREER_ACCESS_TOKEN", "")
    if not token:
        print("❌ .env に THREADS_CAREER_ACCESS_TOKEN が設定されていません。")
        print("先に: python setup/threads_token.py setup")
        return

    print("トークンを更新中...")
    try:
        result = refresh_long_lived_token(token)
    except RuntimeError as e:
        print(f"❌ {e}")
        print("トークンが完全に期限切れの場合は setup コマンドで再取得してください。")
        return

    new_token = result.get("access_token", token)
    expires_in_sec = result.get("expires_in", 5184000)
    expires_date = datetime.now() + timedelta(seconds=expires_in_sec)

    update_env("THREADS_CAREER_ACCESS_TOKEN", new_token)

    expiry_json = Path("config/token_expiry.json")
    expiry_data = {}
    if expiry_json.exists():
        try:
            expiry_data = json.loads(expiry_json.read_text())
        except Exception:
            pass
    expiry_data["threads_career"] = expires_date.isoformat()
    expiry_json.write_text(json.dumps(expiry_data, indent=2, ensure_ascii=False))

    print(f"✅ トークン更新完了（{expires_date.strftime('%Y-%m-%d')} まで有効）")


def cmd_check():
    """トークンの残り有効期限を確認する。"""
    expiry_json = Path("config/token_expiry.json")
    if not expiry_json.exists():
        print("⚠️  有効期限情報なし。setup コマンドでセットアップしてください。")
        return
    data = json.loads(expiry_json.read_text())
    for key, expiry_str in data.items():
        expiry = datetime.fromisoformat(expiry_str)
        remaining = expiry - datetime.now()
        days = remaining.days
        if days > 14:
            status = "✅"
        elif days > 0:
            status = "⚠️ "
        else:
            status = "❌"
        print(f"{status} {key}: {expiry.strftime('%Y-%m-%d')} まで（残り {max(0, days)} 日）")
        if days <= 14 and days > 0:
            print(f"   → 更新推奨: python setup/threads_token.py refresh")
        elif days <= 0:
            print(f"   → 期限切れ: python setup/threads_token.py setup で再取得してください")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "setup":
        cmd_setup()
    elif cmd == "refresh":
        cmd_refresh()
    elif cmd == "check":
        cmd_check()
    else:
        print(__doc__)
