import os
import sys
import requests
from datetime import datetime, timedelta

TOKEN = os.environ.get("THREADS_KONKATSU_ACCESS_TOKEN", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "")
GITHUB_SERVER_URL = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
GITHUB_RUN_ID = os.environ.get("GITHUB_RUN_ID", "")
STEP_SUMMARY = os.environ.get("GITHUB_STEP_SUMMARY", "")

def refresh_token():
    resp = requests.get(
        "https://graph.threads.net/refresh_access_token",
        params={"grant_type": "th_refresh_token", "access_token": TOKEN},
        timeout=30,
    )
    if not resp.ok:
        print(f"[ERROR] トークンリフレッシュ失敗: {resp.status_code} {resp.text}")
        sys.exit(1)
    data = resp.json()
    new_token = data.get("access_token", "")
    expires_in = data.get("expires_in", 5184000)  # default 60days in seconds
    expires_days = expires_in // 86400
    expire_date = (datetime.now() + timedelta(seconds=expires_in)).strftime("%Y-%m-%d")
    return new_token, expire_date, expires_days

def write_summary(new_token, expire_date):
    if not STEP_SUMMARY:
        return
    run_url = f"{GITHUB_SERVER_URL}/{GITHUB_REPOSITORY}/actions/runs/{GITHUB_RUN_ID}"
    with open(STEP_SUMMARY, "a", encoding="utf-8") as f:
        f.write("## Threads トークン リフレッシュ完了\n\n")
        f.write(f"- 更新日時: {datetime.now().strftime('%Y-%m-%d %H:%M')} JST\n")
        f.write(f"- 次回期限: {expire_date}\n\n")
        f.write("### 新しいトークン\n\n")
        f.write(f"```\n{new_token}\n```\n\n")
        f.write("↑ この値をコピーして GitHub Secretsの `THREADS_KONKATSU_ACCESS_TOKEN` を更新してください\n")

def create_issue(expire_date):
    if not GITHUB_TOKEN or not GITHUB_REPOSITORY:
        return
    run_url = f"{GITHUB_SERVER_URL}/{GITHUB_REPOSITORY}/actions/runs/{GITHUB_RUN_ID}"
    secrets_url = f"{GITHUB_SERVER_URL}/{GITHUB_REPOSITORY}/settings/secrets/actions"
    body = f"""## Threads アクセストークンの更新が必要です

トークンのリフレッシュが完了しました。
新しいトークンを下記のワークフロー実行ログから確認して、Secrets を更新してください。

### 手順
1. [ワークフロー実行ログ]({run_url}) → **Summary** タブを開く
2. 新しいトークンをコピー
3. [GitHub Secrets]({secrets_url}) → `THREADS_KONKATSU_ACCESS_TOKEN` を更新
4. このIssueをクローズ

次回期限: **{expire_date}**
"""
    resp = requests.post(
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues",
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        },
        json={
            "title": f"[要対応] Threads トークンを更新してください ({datetime.now().strftime('%Y-%m')})",
            "body": body,
        },
        timeout=30,
    )
    if resp.ok:
        print(f"[Issue作成] {resp.json().get('html_url', '')}")
    else:
        print(f"[WARN] Issue作成失敗: {resp.status_code}")

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] トークンリフレッシュ開始")
    new_token, expire_date, expires_days = refresh_token()
    print(f"[完了] 新トークン取得成功 / 次回期限: {expire_date} ({expires_days}日後)")
    write_summary(new_token, expire_date)
    create_issue(expire_date)

if __name__ == "__main__":
    main()
