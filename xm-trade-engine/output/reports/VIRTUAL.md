# 仮想トレード机 — TradingView + ルール（XMではない）

生成: 2026-09-10T13:37:05.217Z

> これはペーパー。XM口座の残高・約定ではない。VPS/EA がまだでも、ルールで損切りと利確を置いて仮想執行する。
> 方向は LLM の予想ではない。Gold はアジアレンジの OCO 両方。Majors は EMA20/50 クロスだけ。

## データ源

- Gold 足: OKX `XAUT-USDT`（スポット金の連続足。XM 気配ではない）
- スナップショット: TradingView 公開スキャナ `OANDA:XAUUSD` / majors
- Majors 足: Yahoo Finance H1
- Yahoo `XAUUSD=X` は 404 のため使わない

## TradingView スナップショット

- GOLD close 4362.415  high 4435.045  low 4324.17  RSI 48  ATR(D) 103.9801  ATR(H1) 20.7212  SMA20 4466.509  SMA50 4266.5005
- EURUSD close 1.16105  high 1.16419  low 1.15923  RSI 53.3  ATR(D) 0.0045  ATR(H1) 0.001  SMA20 1.16256  SMA50 1.15255
- GBPUSD close 1.35106  high 1.35604  low 1.34912  RSI 48.2  ATR(D) 0.0056  ATR(H1) 0.0013  SMA20 1.35612  SMA50 1.34749
- USDJPY close 154.15  high 154.672  low 153.284  RSI 29.6  ATR(D) 1.2913  ATR(H1) 0.2835  SMA20 157.9267  SMA50 159.8749

## Gold 仮想 OCO（損切り・利確）

- status: `halted` / reason: halt
- last: 4361.6
- アジア: 4389.9 – 4417.9 close 4404.8（range 28, ATR日次比 0.381）
- H1 ATR: 20.72（tradingview_atr60 / OKX H1 17.86） / SL距離 24.87（1.2×ATR） / TP距離 44.76（1.8R）
- chart suggested_side: NONE（参考。執行は OCO 両方）
- BuyStop 4421.01 → 損切り 4396.14 / 利確 4465.77
- SellStop 4386.79 → 損切り 4411.66 / 利確 4342.03

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

