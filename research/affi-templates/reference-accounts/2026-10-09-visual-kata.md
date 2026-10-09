# 2026-10-09 visual-kata（絵の作り方の実測）

- 作成：市場リサーチ（2026-10-09 JST）。数字は実測、目で見て数えたものは「観察」。推測は書かない。取れないものは「不明」。
- 道具：yt-dlp 2026.09.27（TikTok・YouTubeの公開ページ）、ffmpeg（scene>0.3 で切れ目検出、フレーム抽出）、目視（抽出フレームを見る）。ログインなし。
- 作業ファイル：箱の /workspace/video-audit-1009/（動画・フレーム・シート）。

## 0. 対象の選び方（実測）
- 2026-10-09 12:3x JST に各プロフィールの一覧を yt-dlp で取得（junjun 10本／the.care.logic 83本／yako 47本／nuts0629 190本）。再生数はこの時点の値（TikTok表示の丸め値）。
- 2026-10-03 以前（投稿から6日以上）の動画を再生順に並べ、上位3本＋下位2本。junjun と yako は、最初に2026-10-02 締めで選んで計測済みだった4位の1本も「参考」として残した（6本）。
- nuts0629 は最新投稿が 2026-01-31。下位2本は 2025-06 のごく初期の投稿。yako の下位2本も 2026-07 の初期投稿（現在と形式が違う）。上位と下位は時期も形式も違う点に注意。

## 1. 動画ごとの集計（shots_*.csv から）

