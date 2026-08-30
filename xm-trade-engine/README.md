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
  1手は KILL_SWITCH: HALT | PAPER_ONLY | REDUCE_RISK | RESUME だけ
        │
Cursor（参謀）          GitHub Actions（ペーパー + 報告）
  戦略・リスク・EA保守     価格取得 → 仮想帳簿 → commander.json 更新
        │                         │
        └──────────┬──────────────┘
                   ▼
            XM MT5 デモ / 実口座
            ea/XMGrokEngine.mq5
            閉じた H1 で EMA 戦略を実行
            60秒ごとに commander.json を WebRequest
```

| 役割 | やる | やらない |
|---|---|---|
| **EA（実時間）** | XM への発注・SL/TP・日次損失で全決済 | GitHub の遅延シグナルでエントリー |
| **Node tick** | ペーパー追跡・シグナル記録・日次損失で HALT 書き込み | 実口座の損益を捏造 |
| **Grok Bot** | 停止・縮小・継続の 1 手 | 通貨ペアの売買指示、目標金額の変更 |
| **Cursor** | コードと不変条件 | リスク上限を上げる、マーチンゲールを足す |

## 戦略（日付でも乱数でもなく、閉じた足だけ）

`config/strategy.json` が正。EA の input を同じ値に揃える。

- 対象: EURUSD / GBPUSD / USDJPY（H1）
- トレンド: EMA20 と EMA50
- エントリー: 終値が EMA20 をトレンド方向へクロス、RSI(14) が極端域でない
- 損切 1.5×ATR(14)、利確 2.0×ATR(14)
- セッション: 07:00–21:00 UTC、金曜 18:00 UTC 以降は新規禁止＋決済
- 禁止: マーチンゲール、ナンピン、グリッド、LLM エントリー

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

EA 側はこれと独立に、**リアル口座では commander が RESUME のときだけ新規**。デモは HALT 以外で動く。

## セットアップ（デモが先）

1. XM で **デモ口座** を開き、MT5 を入れる（Windows、または Windows VPS。GitHub ランナーでは動かない）。
2. `ea/XMGrokEngine.mq5` を MetaEditor でコンパイルし、EURUSD H1 に載せる。AutoTrading を ON。
3. MT5 → ツール → オプション → EA → **WebRequest を許可** に、このリポジトリの `raw.githubusercontent.com`（必要なら `api.github.com`）を追加。
4. EA の `CommanderURL` に、マージ後の raw URL を入れる:

   `https://raw.githubusercontent.com/<owner>/<repo>/<branch>/xm-trade-engine/output/state/commander.json`

   リポジトリが private なら、contents 読み取りだけの PAT を EA 入力 `CommanderAuthHeader` に `Authorization: token ghp_...` として入れる。**Git にコミットしない。**

5. ローカル確認:

```bash
cd xm-trade-engine
node --check src/tick.js
node src/self-test.js
node src/tick.js --dry-run
```

6. Grok Bot に `docs/grok-bots/G_xm_trade.txt` を貼る。日次 Issue 以外の dump（月100万など）と混ぜない。

7. 実口座は、デモで同じ設定が問題なく回ったあと。リスク上限は上げない。

## 運用コマンド（Grok Bot / 人間）

GitHub Issue「XM Trade — 日次レポート」に **1 行だけ** 書く。

```
KILL_SWITCH: HALT
KILL_SWITCH: PAPER_ONLY
KILL_SWITCH: REDUCE_RISK
KILL_SWITCH: RESUME
```

次の tick が Issue コメントを `commander.json` に写し、EA がそれを読む。
`RESUME` は「実口座ゲートを開け」であり、利益保証ではない。

## ファイル

```
xm-trade-engine/
├── config/strategy.json     # 戦略（決定論）
├── config/risk.json         # リスク上限
├── config/runtime.example.json
├── src/tick.js              # ペーパー 1 ティック
├── src/report.js            # 日次レポート → Issue
├── src/self-test.js
├── ea/XMGrokEngine.mq5      # XM 実時間
└── docs/grok-bots/G_xm_trade.txt
```

秘密情報（口座番号、MT パスワード、MetaApi トークン）は Git に置かない。GitHub Secrets のみ。
