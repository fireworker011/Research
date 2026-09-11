# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-11T13:35:13.734Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4393.01  high 4398.695  low 4292.11  RSI 50.3  ATR(D) 104.8506  ATR(H1) 23.531  SMA20 4465.049  SMA50 4269.939
- EURUSD close 1.16042  high 1.16176  low 1.15692  RSI 52.1  ATR(D) 0.0045  ATR(H1) 0.001  SMA20 1.16272  SMA50 1.15289
- GBPUSD close 1.35221  high 1.35294  low 1.3481  RSI 49.9  ATR(D) 0.0055  ATR(H1) 0.0014  SMA20 1.35607  SMA50 1.34783
- USDJPY close 153.448  high 154.618  low 153.24  RSI 28.7  ATR(D) 1.2975  ATR(H1) 0.3037  SMA20 157.6484  SMA50 159.72234

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4396
- アジア: 4303.7 – 4341.3 close 4332.7（range 37.6, ATR日次比 0.499）
- H1 ATR: 23.53（tradingview_atr60 / OKX H1 21.17） / SL距離 28.24（1.2×ATR） / TP距離 50.83（1.8R）
- chart suggested_side: BUY（参考。執行は OCO 両方）
- BuyStop 4344.83 → 損切り 4316.59 / 利確 4395.66
- SellStop 4300.17 → 損切り 4328.41 / 利確 4249.34

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

