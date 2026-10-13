# DLsite

追記型。古い節は消さない。数字は取得日の公開ページだけ。正本の行は `research/adult-platform-study-2026-10/accounts.csv`。共通の読み方は `patterns.md`。

## 2026-10-12

取得日: 2026-10-12。年齢確認は adultchecked クッキーの範囲だけ。登録・購入・レビューはしていない。

accounts.csv の内訳は、maniax が selling 87 / not_selling 156、がるまにが 16 / 17、BL が 18 / 5。うち maniax 音声/ASMR は selling 40 / not_selling 67。

販売数は product info ajax の dl_count。お気に入りは wishlist_count。期間ランキングの「期間販売数」とは別の数である。

### 選定

- selling は週間・30日間・累計の公開ランキング。同一サークルは最も順位が良いジャンル1件。1回目の maniax 音声は週間1ページ。2回目は週間3〜4ページ、30日間1〜2ページ、累計1ページから28サークル。
- not_selling は発売カレンダー。販売数25以下、登録日は取得時点で古い側（1回目は2026-09-28以前）、サークル作品数3以上、取得作品の最大販売数120以下。2回目の日付は 2026-08-20 から 2026-09-27。CSV の latest_sales_count は最新作品の dl_count で、enrich 後の上限は40。
- カレンダーURLの work_type 指定は無視され、全日全ジャンルが返った。ジャンルは data-work_type。SOU を音声/ASMR にした。
- 販売数の大小は選定に入っている。売れる共通点には使わない。

### 音声で残った差

- お気に入りの範囲は重ならない。selling 40件の最小810、not_selling 67件の最大114。中央値は3938.5と23。
- 表示価格の中央値は1232円と550円。範囲は重なる（最小792円、最大2464円）。1回目の週間上位12件だけでは最小990円、中央値1309円だった。
- 発売間隔の中央値は65日（間隔が取れた38件）と8日（67件）。作品数50は一覧の表示上限の可能性があり、全履歴ではない。
- 声優列は39/40と51/67。1回目の24作品は2026-10-12に声優セルを開き直して CSV と一致した。2回目の83件は開き直していない。声優セルが空のとき、収集は一覧の作者リンクを入れる。
- options の AIP は0/40と47/67。作品ページの「その他」欄を開いたのは、AIP ありの RJ01725920（「AI一部利用」）と AIP なしの RJ01719814（空欄）だけ。残りは未照合。AIP を全件「AI利用」とは書かない。
- 説明の「トラック」は34/40と26/67。1回目の10/12と3/12より差は狭い。
- 割引は28/40と38/67。1回目の週間音声は両側9/12。割引の有無を主因にしない。
- 体験版の秒数は、1回目161行の sample_length に1件も入らなかった。ファイルサイズが取れた maniax 音声は selling 7件が22.14MB〜1.09GB、not_selling 3件が1.59MB、2.05MB、7.37MB。検出は「体験版」、試聴ボタン、options の TRI、一覧の試聴アイコンのいずれかで広い。専売（DLP）は1回目の maniax 音声で両側12/12。

出典:

- `https://www.dlsite.com/maniax/ranking/week?category=voice`
- `https://www.dlsite.com/maniax/ranking/week?category=voice&page=3`
- `https://www.dlsite.com/maniax/ranking/week?category=voice&page=4`
- `https://www.dlsite.com/maniax/ranking/month?category=voice&page=1`
- `https://www.dlsite.com/maniax/ranking/month?category=voice&page=2`
- `https://www.dlsite.com/maniax/ranking/total?category=voice&page=1`
- `https://www.dlsite.com/maniax/new/=/date/2026-08-20` から `2026-09-27` の各日

### 集計に入れていないサークル

コンテュニエーション（maker_id RG01023696）。2026-10-12の product info で4作品、すべて SOU。声優欄は無く、その他欄は「AI一部利用」。表示価格は330円が1本、693円が3本。登録日は2026-10-08が3本、2026-10-11が1本。詳細は `research/adult-platform-study-2026-10/actions.md`。

https://www.dlsite.com/maniax/circle/profile/=/maker_id/RG01023696.html
