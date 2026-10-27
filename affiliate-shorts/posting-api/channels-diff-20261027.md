# channels.json 差分案（2026-10-27）

`channels.json` は変更していない。ここにあるのは案だけ。反映、許可、投稿はしていない。

比べた「今」は、ブランチ `cursor/posting-api-prep-ae48` の `affiliate-shorts/posting-api/channels.json`（コミット `2e12b7f5`、2026-10-26 10:46 +0900）。添付の `video/posting-api/channels.json` はこれより古い（`pet_story_select` が `active`、`kaishain_kane` と `mikukonkatsu` が無い）。古い写しの値は「今」に使っていない。

出どころは次の二つ。

- 本依頼の決定（ナオミチ、2026-10-27）。箇条書きに時刻が無いものは「時刻の記載なし」と書く。
- `daily-pipeline-20261027.md`（動画部隊の案。作成は 2026-10-27 19:31 以降 JST）。

記載どうしが食い違う行は「要確認」。その行の値は案として直していない。数は足していない。handle は先頭の `@` を付けない（`pet_story_select` の書き方に合わせる）。Chrome のプロファイルは新しいキーにせず、変える場合は `note` に書く。

`test_posting.py` の key 一覧は、2026-10-26 に足された `kaishain_kane` と `mikukonkatsu` を含む今のファイルに合わせてある。TikTok `yua` の `login_label=fireworker012` は、この差分案を反映するまでテスト側も今の値のまま。channels.json は変えていない。

## 反映する案

| key | 媒体 | 項目 | 今 | 案 | 出どころ |
|---|---|---|---|---|---|
| moto_konkatsu_miki | TikTok | login_label、note | login_label=`fireworker01`。note は「YouTubeのpet_story_selectと同じ目印。許可はTikTok側で別に取る。」handle は空。title は「元婚活難民ミキ」 | login_label=`fireworker06`。note を「Chrome Profile 1。YouTube の mikukonkatsu とは別。」にする。title は変えない。handle は空のまま（下の要確認） | 本依頼の決定（ナオミチ、2026-10-27、時刻の記載なし）「ミキのTikTok=fireworker06（Chrome Profile 1）」。daily-pipeline のライン表も「ミキ（fireworker06）＝Chrome Profile 1」。同表は今の fireworker01 を「10/25訂正前の古い記載」としている。訂正そのものの時刻は書いていない |
| kane_memo | TikTok | login_label、handle、note。title は変えない | login_label=`fireworker02`。handle は空。title は「金メモ」。note は空 | login_label=`fireworker011`。handle=`takeshiokada215`。note を「Chrome Profile 5。表示名の変更は11/1以降。それまで title は金メモのまま。」にする | 本依頼の決定（ナオミチ、2026-10-27、時刻の記載なし）「金メモTikTok=@takeshiokada215（fireworker011, Profile 5, 名前変更は11/1以降）」。daily-pipeline のライン表も同じ（「10/25に公開1本・予約1本」は実績の記載で、決定の時刻ではない） |
| yua | TikTok | login_label、handle、note | login_label=`fireworker012`。handle は空。title は「ゆあ」。note は「YouTubeの fireworker012 はチャンネル名未定の別枠。TikTokの許可はこちら。」 | login_label=`fireworker02`。handle=`yuayua112245`。note を「Chrome Profile 7。YouTube の fireworker012_reserved とは別。YouTube の行き先は未定。」にする。YouTube 側の key は変えない（下の要確認） | 本依頼の決定（ナオミチ、2026-10-27、時刻の記載なし）「ゆあTikTok=@yuayua112245（fireworker02, Profile 7）」。daily-pipeline のライン表も「@yuayua112245＝Chrome Profile 7（fireworker02）」。同表は今の fireworker012 を食い違いと呼んでいる。決定とライン表の正の記載はどちらも fireworker02 なので、この行は案にする。食い違いの相手は今のファイルの値 |
| nemuri_no_tana | YouTube | status、note | status=`active`。login_label=`fireworker011`。title は「ねむりの棚」。note は空 | status=`shelved`。note を「2026-10-23 お蔵入り。投稿先にしない。」にする。login_label と title は変えない。`shelved` は今のファイルに無い値。hold（保留）や excluded（API投稿に使わない）とは別に置く案 | 本依頼の決定（ナオミチ）「ねむりの棚はお蔵入り（10/23）」。10/23 の時刻は書いていない。daily-pipeline も「ねむりお蔵入り」が channels.json に未反映、と書いている |
| pet_chiisana_monogatari | TikTok | handle のみ | handle は空。login_label=`okadatakeshi510`。title は「ペットと暮らす小さな物語り」 | handle=`pet_mimamori222`。login_label と title は変えない。Chrome のプロファイルは足さない（下の要確認） | daily-pipeline のライン表「@pet_mimamori222（okadatakeshi510）」。本依頼の決定の箇条書きには無い。決定の時刻もライン表には無い（文書は 2026-10-27） |
| yoru_no_tana | TikTok | handle のみ | handle は空。login_label=`fireworker013`。title は「夜の棚」 | handle=`yoru_tana`。login_label と title は変えない。Chrome のプロファイルは足さない（下の要確認） | daily-pipeline のライン表「@yoru_tana（fireworker013）」。本依頼の決定の箇条書きには無い。決定の時刻もライン表には無い（文書は 2026-10-27） |

