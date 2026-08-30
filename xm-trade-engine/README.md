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
1手は KILL_SWITCH: HALT | PAPER_ONLY | REDUCE_RISK | RESUME
  Gold 半自動だけ ARM: GOLD / SKIP: GOLD（方向は書かない）
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

## Gold 半自動（巷の Gold EA から取るもの / 捨てるもの）

巷の XAUUSD EA で **使えるのは半自動の骨格だけ**。99%勝率・グリッド・ナンピンは捨てる。

取るもの:

1. アジア時間にレンジを測る
2. ロンドン前半に BuyStop と SellStop を両方置く（OCO。方向は市場が決める）
3. 人がその日のセットアップを ARM するまで待ってから置く
4. スプレッドが広い日・月初金曜（NFP 隣接）は休む
5. 約定後は SL/TP と「片方約定で反対を取消」だけ自動

捨てるもの: マーチンゲール、ナンピン、グリッド、Telegram シグナルのコピー、LLM に「金は上」と言わせること。

実装:

- Node: `src/gold-breakout.js` + Issue の `ARM: GOLD` / `SKIP: GOLD`
- 実時間: `ea/XMGoldSemi.mq5` を XM の **GOLD（または XAUUSD）M15** に載せる
- リスクは majors と同じ 0.5% / 日次 2% / 最大 0.10 lot。上げない
- GitHub cron では Gold を発注しない（遅延するためペーパー追跡のみ）

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

1. XM で **デモ口座** を開き、MT5 を入れる（Windows、または Windows VPS。GitHub ランナーでは動かない）。
2. `ea/XMGrokEngine.mq5` を EURUSD H1 に載せる。Gold 半自動は `ea/XMGoldSemi.mq5` を GOLD M15 に載せる。AutoTrading を ON。
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
ARM: GOLD
SKIP: GOLD
```

`ARM: GOLD` は今日の OCO 許可だけ。Buy/Sell を書くな。

次の tick が Issue コメントを `commander.json` に写し、EA がそれを読む。
`RESUME` は「実口座ゲートを開け」であり、利益保証ではない。

## ファイル

```
xm-trade-engine/
├── config/strategy.json     # 戦略（決定論）
├── config/risk.json         # リスク上限
├── config/gold.json         # アジアレンジ / ロンドン OCO
├── src/gold-breakout.js
├── ea/XMGrokEngine.mq5      # majors H1
├── ea/XMGoldSemi.mq5        # GOLD M15 半自動
└── docs/grok-bots/G_xm_trade.txt
```

秘密情報（口座番号、MT パスワード、MetaApi トークン）は Git に置かない。GitHub Secrets のみ。
