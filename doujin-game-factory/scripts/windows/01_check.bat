@echo off
setlocal
if not defined WOLF_DIR (
  echo WOLF_DIR が未設定。Editor.exe があるフォルダを指定する。
  echo 例: set WOLF_DIR=C:\Games\WOLF_RPG_Editor
  exit /b 1
)
if not exist "%WOLF_DIR%\Editor.exe" (
  echo Editor.exe が見つからない: %WOLF_DIR%\Editor.exe
  exit /b 1
)
if not exist "%WOLF_DIR%\Game.exe" (
  echo Game.exe が見つからない。公式パッケージが壊れている。
  exit /b 1
)
echo OK Editor.exe
echo OK Game.exe
echo 次: node src/cli.js generate と woditor を回し、event-code.txt を自動実行イベントへ貼る。
exit /b 0
