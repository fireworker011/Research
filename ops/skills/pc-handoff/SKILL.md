---
name: pc-handoff
description: PCのGrok Buildへ渡すジョブmdの型。lane / review / timeout_min、禁止事項、報告先 out\。
---

# PCへ渡すジョブ

PC の Grok Build に渡す指示は、1ジョブ1ファイルの markdown だけにする。口頭やチャットの追記で補わない。置き場所は `C:\Users\hp\Documents\grokbuild\queue\` の `1-video`、`2-cg`、`3-sakura` のいずれか。ファイル名はフォルダをまたいで重複させない。`TEMPLATE` で始まるファイルは見本で、実行されない。

## 先頭20行

ランナーは先頭20行しか読まない。次の3行は必須。値のうしろにコメントを書くなら ` # ` で離す。

```
lane: chrome
review: true
timeout_min: 60
```

- `lane` は `chrome`、`edge`、`none` のいずれか。同じレーンは同時に1本。ブラウザを使わない作業は `none`。
- `review: true` は、成功しても `_needs-review` に置き、ナオミチの確認を待つ。確認が要らないときだけ `false`（`_done` へ進む）。
- `timeout_min` は分。超えたら、そのジョブとして起動した PID だけを止めて失敗にする。

任意:

```
imagine: true
requires: 22-queueB-kane-09.md
```

- `imagine: true` かつ終了コードが 0 でないとき、まとめに Imagine異常と書く。
- `requires` は、そのファイル名が `_done` か `_needs-review` に入るまで待たせる。カンマ区切りで複数可。

## 本文に必ず書く禁止

- 投稿しない。予約、共有、送信、公開もしない。
- パスワードを入力しない。確認コードも打たない。
- X を操作しない。
- Windows をシャットダウンしない。再起動もしない。自分以外の grok.exe、ブラウザ、powershell を止めない。

## 報告先

成果と途中経過は `out\` に書く。夜のランナー配下なら `C:\Users\hp\Documents\grokbuild\out\<このファイル名>\REPORT.md`。人の操作が要る画面は、同じフォルダに `BLOCKED.png` を置いて終了する。ログインが切れていても、パスワードは打たない。

起動はランナーが行う。コマンドは次の形だけ。`--background-wait-timeout` に値がないと grok.exe はエラーで落ちる。

```
grok.exe --prompt-file <ジョブmdのフルパス> --always-approve --background-wait-timeout 3600
```

## 渡す前

1. `lane` / `review` / `timeout_min` が先頭20行にある。
2. 禁止4項と、報告先 `out\` が本文にある。
3. 入力（手順書、セリフ、参照画像）と出力（mp4、QC表、Eagle、Drive）のパスが、そのジョブの本文に書いてある。書いていないパスは作らせない。
4. アカウントを開くジョブなら、先に `account-registry` で行とプロファイルが一致していることを確認する。場所が不明なら、そのジョブはキューに置かない。
