# PC 常駐ランナー（Grok Build）

Windows の PC（ユーザー `hp`、マシン `LAPTOP-PL4TICBO`）で、注文ファイルを置いたら Grok Build がすぐ動くようにする常駐です。毎回 PowerShell を起動して結果を集め直す待ちを減らします。

モデルは常に `grok-4.7` です。`--reasoning-effort` は `high` か `xhigh` だけです。既定は `xhigh` です。fast モードは使いません。

`--always-approve` は、Grok のコマンドがツール確認で止まらないようにするためのフラグです。保存・送信・投稿・削除・公開・支払いは、下の確認ファイルで人間が許可します。

## フォルダ

PC 上の根は `C:\Users\hp\Documents\grokbuild` です（ログイン中のユーザーの `Documents\grokbuild`）。変えるときは環境変数 `GROKBUILD_ROOT` を置きます。

```
queue\inbox\       注文 *.md を置く
queue\running\     実行中
queue\done\        完了、または拒否して正常終了
queue\failed\      失敗、中断、拒否でプロセスを止めたもの
queue\status\      <job-id>.json  （注文を動かしてもここは動かない）
queue\confirm\     確認 JSON と .ok / .ng
queue\logs\        grok の出力（秘密は伏せ字）
queue\heartbeat.json
queue\STOP         これを置くと常駐が止まる
queue\resident.pid
resident\          インストールがコピーしたスクリプト
```

状態は `running`、`awaiting_confirm`、`done`、`denied`、`aborted`、`failed`、`rejected` です。まだ拾っていない注文を Linux 側から聞くと `missing` が返ります。

## PC への入れ方

ユーザー `hp` でログオンした Windows PowerShell 5.1 で実行します。`grok.exe` の既定は `C:\Users\hp\.grok\bin\grok.exe` です。違う場所なら `-GrokExe` を付けます。

```powershell
cd <このリポジトリ>\tools\pc-grokbuild-resident\pc
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Install-Resident.ps1 -StartNow
```

これで次が起きます。

- `C:\Users\hp\Documents\grokbuild` にキューと `resident\` を作る
- スクリプトを `resident\` にコピーする（タスクはコピー側を起動する）
- ログオン時のユーザー タスク `GrokBuildResident` を登録する（`LAPTOP-PL4TICBO\hp`、対話、制限付き）
- `-StartNow` で今すぐ起動する

登録し直すときも同じコマンドです。タスクだけ後から付けるなら、先に `-SkipTask` でフォルダだけ作り、あとから `-StartNow` なしでもう一度実行します。

起動し直す、止める、タスクを外す:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Start-Resident.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Stop-Resident.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Uninstall-Resident.ps1
```

停止は `queue\STOP` を書きます。動いている注文は中断（終了コード 30）してから常駐が終わります。アンインストールはタスクを消します。キューのファイルは残します。

動いているかは `queue\heartbeat.json` です。約 10 秒ごとに書き直します。inbox は約 1 秒ごとに見ます。

## 動き方

- 一度に本線は 1 件です。先着は `seq`（整数）がある注文が先、そのあとファイル名です。
- 全部が read-only の注文は、空いていれば読み取りレーンでもう 1 件同時に動きます。`lane: readonly` と書いた注文に不可逆ステップがあると、起動せず拒否します。
- 拾うと `running\` へ移し、`status\<id>.json` に id、状態、開始、終了、終了コード、pid を書きます。
- 常駐が落ちて `running\` に注文が残っていたら、再開しません。失敗（終了コード 40）にします。
- front matter に `sha256` があるとき、本文と合わなければ起動しません（終了コード 10）。

終了コード:

| コード | 意味 |
| --- | --- |
| 0 | 完了。拒否されて grok が自分で終わったときも 0 で、状態は `denied`、置き場は `done` |
| 10 | 注文の形か sha256 が違う。grok は起動しない |
| 12 | grok.exe が見つからない |
| 20 | 確認の待ちが時間切れ。プロセスを止めて `failed`（状態 `aborted`） |
| 21 | 拒否したのにプロセスが残ったので止めた。`failed`（状態 `denied`） |
| 30 | 停止要求 |
| 40 | 前回の実行中ファイルが残っていた。再開しない |

## 注文

UTF-8 です。UTF-16 は拒否します。`id` は英数字と `.` `_` `-` で、先頭は英数字、80 文字までです。同じ id は同時に置けません。パスワードやトークンは書かないでください。ログは `password=` や `token=` などを伏せますが、注文本文そのものは grok に渡すので伏せません。

```markdown
---
id: example-readonly
reasoning: xhigh
confirm_timeout_sec: 600
steps:
  - id: look
    mode: read-only
    summary: ページを開いてタイトルを写す。何も変えない。
---

