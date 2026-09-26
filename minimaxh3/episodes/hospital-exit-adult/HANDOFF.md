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

## Wan 2.2（H3 の横。H3 ノートは置き換えない）

描画だけ Wan 2.2。台本・ドロップダウン・HUD 結合は H3 の `prepare_episode` と `finish_episode` のまま。

- コード: `colab/wan_episode.py`（`minimaxh3/wan_episode.py` と同じ）
- 入口: `colab/wan_episode_colab_main.py`
- ノート: `wan_hospital_episode_bot.ipynb`。最初のセルで OneDrive をマウントし、次のセルの **CivitaiのAPIキー** にキーを貼る。生成セルは人間が実行する。キーもトークンも空のまま保存する
- 保存先: OneDrive（`WAN_ONEDRIVE_ROOT`、既定はこの PC の `OneDrive/wan-hospital`）。Google Drive には書かない
- `source` が t2v のビートは Wan T2V。開始画像なし。chain と still だけ、前のビートの最終フレームを開始画像にする
- `extra_loras` の名前は残す。中身は Wan 2.2 の high / low 組（`wan-<名前>-high.safetensors` と `wan-<名前>-low.safetensors`）。high は high expert、low は low expert にだけ付ける。一覧は `WAN_SLOT_LORAS`。ファイルが無いスロットは強度 0 で飛ばす。H3 の重みと `pose_motion_lock.py` は読まない
- 用意された動作に合う LoRA だけ Wan が足す。肛門への挿入は `anal`（high 2161023 / low 2161067、トリガー `anal sex`）。抱え上げたフルネルソンは `nelson`。四つん這いは `doggy`。仰向けの相手の間は `missionary`。黄色の放尿は `pee`。和式の排出は `scat`。親指だけの肛門、歩き、角・騎乗の跨ぎには肛門 LoRA を付けない。台本の文は変えない
- Colab: `wan_hospital_episode_bot.ipynb`。0 で OneDrive をマウント、1 で重み（Civitai のキーはここ）、最後のセルで生成。人間が実行する
- テキストエンコーダは umt5
- テスト: `python3 -m pytest colab/test_wan_episode.py -q`。H3 の `colab/test_h3_episode.py -q -k hospital` は壊さない

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
- 同じ相手の次の行為、ポーズ、トイレ、灰色、角、戦いも I2V。台本の `connect: t2v` は、この病棟でチェーンを選んだときは効かない
- 「カット」を選ぶと全部 T2V。ただし着座と絶頂で connect が chain の肋骨騎乗は、カットでも I2V のまま。ギンの `04-gin-jupo` `04-gin-ride` `04-gin-peak` も同じ
- 角・騎乗の wait と walk、角・個室の stall と stall-kiss と walk は connect が cut。チェーンを選んでも T2V。通路の最終フレームを個室の首にしない。個室のキスはドア正面の続きにしない
- ギンの `04-gin-cunny` も connect が cut。チェーンを選んでも T2V。尻餅の最終と、すでに竿がある最終を、成長カットの首にしない
- 受け入れる＋灰色・犯される＋角の立ちバック＋トイレ＋4人登場で測ると、T2V は `01-cover` と `04-gin-cunny`。遭遇も I2V

遭遇を足す関数は `insert_presence_beats`。spot は最初から `source: chain` `connect: chain` で作る。`keep_chain_cast` は `-spot` の新人を T2V に戻さない。遭遇を消さず、遭遇自体を chain のままにする。遭遇カットでは前のカットの余分な人を残さない。

## 容姿

初期の見た目は `cast` の `lock`。そのカットだけ違うときは `cast_lock`。汚れ、傷、粘液、髪、肌の色、竿の長さと色はここに書く。

各病棟カットのプロンプトには `Look that stays for this whole shot` が付く。否定の句（`no` `never` `not` `without`）はそこから落とす。竿を消す歩きだけ、action に `No penis` と `The grown shaft is gone` と書く。その歩きには竿を戻さない。

チェーンの I2V は、前フレームが汚れや竿を落としていても、`subject_definitions` の見た目に戻す。

遭遇 `-spot` も同じ Look を付ける。action にあやの grimy brown hospital dirt を書く。新人は already ではなく、画面に入ってくる。

## ギンの騎乗（`灰色・犯される`）

