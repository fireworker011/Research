#!/usr/bin/env python3
"""
Windows タスクスケジューラ 登録スクリプト

使い方（sns-affiliate-bot フォルダで実行）:
  python scheduler/windows_task.py install    # タスクを登録
  python scheduler/windows_task.py uninstall  # タスクを削除
  python scheduler/windows_task.py status     # 登録状態を確認

登録されるタスク:
  - SNS-AffiliateBot-Career: メインスケジューラ（毎日8:00起動、常時実行）
  - SNS-AffiliateBot-TokenCheck: Threadsトークン残日数チェック（毎週月曜）
"""

import os
import subprocess
import sys
from pathlib import Path


def get_python_path() -> str:
    return sys.executable


def get_project_root() -> Path:
    return Path(__file__).parent.parent.resolve()


def create_bat_file(root: Path, python_path: str) -> Path:
    """バックグラウンド実行用の .bat ファイルを生成する。"""
    bat_content = f"""@echo off
cd /d "{root}"
"{python_path}" main.py run career >> logs\\scheduler.log 2>&1
"""
    bat_path = root / "scheduler" / "run_scheduler.bat"
    bat_path.write_text(bat_content, encoding="utf-8")
    return bat_path


def create_token_check_bat(root: Path, python_path: str) -> Path:
    """トークン確認用の .bat ファイルを生成する。"""
    bat_content = f"""@echo off
cd /d "{root}"
"{python_path}" setup/threads_token.py check >> logs\\token_check.log 2>&1
"""
    bat_path = root / "scheduler" / "check_token.bat"
    bat_path.write_text(bat_content, encoding="utf-8")
    return bat_path


def create_vbs_wrapper(bat_path: Path) -> Path:
    """コンソールウィンドウを表示せずに .bat を実行する .vbs ファイルを生成する。"""
    vbs_content = f'CreateObject("WScript.Shell").Run "{bat_path}", 0, False\n'
    vbs_path = bat_path.with_suffix(".vbs")
    vbs_path.write_text(vbs_content, encoding="utf-8")
    return vbs_path


def schtasks_create(task_name: str, command: str, schedule_type: str, start_time: str = "08:00", day: str = "") -> bool:
    """schtasks コマンドでタスクを登録する。"""
    args = [
        "schtasks", "/create",
        "/tn", task_name,
        "/tr", command,
        "/sc", schedule_type,
        "/st", start_time,
        "/f",
    ]
    if schedule_type == "WEEKLY" and day:
        args += ["/d", day]
    result = subprocess.run(args, capture_output=True, text=True, encoding="cp932")
    if result.returncode == 0:
        return True
    print(f"  schtasks エラー: {result.stderr.strip()}")
    return False


def cmd_install():
    root = get_project_root()
    python_path = get_python_path()
    logs_dir = root / "logs"
    logs_dir.mkdir(exist_ok=True)

    print(f"プロジェクトルート: {root}")
    print(f"Python: {python_path}")
    print()

    bat_path = create_bat_file(root, python_path)
    vbs_path = create_vbs_wrapper(bat_path)
    print(f"✅ 起動スクリプト作成: {bat_path.name}")

    token_bat = create_token_check_bat(root, python_path)
    token_vbs = create_vbs_wrapper(token_bat)
    print(f"✅ トークン確認スクリプト作成: {token_bat.name}")

    print("\nWindowsタスクスケジューラに登録中...")

    ok1 = schtasks_create(
        task_name="SNS-AffiliateBot-Career",
        command=f'wscript.exe "{vbs_path}"',
        schedule_type="DAILY",
        start_time="08:00",
    )
    if ok1:
        print("✅ SNS-AffiliateBot-Career: 毎日 08:00 に起動するよう登録")
    else:
        print("❌ メインタスク登録失敗（管理者権限で実行してみてください）")

    ok2 = schtasks_create(
        task_name="SNS-AffiliateBot-TokenCheck",
        command=f'wscript.exe "{token_vbs}"',
        schedule_type="WEEKLY",
        start_time="09:00",
        day="MON",
    )
    if ok2:
        print("✅ SNS-AffiliateBot-TokenCheck: 毎週月曜 09:00 に実行するよう登録")
    else:
        print("❌ トークン確認タスク登録失敗")

    print("""
=== 完了 ===

次回から毎日 08:00 に自動で投稿スケジューラが起動します。
ログ確認: logs/scheduler.log

手動テスト（今すぐ動かす場合）:
  python main.py post threads career

完全自動モード（手動起動）:
  python main.py run career

注意: PC がスリープ中はタスクが実行されません。
  常時稼働が必要な場合はVPS（さくらのVPS, ConoHa等）への移行を検討してください。
""")


def cmd_uninstall():
    tasks = ["SNS-AffiliateBot-Career", "SNS-AffiliateBot-TokenCheck"]
    for task in tasks:
        result = subprocess.run(
            ["schtasks", "/delete", "/tn", task, "/f"],
            capture_output=True, text=True, encoding="cp932",
        )
        if result.returncode == 0:
            print(f"✅ {task} を削除しました。")
        else:
            print(f"⚠️  {task}: {result.stderr.strip()}")


def cmd_status():
    tasks = ["SNS-AffiliateBot-Career", "SNS-AffiliateBot-TokenCheck"]
    print("=== タスクスケジューラ登録状態 ===\n")
    for task in tasks:
        result = subprocess.run(
            ["schtasks", "/query", "/tn", task, "/fo", "LIST"],
            capture_output=True, text=True, encoding="cp932",
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if any(k in line for k in ["タスク名", "状態", "次の実行時刻", "TaskName", "Status", "Next Run"]):
                    print(f"  {line.strip()}")
            print()
        else:
            print(f"  ❌ {task}: 未登録\n")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "install":
        cmd_install()
    elif cmd == "uninstall":
        cmd_uninstall()
    elif cmd == "status":
        cmd_status()
    else:
        print(__doc__)