| アカウント | 動画ID | 区分 | 再生 | 投稿日 | 尺(秒) | 切れ目検出 scene>0.3 のショット数 | 目視で追加した場面替わり | 動きのあるショットの平均「動きの数」 | 10秒あたり動きの数 | 動きのあるショットの平均秒数 | 種別 | 出典 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| @the.care.logic | 7677586914253507858 | 上位1 | 1,400,000 | 2026-08-24 | 28.2 | 3 | 0 | 3 | 3.19 | 9.4 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@the.care.logic/video/7677586914253507858 |
| @the.care.logic | 7663785920939740424 | 上位2 | 504,800 | 2026-07-18 | 40.1 | 9 | 0 | 1.75 | 3.49 | 5.0 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@the.care.logic/video/7663785920939740424 |
| @the.care.logic | 7654945834039102727 | 上位3 | 285,600 | 2026-06-24 | 56.07 | 3 | 0 | 3.5 | 1.25 | 28.0 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@the.care.logic/video/7654945834039102727 |
| @the.care.logic | 7689722804769393938 | 下位2 | 778 | 2026-09-26 | 30.03 | 4 | 0 | 3 | 3.0 | 9.99 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@the.care.logic/video/7689722804769393938 |
| @the.care.logic | 7689089480808041735 | 下位1 | 768 | 2026-09-24 | 37.27 | 2 | 0 | 3 | 1.61 | 18.63 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@the.care.logic/video/7689089480808041735 |
| @yako.shiawasekon | 7692202183814581524 | 上位1 | 237,800 | 2026-10-03 | 59.73 | 16 | 0 | 2.08 | 4.52 | 4.55 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@yako.shiawasekon/video/7692202183814581524 |
| @yako.shiawasekon | 7690523678567615764 | 上位2 | 223,900 | 2026-09-28 | 179.17 | 34 | 10 | 2.09 | 3.85 | 5.43 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@yako.shiawasekon/video/7690523678567615764 |
| @yako.shiawasekon | 7689595690397224212 | 上位3 | 93,300 | 2026-09-26 | 122.87 | 31 | 3 | 1.76 | 4.15 | 4.06 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@yako.shiawasekon/video/7689595690397224212 |
| @yako.shiawasekon | 7691824225895615765 | 参考(4位) | 84,900 | 2026-10-02 | 56.01 | 18 | 0 | 2.06 | 6.25 | 3.21 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@yako.shiawasekon/video/7691824225895615765 |
| @yako.shiawasekon | 7666588350878321941 | 下位2 | 864 | 2026-07-26 | 12.07 | 3 | 0 | 2 | 4.97 | 4.02 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@yako.shiawasekon/video/7666588350878321941 |
| @yako.shiawasekon | 7666304080490433813 | 下位1 | 847 | 2026-07-25 | 18.53 | 1 | 0 | 4 | 2.16 | 18.53 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@yako.shiawasekon/video/7666304080490433813 |
| @junjun_ranran | 7692378853490167046 | 上位1 | 1,800,000 | 2026-10-03 | 71.55 | 20 | 3 | 1.74 | 4.61 | 3.74 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@junjun_ranran/video/7692378853490167046 |
| @junjun_ranran | 7690894121547861254 | 上位2 | 630,400 | 2026-09-29 | 37.48 | 2（暗い映像のため scene>0.1 で 8） | 0 | 1.71 | 3.2 | 5.32 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@junjun_ranran/video/7690894121547861254 |
| @junjun_ranran | 7655625158299897108 | 上位3 | 407,000 | 2026-06-26 | 25.45 | 5 | 2 | 2.5 | 3.93 | 6.12 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@junjun_ranran/video/7655625158299897108 |
| @junjun_ranran | 7670122320844967189 | 参考(4位) | 365,200 | 2026-08-04 | 95.96 | 5（暗い映像のため scene>0.1 で 14） | 5 | 1.64 | 2.4 | 6.85 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@junjun_ranran/video/7670122320844967189 |
| @junjun_ranran | 7655019299546926357 | 下位2 | 148,300 | 2026-06-25 | 17.83 | 6 | 1 | 1.5 | 5.05 | 2.97 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@junjun_ranran/video/7655019299546926357 |
| @junjun_ranran | 7661624277401128209 | 下位1 | 87,900 | 2026-07-12 | 127.59 | 19 | 10 | 2 | 2.82 | 7.08 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@junjun_ranran/video/7661624277401128209 |
| @nuts0629 | 7533937942935440648 | 上位1 | 1,300,000 | 2025-08-02 | 8.01 | 1 | 0 | 2 | 2.5 | 8.01 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@nuts0629/video/7533937942935440648 |
| @nuts0629 | 7536538803377310983 | 上位2 | 765,500 | 2025-08-09 | 8.01 | 1 | 0 | 2 | 2.5 | 8.01 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@nuts0629/video/7536538803377310983 |
| @nuts0629 | 7517051675677429010 | 上位3 | 541,200 | 2025-06-18 | 5.11 | 1 | 0 | 2 | 3.92 | 5.11 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@nuts0629/video/7517051675677429010 |
| @nuts0629 | 7515055931919486226 | 下位2 | 562 | 2025-06-12 | 19.7 | 3 | 0 | 2.5 | 2.54 | 8.93 | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@nuts0629/video/7515055931919486226 |
| @nuts0629 | 7515363273139555592 | 下位1 | 527 | 2025-06-13 | 12.77 | 1 | 4 | 0（動きなし） | 0.0 | — | 実測（秒・本数）／観察（動き） | https://www.tiktok.com/@nuts0629/video/7515363273139555592 |

- 「動きの数」は1ショットの中で目で見えた動作を動詞で数えたもの（話す・振り向く・泣く…）。表紙1枚・黒地の文字・最後の数フレームなど動きゼロのショットは平均から外した。
- scene>0.3 は暗い映像・溶けるような切り替え・似た背景の連続で切れ目を拾えない。拾えなかった場面替わりは csv の「カメラ」欄に「目視で場面替わりN」と書いた。
## 2. 答え：「伸びた回は、1ショットの動きの数が少ないか」