## 要確認（直さない）

| key | 媒体 | 今 | 食い違っている記載 | 扱い | 出どころ |
|---|---|---|---|---|---|
| pet_story_select と pet_kurasu_monogatari | YouTube | pet_story_select は status=`excluded`、login_label=`fireworker01`。note は「2026-10-26 ナオミチ決定: ペットYouTubeのAPI投稿先は pet_kurasu_monogatari（naomichi235）。このチャンネルはAPI投稿に使わない。」pet_kurasu_monogatari は status=`active`、login_label=`naomichi235`。note は「2026-10-26 ナオミチ決定: ペットYouTubeのAPI投稿先はここ。」 | 本依頼の決定は「API投稿先=pet_kurasu_monogatari（naomichi235, 10/26 9:48）。@pet_story_select にAPIで出さない」。今の status はこの文と一致している。一方 daily-pipeline の不明6は、この 10/26 の決定と、10/24 棚卸し「naomichi235配下の実チャンネルは@pet_story_select」が食い違う、と書いている | 要確認。status も note も変えない。10/26 9:48 は出どころの時刻であり、note の文をこの作業で書き換えない | 本依頼の決定（2026-10-26 9:48）。daily-pipeline 不明6（2026-10-27 の文書。10/24 棚卸しの時刻は文書に無い） |
| yoru_no_tana | YouTube | login_label は空。status=`hold`。handle=`夜の棚`。note は「YouTubeのGoogleアカウントは未定。許可しない。」 | 本依頼の決定は「YouTubeのアップロード許可があるのは今は fireworker01（夜の棚）だけで、テストモードのため 10/29ごろ切れる見込み」。daily-pipeline は「@夜の棚（fireworker01 の配下、10/14実画面）。channels.json は hold＝API不可」。kaishain_kane の note（2026-10-26 追加）は「fireworker01 には夜の棚と会社員の金メモの2チャンネルがある。確認まで hold」。pet_story_select の note は「fireworker01のトークンは夜の棚のものが他フォルダにコピーされた疑いあり、確認まで使わない」 | 要確認。login_label も status も変えない。10/29 は「ごろ」「見込み」であり、切れる日時としては確定していないので、日付を確定値として書かない | 本依頼の決定（ナオミチ、2026-10-27、時刻の記載なし）。daily-pipeline のライン表（10/14実画面、という記載。10/14 の時刻は無い）。channels.json の note（2026-10-26 追加。コミット `0723d1cf` と `2e12b7f5`） |
| kaishain_kane | YouTube | status=`hold`。login_label=`fireworker01`。handle=`kaishain_kane`。title は「会社員の金メモ」。2026-10-26 追加 | daily-pipeline は「channels.json は10/23版」「@kaishain_kane は未登録＝API不可」と書いている。今のファイルにはこの key がある。アップロード許可の文（上の行）は「許可があるのは夜の棚だけ」とも読める | 要確認。hold を外さない。key も消さない | daily-pipeline（2026-10-27。見た channels.json を10/23版としている）。本依頼の決定の許可の文（2026-10-27、時刻の記載なし）。ファイル上の追加日は note の 2026-10-26 |
| mikukonkatsu | YouTube | status=`hold`。login_label=`miki.konkatsu.life`。handle=`みくこんかつ`。note は「2026-10-26 ナオミチのスマホ画面で確認。OAuthクライアントJSONがまだ無い。用意できるまで許可しない」 | daily-pipeline は「ログインするGoogleアカウント不明」「channels.json に未登録＝API不可」、不明4に「@みくこんかつのログイン先」と書いている。本依頼の決定は TikTok だけで、この YouTube のログインには触れていない | 要確認。login_label を消さない。active にもしない | channels.json の note（2026-10-26。時刻はコミット `2e12b7f5` が 10:46 +0900。画面確認がその時刻とは書かれていない）。daily-pipeline 不明4（2026-10-27） |
| moto_konkatsu_miki | TikTok | handle は空 | daily-pipeline は「ハンドルは記録に無い」、不明4に「ミキ TikTok のハンドル」。本依頼の決定にもハンドルは無い（fireworker06 と Profile 1 だけ） | 要確認。handle は空のまま | daily-pipeline 不明4（2026-10-27）。本依頼の決定（2026-10-27、ハンドルの記載なし） |
| yoru_no_tana | TikTok | プロファイルの欄は無い。login_label=`fireworker013` | daily-pipeline は「Chromeプロファイル不明（10/25の一覧に fireworker013 が無い）」、不明5。本依頼の決定にプロファイルは無い | 要確認。プロファイルは足さない | daily-pipeline 不明5（2026-10-27。10/25の一覧の時刻は書いていない） |
| pet_chiisana_monogatari | TikTok | プロファイルの欄は無い。login_label=`okadatakeshi510` | daily-pipeline はプロファイルが不明、と書いている。10/26 digest は「Profile 2」、10/25の一覧では Profile 2＝fireworker01、という食い違い。不明5。本依頼の決定にペット TikTok のプロファイルは無い | 要確認。プロファイルは足さない | daily-pipeline のライン表と不明5（2026-10-27） |
| fireworker012_reserved | YouTube | status=`reserved`。title は空。login_label=`fireworker012`。note は「チャンネル名が決まるまで許可しない。TikTokのゆあとは別」 | daily-pipeline は「ゆあの YouTube の行き先は記録に無い」、不明3。本依頼の決定はゆあの TikTok だけで、YouTube の行き先は無い | 要確認。この key をゆあの投稿先にしない。status は reserved のまま | daily-pipeline 不明3（2026-10-27）。本依頼の決定（2026-10-27、YouTube の記載なし） |
| yoru_neko_camera、sonae_30、pet_kurasu_monogatari | YouTube | いずれも status=`active`（pet_kurasu_monogatari の login は naomichi235。他は各行の login_label） | 本依頼の「アップロード許可があるのは今は fireworker01（夜の棚）だけ」は、active のまま許可対象に見えるこれらの行と並ぶと読める。ペットの API 投稿先は別の決定で pet_kurasu_monogatari（上の要確認）。ねむりの棚を active のままにするかどうかは、ここでは扱わない（お蔵入りの案は別行） | 要確認。この3つの status は変えない。許可が今どのログインで有効かは、夜の棚の行と同じく確定しない | 本依頼の決定（2026-10-27、時刻の記載なし）。ペットの投稿先は 2026-10-26 9:48 |

