# XM Trade Engine — Cursor / Grok Bot 自動トレード

XM の MT4/MT5 口座向けに、**エントリーはルール、司令塔は停止判断**で回す自動売買。
Affiliate Engine と同じく GitHub 上で保守し、Grok Bot が日次レポートを読んで 1 手出す。

> **最初に正直な前提を。** 自動売買は口座資金を失う。このリポジトリは利益を保証しない。
> 数字はペーパー帳簿か、接続した口座の実測だけを書く。未確認は「未確認」。
> LLM（Grok / Cursor）に「今 EURUSD を買え」と選ばせない。それは幻覚で破産する。

## なぜ GitHub Actions だけでは XM を回せないか

XM に公式の REST/FIX API はない。自動売買の正は **MetaTrader の EA** である。
GitHub の cron は 1〜4 時間遅延するのが常態なので、H1 の発注クロックには使えない。

```
Grok Bot（司令塔）
  Issue「XM Trade — 日次レポート」を読む
  1手は KILL_SWITCH または SKIP: GOLD
  エントリーは出さない。xm-fill / xm-close は告知
        │
Cursor（参謀）          GitHub Actions（ペーパー + 報告）
  戦略・リスク・EA保守     価格取得 → 仮想帳簿 → commander.json 更新
        │                         │
        └──────────┬──────────────┘
                   ▼
            XM MT5 デモ / 実口座
            ea/XMGrokEngine.mq5（majors H1 完全自動）
            ea/XMGoldSemi.mq5（GOLD M15 完全自動 OCO）
            約定・決済で Issue へ xm-fill / xm-close
```

| 役割 | やる | やらない |
|---|---|---|
| **EA（実時間）** | XM への発注・SL/TP・日次損失で全決済・約定/決済告知 | GitHub の遅延シグナルでエントリー |
| **Node tick** | ペーパー追跡・シグナル記録・日次損失で HALT 書き込み | 実口座の損益を捏造 |
| **Grok Bot** | 停止判断。fill/close を読む | 方向予想、ENTRY、ロット変更 |
| **Cursor** | コードと不変条件 | リスク上限を上げる、マーチンゲールを足す |

## 戦略（日付でも乱数でもなく、閉じた足だけ）

`config/strategy.json` が正。EA の input を同じ値に揃える。

- 対象: EURUSD / GBPUSD / USDJPY（H1）
- トレンド: EMA20 と EMA50
- エントリー: 終値が EMA20 をトレンド方向へクロス、RSI(14) が極端域でない
- 損切 1.5×ATR(14)、利確 2.0×ATR(14)
- セッション: 07:00–21:00 UTC、金曜 18:00 UTC 以降は新規禁止＋決済
- 禁止: マーチンゲール、ナンピン、グリッド。LLM に majors / Gold のエントリーを選ばせない

## Gold 完全自動（巷の Gold EA から取るもの / 捨てるもの）

巷の XAUUSD EA で **使えるのはアジアレンジ → ロンドン OCO の骨格だけ**。99%勝率・グリッド・ナンピンは捨てる。

取るもの:

1. アジア時間にレンジを測る（ブローカーサーバー 0–7。UTC ではない）
2. ロンドン開始（サーバー 7–11）に **BuyStop と SellStop の両方**を自動で置く
3. スプレッドが広い日・月初金曜（NFP 隣接）は休む
4. 約定後は SL/TP と反対 pending の取消だけ自動
5. 約定と決済を Issue と Alert で告知する

捨てるもの: マーチンゲール、ナンピン、グリッド、Telegram シグナルのコピー、Grok に方向を選ばせること。対応表と載せ方は [`docs/SETUP.md`](docs/SETUP.md)。

実装:

- Node: `src/gold-breakout.js`（ペーパー。`entry_operator: auto`）
- 実時間: `ea/XMGoldSemi.mq5` + `ea/xm_notify.mqh` を **GOLD M15**
- リスクは majors と同じ 0.5% / 日次 2% / 最大 0.10 lot。上げない

XM のゴールド銘柄はエンティティにより `GOLD` / `XAUUSD`。チャートの銘柄に EA を付ける。

## リスク（`config/risk.json`）

| 項目 | 既定 |
|---|---|
| 1 トレードリスク | 残高の 0.5% |
| 日次最大損失 | 2% で HALT（新規停止＋決済） |
| 同時建玉 | 2 |
| 最大ロット | 0.10 |
| 実発注 | `runtime.live_enabled` が false のあいだ MetaApi は呼ばない |

実口座の Node 経由発注（MetaApi）は次を全部満たしたときだけ:

1. `config/runtime.json` の `live_enabled: true`
2. commander が `RESUME`
3. 環境変数 `XM_LIVE_CONFIRM=I_UNDERSTAND_THE_RISK`
4. `METAAPI_TOKEN` と `METAAPI_ACCOUNT_ID`

EA 側はこれと独立に、**リアル口座では commander が RESUME のときだけ新規**。デモは HALT 以外で動く。Gold 完全自動も同じ。

## セットアップ（デモが先）

載せ方の正は [`docs/SETUP.md`](docs/SETUP.md)。要約:

1. この変更を **デフォルトブランチへマージ**する。
2. XM **デモ** MT5 で `XMGoldSemi.mq5` と `xm_notify.mqh` を **GOLD M15** に載せる。AutoTrading ON。
3. WebRequest に `api.github.com` を許可。PAT は Contents Read + Issues Write。
4. `CommanderURL` はデフォルトブランチの Contents API。`NotifyIssueNumber` に追跡 Issue 番号。
5. `docs/grok-bots/G_xm_trade.txt` を Grok Bot に貼る。ENTRY は出さない。

ローカル確認:

```bash
cd xm-trade-engine
node --check src/tick.js
node src/self-test.js
node src/tick.js --dry-run
```

Majors は `ea/XMGrokEngine.mq5` を EURUSD H1 に別チャートで載せる。Gold と混ぜない。
実口座は、デモでロック → 自動 pending → `xm-fill` / `xm-close` を確認したあと。リスク上限は上げない。

## 運用コマンド（Grok Bot / 人間）

完全自動なので、止めるときだけ Issue に **1 行**。

```
KILL_SWITCH: HALT
KILL_SWITCH: PAPER_ONLY
KILL_SWITCH: REDUCE_RISK
KILL_SWITCH: RESUME
SKIP: GOLD
```

`xm-fill:` / `xm-close:` は EA の告知。指令ではない。`RESUME` は利益保証ではない。

## ファイル

```
xm-trade-engine/
├── config/strategy.json     # 戦略（決定論）
├── config/risk.json         # リスク上限
├── config/gold.json         # アジア/ロンドンはブローカー時刻。offset はペーパー用
├── docs/SETUP.md            # 完全自動の載せ方
├── src/gold-breakout.js
├── ea/xm_notify.mqh         # 約定・決済の Issue / Slack 告知
├── ea/XMGrokEngine.mq5      # majors H1
├── ea/XMGoldSemi.mq5        # GOLD M15 完全自動 OCO
└── docs/grok-bots/G_xm_trade.txt
```

秘密情報（口座番号、MT パスワード、MetaApi トークン）は Git に置かない。GitHub Secrets のみ。
