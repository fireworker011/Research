# AI和装・和風美女の縦型（2026-10-13）

取得日は 2026-10-13。投稿・フォロー・コメントはしていない。再生は、その日に公開ページから読めた数だけを書く。読めなかった欄は「不明」。

## 要約

10秒の単景ループで、公開の再生が万を超えて見えたのは TikTok の1アカウントだけだった。@ai_japanese_girl1 は全9本が10秒で、中央値 6,199、最大 504,500（2026-06-22 の第1回）。第2回以降は 1,543〜12,100。情景は電車の吊り革で、着物でも月夜の庭でもない。

着物・和の情景そのものでは、10〜17秒の単景は 137〜1,819 に収まっていた。1万を超えて見えた着物題は、YouTube の 1分43秒〜3分36秒の「12ヶ月から選ぶ」動画と、2023年の4Kルックブックだった。近い文面の YouTube「シネマティックAI美女画廊」は登録 41、直近15本の中央値 56、最大 1,836（朝の祇園）。

Instagram は本日、プロフィール API が 429 で、本人以外のリール再生は取れていない。本人 @sakura_ai_beauty の前回（2026-10-12）は登録 2,749、直近6本 65〜115、中央値 102.5。@veloriasky_ は TikTok も Instagram も、この環境ではアカウントとして開かなかった。

この10秒の形のリーチは、観測できた範囲では TikTok が大きい。着物の絵で万を超えた観測は YouTube の長めの選ばせ動画側にある。同じ型のなかでは、部屋や温泉の題が着物の題を上回っていた。

## 取り方

- YouTube のチャンネル登録と直近の再生は `yt-dlp` のフラット一覧。直近15本の再生・投稿日・説明はチャンネル RSS（`feeds/videos.xml` の `media:statistics`）。検索で当たった単体は、検索結果の再生表示か `yt-dlp` 検索の `view_count`。
- 視聴ページはログイン要求で開けなかった。冒頭1秒、カメラの動き、画面内の文字、曲名は未観察。
- TikTok の再生と尺は `yt-dlp` のユーザー一覧。フォロワーはプロフィール HTML の `followerCount`。
- Instagram の `web_profile_info` は、試した4ハンドルすべて HTTP 429。

再生の中央値は、その表に書いた本数の中央値である。チャンネル全体の最大が別の題（温泉、部屋、水着、学園）のときは、その題を分けて書く。

## 参照に指定された2件

| ハンドル | 媒体 | 今日分かったこと |
|---|---|---|
| @sakura_ai_beauty | Instagram | プロフィール https://www.instagram.com/sakura_ai_beauty/ 本日の API は 429。2026-10-12 の前回 API では登録 2,749、投稿 350。直近6本の `video_view_count` は 65, 105, 115, 100, 95, 108。中央値 102.5、最大 115。尺の前回値は 10.041秒。キャプション例は「蛍をすくう川辺」。出典は前回記録 `research/account-study-2026-10/genre-サクラ.md` とリール https://www.instagram.com/reel/DeXncvVvZbr/ 。本日の再取得ではない。 |
| @veloriasky_ | TikTok / Instagram | TikTok https://www.tiktok.com/@veloriasky_ は `yt-dlp` がユーザーIDを取れず、ページの `statusCode` は 10221。Instagram も 429。別ハンドル @veloriasky（末尾アンダースコアなし）は存在し、直近は Roblox の動画（334〜1,486再生、13〜57秒）で、和装のループではない。https://www.tiktok.com/@veloriasky |

## 比較したアカウント

近い順。登録は 2026-10-13 の `yt-dlp` または TikTok HTML。YouTube の登録は表示の概数がある。

