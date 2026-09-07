# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-07T04:09:56.092Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4405.02  high 4435.255  low 4389.585  RSI 50.7  ATR(D) 104.1513  ATR(H1) 18.637  SMA20 4466.847  SMA50 4247.3316
- EURUSD close 1.16108  high 1.16203  low 1.16074  RSI 54.5  ATR(D) 0.0045  ATR(H1) 0.0007  SMA20 1.16115  SMA50 1.15126
- GBPUSD close 1.35114  high 1.35222  low 1.35056  RSI 49  ATR(D) 0.0055  ATR(H1) 0.0009  SMA20 1.35544  SMA50 1.34601
- USDJPY close 156.118  high 156.293  low 155.801  RSI 32.5  ATR(D) 1.1566  ATR(H1) 0.2674  SMA20 158.84195  SMA50 160.40256

## Gold 仮想 OCO（損切り・利確）

- status: `forming` / reason: asia_forming
- last: 4399.6
- アジア: 4386.6 – 4426.4 close 4399.6（range 39.8, ATR日次比 0.561）
- H1 ATR: 18.64（tradingview_atr60 / OKX H1 7.7） / SL距離 22.36（1.2×ATR） / TP距離 40.26（1.8R）
- chart suggested_side: SELL（参考。執行は OCO 両方）
- BuyStop 4429.2 → 損切り 4406.84 / 利確 4469.46
- SellStop 4383.8 → 損切り 4406.16 / 利確 4343.54
- lot: 0.02（リスク 0.5%、上限 0.10。固定lotではない）
- アジア未確定。ロンドン開始まで高安は更新され得る。OCO は仮置き。

## ペーパー帳簿（仮想資金）

- equity: 10000 / balance: 10000 / 本日実現: 0
- commander: `PAPER_ONLY`
- live_gate: runtime.live_enabled is false; commander PAPER_ONLY; XM_LIVE_CONFIRM is not I_UNDERSTAND_THE_RISK

### 未約定 pending

- OCO GOLD lot=0.02 status=forming
  - BUY 4429.2 SL 4406.84 TP 4469.46
  - SELL 4383.8 SL 4406.16 TP 4343.54

- 建玉なし（約定待ち、またはルール未点火）

## Majors（EMAルール。LLMは選ばない）

- EURUSD: FLAT (out_of_session)
- GBPUSD: FLAT (out_of_session)
- USDJPY: FLAT (out_of_session)

## やらない

- ゴールドの方向を文章で予想しない
- majors を LLM が買わせない
- マーチンゲール・ナンピン・グリッド
- リスク上限を上げる
- この数字を XM 残高として読む

