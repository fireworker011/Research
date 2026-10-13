# とらのあな（2026-10-12）

サークル行は0。

同人を含むカタログHTMLは開けた。ナビゲーションに同人誌（成年）と、ランキングポータルへのリンク `/tora_r/ec/cot/pages/all/portal/standard/ranking/1/` があった。価格帯のファセット（～500円、501円～1000円、など）もページ内にあった。

サークル単位の順位、販売数、作品数は、このポータルページからは抽出していない。ファセットの価格帯は検索UIの区分で、個別作品の価格ではない。

## 2回目（2026-10-12）

週間売上ランキングを開いた。タイトルは「週間売上ランキング - 同人誌通販のとらのあな成年向け通販」。URL は `https://ec.toranoana.jp/tora_r/ec/cot/ranking/weekly/all/`。カードは100件。販売数の数値は無く、順位は No. だけ。同一サークル1件で24件を selling（ジャンルは同人誌）にした。価格が取れた24件の中央値は950.5円。体験版・試聴の語が商品ページにあった件数は CSV の sample_available を見る。声優の語は、この24件のフラグスキャンでは立てていない（description_structure に「声優」が無い）。

not_selling は2系統。

- 同人誌（漫画）の検索は初期表示が新着順。`https://ec.toranoana.jp/tora_r/ec/app/catalog/list?searchDisplay=12&searchCategoryCode=04&searchChildrenCategoryCode=04COT001&catalogListSortType=1&currentPage=1`。週間と月間（`/cot/ranking/monthly/all/`）の取得範囲に無いサークルで、サークルページの商品リンクが3以上の16件。価格の中央値は787円（16件）。販売数は非公開。
- 同人音楽。`searchChildrenCategoryCode=04CIT009` の新着順から、商品リンク3以上の8件。ジャンルは同人音楽。ASMR とは書かない。価格の中央値は2200円（8件）。東方系の音楽サークルが含まれる。成人向け音声作品の相場としては読まない。

CD週間ランキング（`/mcd/ranking/weekly/all/`）は市販CDで、同人サークル行にはしなかった。
