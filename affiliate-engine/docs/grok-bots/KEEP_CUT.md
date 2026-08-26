# KEEP_CUT — 2026-08-26 20:25 JST

司令部の取捨選択。工場の再構築ではない。`agents/` 本文は直していない。

## 約束

- 残す / 休ませる / 切るは、ファイル行か公開URLだけで決める。推論で埋めない。
- 根拠が無ければ判定そのものを **INSUFFICIENT** と書く。INSUFFICIENT を keep にしない。
- 売上予想は書かない。カタログ報酬・公開ページの報酬表示を `approved_yen` に足さない。
- `affiliate-engine/data/conversions.csv` に実測の成果行が無いあいだ、実測売上は **¥0**。
- **cut / rest の作業意味は「投稿・応募・製作を止める」**。Grok Bot や Cursor エージェントの削除UIは人間だけ。この文書は削除しない。
- ナオミチ意見は材料。判定に使わない。

## 読んだもの（リモート）

クローン方針は `docs/grok-bots/FETCH.md`（リポジトリ `fireworker011/Research`、参照ブランチ `cursor/video-channel-playbook-e013`）。ローカル作業コピーではなく、`origin/cursor/video-channel-playbook-e013`（`7d23361`）と raw を見た。

`research/` ディレクトリは **このリポジトリに無い**（`git ls-tree origin/cursor/video-channel-playbook-e013` のトップは `.cursor` `.github` `affiliate-engine`）。リポジトリ名が Research。

