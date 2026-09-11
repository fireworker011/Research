# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-11T23:16:33.593Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4349.42  high 4402.63  low 4292.11  RSI 47.6  ATR(D) 105.1317  ATR(H1) 20.7433  SMA20 4462.8695  SMA50 4269.0672
- EURUSD close 1.15993  high 1.16176  low 1.15692  RSI 51.1  ATR(D) 0.0045  ATR(H1) 0.0009  SMA20 1.1627  SMA50 1.15288
- GBPUSD close 1.35264  high 1.3535  low 1.3481  RSI 50.5  ATR(D) 0.0056  ATR(H1) 0.0012  SMA20 1.35609  SMA50 1.34784
- USDJPY close 153.533  high 154.618  low 153.24  RSI 28.9  ATR(D) 1.2975  ATR(H1) 0.2521  SMA20 157.65265  SMA50 159.72404

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4348.9

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

