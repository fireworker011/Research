# XM Gold 半自動の載せ方

このファイルが **MT5 に載せる手順の正**。戦略の中身は `README.md`。Grok の1行は `COMMANDS.md`。

> 自動売買は口座資金を失う。利益は保証しない。デモが先。リスク上限（0.5% / 日次 2% / 0.10 lot）は上げない。

## 全体像

```
Grok Bot  → Issue「XM Trade — 日次レポート」に ENTRY/SKIP 1行
     ↓  issue_comment（デフォルトブランチの workflow）
commander.json（デフォルトブランチ）
     ↓  MT5 WebRequest 30秒ごと
XMGoldSemi.mq5 が GOLD M15 に BuyStop または SellStop
```

GitHub cron は発注クロックに使わない。ロンドン開始は EA のサーバー時刻が正。

## 手順（この順）

### 1. この PR をデフォルトブランチへマージする

`issue_comment` ワークフローは **デフォルトブランチの YAML だけ**が動く。
マージしないと Grok のコメントは `commander.json` に届かない。

デフォルトブランチは `claude/setup-colab-comfyui-Eb9Lh`。
Threads の schedule は戻さない。

### 2. XM の MT5 デモを用意する

Windows か Windows VPS。GitHub ランナーでは動かない。
チャートの銘柄名はエンティティにより `GOLD` または `XAUUSD`。

### 3. EA をコンパイルして載せる

1. MetaEditor で `xm-trade-engine/ea/XMGoldSemi.mq5` をコンパイルする。
2. **GOLD（または XAUUSD）の M15** チャートに付ける。H1 や EURUSD には付けない。
3. AutoTrading を ON。
4. 同じ銘柄に他の EA を同時に載せない（特にネット口座）。

`XMGrokEngine.mq5`（EURUSD など H1）とは別チャート。混ぜない。

### 4. WebRequest を許可する

MT5 → ツール → オプション → EA → **WebRequest で許可された URL**:

| リポジトリ | URL |
|---|---|
| public | `https://raw.githubusercontent.com` |
| private | `https://api.github.com` も追加 |

### 5. `CommanderURL` を入れる

**public の raw（デフォルトブランチ）:**

```
https://raw.githubusercontent.com/<owner>/<repo>/claude/setup-colab-comfyui-Eb9Lh/xm-trade-engine/output/state/commander.json
```

PR ブランチの raw を指定すると、Grok のコメント（デフォルトへ書く）と EA が食い違う。

**private リポジトリ**は raw が 404 になる。Contents API を使う:

```
https://api.github.com/repos/<owner>/<repo>/contents/xm-trade-engine/output/state/commander.json?ref=claude/setup-colab-comfyui-Eb9Lh
```

EA 入力 `CommanderAuthHeader` に次を入れる（Git にコミットしない）:

```
Authorization: token ghp_xxxxxxxx
```

PAT は contents:read だけでよい。EA は `Accept: application/vnd.github.raw` を付ける。

### 6. チャートで時刻を確認する

EA は **ブローカーサーバー時刻**でアジア 0–7 / ロンドン 7–11（GoldLondonBreakout と同じ）。
XM はだいたい UTC+2（夏時間 +3）。

チャート左下の Comment に `asia_locked` と `chart_side` が出る。
アジア確定で Alert が1回鳴る。

`config/gold.json` の `broker_utc_offset_hours` は **ペーパー / Yahoo 用**。
MT5 の「サーバー時刻 − UTC」が 3 なら 3 に変える。EA 自体は `TimeCurrent()` なのでこの値を読まない。

### 7. Grok Bot を載せる

`docs/grok-bots/G_xm_trade.txt` だけを貼る。月100万 dump と混ぜない。
Issue タイトルは正確に `XM Trade — 日次レポート`。
Grok はセットアップカードの `suggested_side` にだけ従う。

### 8. デモで1サイクル見てから実口座

実口座は commander が `RESUME` のときだけ新規。デモは HALT 以外で動く。
`RESUME` の前に、アジアロック → ENTRY → pending → 約定または期限切れ をデモで確認する。

## GoldLondonBreakout との対応

巷の Gold EA（GoldLondonBreakout、M15、サーバー 0–7 / 7–11）の **半自動の骨格だけ**を載せる。99%勝率・グリッド・ナンピンは捨てた。

| 項目 | 元 EA | この実装 |
|---|---|---|
| 時間 | ブローカー アジア 0–7、ロンドン 7–11 | **同じ**（EA は `TimeCurrent()`） |
| 足 | GOLD/XAUUSD M15 | **同じ** |
| レンジ | アジア高安 | **同じ**（確定足、形成中バー除外） |
| エントリー | ロンドン開始で **BuyStop と SellStop を両方** | **違う（意図）**: Grok の `ENTRY: GOLD BUY\|SELL` で片側。人間の `ARM: GOLD` だけ両方 |
| バッファ / SL / TP | ATR 比 | **同じ既定**（0.15 ATR / 1.2 ATR / 1.8R） |
| レンジフィルタ | 日足 ATR 比 | **同じ**（0.15–0.70） |
| 期限 | ロンドン終了で pending 取消 | **同じ**（`ORDER_TIME_SPECIFIED`） |
| 約定後 | 反対 pending を消す | **同じ** |
| スプレッド | 広すぎたら見送り | **同じ**（既定 0.80） |
| 月初金曜 | 元は自動発注することが多い | **違う（意図）**: NFP 隣接を休む |
| グリッド / ナンピン | 巷の改変版に多い | **載せない** |
| ロット | 元は固定ロットが多い | 残高 0.5%（`REDUCE_RISK` で半分）。最大 0.10 |
| 日次損失 | なしが多い | 2% で HALT・決済 |

完全再現ではない。**時間窓・レンジ・OCO の置き方・ATR パラメータは揃えた。** 自動で両方置く代わりに、Grok がパネルの片側ボタンを押す。

## 残る差（直さない／直した）

直した:

- Node ペーパーが UTC 0–7 をアジアと誤認していた → `broker_utc_offset_hours` で XM に合わせる
- 片側 ENTRY なのに反対値幅が近いと両方とも置かなかった → 置く側だけ判定
- ARM で片方が失敗するとリトライしなかった
- `SKIP: GOLD` が既存 pending を消さなかった
- `REDUCE_RISK` が Gold EA のロットに効いていなかった
- 司令塔 workflow が PR ブランチに書いて EA の raw とずれることがあった → デフォルトブランチへ書く

直さない（設計）:

- ペーパーの `suggested_side` は Yahoo `XAUUSD=X` の H1。MT5 の高安・終値とは一致しないことがある。チャートの `chart_side` と Issue が食い違ったら **SKIP**
- GitHub tick は遅延する。約定の正は EA
- 実口座の損益をペーパーから発明しない

## 動かないとき

| 症状 | 見る場所 |
|---|---|
| コメントしても EA が IDLE のまま | デフォルトへマージしたか。Issue タイトルが完全一致か。`gold-notice:` 付きコメントは指令ではない |
| `commander HTTP 404` | private なのに raw URL。API + PAT にする |
| `commander HTTP 403/401` | WebRequest 許可リスト、PAT、ヘッダの改行 |
| アジアがロックされない | 銘柄が GOLD/XAUUSD か。M15 か。サーバー時刻 7 時以降か。レンジが ATR 比の外なら `asia skip frac=` がログに出る |
| pending が付かない | AutoTrading。`gold_arm_date` が今日の UTC 日付か。ロンドン 7–11 か。リアル口座なら RESUME |
| 毎日同じ方向 | `suggested_side` はアジア終値の位置だけ。予想ではない |
