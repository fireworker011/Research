#!/usr/bin/env python
"""
婚活ニッチ Threads 自動投稿スクリプト

queue/threads/konkatsu/pending/ にある .json ファイルを
ファイル名順に1件取り出して投稿する。
キューが空の場合はテンプレートからランダム生成して投稿。

使い方:
  python scripts/post_konkatsu.py        # 通常実行
  python scripts/post_konkatsu.py test   # 投稿せずに内容確認
"""
import json
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

NICHE_ID = "konkatsu"
PENDING_DIR = BASE_DIR / f"queue/threads/{NICHE_ID}/pending"
DONE_DIR = BASE_DIR / f"queue/threads/{NICHE_ID}/done"


def read_json(path):
    """BOM付きUTF-8にも対応してJSONを読む。"""
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def get_next_pending():
    """pendingフォルダから最も古い投稿ファイルを返す。"""
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    posts = sorted(PENDING_DIR.glob("*.json"))
    return posts[0] if posts else None


def mark_done(path):
    """投稿済みファイルを done/ に移動する。"""
    DONE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(DONE_DIR / path.name))
    print(f"[Queue] 完了: {path.name} -> done/")


def post_from_queue(dry_run=False):
    """キューから次の投稿を取得して Threads に投稿する。"""
    from platforms.threads.poster import ThreadsPoster

    post_path = get_next_pending()
    if not post_path:
        print("[Queue] キューが空です。テンプレートから生成します。")
        return False

    content = read_json(post_path)

    print(f"[Queue] 投稿: {post_path.name}")
    print(f"[内容]\n{content['text']}\n")

    if dry_run:
        print("[テストモード] 投稿はスキップされました")
        return True

    poster = ThreadsPoster(NICHE_ID)
    poster.post_text(content)
    mark_done(post_path)
    return True


def post_from_template(dry_run=False):
    """テンプレートからコンテンツを生成して Threads に投稿する。"""
    from content.generator import ContentGenerator
    from platforms.threads.poster import ThreadsPoster
    from ai.provider import AIProvider

    config_path = BASE_DIR / f"config/niches/{NICHE_ID}.json"
    niche_config = read_json(config_path)

    generator = ContentGenerator(niche_config, AIProvider())
    content = generator.generate_threads_post()

    print(f"[Template] 生成完了\n{content['text']}\n")

    if dry_run:
        print("[テストモード] 投稿はスキップされました")
        return

    poster = ThreadsPoster(NICHE_ID)
    poster.post_text(content)


def main():
    dry_run = len(sys.argv) > 1 and sys.argv[1] == "test"
    if dry_run:
        print("[テストモード] 投稿は実行されません")

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] 婚活 Threads 投稿開始")

    try:
        if not post_from_queue(dry_run):
            post_from_template(dry_run)
        print(f"[{ts}] 完了")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