| 事実 | 種別 | 出典 |
|---|---|---|
| 4アカウント合計：上位3本の動きのあるショット121本の平均 1.97（中央値2、3以上は24本＝20%）。下位2本の35本の平均 2.14（中央値2、3以上は9本＝26%）。参考(4位)31本は平均 1.87。 | 観察（目視で数えた動き）／実測（ショット数） | shots_*.csv |
| @the.care.logic：上位 13ショット 平均2.31（3以上 46%）／下位 5ショット 平均3.0（3以上 100%）。 | 観察 | shots_the.care.logic.csv |
| @yako.shiawasekon：上位 75ショット 平均1.96（3以上 16%）／下位 4ショット 平均2.5（3以上 25%）。下位はショット数が4しかない。 | 観察 | shots_yako.shiawasekon.csv |
| @junjun_ranran：上位 30ショット 平均1.83（3以上 20%）／下位 24ショット 平均1.88（3以上 8%）。ほぼ同じ。 | 観察 | shots_junjun_ranran.csv |
| @nuts0629：上位3本は各1ショット（8.0／8.0／5.1秒）で動き2ずつ。下位は 2ショット平均2.5と、動きゼロの静止画つなぎ1本。 | 観察 | shots_nuts0629.csv |
| 結論：中央値はどちらも2で同じ。平均では上位のほうが少し少ない（1.97 対 2.14）。差がはっきりしているのは the.care.logic（2.31 対 3.0）だけ。junjun では差がない。下位はショット数が少なく（35本）、時期・形式も違うので、「動きが少ないから伸びた」とは言えない。 | 観察からの集計 | 上記 |
| 1本の中の長さ：上位の動きのあるショットの平均秒数は 3.7〜9.4秒（the.care.logic の 28.0秒の1本を除く）。上位の多くは1ショット2〜6秒。 | 実測 | 表1 |

## 3. 冒頭0〜2秒（0.0／0.5／1.0／2.0秒のフレーム）

画像：frames/{account}/{動画ID}_open_0-2s.jpg（4枚を横に並べたもの）。主役の画面高は目測（10%刻み程度）。

