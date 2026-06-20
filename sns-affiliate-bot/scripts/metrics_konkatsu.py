#!/usr/bin/env python
"""
婚活 Threads メトリクス収集 + Claude API 週次分析

使い方:
  python scripts/metrics_konkatsu.py            # メトリクス収集のみ
  python scripts/metrics_konkatsu.py --weekly   # 週次分析も実行
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = BASE_DIR / "konkatsu_state.json"
METRICS_FILE = BASE_DIR / "konkatsu_metrics.json"
ACCESS_TOKEN = os.environ.get("THREADS_KONKATSU_ACCESS_TOKEN", "")
BASE_URL = "https://graph.threads.net/v1.0"


def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_post_insights(post_id):
    """Threads API からインサイトを取得する。"""
    url = f"{BASE_URL}/{post_id}/insights"
    params = {
        "metric": "views,likes,replies,reposts,quotes",
        "access_token": ACCESS_TOKEN
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        result = {}
        for item in resp.json().get("data", []):
            result[item["name"]] = item.get("values", [{}])[0].get("value", 0)
        return result
    except Exception as e:
        print(f"[Metrics] APIエラー post_id={post_id}: {e}")
        return None


def collect_metrics():
    """state.json の recent_posts のメトリクスを収集・更新する。"""
    state = load_json(STATE_FILE, {})
    metrics_data = load_json(METRICS_FILE, {"posts": [], "weekly_reports": []})
    existing = {p["post_id"]: p for p in metrics_data["posts"]}

    recent_posts = state.get("recent_posts", [])
    if not recent_posts:
        print("[Metrics] 収集対象の投稿がありません")
        return

    updated = False
    for post in recent_posts:
        post_id = post.get("post_id")
        if not post_id:
            continue

        # 投稿から1時間未満はスキップ
        posted_at = datetime.fromisoformat(post.get("posted_at", "2000-01-01T00:00:00"))
        if datetime.now() - posted_at < timedelta(hours=1):
            print(f"[Metrics] スキップ（1時間未満）: {post_id}")
            continue

        print(f"[Metrics] 取得中: {post.get('title', post_id)}")
        metrics = get_post_insights(post_id)
        if metrics is None:
            continue

        views = metrics.get("views", 0)
        likes = metrics.get("likes", 0)
        er = round(likes / views * 100, 2) if views > 0 else 0.0

        existing[post_id] = {
            "post_id": post_id,
            "posted_at": post.get("posted_at"),
            "title": post.get("title", ""),
            "type": post.get("type", ""),
            "post_time": posted_at.strftime("%H:%M"),
            "metrics": metrics,
            "engagement_rate": er,
            "metrics_collected_at": datetime.now().isoformat(),
        }
        print(f"  views={views}, likes={likes}, ER={er}%")
        updated = True

    if updated:
        metrics_data["posts"] = list(existing.values())
        save_json(METRICS_FILE, metrics_data)
        print(f"[Metrics] 保存完了")
    else:
        print("[Metrics] 更新なし")


def analyze_weekly():
    """Claude API で週次分析レポートを生成する。"""
    import anthropic

    metrics_data = load_json(METRICS_FILE, {"posts": [], "weekly_reports": []})
    posts = metrics_data.get("posts", [])

    if len(posts) < 2:
        print("[分析] データ不足（最低2投稿必要）")
        return

    # 過去7日のデータ（なければ直近10件）
    cutoff = datetime.now() - timedelta(days=7)
    recent = [
        p for p in posts
        if datetime.fromisoformat(p.get("posted_at", "2000-01-01T00:00:00")) > cutoff
    ] or posts[-10:]

    # タイプ別集計
    by_type = {}
    for p in recent:
        t = p.get("type", "unknown")
        if t not in by_type:
            by_type[t] = {"views": [], "likes": [], "er": []}
        m = p.get("metrics", {})
        by_type[t]["views"].append(m.get("views", 0))
        by_type[t]["likes"].append(m.get("likes", 0))
        by_type[t]["er"].append(p.get("engagement_rate", 0))

    summary = {
        k: {
            "avg_views": round(sum(v["views"]) / len(v["views"]), 1),
            "avg_likes": round(sum(v["likes"]) / len(v["likes"]), 1),
            "avg_er": round(sum(v["er"]) / len(v["er"]), 2),
            "count": len(v["views"]),
        }
        for k, v in by_type.items()
    }

    # 投稿時間帯比較
    def avg_er(lst):
        return round(sum(p.get("engagement_rate", 0) for p in lst) / len(lst), 2) if lst else 0.0

    noon = [p for p in recent if p.get("post_time", "")[:2] in ("11", "12")]
    evening = [p for p in recent if p.get("post_time", "")[:2] in ("20", "21")]
    time_cmp = {
        "12:00": {"count": len(noon), "avg_er": avg_er(noon)},
        "21:00": {"count": len(evening), "avg_er": avg_er(evening)},
    }

    post_details = [
        {
            "title": p["title"],
            "type": p["type"],
            "views": p.get("metrics", {}).get("views", 0),
            "likes": p.get("metrics", {}).get("likes", 0),
            "replies": p.get("metrics", {}).get("replies", 0),
            "er": p.get("engagement_rate", 0),
        }
        for p in recent
    ]

    prompt = f"""あなたは日本のSNSマーケティング専門家です。
婚活 Threads アカウント「miki_konkatsu_life1212」の過去1週間のパフォーマンスを分析してください。

ペルソナ: 34歳・元婚活難民。28歳から6年間アプリ20社・出会い100人超で全滅。戦略変更後8ヶ月で入籍。
アフィリエイト: パートナーエージェント（19,523円/新規来店）

《投稿タイプ別パフォーマンス》
{json.dumps(summary, ensure_ascii=False, indent=2)}

《投稿時間帯比較》
{json.dumps(time_cmp, ensure_ascii=False, indent=2)}

《直近投稿詳細》
{json.dumps(post_details, ensure_ascii=False, indent=2)}

以下を日本語で分析してください：

## 1. パフォーマンス総評
## 2. 最も効果的だった投稿タイプと理由
## 3. 改善が必要なタイプと具体的改善案
## 4. 投稿時間帯の評価と推奨
## 5. 次週の投稿戦略（優先タイプ・テーマ）
## 6. 次週の投稿案（3本、ミキキャラで具体的なテキスト込み）
"""

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    report_text = resp.content[0].text
    week = datetime.now().strftime("%Y-W%V")

    metrics_data["weekly_reports"].append({
        "week": week,
        "generated_at": datetime.now().isoformat(),
        "summary": summary,
        "report": report_text,
    })
    save_json(METRICS_FILE, metrics_data)

    report_path = BASE_DIR / f"konkatsu_report_{week}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# 婚活 Threads 週次レポート {week}\n\n")
        f.write(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(report_text)
    print(f"[分析] レポート生成完了: {report_path.name}")
    print(f"\n{report_text[:300]}...")


def main():
    weekly = "--weekly" in sys.argv
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] メトリクス収集開始")
    collect_metrics()
    if weekly:
        print("\n[週次分析] 開始")
        analyze_weekly()
    print("完了")


if __name__ == "__main__":
    main()
