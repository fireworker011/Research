# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-17T22:10:29.148Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4342.415  high 4343.365  low 4341.925  RSI 48.5  ATR(D) 97.6436  ATR(H1) 18.4228  SMA20 4420.13275  SMA50 4288.0412
- EURUSD close 1.1476  high 1.14795  low 1.14756  RSI 34.7  ATR(D) 0.0046  ATR(H1) 0.0008  SMA20 1.1593  SMA50 1.15366
- GBPUSD close 1.33576  high 1.33608  low 1.33527  RSI 31.6  ATR(D) 0.0057  ATR(H1) 0.0014  SMA20 1.35168  SMA50 1.34809
- USDJPY close 155.988  high 156.024  low 155.928  RSI 44.6  ATR(D) 1.2095  ATR(H1) 0.1901  SMA20 156.7731  SMA50 159.05922

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4342.6
- アジア: 4342.5 – 4346.6 close undefined（range 4.1, ATR日次比 0.058）
- H1 ATR: undefined（tradingview_atr60 / OKX H1 15.37） / SL距離 undefined（1.2×ATR） / TP距離 undefined（1.8R）
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

