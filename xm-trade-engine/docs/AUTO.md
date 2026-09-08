# XM 自動システム — いま組むもの / まだ組まないもの

Naomiichi は iPhone のみ。Threads の自動投稿は触らない。XM パスワードは Grok に渡さない。

自動は **2層**。混ぜると破産する。

| 層 | 何が自動か | 実口座？ | いま |
|---|---|---|---|
| **A. GitHub ペーパー** | TradingView + ルールで Gold OCO（損切り・利確つき）を置き、Issue に `virtual-desk:` を書く。Grok は表を写すだけ | いいえ | この PR をデフォルトへマージすれば平日 04–21 UTC で回る |
| **B. VPS + MT5 EA** | XM デモへ本当の BuyStop/SellStop | デモのみ。ライブはまだ禁止 | VPS を借りて [`docs/IPHONE.md`](docs/IPHONE.md) |

GitHub cron は遅延する。**EA の発注クロックには使わない。**

## 層A（今やる。マージ1回）

1. PR をデフォルトブランチへマージする。
2. Actions で **XM Trade ペーパーティック** を 1 回 Run する。
3. Issue https://github.com/fireworker011/Research/issues/93 を Subscribe。
4. Grok Bot には [`docs/grok-bots/G_xm_trade.txt`](docs/grok-bots/G_xm_trade.txt) **だけ**（貼済みなら貼り直さなくてよい）。

動くもの:

- Gold: アジアレンジ確定 → ロンドンで BuyStop と SellStop の両方。先に触れた側だけ。SL 1.2×H1 ATR、TP 1.8R
- Majors: EMA20/50 クロスのみ。LLM は選ばない
- 日次レポートが Issue 本文を更新
- `virtual-desk:` は告知。ENTRY ではない

やらない: マーチンゲール、リスク上限の引き上げ、`RESUME`、Threads cron 再開。

## 層B（実発注。VPSが要る）

iPhone の XM アプリに EA は載らない。安い Windows VPS + スマホの Windows App（Remote Desktop）が必要。手順の正は [`docs/IPHONE.md`](docs/IPHONE.md)。

デモで `xm-fill:` / `xm-close:` が Issue に付くまで、本物の口座は開かない。

## ナオミチの1手

- **今夜〜マージまで**: XM に触らない。Grok が「買え」と書いたら捨てる。
- **マージした日**: Issue の `virtual-desk:` を見る。数字は仮想。XM残高ではない。
- **VPS を借りた日**: IPHONE.md の順。PAT は Grok に送らない。
