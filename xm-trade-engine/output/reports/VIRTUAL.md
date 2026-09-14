# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-14T09:53:11.413Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4283.415  high 4355.405  low 4278.3  RSI 43.6  ATR(D) 103.1298  ATR(H1) 19.5069  SMA20 4456.20625  SMA50 4271.4332
- EURUSD close 1.15428  high 1.15979  low 1.15343  RSI 41.8  ATR(D) 0.0046  ATR(H1) 0.001  SMA20 1.16251  SMA50 1.15308
- GBPUSD close 1.34879  high 1.35289  low 1.34734  RSI 45.1  ATR(D) 0.0056  ATR(H1) 0.0011  SMA20 1.35582  SMA50 1.34804
- USDJPY close 154.52  high 154.612  low 153.374  RSI 35.5  ATR(D) 1.2932  ATR(H1) 0.2427  SMA20 157.4052  SMA50 159.57252

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4289.4
- アジア: 4325 – 4356.1 close 4331.6（range 31.1, ATR日次比 0.456）
- H1 ATR: 19.51（tradingview_atr60 / OKX H1 11.42） / SL距離 23.41（1.2×ATR） / TP距離 42.13（1.8R）
- chart suggested_side: SELL（参考。執行は OCO 両方）
- BuyStop 4359.03 → 損切り 4335.62 / 利確 4401.16
- SellStop 4322.07 → 損切り 4345.48 / 利確 4279.94

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

