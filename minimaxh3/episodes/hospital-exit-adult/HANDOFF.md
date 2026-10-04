# 病棟出口 引き継ぎプロンプト

この文を Cursor でも Grok でも、そのまま最初の指示として貼る。チャット履歴は正本にしない。正本は下のファイルだけ。両方のツールは同じブランチの同じファイルを編集する。

## 役割

病棟出口 `hospital-exit-adult` の既存カットだけを直す。新しい話、新しいキャラ、投稿、トレードはしない。生成ボタンは人間が押す。こちらは台本・つなぎ・テストを合わせる。

## 正本（ここだけを編集する）

- リポジトリ: `fireworker011/Research`
- ブランチ: `cursor/h3-hospital-ward-34e4`
- PR: https://github.com/fireworker011/Research/pull/147
- Colab: https://colab.research.google.com/github/fireworker011/Research/blob/cursor/h3-hospital-ward-34e4/minimax_h3_episode_bot.ipynb
- 台本: `minimaxh3/episodes/hospital-exit-adult/episode.json`
- エンジン: `colab/h3_episode.py` を直したら、同じ内容を `minimaxh3/h3_episode.py` にコピーする。片方だけ直さない
- Colab 入口: `colab/h3_episode_colab_main.py` と `minimaxh3/h3_episode_colab_main.py` も同様に揃える
- ノートのフォーム: `colab/_write_episode_nb.py` を直し、`python3 colab/_write_episode_nb.py` で `minimax_h3_episode_bot.ipynb` と `minimaxh3/minimax_h3_episode_bot.ipynb` を再生成する。ipynb を手で直さない
- テスト: `python3 -m pytest colab/test_h3_episode.py -q`
- このファイル: `minimaxh3/episodes/hospital-exit-adult/HANDOFF.md`。仕様が変わったら、ここを同じコミットで更新する

## いま（2026-09-30）

仕様の差分は `05608320` と `ec8371ba`。ブランチと PR は上のまま。`python3 -m pytest colab/test_h3_episode.py colab/test_wan_episode.py -q` は 109 通過。生成はまだ人間。新しい話も新しい id も足していない。

動画 `1fqfA6jJdQygxKev67RMgZL27V3L4cETj`（5:31）は、この台本より前の生成である。角・病室の横挿入は入っていない。便器は白い磁器。灰色は通路のギンで、一つの目と生え際の角が無い。白い筋はあやの顔に落ちている。

直したあと、まだ動画になっていないもの。

- `05608320`。「前の最終フレームから続ける」と着地は、台本の `connect: cut` も I2V。カットを選ぶと cut は T2V。connect 欄は書き換えていない。チェーンの T2V は `01-cover` だけ。
- `ec8371ba`。洋式・和式・触手の便器は有機物。緑の外皮、赤い肉の口、琥珀の液、根。和式は床と同じ高さの長い植物の口で、遠端は葉のフード。磁器は消した。和式の軸（フード左、扉右、頭は左端の前腕）は残す。
- `ec8371ba`。顔射は cumshot 1.0 と `CUMSH0T`。寝室の中出し `04-tsuno-peak` は thrust 0.55、synth 0.4、`PENISLORA`。`merge_trigger` は、積んだ cumshot / cmst / cumouf / penis / spoonlg / thrust の語が空ならプロンプトに足す。

角の口 `04-tsuno-oral` は blowjob 0.8 と `bl0w_j0b`。mystic 0.5 と penis 0.45 は残す。動作文と connect 欄は変えていない。横挿入と寝室アナルの両方。

角の二人の顔。あやと角が同じ画面にいる拍は `lewd pleasure-drunk happy smile`。頬は赤く、涎が垂れ、快感に酔って、互いを慕う。口が塞がる拍と、向きを固定した拍は、その姿勢のまま。あや一人の歩きは変えていない。connect 欄は変えていない。

容姿。Colab のあやの欄と敵の1行が空なら、今の lock のまま。書いた項目だけ、その人の Look と、同じ句が本文にあるところを置き換える。髪型を書くと髪色は使わない。竿の「今のまま」は台本どおり。「あり」はあやの lock に 24cm を足す。ギンの `no penis` は、ギンを「あり」にしたときだけ置き換える。「なし」は、その敵の竿の句を `a bare hairless groin` に置き換える。英語だけ。`no` `never` `not` `without` `blood` は書かない。connect 欄は変えない。

人間が FRESH するもの。トイレの個室。`04-tsuno-oral` `04-tsuno-wait` `04-tsuno-peak` `04-tsuno-jo-cum`。かなの `09-kana-facial`。角を出すときは `04-tsuno-meet-spot` からその枝の最後。顔を足したので、その枝は最後まで FRESH。

触らない。Wan ノート。`WAN_HANDOFF.md`。pee と finger の動作本文。ギンの口の本文。角の connect 欄。新しい話。

## Wan 2.2（H3 の横。H3 ノートは置き換えない）

描画だけ Wan 2.2。台本・ドロップダウン・HUD 結合は H3 の `prepare_episode` と `finish_episode` のまま。

- コード: `colab/wan_episode.py`（`minimaxh3/wan_episode.py` と同じ）
- 入口: `colab/wan_episode_colab_main.py`
- ノート: `wan_hospital_episode_bot.ipynb`。0 で Google ドライブを接続する。1 は CPU で、無い重みだけ `マイドライブ/wan-hospital` へ取る。最後のセルは GPU で、その重みを使って描く。人間が実行する。キーは空のまま保存する
- 保存先: Google ドライブ（`WAN_ONEDRIVE_ROOT`、Colab 既定 `/content/drive/MyDrive/wan-hospital`）
- `source` が t2v のビートは Wan T2V。開始画像なし。chain と still だけ、前のビートの最終フレームを開始画像にする
- `extra_loras` の名前は残す。中身は Wan 2.2 の high / low 組（`wan-<名前>-high.safetensors` と `wan-<名前>-low.safetensors`）。high は high expert、low は low expert にだけ付ける。一覧は `WAN_SLOT_LORAS`。ファイルが無いスロットは強度 0 で飛ばす。H3 の重みと `pose_motion_lock.py` は読まない
- 用意された動作に合う LoRA だけ Wan が足す。肛門への挿入は `anal`（high 2161023 / low 2161067、トリガー `anal sex`）。抱え上げたフルネルソンは `nelson`。四つん這いは `doggy`。仰向けの相手の間は `missionary`。黄色の放尿は `pee`。和式の排出は `scat`。親指だけの肛門、歩き、角・騎乗の跨ぎには肛門 LoRA を付けない。台本の文は変えない
- Colab: `wan_hospital_episode_bot.ipynb`。0 で Google ドライブ、1 で初回の重み（GPU 不要）、最後のセルで生成。人間が実行する
- テキストエンコーダは umt5
- テスト: `python3 -m pytest colab/test_wan_episode.py -q`。H3 の `colab/test_h3_episode.py -q -k hospital` は壊さない
- リライト側へ貼る文は `minimaxh3/episodes/hospital-exit-adult/WAN_HANDOFF.md`。`26afb1fc` の台本に対する source とスロットの実測はそこ。`test_wan_episode.py` の期待はそれより古い

## プロンプトの書き方

- 英語の動作文。日本語は「」のセリフだけ
- 体位の名前は書かない。誰がどこへ動くかを書く
- 否定で消したいものを描かせない。`blood` `zombie` `corpse` は書かない。H3 は否定してもその語を描く。消したい動きも否定で書かない。着座の最後は `They HOLD still joined at the BASE until the last frame`
- 着座と上下は別カット。着座に thrust / sideride を積まない
- 足が切れる参照動画があっても、画面は全身、両足まで入れる。対面座位のあやの足は床に無い。ギンの ride は肋骨の両側に足裏。片膝上げは書かない
- 数字は台本とテストに既にあるものだけ使う。尺や売上を新しく作らない

## つなぎ（確認済み）

Colab の「前の最終フレームから続ける」は `connect=chain`。

- 最初の GPU カットだけ T2V
- 遭遇カット（id が `-spot`）も I2V。前の最終フレームのあやに、新しい人が入る
- それ以外の GPU カットも、前の最終フレームからの I2V
- 同じ相手の次の行為、ポーズ、トイレ、灰色、角、戦いも I2V。台本の `connect: t2v` と `connect: cut` は、この病棟でチェーンか着地を選んだときは効かない
- 「カット」を選ぶと、台本の `connect: cut` と `connect: t2v` は T2V。ただし connect が chain の肋骨騎乗の着座と絶頂、角の寝室 chain（kiss、oral、wait、peak、ride-kiss、behind、jo-anal、jo-cum、jo-gape）、ギンの `04-gin-jupo` `04-gin-mouth` `04-gin-spitkiss` `04-gin-wait` `04-gin-ride` `04-gin-peak`、みき／れい／かな／しのの `*-wait` はカットでも I2V のまま
- チェーンを選んだとき、T2V は `01-cover` だけ。立ちバック、寝室、個室、顔射、触手の出、犬の spot も I2V。台本の connect 欄は書き換えない。和式ミキは全拍 chain
- `04-gin-cunny` は connect chain。首は舐めの最終（座り、マンコ、竿なし、舌がクリ）。Look の 0 秒に 24cm は書かない
- 角・病室の wait は connect chain。lie、ride、walk の connect は cut。カットを選ぶとこの3つは T2V。チェーンと着地では I2V。跪きの最終を跨ぎの首にしないのは、カットを選んだとき
- 騎乗枝の歩き `04-gin-walk` `03-kiss-walk` `06-doggy-walk` `09-join-walk` `12-exit-walk` も connect chain。抜くのはこの歩きの 0–3 秒だけ。しのの `12-exit-walk` は `12-exit-kiss` のあと。drop と kiss が既にあるので、結末はもう一組足さない。peak と drop のあいだに歩きを置くと、次の拍でしのが戻り遭遇スポットが足される
- 角・個室の stall と stall-kiss と walk の connect は cut のまま。カットを選ぶと T2V。チェーンと着地では I2V。台本の connect 欄は chain に書き換えない
- 犬の wait は connect chain。和式ミキは全拍 connect chain。排出の和式に gape は無い

