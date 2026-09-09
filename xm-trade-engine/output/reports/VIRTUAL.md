# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-09T17:50:27.729Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4413.93  high 4434.175  low 4341.255  RSI 51.4  ATR(D) 103.4497  ATR(H1) 19.7495  SMA20 4466.5425  SMA50 4261.9606
- EURUSD close 1.16384  high 1.16544  low 1.16202  RSI 58.7  ATR(D) 0.0044  ATR(H1) 0.001  SMA20 1.16218  SMA50 1.15221
- GBPUSD close 1.35586  high 1.3568  low 1.35304  RSI 55.1  ATR(D) 0.0055  ATR(H1) 0.0013  SMA20 1.35606  SMA50 1.34719
- USDJPY close 153.48  high 154.019  low 152.937  RSI 24.8  ATR(D) 1.2838  ATR(H1) 0.3171  SMA20 158.19185  SMA50 160.01302

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4411
- アジア: 4343 – 4381.9 close 4381.5（range 38.9, ATR日次比 0.569）
- H1 ATR: 19.75（tradingview_atr60 / OKX H1 17.32） / SL距離 23.7（1.2×ATR） / TP距離 42.66（1.8R）
- chart suggested_side: BUY（参考。執行は OCO 両方）
- BuyStop 4384.86 → 損切り 4361.16 / 利確 4427.52
- SellStop 4340.04 → 損切り 4363.74 / 利確 4297.38

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

