"""
翌日リサーチ自動起動スクリプト

YouTube投稿の翌日に monitor_and_research.py を自動実行する。
posted_log.json に昨日の投稿記録があれば実行、なければスキップ。

【Windows タスクスケジューラー設定手順】
  1. タスクスケジューラーを開く（Win+S → "タスクスケジューラー"）
  2. 「基本タスクの作成」
  3. 名前: SNS Bot 翌日リサーチ
  4. トリガー: 毎日 → 開始時刻: 10:00
  5. 操作: プログラムの開始
     プログラム: C:\Users\ys734\AppData\Local\Programs\Python\Python314\python.exe
     引数:       daily_check.py
     開始場所:   C:\Users\ys734\Desktop\Research\sns-affiliate-bot
  6. 完了

使い方（手動テスト）:
  python daily_check.py          # 昨日の投稿を確認して実行 or スキップ
  python daily_check.py --force  # 強制実行（テスト用）
"""

import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

POST_LOG  = Path("posted_log.json")
SCRIPT    = Path("monitor_and_research.py")


def load_log() -> list[dict]:
    if not POST_LOG.exists():
        return []
    try:
        return json.loads(POST_LOG.read_text(encoding="utf-8"))
    except Exception:
        return []


def was_posted_yesterday() -> list[dict]:
    yesterday = str(date.today() - timedelta(days=1))
    log = load_log()
    return [entry for entry in log if entry.get("posted_date") == yesterday]


def run_research():
    print(f"  monitor_and_research.py を実行します...")
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=str(Path(__file__).parent),
    )
    return result.returncode == 0


def main():
    force = "--force" in sys.argv

    print("=" * 50)
    print("翌日リサーチ 自動チェック")
    print("=" * 50)

    if force:
        print("  ⚡ 強制実行モード")
        run_research()
        return

    posted = was_posted_yesterday()

    if not posted:
        yesterday = str(date.today() - timedelta(days=1))
        print(f"  ℹ️  昨日（{yesterday}）の投稿記録なし → スキップ")
        return

    yesterday = str(date.today() - timedelta(days=1))
    print(f"  ✅ 昨日（{yesterday}）の投稿を検出:")
    for p in posted:
        print(f"     - 「{p.get('title', '不明')}」 {p.get('url', '')}")

    print()
    ok = run_research()
    if ok:
        print("\n✅ リサーチ完了。reports/ フォルダを確認してください。")
    else:
        print("\n❌ リサーチ中にエラーが発生しました。手動で確認してください。")


if __name__ == "__main__":
    main()
