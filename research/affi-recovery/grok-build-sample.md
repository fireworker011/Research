# Grok Build に貼る指示（見本1本）

あなたはナオミチの Windows PC（ユーザー `C:\Users\hp`）で動く。今やるのは、いらすとやの見本動画を1本だけ作ること。投稿しない。台本を新しく書かない。H3 も Imagine も触らない。ブランチをマージしない。push しない。トークンやパスワードをファイルにもチャットにも書かない。

作業の枠は平日 6:30〜7:30 の1時間。同じ失敗は1回で止める。別の入れ方を探してやり直さない。

終わったら、下の「報告」の形で日本語だけ返す。

## 止める

次のどれかなら、その場で止めて報告する。続きを推測で埋めない。

- コマンドが失敗した
- 認証を聞かれた（GitHub のログイン、規約の同意で先に進めない）
- 指定したファイルが無い
- `make` に渡す JSON に `bullets` が無い
- 日本語フォントが3候補とも無い
- mp4 が空、または出来ていない

止めたあとに、台本の文を足す、別ブランチへ乗り換える、画像を自作する、投稿する、はしない。

## 置く場所

- リポジトリ: `C:\Users\hp\Documents\affi\Research`
- 仮想環境: `C:\Users\hp\Documents\affi\venv`
- 見本: `C:\Users\hp\Documents\affi\sample\ogori.mp4`
- 作業フォルダ: `C:\Users\hp\Documents\affi\sample\work`
- 次回用の手順: `C:\Users\hp\Documents\affi\GROK-BUILD.md`
- 次回用のスキル: `C:\Users\hp\Documents\affi\skills\irasutoya-sample\SKILL.md`

`C:\Users\hp\Documents\affi` が無ければ作る。

## 1. 道具を確かめる

PowerShell で、あるものには手を付けない。無いものだけ入れる。winget が失敗したら止める。別のサイトから探さない。

1. `git --version`
   無ければ `winget install -e --id Git.Git`
2. `py -3 --version`
   3.10 以上でなければ `winget install -e --id Python.Python.3.11`
   入れた直後は PowerShell を開き直し、もう一度 `py -3 --version` を見る。3.10 未満のままなら止める。
3. `ffmpeg -version`
   無ければ `winget install -e --id Gyan.FFmpeg`
   入れた直後は PowerShell を開き直す。まだ PATH に無ければ止める。`make` の前に、この窓で `ffmpeg -version` が通っていること。
4. tesseract は無くてよい。文字入り素材の検査が弱くなる、と報告に1行書く。入れない。

仮想環境が無ければ作る。既にあれば作り直さない。

```powershell
py -3 -m venv C:\Users\hp\Documents\affi\venv
```

以降の Python は `C:\Users\hp\Documents\affi\venv\Scripts\python.exe` をフルパスで使う。`Activate.ps1` は使わない。

## 2. ブランチを取る

次の4つだけ見る。ディスク全体は探さない。

- `C:\Users\hp\Documents\affi\Research`
- `C:\Users\hp\Documents\Research`
- `C:\Users\hp\source\Research`
- `C:\Users\hp\Research`

`tools\irasutoya-short` があるフォルダが1つあれば、それを使う。無ければ次でクローンする。

```powershell
git clone --branch cursor/irasutoya-short-pipeline-a21d --single-branch https://github.com/fireworker011/Research.git C:\Users\hp\Documents\affi\Research
```

既にある場合は、そのフォルダで次だけ行う。ローカルの変更で checkout が拒否されたら、捨てずに止める。

```powershell
git fetch origin cursor/irasutoya-short-pipeline-a21d
git checkout cursor/irasutoya-short-pipeline-a21d
```

今のブランチが `cursor/irasutoya-short-pipeline-a21d` であることを `git status -sb` で確認する。違うなら止める。

## 3. 既存の ogori を取る

このブランチの例は `tools\irasutoya-short\examples\oshitsuke.json` だけである。ogori の JSON は無い。

`make` が読める既存ファイルは、別ブランチ `cursor/script-kata-measure-a21d` の `tools/irasutoya-short/examples/ogori.json` である。中身は hook、bullets、punchline、asset_urls。台本は新しく書かない。この1ファイルだけを作業ツリーに出す。

```powershell
cd C:\Users\hp\Documents\affi\Research
git fetch origin cursor/script-kata-measure-a21d
git checkout origin/cursor/script-kata-measure-a21d -- tools/irasutoya-short/examples/ogori.json
```

`research/script-kata/scripts/irasutoya-ogori.json` はシーン表で、bullets が無い。このブランチの `make` は bullets が空だと止まる。そのファイルは取らない。文を足して直さない。

取った JSON を Python で読み、`bullets` が1件以上あることだけ確認する。無ければ止める。中身の文は変えない。`closing` が空でも埋めない。コードが空の closing を「あなたならどうする？」にするなら、そのままでよい。直さない。報告にその旨を書く。

この JSON はコミットしない。

## 4. ライブラリと VOICEVOX

`tools\irasutoya-short` で、仮想環境に入れる。

```powershell
cd C:\Users\hp\Documents\affi\Research\tools\irasutoya-short
C:\Users\hp\Documents\affi\venv\Scripts\python.exe -m pip install -r requirements.txt
C:\Users\hp\Documents\affi\venv\Scripts\python.exe -m pip install "https://github.com/VOICEVOX/voicevox_core/releases/download/0.16.4/voicevox_core-0.16.4-cp310-abi3-win_amd64.whl"
```

wheel のインストールが失敗したら止める。Linux 用の wheel は入れない。