| # | ハンドル | 媒体 | 登録 | 投稿の間隔 | 直近の再生（中央値 / 最大） | 着物・和の題で見えた再生 | 型 |
|---|---|---|---|---:|---|---|---|
| 1 | @ai_japanese_girl1 | TikTok | 1,139（動画9、いいね 9,024） | 2026-06-22〜07-10 の9本。間隔の中央値 1.17日。以降の動画はこの一覧に無い | 全9本の中央値 6,199 / 最大 504,500。第1回を除く8本の中央値 5,901.5、範囲 1,543〜12,100 | 題に着物・神社・桜は無い。全員10秒の人物ループ | 10秒ループ。情景は電車 |
| 2 | @Ayu_Saeki | TikTok | 1,759（動画238、いいね 9,502） | 取得した最新20本は 2026-06-15〜06-21。6.5日で19間隔、1日あたり約2.9本。最新の公開日時は 2026-06-21 22:00 UTC | その20本の中央値 161.5 / 最大 402。尺の中央値 8.5秒（4〜19秒） | この20本の題に着物は無い。公式サイトに浴衣の写真集ページはある。そのページの再生数は無い | 短いAI美女。東京・ポートレートの文面 |
| 3 | シネマティックAI美女画廊 | YouTube | 41 | RSS15本は 2026-08-01〜10-12。8月上旬は連日、10月は 10/7・10/9・10/12 | RSS15本の中央値 56 / 最大 1,836 | 月の茶会ショート 23 と 496。祇園ショート 96 と 390。ショートタブ最大の「朝の祇園」は 1,836。同企画のロングは 208 | 詩1行のショートと、作業用BGMのスライド |
| 4 | HuneX channel | YouTube | 2,280 | RSS最新は 2025-10-20。2025-08-20 と 10/17〜10/20 に言語別でまとめて出している | RSS15本の中央値 576 / 最大 99,253 | 着物題は 263、407（日本語）、576、586（英語FHD）、1,819（韓国語）。英語FHDの検索尺は 0:17 | 17秒前後の公式ショート。アプリ紹介 |
| 5 | AI VERSE | YouTube | 750 | RSS15本は 2026-07-18〜10-11。間隔の中央値 2.0日 | RSS15本の中央値 556 / 最大 129,718 | この15本のなかの着物題は、花嫁の着物 5,535（2026-09-13）、ダークプリンセスの着物 592（08-06）、月夜の花魁 299（08-03）。検索で当たった「日本伝統色×着物」は表示 31,358、尺 2:01。RSS15本より古い | 12人・12ヶ月のASMR。和装が混ざる |
| 6 | JapanEcho AI | YouTube | 855 | RSS15本は 2025-12-12〜2026-02-28。間隔の中央値 4.5日。2026-02-28 以降はRSSに無い | RSS15本の中央値 1,363 / 最大 90,070 | 着物ドレス 3,366（2026-02-23）、どの花の着物を選ぶ 2,150（02-17）。どちらも検索尺 1:45 | 誕生花のASMR。質問形の題 |
| 7 | Naviflow ASMR | YouTube | 3,890 | RSS15本は 2025-12-14〜2026-09-12。間隔の中央値 8.0日 | RSS15本の中央値 11,621 / 最大 338,491 | 「一年を彩る着物コレクション」は検索表示 165,561、尺 1:43。この15本の題には無い。15本の最大は花のドレス 338,491 | 12ヶ月のASMR。チャンネルの中心は着物ではない |
| 8 | JivaroAI | YouTube | 不明（一覧が1本で、登録が空） | 公開動画は 2025-04-10 の1本 | 159 / 159 | その1本。検索尺 0:11。説明は、山の寺を背にした着物の若い女性、という文 | 11秒の単景。アカウントはこれだけ |
| 9 | Tanu-たぬ-【公式】 | YouTube | 694 | RSS15本は 2026-06-11〜10-10。間隔の中央値 6.5日 | RSS15本の中央値 435 / 最大 1,955 | 「雪の金閣寺と着物美人」は検索表示 137、尺 0:11。この15本は池袋・山手線・彼岸花で、題にAI着物は無い | 東京の短い風景。着物AIは検索で1本 |
| 10 | AI Fashion LookBook（音羽アイ） | YouTube | 10,500 | RSS15本は 2023-09-01〜12-23。間隔の中央値 8.5日。2023-12-23 以降はRSSに無い | RSS15本の中央値 19,651 / 最大 177,965 | 和スタイル3本は 25,143（12-05）、12,302（12-13）、13,096（12-23）。検索の別題「華麗なるAI美女！着物スタイル」は view_count 13,400、尺 1:16（`7w4o6YJZPY8`） | キャラが話すルックブック。和は3本 |
| 11 | BIJINYA★JAPAN | YouTube | 4,740 | RSSにあるのは5本、2023-05-01〜05-13。間隔の中央値 2.0日。以降はRSSに無い | 5本の中央値 50,073 / 最大 517,717 | 着物の1本は 27,989（2023-05-02）、検索尺 3:36。最大 517,717 は学生服の別動画 | 4KのAIルックブック。着物は1本 |
| 12 | AI美少女図鑑 | YouTube | 8,670 | RSS15本は 2023-04-04〜05-07。間隔の中央値 1.0日。以降はRSSに無い | RSS15本の中央値 15,503 / 最大 82,540 | 検索の「着物」は view_count 4,254、尺 61秒（`lMlZlXslMHc`）。RSSの「桜×美少女」は 9,906（2023-04-10）。最大 82,540 は百合のまとめ | テーマ別のAI美少女まとめ |
| 13 | AI生成美女図鑑 | YouTube | 547 | RSS15本は 2024-05-31〜2025-07-05。間隔の中央値 6.0日 | RSS15本の中央値 191 / 最大 617 | 2025-06-19 の浴衣の夏祭りは 149。検索の「着物美人編」は view_count 2,363、尺 92秒（`gCnCteA7Ffo`）。この15本の最大は妹の別題 617 | 図鑑。浴衣の新しい方は149 |
| 14 | AI Art あそび。 | YouTube | 1,420 | RSS15本は 2023-04-28〜09-14。間隔の中央値 6.5日。以降はRSSに無い | RSS15本の中央値 5,624 / 最大 57,998 | 浴衣女子 #1 は 1,469（2023-07-22、`__Kd__mnc9M`）。検索の「AI和服美女 #1」は view_count 2,322、尺 104秒（`Ag2VZZSlIZ4`）。最大 57,998 はスク水の別動画 | 衣装ごとのルックブック |
| 15 | AI美女量産チャンネル | YouTube | 874 | RSS15本は 2024-01-05〜01-20。間隔の中央値 0.5日。以降はRSSに無い | RSS15本の中央値 264 / 最大 3,354 | 検索の Kimono Beauty Edition は view_count 250、尺 2:10（`ppXZVYtv-Ts`） | ルックブック。着物版は250 |
| 16 | TAPPY NEST WORLD | YouTube | 48,000 | RSS15本は 2025-10-17〜2026-02-20。間隔の中央値 2.0日 | RSS15本の中央値 28,174 / 最大 371,187 | 「Kimono Dolls of the 12 Months」は検索表示 88,628、尺 1:47（`HPnQjKnU1VI`）。この15本はたい焼き・桜餅のキャラクターで、題に着物は無い。15本の最大は別のクッキング動画 | いまの投稿はキャラASMR |
| 17 | Makome's Ai Art Atelier | YouTube | 3,450 | RSS15本は 2023-11-29〜12-16。間隔の中央値 1.0日。以降はRSSに無い | RSS15本の中央値 14,823 / 最大 31,884 | 検索の kimono & yukata 2 は view_count 4,210、尺 635秒（`fzAAB5Fwng0`）。この15本の題は Girl / School Girl | 長い写真集。説明に Instagram と TikTok の案内 |
| 18 | AI様に首ったけ | YouTube | 10 | RSS15本は 2026-02-28〜05-21。間隔の中央値 1.0日。05-21 以降はRSSに無い | RSS15本の中央値 13 / 最大 130 | 検索の「AI着物美」は view_count 466、尺 1:09（`dFEz4uN0zgA`）。RSS内の着物ダンスは 14、20、37 | 短い生成テスト。再生は小さい |

