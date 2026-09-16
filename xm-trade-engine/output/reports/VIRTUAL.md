# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-16T22:11:00.027Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4261.135  high 4262.825  low 4259  RSI 42.1  ATR(D) 96.5652  ATR(H1) 23.4652  SMA20 4429.12625  SMA50 4281.9922
- EURUSD close 1.1464  high 1.14672  low 1.14562  RSI 32.3  ATR(D) 0.0047  ATR(H1) 0.0012  SMA20 1.16024  SMA50 1.15352
- GBPUSD close 1.33783  high 1.33896  low 1.33753  RSI 33.3  ATR(D) 0.0057  ATR(H1) 0.0015  SMA20 1.35321  SMA50 1.34822
- USDJPY close 156.263  high 156.282  low 156.212  RSI 45.8  ATR(D) 1.232  ATR(H1) 0.236  SMA20 156.93795  SMA50 159.17962

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4266.5
- アジア: 4265.2 – 4274.4 close undefined（range 9.2, ATR日次比 0.125）
- H1 ATR: undefined（tradingview_atr60 / OKX H1 20.57） / SL距離 undefined（1.2×ATR） / TP距離 undefined（1.8R）
- chart suggested_side: undefined（参考。執行は OCO 両方）
- BuyStop undefined → 損切り undefined / 利確 undefined
- SellStop undefined → 損切り undefined / 利確 undefined

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

