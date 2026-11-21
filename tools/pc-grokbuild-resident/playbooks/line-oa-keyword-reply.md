# LINE公式アカウント キーワード応答を直す

ひな型です。`id` を注文ごとに変えてから inbox に置きます。パスワードは書きません。

ログイン画面、パスワード欄、2FA（SMS・認証アプリ・確認コード）が出たら、その場で止まります。URL を報告して、コードは打ちません。

## 止める条件

- ログイン画面が出た
- 2FA が出た
- 保存ボタンを押す前に、確認 JSON と違う内容になりそうなとき
- 別の公式アカウントが開いているとき

## コピーして使う注文

```order
---
id: line-keyword-template
reasoning: xhigh
confirm_timeout_sec: 600
steps:
  - id: open-keywords
    mode: read-only
    summary: LINE Official Account Manager を開き、対象アカウントのキーワード応答一覧を読む
  - id: save-keyword
    mode: irreversible
    kind: save
    summary: 指定したキーワード応答だけを保存する
---

対象アカウント: {{ACCOUNT}}
管理画面: https://manager.line.biz/

読むもの: いま登録されているキーワードと応答文。変更しない。

保存するもの:
- キーワード: {{KEYWORD}}
- 応答文: {{RESPONSE}}

上の1件以外は触らない。公開範囲やリッチメニューは変えない。
ログイン画面か 2FA が出たら、操作せず URL を報告して止まる。
保存の前に confirm JSON を書き、.ok まで待ってから保存する。
```