- 遭遇 `04-gin-lick-spot` は I2V。前フレームのあやに続ける。ギンは画面左端から入る。視聴者から見てあやの左＝あやの真後ろを、あやの歩幅に合わせて歩く。あやの歩きは徐々遅くなり、恐る恐る立ち止まる。あやは右、ギンは左。天井から落ちる構図は使わない。あやは右向きのまま
- `04-gin-lick`: あやは恐る恐る振り向いて、尻餅は右側。頭は画面右、足先は左。そこがゴール。ギンは左でしゃがみ、長い舌があやのマンコとクリを下から舐め続ける。竿は生えない。ギンもあやも竿なし。容姿・汚れ・眼窮はそのまま。`futanari` の語は書かない。右端は暗い通路が続く。壁という語は書かない。extra_loras は mystic + cunny。トリガー `performing cunnilingus`
- `04-gin-cunny`: 0秒はすでに仰向け。後頭部と肩はリノリウム。頭は RIGHT、足は LEFT、両膝は開く。マンコだけ。Look に 24cm を書かない。倒れる工程は書かない。舌はクリを舐め続ける。そのあとクリが直立の 24cm に生える。生えた瞬間、顔は wide-eyed surprised joyful excited smile。ギンは新しい竿を一度舐める。最終は仰向けのまま 24cm が真上、ギンは左でしゃがむ。extra は cunny 0.8 + mystic 0.5。futatf と penis は積まない。`Aya's shaft written in that look stays erect` は付けない。connect は cut
- `04-gin-jupo`: 0秒から仰向け＋24cm。cunny の最終を継承。倒れる工程は書かない。座ったまま、両腕を後ろ、LIES BACK、マンコが真上、は書かない。ギンは腰の左で跪き、閉じた唇。快楽に酔った笑顔。閉じた唇が根元まで下り、亀頭へ戻ってまた根元まで下りる。24cm は口の中。最後も仰向け、唇は根元。Look の竿文はここから付ける。connect は chain
- そこから既存の分岐（騎乗 / 正常位 / 後背）。成長とジュボは別カット。犯すと誘う後背の cunny 本文は残す
- `04-gin-ride`: 乗るのはギン。あやは仰向けのまま。ギンはすでに股の上に立ち、頭は LEFT。両足裏は肋骨の左右、胸の左右に一枚ずつ。マンコは亀頭の真上。一度まっすぐ下ろして根元。`HOLD still joined at the BASE until the last frame`。両手はあやの胸。SITS ON、SQUATS、三度下ろす、STANDS UP、steps over、folds down は書かない。extra は mystic 0.5 + penis 0.45 + synth 0.4。sideride と thrust は積まない。connect は chain。新しい id は足さない
- `04-gin-peak`: すでに結合。あやは仰向け、頭 RIGHT。ギンは股の上、足裏は肋骨の左右。短い上下は `Short vertical moves keep the glans inside`。あやは Gin の中で終わる。根元のまわりに少し WHITE goo が残り、中に留まる。最終も根元。`LIFTS` は書かない。extra は sideride 0.8 + penis 0.45 + synth 0.4 + thrust 0.55。mystic は積まない。connect は chain。再生成は FRESH。順番は cunny → jupo → ride → peak。今の Drive の4本は使わない

## 角の遭遇（`角`）

- 遭遇 `04-tsuno-meet-spot` とギンの `04-gin-lick-spot` は同じ遅れ足。新人は `ENTERS from the LEFT edge`。膝は硬い。一歩が遅れる。後ろ足はリノリウムを滑る。両腕は遅れて揺れる。頭は少し傾く。短い間隔を保つ。あやは右へ歩き、遅くなって止まる。あやの他の歩様は変えない。`zombie` `corpse` `blood` `undead` `shambling` `match stride` は書かない。spot はそこで終わる。異種の spot 本文は変えない
- `04-tsuno-meet`: ミキへの背後抱きと同じ。体を背中に押しつけ、胸が潰れるまで密着し、両手で胸を揉む。その密着のまま竿が肛門へ入る。入った瞬間、あやも角も止まる。顔は驚きと快楽。声は「んおおおおぉー」。結合部を見せる横ずれは書かない。壁へ移る動きのあとに止まる。LUNGES は使わない。フルネルソンの meet も同じ抱擁から入り、文は `wraps Aya from behind`。立ちバック・後ろアナル・フルネルソンの本文は残す

## 角・騎乗（新話 `invite_ride`）

