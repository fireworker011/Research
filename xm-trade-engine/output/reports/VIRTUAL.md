# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-11T08:55:45.407Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4348.24  high 4361.15  low 4300.795  RSI 47.5  ATR(D) 101.5485  ATR(H1) 19.5681  SMA20 4462.8105  SMA50 4269.0436
- EURUSD close 1.16003  high 1.16176  low 1.15997  RSI 51.3  ATR(D) 0.0043  ATR(H1) 0.0008  SMA20 1.1627  SMA50 1.15288
- GBPUSD close 1.3508  high 1.35266  low 1.34958  RSI 47.8  ATR(D) 0.0054  ATR(H1) 0.0011  SMA20 1.356  SMA50 1.3478
- USDJPY close 154.088  high 154.618  low 153.962  RSI 30.5  ATR(D) 1.2459  ATR(H1) 0.246  SMA20 157.6804  SMA50 159.73514

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4350
- アジア: 4303.7 – 4341.3 close 4332.7（range 37.6, ATR日次比 0.516）
- H1 ATR: 19.57（tradingview_atr60 / OKX H1 17.19） / SL距離 23.48（1.2×ATR） / TP距離 42.27（1.8R）
- chart suggested_side: BUY（参考。執行は OCO 両方）
- BuyStop 4344.24 → 損切り 4320.76 / 利確 4386.51
- SellStop 4300.76 → 損切り 4324.24 / 利確 4258.49

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

