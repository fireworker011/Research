# すぐ使う30本

投稿はしない。動画も声も、ここでは作らない。

絵は口の開閉だけ。声は、各行の `start_s` から `mouth_s` 秒に、あとから合わせる。せりふは声用。

## H3（猫15本）

Colab の「この1本」へ、`ready/<名前>.json` の次のキーを、同名の欄に入れる。

| JSONのキー | 欄 |
| --- | --- |
| 構成 | 構成 |
| 人 | 人 |
| 客の動物 | 客の動物 |
| ツッコミの動物 | ツッコミの動物 |
| 丁寧の動物 | 丁寧の動物 |
| 場所 | 場所 |
| セリフ | セリフ |

`構成` は stories/INDEX.md の名前。yaml は秒とショット。人、動物、場所は、この JSON。セリフ欄は `stories/<名前>_lines.txt`。空欄でも、構成の名前から同じファイルを読む。

声は `tts` の行を、役の声で読んで、`timing` の秒に合わせる。

| 役 | 声 |
| --- | --- |
| ツッコミ retort | ja-JP-KeitaNeural |
| 丁寧 polite | ja-JP-NanamiNeural |
| 客 guest | espeak:ja |
| 飼い主 owner | gtts:ja |

## いらすとや（15本）

`ready/irasutoya_*.json` を、5ビートの `tools/irasutoya-short` の `make` に渡す。読むキーは `hook`、`series_character`、`bullets`、`punchline`、`closing`。

箇条書きは3つ。1つ目の「」が相手の一言、2つ目が黒地の一文、3つ目が主人公の対抗。`closing` は空。読み上げは5行。

`timing` と `tts` は、その `make` が読み飛ばす。口の秒はここ。声はあとからこの秒に合わせる。クレジットの2.2秒は名前の表示だけ。

| 役 | 声 |
| --- | --- |
| 相手 rival | VOICEVOX:玄野武宏（style_id 11） |
| ナレーション narrator | VOICEVOX:四国めたん（style_id 2） |
| 主人公 hero | VOICEVOX:白上虎太郎（style_id 34） |

説明欄の末尾は、動画末尾と同じ VOICEVOX の名前。

## 一覧

| 名前 | 種類 | 尺 | 入力 | 投稿タイトル |
| --- | --- | --- | --- | --- |
| laundry_sock | H3 | 48.800秒 | `ready/laundry_sock.json` | 片っぽの靴下が、頭に乗っていた |
| box_seat | H3 | 47.000秒 | `ready/box_seat.json` | 空の段ボールは、中が満席だった |
| fridge_slit | H3 | 47.800秒 | `ready/fridge_slit.json` | 冷蔵庫の光で寝て、指一本だけ残した |
| curtain_slit | H3 | 47.200秒 | `ready/curtain_slit.json` | 光の筋に三匹入って、自分で影にした |
| keyboard_blank | H3 | 50.000秒 | `ready/keyboard_blank.json` | キーボードの上で丸くなって、画面は真っ白 |
| soil_nose | H3 | 50.400秒 | `ready/soil_nose.json` | 植木は無事で、鼻だけ土が残った |
| remote_bowl | H3 | 50.000秒 | `ready/remote_bowl.json` | リモコンを、四角い魚だと思った |
| mat_drag | H3 | 49.800秒 | `ready/mat_drag.json` | 乾いたマットを、自分で濡れ床へ引いた |
| rain_nose | H3 | 45.000秒 | `ready/rain_nose.json` | 雨の窓を見学して、鼻が冷えた |
| yarn_line | H3 | 45.000秒 | `ready/yarn_line.json` | 毛糸を一回たたいて、線のままにした |
| alarm_paw | H3 | 45.400秒 | `ready/alarm_paw.json` | 鳴る前に電話を止めて、また寝る |
| cushion_stack | H3 | 45.800秒 | `ready/cushion_stack.json` | クッションの山から、耳だけ出ていた |
| suitcase_tail | H3 | 45.400秒 | `ready/suitcase_tail.json` | 荷物に入って、しっぽだけ出た |
| hall_lap | H3 | 45.200秒 | `ready/hall_lap.json` | 一回だけ走ると言って、往復した |
| toy_stick | H3 | 45.000秒 | `ready/toy_stick.json` | 振らなくていいと言って、自分で持った |
| irasutoya_printer | いらすとや | 27.650秒 | `ready/irasutoya_printer.json` | 共有プリンタを占拠した相手の資料だけ、裏紙のまま配られた話 |
| irasutoya_umbrella | いらすとや | 27.650秒 | `ready/irasutoya_umbrella.json` | 勝手に傘を持った相手の椅子だけ、しずくで濡れていた話 |
| irasutoya_bento | いらすとや | 27.650秒 | `ready/irasutoya_bento.json` | 名前の無い弁当に手をつけた相手が、蓋の裏の自分の名前を見た話 |
| irasutoya_minutes | いらすとや | 27.650秒 | `ready/irasutoya_minutes.json` | 会議に遅れて結論をひっくり返した相手が、昨日の自分の文を読んだ話 |
| irasutoya_mug | いらすとや | 27.650秒 | `ready/irasutoya_mug.json` | 洗い置きのマグに注いだ相手が、一口目で塩だと顔を止めた話 |
| irasutoya_seat | いらすとや | 27.650秒 | `ready/irasutoya_seat.json` | 荷物の上に座った相手の切符が、隣の車両の指定だった話 |
| irasutoya_reply | いらすとや | 27.650秒 | `ready/irasutoya_reply.json` | 既読無視を自慢した相手の転送先が、部長の個人チャットだった話 |
| irasutoya_typo | いらすとや | 27.650秒 | `ready/irasutoya_typo.json` | 企画メモをそのまま載せた相手が、誤字を自分の工夫だと読んだ話 |
| irasutoya_trash | いらすとや | 27.650秒 | `ready/irasutoya_trash.json` | 押し付けたゴミ袋の底から、相手の名札だけ出てきた話 |
| irasutoya_elevator | いらすとや | 27.650秒 | `ready/irasutoya_elevator.json` | 満員に割り込んだ相手が、鍵のかかった倉庫の前で止まった話 |
| irasutoya_folder | いらすとや | 27.650秒 | `ready/irasutoya_folder.json` | 合言葉を聞いてきた相手が、空のフォルダを開いた話 |
| irasutoya_oversleep | いらすとや | 27.650秒 | `ready/irasutoya_oversleep.json` | 定時帰りを馬鹿にした相手だけ、朝礼の開始に改札にいた話 |
| irasutoya_receipt | いらすとや | 27.650秒 | `ready/irasutoya_receipt.json` | 混ぜた経費の一枚が、相手の昼のゲームセンターだった話 |
| irasutoya_group | いらすとや | 27.650秒 | `ready/irasutoya_group.json` | 通知を切ったつもりの相手の愚痴が、案件の全員に届いた話 |
| irasutoya_gate | いらすとや | 27.650秒 | `ready/irasutoya_gate.json` | 鼻先に止めた相手の車だけ、閉まるバーの手前で出られなくなった話 |
