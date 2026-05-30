#!/usr/bin/env python3
"""
Windows タスクスケジューラ 登録スクリプト

使い方（sns-affiliate-bot フォルダで実行）:
  python scheduler/windows_task.py install-weekly   # 1週間トライアル登録（08:00/12:00/19:00）
  python scheduler/windows_task.py setup-wake       # スリープ自動起床設定（install-weekly の後に実行）
  python scheduler/windows_task.py uninstall-weekly # 1週間トライアル解除
  python scheduler/windows_task.py status           # 登録状態を確認
  python scheduler/windows_task.py install          # 常時稼働スケジューラを登録（旧方式）
  python scheduler/windows_task.py uninstall        # 常時稼働スケジューラを削除（旧方式）

setup-wake でできること（スリープモード限定）:
  - 投稿時間の少し前に PC をスリープから自動起床
  - スリープ復帰後のパスワード要求を無効化
  ※ セッションは維持されるので自動ログイン設定は不要
  ※ 完全シャットダウンからの自動起動は BIOS 設定が必要（機種依存）
"""

import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

WEEKLY_TASKS = {
    "SNS-Threads-Career-Morning": "08:00",
    "SNS-Threads-Career-Noon":    "12:00",
    "SNS-Threads-Career-Evening": "19:00",
}


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


def cmd_install_weekly(days: int = 7):
    """1週間トライアル: 3時間帯それぞれに独立タスクを登録する（1投稿=1プロセス方式）。"""
    root = get_project_root()
    python_path = get_python_path()
    logs_dir = root / "logs"
    logs_dir.mkdir(exist_ok=True)

    end_date = (datetime.now() + timedelta(days=days)).strftime("%Y/%m/%d")

    # autopost 用 bat / vbs を生成（3タスクが共用）
    bat_path = root / "scheduler" / "autopost.bat"
    bat_content = (
        f"@echo off\r\n"
        f"cd /d \"{root}\"\r\n"
        f"\"{python_path}\" main.py autopost threads career >> logs\\autopost.log 2>&1\r\n"
    )
    bat_path.write_text(bat_content, encoding="utf-8")
    vbs_path = create_vbs_wrapper(bat_path)
    print(f"✅ 投稿スクリプト作成: {bat_path.name}")

    # トークン確認 bat / vbs
    token_bat = create_token_check_bat(root, python_path)
    token_vbs = create_vbs_wrapper(token_bat)

    print(f"\n期間: 今日 〜 {end_date}（{days}日間）")
    print("Windowsタスクスケジューラに登録中...\n")

    all_ok = True
    for task_name, time_str in WEEKLY_TASKS.items():
        args = [
            "schtasks", "/create",
            "/tn", task_name,
            "/tr", f'wscript.exe "{vbs_path}"',
            "/sc", "DAILY",
            "/st", time_str,
            "/ed", end_date,
            "/f",
        ]
        result = subprocess.run(args, capture_output=True, text=True, encoding="cp932")
        if result.returncode == 0:
            print(f"  ✅ {task_name}: 毎日 {time_str}")
        else:
            print(f"  ❌ {task_name}: 失敗 - {result.stderr.strip()}")
            all_ok = False

    ok_token = schtasks_create(
        task_name="SNS-AffiliateBot-TokenCheck",
        command=f'wscript.exe "{token_vbs}"',
        schedule_type="WEEKLY",
        start_time="09:00",
        day="MON",
    )
    if ok_token:
        print(f"  ✅ SNS-AffiliateBot-TokenCheck: 毎週月曜 09:00")
    else:
        print(f"  ❌ TokenCheck: 登録失敗")

    print(f"""
{'✅ 登録完了！' if all_ok else '⚠️  一部タスクの登録に失敗しました（管理者として実行し直してください）。'}

スケジュール:
  08:00 / 12:00 / 19:00 に Threads へ自動投稿（{end_date} まで）

ログ確認:
  logs/autopost.log      ← 投稿ログ（成功・失敗）
  logs/autopost_errors.log ← エラー詳細

1週間後は自動で停止します（タスクが終了日を過ぎると実行されません）。
手動で止めたい場合:
  python scheduler/windows_task.py uninstall-weekly

注意: PC がスリープ中はタスクが実行されません。
""")


