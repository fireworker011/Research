# DiGiket

追記型。古い節は消さない。数字は取得日の公開ページだけ。正本の行は `research/adult-platform-study-2026-10/accounts.csv`。

## 2026-10-12

取得日: 2026-10-12。年齢確認は `age_check.php?declared=yes` の範囲。登録・購入はしていない。HTML は cp932。

accounts.csv は selling 64 / not_selling 17。販売数はページに無かった。selling は男性向の月間ランキング掲載。not_selling は新着で、ランキング採用サークルではなく、作品一覧3件以上だった行。DLsite の低 dl_count と同じ「売れない」とは書かない。

音声の月間は11サークル（1回目8、2回目は39位・43位・46位の3）。価格が取れた8件は550、660、770、990、1100、1100、1430、2200円。中央値1045円。3件は空欄。1回目の月間音声8件は、体験版またはストリーミング表記が8/8。秒数はほぼ空。

新着（`sort=new`）から条件を満たした追加は漫画1件だけ。音声の新着は0件。0のまま残す。KEY=voice の新着指定は、1回目の確認では無視され全件新着に寄った。

声優列は月間カードの staff リンク。役割ラベルは未保存。新着側は未取得。声優の有無としては使わない。

「ポイント15%」は、収集処理が1回目の selling 全件に足した定型文だった。ページごとの %OFF は残っていない。CSV からは削除した。ポイント還元を根拠にしない。

発売日は空欄。発売間隔は比べていない。作者自身の X は、共有ボタン `twitter.com/intent/tweet` を除くと残らなかった。

作品数は作品一覧1ページ目の作品ID数。全作品数ではない。

出典:

- `https://www.digiket.com/a/ranking_etc/_data/KEY=voice/`
- `https://www.digiket.com/a/ranking_etc/_data/KEY=comic/`
- `https://www.digiket.com/a/ranking_etc/_data/KEY=cg/`
- `https://www.digiket.com/a/ranking_etc/_data/KEY=novel/`
- `https://www.digiket.com/a/ranking_etc/_data/KEY=doujingame/`
- `https://www.digiket.com/a/result/_data/sort=new/`
