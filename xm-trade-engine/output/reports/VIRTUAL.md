# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-09T13:44:27.658Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4416.105  high 4434.175  low 4341.255  RSI 51.5  ATR(D) 103.4497  ATR(H1) 17.5573  SMA20 4466.65125  SMA50 4262.0041
- EURUSD close 1.16471  high 1.16544  low 1.16219  RSI 60  ATR(D) 0.0044  ATR(H1) 0.0008  SMA20 1.16222  SMA50 1.15223
- GBPUSD close 1.3558  high 1.3568  low 1.35304  RSI 55.1  ATR(D) 0.0055  ATR(H1) 0.0012  SMA20 1.35606  SMA50 1.34719
- USDJPY close 153.401  high 154.019  low 152.937  RSI 24.6  ATR(D) 1.2838  ATR(H1) 0.3165  SMA20 158.1879  SMA50 160.01144

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4414.5
- アジア: 4343 – 4381.9 close 4381.5（range 38.9, ATR日次比 0.544）
- H1 ATR: 17.56（tradingview_atr60 / OKX H1 15.21） / SL距離 21.07（1.2×ATR） / TP距離 37.92（1.8R）
- chart suggested_side: BUY（参考。執行は OCO 両方）
- BuyStop 4384.53 → 損切り 4363.46 / 利確 4422.45
- SellStop 4340.37 → 損切り 4361.44 / 利確 4302.45

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