これは新しい話。既存の `off / accept_stand / invite_stand / anal_back / nelson` は残る。立ちバックの `04-tsuno-meet` は流用しない。お姫様抱っこではない。`invite_pose=embrace` には載せない。RIDE_FOLD は付けない。

順番: `04-tsuno-meet-spot` → `04-tsuno-kiss` → `04-tsuno-oral` → `04-tsuno-wait` → `04-tsuno-ride` → `04-tsuno-peak` → `04-tsuno-ride-kiss` → `04-tsuno-walk`。角が仰向け、あやが跨ぐ。ギン型にしない。

- kiss 8秒: 背後ハグ、胸を揉む、体ごと振り向いてべろちゅー。extra は kiss 0.5 + mystic 0.5
- oral 8秒: 跪き口。最終も跪き、唇は根元。extra は mystic 0.5 + penis 0.45
- wait 6秒: すでに仰向けで跨ぐ。未結合。`DIRECTLY ABOVE the glans`。connect は cut。跪きの最終を着座の首にしない
- ride 8秒: 一度下ろして `HOLD still joined at the BASE until the last frame`。sideride と thrust は積まない。connect は chain
- peak 8秒: 短い上下。中出し。sideride 0.8。mystic は積まない。penis 0.45、synth 0.4、thrust 0.55。connect は chain
- ride-kiss 6秒: 結合のまま涎キス。extra は kiss 0.5
- walk 8秒: あや一人。`No penis` `The grown shaft is gone`。connect は cut

竿を書くカットは `erect ashen-gray 24cm`。あやに竿は生やさない。

## 角・個室（新話 `wash_carry`）

これは新しい話。トイレ枠は消さない。角を「出ない」にしてもトイレは残る。id は `04-tsuno-*` だけ。`04-toilet-*` はコピーしない。ThumbInButt は積まない。和式の Look（個室、ベージュの台、フードが奥）だけ使う。通路から個室へは歩かない。通路クリップを個室の首に使わない。`04-tsuno-stall` の connect は cut。

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
- 次の hold: 両膝を上げ、マンコが亀頭の前になってから一度入れて根元。`HOLD still joined at the BASE until the last frame`。着座に thrust を積まない。新しい id は足さない。体位名は書かない
- 次の絶頂: 入ったまま、膝は上がったまま。短い上下。亀頭は中。口は付いたまま
- 歩きは 8 秒。0–3 秒は笑顔のべろちゅーと涎の糸、竿は抜ける。3–5 秒で相手が右へ消える。5–8 秒はあや一人が右へ歩く

## 向き（キス・遭遇のあと）

向かい合いの最終から後ろへ入るとき、あやは壁向きのまま手を壁へ。相手が体ごとあやの後ろへ回り、同じ向きになる。胸はあやの背中。足は床。もう同じ向きの開始には、もう一度回らない。ネルソンは別。口のあと相手が後ろへ回り、両前腕を太腿の下へ入れて持ち上げる。

## 口のカメラ

ミキの騎乗前の口は、全身のままカメラを引く。ミキの顔は竿の横に全部残る。ショートの茶髪、空洞の目、紫の顔の裂け目、髪から顎まで。スタートは全身。ギン以外の口、かなの顔射、キスは、二人の顔が画面の中に全部残る。竿役の顔も全部残る。カメラは顔が切れる距離まで寄らない。`zoom` と `Do not push the camera in` は書かない。正の文だけ。挿入に移る前に、カメラはまた全身まで引く。頭も足も全部。ギンの `04-gin-jupo` はこの顔フレームを足さない。

## 騎乗の LoRA

ギン以外の着座に sideride と thrust は積まない。着座は mystic 0.5、penis 0.45、synth 0.4。絶頂の sideride は 0.8。絶頂に mystic は重ねない。penis 0.45、synth 0.4、thrust 0.55 は絶頂に残す。ファイルは `cowgirl-side-2-mh3-e50-az420.safetensors` のまま。あやのロックは `female body`。penis と futanari の否定はあやに書かない。

## 対面座位

誘い方の `sit` は `invite_pose_sit`。みき、れい、かな、しのの4カットにある。LoRA は kiss 0.5。

