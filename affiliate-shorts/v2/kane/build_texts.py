#!/usr/bin/env python3
"""金メモ v2 の台本・字幕・読みを書き、文字数と尺を検査する。"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# 各キューは (開始秒, 終了秒, 行のタプル)。最後のキューがPRで、長さは2秒。
VIDEOS: list[dict] = [
    {
        "id": "01",
        "title": "千分の五",
        "theme": "令和8年度、一般の事業の雇用保険で労働者が負担する料率",
        "opening": "数字から入る。最初の一声は「千分の五。」",
        "tempo": "約2.5秒の等間隔。短いカットを畳む",
        "length_sec": 22.0,
        "signature": "kane:C3-P2-T5-F1-H2-M1-B1-L1-A2",
        "look": "クリームの紙面に赤の印。中央に大きい 5/1000。明細は見出しだけが見えるよう上を切り、人物は小さく端に置く。",
        "palette": "クリーム #F3E6C8 / 朱 #B4332A / 墨 #2C2416",
        "cues": [
            (0.0, 1.6, ("千分の五。",)),
            (1.6, 3.6, ("令和八年四月から",)),
            (3.6, 5.4, ("来年の三月まで。",)),
            (5.4, 7.6, ("一般の事業なら",)),
            (7.6, 9.6, ("労働者の負担。",)),
            (9.6, 12.0, ("雇用保険は千分の五。",)),
            (12.0, 14.6, ("業種が違えば",)),
            (14.6, 17.2, ("率も変わる。",)),
            (17.2, 20.0, ("明細の行は雇用保険。",)),
            (20.0, 22.0, ("#PR", "出典は説明欄")),
        ],
        "yomi": [
            ("千分の五", "センブンノゴ", "4"),
            ("雇用保険", "コヨーホケン", "0"),
            ("令和", "レイワ", "1"),
            ("業種", "ギョーシュ", "1"),
            ("#PR", "ピーアール", "3"),
        ],
        "sources": [
            ("厚生労働省「令和8（2026）年度 雇用保険料率のご案内」", "https://www.mhlw.go.jp/content/12600000/001672913.pdf"),
            ("厚生労働省「雇用保険料率について」", "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000108634.html"),
        ],
        "says": "一般の事業では、令和8年4月1日から令和9年3月31日まで、労働者負担は 5/1,000。農林水産・清酒製造の事業と建設の事業は別の率で、園芸サービスなどの一部は一般の事業の率になる。",
        "does_not": "給与額の例、手取りの減り方、自分の明細だったという話は置かない。業種ごとの率の数字も、この本編では言わない。",
    },
    {
        "id": "02",
        "title": "半分ずつ",
        "theme": "厚生年金保険料率 18.300% と、本人と会社の折半",
        "opening": "質問から入る。最初の一声は「その年金、全部あなたの負担？」",
        "tempo": "7秒から8秒の長いカット。画面を割ったまま動かさない",
        "length_sec": 48.0,
        "signature": "kane:C2-P6-T3-F3-H1-M3-B1-L4-A6",
        "look": "左が金、右が紺の縦二分割。左に年金手帳、右に年金事務所。字幕は中央の縦書きだけで、同じ文を左右に重ねない。人物は出さない。",
        "palette": "紺 #0E1A33 / 金 #E4C36A / 生成り #F7F1DE",
        "cues": [
            (0.0, 7.0, ("その年金、", "全部あなたの負担？")),
            (7.0, 15.0, ("料率は", "18.300パーセント。")),
            (15.0, 23.0, ("平成二十九年九月から", "この率で固定。")),
            (23.0, 31.0, ("会社と本人で", "半分ずつ。")),
            (31.0, 38.0, ("本人の分は", "9.150パーセント。")),
            (38.0, 46.0, ("賞与も同じ料率。", "厚生年金基金は別。")),
            (46.0, 48.0, ("#PR", "料率は公式")),
        ],
        "yomi": [
            ("厚生年金", "コーセーネンキン", "5"),
            ("料率", "リョーリツ", "1"),
            ("18.300", "ジューハチテンサン", "0"),
            ("9.150", "キューテンイチゴ", "0"),
            ("パーセント", "パーセント", "3"),
            ("折半", "セッパン", "0"),
            ("#PR", "ピーアール", "3"),
        ],
        "sources": [
            ("日本年金機構「厚生年金保険の保険料」", "https://www.nenkin.go.jp/service/kounen/hokenryo/hoshu/20150515-01.html"),
            ("日本年金機構「厚生年金保険料額表（令和8年度版）」", "https://www.nenkin.go.jp/service/kounen/hokenryo/ryogaku/ryogakuhyo/20200825.files/R08ryougaku.pdf"),
        ],
        "says": "保険料率は 18.300% で、平成29年9月を最後に固定されている。毎月の保険料は標準報酬月額にこの率を掛け、本人と事業主で半分ずつ。折半額は 9.150%。賞与（標準賞与額）にも同じ率を掛ける。厚生年金基金の加入員は 13.300% から 15.900% で、一般の率とは別。",
        "does_not": "将来の年金額、お得、自分の等級がいくらだったかは言わない。基金の幅は説明欄にだけ書き、本編は「別」までにする。",
    },
    {
        "id": "03",
        "title": "月十五万円まで",
        "theme": "電車・バス通勤の通勤手当が非課税になる上限",
        "opening": "明細の行名から入る。最初の一声は「明細の、通勤手当。」",
        "tempo": "5秒から8秒。最後のカットだけ長く残す",
        "length_sec": 34.0,
        "signature": "kane:C6-P3-T6-F2-H6-M5-B1-L3-A3",
        "look": "ミントの地に、斜めの定期券が大きく左。電車は右上を横切る。文字は右の柱。人物は出さない。",
        "palette": "ミント #E7F6F1 / 墨 #17211F / 券の水色は素材のまま",
        "cues": [
            (0.0, 5.0, ("明細の、通勤手当。",)),
            (5.0, 11.0, ("最も経済的で", "合理的な経路。")),
            (11.0, 17.0, ("その定期代が", "非課税。")),
            (17.0, 24.0, ("月十五万円が", "上限になる。")),
            (24.0, 32.0, ("超えた分は給与。", "グリーン料金は別。")),
            (32.0, 34.0, ("#PR", "上限の出典あり")),
        ],
        "yomi": [
            ("通勤手当", "ツーキンテアテ", "4"),
            ("非課税", "ヒカゼイ", "2"),
            ("経済的", "ケーザイテキ", "3"),
            ("合理的", "ゴーリテキ", "2"),
            ("グリーン料金", "グリーンリョーキン", "5"),
            ("#PR", "ピーアール", "3"),
        ],
        "sources": [
            ("国税庁 No.2582「電車・バス通勤者の通勤手当」（令和8年4月1日現在法令等）", "https://www.nta.go.jp/taxes/shiraberu/taxanswer/gensen/2582.htm"),
        ],
        "says": "電車やバスだけを使う通勤手当は、最も経済的かつ合理的な経路・方法の定期代などが非課税。その額が月15万円を超えるときは15万円が限度で、超えた分は給与として課税される。グリーン料金は、最も経済的かつ合理的な通勤の料金とは認められない。",
        "does_not": "マイカー通勤の距離区分は別の動画（08）に置く。この本編では運賃の実額も、自分の定期だったという話もしない。",
    },
    {
        "id": "04",
        "title": "六十時間の先",
        "theme": "月60時間を超える時間外労働の割増賃金率",
        "opening": "超えたあとの話から入る。最初の一声は「六十時間を超えた分。」",
        "tempo": "短いカットから、終わりにかけて少しずつ長くする",
        "length_sec": 27.5,
        "signature": "kane:C1-P4-T2-F5-H3-M4-B1-L2-A6",
        "look": "黄と濃いグレー。中央に60。下帯に字幕。時計の針ではなく数字を主にする。",
        "palette": "黄 #F2C94C / 濃グレー #2B2B2B",
        "cues": [
            (0.0, 3.0, ("六十時間を超えた分。",)),
            (3.0, 6.2, ("通常の時間外は",)),
            (6.2, 9.4, ("二割五分以上。",)),
            (9.4, 13.2, ("月六十時間の先は",)),
            (13.2, 16.2, ("五割以上。",)),
            (16.2, 20.4, ("令和五年四月から", "規模は問わない。")),
            (20.4, 23.2, ("法定休日は数えない。",)),
            (23.2, 25.5, ("深夜と重なると足す。",)),
            (25.5, 27.5, ("#PR", "条文は説明欄")),
        ],
        "yomi": [
            ("割増", "ワリマシ", "2"),
            ("時間外", "ジカンガイ", "2"),
            ("二割五分", "ニワリゴブ", "0"),
            ("五割", "ゴワリ", "1"),
            ("法定休日", "ホーテーキュージツ", "5"),
            ("#PR", "ピーアール", "3"),
        ],
        "sources": [
            ("労働基準法第三十七条（e-Gov、時点指定 2026-09-18）", "https://laws.e-gov.go.jp/law/322AC0000000049"),
            ("厚生労働省「月60時間を超える時間外労働の割増賃金率が引き上げられます」", "https://www.mhlw.go.jp/content/12600000/001076011.pdf"),
            ("厚生労働省「法定労働時間と割増賃金について教えてください。」", "https://www.mhlw.go.jp/bunya/roudoukijun/faq_kijyungyosei07.html"),
        ],
        "says": "時間外労働の割増は通常の賃金の2割5分以上。1か月60時間を超えた時間は5割以上。中小企業も令和5年4月1日から同じ。月60時間の算定に法定休日の労働は含まれない。60時間超が深夜（原則22時から5時）にかかると、深夜の2割5分以上がさらに足される。",
        "does_not": "時給の例、自分の残業時間、未払いだったという話は置かない。法定休日以外の休日が60時間に入る点は説明欄に書く。",
    },
    {
        "id": "05",
        "title": "五日、取らせる",
        "theme": "年次有給休暇が年10日以上付与される労働者への、年5日の取得",
        "opening": "カレンダーの数字から入る。最初の一声は「カレンダーに、五日。」",
        "tempo": "紙芝居。1カット6秒から7秒で、めくらずに置く",
        "length_sec": 46.0,
        "signature": "kane:C6-P5-T1-F4-H6-M6-B1-L4-A3",
        "look": "薄紫の台紙に、日めくりを1枚ずつ置く。字幕は上の帯。人物の口は動かさない。",
        "palette": "薄紫 #E7DDF2 / 白 #F7F4FB",
        "cues": [
            (0.0, 6.0, ("カレンダーに、五日。",)),
            (6.0, 12.0, ("年休が年十日以上の人。",)),
            (12.0, 19.0, ("一年以内に", "五日、取らせる。")),
            (19.0, 26.0, ("自分で取った分も", "計画年休も、入る。")),
            (26.0, 33.0, ("五日に達していたら", "時季指定はしない。")),
            (33.0, 39.0, ("繰り越しだけでは", "義務は始まらない。")),
            (39.0, 44.0, ("見るのは、その年の付与。",)),
            (44.0, 46.0, ("#PR", "義務の出典あり")),
        ],
        "yomi": [
            ("年次有給休暇", "ネンジユーキューキューカ", "7"),
            ("年休", "ネンキュー", "1"),
            ("時季指定", "ジキシテー", "3"),
            ("計画年休", "ケーカクネンキュー", "6"),
            ("#PR", "ピーアール", "3"),
        ],
        "sources": [
            ("厚生労働省「年次有給休暇の時季指定」", "https://hatarakikatakaikaku.mhlw.go.jp/salaried.html"),
            ("厚生労働省「働き方改革って、な〜に？」年5日の解説", "https://www.check-roudou.mhlw.go.jp/study/roudousya_hatarakikatakaikaku.html"),
            ("労働基準法第三十九条第七項・第八項（e-Gov）", "https://laws.e-gov.go.jp/law/322AC0000000049"),
        ],
        "says": "法定の年次有給休暇が10日以上付与される労働者について、使用者は基準日から1年以内に5日を取得させる。本人の請求、計画年休、使用者の時季指定のどれかで5日に達すればよい。すでに5日以上取得している人には、使用者は時季指定をしない（することもできない）。義務が生まれるのは、その年に10日以上付与された場合で、繰り越し分を足して10日になった場合ではない。",
        "does_not": "取得率、罰則の金額、自分の残日数は本編に出さない。時季指定には意見聴取が要る点は説明欄に残す。",
    },
    {
        "id": "06",
        "title": "余った枠",
        "theme": "つみたて投資枠の年間120万円と、使い残しが翌年に繰り越せないこと",
        "opening": "できないことから入る。最初の一声は「余った枠は来年に足せない。」",
        "tempo": "約2.4秒で畳む。10本でいちばん短い",
        "length_sec": 19.0,
        "signature": "kane:C4-P1-T5-F1-H3-M1-B1-L1-A6",
        "look": "白地に紺の数字 120 だけを縦に積み、説明は下に1行。小物は置かない。",
        "palette": "白 #F4F7FB / 紺 #16325C",
        "cues": [
            (0.0, 2.2, ("余った枠は来年に足せない。",)),
            (2.2, 4.4, ("つみたて投資枠。",)),
            (4.4, 6.8, ("年間百二十万円。",)),
            (6.8, 9.2, ("使い残しても",)),
            (9.2, 11.6, ("翌年へは繰り越せない。",)),
            (11.6, 14.2, ("翌年も百二十万円。",)),
            (14.2, 17.0, ("それが上限。",)),
            (17.0, 19.0, ("#PR", "枠の出典あり")),
        ],
        "yomi": [
            ("つみたて投資枠", "ツミタテトーシワク", "6"),
            ("繰り越せない", "クリコセナイ", "3"),
            ("百二十万円", "ヒャクニジューマンエン", "0"),
            ("#PR", "ピーアール", "3"),
        ],
        "sources": [
            ("金融庁「NISAを知る」年間投資枠の拡大（つみたて投資枠 年間120万円）", "https://www.fsa.go.jp/policy/nisa2/know/"),
            ("政府広報オンライン「NISAって何？」未使用の年間投資枠は翌年繰り越し不可", "https://www.gov-online.go.jp/article/202401/entry-5555.html"),
        ],
        "says": "18歳以上のつみたて投資枠の年間投資枠は120万円。使い残しても翌年の枠には足せない。翌年も上限は120万円のまま。",
        "does_not": "成長投資枠、生涯の1,800万円、利回り、おすすめの商品は本編に混ぜない。令和9年1月からの未成年の枠は別制度なので、この動画の120万円には含めない。説明欄にその境界だけ書く。",
    },
    {
        "id": "07",
        "title": "引かない0.36",
        "theme": "子ども・子育て拠出金は事業主が全額負担すること",
        "opening": "天引きされない、から入る。最初の一声は「この0.36は、給料から引かない。」",
        "tempo": "短、長、中、長。均等に切らない",
        "length_sec": 30.0,
        "signature": "kane:C5-P4-T4-F6-H3-M5-B1-L2-A6",
        "look": "画面を上下に割る。上に率、下に「事業主」。吹き出しではなく、紙を二つに折った形。",
        "palette": "黄 #F6E27A / 墨 #242424",
        "cues": [
            (0.0, 4.0, ("この0.36は", "給料から引かない。")),
            (4.0, 12.0, ("子ども・子育て拠出金。",)),
            (12.0, 18.0, ("令和八年四月から", "0.36パーセント。")),
            (18.0, 28.0, ("事業主が全額負担。", "給与の天引きではない。")),
            (28.0, 30.0, ("#PR", "拠出金の出典")),
        ],
        "yomi": [
            ("子ども・子育て拠出金", "コドモコソダテキョシュツキン", "0"),
            ("0.36", "レイテンサンロク", "0"),
            ("事業主", "ジギョーヌシ", "3"),
            ("拠出金", "キョシュツキン", "3"),
            ("#PR", "ピーアール", "3"),
        ],
        "sources": [
            ("日本年金機構「厚生年金保険料額表（令和8年度版）」子ども・子育て拠出金率", "https://www.nenkin.go.jp/service/kounen/hokenryo/ryogaku/ryogakuhyo/20200825.files/R08ryougaku.pdf"),
        ],
        "says": "子ども・子育て拠出金率は令和8年4月1日から 0.36%。事業主が全額負担し、給与から被保険者分として天引きするものではない。算定の土台は、厚生年金の標準報酬月額と標準賞与額。",
        "does_not": "児童手当の受取額、自分の給与から引かれていたという話は置かない。民間の保険の話とも混ぜない。",
    },
    {
        "id": "08",
        "title": "二キロ未満",
        "theme": "マイカー・自転車通勤で片道2キロメートル未満の手当は全額課税",
        "opening": "距離から入る。最初の一声は「片道、二キロ未満。」",
        "tempo": "3秒台の中速をほぼ一定で進める",
        "length_sec": 33.0,
        "signature": "kane:C3-P1-T2-F5-H2-M2-B1-L3-A3",
        "look": "白と紺。左に距離の目盛り、右下に字幕。電車の定期は出さない（03と絵を分ける）。",
        "palette": "白 #F7F8FA / 紺 #1D3557",
        "cues": [
            (0.0, 3.2, ("片道、二キロ未満。",)),
            (3.2, 6.6, ("マイカーと自転車。",)),
            (6.6, 10.4, ("通勤手当は",)),
            (10.4, 14.6, ("全額、課税。",)),
            (14.6, 19.0, ("令和八年四月の表でも", "同じ。")),
            (19.0, 23.4, ("二キロ以上は",)),
            (23.4, 27.4, ("距離で限度が変わる。",)),
            (27.4, 31.0, ("駐車場は、別の条件。",)),
            (31.0, 33.0, ("#PR", "表は国税庁")),
        ],
        "yomi": [
            ("片道", "カタミチ", "0"),
            ("全額", "ゼンガク", "1"),
            ("課税", "カゼイ", "0"),
            ("通勤手当", "ツーキンテアテ", "4"),
            ("#PR", "ピーアール", "3"),
        ],
        "sources": [
            ("国税庁 No.2585「マイカー・自転車通勤者の通勤手当」（令和8年4月1日現在法令等）", "https://www.nta.go.jp/taxes/shiraberu/taxanswer/gensen/2585.htm"),
            ("国税庁「通勤手当の非課税限度額の改正について」（令和8年度）", "https://www.nta.go.jp/users/gensen/2026tsukin/index.htm"),
        ],
        "says": "マイカーや自転車などで通勤する人の非課税限度は距離で分かれる。片道2キロメートル未満は全額課税。この区分は令和8年4月1日以後の表でも改正前と同じ。2キロメートル以上は距離ごとの限度額がある。一定の駐車場を使う場合の加算（上限5,000円）は別の条件で、令和8年4月1日以後に支払われる手当から。",
        "does_not": "距離ごとの円額の一覧と、駐車場5,000円は本編の数字にしない。説明欄に出典とともに書く。自分の通勤距離だったという話は置かない。",
    },
    {
        "id": "09",
        "title": "賞与の頭打ち",
        "theme": "厚生年金の標準賞与額は、1か月150万円が上限",
        "opening": "欄の名前から入る。最初の一声は「賞与の欄に、上限がある。」",
        "tempo": "8秒から9秒。10本でいちばんゆっくり",
        "length_sec": 52.0,
        "signature": "kane:C3-P5-T6-F3-H6-M3-B1-L5-A2",
        "look": "薄紫の台帳。賞与の欄を大きくし、字幕は右下の付箋。人物は出さない。",
        "palette": "薄紫 #E4D7F0 / 付箋の白 #FFFcf7",
        "cues": [
            (0.0, 8.0, ("賞与の欄に、上限がある。",)),
            (8.0, 16.0, ("厚生年金の", "標準賞与額。")),
            (16.0, 24.0, ("千円未満は、切り捨て。",)),
            (24.0, 33.0, ("一ヶ月の上限は", "百五十万円。")),
            (33.0, 42.0, ("超えた分は", "計算の土台に入らない。")),
            (42.0, 50.0, ("子ども・子育て拠出金も", "同じ上限。")),
            (50.0, 52.0, ("#PR", "額表が出典")),
        ],
        "yomi": [
            ("標準賞与額", "ヒョージュンショーヨガク", "6"),
            ("厚生年金", "コーセーネンキン", "5"),
            ("百五十万円", "ヒャクゴジューマンエン", "0"),
            ("頭打ち", "アタウチ", "0"),
            ("#PR", "ピーアール", "3"),
        ],
        "sources": [
            ("日本年金機構「厚生年金保険料額表（令和8年度版）」賞与の注記", "https://www.nenkin.go.jp/service/kounen/hokenryo/ryogaku/ryogakuhyo/20200825.files/R08ryougaku.pdf"),
        ],
        "says": "賞与の保険料は、賞与額から1,000円未満を切り捨てた標準賞与額に料率を掛ける。厚生年金と子ども・子育て拠出金の標準賞与額は、1か月あたり150万円が上限。上限を超えた分は、この計算の土台に入らない。",
        "does_not": "賞与額の例、手取りがいくら減ったかは置かない。料率そのものは02の動画に置き、ここでは上限だけを話す。",
    },
    {
        "id": "10",
        "title": "夜十時から",
        "theme": "深夜労働（原則、午後10時から午前5時）の割増賃金",
        "opening": "時刻から入る。最初の一声は「夜十時から、朝五時。」",
        "tempo": "4秒から5秒の中速を、ほぼ一定で進める",
        "length_sec": 29.0,
        "signature": "kane:C1-P6-T1-F2-H2-M2-B1-L2-A3",
        "look": "暗い紺の帯を画面の上三分の一に置き、時刻だけを白くする。04の黄色とは色を分ける。",
        "palette": "夜の紺 #101828 / 白 #F4F1EA",
        "cues": [
            (0.0, 4.0, ("夜十時から、朝五時。",)),
            (4.0, 8.2, ("このあいだは、深夜。",)),
            (8.2, 12.6, ("割増は二割五分以上。",)),
            (12.6, 17.4, ("時間外と重なれば", "率は足される。")),
            (17.4, 22.6, ("休日と重なれば", "三割五分に二割五分。")),
            (22.6, 27.0, ("定める地域は", "時刻がずれる。")),
            (27.0, 29.0, ("#PR", "時刻の出典あり")),
        ],
        "yomi": [
            ("深夜", "シンヤ", "1"),
            ("割増", "ワリマシ", "2"),
            ("二割五分", "ニワリゴブ", "0"),
            ("三割五分", "サンワリゴブ", "0"),
            ("#PR", "ピーアール", "3"),
        ],
        "sources": [
            ("労働基準法第三十七条第四項（e-Gov、時点指定 2026-09-18）", "https://laws.e-gov.go.jp/law/322AC0000000049"),
            ("厚生労働省「法定労働時間と割増賃金について教えてください。」", "https://www.mhlw.go.jp/bunya/roudoukijun/faq_kijyungyosei07.html"),
        ],
        "says": "原則として午後10時から午前5時までの労働は、通常の賃金の2割5分以上の割増。時間外と重なれば合計で5割以上、法定休日と重なれば3割5分以上に2割5分以上を足して6割以上。厚生労働大臣が定める地域または期間は、午後11時から午前6時。",
        "does_not": "時給の例と、自分の夜勤だったという話は置かない。月60時間超の5割は04に置き、ここでは深夜の原則だけを話す。",
    },
]


def srt_time(sec: float) -> str:
    total_ms = int(round(sec * 1000))
    h, rem = divmod(total_ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def body_and_pr(cues: list[tuple]) -> tuple[list[tuple], tuple]:
    body = list(cues[:-1])
    pr = cues[-1]
    return body, pr


def narration_of(cues: list[tuple]) -> str:
    body, _ = body_and_pr(cues)
    lines: list[str] = []
    for _a, _b, rows in body:
        lines.extend(rows)
    return "\n".join(lines) + "\n"


def pr_of(cues: list[tuple]) -> str:
    _a, _b, rows = cues[-1]
    return "\n".join(rows) + "\n"


def srt_of(cues: list[tuple]) -> str:
    blocks: list[str] = []
    for i, (start, end, rows) in enumerate(cues, start=1):
        blocks.append(str(i))
        blocks.append(f"{srt_time(start)} --> {srt_time(end)}")
        blocks.extend(rows)
        blocks.append("")
    return "\n".join(blocks)


def script_md(v: dict) -> str:
    rows = []
    for start, end, lines in v["cues"]:
        role = "PR" if start >= v["length_sec"] - 2.01 else "本編"
        rows.append(f"| {start:.1f}–{end:.1f} | {role} | {' / '.join(lines)} |")
    src = "\n".join(f"- {name} {url}" for name, url in v["sources"])
    table = "\n".join(rows)
    return f"""# {v["id"]} {v["title"]}

