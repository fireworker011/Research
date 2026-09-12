# 指示マシーン（正）

日常の入口は dump **1ファイル**だけ。更新日時で他を選ぶな。結合するな。
仕分けは `dump/README.md`。Cursor の台帳は `HQ_ROSTER.md`（Bot は開けるな）。

| 誰 | やる | やらない |
|---|---|---|
| **ナオミチ** | 外部サイトのクリック、初回ログイン、重要判断。席は1回 | 日常チャット、時計進行、コード、ログイン確認のループ、毎晩の1語 |
| **Grok Bot（1 clone）** | 普通のやり取り、日次1手、XM の停止判断、dump を1つ開く | コード、外部ログイン、Cursor を常時起こす、dump を結合、1語チェーンを自分で選ぶ、CW 司令塔を開く |
| **Cursor（総司令1体）** | 仕組み・台帳・統括命令・カレンダー。他 Cursor の本線マージを許可/禁止する。起こされた日はゲート照合と `TODAY.md` を1回更新して止まる | 87体の並列司令塔、日常、常時の時計、dump 貼り付け、ログイン確認ループ |

## BOT が開くファイル

| いつ | ファイル |
|---|---|
| **毎日の入口（clone に一度）** | `dump/G_hq_boot.txt` |
| **指示役（GitHub）** | 07:22 JST と Issue コメントと conversions.csv。**既定は席1回** `G_hq_human_sitting.txt`。`overlay-filled` ≥ 1 なら計測。確定円が 100万なら freeze。`AFFI: STOP` のときだけ XM |
| overlay が空のとき | `dump/G_hq_human_sitting.txt` |
| overlay が1以上のとき | `dump/G_hq_a8_csv.txt` |
| 仕組みが足りないとき | 下の「参謀へ」 |

`G_hq_cw_remain.txt` と `G_hq_cw_n10.txt` は **駐車**。開けるな。1語 dump も Bot は開くな。
CW 司令塔 PR #122 を instruct / boot にマージするな。

日次の数字は指示役の `overlay-filled:` / `approved-yen:` / `hq-gate:`。ゲート表は `HQ_CALENDAR.md`（Bot は開けるな）。

`HUMAN.md` は貼るな。Threads cron は戻すな。数字は invent するな。アフィ URL をチャットに出すな。

## 参謀へ（Cursor を起こしてよい唯一の形）

日常の欠測や「ログインしたか」では起こすな。仕組みの穴だけ、1行:

```
参謀へ: [足りない仕組みを1つ。外部クリックを要求するな]
```

Cursor はそれを環境にして止まる。常時稼働しない。新しい司令塔エージェントを増やさない。
