# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-15T09:29:47.020Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4266.93  high 4317.63  low 4261.375  RSI 42.6  ATR(D) 101.4175  ATR(H1) 16.1237  SMA20 4453.62925  SMA50 4274.9715
- EURUSD close 1.15356  high 1.15537  low 1.15271  RSI 40.7  ATR(D) 0.0046  ATR(H1) 0.0008  SMA20 1.16235  SMA50 1.15334
- GBPUSD close 1.34746  high 1.3505  low 1.34644  RSI 43.3  ATR(D) 0.0055  ATR(H1) 0.001  SMA20 1.3556  SMA50 1.34829
- USDJPY close 155.004  high 155.24  low 154.213  RSI 38.6  ATR(D) 1.2999  ATR(H1) 0.2251  SMA20 157.16525  SMA50 159.42672

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4270.5
- アジア: 4285.7 – 4316.8 close 4306（range 31.1, ATR日次比 0.45）
- H1 ATR: 16.12（tradingview_atr60 / OKX H1 13.17） / SL距離 19.35（1.2×ATR） / TP距離 34.83（1.8R）
- chart suggested_side: NONE（参考。執行は OCO 両方）
- BuyStop 4319.22 → 損切り 4299.87 / 利確 4354.05
- SellStop 4283.28 → 損切り 4302.63 / 利確 4248.45

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

