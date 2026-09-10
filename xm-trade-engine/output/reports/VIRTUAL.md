# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-10T20:53:05.210Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4316.425  high 4435.045  low 4313.85  RSI 45.3  ATR(D) 104.7172  ATR(H1) 20.0422  SMA20 4464.2095  SMA50 4265.5807
- EURUSD close 1.16096  high 1.16419  low 1.15923  RSI 53.1  ATR(D) 0.0045  ATR(H1) 0.001  SMA20 1.16255  SMA50 1.15255
- GBPUSD close 1.35104  high 1.35604  low 1.34912  RSI 48.2  ATR(D) 0.0056  ATR(H1) 0.0012  SMA20 1.35612  SMA50 1.34749
- USDJPY close 154.459  high 154.672  low 153.284  RSI 31.8  ATR(D) 1.2913  ATR(H1) 0.2503  SMA20 157.94215  SMA50 159.88108

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4320.7
- アジア: 4389.9 – 4417.9 close 4404.8（range 28, ATR日次比 0.39）
- H1 ATR: 20.04（tradingview_atr60 / OKX H1 17.53） / SL距離 24.05（1.2×ATR） / TP距離 43.29（1.8R）
- chart suggested_side: NONE（参考。執行は OCO 両方）
- BuyStop 4420.91 → 損切り 4396.86 / 利確 4464.2
- SellStop 4386.89 → 損切り 4410.94 / 利確 4343.6

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

