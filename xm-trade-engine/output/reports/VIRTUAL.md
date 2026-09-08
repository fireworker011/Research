# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-08T21:30:07.851Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4355.705  high 4442.98  low 4345.06  RSI 47.5  ATR(D) 104.2597  ATR(H1) 18.1827  SMA20 4466.27225  SMA50 4254.3161
- EURUSD close 1.16253  high 1.16262  low 1.16236  RSI 56.8  ATR(D) 0.0042  ATR(H1) 0.0007  SMA20 1.16211  SMA50 1.15218
- GBPUSD close 1.3537  high 1.35392  low 1.35358  RSI 52.2  ATR(D) 0.0052  ATR(H1) 0.001  SMA20 1.35596  SMA50 1.34714
- USDJPY close 153.962  high 154.019  low 153.914  RSI 26.1  ATR(D) 1.214  ATR(H1) 0.3201  SMA20 158.21595  SMA50 160.02266

## Gold 仮想 OCO（損切り・利確）

- status: `expired` / reason: london_expired
- last: 4360.9
- アジア: 4405 – 4441.4 close 4432.2（range 36.4, ATR日次比 0.528）
- H1 ATR: 18.18（tradingview_atr60 / OKX H1 14.41） / SL距離 21.82（1.2×ATR） / TP距離 39.27（1.8R）
- chart suggested_side: BUY（参考。執行は OCO 両方）
- BuyStop 4444.13 → 損切り 4422.31 / 利確 4483.4
- SellStop 4402.27 → 損切り 4424.09 / 利確 4363

## ペーパー帳簿（仮想資金）

- equity: 9996.63 / balance: 10000 / 本日実現: 0
- commander: `PAPER_ONLY`
- live_gate: runtime.live_enabled is false; commander PAPER_ONLY; XM_LIVE_CONFIRM is not I_UNDERSTAND_THE_RISK

### 建玉

- BUY EURUSD lot=0.1 entry=1.162580408630371 SL=1.16146 TP=1.16394 uPnL=3.46
- BUY GBPUSD lot=0.1 entry=1.354192890701294 SL=1.35258 TP=1.3562 uPnL=-6.83

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

