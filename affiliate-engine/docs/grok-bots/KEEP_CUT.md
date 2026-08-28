# KEEP_CUT — 2026-08-26 夜

sprint dump 用コピー（元 `cursor/video-channel-playbook-e013`）。今夜の新規4と N は `output/sprint/CW_LIVE.md` が正。この文書の公開6件へは再応募するな。

司令部の取捨選択。工場の再構築ではない。`agents/` 本文は直していない。

前回（PR #65）の誤り: 司令部が始めた日に円が0だから CW / note / 秋バナーを rest した。それは早い。**始めていない線に rest をかけるな。** 初回サイクルが回るまで rest しない。

## 約束

- 判定は `keep` / `run` / `rest` / `cut` / `INSUFFICIENT` / `未開始`。
- 残す / 休ませる / 切る / 回すは、ファイル行か公開URLか、この文書に書いた司令部実行だけ。推論で keep 3を埋めない。
- **run は keep ではない。** 初回サイクル中の線を keep 3に入れない。
- 根拠が無ければ **INSUFFICIENT**。INSUFFICIENT を keep にしない。
- 売上予想は書かない。カタログ報酬を `approved_yen` に足さない。
- `conversions.csv` に実測の成果行が無いあいだ、実測売上は **¥0**。円0は rest 条件ではない（初回サイクル前）。
- **cut の作業意味は「投稿・応募・製作を止める」**。run は止めない。Grok Bot / Cursor エージェントの削除UIは人間だけ。
- ナオミチ意見は材料。keep 3の根拠にしない。

## 今夜の司令部実行（2026-08-26）

| 線 | 今夜やること | 今夜やらないこと | 出典 |
|---|---|---|---|
| CW | **応募再開**（ブラウザ障害の未完を含む） | `fireworker12` のプロフィールを直す | この司令部実行。ACCOUNT_NOTE.md 20行・152行 |
| 秋バナー | **10枚は製作のみ** | 出品。手順書と1記事同梱 | この司令部実行。ACCOUNT_NOTE.md 141行「未完成なら出さない」、157行 |
| note | 下書きは置く | **今夜公開しない** | ACCOUNT_NOTE.md 136行「今夜はD0にしない」、157行 項6 |

## 読んだもの（リモート）

参照ブランチ `cursor/video-channel-playbook-e013`（`4cabdfa` 時点の親 + 本修正）。クローン方針は `FETCH.md`。

| 指定 | 実体 |
|---|---|
| HQ | `docs/grok-bots/HQ_100MAN.md` |
| conversions | `data/conversions.csv`（ヘッダ + `#` コメントのみ） |
| playbook | `docs/video-channel-playbook.md` |
| ledger | `docs/grok-bots/ledger/*.md` |
| note設計 | `docs/grok-bots/ACCOUNT_NOTE.md` |
| 実験 | `docs/video-cash-loop.md` |
| 判定Issue | https://github.com/fireworker011/Research/issues/52 |

`research/` ディレクトリは無い。リポジトリ名が Research。`OFFERS.md` 本文はこのリポジトリに無い（HQ_100MAN.md 49行）。

## 期限と実測円

| 項目 | 値 | 根拠 |
|---|---|---|
| 期間 | 2026-08-26 〜 2026-09-30 | HQ_100MAN.md 9行 |
| 目標 | ¥1,000,000 | HQ_100MAN.md 10行 |
| 残日数（2026-08-26 時点） | 36（今日含む） | HQ_100MAN.md 11行 |
| `approved_yen` 合計 | 0 | conversions.csv に実測行なし。HQ_100MAN.md 18–22行 |
| 不足円 | ¥1,000,000 | HQ_100MAN.md 27行 |

司令部実測（2026-08-26 20:25 JST）の円はすべて 0 で conversions.csv と矛盾しない。円0を rest に使わない。

## 今夜 keep 3

**keep 0本。** run の3線で枠を埋めない。

`conversions.csv` に、どの線も `approved_yen` の実測行が無い。keep にする「この期限の円を出した」ファイル行も公開URLも無い。

## 状態一覧

