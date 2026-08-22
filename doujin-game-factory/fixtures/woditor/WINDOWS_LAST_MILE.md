# Windows last mile

Cloud / Linux / スマホだけでは Game.exe は作れない。
必要手順:
1. Windows（自宅PC、クラウドVM、誰かへの依頼）で公式ウディタを入れる
2. 空プロジェクトを作る
3. `commands.txt` をイベントに貼る、または将来 `-txtinput` 用テキストへ変換する
4. `Editor.exe -gamedata` で配布用フォルダを出す
5. Editor.exe 自体は配布しない（公式の配布物ルール）

自動化の境界: ここまでが人間または Windows ランナー。IR 生成までは Cloud Agent。
