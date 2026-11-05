# 同人成人ゲーム工場（PC / ウディタ前提）

制約を「ほぼPC不可」から **Windows PC で作業する** に切り替えた。エンジンはウディタを本線にする。

切り替えても死んだままのこと:

- DLsite の AI生成は申請月3本。週1（≈4本）は販売枠で死ぬ。PCは関係ない
- 月利200万は売価2200・取り分0.6仮定で約1516本/月。未出荷で計画値にするな
- 戦闘付きRPGは最初の検証物にしない。工数最大で需要未証明

## PCで動かす

Windows に Node.js と [WOLF RPGエディター](https://silversecond.com/WolfRPGEditor/) を入れる。

```bat
set WOLF_DIR=C:\path\to\WOLF_RPG_Editor
cd doujin-game-factory
node --test
node src/cli.js generate --seed data/seeds/sample-adult-adv.json
node src/cli.js woditor --in output/ir/game.json
scripts\windows\01_check.bat
```

1. Editor で空プロジェクト（サンプル複製）を開く
2. タイトルマップにイベントを1つ、起動条件「自動実行」
3. `output/woditor/event-code.txt` をコピーし、コマンド欄で **E**（クリップボード→コード貼り付け）。Vでは貼れない
4. F9 で両分岐を通す
5. `scripts\windows\04_gamedata.bat` で配布用フォルダ。Editor.exe は入れない

手順の全文は `docs/PC_PIPELINE.md` と `scripts/windows/`。

`fixtures/preview/index.html` はグラフ確認用。本番テストは Editor の F9。

## 変更後の決定

| 今決める | 後で決める |
|---|---|
| エンジンはウディタ | 戦闘システムを足すか |
| 初作は短い成人ADV | 価格 |
| ペースは月1（キャップ内） | 世界観の量産 |
| 200万は初作30日30本の後 | FANZAゲーム行の月2の確定 |

失敗条件: event-code を貼って F9 が通らないのに量産する。AI非申告。未成年に見える絵。週1で申請する。

不可逆: 虚偽AI申告、未成年表現、複数サークル回避。  
可逆: 戦闘追加、価格、HTMLプレビューの併用。

## 数字（推定取り分。公式卸表が正）

`node src/cli.js gate --price 2200 --copies 0 --works 0`

週4本・1作10本売りのシミュレーションは `finance --copies 10 --works 4 --cap 3` で CAP と DEMAND_30 が同時に落ちる。

## フェーズ記録の修正点

前回の「PC不可だからウディタを外す」は、今回の前提では捨てる。  
前回の「週1と200万はキャップと未出荷で死ぬ」は残す。Xは未接続のまま調べていない。

詳細な問題定義・情報源・視点分析の原本は git の先行コミットを見よ。繰り返さない。