金メモ v2。会社員の明細を、制度か数字の一つだけに絞る。ランキング、二人の掛け合い、スカッとの型は使わない。

- テーマ: {v["theme"]}
- 出だし: {v["opening"]}
- テンポ: {v["tempo"]}
- 長さ: {v["length_sec"]:.1f} 秒（最後の 2.0 秒が PR）
- 署名: `{v["signature"]}`
- 画面: {v["look"]}
- 色: {v["palette"]}
- 声: VOICEVOX:冥鳴ひまり（このフォルダの書き出し動画は絵だけで、音声ファイルは入れない）
- 口: 動かさない
- 本編の CTA: なし。申込、プロフィール、お得、体験は言わない
- 投稿: しない

## この本編が言うこと

{v["says"]}

## この本編が言わないこと

{v["does_not"]}

## 出典

{src}

確認日は 2026-10-18。金額と制度は上のページに書いてあるものだけを使った。

## 字幕

| 秒 | 区分 | 行 |
|---|---|---|
{table}

1行は16文字以内。PR の行は最後の2秒だけ。
"""


def description_of(v: dict) -> str:
    src = "\n".join(f"- {name}\n  {url}" for name, url in v["sources"])
    return f"""{v["title"]}

{v["says"]}

#PR
制度のメモです。体験談ではなく、収益の保証でもありません。申込リンクは置いていません。

