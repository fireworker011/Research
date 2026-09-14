# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-14T23:52:49.716Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4288.455  high 4300.19  low 4287.065  RSI 43.9  ATR(D) 98.3368  ATR(H1) 18.4913  SMA20 4454.7055  SMA50 4275.402
- EURUSD close 1.15481  high 1.15537  low 1.15476  RSI 42.5  ATR(D) 0.0044  ATR(H1) 0.0009  SMA20 1.16242  SMA50 1.15337
- GBPUSD close 1.35008  high 1.3505  low 1.34984  RSI 46.8  ATR(D) 0.0053  ATR(H1) 0.0011  SMA20 1.35573  SMA50 1.34834
- USDJPY close 154.382  high 154.445  low 154.213  RSI 34.7  ATR(D) 1.2431  ATR(H1) 0.2267  SMA20 157.13415  SMA50 159.41428

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4290.9
- アジア: 4290 – 4303.6 close 4290.9（range 13.6, ATR日次比 0.201）
- H1 ATR: 18.49（tradingview_atr60 / OKX H1 14.15） / SL距離 22.19（1.2×ATR） / TP距離 39.94（1.8R）
- chart suggested_side: SELL（参考。執行は OCO 両方）
- BuyStop 4306.37 → 損切り 4284.18 / 利確 4346.31
- SellStop 4287.23 → 損切り 4309.42 / 利確 4247.29

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

