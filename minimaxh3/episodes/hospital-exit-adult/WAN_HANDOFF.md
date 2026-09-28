# Wan 2.2 リライトへ渡すプロンプト

この文を、病棟の仕組みを Wan 2.2 用にリライトしている側の最初の指示として貼る。チャット履歴は正本にしない。H3 のノートは置き換えない。台本の文は Wan の古いマッチャに合わせて戻さない。生成ボタンは人間が押す。

## 正本

- リポジトリ: `fireworker011/Research`
- ブランチ: `cursor/h3-hospital-ward-34e4`
- HEAD: `26afb1fc7a3ef2ed7d4916cac2c5c0714b794182`（`h3 hospital: add wash gape, kneeling oral, and rib-stand waits`）。origin と手元は同じ
- PR: https://github.com/fireworker011/Research/pull/147 （draft。base は `cursor/h3-kasumi-adult-0402`）。この PR は Stack #155 に入っている。PR #155 は無い。新しい PR は作らない
- 台本: `minimaxh3/episodes/hospital-exit-adult/episode.json`
- H3 の引き継ぎ: `minimaxh3/episodes/hospital-exit-adult/HANDOFF.md`
- H3 エンジン: `colab/h3_episode.py` と `minimaxh3/h3_episode.py` は同じ
- Wan コード: `colab/wan_episode.py` と `minimaxh3/wan_episode.py` は同じ。入口 `colab/wan_episode_colab_main.py` も `minimaxh3/` と揃える
- ノート: `wan_hospital_episode_bot.ipynb` と `minimaxh3/wan_hospital_episode_bot.ipynb` は同じ。再生成は `python3 colab/_write_wan_episode_nb.py`。ipynb を手で直さない
- H3 Colab: https://colab.research.google.com/github/fireworker011/Research/blob/cursor/h3-hospital-ward-34e4/minimax_h3_episode_bot.ipynb
- Wan Colab: https://colab.research.google.com/github/fireworker011/Research/blob/cursor/h3-hospital-ward-34e4/wan_hospital_episode_bot.ipynb

## 役割

描画だけ Wan 2.2。台本の順番、ドロップダウン、尺、HUD の結合は H3 の `prepare_episode` と `finish_episode` のまま。プロンプト本文は `build_beat_prompt`。Wan は `source` を見て T2V か I2V かを決め、`extra_loras` の名前を Wan の high / low 組に読み替え、動作に合う scene slot を足す。

`source` が t2v のビートは開始画像なし。chain と still だけ、前のビートの最終フレームを開始画像にする。high は high expert、low は low expert。ファイルが無いスロットは強度 0 で飛ばす。H3 の重みと `pose_motion_lock.py` は読まない。チェックポイントは NSFW Fast Move V2 Q8（high 2540892 / low 2540896）。steps 4、CFG 1、fps 16、長さは 4n+1。Lightning は中に入っているので、もう一枚積まない。テキストエンコーダは umt5。保存先は `WAN_ONEDRIVE_ROOT`。Colab 既定は `/content/drive/MyDrive/wan-hospital`。

## 台本が今こうなっている

`26afb1fc` で足した id はこの 8 つだけ。`04-toilet-gape` `04-gin-mouth` `04-gin-spitkiss` `04-gin-wait` `03-kiss-wait` `06-doggy-wait` `09-join-wait` `12-exit-wait`。角の `04-tsuno-wait` と `04-tsuno-gape` は既存。`04-toilet-*` は角個室に無い。

- 和式ミキは全拍 chain。順は in → squat → spot → push → 挿入 → cum → gape → out。排出の和式に gape は無い。push は後ろから抱えて掌を背中に当て、そのあと胸を台へ、腰を高くする。Jack-O は push だけ。gape は 6 秒。すでに結合した状態から腰を一度後ろへ引き、24cm が肛門を離れ、輪が開いたまま WHITE goo が穴へ垂れる。out は向き直してべろちゅーして右へ歩く。抜きは out に無い
- 口の 0 秒も最終も跪き。ギンは jupo → mouth → spitkiss → wait → ride → peak。みき／れい／かな／しのは口 → wait → ride → peak。角の口の最終は跪き。跨ぎは既存の `04-tsuno-wait`
- wait は両足裏を肋骨の左右に置き、マンコを亀頭の真上に置く。未結合。STANDS は wait だけ
- 着座はすでにその足。LOWERS を一度。根元で HOLD。着座に thrust は積まない
- peak、和式 cum、角 cum、犬 cum の最終は `Thick WHITE goo OVERFLOWS from the join down the buried shaft and over the groin`。根元は埋まったまま。結合に cmst は積まない
- `04-gin-mouth` の extra は blowjob 0.7 + cumouf 0.5。`04-gin-spitkiss` の extra は kiss 0.5 + cumouf 0.45
- 犬の lick と lick-peak は chain。invite から cum まで chain。walk の end はそのまま。犬の wait は connect cut。向き文と舐め動詞はそのまま