| アカウント | 動画ID | 区分 | 再生 | 主役 | 主役の画面高 | 感情 | 文字 | 種別 | 画像 |
|---|---|---|---|---|---|---|---|---|---|
| @the.care.logic | 7677586914253507858 | 上位1 | 1,400,000 | 子宮キャラ1体（正面・全身） | 約55% | 悲しい（涙目・手を組む） | なし（透かし「The Care Logic」のみ） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/the.care.logic/7677586914253507858_open_0-2s.jpg |
| @the.care.logic | 7663785920939740424 | 上位2 | 504,800 | 玉ねぎキャラ＋少女 | 0.0〜1.0秒 玉ねぎ約30%・少女約50%／2.0秒 玉ねぎ約55% | 怒る・叫ぶ（玉ねぎ、2.0秒）／困る（少女が頭を抱える） | なし（背景の貼り紙のみ） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/the.care.logic/7663785920939740424_open_0-2s.jpg |
| @the.care.logic | 7654945834039102727 | 上位3 | 285,600 | 美容液ボトルキャラ | 約50%→2.0秒 約70% | なし→笑う | あり（0.0秒 大きなビルマ語題字、0.5秒以降 上部に小さな題字「All-rounder Skincare… (Part-1)」） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/the.care.logic/7654945834039102727_open_0-2s.jpg |
| @the.care.logic | 7689722804769393938 | 下位2 | 778 | 玉座のドリアン王 | 約35% | なし（得意げ） | あり（0.0秒のみ 大きなビルマ語題字） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/the.care.logic/7689722804769393938_open_0-2s.jpg |
| @the.care.logic | 7689089480808041735 | 下位1 | 768 | チョコドーナツキャラ（冷蔵庫） | 約30% | なし（にやり顔） | なし（透かしのみ） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/the.care.logic/7689089480808041735_open_0-2s.jpg |
| @yako.shiawasekon | 7692202183814581524 | 上位1 | 237,800 | 男女の後ろ姿（夜の街） | 約75% | なし | あり（上部に題字「友達から恋人になる瞬間」＋0.5秒からせりふ字幕） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/yako.shiawasekon/7692202183814581524_open_0-2s.jpg |
| @yako.shiawasekon | 7690523678567615764 | 上位2 | 223,900 | 男女2人（歩く） | 約75% | 戸惑い（女性） | あり（上部に題字2行＋せりふ字幕） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/yako.shiawasekon/7690523678567615764_open_0-2s.jpg |
| @yako.shiawasekon | 7689595690397224212 | 上位3 | 93,300 | 男女2人（夜景） | 約70% | なし | あり（題字「ショートドラマ 結婚相手に気づいて欲しい違和感」＋せりふ字幕） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/yako.shiawasekon/7689595690397224212_open_0-2s.jpg |
| @yako.shiawasekon | 7691824225895615765 | 参考(4位) | 84,900 | 格子越しの男→2.0秒 女 | 約60〜70% | なし | あり（題字「初デートがここの理由」、2.0秒からせりふ字幕） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/yako.shiawasekon/7691824225895615765_open_0-2s.jpg |
| @yako.shiawasekon | 7666588350878321941 | 下位2 | 864 | カフェの男女（座る） | 各約45% | なし | あり（題字「誠実だけどつまらない男性」＋せりふ字幕） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/yako.shiawasekon/7666588350878321941_open_0-2s.jpg |
| @yako.shiawasekon | 7666304080490433813 | 下位1 | 847 | 駅前の男女（全身） | 約85% | なし | あり（題字「婚活あるある｜誰、あなた」＋1.0秒からせりふ字幕） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/yako.shiawasekon/7666304080490433813_open_0-2s.jpg |
| @junjun_ranran | 7692378853490167046 | 上位1 | 1,800,000 | カラス（青空）→2.0秒 窓辺の猫2匹 | カラス約70%／猫約25% | 怒る（悪口「おい、そこのデブ」） | あり（0.5秒からせりふ字幕） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/junjun_ranran/7692378853490167046_open_0-2s.jpg |
| @junjun_ranran | 7690894121547861254 | 上位2 | 630,400 | 白猫とリンの寝顔（暗い寝室） | 白猫約45%・リン約50% | なし（寝顔） | あり（0.5秒からせりふ字幕「ジュンジュンのご飯」） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/junjun_ranran/7690894121547861254_open_0-2s.jpg |
| @junjun_ranran | 7655625158299897108 | 上位3 | 407,000 | 病室のリン＋手前に猫の後ろ姿 | リン約60% | 笑う（喜び） | あり（せりふ字幕「私に手足をくれる人が」） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/junjun_ranran/7655625158299897108_open_0-2s.jpg |
| @junjun_ranran | 7670122320844967189 | 参考(4位) | 365,200 | 写真立て→猫の前足 | 写真立て約35%→猫アップ | なし | 2.0秒まで字幕なし（2.0秒で「また」） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/junjun_ranran/7670122320844967189_open_0-2s.jpg |
| @junjun_ranran | 7655019299546926357 | 下位2 | 148,300 | 病室のリン＋手前に猫の後ろ姿 | リン約50% | 笑う | あり（せりふ字幕） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/junjun_ranran/7655019299546926357_open_0-2s.jpg |
| @junjun_ranran | 7661624277401128209 | 下位1 | 87,900 | 0.0秒は真っ黒→下から照らされた猫の顔 | 0.5秒以降 約65% | なし | あり（1.0秒から「緊急事態発令」） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/junjun_ranran/7661624277401128209_open_0-2s.jpg |
| @nuts0629 | 7533937942935440648 | 上位1 | 1,300,000 | 女性がマイクを向ける犬（横長16:9） | 犬約35%・女性約80% | 笑う（女性） | なし | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/nuts0629/7533937942935440648_open_0-2s.jpg |
| @nuts0629 | 7536538803377310983 | 上位2 | 765,500 | 犬（横長映像を縦枠に入れ上下黒帯） | 映像内で犬約40%（縦枠全体では小さい） | なし | あり（上部「好きなおやつは？」） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/nuts0629/7536538803377310983_open_0-2s.jpg |
| @nuts0629 | 7517051675677429010 | 上位3 | 541,200 | チワワの顔アップ | 約70% | なし | なし（右上に透かし「Pollo.ai」） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/nuts0629/7517051675677429010_open_0-2s.jpg |
| @nuts0629 | 7515055931919486226 | 下位2 | 562 | 玩具パッケージ（STARTER PACK）と中の犬 | 箱約90%・犬約40% | なし | あり（画中の文字「STARTER PACK」「PINON」） | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/nuts0629/7515055931919486226_open_0-2s.jpg |
| @nuts0629 | 7515363273139555592 | 下位1 | 527 | 果物の部屋の黒い犬 | 約35% | なし | なし | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/nuts0629/7515363273139555592_open_0-2s.jpg |