出典（2026-10-18 に確認）
{src}

VOICEVOX:冥鳴ひまり
イラスト：いらすとや

投稿はしない。
"""


def yomi_of(rows: list[tuple[str, str, str]]) -> str:
    lines = ["表記,読み,アクセント型"]
    for surface, reading, accent in rows:
        lines.append(f"{surface},{reading},{accent}")
    return "\n".join(lines) + "\n"


def cues_ts() -> str:
    body = ["export type Cue = { start: number; end: number; lines: string[] };", "", "export const cues: Record<string, Cue[]> = {"]
    for v in VIDEOS:
        if v["id"] not in {"01", "02", "03"}:
            continue
        body.append(f"  {json.dumps(v['id'])}: [")
        for start, end, lines in v["cues"]:
            body.append(
                "    { start: %s, end: %s, lines: %s }," % (start, end, json.dumps(list(lines), ensure_ascii=False))
            )
        body.append("  ],")
    body.append("};")
    body.append("")
    return "\n".join(body)


def check() -> list[str]:
    problems: list[str] = []
    openings: list[str] = []
    themes: list[str] = []
    lengths: list[float] = []
    for v in VIDEOS:
        cues = v["cues"]
        if abs(cues[-1][0] - (v["length_sec"] - 2.0)) > 0.05:
            problems.append(f"{v['id']} PR start {cues[-1][0]} != {v['length_sec'] - 2}")
        if abs(cues[-1][1] - cues[-1][0] - 2.0) > 0.05:
            problems.append(f"{v['id']} PR is not 2.0s")
        if abs(cues[-1][1] - v["length_sec"]) > 0.05:
            problems.append(f"{v['id']} end mismatch")
        if cues[-1][1] > 58:
            problems.append(f"{v['id']} over 58s")
        prev = 0.0
        for start, end, lines in cues:
            if start < prev - 0.001 or end <= start:
                problems.append(f"{v['id']} bad range {start}-{end}")
            prev = end
            for line in lines:
                if len(line) > 16:
                    problems.append(f"{v['id']} line {len(line)} > 16: {line}")
                if len(line) == 0:
                    problems.append(f"{v['id']} empty line")
        openings.append(cues[0][2][0])
        themes.append(v["theme"])
        lengths.append(v["length_sec"])
        folder = ROOT / v["id"]
        text = (folder / "subs.srt").read_text(encoding="utf-8")
        if srt_of(cues) != text:
            problems.append(f"{v['id']} srt drift")
        if (folder / "narration.txt").read_text(encoding="utf-8") != narration_of(cues):
            problems.append(f"{v['id']} narration drift")
        if (folder / "pr_last2s.txt").read_text(encoding="utf-8") != pr_of(cues):
            problems.append(f"{v['id']} pr drift")
    if len(set(openings)) != 10:
        problems.append(f"openings not unique: {openings}")
    if len(set(themes)) != 10:
        problems.append("themes not unique")
    if len(set(lengths)) != 10:
        problems.append("lengths not unique")
    return problems


def main() -> None:
    for v in VIDEOS:
        folder = ROOT / v["id"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "script.md").write_text(script_md(v), encoding="utf-8")
        (folder / "narration.txt").write_text(narration_of(v["cues"]), encoding="utf-8")
        (folder / "pr_last2s.txt").write_text(pr_of(v["cues"]), encoding="utf-8")
        (folder / "description.txt").write_text(description_of(v), encoding="utf-8")
        (folder / "subs.srt").write_text(srt_of(v["cues"]), encoding="utf-8")
        (folder / "yomi.csv").write_text(yomi_of(v["yomi"]), encoding="utf-8")
    ts_path = ROOT.parent / "remotion" / "src" / "cues.ts"
    ts_path.parent.mkdir(parents=True, exist_ok=True)
    ts_path.write_text(cues_ts(), encoding="utf-8")
    problems = check()
    if problems:
        raise SystemExit("\n".join(problems))
    print("wrote 10 folders, cues.ts ok")


if __name__ == "__main__":
    main()
