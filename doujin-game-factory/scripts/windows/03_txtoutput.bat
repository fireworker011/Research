@echo off
setlocal
if not defined WOLF_DIR (
  echo WOLF_DIR が未設定。
  exit /b 1
)
if not exist "%WOLF_DIR%\Editor.exe" (
  echo Editor.exe が見つからない。
  exit /b 1
)
cd /d "%WOLF_DIR%"
echo ゲームデータをテキストへ出す。プロジェクトを一度 Editor で保存してから実行すること。
Editor.exe -txtoutput -txt_folder Data_AutoTXT -target ALL -wait
echo 終わったら Data_AutoTXT を Git に入れてよい。ゲーム中には読めない。
exit /b 0