遭遇を足す関数は `insert_presence_beats`。spot は最初から `source: chain` `connect: chain` で作る。`keep_chain_cast` は `-spot` の新人を T2V に戻さない。遭遇を消さず、遭遇自体を chain のままにする。遭遇カットでは前のカットの余分な人を残さない。

## 容姿

初期の見た目は `cast` の `lock`。そのカットだけ違うときは `cast_lock`。汚れ、傷、粘液、髪、肌の色、竿の長さと色はここに書く。

あやは 21 歳のまま。顔は肩より下まで落ちる長いストレートの暗い髪、額を横切る直線の前髪、左頬の小さいほくろ、柔らかい卵型、暗い茶色の目、細い眉、薄いピンクの唇。体は細身のスレンダー、Cカップ、細い腰、細い腕。パイパンは `hairless pussy` のまま。汗と `grimy brown hospital dirt` の文は変えない。帽子は書かない。`cast.lock` と `looks.white_upper` とギンの `cast_lock.aya` を同じ顔に揃える。

各病棟カットのプロンプトには `Look that stays for this whole shot` が付く。否定の句（`no` `never` `not` `without`）はそこから落とす。竿を消す歩きだけ、action に `No penis` と `The grown shaft is gone` と書く。その歩きには竿を戻さない。

チェーンの I2V は、前フレームが汚れや竿を落としていても、`subject_definitions` の見た目に戻す。

遭遇 `-spot` も同じ Look を付ける。action にあやの grimy brown hospital dirt を書く。新人は already ではなく、画面に入ってくる。

## ギンの騎乗（`灰色・犯される`）

- 遭遇 `04-gin-lick-spot` は I2V。前フレームのあやに続ける。ギンは画面左端から入る。視聴者から見てあやの左＝あやの真後ろを、あやの歩幅に合わせて歩く。あやの歩きは徐々遅くなり、恐る恐る立ち止まる。あやは右、ギンは左。天井から落ちる構図は使わない。あやは右向きのまま
- `04-gin-lick`: あやは恐る恐る振り向いて、尻餅は右側。頭は画面右、足先は左。そこがゴール。ギンは左でしゃがみ、長い舌があやのマンコとクリを下から舐め続ける。竿は生えない。ギンもあやも竿なし。容姿・汚れ・眼窮はそのまま。`futanari` の語は書かない。右端は暗い通路が続く。壁という語は書かない。舐め本文は変えない。Aya says 「気持ちいい」。extra は mystic + cunny + jpnmoans 0.55。トリガー `performing cunnilingus` と `jpnMoans`。声はあやの `きもちいい` とギンの `れろっ`
- `04-gin-cunny`: source も connect も chain。0秒は舐めの最終。あやは右側に座り、マンコ、竿なし、舌はクリ。Look に 24cm を書かない。舌はクリを舐め続ける。THEN クリが直立の 24cm に生える。生えた瞬間だけ wide-eyed surprised joyful excited smile。Aya says 「すごい」。背中はリノリウムへ下り、頭は RIGHT、足は LEFT。ギンは新しい竿を一度舐める。最終は jupo の首。仰向け、24cm が真上、ギンは左でしゃがむ。extra は cunny 0.8 + mystic 0.5 + jpnmoans 0.55。futatf と penis は積まない。Turbo / Eros 8step / Larry は extra に置かない。この拍は `steps` 8、`turbo` false。Comfy はこの 8 を使う。API 経路は steps 欄が無いので Turbo を切る。`Aya's shaft written in that look stays erect` は付けない。`FALLS ONTO` は書かない
- `04-gin-jupo`: 0秒から仰向け＋24cm。cunny の最終を継承。倒れる工程は書かない。座ったまま、両腕を後ろ、LIES BACK、マンコが真上、は書かない。ギンは腰の左で跪き、閉じた唇。閉じた唇が根元まで下り、亀頭へ戻ってまた根元まで下りる。0秒も最終も跪き。最終の跨ぎ文は書かない。Look の竿文はここから付ける。connect は chain
- `04-gin-mouth`: あやの 24cm がギンの口から一度出る。亀頭はギンの顔の前。slit から WHITE rope がギンの顔と舌へ。あやの顔には掛けない。extra は cumshot 1.0 + cmst 0.55 + mystic 0.5。トリガーは `CUMSH0T` と `cmst`。cumshot は 1.0 未満だと絵の具になる。blowjob と cumouf は積まない。jupo は触らない。STANDS は書かない。次の spitkiss も WHITE はギンの顔
- `04-gin-spitkiss`: 口から抜く文は書かない。WHITE はギンの口と舌の中。ギンが口をあやの口へ持っていく。口が付いたまま、ギンの舌が WHITE をあやの口の中へ渡す。あやの舌に着く。それから口が離れ、舌と舌のあいだに WHITE の糸。顔の上をなぞるだけでは口移しにならない。extra は kiss 0.5 + cumouf 0.45。STANDS は書かない
- `04-gin-wait`: あやは仰向け、24cm は真上。ギンは股の上に立つ。両足裏は肋骨の左右、両膝は曲がったまま、マンコは亀頭の DIRECTLY ABOVE。未結合。STANDS はここだけ
- そこから既存の分岐（騎乗 / 正常位 / 後背）。成長とジュボは別カット。犯すと誘う後背の cunny 本文は残す
- `04-gin-ride`: 乗るのはギン。あやは仰向けのまま。参照は IMG_0718。0秒は wait の足。両足裏は肋骨の左右、胸の左右に一枚ずつ。両膝は曲がったまま。腰は股の上。体重は足裏。マンコは亀頭の真上。LOWERS 一度、根元で HOLD。`HOLD still joined at the BASE until the last frame`。最終も両膝は曲がったまま、足裏は肋骨の横、根元。両手はあやの胸。SQUATS、sits beside、knees on the linoleum、LIFTS、folds down、Three separate lowers、SITS ON、STANDS UP、steps over は書かない。STANDS は書かない。extra は mystic 0.5 + penis 0.45 + synth 0.4。sideride と thrust は積まない。connect は chain
- `04-gin-peak`: すでに結合。足は着座と同じ。両膝は曲がったまま。腰は股の上。体重は足裏。短い上下は `Short vertical moves keep the glans inside`。`Hips return flush`。`HOLD still joined at the BASE until the last frame`。`The shaft stays buried to the root until the last frame`。あやは Gin の中で終わる。`Thick WHITE goo OVERFLOWS from the join down the buried shaft and over the groin`。最終は根元のまま、WHITE goo は結合に溜まって流れる。根元は抜かない。`LIFTS` `PULL BACK` `SLIDES OFF` は書かない。ギンの唇は閉じたまま。Aya says 「あ、いく」。extra は penis 0.45 + synth 0.4 + thrust 0.55 + jpnmoans 0.55。sideride と mystic と cmst は積まない。connect は chain。声は `あ、いく` の1句
- `04-gin-walk`: connect chain。0–3 秒は口と口、涎の糸、ここでギンのマンコから抜ける。3–5 秒でギンが右へ。5–8 秒はあや一人。`No penis` `The grown shaft is gone`。T 字路の文は残す。extra は kiss 0.5。犯す側の歩きは connect end のまま
- 再生成は FRESH。順番は舐めの最終 → cunny → jupo → mouth → spitkiss → wait → ride → peak → walk。今の Drive の抜け 3 本（`13rHcn` `1QbWMV` `1cqrvu`）は首にしない。`1cqrvu` は角ではない。`04-gin-peak`

## 角の遭遇（`角`）

- 遭遇 `04-tsuno-meet-spot` とギンの `04-gin-lick-spot` は同じ遅れ足。新人は `ENTERS from the LEFT edge`。膝は硬い。一歩が遅れる。後ろ足はリノリウムを滑る。両腕は遅れて揺れる。頭は少し傾く。短い間隔を保つ。あやは右へ歩き、遅くなって止まる。あやの他の歩様は変えない。`zombie` `corpse` `blood` `undead` `shambling` `match stride` は書かない。spot はそこで終わる。異種の spot 本文は変えない
- `04-tsuno-meet`: ミキへの背後抱きと同じ。体を背中に押しつけ、胸が潰れるまで密着し、両手で胸を揉む。その密着のまま竿が肛門へ入る。入った瞬間、あやも角も止まる。顔は驚きと快楽。声は「んおおおおぉー」。結合部を見せる横ずれは書かない。壁へ移る動きのあとに止まる。LUNGES は使わない。フルネルソンの meet も同じ抱擁から入り、文は `wraps Aya from behind`。立ちバック・後ろアナル・フルネルソンの本文は残す

角の二人は、あやと角が同じ画面にいる拍で `lewd pleasure-drunk happy smile`。頬は赤く、涎が垂れ、快感に酔って、互いを慕う。口が竿や相手の口に付いている拍は、その口を開け直さない。`do not turn to face each other` の拍と、顔の向きが既にある拍は、その姿勢のまま笑う。あや一人の歩きには足さない。Look は無表情の lock に戻さない。

## 角・廃病室

