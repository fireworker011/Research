#!/usr/bin/env python3
"""
Threads API アクセストークン取得・更新ヘルパー

使い方:
  python setup/threads_token.py setup career    # career ニッチの初回セットアップ
  python setup/threads_token.py setup marriage  # marriage ニッチの初回セットアップ
  python setup/threads_token.py refresh career  # career トークン更新
  python setup/threads_token.py refresh marriage
  python setup/threads_token.py check           # 全ニッチの有効期限確認

前提:
  - sns-affiliate-bot アプリを Meta for Developers で作成済み
  - ニッチごとに Instagram プロアカウント + Threads アカウントあり
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
ENV_FILE = Path(".env")

NICHE_ENV_KEYS = {
    "career":   ("THREADS_CAREER_USER_ID",   "THREADS_CAREER_ACCESS_TOKEN"),
    "marriage": ("THREADS_MARRIAGE_USER_ID",  "THREADS_MARRIAGE_ACCESS_TOKEN"),
}

NICHE_LABELS = {
    "career":   "転職×AI（カズト）",
    "marriage": "婚活×マッチング（ミキ）",
}


def exchange_for_long_lived_token(short_lived_token: str) -> dict:
    app_id = os.getenv("META_APP_ID", "")
    app_secret = os.getenv("META_APP_SECRET", "")
    if not app_id or not app_secret:
        raise EnvironmentError(
            "META_APP_ID または META_APP_SECRET が .env に設定されていません。"
        )
    resp = requests.get(
        "https://graph.threads.net/access_token",
        params={
            "grant_type": "th_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "access_token": short_lived_token,
        },
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"トークン交換失敗: {resp.text}")
    return resp.json()


def refresh_long_lived_token(long_lived_token: str) -> dict:
    resp = requests.get(
        "https://graph.threads.net/refresh_access_token",
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


def cmd_setup(niche: str):
    if niche not in NICHE_ENV_KEYS:
        print(f"❌ 未対応のニッチ: {niche}  (使えるのは: {list(NICHE_ENV_KEYS.keys())})")
        return

    uid_key, token_key = NICHE_ENV_KEYS[niche]

    print("=" * 60)
    print(f"Threads API 初回セットアップ — {NICHE_LABELS.get(niche, niche)}")
    print("=" * 60)
    print(f"""
【事前準備】Meta for Developers での作業:

1. https://developers.facebook.com にアクセス
2. 「sns-affiliate-bot」アプリを開く
3. 左メニュー「アプリの役割」→「テスター」に
   {niche} 用の Instagram アカウントを追加

4. 「ツール」→「Graph APIエクスプローラー」
5. 右上で「sns-affiliate-bot」アプリを選択
6. 「ユーザーまたはページ」で {niche} 用アカウントを選択
7. permissions に以下を追加:
   ✅ threads_basic
   ✅ threads_content_publish
8. 「アクセストークンを生成」をクリック → コピー
""")

    short_token = input("コピーしたアクセストークンをここに貼り付けてください:\n> ").strip()
    if not short_token:
        print("❌ トークンが入力されていません。")
        return

    print("\n長期トークン（60日間）に変換中...")
    try:
        result = exchange_for_long_lived_token(short_token)
        long_token = result.get("access_token", "")
        expires_in_sec = result.get("expires_in", 5184000)
    except RuntimeError as e:
        print(f"⚠️  長期変換失敗: {e}")
        print("短期トークンのまま保存します（2時間で期限切れ）")
        long_token = short_token
        expires_in_sec = 7200

    expires_date = datetime.now() + timedelta(seconds=expires_in_sec)
    expires_days = expires_in_sec // 86400
    print(f"✅ トークン取得成功！（有効: {max(1, expires_days)}日 / {expires_date.strftime('%Y-%m-%d')}まで）")

    print("\nThreadsユーザーIDを取得中...")
    try:
        user_id = get_threads_user_id(long_token)
    except RuntimeError as e:
        print(f"❌ ユーザーID取得失敗: {e}")
        user_id = input("Threads User ID を手動で入力してください:\n> ").strip()

    update_env(token_key, long_token)
    update_env(uid_key, user_id)

    expiry_json = Path("config/token_expiry.json")
    expiry_json.parent.mkdir(exist_ok=True)
    expiry_data = {}
    if expiry_json.exists():
        try:
            expiry_data = json.loads(expiry_json.read_text())
        except Exception:
            pass
    expiry_data[f"threads_{niche}"] = expires_date.isoformat()
    expiry_json.write_text(json.dumps(expiry_data, indent=2, ensure_ascii=False))

    print(f"\n✅ .env に保存しました:")
    print(f"  {uid_key}={user_id}")
    print(f"  {token_key}={long_token[:20]}...")
    print(f"\n次のステップ:")
    print(f"  python main.py check")
    print(f"  python main.py post threads {niche}")


def cmd_refresh(niche: str):
    if niche not in NICHE_ENV_KEYS:
        print(f"❌ 未対応のニッチ: {niche}")
        return

    uid_key, token_key = NICHE_ENV_KEYS[niche]
    load_dotenv()
    token = os.getenv(token_key, "")
    if not token:
        print(f"❌ .env に {token_key} が設定されていません。")
        print(f"先に: python setup/threads_token.py setup {niche}")
        return

    print(f"[{niche}] トークンを更新中...")
    try:
        result = refresh_long_lived_token(token)
    except RuntimeError as e:
        print(f"❌ {e}")
        return

    new_token = result.get("access_token", token)
    expires_in_sec = result.get("expires_in", 5184000)
    expires_date = datetime.now() + timedelta(seconds=expires_in_sec)

    update_env(token_key, new_token)

    expiry_json = Path("config/token_expiry.json")
    expiry_data = {}
    if expiry_json.exists():
        try:
            expiry_data = json.loads(expiry_json.read_text())
        except Exception:
            pass
    expiry_data[f"threads_{niche}"] = expires_date.isoformat()
    expiry_json.write_text(json.dumps(expiry_data, indent=2, ensure_ascii=False))

    print(f"✅ [{niche}] トークン更新完了（{expires_date.strftime('%Y-%m-%d')} まで有効）")


def cmd_check():
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
        niche = key.replace("threads_", "")
        if 0 < days <= 14:
            print(f"   → 更新推奨: python setup/threads_token.py refresh {niche}")
        elif days <= 0:
            print(f"   → 期限切れ: python setup/threads_token.py setup {niche}")


if __name__ == "__main__":
    args = sys.argv[1:]
    cmd = args[0] if args else "check"
    niche_arg = args[1] if len(args) > 1 else "career"

    if cmd == "setup":
        cmd_setup(niche_arg)
    elif cmd == "refresh":
        cmd_refresh(niche_arg)
    elif cmd == "check":
        cmd_check()
    else:
        print(__doc__)
