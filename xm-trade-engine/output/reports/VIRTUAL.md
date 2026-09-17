# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-17T19:02:27.161Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4355.345  high 4381.065  low 4257.6  RSI 49.4  ATR(D) 105.0374  ATR(H1) 20.0872  SMA20 4433.83675  SMA50 4283.8764
- EURUSD close 1.14754  high 1.14978  low 1.14561  RSI 34.6  ATR(D) 0.0049  ATR(H1) 0.0009  SMA20 1.1603  SMA50 1.15354
- GBPUSD close 1.33538  high 1.34066  low 1.33363  RSI 31.4  ATR(D) 0.0061  ATR(H1) 0.0015  SMA20 1.35309  SMA50 1.34817
- USDJPY close 156.036  high 156.314  low 155.338  RSI 44.7  ATR(D) 1.2952  ATR(H1) 0.2139  SMA20 156.9266  SMA50 159.17508

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4352.5
- アジア: 4263.5 – 4318.5 close undefined（range 55, ATR日次比 0.778）
- H1 ATR: undefined（tradingview_atr60 / OKX H1 17.51） / SL距離 undefined（1.2×ATR） / TP距離 undefined（1.8R）
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