| 指定 | 実体 | 確認 |
|---|---|---|
| HQ | `affiliate-engine/docs/grok-bots/HQ_100MAN.md` | [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/video-channel-playbook-e013/affiliate-engine/docs/grok-bots/HQ_100MAN.md) |
| conversions | `affiliate-engine/data/conversions.csv` | [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/video-channel-playbook-e013/affiliate-engine/data/conversions.csv) |
| playbook | `affiliate-engine/docs/video-channel-playbook.md` | 同上ブランチ |
| ledger | `affiliate-engine/docs/grok-bots/ledger/*.md` | 同上ブランチ。婚活は [raw](https://raw.githubusercontent.com/fireworker011/Research/cursor/video-channel-playbook-e013/affiliate-engine/docs/grok-bots/ledger/konkatsu.md) |
| 実験 | `affiliate-engine/docs/video-cash-loop.md` | 同上ブランチ |
| 判定Issue | GitHub Issue #52 | https://github.com/fireworker011/Research/issues/52 |

`affi-shorts-agent/docs/OFFERS.md` の本文は、HQ_100MAN.md 49行が「このリポジトリに置かない」と書いており、このクローンにも無い。

## 期限と実測円

出典: `HQ_100MAN.md` 期限表・「いまの実測円」。`conversions.csv` はヘッダ + `#` コメント1行のみ。実測の成果行は無い。

| 項目 | 値 | 根拠 |
|---|---|---|
| 期間 | 2026-08-26 〜 2026-09-30 | HQ_100MAN.md 9行 |
| 目標 | ¥1,000,000 | HQ_100MAN.md 10行。カタログ単価・再生は売上ではない |
| 残日数（2026-08-26 時点） | 36（今日含む） | HQ_100MAN.md 11行。感覚で丸めない |
| `approved_yen` 合計 | 0 | conversions.csv に実測行が無い。HQ_100MAN.md 18–22行 |
| 不足円 | ¥1,000,000 | HQ_100MAN.md 27行。カタログで埋めない |
| `video_cash_log.csv` のクリック | 期限の実測円にしない | HQ_100MAN.md 31–35行 |

司令部が渡した実測（2026-08-26 20:25 JST）は、このリポジトリのファイル行ではない。円はすべて 0 で conversions.csv と矛盾しない。クリック・応募件数は下の各線に「司令部実測」と書いてファイル行と分けた。

## 今夜残す線（最大3）

**keep 0本。** 3枠を推論で埋めない。

`conversions.csv` に、どの線も `approved_yen` の実測行が無い。keep にする「この期限の円を出した」ファイル行も公開URLも無い。

ファイルが既に書いている寄せ先（auひかり / オリコ / ガス屋）は、カタログ出典 `OFFERS.md` がこのリポジトリに無く、HQ_100MAN.md 49行が「カタログを確定したと書くな」とするため、**operational keep にしない**（判定は INSUFFICIENT）。

## 切る線（投稿・応募・製作を止める）

エージェントは削除しない。

| 線 | 止めること |
|---|---|
| A8 / Furbo / ペット癒しを **この期限の円本線** にすること | 円本線としてのリンク投稿・量産・bot分割を止める |
| 06:00部隊（美容 / 教育 / 筋トレ / 副業 / 節約 / 睡眠）の YouTube | 投稿を始めない。製作を始めない。チャンネルを開かない |
| 転職 YouTube（06:00リスト外だが台帳は同型） | 投稿を始めない。製作を始めない |
| PARKED ジャンルキー | 起動しない（「今日は起動するな」） |

## 休ませる線（円本線に数えない。投稿・応募・製作を止める）

エージェントは削除しない。既存の応募取り下げ・予約キャンセルは、ファイルに手順が無いので書かない。

| 線 | 止めること |
|---|---|
| キャッシュループ `@pet_story_select`（円本線） | 円本線の投稿・製作を止める。実験ファイルは消さない |
| Imagineペット `UC65pP_901i2ERosuStSAIVw` | 上と同一チャンネル。円本線の新作Imagine製作を止める |
| みくこんかつ | 新規投稿・新規製作を止める |
| Threads 9キーの収益投稿 | リンク付き投稿を増やさない（空キーは既にスキップ） |
| CrowdWorks | **新規応募を止める** |
| note | **公開と追加製作を止める** |
| 秋バナー素材 | **出品と追加製作を止める** |
| 申込型ハイチケット | このリポジトリに案件本文が無いので、ここから投稿・応募を始めない |

14日クリック実験の手順書（`video-cash-loop.md`）と Issue #52 の `CONTINUE_EXPERIMENT` は消さない。それは今夜の100万 keep 枠に入れない。8/27 07:00 の次投稿を出す/出さないは、司令部実測と Issue #52 の「残り3本」再掲がある一方、円本線 keep ではない。**どちらが今宵の作業かはこの期限スコアでは INSUFFICIENT**（推論で予約を壊さない / 推論で100万枠に入れない）。

---

## 線ごと

判定は `keep` / `rest` / `cut` / `INSUFFICIENT`。円の列は実測のみ。予想は空欄にしない（書かない）。

### 1. A8（Furbo / ペット癒しを円本線にする）

**cut**（この期限の円本線として。エージェント削除ではない）

| 種類 | 内容 |
|---|---|
| 実測円 | ¥0。conversions.csv に実測行なし |
| ファイル | HQ_100MAN.md 39行: 「Furbo 購入10% / ペット癒しでは、この期限に届かない。根拠は現状 11–50 クリック / 2ヶ月」。41行: 量産や bot 分割では埋まらない。`config/links.json` 19行 `ペット_Furbo` は空文字 |
| 公開URL | [A8 ペット商品ランキング](https://support.a8.net/as/HintOfProgram/ranking/pet.php)（最終更新 2026.8.10）に Furbo は成果報酬「購入10%」と表示。カタログ。実測円に足さない |
| 司令部実測 | 成果0 / 承認0 / 8月クリック9。円0 |
| ログメモ | `data/video_cash_log.csv` 2行 note: `A8 8月累計9`。clicks 列の期限合計には使わない |
| 止める | 円本線としての A8 投稿・量産を止める。削除UIは触らない |

### 2. CrowdWorks

**rest**（keep の円根拠なし。3枠を埋めない。cut のファイル行も無し）

| 種類 | 内容 |
|---|---|
| 実測円 | ¥0。conversions.csv に CW 行なし。このリポジトリに CrowdWorks の台帳ファイルは無い |
| 司令部実測 | 応募6（13406612, 13373869, 13354930, 13406730, 13397838, 13406417）。契約0。売上0。追加4件はブラウザ障害で未完 |
| 公開URL | 6件とも公開ページあり。**契約した人は6件とも 0**。[13406612](https://crowdworks.jp/public/jobs/13406612) / [13373869](https://crowdworks.jp/public/jobs/13373869) / [13354930](https://crowdworks.jp/public/jobs/13354930) / [13406730](https://crowdworks.jp/public/jobs/13406730) / [13397838](https://crowdworks.jp/public/jobs/13397838) / [13406417](https://crowdworks.jp/public/jobs/13406417) |
| 公開ページの応募表示 | 6件の「最近応募したクラウドワーカー」に `fireworker12` が出ている（時刻はページ上 2026/08/26）。HQの6 IDとページは対応する。契約0は公開事実 |
| 報酬表示 | 公開ページに報酬レンジの表示がある。**カタログ。実測円に足さない。ここに金額を写して予想にしない** |
| 止める | 新規応募を止める。追加4件の応募も止め（未完のまま）。既存6件の取り下げはファイルに無い → 書かない |

### 3. note

**rest**

| 種類 | 内容 |
|---|---|
| 実測円 | ¥0。conversions.csv に note 行なし。このリポジトリに note の台帳は無い |
| 司令部実測 | 下書き1本（手順書980円）未公開。売上0 |
| 公開URL | **INSUFFICIENT**。未公開のため、このアカウントの公開記事URLを確認していない |
| 止める | 公開を止める。追加製作を止める。980円は下書きの表示であり売上ではない |

### 4. 素材（秋バナー）

**rest**

| 種類 | 内容 |
|---|---|
| 実測円 | ¥0。conversions.csv に素材行なし。このリポジトリに出品台帳は無い |
| 司令部実測 | 秋バナー10枚製作中。未出品。売上0 |
| 公開URL | **INSUFFICIENT**。未出品のため公開ページ無し |
| 止める | 出品を止める。追加製作を止める |

### 5. Imagineペット `UC65pP_901i2ERosuStSAIVw` と 6. キャッシュループ `@pet_story_select`

**同一公開チャンネル。円本線としては rest。実験ファイルは消さない。100万 keep 枠には入れない。**

| 種類 | 内容 |
|---|---|
| 実測円 | ¥0。conversions.csv に行なし。HQ_100MAN.md 18行 |
| 公開URL | `@pet_story_select` の RSS チャンネルIDは `UC65pP_901i2ERosuStSAIVw`。タイトル「ペットと暮らす小さな物語」。[チャンネル](https://www.youtube.com/channel/UC65pP_901i2ERosuStSAIVw) / [ハンドル](https://www.youtube.com/@pet_story_select)。司令部が分けた2線は、公開ページでは1チャンネル |
| ファイル（実験） | `video-cash-loop.md` 6–16行: 対象 `@pet_story_select`。登録者 107（2026-08-22、公開事実と書いてある）。本数 32 Shorts / 約2ヶ月。最多再生 5,219 は商品・PR・リンクなし |
| 公開RSS | 直近に [OBxOZp_3hg0](https://www.youtube.com/shorts/OBxOZp_3hg0) viewCount 5219（ファイルの 5,219 と一致）。RSSはこの呼び出しで15本。32本の全数確認は **INSUFFICIENT**（全件リストを取っていない） |
| 登録者の「いま」 | 公開ページのマークダウン化では登録者数が取れなかった → **INSUFFICIENT**。ファイルと司令部実測は 107 |
| 判定 | `output/video/latest.json` `verdict.canTalk1M`: false。Issue #52（2026-08-26 JST）: **CONTINUE_EXPERIMENT** 実験 5/14日目。CSVクリックは記録行1（最終 2026-08-22）で直近7日クリック0。`video-judge.js` 33–34行: 週50が3週で `canTalk1M` |
| HQ | 39行: この期限に届かない。61–65行: 実験ファイルは消さない。期限の売上トラッカーは HQ_100MAN。`video_cash_log.csv` のクリックを実測円にしない |
| playbook | 19行: 稼働チャンネルは `@pet_story_select` のみ。28–34行: TikTok / IG / 新チャンネル / A8全案件量産はゲートまで着手禁止 |
| 台帳 | `ledger/pet.md`: チャンネル `@pet_story_select`、開設はい、未投稿なし、make `one_if_clear` |
| 司令部実測 | Imagine: 1万人実験。次投稿 8/27 07:00。円の本線に数えていない。キャッシュループ: 登録107・32本。`canTalk1M` false |
| 止める | 円本線としての投稿・Imagine新作・量産を止める。ジャンル転換しない。`insight.js` をYouTubeに使わない。削除しない |

### 7. みくこんかつ

**rest**（実在は確認した。円の keep 根拠は無い）

| 種類 | 内容 |
|---|---|
| 実測円 | ¥0。conversions.csv に行なし |
| ファイル | `ledger/konkatsu.md` 6–14行: チャンネル「元婚活難民ミキ【6年→8ヶ月で入籍】」(`UCw0lvmZyj0etYPR6yPfaPyg` / `@みくこんかつ`)。開設はい。未投稿 `konkatsu_app_fatigue_01/reel.mp4`。直近投稿 2026-08-23 `ZF_C-IubJes`。投稿チェックなし。**今動画を作ってよいか: 不可**。準備レシピの量産禁止 |
| ファイルの食い違い | `data/video_ledger.json` 15–23行（as_of 2026-08-24）は婚活 `channel: null`, `channel_open: false`, `make: never`。ledger md（更新 2026-08-26）と不一致。どちらを「今の稼働」とするかの裁定は、この文書ではしない（agents / ledger を直さない） |
| HQ | 53–55行: 稼働面に YouTube みくこんかつ。新しいチャンネルを開くな |
| playbook | 31行: 婚活などの新チャンネルはゲート突破まで着手禁止 |
| 公開URL | [チャンネル](https://www.youtube.com/channel/UCw0lvmZyj0etYPR6yPfaPyg) / [ハンドル](https://www.youtube.com/@みくこんかつ) タイトル一致。RSS直近 [ZF_C-IubJes](https://www.youtube.com/shorts/ZF_C-IubJes)（2026-08-23、viewCount 341）。RSSはこの呼び出しで6本 |
| 司令部実測 | 実在。未投稿パケットあり |
| 止める | 新規投稿を止める。新規製作を止める（台帳も「不可」）。未投稿1本を上げるかは、台帳が「ZF_C-IubJes のチェックが先」と書いており、円本線 keep にはしない |

### 8. 06:00部隊（美容 / 教育 / 筋トレ / 副業 / 節約 / 睡眠）

**cut**（開始しない = 投稿・製作を止める）

| 種類 | 内容 |
|---|---|
| 実測円 | ¥0。conversions.csv に行なし |
| ファイル | 各 `ledger/{beauty,education,bodymake,sidejob,setsuyaku,sleep}.md`: チャンネル未開設、`make: never`、今動画を作ってよいか: 不可、準備レシピを量産するな。`video_ledger.json` も各 `channel_open: false`, `make: never`。playbook 28–34行 着手禁止。`CREATE.md` 11–17行「今生成してよいもの: 作るな」。PARKED キー例 `launch-keys/PARKED-genre-beauty.md` 5行: 「今日は起動するな」 |
| 公開URL | 06:00各ジャンルの自社チャンネルURLは **INSUFFICIENT**（台帳が未開設） |
| 司令部実測 | チャンネル無し |
| 止める | 投稿を始めない。製作を始めない。チャンネルを開かない。エージェント削除はしない |

転職は司令部の06:00リストに無い。`ledger/tenshoku.md` は同じ「未開設 / make: never」。**cut**（始めない）。

### 9. Threads（HQの稼働面）

**rest**（円本線 keep の根拠なし）

| 種類 | 内容 |
|---|---|
| 実測円 | ¥0。conversions.csv に Threads 行なし |
| ファイル | HQ_100MAN.md 55行: Threads 5 accounts（`config/accounts.json` コメントの開設済み5。9キー全部が稼働面ではない）。`accounts.json` 2行コメント「全5アカウント開設済み」。`links.json` の案件キーはすべて空文字。空キーは投稿時スキップ（ファイルコメント） |
| GitHub | トークン更新 Issue が OPEN（例: [#56](https://github.com/fireworker011/Research/issues/56)）。投稿が今動いているかは **INSUFFICIENT** |
| 止める | リンク付き収益投稿を増やさない。アカウント削除はしない |

### 10. 申込型ハイチケット（auひかり / オリコ / ガス屋）

**INSUFFICIENT**（寄せ先はファイルにある。今夜の keep 作業にはしない）

| 種類 | 内容 |
|---|---|
| 実測円 | ¥0。conversions.csv に行なし |
| ファイル | HQ_100MAN.md 41–49行: 寄せ先は申込型ハイチケット。数字はカタログ。自前 CV ではない。実測円に足すな。出典 `affi-shorts-agent/docs/OFFERS.md`。**このリポジトリに本文は置かない。カタログを確定したと書くな** |
| 公開URL（このクローンで本文確認） | **INSUFFICIENT**。OFFERS.md が無い |
| 止める | このリポジトリから、確認できない案件の投稿・応募を始めない |

## ナオミチ意見（材料。判定に未使用）

「アフィ本線にしない、CW・note・素材を先、法律は守る」

使わなかった。CW / note / 素材を keep 3に入れる根拠にはしていない。法令の適合判定も、このリポジトリに「みくこんかつが合法/違法」と書いた行は無く **INSUFFICIENT**。ボット契約 `COMMON.md` 18行は体験談の捏造禁止（エージェント向け）。チャンネル本文は直していない。

## ファイルに無いもの（転記しない）

- conversions.csv の実測 `clicks` / `cv` 合計（実測行なし。0件と書いてあるわけではない — HQ_100MAN.md 23–24行）
- 登録者の公開ページ上の「いま」の数（取得できず）
- note 公開URL、秋バナー出品URL、OFFERS.md 本文
- CrowdWorks の自前契約・売上（公開ページは契約0。司令部も契約0 売上0）
- どの線が 9/30 までにいくらになるか

## 削除について

切る / 休ませる = 投稿・応募・製作を止める。  
Grok Bot の削除、Cursor エージェントの削除、YouTube / Threads アカウント削除は **人間のUIだけ**。この文書は削除手順を書かない。
