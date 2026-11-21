# Google ドライブの共有を変える

ひな型です。`id` を注文ごとに変えます。パスワードは書きません。

ログイン画面か 2FA が出たら、操作せず URL を報告して止まります。オーナーの譲渡はしません。譲渡のボタンしかない画面なら止まります。

## 止める条件

- ログイン画面、パスワード欄、2FA
- 開いたファイルが {{FILE_NAME}} でない
- オーナー譲渡、または確認 JSON にないメールアドレス
- リンクを「インターネット上の全員」に広げる操作が、注文に書いていない

## 人を足す、または役割を変える

```order
---
id: drive-share-template
reasoning: xhigh
confirm_timeout_sec: 600
steps:
  - id: read-sharing
    mode: read-only
    summary: 対象ファイルの共有一覧とリンク設定を読む
  - id: change-sharing
    mode: irreversible
    kind: save
    summary: 指定した相手の共有役割だけを変える
---

ファイル: {{FILE_NAME}}
URL: {{FILE_URL}}
相手: {{EMAIL}}
変更前の役割: {{ROLE_BEFORE}}
変更後の役割: {{ROLE_AFTER}}

共有画面: https://drive.google.com/

先にいまの共有相手と役割を読む。書いていない人は消さない。オーナーは変えない。
ログイン画面か 2FA が出たら、操作せず URL を報告して止まる。
保存の前に confirm JSON へ、ファイル URL、メール、変更前、変更後を書いて .ok を待つ。
```

## リンクの公開範囲を変える

範囲を広げる操作です。`kind` は publish にします。狭めるだけのときは save の注文を別に作ります。

```order
---
id: drive-link-template
reasoning: xhigh
confirm_timeout_sec: 600
steps:
  - id: read-link
    mode: read-only
    summary: 対象ファイルのリンク共有の現在値を読む
  - id: change-link
    mode: irreversible
    kind: publish
    summary: リンクを知っている人の公開範囲だけを変える
---

ファイル: {{FILE_NAME}}
URL: {{FILE_URL}}
変更前: {{LINK_BEFORE}}
変更後: {{LINK_AFTER}}

オーナー譲渡はしない。他のファイルの共有は開かない。
ログイン画面か 2FA が出たら、操作せず URL を報告して止まる。
変更の前に confirm JSON へ、ファイル URL と変更前後を書いて .ok を待つ。
```
