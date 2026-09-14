# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-14T20:57:08.468Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4298.265  high 4355.405  low 4253.635  RSI 44.5  ATR(D) 104.8916  ATR(H1) 20.0248  SMA20 4456.94875  SMA50 4271.7302
- EURUSD close 1.155  high 1.15979  low 1.15231  RSI 42.8  ATR(D) 0.0047  ATR(H1) 0.0011  SMA20 1.16255  SMA50 1.15309
- GBPUSD close 1.35005  high 1.35289  low 1.3464  RSI 46.8  ATR(D) 0.0056  ATR(H1) 0.0012  SMA20 1.35588  SMA50 1.34806
- USDJPY close 154.348  high 155  low 153.374  RSI 34.5  ATR(D) 1.3209  ATR(H1) 0.2507  SMA20 157.3966  SMA50 159.56908

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4301.3
- アジア: 4325 – 4356.1 close 4331.6（range 31.1, ATR日次比 0.46）
- H1 ATR: 20.02（tradingview_atr60 / OKX H1 15.96） / SL距離 24.03（1.2×ATR） / TP距離 43.25（1.8R）
- chart suggested_side: SELL（参考。執行は OCO 両方）
- BuyStop 4359.1 → 損切り 4335.07 / 利確 4402.35
- SellStop 4322 → 損切り 4346.03 / 利確 4278.75

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