実行ファイルの置き場所は `C:\Users\hp\.cache\irasutoya-short\voicevox`。次の3つが揃っていれば、ダウンロードはしない。

- `dict\open_jtalk_dic_utf_8-1.11` がフォルダである
- `onnxruntime\lib` に onnxruntime の DLL がある
- `models\vvms\0.vvm` と `4.vvm` と `9.vvm` がある

揃っていなければ、0.16.4 の Windows 用ダウンローダだけを使う。

```powershell
New-Item -ItemType Directory -Force -Path C:\Users\hp\.cache\irasutoya-short\voicevox
Invoke-WebRequest -Uri "https://github.com/VOICEVOX/voicevox_core/releases/download/0.16.4/download-windows-x64.exe" -OutFile C:\Users\hp\AppData\Local\Temp\download-windows-x64.exe
```

引数は README と同じである。最初に本体と `0.vvm`。続けて `4.vvm` と `9.vvm` だけ。他の vvm は落とさない。青山龍星は使わない。

```powershell
$vv = "C:\Users\hp\.cache\irasutoya-short\voicevox"
$dl = "C:\Users\hp\AppData\Local\Temp\download-windows-x64.exe"
echo y | & $dl --exclude c-api --exclude additional-libraries --models-pattern "0.vvm" -o $vv
echo y | & $dl --only models --models-pattern "4.vvm" -o $vv
echo y | & $dl --only models --models-pattern "9.vvm" -o $vv
```

`--help` に `--models-pattern` が無い、または規約の同意で止まった、なら止める。別バージョンは落とさない。`echo y` は、ダウンローダが規約の確認に y を求めたときだけ意味がある。

確認:

```powershell
$env:IRASUTOYA_VOICEVOX = "C:\Users\hp\.cache\irasutoya-short\voicevox"
$env:PYTHONPATH = "C:\Users\hp\Documents\affi\Research\tools\irasutoya-short"
C:\Users\hp\Documents\affi\venv\Scripts\python.exe -m irasutoya_short doctor
```

表示が `voicevox: ok` でなければ止める。`make` は始めない。

## 5. 日本語フォントを1行足す

`irasutoya_short\constants.py` の `FONT_CANDIDATES` は Linux のパスだけである。Windows では、次のうち実在する最初の1つを、タプルの先頭に足す。足すのはパスだけ。シーンも台本も変えない。既にそのパスがあれば足さない。

1. `C:\Windows\Fonts\YuGothM.ttc`
2. `C:\Windows\Fonts\meiryo.ttc`
3. `C:\Windows\Fonts\msgothic.ttc`

3つとも無ければ止める。フォントをダウンロードしない。この変更はコミットしない。

## 6. 見本を1本作る

unittest は回さない。スクショは渡さない。

```powershell
cd C:\Users\hp\Documents\affi\Research\tools\irasutoya-short
$env:PYTHONPATH = "C:\Users\hp\Documents\affi\Research\tools\irasutoya-short"
$env:IRASUTOYA_VOICEVOX = "C:\Users\hp\.cache\irasutoya-short\voicevox"
$env:PYTHONUTF8 = "1"
New-Item -ItemType Directory -Force -Path C:\Users\hp\Documents\affi\sample
C:\Users\hp\Documents\affi\venv\Scripts\python.exe -m irasutoya_short make .\examples\ogori.json --work C:\Users\hp\Documents\affi\sample\work --out C:\Users\hp\Documents\affi\sample\ogori.mp4
```

失敗したら止める。作り直さない。`revise` は今回やらない。

出来たあとに確認する。

- `C:\Users\hp\Documents\affi\sample\ogori.mp4` が存在し、サイズが 0 ではない
- `C:\Users\hp\Documents\affi\sample\work\REPORT.json` を読む

報告に書く数字は、この REPORT にあるものだけ。`duration_sec`、`scene_count`、`asset_count`、`within_25_40`、`credits`。無い項目は「REPORTに無い」。`within_25_40` が false でも、mp4 が出来ていれば作り直さない。

投稿しない。YouTube も TikTok も開かない。

## 7. 次回は一言で回す

成功したときだけ、次の2ファイルを書く。失敗で止めたときは書かない。

`C:\Users\hp\Documents\affi\GROK-BUILD.md` には、今日通ったコマンドをそのまま書く。

- ブランチ名 `cursor/irasutoya-short-pipeline-a21d`
- Python のフルパス
- `IRASUTOYA_VOICEVOX` と `PYTHONPATH`
- `make` の1行（同じ JSON、同じ出力先）
- 一言「見本をもう一回」は、再インストールをせず、この `make` だけを実行する意味である
- 投稿しない。台本を書かない。コミットしない

`C:\Users\hp\Documents\affi\skills\irasutoya-sample\SKILL.md` には、同じ一言の手順だけを短く書く。Grok Build が別のスキル置き場を既に持っているなら、そこにも同じファイルをコピーし、報告にそのパスを書く。置き場が無いなら、上のパスだけでよい。新しい仕組みは作らない。

## 報告

この形だけ。

```
結果: できた
または
結果: 止めた

止めた段: （成功なら「なし」。失敗なら番号とコマンドと、エラーの末尾）
mp4: C:\Users\hp\Documents\affi\sample\ogori.mp4
REPORT: duration_sec / scene_count / asset_count / within_25_40 / credits
締めの問い: （コードが入れたなら「入った」。確認できないなら「未確認」）
tesseract: あり / なし
投稿: していない
手順書: C:\Users\hp\Documents\affi\GROK-BUILD.md
スキル: （書いたパス。書いていなければ「なし」）
```
