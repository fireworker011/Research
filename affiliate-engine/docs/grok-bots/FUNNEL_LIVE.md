# 申込型 公開ページ実測（参謀・2026-08-28 JST）

開封: 2026-08-28 再読。**再々読: 2026-08-28 07:51 JST**。**Hour19: 2026-08-28 08:16 JST**（sns.php HTML）。**Hour+ : 2026-08-28 08:40 JST**（教育 Threads 公開プロフィール再読。sns.php は timeout）。円は足していない。掲載媒体（YouTube の有無）はこの公開ページに無い。neo 公開IDは **`s00000018427001` のまま**。UZUZ `s00000014490001`、N高 `s00000027548001`。auひかりはこのページに無い。

出典:
- [sns.php](https://support.a8.net/as/HintOfProgram/sns.php)（SNS投稿おすすめ）
- [highprice.php](https://support.a8.net/as/HintOfProgram/ranking/highprice.php)（最終更新 2026.8.10）
- YouTube 一般ガイド: https://www.a8.net/as/youtube/（プログラム個別の掲載媒体ではない）

## いま確認する1件（貼るな）

公開タイトル: **第二/既卒/フリーター/中退/高卒の就職・転職支援【第二新卒エージェントneo】**  
置き場: sns.php「売れてる案件」  
公開プログラムID（sns.php「提携する」の `programId`）: **`s00000018427001`**  
公開の成果地点（カタログ）: 新規カウンセリング15000円 → **approved_yen に足すな**  
既存アカ: 転職（鍵 `転職_neo` は空。`accounts.json` の tenshoku `handle` は未記入）  
掲載媒体に YouTube があるか: **ファイルに無い**（ログイン後のプログラム詳細）

人間が返すのは次の1語だけ: `未提携` / `Threadsあり` / `YouTubeあり` / `項目なし` / `媒体なし`。
- `未提携` → dump `G_hq_a8_partner.txt`。承認前に貼るな
- `Threadsあり` → dump `G_hq_threads_exist.txt`（開設済み / 未開設）
- `YouTubeあり` → dump `G_hq_yt_only.txt`（Threads が欄に無い。プロフィールに置くな）。そのあと dump `G_hq_sns_nko.txt`
- `項目なし` / `媒体なし` → neo は貼るな（auひかりと同じ）。**止まれではない。** 次は N高 dump `G_hq_sns_nko.txt`

sns.php の「提携する」href は未ログインでも `detail-not-partnered`。**このメディアが未提携である証明ではない。** 提携済みかはログイン後だけ。

開くIDは `s00000018427001` だけ。次は開くな:

| 公開名 | 公開プログラムID | 理由 |
|---|---|---|
| 第二新卒向け転職エージェント【UZUZ第二新卒】 | `s00000014490001` | neo の代わりにしない |
| ネット×リアルで高卒資格＋進路実現！KADOKAWA・ドワンゴが贈る通信制高校【N高等学校】 | `s00000027548001` | 教育。neo の掲載媒体の前に開くな |

## 同じページにあるが、今夜の代入に使わない

| 公開名 | 置き場 | 使わない理由 |
|---|---|---|
| 第二新卒向け転職エージェント【UZUZ第二新卒】 | 売れてる案件 | neo の代わりにしない |
| 【auひかり】 | highprice.php | 管理画面に SNS 掲載項目なし。見るな |
| オリコで乗ーる | highprice.php | カーリース。オリコカードではない |
| 【Pappy】 | highprice.php | マッチング。使わない |
| ココナラ電話占い | sns.php / highprice | 占い。今夜の導線ではない |

## 注目案件（教育。neo の次）

公開タイトル: **ネット×リアルで高卒資格＋進路実現！KADOKAWA・ドワンゴが贈る通信制高校【N高等学校】**  
置き場: sns.php「注目案件」  
公開プログラムID: **`s00000027548001`**  
公開の成果地点（カタログ）: 新規資料請求15000円 → **足すな**  
鍵 `教育_N高` は空。neo の掲載媒体を見る前に N高を開くな。neo が `項目なし` / `媒体なし` / `YouTubeあり` のあとだけ開く。

教育 Threads は公開プロフィールが **2026-08-28 08:40 JST に実在**（表示名「はな｜小学生の習い事メモ」。ハンドルは `accounts.json`。チャットに書くな）。未開設の証明には使わない。返しは `EXIST_EDU.md` の1語。教育 YouTube は始めない（台帳 `make: never`）。N高を転職 / ペット / 副業アカに置くな。

## 一般ガイド（個別許可ではない）

A8 の YouTube ガイドは「詳細欄にリンク + PR + 有料プロモーション」と書く。YouTube アカウントのサイト登録も求める。これは **全プログラムに YouTube が載っている証明ではない**。neo の掲載媒体欄の代わりにしない。

## クリック可能な場所（確認後・指令塔が「置いてよい」と出したあと）

Secret に URL を入れただけでは円は動かない。post / insight は `claude/monthly-revenue-system-gvi02u` を checkout し、2026-08-28 時点のそのブランチは Secret を読まない（`CHECKOUT.md`）。cron を戻さなくても、次だけ人間が置ける。

| 場所 | 条件 | やるな |
|---|---|---|
| A8 副サイト | `Threadsあり` かつ `開設済み` のあと。開設済み転職 Threads だけ。公式「副サイトを登録する」 | 未開設の箱を新造。転職 YouTube。URL をチャットへ |
| 転職 Threads のプロフィールリンク欄 | Secret のあと。掲載媒体に Threads が書いてあるとき。開設済みの転職アカだけ | スレッド本文。未開設の箱。他ジャンルのアカ。cron 再開 |
| 指令塔が指名した既存 YouTube の詳細欄 | `YouTubeあり` のあと。動画を指令塔が指名したとき | 転職ジャンルの新規チャンネル（`make: never`）。ペットに neo。動画内URL。Shortsコメント |

dump: `未提携` → `G_hq_a8_partner.txt`（承認後に `G_hq_sns_next.txt` 再貼り）→ `Threadsあり` なら `G_hq_threads_exist.txt` → `開設済み` なら `G_hq_a8_site.txt` → `G_hq_secret_neo.txt` → `G_hq_threads_profile.txt`。`YouTubeあり`（Threads 無し）なら `G_hq_yt_only.txt` のあと `G_hq_sns_nko.txt`。`項目なし` / `媒体なし` なら `G_hq_sns_nko.txt`。`未開設` なら新造するな。結合するな。

N高 dump: `G_hq_sns_nko.txt` → `未提携` なら `G_hq_a8_partner_nko.txt` → `Threadsあり` なら `G_hq_edu_exist.txt` → `開設済み` なら `G_hq_a8_site_edu.txt` → `G_hq_secret_nko.txt` → `G_hq_threads_profile_edu.txt`。N高 `YouTubeあり` なら `G_hq_yt_only_nko.txt`。

## ファイルに無いもの

- ログイン後の掲載媒体欄
- 提携済みかどうか（画面を見ていない。sns.php の detail-not-partnered は未ログイン CTA）
- カタログ 15000 円が確定円になる日
- 転職 Threads のハンドル（accounts.json は未記入。トークンは engage ログで未設定。公開 fetch はアプリ誘導のみで存在は証明できない）
- 指令塔が指名する既存 YouTube 動画
- ログイン後の副サイト一覧
