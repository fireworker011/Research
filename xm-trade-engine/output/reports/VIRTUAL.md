# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-08T23:24:21.674Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4353.93  high 4357.92  low 4350.74  RSI 47.4  ATR(D) 97.3254  ATR(H1) 16.3784  SMA20 4463.5425  SMA50 4260.7606
- EURUSD close 1.16258  high 1.16274  low 1.16236  RSI 56.8  ATR(D) 0.0042  ATR(H1) 0.0006  SMA20 1.16211  SMA50 1.15218
- GBPUSD close 1.35413  high 1.35426  low 1.35358  RSI 52.9  ATR(D) 0.0053  ATR(H1) 0.0009  SMA20 1.35598  SMA50 1.34715
- USDJPY close 153.564  high 154.019  low 153.51  RSI 25  ATR(D) 1.2429  ATR(H1) 0.3192  SMA20 158.19605  SMA50 160.0147

## Gold 仮想 OCO（損切り・利確）

- status: `forming` / reason: asia_forming
- last: 4354.5
- アジア: 4353.1 – 4363.8 close 4354.5（range 10.7, ATR日次比 0.155）
- H1 ATR: 16.38（tradingview_atr60 / OKX H1 13.34） / SL距離 19.65（1.2×ATR） / TP距離 35.38（1.8R）
- chart suggested_side: SELL（参考。執行は OCO 両方）
- BuyStop 4366.26 → 損切り 4346.61 / 利確 4401.64
- SellStop 4350.64 → 損切り 4370.29 / 利確 4315.26
- lot: 0.02（リスク 0.5%、上限 0.10。固定lotではない）
- アジア未確定。ロンドン開始まで高安は更新され得る。OCO は仮置き。

## ペーパー帳簿（仮想資金）

- equity: 10003.04 / balance: 10000 / 本日実現: 0
- commander: `PAPER_ONLY`
- live_gate: runtime.live_enabled is false; commander PAPER_ONLY; XM_LIVE_CONFIRM is not I_UNDERSTAND_THE_RISK

### 未約定 pending

- OCO GOLD lot=0.02 status=forming
  - BUY 4366.26 SL 4346.61 TP 4401.64
  - SELL 4350.64 SL 4370.29 TP 4315.26

### 建玉

- BUY EURUSD lot=0.1 entry=1.162580408630371 SL=1.16146 TP=1.16394 uPnL=3.46
- BUY GBPUSD lot=0.1 entry=1.354192890701294 SL=1.35258 TP=1.3562 uPnL=-0.42

## Majors（EMAルール。LLMは選ばない）

- EURUSD: HOLD (out_of_session_hold)
- GBPUSD: HOLD (out_of_session_hold)
- USDJPY: FLAT (out_of_session)

## やらない

- ゴールドの方向を文章で予想しない
- majors を LLM が買わせない
- マーチンゲール・ナンピン・グリッド
- リスク上限を上げる
- この数字を XM 残高として読む

