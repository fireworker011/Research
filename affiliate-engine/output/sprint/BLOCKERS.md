# 収益ブロッカー（参謀盤面・2026-08-28 JST）

目標は変えない。期限 2026-09-30・確定 ¥1,000,000。実測円は conversions.csv の approved_yen = **¥0**。
カタログ円を足さない。予想売上は書かない。

順序: **ブロッカー解消 → 高単価導線 → 計測**。指令の発出は指令塔。

## いま円を止めているもの

| 順 | 線 | 状態 | ブロッカー（ファイルにある分） | 今夜やってよいか |
|---|---|---|---|---|
| 1 | CW `fireworker12` | **run** | 08:16 JST 再読でも公開6件のみ。新規4に fireworker12 なし。13405300 応募 **13**。応募文 `CW_APPLY.md`。13406612 / 13405803 期限 **2026-08-29** | 新規4だけ。無い実績は書くな。プロフィールは直すな |
| 2 | note 手順書 980 | **run**（下書きあり・未公開） | 本文: `docs/grok-bots/note/SKU1_tejun.md`。公開URL **ファイルに無い**。今夜はD0にしない | 下書きを note に置く。公開するな |
| 3 | 秋バナー10枚 | **run**（製作済）/ 出品は未開始 | 記録: `docs/grok-bots/note/BANNER_LOG.md`。通す **10**。出品URL **ファイルに無い** | 出品するな |
| 4 | 申込型ハイチケット | **INSUFFICIENT / 未開始** | auひかりは提携済みだが 2026-08-27 管理画面に SNS/YouTube/TikTok/Threads 掲載項目なし＝貼らない。オリコカード・ガス屋のプログラム名は公式公開ページに **ファイルに無い**。オリコで乗ーるはカードではない（代入禁止） | 貼るな。応募を始めるな |
| 5 | Threads 5アカ | 稼働面。cron 停止 | links.json 空。トークン Issue #56 OPEN。投稿可否 INSUFFICIENT | 指令塔が再開を出すまで cron を戻すな |
| 6 | ペット Shorts 実験 | CONTINUE_EXPERIMENT 7/14 | video_cash_log 最終行 2026-08-22。直近7日の記録 投稿0/クリック0。**円本線としては cut**（Furbo では期限に届かない） | 型を変えるな。量産するな。CSV 追記は人間 |

## 高単価導線が止まっている理由（貼れない）

- A8 公開FAQの許可SNS: Instagram / YouTube / TikTok / Pinterest。Threads 本文は不可、プロフィールリンク欄は可。
- auひかり `s00000019044001` は管理画面に SNS 掲載項目なし＝貼らない。
- 2026-08-28 07:51 JST 再々読の [sns.php](https://support.a8.net/as/HintOfProgram/sns.php) に neo は載っている。公開プログラムID **`s00000018427001`**。掲載媒体の YouTube 可否はログイン後。確認前に貼るな。公開実測: `docs/grok-bots/FUNNEL_LIVE.md`
- 同ページの **UZUZ第二新卒** は `s00000014490001`。neo の代わりに開くな。
- 同ページ注目案件の **N高等学校** は `s00000027548001`（資料請求15000円はカタログ）。neo の前に開くな。
- neo `s00000018427001` の提携済みかは **ファイルに無い**。sns.php の「提携する」は未ログインでも detail-not-partnered。ログイン後の返しは `未提携` / YouTube 3語。未提携なら dump `G_hq_a8_partner.txt`。承認前に貼るな
- Secret の前に、開設済み転職 Threads の副サイト登録が必要（公式 FAQ post_1955）。dump `G_hq_a8_site.txt`。未開設なら登録するな
- Secret だけではクリックできない。そのあと dump `G_hq_threads_profile.txt`（プロフィールリンク欄だけ。cron は戻すな）
- post / insight / report の checkout は `claude/monthly-revenue-system-gvi02u`。sprint の `loadLinks()` は本番ジョブで動かない。実測: `docs/grok-bots/CHECKOUT.md`。プロフィール欄は Actions を通らないので重ね未マージでも置ける。重ね PR https://github.com/fireworker011/Research/pull/77 （checkout）/ https://github.com/fireworker011/Research/pull/78 （デフォルト YAML env）。どちらも draft。cron は戻していない
- 2026-08-28 08:16 JST sns.php HTML 再読でも neo 公開IDは `s00000018427001`
- 公開 Shorts 例 `umfmYHktBNk` は他チャンネル。自チャンネルの許可には使わない。
- 導線の置き場: `docs/grok-bots/FUNNEL_APPLY.md`。テンプレ鍵 `転職_neo` / `教育_N高` は空。`YouTubeあり` のあとだけ `SECRET.md` / `dump/G_hq_secret_neo.txt`。cron は戻すな。

## 計測

- 円: `data/conversions.csv` が正本。書き方: `docs/grok-bots/MEASURE.md`
- 最終実測行: **2026-08-27**。今日（2026-08-28）の行は **ファイルに無い**。実測円は ¥0 のまま（invent していない）
- 残日数・ペース: `output/sprint/TODAY.md`（`node src/sprint-1m.js`）
- ペット実験: `output/video/TODAY.md`（円に足さない）
- CW 公開実測: `output/sprint/CW_LIVE.md`
- 日次レポート cron: **stopped**。`report.js` は `approved_yen` を読む。amount_jpy は使わない

## 参謀がやらないこと

指示の発出。実投稿。アフィURLのコミット。オリコで乗ーるをオリコカードに代入。数字の発明。既応募6件への再応募指示のまま放置。