全枝の `04-tsuno-meet-spot` は廃病室、connect は cut。角はマットレスの縁に座り、右手が `erect ashen-gray 24cm` を上下。あやが扉から入る。extra は mystic 0.5。通路の遅れ足は角の spot に書かない。

立ちバック、誘う立ちバック、後ろアナル、フルネルソンは、spot の次に `04-tsuno-stand`（縁から立つ）。spot、stand、meet、in、carry の connect は cut。カットを選ぶと T2V。チェーンと着地では I2V。密着の meet、後ろアナル、フルネルソンの本文は残す。壁立ちバックの in と peak は肛門。脹脛のあいだの低いカメラと、すでに屈んだ一回の挿入。場所の語は病室。`04-tsuno-stall` 以降の connect 欄も cut のまま。カットでは T2V。チェーンと着地では I2V。

## 選択肢の名前

6番とシーンごと。足を揃えて立ってから下ろすのが今の跨ぎ。最初から膝を曲げて下ろすのが、姿勢の違いを聞く前の跨ぎ。角の一覧では「角・病室で横になって挿入」が寝室の横並び、「角・病室でベッドの後ろアナル」がベッドのままの後ろアナル。「角・騎乗・細い柱」は一覧に出さない。中身は横になって挿入と同じ。

## 角・騎乗（`invite_ride`）

順番: `04-tsuno-meet-spot` → `04-tsuno-kiss` → `04-tsuno-oral` → `04-tsuno-wait` → `04-tsuno-spit` → `04-tsuno-beckon` → `04-tsuno-lie` → `04-tsuno-sidekiss` → `04-tsuno-ride` → `04-tsuno-peak` → `04-tsuno-ride-kiss` → `04-tsuno-walk`。仰向けにしない。action に SPOONLG と体位名は書かない。否定は書かない。首の角度の禁止は書かない。

- kiss chain: 角は座ったまま。同じあや一人が膝の間に立ったまま、胴を前へ倒して口が付く。涎の糸。カメラはドア正面の広い全身のまま、距離は固定。顔の寄りは足さない。`nothing new enters` と `Two faces` はこの拍に足さない。kiss 0.5 + mystic 0.5。寝室の同じ `04-tsuno-kiss` も同じ文
- oral chain: あやが深く膝を曲げる。閉じた唇が根元往復。blowjob 0.8 + mystic 0.5 + penis 0.45。トリガーは `bl0w_j0b`。横挿入と寝室アナルの両方。STANDS は書かない
- wait chain: 一度口から出す。WHITE はあやの顔と舌。寄り。extra は cumshot 1.0 + cmst 0.8 + penis 0.45 + mystic 0.5。トリガーは `CUMSH0T` `cmst` `PENISLORA`。cumshot は 1.0 未満だと絵の具になる
- spit cut: あやがしゃがみから両足で立つ。角はマットレスの縁に座ったまま。口が付き、あやの舌が WHITE を角の舌へ渡す。涎の糸。カメラはドア正面。extra は kiss 0.5 + cumouf 0.5。トリガーは `CUMOUF`。寝室 Jack-O には付けない
- beckon chain: 角はベッドの右半分のマットレスの上で横になる。縁のそばには置かない。頭は画面の左、足は右。胸は窓。空いた手がベッドへ手招き。あやは手前の床に立ったまま。カメラはベッド横の `PROFILE`。距離は固定。全身
- lie cut: あやは手前（カメラ側）、角は奥（窓側）。頭は二人とも画面の左、足は右。背中は角の胸に密着。膝をマットレスに上げ、腰を下ろして角の前で同じ向きに横になる。上の膝は窓へ上がる。下の脚はマットレス。角の近い腕はあやの首の下。もう一方の手は上がった腿。竿は太ももの外側。カメラはベッド横の `PROFILE`。`FRONT from the doorway` は書かない。参照は Drive `1QLLFwFEMCtXvnghJaXiRp6DadqzdaluM`
- sidekiss chain: 胸は窓のまま、顎だけ肩越しに戻して口が付く。上の膝は窓へ上がったまま。角の手はその腿。竿は太ももの外側。カメラはベッド横の `PROFILE`。`FRONT from the doorway` は書かない
- ride 10秒 cut: 横のまま。上の膝は窓。下の脚はマットレス。角の近い手がその腿を持つ。角の腰がマットレスに沿って一度前へ。太ももの線に沿って一度マンコへ入れて `HOLD still joined at the BASE until the last frame`。口は上がった腿の横で近い。結合部は太ももの横、画面中央。extra 先頭 spoonlg 1.0、penis 0.6。trigger は `SPOONLG.`。Turbo は切る。`LIFTS` も前腕も空中の足も書かない
- peak chain: 同じ膝と手のまま、口は付いたまま。角の腰がマットレスに沿って後ろへ戻り、竿は上がった腿の外側、亀頭はマンコに当たる。それから前へ戻して根元。その抜き差しをもう二回。腰は密着に戻る。溢れ。`HOLD still joined at the BASE until the last frame`。結合部は太ももの横、画面中央。`FRONT from the doorway` は消す。extra は spoonlg 1.0 + penis 0.6 + synth 0.4 + thrust 0.55 + jpnmoans 0.55。トリガーは `SPOONLG.` と中出しの文と `PENISLORA` と `jpnMoans`。あやは「あ、いく」
- ride-kiss chain: 結合のまま口。kiss 0.5
- walk cut: 0–3 秒はベッドで口、ここで抜ける。そのあと入り口のあや一人。`No penis` `The grown shaft is gone`

竿を書くカットは `erect ashen-gray 24cm`。あやに竿は生やさない。寝室の walk の次の `04-dog-spot` も、チェーンと着地では I2V。犬の spot を T2V に戻さない。

## 角・寝室アナル（`invite_jacko`、UI「角・寝室アナル」）

顔射のあと別枝。個室 id は使わない。`04-toilet-*` はコピーしない。

順番: spot → kiss → oral → wait → `04-tsuno-jo` → `04-tsuno-behind` → `04-tsuno-jo-anal` → `04-tsuno-jo-cum` → `04-tsuno-jo-gape` → `04-tsuno-jo-kiss` → `04-tsuno-jo-walk`。spot、jo、jo-kiss、jo-walk の connect は cut。カットを選ぶと T2V。チェーンと着地では I2V。behind、jo-anal、jo-cum、jo-gape の connect は chain。カットでも I2V。

- jo: 胸と片頬がマット。尻は高い。顔は扉。jacko 0.8
- behind: 角が後ろ。同じ向き。掌は尻。未挿入。jacko 0.8
- jo-anal: 一度肛門へ根元。`HOLD still joined at the BASE until the last frame`。jacko 0.7。Turbo は切る
- jo-cum: 中出しの溢れ。jacko 0.65 + thrust 0.55。あやは「あ、いく」
- jo-gape: 抜いて輪が開く。白が垂れる。jacko 0.65
- jo-kiss: 立って向き直し、口
- jo-walk: 入り口のあや一人

action に jacko、doggy、hug、wraps は書かない。doggy LoRA は同時に積まない。

## 洋式

便器は有機物だけ。洋式は緑の外皮、赤い肉の口がボウル、植物の唇、琥珀の液、根、後ろにもう一本のウツボカズラ。磁器もタンクも便座も書かない。動作は変えない。触手も同じ植物便器に座る。順番は in で座る → fill で両手首と両足首 → toilet の 0–3 秒で 4 本が付いて HOLD → out は cut、触手が外れて立つ。tentacles3d 0.45 は 4 本の拍。和式は床と同じ高さの長い植物の口。フードは遠端のウツボカズラの葉。beige platform は戻さない。

## 角・個室（新話 `wash_carry`）

これは新しい話。トイレ枠は消さない。角を「出ない」にしてもトイレは残る。id は `04-tsuno-*` だけ。`04-toilet-*` はコピーしない。ThumbInButt は積まない。spot と抱き上げは廃病室。`04-tsuno-stall` 以降の connect 欄は cut。カットを選ぶと個室は独立の T2V。チェーンと着地では前の最終フレームから I2V。connect 欄は chain に書き換えない。

お姫様抱っこは駅弁でもネルソンでもない。`LIFTS` はこの抱き上げだけ。腰の上下には使わない。

順番: `04-tsuno-meet-spot` → `04-tsuno-carry` → `04-tsuno-stall` → `04-tsuno-set` → `04-tsuno-anal` → `04-tsuno-cum` → `04-tsuno-gape` → `04-tsuno-rise` → `04-tsuno-stall-kiss` → `04-tsuno-walk`。

- carry 6秒: その場で抱き上げて HOLD
- stall 6秒: すでに個室。connect は cut
- set 6秒: 下ろして四つん這い。未挿入
- anal 10秒: 一度寄せて根元 HOLD。mystic 0.5 + penis 0.45 + synth 0.4
- cum 8秒: 中出し。thrust 0.55 を足す
- gape 6秒: 抜いて輪が開く
- rise 6秒: 台上で向かい合う
- stall-kiss 8秒: rise のあと。横スク `PROFILE`。ドア正面のままにしない。connect は cut。kiss 0.5
- walk 8秒: 通路を一人。connect は cut。`No penis` `The grown shaft is gone`

各枝の最後はあや一人。

## 正常位

受け入れ側は後頭部をリノリウムにつけて仰向け。肩も床。快楽に酔った笑顔、目は細める。体位名は書かない。あやは誘う M字の挿入と絶頂。ギンは犯すの `04-gin-in` と絶頂。

## ミキ冒頭（誘うの `01-cover`）

