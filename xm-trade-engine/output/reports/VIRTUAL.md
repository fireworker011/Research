# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-11T20:58:34.802Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4348.905  high 4402.63  low 4292.11  RSI 47.5  ATR(D) 105.1317  ATR(H1) 20.7433  SMA20 4462.84375  SMA50 4269.0569
- EURUSD close 1.15986  high 1.16176  low 1.15692  RSI 51  ATR(D) 0.0045  ATR(H1) 0.0009  SMA20 1.16269  SMA50 1.15287
- GBPUSD close 1.35252  high 1.3535  low 1.3481  RSI 50.4  ATR(D) 0.0056  ATR(H1) 0.0012  SMA20 1.35609  SMA50 1.34784
- USDJPY close 153.536  high 154.618  low 153.24  RSI 28.8  ATR(D) 1.2975  ATR(H1) 0.2521  SMA20 157.6515  SMA50 159.72358

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4347
- アジア: 4303.7 – 4341.3 close 4332.7（range 37.6, ATR日次比 0.52）
- H1 ATR: 20.74（tradingview_atr60 / OKX H1 18.91） / SL距離 24.89（1.2×ATR） / TP距離 44.81（1.8R）
- chart suggested_side: BUY（参考。執行は OCO 両方）
- BuyStop 4344.41 → 損切り 4319.52 / 利確 4389.22
- SellStop 4300.59 → 損切り 4325.48 / 利確 4255.78

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