本文。ログイン画面や 2FA が出たら、入力せず URL を報告して止まる。
```

- `reasoning` は `high` または `xhigh`。省略すると `xhigh`。
- `model` を書くなら `grok-4.7` だけ。別の値は拒否します。
- `fast: true` は拒否します。
- `confirm_timeout_sec` は 1 から 86400。省略は 600 秒。
- `seq` は並び用の整数です。
- ステップの `mode` は `read-only`（`readonly` / `read` も可）か `irreversible`（`write` も可）。
- 不可逆ステップには `kind` が必要です。`save` `send` `post` `delete` `publish` `payment` のいずれかです。

`sha256` は本文（閉じる `---` の直後の改行は本文に含めない）の SHA-256 小文字です。Linux の helper が押すときに付けます。手で付けるなら `linux/order_stamp.py` と同じ規則にしてください。

## 確認ゲート

常駐は注文の前に固定の英文前置きを足します。内容は次のとおりです。

- read-only はすぐにやる
- 不可逆の前に、必ず `queue\confirm\<job-id>.json` を 1 本書く。中身は何が変わるか（`job_id`、`step_id`、`kind`、`target_url`、`changes` の `field` / `before` / `after`）。この 1 ファイルで、その注文の不可逆ステップを全部書く
- `.ok` か `.ng` が出るまで待つ。時間切れなら常駐がプロセスを止める
- 秘密、パスワード、トークン、cookie を JSON にもログにも出さない
- ログイン、パスワード欄、2FA が出たら入力せず URL を報告して止まる
- 注文にない不可逆操作を足さない

`.ok` は、JSON が既にあるときだけ有効です。JSON なしの `.ok` では進みません。`.ng` は JSON がなくても拒否です。両方あるときは拒否が勝ちます。

## ひな型

`playbooks\` は文面の見本です。`id` を注文ごとに変えてから使います。ログインや 2FA が出たら止まる、と書いてあります。このリポジトリから YouTube や LINE へ投稿はしません。

- `line-oa-keyword-reply.md` … キーワード自動応答の確認と保存
- `line-oa-rich-menu.md` … リッチメニューの確認と保存
- `youtube-studio-schedule-pin.md` … 予約公開と、コメント固定。注文は2本に分ける
- `google-drive-sharing.md` … 共有相手やリンク範囲。オーナー譲渡はしない

`examples\` に、読み取りだけの注文と、確認が必要な注文があります。

## Linux から PC を操作する

`linux/grokbuild-remote.sh` は、PC で短い PowerShell を1回走らせます。接続そのものは作りません。呼び出し側が既にある遠隔シェルで、UTF-16LE の EncodedCommand を渡します。

```bash
grokbuild_pc() {
  ssh -o BatchMode=yes hp@LAPTOP-PL4TICBO \
    powershell.exe -NoProfile -NonInteractive -EncodedCommand "$1"
}
export -f grokbuild_pc
export GROKBUILD_RSH_FUNC=grokbuild_pc

linux/grokbuild-remote.sh push ./order.md
linux/grokbuild-remote.sh status <job-id>
linux/grokbuild-remote.sh wait <job-id> 600
linux/grokbuild-remote.sh approve <job-id>
linux/grokbuild-remote.sh deny <job-id>
linux/grokbuild-remote.sh pull <job-id> ./out
```

`show` を付けると、PC に送らず PowerShell の本文を表示します。PC 側では `GROKBUILD_ROOT` を空のままにします。ユーザーの `Documents\grokbuild` を使います。

- `push` は sha256 を付け、inbox のファイル名の先頭に UTC 時刻を付けます。1往復です。
- `status` は `queue\status\<id>.json` を1回読むだけです。無ければ `{"id":"...","state":"missing"}` です。
- `approve` は JSON が無い、または `.ng` が既にあると失敗します（終了 3）。
- `deny` は `.ok` が既にあると失敗します。JSON より前の拒否はできます。
- `pull` は status、注文、ログを取ります。ログは PC に保存されたバイトのままです。
- `wait` は 2 秒おきに status を見ます。`awaiting_confirm` のときは確認ファイルを読んで approve か deny するよう1回知らせます。時間切れは終了 4 です。

PC 上で同じことを手でやる一行です。`hp` で、`GROKBUILD_ROOT` は空です。

状態:

```powershell
powershell.exe -NoProfile -NonInteractive -Command "Get-Content -LiteralPath (Join-Path $env:USERPROFILE 'Documents\grokbuild\queue\status\<id>.json') -Raw"
```

許可（JSON があること）:

```powershell
powershell.exe -NoProfile -NonInteractive -Command "Set-Content -LiteralPath (Join-Path $env:USERPROFILE 'Documents\grokbuild\queue\confirm\<id>.ok') -Value 'ok' -Encoding ascii"
```

拒否:

```powershell
powershell.exe -NoProfile -NonInteractive -Command "Set-Content -LiteralPath (Join-Path $env:USERPROFILE 'Documents\grokbuild\queue\confirm\<id>.ng') -Value 'ng' -Encoding ascii"
```

心拍:

```powershell
powershell.exe -NoProfile -NonInteractive -Command "Get-Content -LiteralPath (Join-Path $env:USERPROFILE 'Documents\grokbuild\queue\heartbeat.json') -Raw"
```

## テスト

Linux では pwsh 7 で自己テストが動きます。キューの状態機械、sha256、レーン、確認の時間切れ、拒否、孤児の非再開、インストールのコピー、ラッパーの伏せ字を見ます。Pester が入っていれば `tests/QueueStateMachine.Tests.ps1` が同じ関数を呼びます。

```bash
cd tools/pc-grokbuild-resident
bash tests/run-all.sh
```

Windows のタスク登録と、本物の `grok.exe` 起動は、この Linux では実行していません。
