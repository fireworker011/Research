# 収益ブロッカー（参謀盤面・2026-08-28 JST）

目標は変えない。期限 2026-09-30・確定 ¥1,000,000。実測円は conversions.csv の approved_yen = **¥0**。
カタログ円を足さない。予想売上は書かない。

順序: **ブロッカー解消 → 高単価導線 → 計測**。指令の発出は指令塔。

## いま円を止めているもの

| 順 | 線 | 状態 | ブロッカー（ファイルにある分） | 今夜やってよいか |
|---|---|---|---|---|
| 1 | CW `fireworker12` | **run** | 再読でも公開6件のみ。新規4に fireworker12 なし。応募文 `CW_APPLY.md`。13406612 期限 **2026-08-29**（応募済） | 新規4だけ。無い実績は書くな。プロフィールは直すな |
| 2 | note 手順書 980 | **run**（下書きあり・未公開） | 本文: `docs/grok-bots/note/SKU1_tejun.md`。公開URL **ファイルに無い**。今夜はD0にしない | 下書きを note に置く。公開するな |
| 3 | 秋バナー10枚 | **run**（製作）/ 出品は未開始 | ブリーフ: `docs/grok-bots/note/BANNER_10.md`。完成枚数 **ファイルに無い**。出品URL **ファイルに無い** | 製作のみ。出品するな |
| 4 | 申込型ハイチケット | **INSUFFICIENT / 未開始** | auひかりは提携済みだが 2026-08-27 管理画面に SNS/YouTube/TikTok/Threads 掲載項目なし＝貼らない。オリコカード・ガス屋のプログラム名は公式公開ページに **ファイルに無い**。オリコで乗ーるはカードではない（代入禁止） | 貼るな。応募を始めるな |
| 5 | Threads 5アカ | 稼働面。cron 停止 | links.json 空。トークン Issue #56 OPEN。投稿可否 INSUFFICIENT | 指令塔が再開を出すまで cron を戻すな |
| 6 | ペット Shorts 実験 | CONTINUE_EXPERIMENT 7/14 | video_cash_log 最終行 2026-08-22。直近7日の記録 投稿0/クリック0。**円本線としては cut**（Furbo では期限に届かない） | 型を変えるな。量産するな。CSV 追記は人間 |

## 高単価導線が止まっている理由（貼れない）

- A8 公開FAQの許可SNS: Instagram / YouTube / TikTok / Pinterest。Threads 本文は不可、プロフィールリンク欄は可。
- auひかり `s00000019044001` は管理画面に SNS 掲載項目なし＝貼らない。
- 2026-08-28 再読の [sns.php](https://support.a8.net/as/HintOfProgram/sns.php) に、SNS経由で成果が出たと書いてある申込型がある。次に確認する1件は **第二新卒エージェントneo**（売れてる案件・新規カウンセリング15000円はカタログ）。プログラム詳細の YouTube 可否はログイン後。確認前に貼るな。公開実測: `docs/grok-bots/FUNNEL_LIVE.md`
- 同ページに **UZUZ第二新卒** もある。neo の代わりにしない。
- 同ページ注目案件に **N高等学校**（資料請求15000円はカタログ）。教育アカ用。neo の前に開くな。
- 公開 Shorts 例 `umfmYHktBNk` は他チャンネル。自チャンネルの許可には使わない。
- 導線の置き場: `docs/grok-bots/FUNNEL_APPLY.md`。テンプレ鍵 `転職_neo` / `教育_N高` は空。

## 計測

- 円: `data/conversions.csv` が正本。書き方: `docs/grok-bots/MEASURE.md`
- 最終実測行: **2026-08-27**。今日（2026-08-28）の行は **ファイルに無い**。実測円は ¥0 のまま（invent していない）
- 残日数・ペース: `output/sprint/TODAY.md`（`node src/sprint-1m.js`）
- ペット実験: `output/video/TODAY.md`（円に足さない）
- CW 公開実測: `output/sprint/CW_LIVE.md`
- 日次レポート cron: **stopped**。`report.js` は `approved_yen` を読む。amount_jpy は使わない

## 参謀がやらないこと

指示の発出。実投稿。アフィURLのコミット。オリコで乗ーるをオリコカードに代入。数字の発明。既応募6件への再応募指示のまま放置。