ミキは歩いている。あやが後ろから抱きついた瞬間に、ミキの足が開いたリノリウムの上で止まる。壁まで歩いてから止まらない。その停止と同じ瞬間、右側に T 字路の壁が見えてくる。足と壁のあいだにリノリウムが残る。抱きつかれた瞬間、ミキは空の眼窩のまま不気味な笑顔。`zombie` `corpse` `blood` は書かない。胸・腹・腰・腿は隙間なく密着。片手で胸を揉み、もう片方の手で勃起した 24cm を上下する。振り向くとき両手は竿から離れる。そのあとのべろちゅーが残りの尺。ミキの竿は lock も含めて全部 24cm。歩きは全身。口が付いたあとは、膝の上から顔まで。あやの顔とミキの顔は両方、画面の中。

## 誘う・抱擁

6番 `抱擁ベロチュー→壁片足→クンニ→両足抱え`。犬・スライム・獣・ギンには付かない。それ以外は spot の次から。キス LoRA 0.5。

- みき・れい・かな・しの: 相手が近づき、両手をあやの背中へ回して密着し、べろちゅー
- 角: 冒頭と同じ背後ハグ。胸を揉み、勃起した 24cm を上下。あやが振り向くとき手は竿から離れてべろちゅー
- 次: 竿役があやを壁まで押す。あやは背中を壁に、笑顔。片足は膝を外へ開き、もう片足は床
- 次: 竿役がしゃがみ、舌。トリガー `performing cunnilingus`。cunny 0.8。クンニの最終で相手は両足で立つ。しゃがんだ最終のまま hold に渡さない
- 次の hold: みき・れい・かな・しのだけ。すでに壁の同じ場所で向かい合い、両足は床。`{name} stands.` は工程にしない。両腕が腿の下に入り、抱き上げて足が床から離れるまで。両膝は上がる。足は空中、相手の腰の横。腕は背中。口は付いたまま。マンコは亀頭の DIRECTLY 前。竿は外。挿入は書かない。loco は planted にしない。extra は kiss 0.5 + mystic 0.5 + penis 0.45 + synth 0.4。thrust は積まない
- 次の in: 同じ4人。id は `03-kiss-in` `06-doggy-in` `09-join-in` `12-exit-in`。すでに足は空中。一度入れて根元。`HOLD still joined at the BASE until the last frame`。`one continuous press`。loco は planted にしない。extra は hold と同じ。角の抱擁 hold はこれまでどおり、抱き上げと挿入が同じ hold。`04-tsuno-in` は足さない
- 次の絶頂: 入ったまま、両膝は上がったまま。`keep the glans inside`。`HOLD still joined at the BASE until the last frame`。口は付いたまま。快楽の顔。Aya says 「あ、いく」。extra は kiss + mystic + thrust + jpnmoans 0.55。声は `あ、いく`。hold と歩きに jpnmoans は積まない
- 歩きは 8 秒。0–3 秒は笑顔のべろちゅーと涎の糸、竿は抜ける。3–5 秒で相手が右へ消える。5–8 秒はあや一人が右へ歩く

## 向き（キス・遭遇のあと）

向かい合いの最終から後ろへ入るとき、あやは壁向きのまま手を壁へ。相手が体ごとあやの後ろへ回り、同じ向きになる。胸はあやの背中。足は床。もう同じ向きの開始には、もう一度回らない。ネルソンは別。口のあと相手が後ろへ回り、両前腕を太腿の下へ入れて持ち上げる。

## 口のカメラ

ミキの騎乗前の口は、全身のままカメラを引く。ミキの顔は竿の横に全部残る。ショートの茶髪、空洞の目、紫の顔の裂け目、髪から顎まで。スタートは全身。ギン以外の口とキスは、二人の顔が画面の中に全部残る。竿役の顔も全部残る。かなの顔射はあやの顔と竿だけ。かなの顔は画面に出さない。カメラは顔が切れる距離まで寄らない。`zoom` と `Do not push the camera in` は書かない。正の文だけ。挿入に移る前に、カメラはまた全身まで引く。頭も足も全部。ギンの `04-gin-jupo` はこの顔フレームを足さない。

## 騎乗の LoRA

ギン以外の着座に sideride と thrust は積まない。着座は mystic 0.5、penis 0.45、synth 0.4。あやの騎乗絶頂（`03-kiss-peak` `06-doggy-peak` `09-join-peak` `12-exit-peak`）と `04-gin-peak` に sideride は積まない。肋骨跨ぎのまま。絶頂に mystic は重ねない。penis 0.45、synth 0.4、thrust 0.55 は絶頂に残す。角の `04-tsuno-peak` だけ sideride は 0.8。ファイルは `cowgirl-side-2-mh3-e50-az420.safetensors` のまま。あやのロックは `female body`。penis と futanari の否定はあやに書かない。

## 対面座位

誘い方の `sit` は `invite_pose_sit`。みき、れい、かな、しのの4カットにある。LoRA は kiss 0.5。

- みきの `03-kiss-zai1` は 0 秒からミキがすでに座っている。胴は直立、膝は曲がり、床にあるのはミキの両足、頭は RIGHT。24cm は股間から上。あやは LEFT から向かい合って腰を下ろす。太ももはミキの腰の外側。ふくらはぎはミキの背中の後ろでロック。あやの両足はミキの後ろで合い、床から離れる。あやの腕は肩、ミキの腕はあやの腰。胸が密着。24cm が根元まで入ったら `They HOLD still joined at the BASE until the last frame`。このカットは着座だけ。仰向けにしない。跪きから立つ入りと、`knees plant on the linoleum` と、あやの `feet stay on the linoleum` は書かない。extra は kiss 0.5。thrust と sideride は積まない。挿入なので Turbo は切る
- れい 24cm／かな 20cm／しの 35cm の `zai1` も同じ。相手がすでに座り、あやが向かい合って下ろす。脚は WRAP OUTSIDE / calves LOCK behind / feet meet behind, off the linoleum。`knees plant on the linoleum` は書かない。zai1 は上下しない。zai2 が上下。walk 本文は触らない。kiss 0.5 は残す。thrust と sideride は積まない
- `zai2`: 入ったまま、相手は座ったまま。あやは向かい合って直立。太ももは腰の外側、ふくらはぎは背中の後ろでロック、両足は相手の後ろで床から離れる。べろちゅーのまま腰は真上と真下。`ankles stayed crossed` は書かない。thrust は積まない
- `peak`: 同じ脚のまま中出し。口は付いたまま。終わったら唇をゆっくり離す。涎が糸を引く。お互い笑顔。thrust と sideride は積まない。誘うの最後は、この跨ぎからあやが背中を床へ倒し、竿は抜ける。`12-exit-drop` は 0 秒から仰向けで始めない
- `walk`: 8秒。最初に抜いて、笑顔で別れのべろちゅー。5秒以降はあや一人が右へ歩く。最後のコマはあやだけ

## ギンの口と騎乗

`04-gin-jupo` は閉じた唇が垂直の 24cm を根元まで下り、亀頭へ戻ってまた根元まで下りる。あやは 0 秒から仰向け。両掌と LIES BACK は書かない。0秒も最終も跪き。跨ぎは `04-gin-wait`。ギンは股の上に立ち、両足裏はあやの肋骨の左右、両膝は曲がったまま、マンコは亀頭の真上。STANDS は wait だけ。
ギンの容姿ロックは「舌が顎の下まで垂れる」ので、`04-gin-jupo`・`04-gin-ride`・`04-gin-peak` だけ拍の `cast_lock.gin` を閉じた唇、口の中の舌、女の股間に置き換える。`hanging out past the chin` と `lips pulled back` はこの3拍から消す。舐める拍の垂れ舌は残す。cunny の Look には 24cm を書かない。竿が残る文 `Aya's shaft written in that look stays erect` は jupo から付ける。

`04-gin-ride` はあやが仰向けのまま。乗るのはギン。参照は IMG_0718。両足裏は肋骨の左右、両膝は曲がったまま、腰は股の上。一度下ろして根元。`HOLD still joined at the BASE until the last frame`。着座に sideride と thrust は積まない。着座 extra は mystic 0.5 + penis 0.45 + synth 0.4。挿入なので Turbo は切る。fold 句は gin-ride と gin-peak に足さない。`04-gin-peak` も肋骨跨ぎのまま。sideride は積まない。結合のまま短い上下。亀頭は中。あやは Gin の中で終わり、WHITE goo は結合から溢れて根元の竿を伝う。根元は抜かない。`LIFTS` は書かない。04 の歩きは出口ではない。オプションを全部入れてもギンの次は `04-tsuno-meet-spot`。角の次の拍は `04-dog-spot`。犬の LoRA はページ URL しか無く、保存された HTML を重みとして読むと Comfy がそこで落ち、角の動画のあと生成が止まる。HTML は消して、その拍は LoRA なしで続ける。ミッション完了は最後の拍だけ。誘うでは最後も完了にしない。

## 生成棚卸しで直した3点

和式ミキの push / 挿入 / 中出し / gape。レンズは腰の後ろ下。フードは LEFT、扉は RIGHT。頭は左端の前腕の上、肩の前。首は頭と両肩をつなぐ。顔はその左端からカメラを見る。胸はタイル。腰は高い。両股関節は骨盤にある。各腿は股関節から膝へ下り、両膝は腰幅の外でタイル。すねと足は膝の後ろ、爪先は扉。肛門は上がった腰。ミキは両膝をあやの腿の外のタイルに置き、すねと足もタイル。骨盤はあやの尻の上。胸はあやの背中へ。背中と尻はカメラ。頭は一つ、首は一つ、あやの肩よりフード側。両手はあやの腰。jacko は push 0.45、挿入 0.40、絶頂と gape 0.35。0.8 は胸と尻が同じ向きに折れ、脚が直線に割れる。参照の崩れは Drive `1oeAMHQ6L7kyXr4R4Ch1RbqqC3puiU8lZ`。挿入は膝をタイルに置いたまま腰が一度下り、24cm は上から肛門へ根元。HOLD。cum は膝をタイルに置いたまま短い上下。gape は膝をタイルに置いたまま腰が一度後ろへ上がり、竿が肛門を出る。輪が開く。