- みきの `03-kiss-zai1`: あやは LEFT で跪き、唇が勃起した 24cm にある。ミキは RIGHT で立っている。口が竿を離す。ミキはその RIGHT のリノリウムに座る。胴は直立、膝は曲がり、床にあるのはミキの両足。24cm は股間から上。あやは跪きから立ち、ミキへ寄って向かい合って座る。太ももはミキの腰の外側。ふくらはぎはミキの背中の後ろでロック。あやの両足はミキの後ろで合い、床から離れる。あやの腕は肩、ミキの腕はあやの腰。胸が密着。一度腰を下ろし、24cm が根元まで入ったら `They HOLD still joined at the BASE until the last frame`。このカットは着座だけ。上下しない。extra は kiss 0.5。thrust と sideride は積まない
- れい 24cm／かな 20cm／しの 30cm の `zai1` も同じ脚（WRAP OUTSIDE / calves LOCK behind / feet meet behind, off the linoleum）。`knees plant on the linoleum` は書かない。zai1 は上下しない。zai2 が上下。kiss 0.5 は残す。thrust と sideride は積まない
- `zai2`: 入ったまま、足首はクロスのまま、べろちゅーのまま腰を上下する
- `peak`: 始まりは中出し。口は付いたまま。終わったら唇をゆっくり離す。涎が糸を引く。お互い笑顔
- `walk`: 8秒。最初に抜いて、笑顔で別れのべろちゅー。5秒以降はあや一人が右へ歩く。最後のコマはあやだけ

## ギンの口と騎乗

`04-gin-jupo` は閉じた唇が垂直の 24cm を根元まで下り、亀頭へ戻ってまた根元まで下りる。24cm は口の中。あやは 0 秒から仰向け。両掌と LIES BACK は書かない。
ギンの容姿ロックは「舌が顎の下まで垂れる」ので、`04-gin-jupo`・`04-gin-ride`・`04-gin-peak` だけ拍の `cast_lock.gin` を閉じた唇、口の中の舌、女の股間に置き換える。`hanging out past the chin` と `lips pulled back` はこの3拍から消す。舐める拍の垂れ舌は残す。cunny の Look には 24cm を書かない。竿が残る文 `Aya's shaft written in that look stays erect` は jupo から付ける。

`04-gin-ride` はあやが仰向けのまま。乗るのはギン。両足裏は肋骨の左右、胸の左右に一枚。一度下ろして根元。`HOLD still joined at the BASE until the last frame`。着座に sideride と thrust は積まない。着座 extra は mystic 0.5 + penis 0.45 + synth 0.4。fold 句は gin-ride と gin-peak に足さない。`04-gin-peak` は結合のまま短い上下。亀頭は中。あやは Gin の中で終わり、根元のまわりに少し WHITE goo。`LIFTS` は書かない。04 の歩きは出口ではない。オプションを全部入れてもギンの次は `04-tsuno-meet-spot`。角の次の拍は `04-dog-spot`。犬の LoRA はページ URL しか無く、保存された HTML を重みとして読むと Comfy がそこで落ち、角の動画のあと生成が止まる。HTML は消して、その拍は LoRA なしで続ける。ミッション完了は最後の拍だけ。誘うでは最後も完了にしない。

## 騎乗のカメラ

ギン以外。横からの距離固定。全身、両足。同じ大きさ。竿役は仰向け、後頭部と肩はリノリウム、頭は RIGHT、足先は LEFT。勃起は股間から真上。あやの頭は LEFT。両足裏は肋骨の左右、胸の左右に一枚ずつ。マンコは亀頭の真上。一度まっすぐ下ろして根元。`HOLD still joined at the BASE until the last frame`。片腿上げと、片足を腰横の床、は書かない。着座に sideride と thrust は積まない。着座の trigger に `side view riding sex` は付けない。親ビートの `kiss smack` と `wet jupo` は着座と絶頂の sfx に残さない。倒す工程は着座に書かない。`folds down` と `rises into the rider` は着座と絶頂の wrap に足さない。跪きから立つ工程も wrap が戻さない。口の最終コマだけ、相手はすでに仰向け、あやは股の上に立っている。跪きの最終は書かない。フェラ本文は残す。着座と絶頂の connect は chain。カットでも source を t2v に戻さない。絶頂だけ sideride 0.8 と thrust 0.55。短い上下は `Short vertical moves keep the glans inside`。最終も根元。`LIFTS` は書かない。着座も絶頂も、画面の二人はあやと相手だけ。`nothing new enters` は書かない。乗るのはあや。ギンの着座はあやが仰向けで、ギンが跨ぐ。再生成は FRESH。口の最終から着座、着座の根元密着だけを絶頂の首にする。今の Drive の着座と絶頂は使わない。

## キス音