登録の出典は各チャンネルの動画一覧かショート一覧を `yt-dlp` で開いたときの `channel_follower_count`。TikTok の2件はプロフィール HTML。

## 上位の動画で、文面から揃っていたこと

映像そのものは見ていない。揃っていたのは、題・説明・尺・再生の並びである。

10秒で 504,500 だったのは @ai_japanese_girl1 の第1回（2026-06-22、尺10秒、題は「吊り革に捕まる日本人女性Part1」、ハッシュタグは #電車 #美女 #japanesebeauty #japanesestyle #fyp）。同じ10秒・同じハッシュタグの第2回は 12,100、第26回は 1,543。プロフィール文は「follow me」。曲名と画面内の文字は不明。

https://www.tiktok.com/@ai_japanese_girl1/video/7654199558473469192

同じ17秒の型で、HuneX の温泉FHDは 99,253、着物の英語FHDは 586、日本語の着物ショートは 407。最大の着物題は韓国語版の 1,819。題の主題で再生が分かれている。説明はアプリ AI Gallery の紹介。

https://www.youtube.com/watch?v=mAX9LTFYCRA  
https://www.youtube.com/watch?v=XlxotxMSi4o

JapanEcho の同じ質問形で、部屋の題は 90,070、着物の題は 3,366 と 2,150。質問形にしたあとも、着物は部屋の再生に届いていない。