| 事実（並べて見た結果） | 種別 | 出典 |
|---|---|---|
| junjun：上位1（180万）は0.0秒からカラスの顔が画面の約70%、0.5秒で悪口の字幕。下位1（8.8万）は0.0秒が真っ黒。 | 観察 | 上表 |
| the.care.logic：上位1（140万）は0.0秒から泣き顔のキャラが画面の約55%。下位2本は主役が約30〜35%で感情なし。上位3と下位2は0.0秒に大きな題字の表紙1枚（0.07秒）がある。 | 観察 | 上表 |
| yako：上位も下位も全部、上部に題字＋せりふ字幕。主役は男女2人で画面の約45〜85%。冒頭の感情は「なし」か「戸惑い」程度。上下で目立つ差は見えない。 | 観察 | 上表 |
| nuts0629：上位3本は文字なしか短い問いだけ。上位1は横長 1280x720 の動画。上位2は縦 1080x1916 の枠の中に横長の映像（上下が黒帯）。上位3は 720x914。 | 観察／実測（解像度は yt-dlp の info.json） | 上表 |

## 4. キャラの固定

| 事実 | 種別 | 出典 |
|---|---|---|
| @junjun_ranran：猫2匹は回をまたいで同じ柄・体型で出る（計測6本中、ジュンジュンは6本、ランランは3本。うち1本は写真立ての中だけ）。3回分を並べた画像あり。 | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/junjun_ranran/char3_junjun.jpg , https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/junjun_ranran/char3_ranran.jpg |
| ランラン：白一色の長毛。首まわりの毛が多く、ふさふさ。鼻と耳の内側はピンク。目は金色〜琥珀色（黄色寄り）。まぶたが半分閉じた眠そうな目が多い。体格は中〜大型で、毛のぶん大きく見える。 | 観察 | 7692378853490167046（23.5秒・49.3秒）、7690894121547861254（10.7秒）、7670122320844967189（95.6秒の写真） |
| ジュンジュン：白地にキジトラ（茶色〜こげ茶の縞）のぶち。頭のてっぺん・両耳・目のまわりから背中にキジトラ柄、鼻すじ・口まわり・胸・お腹・足は白。鼻はピンク。目は黄緑〜黄色。体格は太っていて丸く大きい（お腹が出ている）。 | 観察 | 7661624277401128209（113.8秒）、7655625158299897108（5.1秒）、7670122320844967189（50.0秒） |
| ずれ：最も伸びた 7692378853490167046（カラス回）では、ジュンジュンのぶちが他の回より黒っぽく、背中のぶちの位置も違って見える。柄は完全には固定されていない。 | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/junjun_ranran/char_junjun_variation_7692378853490167046.jpg |
| 飼い主リン：顔は回ごとに少し違う（既存 spec と同じ所見）。7670122320844967189 ではランランは写真立ての中だけで、生きた姿では出ない（亡くなった設定）。 | 観察 | spec_junjun_ranran.md、7670122320844967189 |
| @the.care.logic：計測5本の主役は全部ちがうキャラ（子宮・玉ねぎ・美容液ボトル・ドリアン王・ドーナツ）。固定キャラはない。画づくり（ピクサー風3D、ピンク〜金色の暖色、右上の透かし「The Care Logic」）は共通。 | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/the.care.logic/char3_leads.jpg |
| @yako.shiawasekon：女性主役は回ごとに顔・髪型が違う別人。固定キャラはない。固定は右上のロゴ「紫藤乃やこ 婚活サポート」と上部の題字。 | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/yako.shiawasekon/char3_female_lead.jpg |
| @nuts0629：クリーム色の長毛チワワ（首に紫の花飾り）が回をまたいで出る。黒×タンのチワワ（PINON）も2本に出る。実写風の回と玩具パッケージ風の回で見た目の質感は違う。 | 観察 | https://github.com/fireworker011/Research/blob/cursor/affi-template-bake-44d6/research/affi-templates/reference-accounts/frames/nuts0629/char3_nuts.jpg |
| 画面に見えたツールの透かし：nuts0629 7533937942935440648 右下「Veo」、7517051675677429010 右上「Pollo.ai」。yako 7666588350878321941 右下「KlingAI 3.0」。the.care.logic 7663785920939740424 右下に四方に光る星形マーク（どのツールかは不明）。他の16本は透かしを確認できず。 | 観察 | 各動画URL |
## 5. 声なしで伸びている AI 動物／3Dキャラ Shorts（日本語・直近30日）