`04-gin-mouth`。ギンの口と舌が亀頭の下。白い筋はギンの頬と舌。あやの顔は RIGHT の端。あやの舌はあやの口の中。ギンの look はこの拍だけ口を開け、舌を亀頭の下に出す。

人が残る文から角・翼・尾の名前を外した。残る二人だけを枠が持つ。犬は四本足のまま。角の lock から「not two eyes」「horned mask」を外し、小さな角が生え際に立つ。フルネルソンの絶頂は、足を下ろして抜く文をやめ、根元のまま HOLD。

## 騎乗の分岐

足は2種類。両方残す。新しい beat id は足さない。

- **細い柱**（今の足）。口の跪きから一度立ち上がる。両脚は真下、足首は近い。両足裏は肋骨のすぐ横の床。横から見ると手前の足が腹の前を横切る。足裏は床。THEN 両膝が曲がり、乗る人の両手が仰向けの胸へ付き、一度下ろして根元。HOLD。6番の「対面M字騎乗」と、シーンの「□誘う・騎乗・細い柱」と、ドロップダウン「騎乗・細い柱」。
- **曲げ膝**（姿勢の違いを聞く前の足）。最初から両膝は曲がったまま。両足裏は肋骨の左右、胸の左右に一枚。腰は股の上。体重は足裏。相手の両手が乗る人の胸。一度下ろして根元。HOLD。6番の「騎乗・曲げ膝」と、シーンの「□誘う・騎乗・曲げ膝」と、ドロップダウン「騎乗・曲げ膝」。

それぞれのドロップダウンの選択肢は なし、みき、れい、かな、しの、ギン、😈。選んだ人だけその足。なしはシーンのまま。同じ人を両方選ぶと細い柱。戦い構成のとき、みき・れい・かな・しのはシーンごとと同じで無視。ギンは「灰色・犯される」が曲げ膝、「灰色・騎乗・細い柱」が細い柱。😈は「角・騎乗」が曲げ膝、「角・騎乗・細い柱」が細い柱。ギンが乗るときはあやが仰向け。細い柱のギンはギンの手があやの胸。曲げ膝のギンはギンの手があやの乳房。あやが乗る曲げ膝は、仰向けの相手の手があやの乳房。あやが乗る細い柱は、あやの手が仰向けの相手の胸。絶頂はどちらも結合のまま、両膝は曲がったまま。

## 騎乗のカメラ

みき・れい・かな・しのの `*-wait` は、最後が直立の細い柱。口の跪きから一度立ち上がる。両脚は真下、足首は近い。両足裏は肋骨のすぐ横、手前と奥。横から見ると手前の足が腹の前を横切る。足裏は床。`Both knees stay bent` はこの4人の wait と着座の開始に足さない。共有の曲がった膝の文が逆Vに戻す。`*-ride` の 0 秒はその柱。THEN 両膝が曲がり、胴が竿役へ傾き、あやの両手が竿役の胸へ付き、一度下ろして根元。HOLD。竿役は仰向け、頭 RIGHT、足 LEFT のまま。長さはみき 24cm、れい 24cm、かな 20cm、しの 35cm。ギンの wait と着座は曲がった膝のまま。

ギン以外。横からの距離固定。全身、両足。同じ大きさ。竿役は仰向け、後頭部と肩はリノリウム、頭は RIGHT、足先は LEFT。勃起は股間から真上。あやの頭は LEFT。参照は IMG_0718。両足裏は肋骨の左右、胸の左右に一枚ずつ。両膝は曲がったまま。腰は股の上。体重は足裏。尻は腿の横へ落とさない。その姿勢は `Both knees stay bent. Hips stay over the groin. Weight stays on the soles.` と書く。みきの `03-kiss-wait` と `03-kiss-ride` はこの文を使わない。SQUATS は動詞にしない。マンコは亀頭の真上。一度まっすぐ下ろして根元。`HOLD still joined at the BASE until the last frame`。最終は `hips flush, the shaft buried to the root, both soles beside the ribs, both knees bent`。片腿上げと、片足を腰横の床、は書かない。着座に sideride と thrust は積まない。着座から消す語は SQUATS、sits beside、knees on the linoleum、LIFTS、folds down、Three separate lowers。絶頂も同じ足。`Short vertical moves keep the glans inside`。`Hips return flush`。着座の trigger に `side view riding sex` は付けない。親ビートの `kiss smack` と `wet jupo` は着座と絶頂の sfx に残さない。倒す工程は着座に書かない。`folds down` と `rises into the rider` は着座と絶頂の wrap に足さない。跪きから立つ工程も wrap が戻さない。口の 0 秒も最終も跪き。相手は仰向け、あやは腰の左で跪き、口は竿。跨ぎの足は `*-wait`。IMG_0718 は wait と着座。両足裏は肋骨の左右、両膝は曲がったまま、腰は股の上、マンコは亀頭の真上。着座は already その足。LOWERS 一度。HOLD 根元。STANDS は wait だけ。着座と絶頂の connect は chain。カットでも source を t2v に戻さない。あやの騎乗絶頂（`03-kiss-peak` `06-doggy-peak` `09-join-peak` `12-exit-peak`）に sideride は積まない。肋骨跨ぎのまま。thrust 0.55 は残す。短い上下は `Short vertical moves keep the glans inside`。絶頂の最終は `Thick WHITE goo OVERFLOWS from the join down the buried shaft and over the groin`。根元は抜かない。cmst は結合に積まない。`06-doggy-walk` の 0–3 秒は肋骨跨ぎのまま抜ける。立ちキスにしない。最終も根元。`LIFTS` は書かない。着座も絶頂も、画面の二人はあやと相手だけ。`nothing new enters` は書かない。乗るのはあや。ギンの着座はあやが仰向けで、ギンが跨ぐ。着座も絶頂も `The shaft stays buried to the root until the last frame`。`LIFTS` `PULL BACK` `SLIDES OFF` は書かない。あやの顔は快楽に酔った笑顔、口は開き、涎が垂れる。相手も同じ。ギンの jupo / ride / peak だけ唇は閉じる。歩きのべろちゅーだけ口を開く。`tired determined` は行為の Look から外す。`01-cover` の lock には残す。再生成は FRESH。口の最終は跪き。次は wait。wait の足から着座。着座の根元密着だけを絶頂の首にする。抜けは歩きの 0–3 秒。騎乗枝の歩きは connect chain。座位の歩きは触らない。今の Drive の着座と絶頂と抜け 3 本は使わない。

## キス音

「ちゅっ」は台詞にしない。唇が触れた音は sfx の `a lip-contact kiss smack when the mouths meet`。声は喘ぎだけ。

## かなの出会い

`07-kana-spot` でかなは右端から入った時点で竿をシコシコしている。WHITE goo は頭から竿、足、足元のリノリウム。通路の真ん中で止まる。あやは短い一歩で前に止まる。次の `07-kana` はその続きで、壁と手すりへ移さない。精液という語は書かない。

## 正常位と後背位の挿入

四つん這いと壁立ちバック、角の立ちバック（肛門の in と peak）は `siderear` 0.8 の次に `anuspussy` 0.40。灰色の誘う後背は膣のまま、同じ並び。`siderear` は `MMH3_NSFW_Doggystyle_Sex_3354622_epoch_20.safetensors`。Civitai 2967815、version 3362792、fileId 3250615。トリガー語は無い。`anuspussy` は `anus_pussy_v2.safetensors`。Civitai 2974434、version 3371009、fileId 3259145。カードの推奨はアニメ静止画で 0.9–1.2。参照動画は 1.0 で絵になる。病棟の写真調では 0.40。トリガーは `zxqanus` と `zxqvagina`。`zxqmei` はキャラトークンなので足さない。`doggy` は足さない。

四つん這いの in / peak と、壁立ちバックの in / peak（角の立ちバックも含む）だけ、カメラを差し替えた。横の `SIDE-REAR` は頬が穴を隠す。四つん這いは開いた太もものあいだ、低い、少し見上げる。肛門とマンコの両方が画面に残る。立ちは脹脛のあいだ、低い、少し見上げる。肛門はマンコの上の閉じた輪。結合部は画面中央。竿の線が見える。距離は固定。参照の後背位（Drive `1JXFwfFM0mghDbtFYMBzTv6vGZSDhGeyz`）は肛門。受けは胸と頬を床に置いたまま、顔を左肩越しに竿役へ戻す。竿役は最初から RIGHT に立っている。左から歩いて入らない。挿入前の拍は閉じた肛門に亀頭を押し当てて HOLD。steps 8、turbo false。次の拍で腰が一度前へ出て、閉じた輪が竿に沿って開き、根元まで入って HOLD。steps 8、turbo false。id は `03-kiss` と `03-kiss-in`、`06-doggy` と `06-doggy-in`、`09-join` と `09-join-in`、`12-exit` と `12-exit-in`。角の四つん這いは `04-tsuno-press` のあと `04-tsuno-in`。挿入の拍は結合が画面中央、開いた太もものあいだに竿の線。中出しの peak は steps 8、turbo false。頭は一つ、腕は二本、脚は二本。peak は右手を竿から離したまま短い前後。亀頭は肛門の中。マンコは肛門の下の閉じた割れ目。中出しは肛門。参照の立ちバック（Drive `16V50kQYP5XmGLxVAmTtyKYeAQPh4lApV`）の映像は膣。台本の壁立ちは肛門。あやは壁へ一歩、爪先で止まり、胴を倒し、両掌は壁。胸は床へ下がる。竿役の左手は腰、右手は亀頭を肛門へ置いて離す。一度前へ入れて根元 HOLD。peak は左手を腰に置いたまま速い前後。胸が揺れ、尻が揺れる。足は爪先。肛門は埋まったまま。マンコは下の閉じた割れ目。角の竿は `erect ashen-gray 24cm`。あやに竿は生やさない。connect 欄は変えていない。灰色の誘う後背は膣のまま。右手で亀頭をマンコへ置き、肛門は上の閉じた輪。

