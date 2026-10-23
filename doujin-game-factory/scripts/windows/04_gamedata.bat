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
echo 直前に Editor で開いていたプロジェクトと同じ設定でゲームデータを作る。
echo Editor.exe は出力フォルダに入れないこと。
Editor.exe -gamedata -crypt NO
echo 出力先は最後に Editor 内で指定した場所。確認して zip する。
exit /b 0
