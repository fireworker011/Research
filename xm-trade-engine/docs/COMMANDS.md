# Commander commands

Issue「XM Trade — 日次レポート」へのコメントは次の1行のみ。大文字小文字は問わない。

| 行 | 意味 |
|---|---|
| `KILL_SWITCH: HALT` | 新規禁止。建玉を閉じる。日次損失ガードもこれを書く |
| `KILL_SWITCH: PAPER_ONLY` | 既定。Node はペーパーのみ。EA はデモなら新規可、リアル口座は新規不可 |
| `KILL_SWITCH: REDUCE_RISK` | リスク半分 |
| `KILL_SWITCH: RESUME` | リアル口座の新規を許可（他ゲートも必要） |

最新コメントが勝つ。`risk-guard` が書いた HALT より古い RESUME は上書きしない。