https://www.youtube.com/watch?v=OaCU1MrhdoY  
https://www.youtube.com/watch?v=Cs5BQ7a2fiM

検索表示で1万を超えていた着物題は、次の4本。尺は検索の length。

| 再生の表示 | 尺 | 題 | URL |
|---:|---|---|---|
| 165,561 | 1:43 | 一年を彩る着物コレクション（Naviflow） | https://www.youtube.com/watch?v=wE3Ao08_fUg |
| 88,628 | 1:47 | Kimono Dolls of the 12 Months（TAPPY） | https://www.youtube.com/watch?v=HPnQjKnU1VI |
| 31,358 | 2:01 | 日本伝統色十二か月、着物オートクチュール（AI VERSE） | https://www.youtube.com/watch?v=q7THEfLBjjc |
| 27,989 | 3:36 | Beautiful woman in Japanese kimono（BIJINYA、2023-05-02、RSSの再生も 27,989） | https://www.youtube.com/watch?v=YTIXYcrnSQs |

この4本の題は、月を選ばせるか、4Kのルックブックか、どちらかだった。10〜11秒の単景で検索に残った「山の寺」は 159、「雪の金閣寺」は 137。

https://www.youtube.com/watch?v=nPuJ9OEGTYk  
https://www.youtube.com/watch?v=1H-ri5-zTa4

シネマティックAI美女画廊の直近で一番高いのは「朝の祇園、着物サロンの開店前」1,836（2026-08-11）。同じ祇園のロングは 208。月の茶会ショートは 496（2026-10-12）と 23（10-09）。説明は、画像がAIの架空の人物であること、本編（約8分）への誘導。祇園のショート説明には本編URLに加えて Amazon の商品URLがある。そのショートは 96 と 390。

https://www.youtube.com/watch?v=bs5BFkZk714  
https://www.youtube.com/watch?v=gJaPAk9exBo  
https://www.youtube.com/watch?v=8-jHu5MMFQg

@Ayu_Saeki の直近20本は、英語の短い文（「POV: you live in tokyo」「quiet luxury kinda day」）と #aimuse #AIart #fyp。尺 4〜19秒。再生は 99〜402。プロフィールは公式サイトへの1行。この文面と尺だけでは、直近20本は400を超えていない。

https://www.tiktok.com/@ayu_saeki

音羽アイの和スタイル3本（12,302〜25,143）の説明は、本人が話しかける文と、コメントでお気に入りを聞く文。最終投稿は 2023-12-23。2026年の投稿はRSSに無い。

## この形で見てよい再生の幅

2026-10-13 に読めた数の範囲である。将来の保証ではない。

- Instagram の本人、2026-10-12 の直近6本: 65〜115。中央値 102.5。本日は取り直していない。
- TikTok の10秒、AIの日本人女性、全9本（電車）: 1,543〜12,100 が第2回以降。全本の中央値 6,199。1本だけ 504,500。
- TikTok のAI美女、4〜19秒、直近20本（Ayu、2026-06-15〜06-21、着物の題は無い）: 99〜402。中央値 161.5。
- YouTube の10〜11秒、着物の単景: 観測は 137 と 159 の2本。
- YouTube の17秒、着物の公式ショート（HuneX、言語別）: 263〜1,819。
- 活動中で文面が一番近いチャンネル（シネマ、RSS15本）: 5〜1,836。中央値 56。和の題に限ると、ショート4本は 23、96、390、496（中央値 243）、ショートタブの「朝の祇園」は 1,836。
- YouTube の着物題で1万超: 27,989（3:36、2023-05-02）、検索表示の 31,358（2:01）、88,628（1:47）、165,561（1:43）。同じチャンネルの直近中央値を、この4本の代わりに使わない。JapanEcho の着物2本は 2,150 と 3,366 で、同じ質問形の部屋動画 90,070 より低い。

登録者が多くても、直近がこの再生帯から出ている例は、今回の着物題には無かった。音羽アイは登録 10,500 で和スタイルが約1.2万〜2.5万だが、投稿は 2023-12 で止まっている。AI VERSE は登録 750 で、十二支の伝統衣装（着物とは別題）が 129,718。

## Sakura が次に並べて見る5つ

同じ10秒を1本作り、出先と題だけを変えて比べる。再生の期待値は、上の幅に置く。