def cmd_setup_wake():
    """
    スリープ（S3）からの自動起床を設定する。
    install-weekly でタスク登録済みであること。
    管理者権限で実行すること。
    """
    print("=== スリープ自動起床セットアップ ===\n")
    print("前提: PC を完全シャットダウンではなくスリープにして使用してください。")
    print("      スリープ中はセッションが保持されるため自動ログイン設定は不要です。\n")

    # 1. 各タスクに WakeToRun フラグを設定（PowerShell 経由）
    task_list = ", ".join(f'"{t}"' for t in WEEKLY_TASKS)
    ps_wake = f"""
$names = @({task_list})
foreach ($name in $names) {{
    $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if ($task) {{
        $task.Settings.WakeToRun = $true
        Set-ScheduledTask -InputObject $task | Out-Null
        Write-Output "  [OK] $name: WakeToRun 有効化"
    }} else {{
        Write-Output "  [SKIP] $name: 未登録 (install-weekly を先に実行してください)"
    }}
}}
"""
    r1 = subprocess.run(
        ["powershell", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps_wake],
        capture_output=True, text=True, encoding="utf-8",
    )
    print(r1.stdout or "（出力なし）")
    if r1.returncode != 0:
        print(f"❌ エラー: {r1.stderr.strip()}")
        print("管理者として実行し直してください。")
        return

    # 2. スリープ復帰時のパスワード要求を無効化
    #    GUID: スリープサブグループ / コンソールロック設定
    ps_pw = (
        "powercfg /setacvalueindex SCHEME_CURRENT "
        "238C9FA8-0AAD-41ED-83F4-97BE242C8F20 "
        "0E796BDB-100D-47D6-A2D5-F7D2DAA51F51 0 ; "
        "powercfg /setdcvalueindex SCHEME_CURRENT "
        "238C9FA8-0AAD-41ED-83F4-97BE242C8F20 "
        "0E796BDB-100D-47D6-A2D5-F7D2DAA51F51 0 ; "
        "powercfg /setactive SCHEME_CURRENT"
    )
    r2 = subprocess.run(
        ["powershell", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps_pw],
        capture_output=True, text=True,
    )
    if r2.returncode == 0:
        print("  [OK] スリープ復帰時のパスワード要求: 無効化")
    else:
        print(f"  [WARNING] パスワード設定変更に失敗しました: {r2.stderr.strip()}")
        print("           「設定 → アカウント → サインインオプション → スリープ解除時に必要」を手動でオフにしてください。")

    # 3. Windowsの「スリープ解除タイマーを許可」を有効化
    ps_timer = (
        "powercfg /setacvalueindex SCHEME_CURRENT "
        "238C9FA8-0AAD-41ED-83F4-97BE242C8F20 "
        "BD3B718A-0680-4D9D-8AB2-E1D2B4AC806D 1 ; "
        "powercfg /setdcvalueindex SCHEME_CURRENT "
        "238C9FA8-0AAD-41ED-83F4-97BE242C8F20 "
        "BD3B718A-0680-4D9D-8AB2-E1D2B4AC806D 1 ; "
        "powercfg /setactive SCHEME_CURRENT"
    )
    r3 = subprocess.run(
        ["powershell", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps_timer],
        capture_output=True, text=True,
    )
    if r3.returncode == 0:
        print("  [OK] スリープ解除タイマー: 許可")
    else:
        print(f"  [WARNING] タイマー設定失敗: {r3.stderr.strip()}")

    print("""
✅ セットアップ完了！

動作の流れ（例: 08:00 投稿）:
  夜：PC をスリープ
  07:59 頃：Windows がスリープから自動起床
  08:00：タスクスケジューラが python main.py autopost threads career を実行
  08:01：投稿完了、PC はそのまま or 次のタスクまで待機
  12:00 / 19:00 も同様に自動実行

注意:
  - スリープ（電源ランプ点滅中）は OK
  - 完全シャットダウン（電源オフ）は NG
    → シャットダウンから起動したい場合は BIOS/UEFI の
      「Wake on RTC アラーム」設定が必要（機種マニュアル参照）
""")


def cmd_uninstall_weekly():
    """1週間トライアルのタスクをすべて削除する。"""
    tasks = list(WEEKLY_TASKS.keys()) + ["SNS-AffiliateBot-TokenCheck"]
    print("タスクを削除中...")
    for task in tasks:
        result = subprocess.run(
            ["schtasks", "/delete", "/tn", task, "/f"],
            capture_output=True, text=True, encoding="cp932",
        )
        if result.returncode == 0:
            print(f"  ✅ {task} 削除")
        else:
            print(f"  ⚠️  {task}: {result.stderr.strip()}")
    print("完了。")


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
    all_tasks = (
        list(WEEKLY_TASKS.keys())
        + ["SNS-AffiliateBot-TokenCheck", "SNS-AffiliateBot-Career"]
    )
    print("=== タスクスケジューラ登録状態 ===\n")
    for task in all_tasks:
        result = subprocess.run(
            ["schtasks", "/query", "/tn", task, "/fo", "LIST"],
            capture_output=True, text=True, encoding="cp932",
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if any(k in line for k in [
                    "タスク名", "状態", "次の実行時刻", "最終実行時刻", "最終の結果",
                    "TaskName", "Status", "Next Run", "Last Run", "Last Result",
                ]):
                    print(f"  {line.strip()}")
            print()
        else:
            print(f"  - {task}: 未登録\n")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "install-weekly":
        cmd_install_weekly()
    elif cmd == "setup-wake":
        cmd_setup_wake()
    elif cmd == "uninstall-weekly":
        cmd_uninstall_weekly()
    elif cmd == "install":
        cmd_install()
    elif cmd == "uninstall":
        cmd_uninstall()
    elif cmd == "status":
        cmd_status()
    else:
        print(__doc__)
