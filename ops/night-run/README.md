# 夜間自動実行キット（HP OMEN / ユーザー hp）

時間: 毎晩 20:00〜04:00 JST。03:30 以降は新しいジョブを始めず、04:00 にこのスクリプトが記録した PID だけ止める。Windows はシャットダウンしない。

対象ランタイム: Windows PowerShell 5.1（`System32\WindowsPowerShell\v1.0\powershell.exe`）。

## 中身

| ファイル | 役目 |
|---|---|
| night-runner.ps1 | キューから優先順にジョブを取り、レーンごとに1本ずつ grok.exe を非表示で起動 |
| install-task.ps1 | タスクスケジューラ「GrokBuild夜間実行」を登録（毎日20:00＋ログオン時、スリープ解除可） |
| queue/1-video, 2-cg, 3-sakura | ジョブmd（1-video は種まき済み） |
| review-digest.md | 朝07:30の「OK待ち一覧」の形式案 |
| tests/ | Pester。`-DryRun` のモック |

## 直した点

- 時間外の終了で mutex を放していなかった。放棄された mutex は次の起動で例外になり、夜が始まらない。取得したら必ず解放し、放棄済みでも続行する。
- 窓の判定を JST（Windows は `Tokyo Standard Time`）に固定した。
- 04:00 ちょうどや、時間外にスクリプトが起動したときは、状態ファイルに残った PID だけを見る。プロセス名が記録と違い、または開始時刻が2分以上ずれていれば止めていない（PID の再利用）。
- `Stop-Computer` / `Restart-Computer` / `shutdown.exe` は使わない。タスクの実行時間上限は 8時間30分（20:00 起点で 04:30）で、切れるのはタスクのプロセスだけ。
- grok の引数は1本の文字列。`grok.exe --prompt-file "<job>" --always-approve --background-wait-timeout`。PS 5.1 の `Start-Process -ArgumentList` 配列は、空白を含むパスを壊す。
- `-DryRun` は grok.exe を起動しない。キューの移動と、上と同じ引数のログだけ行う。代替プロセスは `powershell.exe -NoProfile -Command exit 0`。
- 状態 JSON は 0件でも1件でも配列。起動に失敗したジョブは `_failed` へ戻す。
- `install-task.ps1` は、タイムゾーンが東京でなければ登録しない。`-Grok` をタスク引数へ渡せる。ユーザーは `ドメイン\hp`（ドメインが空ならコンピュータ名）。

## PCへの置き方（次にPCが点いたとき）

1. このフォルダを `C:\Users\hp\Documents\grokbuild\` にコピー（night-runner.ps1・install-task.ps1・queue\ を同じ階層に）。
2. 手順の本体を `C:\Users\hp\Documents\grokbuild\jobs\` に置く: imagine-new5-i2v-20261020.md、rebuild-kane-07〜10-20261019.md、rebuild-nemuri-03〜05-20261019.md、QC-5rules.md（箱: /home/box/video-unit/）。
3. セリフを `C:\Users\hp\Documents\grokbuild\lines\` に置く: kane-07〜10.md、nemuri-03〜05.md（すべて「台本係 確定」済み）。
4. `grok.exe` に PATH が通っているか確認。無ければ `.\install-task.ps1 -Grok "C:\...\grok.exe"`。
5. PC のタイムゾーンを東京（JST）にする。管理者 PowerShell で `.\install-task.ps1` を1回。電源オプションで「スリープ解除タイマーの許可」を有効に。
6. 試運転は 20:00〜04:00 JST の間に `.\night-runner.ps1 -DryRun -PollSec 1`。時間外は新規開始せず終了する。`-NowProvider` はテスト用。実キューに対して昼に使うと、ジョブファイルが `_running` に動く。

## ジョブmdの書き方（先頭20行に）

```
lane: chrome | edge | none
review: true
timeout_min: 60
imagine: true
requires: 22-queueB-kane-09.md
```

- `lane` が無い、または chrome / edge / none 以外なら none。
- `review: true` の成功は `_needs-review`。`false` なら `_done`。
- `requires` は、そのファイルが `_done` か `_needs-review` に入るまで待つ。
- 起動コマンド: `grok.exe --prompt-file <job> --always-approve --background-wait-timeout`（非表示。stdout/stderr は `out\<ジョブ名>\`）。

ジョブ本文の禁止事項と報告先は `ops/skills/pc-handoff/SKILL.md`。

## 動き

- 優先順 1-video → 2-cg → 3-sakura。フォルダ内はファイル名順。`TEMPLATE*` は無視。chrome / edge / none が空いていれば同時に走る。同じレーンは1本。
- 状態フォルダ: `queue\_running` → `_done` / `_needs-review` / `_failed`。前夜 `_running` に残ったものは失敗扱い。
- ログ: `out\night-runner-YYYYMMDD.log`。まとめ: `out\night-summary-YYYYMMDD.md`。YYYYMMDD は夜の始まり（20:00）の日付。
- 自分の PID は `out\night-state-YYYYMMDD.json`。止めるコマンドは `taskkill.exe /PID <記録したPID> /T /F` のみ。

## テスト

リポジトリのルートで:

```powershell
pwsh -NoProfile -Command "Invoke-ScriptAnalyzer -Path ops/night-run -Settings ops/night-run/PSScriptAnalyzerSettings.psd1 -Recurse"
pwsh -NoProfile -Command "Invoke-Pester -Path ops/night-run/tests -Output Detailed"
```

## 種まき済みジョブ（1-video）

- 10〜14: 作り直し5本の新素材 pet-n1 / konkatsu-n1 / pet-n2 / konkatsu-n2 / pet-n3（chrome, Imagine i2v, 各120分上限）
  - 参考: 10/21朝は約65分でカット2本。1晩で5本全部は終わらない見込み（残18カットで約9.75時間）。
- 20〜26: queueB フェーズB 仕上げ kane-07〜10・nemuri-03〜05（none、各60分上限）
- 90 / 91: 00_確認待ちへのアップ（edge。90は kane-09 後、91 は nemuri-05 後）
- 全ジョブに: QC5ルール、Keita +45%、画面に数字なし、PRは最後の2秒のみ、人物・ペットは i2v のみ、投稿禁止、パスワード禁止。
- 注意: 作り直し5本の「本編の仕上げ」（声・字幕）は素材が揃ってから台本係→別ジョブ。今夜分は素材生成まで。
