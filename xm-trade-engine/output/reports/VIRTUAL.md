# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-09T08:58:38.510Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4400.925  high 4413.01  low 4341.255  RSI 50.6  ATR(D) 101.9379  ATR(H1) 16.145  SMA20 4465.89225  SMA50 4261.7005
- EURUSD close 1.16341  high 1.16494  low 1.16236  RSI 58.1  ATR(D) 0.0044  ATR(H1) 0.0007  SMA20 1.16215  SMA50 1.1522
- GBPUSD close 1.35426  high 1.3568  low 1.35358  RSI 53  ATR(D) 0.0054  ATR(H1) 0.0009  SMA20 1.35598  SMA50 1.34716
- USDJPY close 153.655  high 154.019  low 152.937  RSI 25.3  ATR(D) 1.2838  ATR(H1) 0.3339  SMA20 158.2006  SMA50 160.01652

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4399.5
- アジア: 4343 – 4381.9 close 4381.5（range 38.9, ATR日次比 0.555）
- H1 ATR: 16.15（tradingview_atr60 / OKX H1 13.74） / SL距離 19.37（1.2×ATR） / TP距離 34.87（1.8R）
- chart suggested_side: BUY（参考。執行は OCO 両方）
- BuyStop 4384.32 → 損切り 4364.95 / 利確 4419.19
- SellStop 4340.58 → 損切り 4359.95 / 利確 4305.71

## ペーパー帳簿（仮想資金）

- equity: 10014.64 / balance: 10014.64 / 本日実現: 14.64
- commander: `HALT`
- live_gate: runtime.live_enabled is false; commander HALT; XM_LIVE_CONFIRM is not I_UNDERSTAND_THE_RISK

### 未約定 pending

- OCO GOLD lot=0.02 status=forming
  - BUY 4366.26 SL 4346.61 TP 4401.64
  - SELL 4350.64 SL 4370.29 TP 4315.26

- 建玉なし（約定待ち、またはルール未点火）

## Majors（EMAルール。LLMは選ばない）

- EURUSD: CLOSE (halt) lot=0.1 SL=undefined TP=undefined
- GBPUSD: CLOSE (halt) lot=0.1 SL=undefined TP=undefined
- USDJPY: FLAT (halt)

## やらない

- ゴールドの方向を文章で予想しない
- majors を LLM が買わせない
- マーチンゲール・ナンピン・グリッド
- リスク上限を上げる
- この数字を XM 残高として読む