「ちゅっ」は台詞にしない。唇が触れた音は sfx の `a lip-contact kiss smack when the mouths meet`。声は喘ぎだけ。

## かなの出会い

`07-kana-spot` でかなは右端から入った時点で竿をシコシコしている。WHITE goo は頭から竿、足、足元のリノリウム。通路の真ん中で止まる。あやは短い一歩で前に止まる。次の `07-kana` はその続きで、壁と手すりへ移さない。精液という語は書かない。

## 正常位と後背位の挿入

着座は一回の押し。腰と尻が密着し、竿が根元まで入ったところで止める。先だけ、半分、往復は書かない。ピストンは次の絶頂。

## 中出し

しのの誘うと戦って負けるの出口は `Shino finishes INSIDE`。他の体位の絶頂は既に中。口は口内。触手は汚液で中を満たす。

## トイレ

触手は3本。出どころは別々。便器の中から肛門へ。右の壁の穴から口へ。その穴より低い右の壁の穴からマンコへ。全部を便器から生やさない。太腿を押さえる余分な触手は書かない。

小便は、座りが正面の M 字になってから。あやは笑顔のまま、腰は止めたまま、便器も止めたまま。液体は透明なレモン色の黄色い水。見透ける水で、一本の明るい黄色の柱。マンコからその黄色い水をカメラの正面へ飛ばす。動くのは黄色い流れだけ。便器の中へ流す文は書かない。否定の「動かない」は書かない。

洋式指は小便とは別の入り。タンク側を向いて座る。尻と肛門がカメラ。マンコが肛門より上の構図は使わない。行為は chain I2V。right thumb rubs around the anus then TRAVELS INTO the anus。thumbinbutt 0.55 + mystic 0.5。synth と Fingering Pussy は積まない。`feces` は書かない。トリガー `thum1n8utt` は action に書かない。ファイルは `MiniMax H3 - ThumbInButt.safetensors`（Civitai fileId 3168734。ページ URL は重みにしない）。

和式は洋式と別 overlay。便器は奥にフードのある細長いパン。足はパンの左右の台。顔はフード。小物は病棟。和式パン専用の H3 LoRA は市場に無い。Illustrious の squat toilet LoRA は積まない。

排出はしゃがみの次。棒が肛門から穴へ繋がったまま。ThumbInButt 0.55。

ミキ枝はしゃがみのあとミキがドアから入る。押して掌と膝。一度入れて根元。HOLD。絶頂は keep the glans inside。竿はミキ 24cm。あやに竿は生やさない。挿入に ThumbInButt を積まない。挿入は Turbo オフ。挿入 extra は mystic 0.5 + penis 0.45 + synth 0.4。絶頂はそこに thrust 0.55。キス歩きは kiss 0.5。

## かなの顔射のあと

`09-kana-facial` より後のカットは、あやの基本 lock ではなく `cast.aya.looks.white_upper` を読む。上半身に粘つく WHITE goo が付いたまま。顔射のカット自体は元の lock。顔射を通らない話は元の lock のまま。精液という語は書かない。

## かなの着座（`09-join-ride`）

口の最終は、かながすでに仰向け、頭は RIGHT、足先は LEFT。あやは股の上に立ち、両足裏は肋骨の左右の床。マンコは亀頭の真上。跪きの最終は消す。フェラ本文（膝を折って根元まで）は残す。カメラは全身のまま引いた距離。着座はかながすでに仰向け、頭は RIGHT、足先は LEFT。あやは股の上に立ち、両足裏は肋骨の左右の床。マンコは亀頭の真上。一度まっすぐ下ろして根元。HOLD。かなの両手はあやの胸。片腿上げとスクワットは書かない。口カットの途中で着座へ変形しない。あやを仰向けにしない。

## ネルソン

向かい合い（口が付いたあと）から相手が後ろへ回り、両前腕を太腿の下へ入れて持ち上げる。画面はあやがカメラ向き、相手の顔はあやの頭の後ろ。足は空中。`feet leave the linoleum` は書かない。角は遭遇の立ち（後ろ、亀頭が肛門）から同じ持ち上げ。植えの性行為は大人2人、顔2つ。体を増やさない。持ち上げたあとは同じ床の位置。`Feet do not travel` `does not travel` `does not scroll` は足さない。否定の移動は移動として描かれる。

## カメラ

