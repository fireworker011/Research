# Commander commands

Issue「XM Trade — 日次レポート」へのコメントは次の1行のみ。大文字小文字は問わない。

完全自動なので、Grok の既定は **何も書かない**。止めるときだけ書く。

| 行 | 意味 |
|---|---|
| `KILL_SWITCH: HALT` | 新規禁止。建玉を閉じる。日次損失ガードもこれを書く |
| `KILL_SWITCH: PAPER_ONLY` | 既定。Node はペーパーのみ。EA はデモなら新規可、リアル口座は新規不可 |
| `KILL_SWITCH: REDUCE_RISK` | リスク半分 |
| `KILL_SWITCH: RESUME` | リアル口座の新規を許可（他ゲートも必要） |
| `SKIP: GOLD` | 今日の Gold pending を置かない。未約定 pending は取消。建玉は閉じない |
| `ARM: GOLD` | 不要（IDLE で OCO 両方）。人間の明示用に残してある |
| `ENTRY: GOLD BUY` / `SELL` | 片側だけに上書き。完全自動では使わない |

`xm-fill:` と `xm-close:` と `gold-notice:` は EA / Actions の告知。指令ではない。
`gold_arm` は日付付き（UTC）。翌日は `IDLE` に戻り、また自動 OCO。
載せ方は `SETUP.md`。
