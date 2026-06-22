"""
チャンネル監視 + 競合リサーチ自動化ツール

投稿後に実行すると：
  1. 自チャンネル全動画の再生数・いいね・コメントを取得
  2. 同ジャンルのバズり動画をリサーチ
  3. オマージュ候補をレポートとして出力

使い方:
  python monitor_and_research.py

出力先:
  reports/YYYYMMDD_HHMM_report.md
"""

import pickle
import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]
TOKEN_PATH   = Path("token.pickle")
SECRET_PATH  = Path("client_secret.json")
REPORTS_DIR  = Path("reports")
CHANNEL_ID   = "UC65pP_901i2ERosuStSAIVw"

# 競合リサーチキーワード
COMPETITOR_KEYWORDS = [
    "ペットカメラ ショートドラマ",
    "保護猫 感動 shorts",
    "見守りカメラ 猫 shorts",
    "ペット 留守番 感動",
]


# ── 認証 ─────────────────────────────────────────────────────────────────────

def get_youtube():
    creds = None
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(str(SECRET_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)

    return build("youtube", "v3", credentials=creds)


# ── 自チャンネル ──────────────────────────────────────────────────────────────

def get_own_videos(yt) -> list[dict]:
    search_resp = yt.search().list(
        part="id,snippet",
        channelId=CHANNEL_ID,
        type="video",
        order="date",
        maxResults=20,
    ).execute()

    video_ids = [item["id"]["videoId"] for item in search_resp.get("items", [])]
    if not video_ids:
        return []

    stats_resp = yt.videos().list(
        part="snippet,statistics",
        id=",".join(video_ids),
    ).execute()

    videos = []
    for item in stats_resp.get("items", []):
        s = item.get("statistics", {})
        videos.append({
            "title":    item["snippet"]["title"],
            "date":     item["snippet"]["publishedAt"][:10],
            "views":    int(s.get("viewCount",   0)),
            "likes":    int(s.get("likeCount",   0)),
            "comments": int(s.get("commentCount", 0)),
            "url":      f"https://www.youtube.com/shorts/{item['id']}",
        })

    return sorted(videos, key=lambda x: x["date"], reverse=True)


# ── 競合リサーチ ───────────────────────────────────────────────────────────────

def search_competitors(yt, keyword: str, max_results=8) -> list[dict]:
    resp = yt.search().list(
        part="id,snippet",
        q=keyword,
        type="video",
        videoDuration="short",
        order="viewCount",
        regionCode="JP",
        relevanceLanguage="ja",
        maxResults=max_results,
    ).execute()

    video_ids = [
        item["id"]["videoId"]
        for item in resp.get("items", [])
        if item["id"].get("videoId")
    ]
    if not video_ids:
        return []

    stats_resp = yt.videos().list(
        part="snippet,statistics",
        id=",".join(video_ids),
    ).execute()

    results = []
    for item in stats_resp.get("items", []):
        s = item.get("statistics", {})
        results.append({
            "title":   item["snippet"]["title"],
            "channel": item["snippet"]["channelTitle"],
            "views":   int(s.get("viewCount", 0)),
            "likes":   int(s.get("likeCount", 0)),
            "url":     f"https://www.youtube.com/watch?v={item['id']}",
        })

    return sorted(results, key=lambda x: x["views"], reverse=True)


# ── レポート生成 ───────────────────────────────────────────────────────────────

def generate_report(own_videos: list, competitor_data: dict) -> str:
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    lines = [
        f"# チャンネル監視レポート　{now}",
        "",
        "## 自チャンネル動画パフォーマンス",
        "",
        "| 投稿日 | 再生数 | いいね | コメント | タイトル |",
        "|--------|--------|--------|---------|---------|",
    ]
    for v in own_videos:
        lines.append(
            f"| {v['date']} | {v['views']:,} | {v['likes']:,} | "
            f"{v['comments']:,} | {v['title'][:35]} |"
        )

    lines += ["", "---", "", "## 競合リサーチ結果", ""]

    for keyword, videos in competitor_data.items():
        lines += [f"### 🔍「{keyword}」", ""]
        lines += [
            "| 再生数 | いいね | チャンネル | タイトル |",
            "|--------|--------|----------|---------|",
        ]
        for v in videos[:5]:
            lines.append(
                f"| {v['views']:,} | {v['likes']:,} | "
                f"{v['channel'][:12]} | {v['title'][:30]} |"
            )
        lines.append("")

    # オマージュ候補（全キーワードから再生数上位5件）
    all_vids = [v for vlist in competitor_data.values() for v in vlist]
    top5 = sorted(all_vids, key=lambda x: x["views"], reverse=True)[:5]

    lines += [
        "---",
        "",
        "## 次の動画オマージュ候補 TOP5",
        "",
    ]
    for i, v in enumerate(top5, 1):
        lines += [
            f"### {i}位 {v['views']:,}再生",
            f"- **タイトル**: {v['title']}",
            f"- **チャンネル**: {v['channel']}",
            f"- **URL**: {v['url']}",
            "",
        ]

    return "\n".join(lines)


# ── メイン ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("チャンネル監視 + 競合リサーチ")
    print("=" * 55)

    yt = get_youtube()

    # 自チャンネル
    print("\n[1/2] 自チャンネル動画を取得中...")
    own_videos = get_own_videos(yt)
    print(f"  → {len(own_videos)}本")
    for v in own_videos:
        print(f"  {v['date']}  {v['views']:>5,}再生  ❤{v['likes']}  💬{v['comments']}  {v['title'][:30]}")

    # 競合リサーチ
    print("\n[2/2] 競合リサーチ中...")
    competitor_data = {}
    for kw in COMPETITOR_KEYWORDS:
        print(f"  「{kw}」を検索中...")
        competitor_data[kw] = search_competitors(yt, kw)

    # レポート保存
    REPORTS_DIR.mkdir(exist_ok=True)
    filename = REPORTS_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M')}_report.md"
    filename.write_text(generate_report(own_videos, competitor_data), encoding="utf-8")

    print(f"\n{'='*55}")
    print(f"✅ レポート保存: {filename}")
    print(f"{'='*55}")

    # オマージュ候補をコンソールに表示
    all_vids = [v for vlist in competitor_data.values() for v in vlist]
    top3 = sorted(all_vids, key=lambda x: x["views"], reverse=True)[:3]
    print("\n--- オマージュ候補 TOP3 ---")
    for i, v in enumerate(top3, 1):
        print(f"\n{i}. {v['title']}")
        print(f"   {v['views']:,}再生  {v['channel']}")
        print(f"   {v['url']}")


if __name__ == "__main__":
    main()