## 差分なし

変えない。食い違いがあるものは上の「要確認」に置き、ここには置いていない。

| key | 媒体 | 今のままにする項目 | 出どころ |
|---|---|---|---|
| yoru_neko_camera | YouTube | login_label=`fireworker06`、title、status=`active`。上の要確認は「許可の文と active が並ぶこと」であり、この login_label を変える記載は無い | 本依頼の決定と daily-pipeline（どちらも 2026-10-27）に、この key の login や title を変える記載は無い |
| sonae_30 | YouTube | login_label=`fireworker04`、title、status=`active` | 同上。変える記載は無い |
| uchi_no_fukuro | TikTok | login_label=`fireworker04`、title。daily-pipeline は「H3・うちの袋は在庫なしとして扱い、この流れに入れない」と書いている。お蔵入りとは書いていない | daily-pipeline 冒頭（2026-10-27 19:31 以降の案）。本依頼の決定にお蔵入りとは無い |
| pet_kurasu_monogatari | YouTube | status=`active` と login_label=`naomichi235` は、10/26 9:48 の「API投稿先」と一致する。関係の食い違いは要確認の行。値は変えない | 本依頼の決定（2026-10-26 9:48）。daily-pipeline 不明6（2026-10-27） |
| pet_story_select | YouTube | status=`excluded` は「@pet_story_select にAPIで出さない」と一致する。関係の食い違いは要確認の行。値は変えない | 本依頼の決定（2026-10-26 9:48） |