スタートは全身。頭の上に余白、足先の先に床。ギン以外のミキ冒頭キスは、口が付いてから膝の上から顔まで。竿は画面に残る。二人の顔は切らない。ギン以外の口、かなの顔射、キスも二人の顔を全部残す。竿役の顔も全部。カメラは顔が切れるところまで寄らない。挿入の前に全身へ戻す。顔が見切れることだけは不可。行為の前は二人とも全身。`zoom` と `Tight` と `standing close` は書かない。横スク lock の `tracks only left and right` は距離固定に置き換える。`half-step closer` は消す。ギンのカメラはこの訂正を足さない。

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

`04-dog-spot` は I2V 6秒。あやは画面 LEFT、体は RIGHT 向き。四つ足は RIGHT にすでに立ち、頭は LEFT、尾は RIGHT。右端から飛び込まない。並走しない。背中は水平、頭は低い。肩はあやの腰より高い。竿は腹の下、後肢のあいだ。extra は mystic 0.5 + furryenh 0.55。人間後背の Doggy LoRA と Eleptor は犬に積まない。spot から lick まで、頭 LEFT と尾 RIGHT を毎カット繰り返す。回す文は jupo だけ。

- 回避: あやは左へ走る。四つ足は右に残る。spot の向きは他の枝と同じ
- 受け入れる: spot の camera と action だけ同じ向き。あやは右の壁。手は壁。足は床。後脚立ち。24cm がマンコへ。後脚立ちの accept / cum / walk 本文は変えない
- 誘う伏せ: その場で仰向け、舌。wait は胸と頬が床、膝を畳む。犬は同じ向きで背中に覆う。着座は根元まで HOLD。着座に thrust は積まない
- 誘う口: 同じ舌のあと、wait は仰向け M字 のまま。うつ伏せにしない。jupo は後肢があやの頭側。腹下の竿が口へ。着座は平らな床。段差なし。着座に thrust は積まない

## 異種

スライムとケモノは XOR。両方オンにしない。歩きはギンと同じ。左端から真後ろ。あやが恐る恐る止まる。spot はそこで終わる。天井から落ちない。LUNGES は書かない。種 LoRA は調味だけ。あやの肌・汚れ・蛍光灯は I2V の前フレーム。action に anime / cel は書かない。あやの lock は触らない。

- スライム: https://civitai.com/models/2533949 ファイル `slime_girls-MMH3-v1.0.safetensors` トリガー `slime_girls` 強度 0.45
- ケモノ: https://civitai.com/models/2945034 トリガー `(anthro wolf:1.4)` 強度 0.45。amateur 0.35、penis 0.45、synth 0.4
- 四つ足: https://civitai.com/models/1782485/furry-enhancer-video 強度 0.55
- 広げる: `minimax_h3_pussy_spread_v0.2.safetensors` 強度 0.50。fileId は置かない
- クンニ: https://civarchive.com/models/1971266?modelVersionId=3318405 ファイル `cunny-mh3-e62-az420.safetensors`
- アナル指: ファイル `MiniMax H3 - ThumbInButt.safetensors` fileId 3168734。ページ URL は重みにしない

## 禁止語

`blood` `zombie` `corpse` は書かない。ウジ・蛆・虫の語も書かない。ライセンス名も書かない。体位名は書かない。犬と異種の action に `futanari` も書かない。画面の数字は 24cm / 20cm / 30cm だけ。ミキも 24cm。

## 本数

誘う・触手・灰色の騎乗・角の後ろアナル・シーンごと（みきM字、れいフルネルソン、かな騎乗、しの騎乗）は cunny を含めて 45 本。犬と異種を足した枠の上限は `MAX_BEATS` 80。

## メモリ

成功したカットの前に VRAM は下ろさない。メモリ不足でそのカットが失敗したときだけ下ろし、同じ尺をもう一度描く。それでも足りなければ短い尺に落とす。フォームに毎回解放のスイッチは置かない

## 作業の終わり

1. テストが通る
2. `colab/` と `minimaxh3/` の対応ファイルが同じ
3. このブランチへコミットして push
4. PR #147 の説明を、変わった事実だけ直す
5. 人間へ Colab リンクを返す。再生成は FRESH をオン。raw が既にあるカットは、FRESH がオフだと作り直さない。遅れ足にした `04-gin-lick-spot` と `04-tsuno-meet-spot` は、古い raw が残っていると作り直されない。角・騎乗は kiss→oral→wait→ride。角・個室は carry→stall。通路クリップを個室の首に使わない
