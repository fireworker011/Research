# Commander commands

Issue「XM Trade — 日次レポート」へのコメントは次の1行のみ。大文字小文字は問わない。

| 行 | 意味 |
|---|---|
| `KILL_SWITCH: HALT` | 新規禁止。建玉を閉じる。日次損失ガードもこれを書く |
| `KILL_SWITCH: PAPER_ONLY` | 既定。Node はペーパーのみ。EA はデモなら新規可、リアル口座は新規不可 |
| `KILL_SWITCH: REDUCE_RISK` | リスク半分 |
| `KILL_SWITCH: RESUME` | リアル口座の新規を許可（他ゲートも必要） |
| `ARM: GOLD` | 両方の pending（OCO）。人間が明示したときだけ。Grok の既定ではない |
| `ENTRY: GOLD BUY` | Grok のエントリー。BuyStop だけ置く。suggested_side が BUY のとき |
| `ENTRY: GOLD SELL` | Grok のエントリー。SellStop だけ置く。suggested_side が SELL のとき |
| `SKIP: GOLD` | 今日の Gold を見送り |

Grok は `suggested_side` に従う。NONE なら SKIP。価格・ロット・SL をコメントに書いてはいけない。
`gold_arm` は日付付き。翌日は `IDLE`。
Issue コメントは `xm_trade_commander.yml` が commander.json へ即時写す（cron を待たない）。HALT 中は EA が発注しない。
