# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-18T13:36:51.462Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4355.965  high 4399.67  low 4334.295  RSI 49.5  ATR(D) 102.2043  ATR(H1) 18.1416  SMA20 4420.81025  SMA50 4288.3122
- EURUSD close 1.14653  high 1.14919  low 1.1455  RSI 33.5  ATR(D) 0.0048  ATR(H1) 0.0009  SMA20 1.15924  SMA50 1.15364
- GBPUSD close 1.33457  high 1.3376  low 1.33356  RSI 30.7  ATR(D) 0.006  ATR(H1) 0.0013  SMA20 1.35162  SMA50 1.34807
- USDJPY close 157.796  high 158.058  low 155.87  RSI 53.3  ATR(D) 1.3589  ATR(H1) 0.3175  SMA20 156.8635  SMA50 159.09538

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4357
- アジア: 4336.4 – 4367.9 close 4367.9（range 31.5, ATR日次比 0.429）
- H1 ATR: 18.14（tradingview_atr60 / OKX H1 15.67） / SL距離 21.77（1.2×ATR） / TP距離 39.19（1.8R）
- chart suggested_side: BUY（参考。執行は OCO 両方）
- BuyStop 4370.62 → 損切り 4348.85 / 利確 4409.81
- SellStop 4333.68 → 損切り 4355.45 / 利確 4294.49

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