## 実測（`prepare_episode` のあと、`scene_slot_entries`）

チェーンは「前の最終フレームから続ける」。カットは「カット」。

角・騎乗、チェーン: spot chain、kiss chain、oral chain、wait chain、ride chain、peak chain、ride-kiss chain、walk chain。カットにすると spot / kiss / oral / wait / ride-kiss / walk は t2v。ride と peak は chain のまま。

角・個室、チェーン: stall、stall-kiss、walk は t2v。stall に前フレームは無い。anal は chain で scene slot `anal`。cum と gape は chain で scene slot なし。

和式ミキは、チェーンでもカットでも 8 拍すべて source chain。挿入 `04-toilet` だけ scene slot `anal`。cum と gape の scene slot は空。

灰色・犯される、カット: lick-spot、lick、cunny、walk は t2v。jupo、mouth、spitkiss、wait、ride、peak は chain。scene slot はどれも空。

誘う・騎乗位、カット: `03-kiss` `06-doggy` `09-join` `12-exit` の口は t2v。それぞれの wait、ride、peak は chain。scene slot は空。`06-doggy` という id でも四つん這いの文はもう無い。

誘う口の犬、チェーン: lick、lick-peak、jupo、mouth、show、in、cum は chain。wait は t2v。walk は connect end。lick、wait、jupo に scene slot `missionary` が付く。理由は action の `stays on her back` と、腹の下の `between the hind legs`。マンコへ入る文ではない。

## Wan 側で合わせる

`episode.json` は直さない。直すのは `scene_slot_entries` と `colab/test_wan_episode.py` の期待。`colab/` と `minimaxh3/` は同じ内容にする。

`python3 -m pytest colab/test_wan_episode.py -q` は今 2 件落ち、5 件通る。

- `test_invite_ride_order_and_sources`: 角・騎乗のチェーンで `04-tsuno-wait` と `04-tsuno-walk` は source chain。テストの `RIDE_CHAIN` は両方 t2v のまま
- `test_scene_loras_follow_the_prepared_act`: `04-tsuno-cum` の slot は mystic、penis、synth、thrust。`anal` が無い。action は `stays buried in the anus` と OVERFLOWS。マッチャは `into the anus` `inside the anus` `travels into the anus` `fills the anus` だけを見ている。この assert で止まっているので、その後の `06-doggy` の doggy と `09-join` の missionary は未実行。別測ではどちらも scene slot が空

合わせたあとの slot:

- `anal` は、肛門へ `TRAVELS INTO` する挿入と、肛門に根元まで埋まったままの cum。和式ミキの挿入、角個室の anal、角個室の cum、和式ミキの cum。トリガー `anal sex` は今までどおり挿入側に付く
- gape に `anal` は付けない。`04-toilet-gape` も `04-tsuno-gape` も、輪が開いて竿は外
- 歩き、親指だけ、brown log、肋骨の跨ぎ、跪きの口に `anal` は付けない
- `missionary` は、仰向けの相手の腿の間で竿がマンコへ入る拍。肋骨の wait / ride / peak には付けない。犬の `between the hind legs` では付けない。lick の本文は変えない
- `doggy` は action が all fours の拍だけ。id が `06-doggy` でも、跪き口と肋骨の着座には付けない
- `nelson` `pee` `scat` の既存条件はそのまま。pee、親指、排出の和式は、落ちたテストの後半にあって今回は未実行。条件式は変えていない

`colab/test_h3_episode.py -q -k hospital` は 26 件通ったままにする。

## 触らない

洋式の pee / masturbate / tentacle / finger、座位の zai、抱擁の hold、ネルソンの本文、角個室の stall の cut、`04-gin-lick` の舐め本文、犬の向き文、`01-cover`、レイの脱出、kasumi、投稿。H3 ノート `minimax_h3_episode_bot.ipynb` は置き換えない。

## 生成

人間が押す。Wan で作り直す拍は、H3 の FRESH と同じでよい。和式ミキの `04-toilet-push` `04-toilet` `04-toilet-cum` `04-toilet-gape` `04-toilet-out`。ギンの `04-gin-jupo` `04-gin-mouth` `04-gin-spitkiss` `04-gin-wait` `04-gin-ride` `04-gin-peak`。騎乗の `03-kiss` `03-kiss-wait` `03-kiss-ride` `03-kiss-peak` と `06-doggy` `09-join` `12-exit` の口・wait・ride・peak。角の口 `04-tsuno-oral`。犬の `04-dog-lick` `04-dog-lick-peak` と invite から cum。開始シーンに、その話の最初の id を書くと、それより前は残る。
