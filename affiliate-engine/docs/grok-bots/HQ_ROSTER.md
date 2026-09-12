# HQ 台帳（Cursor だけ。Grok Bot は開けるな）

目標は変えない。期間 2026-08-26〜2026-09-30。確定 ¥1,000,000。
実測円は `approved_yen`。無いあいだは ¥0。

棚卸し日: 2026-09-12 JST。Cloud Agent 87 体を読んだ。
本線の Cursor は **総司令 1体だけ**: [１００万円売り上げ自動化](https://cursor.com/agents/bc-9e6f3a09-eff4-42b2-adbe-9caa1758a971)。
統括命令: `HQ_COMMAND.md`。他の Cursor を「司令塔」として起こすな。Grok Bot の clone も1つ（`dump/G_hq_boot.txt`）。

## Cursor の最大化（台数ではなく権限）

Cursor が持つのは仕組みの全部: dump 選択、円カレンダー、この台帳、PR が本線を壊さないこと。
日常チャット・1語・ログイン確認・CW応募・XM ENTRY は Cursor の仕事ではない。
最大化 = 本線の穴を潰して止まる。87体を並列にしない。

## KEEP（動かす）

| 何か | 役割 | 備考 |
|---|---|---|
| Cursor 総司令 1体 | 上流と他 Cursor の統括。起こされた日は命令・台帳・TODAY | 上の URL |
| Grok Bot 1 clone | `G_hq_boot.txt` → Issue 110 の `hq-instruct:` 1ファイル | 毎日貼り直すな |
| 指示役 07:22 JST | overlay / 円で sitting か計測かを書く | 投稿しない |
| `G_hq_human_sitting.txt` | 人間の席1回 | overlay 空のあいだ |
| `G_hq_a8_csv.txt` | 見た円だけ | overlay ≥ 1 |
| `G_xm_trade.txt` | STOP のときだけ | ENTRY は出すな。ペーパー≠残高 |
| video-judge / token refresh | 判定とトークン延命 | 投稿しない |
| ナオミチの席 | A8・プロフィール・Secret | URL はチャットに貼るな |

## PARK（エンジンは残す。日常にしない。マージで本線を上書きするな）

| 何か | 実体 | なぜ駐車 |
|---|---|---|
| **CW 司令塔** | [bc-01a094be…](https://cursor.com/agents/bc-01a094be-1bfa-7e7b-bebc-da2599e7c1fb) / draft [#122](https://github.com/fireworker011/Research/pull/122) | 自動応募はしない設計だが、boot / instruct / HQ_100MAN に CW レーンを差す。**#115 の席マシンを潰す。マージするな** |
| **XM 司令塔** | [bc-01a05178…](https://cursor.com/agents/bc-01a05178-ea89-7fc3-9ddc-6183a41ae2c5) / [#94](https://github.com/fireworker011/Research/pull/94) | ペーパーは Issue 93 で足りる。VPS 実発注と ENTRY 再導入に戻りやすい。iPhone 手順は衝突中 |
| remain / n10 dump | `G_hq_cw_remain.txt` / `G_hq_cw_n10.txt` | 引用1手は替えるな。開けるな |
| 1語 dump 一式 | `G_hq_sns_next.txt` ほか | 席1回に畳んだ。affi-step のテスト用にファイルは残す。Bot は開くな |
| H3 / MiniMax | #50 派生、JPEG アップローダ多数 | 映像。円の席ではない |
| 動画投稿エンジン | #104 ほか | cron 停止中に投稿面を増やさない |
| FANZA / 同人 / サクラIG | #49 #51 #53 | Threads 9アカに出さない。100万本線に足すな |
| ペット試験・キャットフード | #114 #90 | 垂直が違う |
| 古い HQ_APPLY / 100万ループ | #75 #74 #76 #70 | #115 が後から正 |

## KILL / Archive（ダッシュボードで畳んでよい。二度と起こすな）

ログイン確認・overlay 再読・A8/CW/GitHub の「入ってるか」ループ（内部エージェントが十数体）。
H3 の JPEG アップロード専用（内部が数十体）。本線の円を動かさない。
名前が「Check A8 yen if logged in」「Recheck GitHub A8 CW login」のものは全てここ。

## Grok Bot が開いてよいファイル

`dump/README.md` の LIVE だけ。更新日時で他を選ぶな。結合するな。
このファイルと `HQ_CALENDAR.md` は開けるな。

## 起こされた日の Cursor

1. Issue 110 の `hq-gate:` / overlay / 円を読む
2. `HQ_COMMAND.md` の禁止マージを守る（とくに #122）
3. `output/sprint/TODAY.md` を1回更新して止まる
