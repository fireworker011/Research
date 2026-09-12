# 指示マシーン（正）

日常の入口は dump **1ファイル**だけ。更新日時で他を選ぶな。結合するな。

| 誰 | やる | やらない |
|---|---|---|
| **ナオミチ** | 外部サイトのクリック、初回ログイン、重要判断。席は1回 | 日常チャット、時計進行、コード、ログイン確認のループ、毎晩の1語 |
| **Grok Bot** | 普通のやり取り、日次1手、XM の停止判断、dump を1つ開く | コード、外部ログイン、Cursor を常時起こす、dump を結合、1語チェーンを自分で選ぶ |
| **Cursor** | 仕組み・環境・リサーチ成果物・申請文の 100% 下書き。起こされた日は `HQ_CALENDAR.md` の今日のゲートを1回照合して `output/sprint/TODAY.md` を更新し止まる | 日常、常時の時計、dump 貼り付け、ログイン確認ループ |

## BOT が開くファイル

| いつ | ファイル |
|---|---|
| **毎日の入口（clone に一度）** | `dump/G_hq_boot.txt` |
| **指示役（GitHub）** | デフォルトへマージで初回。以後 07:22 JST と、Issue `Grok Bot — 指示` への人間コメントと `conversions.csv` 更新で `hq-instruct:`。**既定は席1回** `G_hq_human_sitting.txt`（GO 不要）。`overlay-filled` ≥ 1 なら計測 `G_hq_a8_csv.txt`。確定円が 100万なら `hq-gate: freeze`。`AFFI: STOP` のときだけ XM。コメントに `overlay-filled:`（鍵名だけ。URLなし）と `approved-yen:`（CSV 合計。ファイルが無ければ `unknown`。0 を invent しない）と `hq-gate:`。同じジョブで `Affiliate — 確定円` も空で立てる |
| FX の日次（STOP のとき instruct / boot から開く） | `xm-trade-engine/docs/grok-bots/G_xm_trade.txt` |
| overlay が空のとき | `dump/G_hq_human_sitting.txt`。教育 Threads を先。1語は返すな。完了しても overlay が空なら同じファイル |
| overlay が1以上のとき | `dump/G_hq_a8_csv.txt`。踏める面は既にある。毎日の仕事は画面を見た円だけ |
| 仕組みが足りないとき（Cursor へ1行） | 下の「参謀へ」 |

`G_hq_cw_remain.txt` と `G_hq_cw_n10.txt` は **駐車**。引用1手は替えるな。開けるな。人間介入が多すぎて日常にしない。

日次の進捗数字は指示役（07:22 JST）の `overlay-filled:` と `approved-yen:` と `hq-gate:`。9/30 までのゲート表は `HQ_CALENDAR.md`（Bot は開けるな。Cursor が起こされた日だけ照合）。

`HUMAN.md` は貼るな。Threads cron は戻すな。数字は invent するな。アフィ URL をチャットに出すな。

## 参謀へ（Cursor を起こしてよい唯一の形）

日常の欠測や「ログインしたか」では起こすな。仕組みの穴だけ、1行:

```
参謀へ: [足りない仕組みを1つ。外部クリックを要求するな]
```

Cursor はそれを環境にして止まる。常時稼働しない。
