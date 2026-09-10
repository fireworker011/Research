# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-10T08:57:25.101Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4394.595  high 4435.045  low 4389.735  RSI 50.1  ATR(D) 99.2969  ATR(H1) 17.5956  SMA20 4468.118  SMA50 4267.1441
- EURUSD close 1.16361  high 1.16419  low 1.16294  RSI 58.4  ATR(D) 0.0042  ATR(H1) 0.0007  SMA20 1.16268  SMA50 1.1526
- GBPUSD close 1.35514  high 1.35604  low 1.35446  RSI 54.3  ATR(D) 0.0052  ATR(H1) 0.0009  SMA20 1.35633  SMA50 1.34757
- USDJPY close 153.616  high 153.744  low 153.284  RSI 25.6  ATR(D) 1.225  ATR(H1) 0.2608  SMA20 157.9  SMA50 159.86422

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4392.4
- アジア: 4389.9 – 4417.9 close 4404.8（range 28, ATR日次比 0.405）
- H1 ATR: 17.6（tradingview_atr60 / OKX H1 15.1） / SL距離 21.11（1.2×ATR） / TP距離 38.01（1.8R）
- chart suggested_side: NONE（参考。執行は OCO 両方）
- BuyStop 4420.54 → 損切り 4399.43 / 利確 4458.55
- SellStop 4387.26 → 損切り 4408.37 / 利確 4349.25

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

