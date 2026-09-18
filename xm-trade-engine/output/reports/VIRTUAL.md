# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-18T23:19:00.680Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4378.385  high 4399.67  low 4334.295  RSI 51.1  ATR(D) 102.2043  ATR(H1) 17.1336  SMA20 4421.93125  SMA50 4288.7606
- EURUSD close 1.14863  high 1.14919  low 1.1455  RSI 36.8  ATR(D) 0.0048  ATR(H1) 0.0009  SMA20 1.15935  SMA50 1.15368
- GBPUSD close 1.33947  high 1.33982  low 1.33356  RSI 37.6  ATR(D) 0.0061  ATR(H1) 0.0013  SMA20 1.35186  SMA50 1.34816
- USDJPY close 156.892  high 158.058  low 155.87  RSI 49.3  ATR(D) 1.3589  ATR(H1) 0.3289  SMA20 156.8183  SMA50 159.0773

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4378.3

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