1. 同じ10秒を TikTok に出す。10秒のAI日本人女性で万を超えた観測は、TikTok の9本のうちの1本だけだった。Instagram の前回6本は 65〜115。
2. 題を「第1回」にする。504,500 は Part1 で、同じ10秒の続きは 1,543〜12,100 に落ちている。見るのは、新しい連番の1本目が、続きの帯を超えるかどうか。
3. 10秒の単景を1本、1分40秒〜2分の「12ヶ月のどれ」を1本。YouTube で1万を超えた着物題は後者の尺だった。JapanEcho では同じ質問形でも着物は 2,150 と 3,366 で、部屋の 90,070 には届いていない。着物で見るなら、その2本の隣に置く。
4. ショートの1行目を場所の名にする。近いチャンネルで 1,836 だった題は「朝の祇園、着物サロンの開店前」。同じ月の詩だけのショートは 23 と 496。本数は少ない。
5. 説明は、AIの架空の人物であるという1行までにする。祇園のショートは Amazon の商品URLと本編URLを足して 96 と 390。Ayu はサイトへの1行があるが、直近20本は 99〜402。URLを増やす実験は、この並びの外側に置く。

冒頭1秒とカメラは、視聴できていないので、変える根拠が無い。

## どの媒体が、この形のリーチが大きいか

10秒のループとして再生が万を超えて見えたのは TikTok だけである。ただし観測は1アカウント、9本で、最大の1本は電車の吊り革であり、月・桜・神社・雨の庭ではない。

着物の絵で1万を超えて見えたのは YouTube で、尺は 1:43〜3:36 の選ばせ・ルックブックだった。10〜17秒の着物単景は、見えた範囲では 137〜1,819。

Instagram は本日 429 で、本人以外のリール再生がゼロのまま。本人の前回6本は 100 前後。この3つのなかで、同じ10秒を今出すなら TikTok、着物の絵を万の帯で試すなら YouTube の選ばせ1本、という分かれ方になる。

## 出典

- TikTok @ai_japanese_girl1 https://www.tiktok.com/@ai_japanese_girl1
- TikTok @Ayu_Saeki https://www.tiktok.com/@ayu_saeki
- Ayu のサイト（浴衣ページがあることまで。再生は無い） https://www.ayu-saeki.com/yukata-photoshoot-japanese-inn/
- シネマティックAI美女画廊 https://www.youtube.com/channel/UC0CsHeSXIVTdIXcFZofJY2A
- HuneX https://www.youtube.com/channel/UC1y1ZSKsjYO_4I1l064YlVA
- AI VERSE https://www.youtube.com/channel/UCjc5K9QaP0w-dK7_QC0rAbA
- JapanEcho AI https://www.youtube.com/channel/UCQat7ZPkLmPs2OyTSO7mhtA
- Naviflow ASMR https://www.youtube.com/channel/UCog0TM4oqcyrm-bUe5fBRew
- JivaroAI https://www.youtube.com/channel/UCKugHMx7FXP2ACzo8HwGVVA
- Tanu-たぬ-【公式】 https://www.youtube.com/channel/UClfBMgVebWWC04iQH-vxnFQ
- AI Fashion LookBook https://www.youtube.com/channel/UCG-pU6seFJTcRgmHYXfA2hQ
- BIJINYA★JAPAN https://www.youtube.com/channel/UCWiDon4hfCXIUvUwOELvC8g
- AI美少女図鑑 https://www.youtube.com/channel/UCbKgoEY4EuWz5zTQ3fizK4g
- AI生成美女図鑑 https://www.youtube.com/channel/UCSgpRa98tiIX8am0GnPTs5g
- AI Art あそび。 https://www.youtube.com/channel/UCPKsAWUbrYWZaYUldrY_C_w
- AI美女量産チャンネル https://www.youtube.com/channel/UCXd6y9rIL7UOcIh7EUife2A
- TAPPY NEST WORLD https://www.youtube.com/channel/UCtyNS2I53lUjJtLUr4e9pHA
- Makome's Ai Art Atelier https://www.youtube.com/channel/UCu65ZmqRgl0Q0DZT-goit1g
- AI様に首ったけ https://www.youtube.com/channel/UCsxO1bfPwkx4lWc0hlEdGXg
- 本人の前回数字 `research/account-study-2026-10/genre-サクラ.md`

RSS は `https://www.youtube.com/feeds/videos.xml?channel_id=` に、上のチャンネルIDをつないだもの。取得日はすべて 2026-10-13。
