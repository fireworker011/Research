#!/usr/bin/env python
"""
GitHub Actions 用 婚活 Threads 自動投稿スクリプト
konkatsu_posts.json から順番に投稿し、konkatsu_state.json で進捗を管理する。
使い方:
  python scripts/post_konkatsu_gha.py        # 通常実行
  python scripts/post_konkatsu_gha.py test   # 投稿せずに内容確認
"""
import importlib.util
import json
import random
import sys
import time
import types
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

POSTS_FILE = BASE_DIR / "konkatsu_posts.json"
STATE_FILE = BASE_DIR / "konkatsu_state.json"
NICHE_CONFIG_FILE = BASE_DIR / "config/niches/konkatsu.json"
NICHE_ID = "konkatsu"
MAX_RECENT_POSTS = 30


def load_json(path, default=None):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_threads_poster():
    """
    platforms/__init__.py のYouTube自動インポートを回避して
    ThreadsPosterだけを直接読み込む。
    """
    for pkg_name, pkg_path in [
        ("platforms", BASE_DIR / "platforms"),
        ("platforms.threads", BASE_DIR / "platforms" / "threads"),
    ]:
        if pkg_name not in sys.modules:
            pkg = types.ModuleType(pkg_name)
            pkg.__path__ = [str(pkg_path)]
            pkg.__package__ = pkg_name
            sys.modules[pkg_name] = pkg

    def _load(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod

    _load("platforms.threads.client", BASE_DIR / "platforms" / "threads" / "client.py")
    poster_mod = _load("platforms.threads.poster", BASE_DIR / "platforms" / "threads" / "poster.py")
    return poster_mod.ThreadsPoster


def pick_from_template(niche_config):
    """AI不要でテンプレートからコンテンツを作成する。"""
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
    tags = list(dict.fromkeys(
        hashtags.get("base", []) + hashtags.get(content_type, [])
    ))[:5]

    text = hook
    if cta:
        text += f"\n\n{cta}"
    if tags:
        text += "\n\n" + " ".join(tags)

    return {"text": text, "type": content_type, "generated": True}


def save_post_to_state(state, post_id, content, posted_at):
    """post_id を state の recent_posts に追加する。"""
    recent = state.setdefault("recent_posts", [])
    recent.append({
        "post_id": post_id,
        "posted_at": posted_at,
        "title": content.get("title", ""),
        "type": content.get("type", ""),
    })
    # 直近30件のみ保持
    state["recent_posts"] = recent[-MAX_RECENT_POSTS:]


def main():
    dry_run = len(sys.argv) > 1 and sys.argv[1] == "test"

    # BOT判定回避: 1～5分のランダム遅延
    if not dry_run:
        delay = random.randint(60, 300)
        print(f"[遅延] {delay}秒待機中...")
        time.sleep(delay)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] 婚活 Threads 投稿開始")

    posts = load_json(POSTS_FILE, [])
    state = load_json(STATE_FILE, {"next_index": 0, "total_posted": 0})
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

    ThreadsPoster = load_threads_poster()
    poster = ThreadsPoster(NICHE_ID)
    result = poster.post_text(content)

    post_id = result.get("post_id", "")
    posted_at = datetime.now().isoformat()
    save_post_to_state(state, post_id, content, posted_at)

    state["total_posted"] = state.get("total_posted", 0) + 1
    save_json(STATE_FILE, state)
    print(f"[完了] post_id={post_id} / 累計: {state['total_posted']}")


if __name__ == "__main__":
    main()
