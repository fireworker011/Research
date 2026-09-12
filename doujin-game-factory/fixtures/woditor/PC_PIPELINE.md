# PCパイプライン（ウディタ本線）

前提: Windows PC で公式 WOLF RPGエディターを使う。
Linux の Cloud Agent は Editor.exe を実行できない。生成物を PC に持っていく。

## 1. 一度だけ

1. https://silversecond.com/WolfRPGEditor/ から最新版を入れる（解凍するだけ）
2. Node.js LTS を入れる
3. 環境変数 `WOLF_DIR` を `Editor.exe` があるフォルダにする
4. `scripts\windows\01_check.bat` を実行し、Editor.exe が見えることを確認する

## 2. 毎回（作品ごと）

1. `node src/cli.js generate --seed data/seeds/sample-adult-adv.json`
2. `node src/cli.js woditor --in output/ir/game.json`
3. Editor.exe を起動し、サンプルゲームを複製した空プロジェクトを開く
4. タイトルマップにイベントを1つ置き、起動条件を「自動実行」
5. `output/woditor/event-code.txt` を全選択コピー
6. イベントコマンド欄で右クリック → 「クリップボード→コード貼り付け」（Eキー）。Vキーでは貼れない
7. Ctrl+T または F9 でテストプレイ。両分岐を最後まで通す
8. 絵・音は Data 配下に入れてから、必要ならコマンドを手で足す
9. `scripts\windows\04_gamedata.bat` または Editor のゲームデータ作成。Editor.exe は配布フォルダに入れない
10. 出力フォルダを zip して DLsite/FANZA に出す。AI申告を偽らない

## 3. 公式テキスト入出力（任意）

共同作業・バックアップ用。ゲーム中には読めない。

```
Editor.exe -txtoutput -txt_folder Data_AutoTXT -target ALL -wait
Editor.exe -txtinput  -txt_folder Data_AutoTXT -target ALL -wait
Editor.exe -gamedata -crypt NO
```

`scripts\windows\03_txtoutput.bat` が同じことをする。
複数保存(TXT)のコモン一括形式は、公式サンプル無しでは捏造しない。貼り付け経路を正とする。

## 4. まだ自動化しないこと

- マップタイルの配置
- 戦闘・データベース一式
- 審査提出そのもの
- 週4本（DLsite AI生成の申請月3と衝突）

一次情報:

- 起動引数: https://silversecond.com/WolfRPGEditor/Help/01control.html
- 自動テキスト出力: https://silversecond.com/WolfRPGEditor/Help/02editor_option.html
- コモンの txt 読込: https://silversecond.com/WolfRPGEditor/Help/02commonev.html
- イベントコードの貼り付け例: http://yado.tk/wolf/01_shoshin/1003_ibekoma_hyouji/
