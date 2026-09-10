# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-10T23:11:42.323Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4318.525  high 4324.065  low 4313.765  RSI 45.4  ATR(D) 97.9731  ATR(H1) 18.1652  SMA20 4461.32475  SMA50 4268.4493
- EURUSD close 1.16089  high 1.16141  low 1.16068  RSI 53  ATR(D) 0.0042  ATR(H1) 0.0009  SMA20 1.16275  SMA50 1.15289
- GBPUSD close 1.35098  high 1.35159  low 1.35061  RSI 48.1  ATR(D) 0.0053  ATR(H1) 0.0011  SMA20 1.35601  SMA50 1.34781
- USDJPY close 154.44  high 154.54  low 154.364  RSI 31.7  ATR(D) 1.2116  ATR(H1) 0.2263  SMA20 157.698  SMA50 159.74218

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4322.6
- アジア: 4319.2 – 4329.2 close undefined（range 10, ATR日次比 0.139）
- H1 ATR: undefined（tradingview_atr60 / OKX H1 15.1） / SL距離 undefined（1.2×ATR） / TP距離 undefined（1.8R）
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

