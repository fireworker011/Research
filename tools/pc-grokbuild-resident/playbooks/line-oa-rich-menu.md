# LINE公式アカウント リッチメニューを保存する

ひな型です。`id` を注文ごとに変えます。パスワードは書きません。

ログイン画面か 2FA が出たら、操作せず URL を報告して止まります。

すでにユーザーへ公開中のメニューを保存すると、表示が変わります。確認 JSON に「公開中か」を書きます。オーナー権限の譲渡はしません。

## 止める条件

- ログイン画面、パスワード欄、2FA
- 別アカウントが開いている
- 画面が「公開」だけを求め、保存内容が確認 JSON と違う
- メニューを削除するボタンしかない（このひな型は削除しない）

## コピーして使う注文

```order
---
id: line-richmenu-template
reasoning: xhigh
confirm_timeout_sec: 600
steps:
  - id: read-menu
    mode: read-only
    summary: 対象アカウントのリッチメニュー一覧と、指定メニューの中身を読む
  - id: save-menu
    mode: irreversible
    kind: save
    summary: 指定したリッチメニューの内容だけを保存する
---

対象アカウント: {{ACCOUNT}}
管理画面: https://manager.line.biz/
メニュー名: {{MENU_NAME}}

読むもの: いまのエリア、画像、アクション、公開中かどうか。

保存するもの: {{WHAT_CHANGES}}

削除はしない。他のメニューは開かない。
ログイン画面か 2FA が出たら、操作せず URL を報告して止まる。
保存の前に confirm JSON を書き、公開中かどうかと変更差分を入れて、.ok まで待つ。
```