灰色の誘う後背は、これまでどおり `SIDE-REAR view. The frame holds a clear view of the shaft where it meets the pussy.` 歩き、顔射、キス、騎乗、M字、角の後ろアナル、ネルソン、背後抱きの meet、寝室スプーン、犬、和式、洋式 pee、寝室 Jack-O にはこのカメラを足さない。古い `doggy`（fileId 3202556）は登録のまま、extra には積まない。action に `Doggy style` は書かない。

## 後ろアナル（Jack-O）

6番とシーンごとは「後ろアナル」。灰色は「灰色・後ろアナル」。今の行為は残す。別枝。角の寝室 Jack-O、和式、犬、pee、立ちバック、スプーン、ネルソン、ギンの犯す枝は触らない。参照は Civitai 143781618。Drive `1tyXGve` には寄せない。

受けは顔と胸が床。頭は肩の前。首は一つ。腰は高い。割れは上。両股関節は骨盤。各腿は股関節から左右へ下り、膝は少し曲がり、かかとは床で腰より低い。理想の見え方は Drive `1_MFyeObobSWEcsCmBoS7Q67aojCQcIt0`。竿役は腰の上。両足は床。膝は曲がる。胸は受けの背中へ。背中と尻はカメラ。頭は一つ、受けの頭の先。竿は上から肛門。距離は固定。結合部は画面中央。みき・れい・かな・しのはあやが受け。あやの股間は hairless pussy。長さはみき 24、れい 24、かな 20、しの 35。ギンはギンが受け。あやの grown erect 24cm。ギンの犯す本文は残す。

id は `03-kiss-jo` `06-doggy-jo` `09-join-jo` `12-exit-jo` に `-set` `-behind` `-anal` `-cum` `-gape` `-kiss`。かなは顔射とキスのあとに続ける。灰色の Jack-O は、先に `04-gin-lick` `04-gin-cunny` `04-gin-jupo` `04-gin-mouth` `04-gin-spitkiss`。ふたなり化、じゅぼ、口の中への WHITE、口移し。そのあと `04-gin-jo-set` でギンが姿勢を作り、`04-gin-jo-behind` であやが腰の上に立つ。それから肛門へ。口の中の WHITE は口に留まる。肛門の WHITE は肛門の結合に留まる。ギンのマンコも、あやの竿の付け根のマンコも、閉じた割れ目のまま。set は connect cut。jacko は set と behind が 0.8、anal が 0.7、cum と gape が 0.65。doggy は積まない。set と behind の最終は未挿入。参照の動きは Drive `1_MFyeObobSWEcsCmBoS7Q67aojCQcIt0`。set は受けが膝を曲げ、顔と胸を床へ、腰を上げ、両脚を左右へ伸ばす。頬は床。口は開く。肛門は割れの上、マンコはその下の閉じた割れ目。竿役は横に立ったまま、竿は外。behind は竿役が腰をまたいで立ち、膝を曲げ、尻をカメラへ。右手が上から下がる竿を肛門へ導き、手を離す。最終は外。anal は竿役の腰が一度下り、受けの頬は床、口が開き、両脚はまっすぐ、両足は床。上から肛門へ根元。HOLD。「気持ちいい」。cum は膝が少し曲がり、腰が少し上がって竿が輪へ寄り、亀頭は中。また腰が下りて尻に戻る。マンコは閉じた割れ目。溢れ。「あ、いく」。ギンの cum は腰を下ろしたまま、最初から最後まで肛門に埋まったまま。gape は膝が伸び、腰が一度上がり、竿が出て輪。kiss で立って口が付き、相手が右へ消え、あや一人が歩く。寝室の Jack-O はベッドの向きのまま。角は膝を曲げて腰を一度下ろし、上から肛門へ。あやの胸と頬はマットレス、顔は扉、腿は窓。

騎乗の口 `03-kiss` `06-doggy` `09-join` `12-exit` は、最初のフレームから竿が既に全長で立っている。途中で生やさない。騎乗の peak は腰を股に下ろしたまま、竿は最初から最後まで根元。短い寄せは亀頭を中に残す。

着座は一回の押し。腰と尻が密着し、竿が根元まで入ったところで止める。先だけ、半分、往復は書かない。ピストンは次の絶頂。`12-exit` の正常位は 0 秒からあやが仰向け、しのは腿の間、35cm は根元、`HOLD still joined at the BASE until the last frame`。立ちキスにしない。立ちキスは `12-exit-kiss` だけ。

## 中出し

しのの誘うと戦って負けるの出口は `Shino finishes INSIDE`。他の体位の絶頂は既に中。口は口内。触手は汚液で中を満たす。

## トイレ

洋式触手の行為 `04-toilet` は 0 秒から触手4本。左乳首、右乳首、マンコ、口。`KEEP THRUSTING` は書かない。`HOLD still joined at those four places until the last frame`。Aya says 「気持ちいい」。声欄はひらがなの `きもちいい`（漢字は声欄に置かない。H3 が読み違える）。extra は tentacles3d 0.45 + mystic 0.5 + jpnmoans 0.55。2D-General は登録しない。ThumbInButt / doggy / jacko / thrust / Turbo は積まない。続く fill も同じ4箇所のまま。汚液はマンコと口へ。肛門と `KEEP THRUSTING` は書かない。出の最終はあや一人。`The tentacles are gone`。`No tentacles` は書かない。

小便は、座りが正面の M 字になってから。あやは笑顔のまま、腰は止めたまま、便器も止めたまま。液体は透明なレモン色の黄色い水。見透ける水で、一本の明るい黄色の柱。マンコからその黄色い水をカメラの正面へ飛ばす。動くのは黄色い流れだけ。便器の中へ流す文は書かない。否定の「動かない」は書かない。

洋式の指枝は、床の吸盤に立った極太のペニス形。小便は触らない。ThumbInButt はこの枝から外す。和式の排出は ThumbInButt のまま。順番は `04-toilet-toy` でしゃがみ、両足は植物の縁の外、肛門は穴の中央、玩具は外。次の `04-toilet` で腰を一度下ろし、根元まで HOLD。「気持ちいい」。`04-toilet-pump` は短い上下で絶頂、溢れ、「あ、いく」。`04-toilet-gape` で腰を一度上げ、玩具が抜けて落ち、輪が開く。`04-toilet-out` で立って歩く。extra は mystic 0.5 + penis 0.45。pump は jpnmoans 0.55 を足す。一人の拍に thrust は積まない。jacko と doggy と ThumbInButt は積まない。

和式は洋式個室。洋式便座は出さない。便器は和式パン。カメラは洋式アナルと同じ低い後ろ下。あやの背中がカメラ。顔はフード。赤い靴は書かない。squat と spot の 0 秒は `Aya already SQUATS deep over the plant mouth, heels on the tiles, both feet planted OUTSIDE the fleshy plant rim of the plant mouth, knees open, anus over the CENTER of the hole, face toward the hood.` `folded over the pan` は書かない。和式パン専用の H3 LoRA は市場に無い。Illustrious の squat toilet LoRA は積まない。

排出はしゃがみの次。棒が肛門から穴へ繋がったまま。ThumbInButt 0.55。

和式のパンは床のタイルと同じ高さ。足はタイル。汚れはタイルと縁とフードと壁。ミキ枝は全拍 connect chain。順は in → squat → spot → push → 挿入 → cum → gape → out。排出枝に gape は足さない。spot はミキの顔も体もフード向き。掌は尻を RUBS。24cm は尻の前で未接触。あやに竿は書かない。`04-toilet-push` は未挿入。extra は jacko 0.45 + mystic 0.5 + jpnmoans 0.55。futatf は積まない。doggy は積まない。竿はミキの 24cm が1本。Jack-O は push から gape まで同じ骨格。参照は Civitai 143781618。両前腕はタイル。頭は前腕の上、肩の前。首は一つ。顔は左端からカメラ。胸はタイル。腰は高い。尻はドア。両股関節は骨盤。膝はタイル、腰幅の外。すねと足は膝の後ろ、爪先は扉。ミキは膝をタイルに置き、胸はあやの背中、背中はカメラ。挿入も絶頂も抜きもこの骨格のまま。out は抜きのあと、二人とも一度立ち上がり、口が付き、ミキが右へ消えて、あや一人が廊下を右へ歩く。out に jacko は積まない。24cm は割れ目の前。Aya says 「やばい、だめ」。最終は胸と頬がタイル、腰は高い、顔はカメラ、24cm は割れ目の外。排出に Jack-O は積まない。挿入は文章のまま肛門。`The erect 24cm TRAVELS INTO the anus to the root`。`HOLD still joined at the BASE until the last frame`。Aya says 「気持ちいい」。挿入 extra は jacko 0.40 + mystic 0.5 + penis 0.45 + jpnmoans 0.55。doggy / ThumbInButt / Turbo は積まない。絶頂は keep the glans inside。WHITE goo は結合から溢れる。根元は抜かない。Aya says 「あ、いく」。絶頂 extra は jacko 0.35 + mystic 0.5 + penis 0.45 + thrust 0.55 + jpnmoans 0.55。声は各カットの「」1句（`きもちいい` はひらがな）。`04-toilet-gape` は 6 秒。extra は jacko 0.65。すでに結合。胸と頬はタイル、腰は高い、両脚は左右、顔はカメラ。腰を一度後ろへ。24cm が肛門を出る。肛門は wide ring。WHITE goo が輪から穴へ垂れる。最終は胸と頬がタイル、輪、垂れた goo、ミキは後ろ。out は向き直してべろちゅーして右へ。抜きは out に書かない。竿はミキ 24cm。あやに竿は生やさない。キス歩きは kiss 0.5。kiss と walk に jpnmoans は積まない。