| 線 | 状態 | rest するか | 理由の種別 |
|---|---|---|---|
| A8 / Furbo 円本線 | **cut** | — | 2ヶ月のクリック母数（HQ_100MAN.md 39行） |
| 06:00部隊 YouTube | **cut** | — | 台帳 `make: never`。チャンネル無し |
| 転職 YouTube | **cut** | — | 台帳 `make: never`（06:00リスト外だが同型） |
| PARKED ジャンルキー | **cut** | — | 「今日は起動するな」 |
| CW | **run** | しない（応募当日の契約0は未返信） | 応募は始まっている。rest は公開後または応募から7日後、かつ契約0のときだけ |
| note 手順書 | **run** | しない（公開前） | 下書きあり。今夜はD0にしない |
| 秋バナー（製作） | **run** | しない（10枚未完成） | 製作中。出品は未開始なので出品に rest をかけない |
| 秋バナー（出品） | **未開始** | かけない | 始めていない線に rest をかけるな |
| 申込型ハイチケット | **INSUFFICIENT / 未開始** | かけない | OFFERS.md 本文無し。rest にしない |
| キャッシュループ 14日実験 | 実験続行（keep ではない） | かけない | Issue #52 `CONTINUE_EXPERIMENT`。円本線は上の cut |
| Imagineペット | 上と同一チャンネル | かけない | 公開RSSの channelId が `@pet_story_select` と同じ |
| みくこんかつ | 台帳どおり（作るな） | かけない | 円0が理由ではない。ledger「今動画を作ってよいか: 不可」 |
| Threads | 稼働面。keep ではない | かけない | 円0が理由ではない。links.json は空キー |

---

## run の終了条件

売上予想は書かない。条件が満たされるまで **rest しない**。満たされても keep 3に推論で入れない。keep に移す唯一の入口は `conversions.csv` の実測 `approved_yen` 行。

### CW（run）

初回サイクルは回っていない。**応募当日は rest しない**（クライアント未返信でも契約0になる）。N=10 は分母の記録。


