# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-18T09:00:47.809Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4392.185  high 4399.67  low 4334.295  RSI 52  ATR(D) 102.2043  ATR(H1) 16.377  SMA20 4422.62125  SMA50 4289.0366
- EURUSD close 1.1482  high 1.14919  low 1.14744  RSI 35.9  ATR(D) 0.0047  ATR(H1) 0.0008  SMA20 1.15933  SMA50 1.15368
- GBPUSD close 1.33704  high 1.3376  low 1.33527  RSI 33.8  ATR(D) 0.0058  ATR(H1) 0.0011  SMA20 1.35174  SMA50 1.34812
- USDJPY close 157.8  high 157.912  low 155.87  RSI 53.3  ATR(D) 1.3485  ATR(H1) 0.318  SMA20 156.8637  SMA50 159.09546

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4389.9
- アジア: 4336.4 – 4367.9 close 4367.9（range 31.5, ATR日次比 0.429）
- H1 ATR: 16.38（tradingview_atr60 / OKX H1 14.13） / SL距離 19.65（1.2×ATR） / TP距離 35.37（1.8R）
- chart suggested_side: BUY（参考。執行は OCO 両方）
- BuyStop 4370.36 → 損切り 4350.71 / 利確 4405.73
- SellStop 4333.94 → 損切り 4353.59 / 利確 4298.57

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

