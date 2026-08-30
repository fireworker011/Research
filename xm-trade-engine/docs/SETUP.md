# XM Trade — 完全自動の載せ方

このファイルが **実装手順の正**。コードは PR をデフォルトへマージしたあとで載せる。

> 自動売買は口座資金を失う。利益は保証しない。デモが先。リスク上限（0.5% / 日次 2% / 0.10 lot）は上げない。
> Threads の schedule は戻さない。

## 何が自動か

| 役割 | 自動 | 人間 / Grok |
|---|---|---|
| Gold | アジアレンジ確定後、ロンドン 7–11 に **BuyStop と SellStop の両方**（OCO）。約定したら反対 pending を消す | `HALT` で全停止。`SKIP: GOLD` で今日だけ見送り |
| Majors（任意） | EURUSD 等 H1 の EMA クロス | 同じ `HALT` |
| 告知 | 約定で Issue に `xm-fill:`、決済で `xm-close:`。MT5 の Alert も鳴る | 読む。ENTRY は出すな |

Grok は予想もエントリーもやらない。止めるボタンだけ。

```
Grok / 人間  HALT or SKIP
        │
commander.json（デフォルトブランチ）
        │  30秒ごと WebRequest
XM MT5 デモ
  XMGoldSemi.mq5   GOLD M15  → 自動 OCO
  XMGrokEngine.mq5 EURUSD H1 → 自動 EMA（載せる場合）
        │  約定 / 決済
Issue「XM Trade — 日次レポート」へコメント
```

## 手順（この順）

### 1. PR をデフォルトへマージする

https://github.com/fireworker011/Research/pull/91  
先: `claude/setup-colab-comfyui-Eb9Lh`

`issue_comment` と日次レポートはデフォルトの YAML だけ動く。

マージ後、Actions で **XM Trade 日次レポート** を 1 回 Run する。  
Issue タイトルは正確に `XM Trade — 日次レポート`。番号を控える（EA の `NotifyIssueNumber` に使える）。

### 2. XM デモと MT5

Windows か Windows VPS。GitHub 上では動かない。銘柄は `GOLD` または `XAUUSD`。

### 3. PAT を作る（private リポジトリ）

GitHub → Settings → Developer settings → Fine-grained PAT（または classic `repo`）。

必要な権限:

- Contents: Read（`commander.json` を読む）
- Issues: Read and Write（`xm-fill` / `xm-close` を書く）

トークンは Git にコミットしない。

### 4. WebRequest を許可する

MT5 → ツール → オプション → EA:

- `https://api.github.com`
- Slack も使うなら Incoming Webhook のホスト（例 `https://hooks.slack.com`）

### 5. Gold EA を載せる（必須）

1. `xm-trade-engine/ea/` の `XMGoldSemi.mq5` と `xm_notify.mqh` を同じフォルダに入れる。
2. MetaEditor で `XMGoldSemi.mq5` をコンパイルする。
3. **GOLD（または XAUUSD）の M15** に付ける。AutoTrading ON。
4. 入力:

| 入力 | 値 |
|---|---|
| `CommanderURL` | `https://api.github.com/repos/fireworker011/Research/contents/xm-trade-engine/output/state/commander.json?ref=claude/setup-colab-comfyui-Eb9Lh` |
| `CommanderAuthHeader` | `Authorization: token ghp_xxxxxxxx` |
| `GitHubRepo` | `fireworker011/Research` |
| `NotifyIssueNumber` | 追跡 Issue の番号。空なら `commander.json` の `issue_number`（日次レポート実行後に入る） |
| `NotifyEnabled` | true |
| `AutoOco` | true（完全自動） |
| `SlackWebhookURL` | 使うなら Incoming Webhook。使わないなら空 |

PR ブランチの URL は使わない。同じ銘柄に他の EA を載せない。

チャート左下に `cmd=` `auto=yes` `notify_issue=` が出れば通信は生きている。

### 6. Majors EA（任意）

EURUSD / GBPUSD / USDJPY の **H1** に `XMGrokEngine.mq5`（同じ `xm_notify.mqh`）。  
Commander / Notify の入力は Gold と同じ。Gold と **別チャート**。

### 7. Grok Bot

`xm-trade-engine/docs/grok-bots/G_xm_trade.txt` **だけ**を貼る。月100万 dump と混ぜない。

Grok が出してよい行:

```
KILL_SWITCH: HALT
KILL_SWITCH: PAPER_ONLY
KILL_SWITCH: REDUCE_RISK
SKIP: GOLD
```

`ENTRY: GOLD BUY` は出さない。完全自動。`ARM: GOLD` も不要（IDLE で両方置く）。

### 8. デモで1サイクル

ブローカーサーバー時刻（XM はだいたい UTC+2）。

| 時刻 | 動き |
|---|---|
| 0:00–7:00 | アジアレンジ |
| 7:00 以降 | ロック。Issue に `gold-notice:`（指令ではない） |
| 7:00–11:00 | **自動で** BuyStop と SellStop |
| 片方約定 | 反対 pending 削除。Issue に `xm-fill:` と Alert |
| SL/TP/金曜クローズ等 | Issue に `xm-close:` と Alert |
| 11:00 | 未約定 pending 取消 |

月初金曜は休む。実口座はデモで fill/close の告知を見てから。実口座の新規は `KILL_SWITCH: RESUME` が必要。

## 動かないとき

| 症状 | 見る場所 |
|---|---|
| pending が付かない | AutoTrading。M15 か。サーバー 7–11 か。`HALT` / `SKIP` か。リアルなら RESUME。レンジが ATR 比の外ならログ `asia skip frac=` |
| 告知が来ない | PAT に Issues Write。`NotifyIssueNumber` か `issue_number`。WebRequest に `api.github.com`。Experts ログ `notify github HTTP` |
| コメントが司令塔に食われる | 本文先頭が `xm-fill:` / `xm-close:` なら無視される。壊さない |
| `commander HTTP 404` | private なのに raw URL。Contents API にする |
