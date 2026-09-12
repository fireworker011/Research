# Commander commands

Issue「CW — 司令塔」へのコメントは次の1行のみ。大文字小文字は問わない。

完全自動（キュー判定）なので、Grok の既定は **何も書かない**。止めるときだけ書く。

| 行 | 誰 | 意味 |
|---|---|---|
| `CW: HALT` | Grok | 新規 qualification 禁止。下書きも増やすな |
| `CW: PAPER_ONLY` | Grok / 人間 | 既定。キューと下書きだけ。応募送信を Bot がするな |
| `CW: SENT <id>` | 人間 | その仕事へ応募を送った |
| `CW: CONTRACT <id>` | 人間 | 契約した |
| `CW: REJECT <id>` | 人間 | 見送り・不採用・募集終了 |

`cw-desk:` は Actions の告知。指令ではない。返信するな。

`CW: RESUME` は **無い**。公式応募 API が無いのでライブ自動送信のゲートを作らない。

指示レーン（Issue `Grok Bot — 指示`）:

| 行 | 意味 |
|---|---|
| `CW: GO` | dump を `G_cw.txt` にする |
| `CW: STOP` | XM に戻す |

remain / n10 はコマンドではない。開けるな。