## かなの顔射のあと

`cast.aya.looks.white_upper` の追加文は `thick extra-viscous sticky WHITE goo clinging to Aya's face, hair, neck, breasts, shoulders, and chest`。`09-kana-facial` の 0 秒 Look には goo を書かない。着地は action。最終は顔と胸。`09-kana-kiss` `09-join*` `10-shino*` `12-exit*` のあや Look にその文が残る。顔射を通らない話は基本 lock のまま。semen / cum / 精液 は書かない。顔射は既存 id のまま。connect 欄は cut。カットを選ぶと正面を独立に描く。チェーンと着地では前の最終フレームから I2V。0 秒からその正面を保持する。同じドアがあやの後ろに残る。あやはレンズを見上げる。かなの 20cm は下端から顔へ向く。WHITE rope が顔と胸へ落ちて留まる。Aya says 「いっちゃった」。声も `いっちゃった` の1句。sfx は肌に当たる音。キスの music は継がない。かなの顔は画面に出さない。extra は cmst 0.65 + penis 0.45 + jpnmoans 0.55。sideride / thrust / Turbo は積まない。8–12 秒、1 工程。`09-join-peak` は中出しのまま。顔射に置き換えない。

## かなの着座（`09-join-ride`）

口の 0 秒も最終も跪き。かなは仰向け、頭は RIGHT、足先は LEFT。あやは腰の左で跪く。跨ぎは `09-join-wait`。あやは股の上に立ち、両足裏は肋骨の左右の床。マンコは亀頭の真上。カメラは全身のまま引いた距離。着座はかながすでに仰向け、頭は RIGHT、足先は LEFT。あやは股の上に立ち、両足裏は肋骨の左右の床。マンコは亀頭の真上。一度まっすぐ下ろして根元。HOLD。かなの両手はあやの胸。片腿上げとスクワットは書かない。口カットの途中で着座へ変形しない。あやを仰向けにしない。

## ネルソン

向かい合い（口が付いたあと）から相手が後ろへ回り、両前腕を太腿の下へ入れて持ち上げる。画面はあやがカメラ向き、相手の顔はあやの頭の後ろ。足は空中。`feet leave the linoleum` は書かない。角は遭遇の立ち（後ろ、亀頭が肛門）から同じ持ち上げ。植えの性行為は大人2人、顔2つ。体を増やさない。持ち上げたあとは同じ床の位置。`Feet do not travel` `does not travel` `does not scroll` は足さない。否定の移動は移動として描かれる。

## カメラ

スタートは全身。頭の上に余白、足先の先に床。ギン以外のミキ冒頭キスは、口が付いてから膝の上から顔まで。竿は画面に残る。二人の顔は切らない。ギン以外の口とキスは二人の顔を全部残す。竿役の顔も全部。かなの顔射はあやの顔と、下端から狙う竿。かなの顔は画面に出さない。カメラは顔が切れるところまで寄らない。挿入の前に全身へ戻す。顔が見切れることだけは不可。行為の前は二人とも全身。`zoom` と `Tight` と `standing close` は書かない。横スク lock の `tracks only left and right` は距離固定に置き換える。`half-step closer` は消す。ギンのカメラはこの訂正を足さない。

## あやの汚れ

体中に粘つく `thick extra-viscous sticky grimy brown hospital dirt`。顔と股だけにしない。

## ミキの汚れ

裂け目と汗はそのまま。`blood` は書かない。粘つく汚れは裂け目の間の intact purple skin と髪に付ける。

## ギンの汚れ

頬・肩・腿の剥けた赤筋繊維はそのまま。粘つく汚れは残った灰色の肌、髪、手足に付ける。筋繊維の文は残す。

## 容姿の持ち越し

`Look that stays` の竿文は、lock に shaft / penis / Ncm がある人の名前だけ付ける。ギンの遭遇に竿文を足さない。

## 4枠

ドロップダウンの既定は全部「出ない」。灰色・角・犬・異種は同時にオンしてよい。犬をオンにしても灰色はオフにしない。1カットの追加相手は一人。各枠の最後はあや一人歩き（`No penis` `The grown shaft is gone`）。次の `-spot` へ渡す。

順番（オンのものだけ）: トイレのあと → 灰色 → 角 → 犬 → 異種 → れい。

角を「出ない」にしてもトイレは消えない。トイレは別ドロップ。オフは角だけ飛ばす。

`HOSPITAL_ENCOUNTERS` には入れない。`OPTIONAL_ENCOUNTERS` に `dog` と `species` がある。

## 犬

`04-dog-spot` は I2V 6秒。あやは画面 LEFT、体は RIGHT 向き。四つ足は RIGHT にすでに立ち、頭は LEFT、尾は RIGHT。右端から飛び込まない。並走しない。背中は水平、頭は低い。肩はあやの腰より高い。竿は腹の下、後肢のあいだ。extra は mystic 0.5 + furryenh 0.55。人間後背の Doggy LoRA は `LORA_FILES["doggy"]` に fileId 3202556 を登録するだけ。今の extra にも犬 overlay にも Jack-O の push にも積まない。action に `Doggy style` は書かない。Eleptor は犬に積まない。spot から lick まで、頭 LEFT と尾 RIGHT を毎カット繰り返す。回す文は jupo だけ。

- 回避: あやは左へ走る。四つ足は右に残る。spot の向きは他の枝と同じ
- 受け入れる: spot の camera と action だけ同じ向き。あやは右の壁。手は壁。足は床。後脚立ち。腰が一度前へ出て、24cm が尻に当たるまでマンコへ入る。そのあと短い前送りで亀頭は中。向きと後脚立ちは残す
- 誘う伏せ: その場で仰向け、舌。wait は胸と頬が床、膝を畳む。犬は同じ向きで背中に覆う。着座は根元まで HOLD。着座に thrust は積まない
- 誘う口: 同じ舌のあと、wait は仰向け M字 のまま。うつ伏せにしない。wait は connect chain。`04-dog-lick` と `04-dog-lick-peak` は connect chain。invite から cum まで chain。walk の end はそのまま。lick のカメラはマンコと顔。lick-peak の最終は全身の横。向き文と舐め動詞は変えない。`04-dog-jupo` と `04-dog-mouth` は後肢があやの頭 LEFT、腹側の竿が1本、口へ、犬の頭は RIGHT。mouth は唇が根元。`04-dog-in` はあやが仰向け、後頭部と肩は床、頭 LEFT、足 RIGHT。四つ足はすでに股の上、頭 LEFT、尾 RIGHT、四本の足は床に着いたまま。腹の 24cm は亀頭がマンコへ向く。腰が一度前へ出て、亀頭がマンコに付き、根元まで入る。HOLD。カメラは同じドアを保持する。尻に当てる文は書かない。`04-dog-cum` は 0 秒からすでに根元。`HOLD still joined at the BASE until the last frame`。`finishes INSIDE`。WHITE goo は結合から溢れる。根元は抜かない。挿入なので Turbo は切る。着座は平らな床。段差なし。着座に thrust は積まない

## 異種

スライムとケモノは XOR。両方オンにしない。歩きはギンと同じ。左端から真後ろ。あやが恐る恐る止まる。spot はそこで終わる。天井から落ちない。LUNGES は書かない。種 LoRA は調味だけ。あやの肌・汚れ・蛍光灯は I2V の前フレーム。action に anime / cel は書かない。あやの lock は触らない。

- スライム: https://civitai.com/models/2533949 ファイル `slime_girls-MMH3-v1.0.safetensors` トリガー `slime_girls` 強度 0.45。meet は背後から密着したまま、腰が一度前へ出て亀頭が入った瞬間に止まる。peak は短い前送り、亀頭は中、腰は戻る
- ケモノ: https://civitai.com/models/2945034 トリガー `(anthro wolf:1.4)` 強度 0.45。amateur 0.35、penis 0.45、synth 0.4。meet と peak の腰はスライムと同じ。毛と口先は今の lock のまま
- 四つ足: https://civitai.com/models/1782485/furry-enhancer-video 強度 0.55
- 広げる: `minimax_h3_pussy_spread_v0.2.safetensors` 強度 0.50。fileId は置かない
- クンニ: https://civarchive.com/models/1971266?modelVersionId=3318405 ファイル `cunny-mh3-e62-az420.safetensors`
- アナル指: 洋式の指枝は吸盤のペニス形。ThumbInButt は積まない。ファイル `MiniMax H3 - ThumbInButt.safetensors` fileId 3168734 は和式排出に残る。ページ URL は重みにしない

## 禁止語