| 項目 | 値 | 根拠 |
|---|---|---|
| 開始 | 2026-08-26 応募 | 司令部実測。公開ページに `fireworker12` |
| いま | 応募6。契約0。売上0。追加4件はブラウザ障害で未完 | 司令部実測。公開6件は「契約した人 0」 |
| 今夜 | 応募再開。プロフィールは直さない | 今夜の司令部実行。ACCOUNT_NOTE.md 20行・152行 |
| 分母 N | **10**（提出済み6 + 未完4） | 記録用。司令部実測の件数を足しただけ。売上ではない。**rest のトリガーにしない** |
| rest に移す | （**公開後** または **その応募から7日後**）かつ **契約0**。時計はどちらか一方。契約0は必須。公開ページ「契約した人」または司令部実測 | 応募当日の契約0はクライアント未返信。N=10 提出の当夜判定にしない |
| rest しない | 応募当日。応募から7日未満。公開前。始めた日の円0。N=10 未達だけを理由にする場合 | この文書の訂正 |
| 採用率の分母 | 提出応募数。いまの記録は N=10 | 分母の記録。rest 条件ではない |
| keep に移す | conversions.csv に CW の `approved_yen` 実測行 | 契約だけの keep 入れはしない |
| 公開URL | [13406612](https://crowdworks.jp/public/jobs/13406612) / [13373869](https://crowdworks.jp/public/jobs/13373869) / [13354930](https://crowdworks.jp/public/jobs/13354930) / [13406730](https://crowdworks.jp/public/jobs/13406730) / [13397838](https://crowdworks.jp/public/jobs/13397838) / [13406417](https://crowdworks.jp/public/jobs/13406417) | 報酬表示はカタログ。足さない |

### note 手順書（run）

公開前の売上0で rest しない。

| 項目 | 値 | 根拠 |
|---|---|---|
| いま | 下書き1本。価格欄の指定 980。未公開。売上0 | 司令部実測。ACCOUNT_NOTE.md 16行 |
| 今夜 | **公開しない** | ACCOUNT_NOTE.md 136行「今夜はD0にしない」、157行 項6 |
| 1週目 N | **7日**（初回SKU公開日を D0 とした7日） | ACCOUNT_NOTE.md 136行 |
| rest に移す | **公開後**、D0 から N=7 日終了時に conversions.csv の note 実測円が 0（実測行なしを含む） | 公開前には適用しない |
| rest しない | 未公開。D0 前。始めた日の円0 | この文書の訂正 |
| keep に移す | conversions.csv に note の `approved_yen` 実測行 | 980 は価格欄であり売上ではない |
| 公開URL | 未公開のため **INSUFFICIENT** | |

### 秋バナー（製作 = run、出品 = 未開始）

| 項目 | 値 | 根拠 |
|---|---|---|
| いま | 10枚製作中。未出品。売上0 | 司令部実測 |
| 今夜 | **製作のみ** | 今夜の司令部実行 |
| 出品 | 未開始 | ACCOUNT_NOTE.md 141行「手順書の次。未完成なら出さない」。手順書は未公開 |
| 製作の観測点 | 10枚完成 | 司令部実測の枚数。完成は rest 条件ではない |
| 出品の rest | **未適用**（出品が始まっていない） | 始めていない線に rest をかけるな |
| 出品後に rest へ移す条件 | 出品公開日をそのSKUの D0 とし、ACCOUNT_NOTE.md 136行の 7日終了時に conversions.csv の素材実測円が 0 | 今夜は出品しないので使わない |
| keep に移す | conversions.csv に素材の `approved_yen` 実測行 | |
| 公開URL | 未出品のため **INSUFFICIENT** | |
| やらない | BOOTH、1記事同梱、別アカウント、価格欄を 500 / 1,480 / 1,980 / 5,000 へ変える | ACCOUNT_NOTE.md §6 |

---

## cut（残す。投稿・応募・製作を止める。削除しない）

### A8 / Furbo をこの期限の円本線にすること — cut

2ヶ月の母数がある。始めた日の円0ではない。

| 種類 | 内容 |
|---|---|
| ファイル | HQ_100MAN.md 39行: 「Furbo 購入10% / ペット癒しでは、この期限に届かない。根拠は現状 11–50 クリック / 2ヶ月」。量産や bot 分割では埋まらない。`links.json` の `ペット_Furbo` は空文字 |
| 公開URL | [A8 ペット商品ランキング](https://support.a8.net/as/HintOfProgram/ranking/pet.php)（最終更新 2026.8.10）Furbo「購入10%」。カタログ。足さない |
| 司令部実測 | 成果0 / 承認0 / 8月クリック9。円0 |
| ログ | `video_cash_log.csv` 2行 note: `A8 8月累計9`。期限の実測円にしない |
| 止める | 円本線としての A8 投稿・量産・bot分割 |

14日クリック実験のファイルは消さない（HQ_100MAN.md 61–65行）。Issue #52 は `CONTINUE_EXPERIMENT`（実験 5/14）。それは円本線 keep ではない。実験を rest にしない（開始済み）。

公開事実: `@pet_story_select` の RSS channelId は `UC65pP_901i2ERosuStSAIVw`（タイトル「ペットと暮らす小さな物語」）。Imagineペットとキャッシュループは同一チャンネル。円本線 cut は両方に効く。

### 06:00部隊（美容 / 教育 / 筋トレ / 副業 / 節約 / 睡眠）— cut

始めていない。rest ではなく cut（台帳が開始を禁じている）。

| 種類 | 内容 |
|---|---|
| ファイル | 各 `ledger/{beauty,education,bodymake,sidejob,setsuyaku,sleep}.md`: 未開設、`make: never`。`video_ledger.json` も `channel_open: false`, `make: never`。playbook 28–34行 着手禁止。`CREATE.md` 「作るな」。PARKED 例 `launch-keys/PARKED-genre-beauty.md` 5行「今日は起動するな」 |
| 司令部実測 | チャンネル無し |
| 止める | 投稿を始めない。製作を始めない。チャンネルを開かない |

転職 YouTube は 06:00 リスト外。`ledger/tenshoku.md` は同じ `make: never`。**cut**。

---

## rest しない線（円0が理由だったもの）

### みくこんかつ

rest しない。keep しない。円0を理由に止めない。新規製作は台帳が既に「不可」。

- `ledger/konkatsu.md`: 実チャンネル、未投稿1本、`ZF_C-IubJes` のチェックが先、今動画を作ってよいか: **不可**
- `video_ledger.json`（as_of 2026-08-24）は婚活 `channel_open: false` のまま。md と不一致。裁定しない（agents / ledger を直さない）
- 公開: [UCw0lvmZyj0etYPR6yPfaPyg](https://www.youtube.com/channel/UCw0lvmZyj0etYPR6yPfaPyg) / [@みくこんかつ](https://www.youtube.com/@みくこんかつ)

### Threads

rest しない。keep しない。HQ_100MAN.md 55行は稼働面 5 accounts。`links.json` は空キー（スキップ）。トークン Issue [#56](https://github.com/fireworker011/Research/issues/56) が OPEN。投稿の可否は **INSUFFICIENT**。

### 申込型ハイチケット（auひかり / オリコ / ガス屋）

**未開始。rest しない。keep しない。** HQ_100MAN.md 41–49行は寄せ先とカタログ。本文はリポジトリに無い。ここから投稿・応募を始めない（手順が INSUFFICIENT）。始めていないので rest をかけない。

---

## ナオミチ意見（材料。keep 3には未使用）

「アフィ本線にしない、CW・note・素材を先、法律は守る」

CW / note / 素材を keep 3に入れていない。今夜の実行は上の司令部実行表（応募再開・バナー製作のみ・note非公開）。法令適合のチャンネル判定はファイルに無く **INSUFFICIENT**。`COMMON.md` 18行は体験談捏造禁止（エージェント向け）。

## ファイルに無いもの

- conversions.csv の実測 `clicks` / `cv` 合計（実測行なし）
- note 公開URL、秋バナー出品URL、OFFERS.md 本文
- CW の rest を N=10 提出の当夜に出すこと（応募当日の契約0は未返信）
- どの線が 9/30 までにいくらになるか

## 削除について

cut = 投稿・応募・製作を止める。  
run = 止めない。  
Grok Bot / Cursor エージェント / 媒体アカウントの削除は **人間のUIだけ**。この文書は削除手順を書かない。
