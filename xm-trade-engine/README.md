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
  1手は KILL_SWITCH または Gold の ENTRY/SKIP
  Gold は suggested_side に従う。自由予想は禁止
        │
Cursor（参謀）          GitHub Actions（ペーパー + 報告）
  戦略・リスク・EA保守     価格取得 → 仮想帳簿 → commander.json 更新
        │                         │
        └──────────┬──────────────┘
                   ▼
            XM MT5 デモ / 実口座
            ea/XMGrokEngine.mq5（majors）
            ea/XMGoldSemi.mq5（GOLD 半自動 OCO）
            60秒ごとに commander.json を WebRequest
```

| 役割 | やる | やらない |
|---|---|---|
| **EA（実時間）** | XM への発注・SL/TP・日次損失で全決済 | GitHub の遅延シグナルでエントリー |
| **Node tick** | ペーパー追跡・シグナル記録・日次損失で HALT 書き込み | 実口座の損益を捏造 |
| **Grok Bot** | 停止判断と Gold の ENTRY（suggested_side のみ） | 自由な方向予想、ロット変更 |
| **Cursor** | コードと不変条件 | リスク上限を上げる、マーチンゲールを足す |

## 戦略（日付でも乱数でもなく、閉じた足だけ）

`config/strategy.json` が正。EA の input を同じ値に揃える。

- 対象: EURUSD / GBPUSD / USDJPY（H1）
- トレンド: EMA20 と EMA50
- エントリー: 終値が EMA20 をトレンド方向へクロス、RSI(14) が極端域でない
- 損切 1.5×ATR(14)、利確 2.0×ATR(14)
- セッション: 07:00–21:00 UTC、金曜 18:00 UTC 以降は新規禁止＋決済
- 禁止: マーチンゲール、ナンピン、グリッド。Majors は LLM エントリー禁止。Gold は suggested_side パネルのみ

## Gold 半自動（巷の Gold EA から取るもの / 捨てるもの）

巷の XAUUSD EA で **使えるのは半自動の骨格だけ**。99%勝率・グリッド・ナンピンは捨てる。

取るもの:

1. アジア時間にレンジを測る（ブローカーサーバー 0–7。UTC ではない）
2. ロンドン開始（サーバー 7–11）に pending を置く
3. Grok がセットアップカードの `suggested_side` に従い `ENTRY: GOLD BUY|SELL`（または NONE なら SKIP）
4. スプレッドが広い日・月初金曜（NFP 隣接）は休む
5. 約定後は SL/TP と反対 pending の取消だけ自動

捨てるもの: マーチンゲール、ナンピン、グリッド、Telegram シグナルのコピー、Grok に「金は上」と自由予想させること。元 EA がロンドン開始で **両方** 置く点は再現しない（Grok が片側ボタン）。対応表は [`docs/SETUP.md`](docs/SETUP.md)。

Grok はパネルの Buy/Sell ボタン。価格・ロット・SL はエンジンが決める。`suggested_side` はアジア終値がレンジの上1/3か下1/3かだけ。

実装:

- Node: `src/gold-breakout.js` + Issue の `ENTRY: GOLD BUY|SELL` / `SKIP: GOLD`
- コメント即時反映: `.github/workflows/xm_trade_commander.yml`（cron を待たない）
- 実時間: `ea/XMGoldSemi.mq5` を XM の **GOLD M15** に載せる
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

EA 側はこれと独立に、**リアル口座では commander が RESUME のときだけ新規**。デモは HALT 以外で動く。Gold 半自動も同じ。

## セットアップ（デモが先）

載せ方の正は [`docs/SETUP.md`](docs/SETUP.md)。要約:

1. この変更を **デフォルトブランチへマージ**する（`issue_comment` はデフォルトの YAML だけ動く）。
2. XM **デモ** MT5 で `ea/XMGoldSemi.mq5` を **GOLD/XAUUSD の M15** に載せる。AutoTrading ON。
3. WebRequest に `raw.githubusercontent.com`（private なら `api.github.com`）を許可。
4. `CommanderURL` はデフォルトブランチの `commander.json`。PR ブランチの raw を指定しない。
5. private なら Contents API URL + `CommanderAuthHeader: Authorization: token ghp_...`（Git に書かない）。
6. `docs/grok-bots/G_xm_trade.txt` を Grok Bot に貼る。Issue タイトルは `XM Trade — 日次レポート`。

ローカル確認:

```bash
cd xm-trade-engine
node --check src/tick.js
node src/self-test.js
node src/tick.js --dry-run
```

Majors は `ea/XMGrokEngine.mq5` を EURUSD H1 に別チャートで載せる。Gold と混ぜない。
実口座は、デモでアジアロック → ENTRY → pending を確認したあと。リスク上限は上げない。

## 運用コマンド（Grok Bot / 人間）

GitHub Issue「XM Trade — 日次レポート」に **1 行だけ** 書く。

```
KILL_SWITCH: HALT
KILL_SWITCH: PAPER_ONLY
KILL_SWITCH: REDUCE_RISK
KILL_SWITCH: RESUME
ENTRY: GOLD BUY
ENTRY: GOLD SELL
SKIP: GOLD
ARM: GOLD
```

Grok の Gold 行は `suggested_side` に従う。NONE なら SKIP。`ARM` は人間が OCO 両方を明示したときだけ。
Issue コメントは commander へ即時反映。Gold EA は 30 秒ごとに読む。`RESUME` は利益保証ではない。

## ファイル

```
xm-trade-engine/
├── config/strategy.json     # 戦略（決定論）
├── config/risk.json         # リスク上限
├── config/gold.json         # アジア/ロンドンはブローカー時刻。offset はペーパー用
├── docs/SETUP.md            # MT5 への載せ方
├── src/gold-breakout.js
├── ea/XMGrokEngine.mq5      # majors H1
├── ea/XMGoldSemi.mq5        # GOLD M15 半自動
└── docs/grok-bots/G_xm_trade.txt
```

秘密情報（口座番号、MT パスワード、MetaApi トークン）は Git に置かない。GitHub Secrets のみ。
