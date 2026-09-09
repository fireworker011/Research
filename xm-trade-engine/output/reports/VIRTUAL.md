# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-09T23:16:04.906Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4399.94  high 4406.105  low 4397.755  RSI 50.5  ATR(D) 96.6569  ATR(H1) 16.6402  SMA20 4468.38525  SMA50 4267.251
- EURUSD close 1.16378  high 1.16384  low 1.16304  RSI 58.7  ATR(D) 0.0042  ATR(H1) 0.0008  SMA20 1.16269  SMA50 1.15261
- GBPUSD close 1.35528  high 1.35548  low 1.35446  RSI 54.5  ATR(D) 0.0052  ATR(H1) 0.0011  SMA20 1.35633  SMA50 1.34758
- USDJPY close 153.338  high 153.623  low 153.308  RSI 24.4  ATR(D) 1.2146  ATR(H1) 0.258  SMA20 157.8861  SMA50 159.85866

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4397.6
- アジア: 4395.2 – 4402.4 close undefined（range 7.2, ATR日次比 0.105）
- H1 ATR: undefined（tradingview_atr60 / OKX H1 13.79） / SL距離 undefined（1.2×ATR） / TP距離 undefined（1.8R）
- chart suggested_side: undefined（参考。執行は OCO 両方）
- BuyStop undefined → 損切り undefined / 利確 undefined
- SellStop undefined → 損切り undefined / 利確 undefined

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

- EURUSD: FLAT (halt)
- GBPUSD: FLAT (halt)
- USDJPY: FLAT (halt)

## やらない

- ゴールドの方向を文章で予想しない
- majors を LLM が買わせない
- マーチンゲール・ナンピン・グリッド
- リスク上限を上げる
- この数字を XM 残高として読む

