# YouTube Studio 予約公開とコメント固定

ふたつの注文に分けてあります。混ぜて1本にしないでください。`id` は毎回変えます。

このひな型は投稿そのものではありません。PC の Grok が、confirm の `.ok` のあとだけ操作します。

ログイン画面か 2FA が出たら、操作せず URL を報告して止まります。再生数や登録者数は作りません。

## 止める条件

- ログイン画面、パスワード欄、2FA
- チャンネルが {{CHANNEL}} でない
- 対象の動画が見つからない
- 確認 JSON に書いていない動画やコメントを触りそうなとき

## 予約公開

```order
---
id: youtube-schedule-template
reasoning: xhigh
confirm_timeout_sec: 600
steps:
  - id: read-visibility
    mode: read-only
    summary: YouTube Studio で対象動画の公開設定を読む
  - id: set-schedule
    mode: irreversible
    kind: publish
    summary: 対象動画の公開日時だけを予約する
---

チャンネル: {{CHANNEL}}
Studio: https://studio.youtube.com/
動画: {{VIDEO_TITLE_OR_URL}}
予約日時: {{WHEN}}
公開範囲: {{VISIBILITY}}

いまの公開状態を先に読む。日時以外（タイトル、説明、終了画面、広告）は変えない。
ログイン画面か 2FA が出たら、操作せず URL を報告して止まる。
予約保存の前に confirm JSON へ、動画、変更前、変更後の日時を書いて .ok を待つ。
```

## コメントを固定する

```order
---
id: youtube-pin-template
reasoning: xhigh
confirm_timeout_sec: 600
steps:
  - id: read-comments
    mode: read-only
    summary: 対象動画のコメント欄を開き、固定したいコメントを見つける
  - id: pin-comment
    mode: irreversible
    kind: post
    summary: 指定したコメントだけを固定する
---

チャンネル: {{CHANNEL}}
Studio: https://studio.youtube.com/
動画: {{VIDEO_TITLE_OR_URL}}
固定するコメント: {{COMMENT_TEXT}}

新しいコメントは書かない。他のコメントの削除やハートはしない。
ログイン画面か 2FA が出たら、操作せず URL を報告して止まる。
固定の前に confirm JSON へ、動画 URL とコメント本文を書いて .ok を待つ。
```