| 事実 | 種別 | 出典 |
|---|---|---|
| 探し方：YouTube の公開検索ページ（yt-dlp で取得。「AI 猫 shorts」「AI動画 猫」「AI生成 犬」「AI 3D キャラ shorts」など10語＋「今月」絞り込みで7語）→日本語のAI動物チャンネル70件の Shorts 一覧→新しい順4本ずつの詳細（投稿日・尺・登録者）を yt-dlp で取得。RSS は70件中ほとんどが取得失敗。transcriptapi は使っていない。 | 実測（手順） | 2026-10-09 13:00〜13:40 JST |
| 条件（日本語・AIと題名やタグに明記・90秒以下・2026-09-09以降の投稿）に合ったのは10本。そのうち音声認識（Whisper small、VAD付き）でせりふが出なかったのは5本、要確認2本、せりふあり2本、取得失敗1本。 | 実測 | 下表 |
| 10本集まらなかった。「せりふなし」で条件を満たした5本は、全部が再生 600回未満（459〜585回）。 | 実測 | 下表 |
| 再生が大きいのは「AI猫にゃんこちん Official」の1本だけ（113,788回、登録者 93,200、再生÷登録者 1.22、36秒）。字幕は状況の見出しと、最後に猫のつぶやき「今日もおつかれ、自分」。せりふの有無は要確認（音声認識が冒頭2秒に1件だけ文字を出したが、無音らしさの値 0.85 と高く、耳で聞いていない）。 | 実測／観察 | https://www.youtube.com/shorts/Ceyy6iv0hzQ |
| 同チャンネルの過去の伸びた回（2025年6〜9月、50万〜105万回、62〜72秒）は、全部に YouTube の自動字幕（ja-orig か en-orig）が付いている。音声の中身は未確認。2026-09-27 の回には自動字幕が付いていない。 | 実測（メタデータ） | https://www.youtube.com/shorts/TNRD-u71oPw , https://www.youtube.com/shorts/Ceyy6iv0hzQ |
| 期間外の参考：POLYFRAME「動物レーシングカーをAIで3Dにしてみた」は 301,228回・34秒だが、投稿 2026-09-08 で30日の外（1日）。日本語の自動字幕（ja-orig）が付いている。登録者数は取得できず不明。 | 実測 | https://www.youtube.com/shorts/VTzb3GcWAD0 |
| 検索で見つかった日本語AI猫チャンネルのうち、再生の大きい「Four Seasons Cats（四季ねこ）」「mofumeshi.」「AI Cat Coco」は、新しい4本の投稿日が全部 2025年（直近30日の投稿は確認できず）。 | 実測 | yt-dlp メタデータ |