`blood` `zombie` `corpse` は書かない。ウジ・蛆・虫の語も書かない。ライセンス名も書かない。体位名は書かない。犬と異種の action に `futanari` も書かない。画面の数字は 24cm / 20cm / 35cm だけ。ミキも 24cm。

## 本数

誘う・触手・灰色の騎乗・角の後ろアナル・シーンごと（みきM字、れいフルネルソン、かな騎乗、しの騎乗）は cunny を含めて 49 本。犬と異種を足した枠の上限は `MAX_BEATS` 80。

## メモリ

成功したカットの前に VRAM は下ろさない。メモリ不足でそのカットが失敗したときだけ下ろし、同じ尺をもう一度描く。それでも足りなければ短い尺に落とす。フォームに毎回解放のスイッチは置かない

## 開始シーン

Colab の **開始シーン** が空なら最初から。beat id を書くと、そのカットから先を今のドロップダウンで作り直す。並びは `prepare_episode` の結果だけ。構成・トイレ・灰色・角・犬・異種・登場・シーンごと・つなぎ方が違う話の id は、その並びに無いので止まる。前のカットは残して首にする。チェーンの前の動画が無い、または前のカットの記録が今の設定と違うときは、そこまで戻って描く。FRESH をオンにして開始シーンが空なら全部作り直す。開始シーンがあるときは、それより前は FRESH でも残す。

## 便器の定義と 2026-10-03 の直し

便器は三択。洋式汚物まみれは小便・オナニー・ディルド。白い磁器に茶色の汚れ。和式汚物まみれは和式排出と和式ミキ。床と同じ高さの和式パンに茶色の汚れ。有機物植物の洋式は触手だけ。植物のボウルに粘液。触手は有機物便器以外に出さない。ディルドは洋式汚物の便座の横。右手で持つ。吸盤も植物の口も使わない。extra は `solodildo` 0.7 と mystic。penis は積まない。ファイル `dildoing-mh3-e60-az420.safetensors`。Civitai 2903074、version 3282820、fileId 3167066。カードに強度の数字は無いので 0.7 のまま。トリガーは `pumping a dildo insider her vagina`。洋式のディルドは膣をポンプする。入れる拍 `04-toilet` と上下の拍 `04-toilet-pump` は steps 8、turbo false。ディルドは同じ太い竿形のまま、右手は付け根を持つ。1拍に拾う・入れる・上下・絶頂を重ねない。便器のボウル、座面、タンクは床に固定。あやは肩越しに快楽の顔を見せる。小便の `04-toilet` も同じ固定と、酔った喜びの顔。

顔射は `cumfacial` 0.8。ファイル `cum_facial_000005400.safetensors`。FunPhantom version 3290895、fileId 3175377。公開名は `face_cum_000001000.safetensors`。トリガーは `cmst` を先に置く。ページの開始帯は 0.75–0.85。ギンの口は先に竿が口の外へ出て、白い筋はギンの顔と舌だけ。あやの口は閉じ、あやの顔はきれいなまま RIGHT の端。かなの顔射と角の顔射も同じ LoRA。あやの顔へかける顔射はかなと角のまま。`10-shino-spot` は角ではなく、しのが入口で最初から前かがみ。頭は管の下。右から歩いて入らない。`10-shino` の誘うはキスしない。あやはしのの一歩手前に留まる。扉はしのの後ろ。歩き拍から外したので、廊下の先へ進まない。マンコへ入る着座と、ギンがあやの竿を入れる着座は、着いた瞬間のあやの顔を足す。目は半目、頬は赤い、口は開く、涎が舌から切れずに垂れる。未知の快楽の喜び。肛門の四つん這いには足さない。

ギンの Jack-O の set は、あやが先にゆっくり立ち、それからギンが姿勢を作る。挿入はしない。behind は尻の後ろへ回り、同じ方向を向いてから立つ。腕は2本。anal で入れる。床の Jack-O も、竿役は尻の後ろへ回ってから同じ方向を向く。

角の口は、角の手が竿を離してマットレスに残る。あやの口だけが竿に付く。blowjob 0.8 はそのまま。

角の横は、角の頭が画面 LEFT、足が RIGHT、全身がマットレス。あやも頭が LEFT。キスのあいだ竿は外。次の ride で入れる。

立ちバックと四つん這いは肛門。anuspussy 0.40。カメラは横。あやは LEFT 向き。竿役は RIGHT で同じ方向。しのの竿は 35cm。抱擁の生成文、曲げ膝の跨ぎ、誘う最後の look、容姿の竿句も 35cm。lock と同じ。

チェックポイントは `eros-max` と `dasiwa`。既定は 10Eros Max。DaSiWa は Hybrid v2 int8、fileId 3203130。

□誘うの壁立ちバックと四つん這い股広げは、横からのアナル。siderear 0.8、anuspussy 0.40。竿は肛門。終わりはあや一人。角・誘う立ちバックの `04-tsuno-in` `04-tsuno-peak` は壁立ちバックと同じ動き。その前の `04-tsuno-meet` は、抱きながら肛門へ入れる拍として残す。角・後ろアナルの `04-tsuno-in` `04-tsuno-peak` は四つん這い股広げと同じ動き。その前の `04-tsuno-meet` は、壁で胸を掴んで入れる拍として残す。人間が「立ちバックだけ」「四つん這いだけ」と言うまで、その前拍は消さない。どちらも終わりは角が消えてあや一人が歩く。受け入れる立ちバックとフルネルソンの peak から、横寝の文は外した。横寝は病室の横挿入だけ。

二人が出る場面の終わりはベロチュー。0–3 秒は向き合って舌を絡め、3–5 秒で相手が右へ消え、5–8 秒であや一人が歩く。extra は kiss 0.5。犬、触手、小便、オナニー、ディルド、和式の一人排出は付けない。

チェックポイントと LoRA の取得は CPU で足りる。ランタイムが CPU のとき、ノートは `H3_WEIGHTS_ONLY=1` を置き、Drive へ取って止まる。Comfy は起動しない。動画は A100 でもう一度 Run all。1MB を超える同名ファイルは取り直さない。

「前の最終フレームから続ける」は、1本目だけ T2V。2本目以降は I2V。新しい人は -spot が先に入る。

しのの抱擁は `12-exit-hug` から `12-exit-walk`、曲げ膝の跨ぎは `12-exit-wait` と `12-exit-ride`、誘うの最後でしのが残る look も 35cm。raw が既にあり FRESH がオフなら作り直さない。直すときはその拍だけ FRESH。生成ボタンは人間。直した終わりの FRESH は `03-kiss-walk` `06-doggy-walk` `09-join-walk` `12-exit-out`、角とギンの `04-*-walk`。

## 作業の終わり

1. テストが通る
2. `colab/` と `minimaxh3/` の対応ファイルが同じ
3. このブランチへコミットして push
4. PR #147 の説明を、変わった事実だけ直す
5. 人間へ Colab リンクを返す。再生成は FRESH。直した拍だけ。角の横挿入は `04-tsuno-spit` `04-tsuno-beckon` `04-tsuno-lie` `04-tsuno-sidekiss` `04-tsuno-ride` `04-tsuno-peak`。寝室 Jack-O に spit は付けない。駅弁の hold は抱き上げのまま。後ろアナルは `03-kiss-jo-set` から `03-kiss-jo-kiss`、同じ並びの `06-doggy-jo` `09-join-jo` `12-exit-jo`、灰色は `04-gin-jo-set` から `04-gin-jo-kiss`。抱擁の抱き上げは `03-kiss-hold` `06-doggy-hold` `09-join-hold` `12-exit-hold`、挿入は同じ親の `-in`。洋式ディルドは `04-toilet-toy` `04-toilet` `04-toilet-pump` `04-toilet-gape` `04-toilet-out`。四つん這いと壁立ちバックの in / peak は、低い結合カメラに差し替えた。FRESH は誘うの四つん這いと壁立ちバックの `03-kiss` `03-kiss-peak` `06-doggy` `06-doggy-peak` `09-join` `09-join-peak` `12-exit` `12-exit-peak`。角は受け入れる立ちバックと誘う立ちバックの `04-tsuno-in` `04-tsuno-peak`。角の口 `04-tsuno-oral` に blowjob 0.8 と `bl0w_j0b` を足した。横挿入と寝室アナルの両方。角の二人は、同じ画面にいる拍で lewd pleasure-drunk happy smile。口が塞がる拍と、向きを固定した拍は、その姿勢のまま。あや一人の歩きと connect 欄は変えていない。FRESH は角を出す枝の `04-tsuno-meet-spot` から最後まで。前回に足す分は、角の `04-tsuno-ride` `04-tsuno-ride-kiss`。ギンの `04-gin-mouth` `04-gin-spitkiss`。和式ミキの `04-toilet-in` `04-toilet-squat` `04-toilet-spot` `04-toilet-push` `04-toilet` `04-toilet-cum` `04-toilet-gape` `04-toilet-out`。排出の和式は個室の高さが変わった `04-toilet-in` `04-toilet-squat` `04-toilet`。和式排出の ThumbInButt 本文はそのまま。座位の zai、ネルソン、洋式の小便、角の寝室 Jack-O、角の個室 stall、犬、立ちバック、スプーン、ギンの犯す、jupo、Wan ノートは触っていない。抱擁は4人の hold を抱き上げだけにし、挿入を `-in` に分けた。洋式の指枝は吸盤のペニス形にした。raw が既にあるカットは、FRESH がオフだと作り直さない。通路クリップを個室の首に使わない。抜け 3 本（`13rHcn` `1QbWMV` `1cqrvu`）と駅弁 5 本は首にしない。`1cqrvu` は角ではない。`04-gin-peak`
