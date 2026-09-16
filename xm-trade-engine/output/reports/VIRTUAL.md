# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-16T14:58:59.093Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4352.715  high 4360.5  low 4275.67  RSI 48.6  ATR(D) 100.2327  ATR(H1) 16.4949  SMA20 4446.46025  SMA50 4281.0225
- EURUSD close 1.15361  high 1.15566  low 1.15275  RSI 40.7  ATR(D) 0.0045  ATR(H1) 0.0008  SMA20 1.16168  SMA50 1.15359
- GBPUSD close 1.34528  high 1.34998  low 1.34458  RSI 40.5  ATR(D) 0.0055  ATR(H1) 0.0011  SMA20 1.35484  SMA50 1.34842
- USDJPY close 155.121  high 155.491  low 154.882  RSI 39.3  ATR(D) 1.2506  ATR(H1) 0.1859  SMA20 157.0191  SMA50 159.27862

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4351.5
- アジア: 4277.6 – 4338.7 close undefined（range 61.1, ATR日次比 0.875）
- H1 ATR: undefined（tradingview_atr60 / OKX H1 14.7） / SL距離 undefined（1.2×ATR） / TP距離 undefined（1.8R）
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