| URL | チャンネル | 再生 | 投稿日 | 登録者 | 再生÷登録者 | 尺(秒) | 字幕 | 心の声字幕か | せりふ音声（Whisper small＋VAD） | 判定 |
|---|---|---|---|---|---|---|---|---|---|---|
| https://www.youtube.com/shorts/Ceyy6iv0hzQ | AI猫にゃんこちん Official | 113,788 | 2026-09-27 | 93,200 | 1.22 | 36 | あり（見出し型「仕事後のやけ食い」「TVで現実逃避」、最後に「今日もおつかれ、自分」） | 一部あり（最後の「今日もおつかれ、自分」は猫自身のつぶやき） | 要確認（Whisperが0.2〜2.2秒に1区間「ご視聴ありがとうございました」を出した。no_speech_prob 0.85。耳で未確認） | 要確認 |
| https://www.youtube.com/shorts/YIoBoRTvdLE | AI猫みみた@バイト旅 | 459 | 2026-09-26 | 522 | 0.88 | 51 | あり（黄色い大きな文字「深夜はヒマにゃ。。。」） | あり（猫の心の声） | 検出なし | 条件を満たす |
| https://www.youtube.com/shorts/-5LZC4oQFQI | AI猫みみた@バイト旅 | 532 | 2026-09-15 | 522 | 1.02 | 46 | 見た8フレームでは字幕なし（最後に「いいね・登録」系の終わり画面） | なし | 検出なし | 条件を満たす |
| https://www.youtube.com/shorts/-7LiqwDAxd0 | AI猫みみた@バイト旅 | 514 | 2026-09-12 | 522 | 0.98 | 56 | 見た8フレームでは字幕なし（終わり画面あり） | なし | 検出なし | 条件を満たす |
| https://www.youtube.com/shorts/j2rRzyoJuhQ | AI猫みみた@バイト旅 | 461 | 2026-09-16 | 522 | 0.88 | 58 | 見た8フレームでは字幕なし（終わり画面あり） | なし | 検出なし | 条件を満たす |
| https://www.youtube.com/shorts/bTNMU4ZBI_c | 野良猫あつめ | 585 | 2026-09-26 | 16,600 | 0.04 | 10 | 見た8フレームでは字幕なし | なし | 検出なし | 条件を満たす |
| https://www.youtube.com/shorts/iZuF6pT7TMQ | AI猫🐾おやじ猫♡ | 591 | 2026-10-04 | 1,490 | 0.40 | 85 | 見た8フレームでは字幕なし | なし | 要確認（Whisperが5.0〜7.0秒に「ぽんぽんぽんぽん」。no_speech_prob 0.76。耳で未確認） | 要確認 |
| https://www.youtube.com/shorts/fKQLIvpZJ1U | 三毛猫のりんちゃんねる | 581 | 2026-09-15 | 32 | 18.16 | 69 | — | — | あり（「行ってくるね」「ただいまーりんちゃん」）→条件外 | 条件外 |
| https://www.youtube.com/shorts/xH5zf5T0H4M | AI猫🐾おやじ猫♡ | 263 | 2026-09-14 | 1,490 | 0.18 | 62 | — | — | あり（「お待たせにゃ」0.5〜5.8秒）→条件外 | 条件外 |
| https://www.youtube.com/shorts/wNMbEivI5YI | 家主(yanushi) | 161 | 2026-09-24 | 370 | 0.44 | 88 | 不明 | 不明 | 不明（動画の取得が403で失敗） | 不明 |

- 「せりふ音声」は Whisper small（VAD付き）の結果。歌・鳴き声・効果音を区別して聞いたわけではない。字幕は8フレーム（等間隔）を目で見た結果なので、見落としはありうる。

## 6. Grok Imagine（アプリ版）でできること：公式の記載だけ

確認日：2026-10-09（JST）。「アプリ版」は grok.com/imagine と iOS／Android の Grok アプリ。API（docs.x.ai）の記載はアプリと別物なので分けて書く。

| 事実 | 種別 | 出典URL |
|---|---|---|
| アプリ版の動画の長さ：Grok 製品ページに「Up to 2K resolution and 15-second videos」「Text-to-video up to 15 seconds at 720p」。 | 公式記載（製品ページ） | https://x.ai/grok |
| 画像から動画：2026-06-16 の発表で「Video 1.5 Fast を grok.com/imagine と iOS・Android アプリに出した」「best image-to-video models」。製品ページにも「from text prompts or reference photos」。 | 公式記載 | https://x.ai/news/grok-imagine-video-1-5 , https://x.ai/grok |
| 参照画像の枚数（アプリ）：「Up to seven references per generation」。画像・声の参照は「US の SuperGrok Heavy／Plus で grok.com/imagine と iOS から開始、数日で全プランへ」。Android の記載はない。 | 公式記載（発表記事、日付表示なし。本文に「Imagine Video 1.5 を先月出した」） | https://x.ai/news/grok-imagine-video-1-5-references |
| 声の参照：「キャラ画像と声の参照を渡すと、顔と声が全シーンで保たれる」。 | 公式記載 | https://x.ai/news/grok-imagine-video-1-5-references |
| 最初／最後のフレーム固定（アプリ）：アプリについての公式記載は見つからない＝不明。 | 公式記載なし | 上記3ページ |
| 日本語せりふの口パク：動画ページ（発表2本・API文書3本・製品ページ）に「Japanese」「日本語」の語はない。アプリで日本語の口パクに対応という公式記載は見つからない＝不明。 | 公式記載なし | 上記ページを語検索（2026-10-09） |
| （参考）音声：「効果音・環境音・せりふを同じ生成で作る。せりふがはっきりし、口とよく合う」（言語の記載なし）。 | 公式記載 | https://x.ai/news/grok-imagine-video-1-5 |
| （参考・API）grok-imagine-video-1.5：1〜15秒、参照画像 最大14枚（旧 grok-imagine-video は7枚・10秒）、プリセット声 最大3、最初・最後のフレーム固定あり、途中フレーム固定 最大4、口パクつき音声。これは API の記載でアプリの記載ではない。 | 公式記載（API） | https://docs.x.ai/developers/model-capabilities/video/overview , https://docs.x.ai/developers/model-capabilities/video/reference-to-video |
| （参考・API）image を渡すとその画像が最初のフレームになる。last_frame で最後のフレームを固定。同じ画像を両方に入れるとループ。 | 公式記載（API） | https://docs.x.ai/developers/model-capabilities/video/overview |
| （参考・別製品）xAI の Text to Speech は日本語を含む 25以上の言語。動画の口パクの言語とは別の製品の記載。 | 公式記載（TTS） | https://x.ai/voice/text-to-speech |

