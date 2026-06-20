#!/usr/bin/env python
"""
GitHub Actions 用 婚活 Threads 自動投稿スクリプト
konkatsu_posts.json から順番に投稿し、konkatsu_state.json で進捗を管理する。
キューが空の場合はニッチ設定のテンプレートから生成。

使い方:
  python scripts/post_konkatsu_gha.py        # 通常実行
  python scripts/post_konkatsu_gha.py test   # 投稿せずに内容確認
"""
import json
import random
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

POSTS_FILE = BASE_DIR / "konkatsu_posts.json"
STATE_FILE = BASE_DIR / "konkatsu_state.json"
NICHE_CONFIG_FILE = BASE_DIR / "config/niches/konkatsu.json"
NICHE_ID = "konkatsu"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def pick_from_template(niche_config):
    """ニッチ設定のテンプレートからランダムにコンテンツを作成する（AI不要）。"""
    templates = niche_config.get("templates", {}).get("threads", {})
    content_types = [
        ct for ct in niche_config.get("content_types", {}).get("threads", [])
        if ct in templates
    ]
    if not content_types:
        content_types = list(templates.keys())

    content_type = random.choice(content_types)
    template = templates[content_type]
    hook = random.choice(template["hooks"])
    cta = template.get("cta", "")

    hashtags = niche_config.get("hashtags", {})
    base_tags = hashtags.get("base", [])
    type_tags = hashtags.get(content_type, [])
    tags = list(dict.fromkeys(base_tags + type_tags))[:5]

    text = hook
    if cta:
        text += f"\n\n{cta}"
    if tags:
        text += "\n\n" + " ".join(tags)

    return {"text": text, "type": content_type, "generated": True}


def main():
    dry_run = len(sys.argv) > 1 and sys.argv[1] == "test"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] 婚活 Threads 投稿開始")

    posts = load_json(POSTS_FILE)
    state = load_json(STATE_FILE) if STATE_FILE.exists() else {"next_index": 0, "total_posted": 0}
    niche_config = load_json(NICHE_CONFIG_FILE)

    idx = state.get("next_index", 0)

    if idx < len(posts):
        content = posts[idx]
        print(f"[Queue] {idx + 1}/{len(posts)}: {content.get('title', '')}")
        state["next_index"] = idx + 1
    else:
        content = pick_from_template(niche_config)
        print(f"[Template] タイプ: {content['type']}")

    print(f"[内容]\n{content['text']}\n")

    if dry_run:
        print("[テストモード] 投稿はスキップされました")
        return

    from platforms.threads.poster import ThreadsPoster
    poster = ThreadsPoster(NICHE_ID)
    poster.post_text(content)

    state["total_posted"] = state.get("total_posted", 0) + 1
    save_json(STATE_FILE, state)
    print(f"[完了] 累計投稿数: {state['total_posted']}")


if __name__ == "__main__":
    main()
