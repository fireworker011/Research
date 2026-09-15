# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-15T22:14:21.089Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4293.59  high 4296.025  low 4293.56  RSI 44.2  ATR(D) 94.3495  ATR(H1) 14.6838  SMA20 4443.504  SMA50 4279.84
- EURUSD close 1.15428  high 1.15454  low 1.15368  RSI 41.8  ATR(D) 0.0043  ATR(H1) 0.0007  SMA20 1.16171  SMA50 1.15361
- GBPUSD close 1.34758  high 1.348  low 1.34713  RSI 43.4  ATR(D) 0.0052  ATR(H1) 0.001  SMA20 1.35495  SMA50 1.34847
- USDJPY close 155.124  high 155.177  low 155.061  RSI 39.4  ATR(D) 1.2154  ATR(H1) 0.1721  SMA20 157.01925  SMA50 159.27868

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4292.5
- アジア: 4292.5 – 4296.1 close undefined（range 3.6, ATR日次比 0.055）
- H1 ATR: undefined（tradingview_atr60 / OKX H1 12.07） / SL距離 undefined（1.2×ATR） / TP距離 undefined（1.8R）
- chart suggested_side: undefined（参考。執行は OCO 両方）
- BuyStop undefined → 損切り undefined / 利確 undefined
- SellStop undefined → 損切り undefined / 利確 undefined

## ペーパー帳簿（仮想資金）

- equity: 10014.64 / balance: 10014.64 / 本日実現: 0
- commander: `HALT`
- live_gate: runtime.live_enabled is false; commander HALT; XM_LIVE_CONFIRM is not I_UNDERSTAND_THE_RISK

### 未約定 pending

- OCO GOLD lot=0.02 status=forming
  - BUY 4366.26 SL 4346.61 TP 4401.64
  - SELL 4350.64 SL 4370.29 TP 4315.26

- 建玉なし（約定待ち、またはルール未点火）

## Majors（EMAルール。LLMは選ばない）

- EURUSD: FLAT (halt)
- GBPUSD: FLAT (halt)
- USDJPY: FLAT (halt)

## やらない

- ゴールドの方向を文章で予想しない
- majors を LLM が買わせない
- マーチンゲール・ナンピン・グリッド
- リスク上限を上げる
- この数字を XM 残高として読む