非公式（ブログ等。公式ではないので判断に使わない）：
- clickup.com のブログ：「アプリと web では 6／10／15秒、480p か 720p を選ぶ」。https://clickup.com/blog/how-to-use-grok-imagine/
- itechguides.com：「アプリの最大秒数や選択肢はアカウントや地域で違うことがある」。https://www.itechguides.com/convert-images-to-videos-with-the-grok-app-make-a-10-second-clip/
- metagrok.io：「App Store・製品ページ・実際の画面で最大秒数と解像度の表示が食い違う」。https://metagrok.io/how-to/make-imagine-video-15s
- eyerys.com：「プロンプトで日本語などを指定すると、その言語で口パクつきのせりふが出る（2026年3月ごろ話題）」。https://www.eyerys.com/articles/news/grok-imagine-can-now-generate-multilingual-videos-near-perfect-lip-sync

## 7. 取れなかったもの・注意

- 全20本（＋参考2本）とも動画の取得はできた（TikTok は yt-dlp、ログインなし）。測れた本数：the.care.logic 5／5、yako 5／5（＋参考1）、junjun 5／5（＋参考1）、nuts0629 5／5。
- scene>0.3 の検出漏れ：暗い映像（junjun）・溶ける切り替え・似た背景が続く画（care.logic の 48秒ショット、yako の長いショット）で多い。junjun の 2本は scene>0.1 を使い、それ以外は csv の「カメラ」欄に目視の場面替わり数を書いた。正確な切れ目の秒は、目視分については測っていない（不明）。
- 主役の画面高%は目測。ピクセル単位では測っていない。
- 動きの数は、ショットごとに2〜8枚のフレームを見て数えた。フレームの間で起きた小さな動き（まばたき等）は数えていない。
- 4（声なしAI動物 Shorts）：10本に届かず。家主(yanushi) の1本は動画取得が 403 で失敗。耳での音声確認はしていない。登録者数が取れなかったチャンネルあり（POLYFRAME）。TikTok 側は調べていない。
- 5（Imagine）：アプリ版の最初／最後フレーム固定、日本語口パク対応は公式記載が見つからず不明。アプリの参照画像7枚は発表記事の記載で、現在の画面の上限は確認していない（ログインしていないため）。
- transcriptapi・課金・投稿・外部連絡は使っていない。

## 8. 出力ファイル

- shots_the.care.logic.csv／shots_yako.shiawasekon.csv／shots_junjun_ranran.csv／shots_nuts0629.csv（列：動画ID, ショット番号, 開始秒, 秒数, 動き, 動きの数, カメラ, 構図）
- frames/{account}/{動画ID}_open_0-2s.jpg（0.0/0.5/1.0/2.0秒）
- frames/junjun_ranran/char3_junjun.jpg, char3_ranran.jpg, char_junjun_variation_7692378853490167046.jpg／frames/the.care.logic/char3_leads.jpg／frames/yako.shiawasekon/char3_female_lead.jpg／frames/nuts0629/char3_nuts.jpg
