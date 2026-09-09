# h3-lora-studio

MiniMax H3 の LoRA を **シチュエーション × モード** で積む。Fal H3 Max には LoRA を差せない。Colab Comfy（T2V / I2V / 参照は R2V）専用。

成人のみ（21+）。速さ用と画質用を分けて積む。エロ本体は 1 系統だけ。3 本以上の画質 LoRA は穴も竿も顔も崩れる。API キーは print しない。

## Colab（初心者はここだけ）

[minimax_h3_lora_studio.ipynb](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_lora_studio.ipynb)

1. Open in Colab → GPU を **A100**
2. [Civitai の API Keys](https://civitai.com/user/account) でキーを作り、**②の「CivitaiのAPIキー」欄に貼る**（シネマ質感とえっち用。専用ノートと同じ「普通」だけなら不要）
3. **①** Drive 許可 → **②** 部品ダウンロード（初回は待つ）→ **③** シーンを日本語で選んで実行。**プロンプトは任意**（空ならおすすめ文。写真からで Picture 1 が無いときは自動で足す）。この版の③初期値は **登校（専用）** ＋ **テキストから（写真なし）**。専用フォルダに試験jpgがあっても「テキストから」なら使わない。

Drive `minimax-h3-comfyui` は専用 I2V / T2V ノートと共用。同時に 2 ノートを動かさない。ココナラ homage ノートの Turbo 既定は変えない。

重み・LoRA・pip / torch / Triton キャッシュは **全部 Drive**（`models/` と `cache/`）。生成時は Drive を mmap しない。②が **土台だけ**（FL2VA・文字・VAE）をローカル SSD に載せる。LoRA は Drive のまま。参照用 unet（ref2va、約21GB）は参照シーンのときだけ。コピーは `.part` で途中再開。空きが足りないときだけ Drive 直読みに戻す。

## エロなし（速い＋綺麗）

速さ LoRA と画質 LoRA を分ける。同時オンは **Turbo 1 + 画質 0〜1**。

| 速さ | LoRA | step | メモ |
|---|---|---|---|
| 常用・顔と質感 | larryvrh v4 step600 EMA（Comfy 変換） | 6–8 | 作者推奨。4step は動きが滲む。8超はシャープ過多。強さ 1.0 |
| 最速プレビュー | LightX2V FL2VA 4step 768p v1.0 | 4 | 768p 直出し。音は弱い |
| 音も残して速く | LightX2V FL2VA 8step v1.0 | 8 | 4step より音がマシ。歌・日本語は Larry の方が安定 |
| 顔固定 R2V | LightX2V Ref2VA 4step v0.1 | 4 | FL2VA 用と混ぜない。参照つなぐの1本目と短編集（参照）で使う |

| 画質（エロなし） | 強さ | 効果 |
|---|---|---|
| Authentic cinematic texture（テンソル修正版 2908686、トリガー `DY`） | 0.7（動き多いなら 0.5）。日常は 0.65 | 光・肌・被写界深度。元 2890588 はテンソルエラーがあるので使わない |
| Cinematic Style + Detail（トリガー `ASTROCINEMAV01K2T`） | カタログのみ | DY と同時に積まない。日常は DY を使う |
| Photoreal Image Generator（トリガー `ph0t0r34l`） | — | 静止画・キーフレーム用。動画本体には載せない |

比較の目安: 20step 基準に対し 8step で約半分、4step で約 1/3。8step 同士なら Larry と LightX2V の画質は近い。音は ベース ＞ Larry 8step ＞ LightX2V。

| ③の名前 | situation | Turbo | 画質 | sampler |
|---|---|---|---|---|
| 日常（速い＋綺麗） | `sfw_daily` | Larry 1.0 | シネマ 0.65 | res_multistep / simple / 8 |
| 最速プレビュー（エロなし） | `sfw_preview` | LightX2V 4step 1.0 | シネマ 0.4 | euler / simple / 4 |
| 音も残す（エロなし） | `sfw_audio` | LightX2V 8step 1.0 | シネマ 0.4 | euler / simple / 8 |
| 普通（エロなし） | `vanilla` | LightX2V 4step 1.0 | なし | 専用 I2V / T2V と同じ |
| （R2V・CLI） | `sfw_r2v` | Ref2VA 4step 1.0 | シネマ 0.5 | FL2VA 用 Turbo は積まない |

Larry の公式重みは [larryvrh/MiniMax-H3-Turbo-Lora](https://huggingface.co/larryvrh/MiniMax-H3-Turbo-Lora)。Colab は LoraLoader 用の [DarkRomeo88 Comfy 変換](https://huggingface.co/DarkRomeo88/MiniMax-H3-turbo-lora-comfyui) を使う。LightX2V は [lightx2v/Minimax-h3-Turbo](https://huggingface.co/lightx2v/Minimax-h3-Turbo)。まとめ: [Civitai 1063735](https://civitai.com/models/1063735)。

`video shift 6` / `audio shift 3` は sampler のメモ。グラフに ModelSamplingAV ノードは無いので未配線。SageAttention / Sol-Attn / Spectrum は LoRA ではない（Turbo と併用するとさらに短いが、このノートでは入れない）。

## エロ

同時オンは **行為 1 + ヘルパー 0〜2 + Turbo 0〜1**。**ふたなりフェラはヘルパー2（竿＋穴）+ Larry 6step。** セックス（女体）/ アナル / 騎乗 / 後背位はヘルパー2で Turbo オフ。**ふたなりシーンは必ず穴 LoRA（`synth-pussy-h3`）をセット。** 竿だけだとハメ役にも竿が付く。体位 LoRA は総合えっちの代わり（同時に積まない）。シネマを足すならヘルパーを落とす。挿入 LoRA と SFW の速い＋綺麗は併用しない。アナルセックスは ThumbInButt + 竿 + 穴で Turbo オフ（専用のアナルセックス LoRA は無い。CoachBate は有料で未使用、AIO は微妙）。穴の見え方 LoRA は積むが、空欄文は全裸のごく普通の若い成人女性（21+）だけ。行為の細かい描写は③の文章欄。男は出さない（女かふたなりのみ）。

| ③の名前 | situation | 行為 | ヘルパー | Turbo | シネマ | sampler |
|---|---|---|---|---|---|---|
| アナル挿入（画質） | `anal_penetration` | ThumbInButt 0.85 | Penis 0.7 + Synth 0.55 | **切る** | **切る** | res_multistep / beta / 16。穴のアップ。遅いが綺麗 |
| アナル舐め・指 | `anal_closeup` | Synth 0.7 | なし | Larry 0.5 | 0.4 | euler / simple / 8。動きの本線はアナル指入れ |
| アナル指入れ | `anal_fingering` | ThumbInButt 0.85 | Synth 0.55 | Larry 0.5 | **切る** | 8step。自分の親指。膣の指入れ・アナルセックスとは別。I2V本線。T2Vは実験的 |
| フェラ（女体） | `oral` | Blowjob 0.8 | Penis 0.7 + Synth 0.55 | Larry 0.5 | なし | 8step。女がふたなりに。竿＋根元のマンコ。男なし |
| 歩行・会話（専用の中で自動） | `futa_visible` | Penis 0.7 | Synth 0.55 | Larry 0.6 | **切る** | euler / simple / 8。セリフ（「」）の本だけ Turbo を外し res_multistep 12step（`sampler_no_turbo`） |
| ふたなりフェラ | `futa_blowjob` | Blowjob 0.75 | Penis 0.7 + Synth 0.55 | Larry 0.5 | なし | ふたなりが受け。男なし。6step |
| セックス（女体） | `futa_sex` | AIO 0.8 | Penis 0.7 + Synth 0.55 | **切る** | **切る** | 男にしない。12step。横クローズ。穴の強調は文章欄 |
| アナルセックス（女体） | `futa_anal` | ThumbInButt 0.85 | Penis 0.7 + Synth 0.55 | **切る** | **切る** | euler / simple / 12。アナル本線。後ろから、穴が膣より上の構図。手は腰。I2V本線 |
| 騎乗位（女体） | `riding` | cowgirl 0.8 | Penis 0.7 + Synth 0.55 | **切る** | **切る** | 12step。AIO も riding-pose I2V も積まない |
| 後背位（女体） | `doggy` | doggy 0.8 | Penis 0.7 + Synth 0.55 | **切る** | **切る** | 12step。前後の突き。T2V は実験的 |
| 正常位POV（女体） | `missionary_pov` | POV 0.85 | Penis 0.7 + Synth 0.55 | Larry 0.5 | **切る** | 8step。横はセックス（女体） |
| 後射精（女体） | `after_ejaculation` | HMCumshot 0.9 | Penis 0.7 + Synth 0.55 | Larry 0.5 | **切る** | 8step。外に出す射精。絶頂・顔射・中出しとは別 |
| 顔射（女体） | `facial` | cmst 0.8 | Penis 0.7 + Synth 0.55 | Larry 0.5 | **切る** | 8step。顔にかける。後射精・口内とは別。I2V本線。T2Vは実験的 |
| 中出し（女体） | `creampie` | Final Thrust 0.85 | Penis 0.7 + Synth 0.55 | **切る** | **切る** | 12step。膣の中。男なし。I2V本線 |
| 口内射精（女体） | `oral_creampie` | CUMOUF 0.5 | Penis 0.7 + Synth 0.55 | Larry 0.5 | **切る** | 8step。口の中。顔射ではない。I2V本線。強さ 0.5 |
| 指入れ | `fingering` | fingering 0.85 | Synth 0.55 | Larry 0.5 | **切る** | 8step。膣。オナニー LoRA は積まない。アナルはアナル指入れ |
| オナニー | `masturbation` | HMMasturbation 0.8 | Synth 0.55 | Larry 0.5 | **切る** | 12step。指入れ LoRA は積まない |
| 足コキ | `footjob` | Type D 0.85 | Penis 0.7 + Synth 0.55 | Larry 0.5 | **切る** | 8step。Type A/B/C は積まない |
| 絶頂 | `remote_orgasm` | Remoteorgasm 0.8 | Synth 0.55 | Larry 0.5 | **切る** | 8step。射精ではない |
| 汎用エロ（女体） | `general_sex` | AIO 0.8 | Penis 0.7 + Synth 0.55 | **切る** | なし | ふたなり＋女。男なし。12step。セックス（女体）と同じ |
| 試し打ち | `preview` | AIO 0.7 | Synth 0.55 | LightX2V 4step 1.0 | なし | euler / simple / 4 |
| レズビアンクンニ | `lesbian_cunnilingus` | クンニ 0.8 | Synth 0.55 | Larry 0.5 | なし | euler / simple / 8。出会い→キス→クンニ |
| 性器を広げる | `pussy_spread` | 広げる 0.75 | Synth 0.55 | Larry 0.5 | なし | euler / simple / 8 |
| レズ＋広げる | `lesbian_spread` | クンニ 0.8 | 広げる 0.6 | Larry 0.5 | なし | euler / simple / 8 |

## やらないこと

- Turbo を 2 本同時（Larry + LightX2V）
- FL2VA 用と Ref2VA 用の取り違え
- エロ挿入 LoRA との併用（アナル系は Turbo 切るのが前提）
- 体位 LoRA と総合えっち（AIO）の同時積み。体位が AIO の代わり
- 指入れ + オナニー、指入れ + アナル指入れ、アナル指入れ + アナルセックス、射精 + 絶頂、後射精 + 顔射、顔射 + 絶頂、中出し + 後射精、中出し + 顔射、中出し + 口内、口内 + 顔射、口内 + フェラ本線
- `riding-pose-i2v` を T2V に載せる（I2V専用。T2V の騎乗は cowgirl）
- シネマ DY を 0.7 以上で挿入ショット（SFW 日常は 0.6–0.7）
- Photoreal still を動画本体に載せる
- DY と ASTROCINEMA の同時積み
- Fal H3 Max に LoRA を差す
- 訓練で体位を足す（既存 FL2VA LoRA を積む）

積まない（意味がない / 別系統）: PinkCherry チェックポイント、Motion Booster、Blackedraw Doggy（Ref2VA）、Wan iGoon、`futa-h3-v51` を体位シーンに足す、HMPussy / HMPenis / HMBreasts（竿・穴と重複）、gay packs、Astro NSFW、胸スライダー、deepthroat-v02（フェラ本線で足りる）。

### ThumbInButt（アナル系の行為 LoRA）

[Civitai 2904444](https://civitai.com/models/2904444)。作者の説明: 親指をアナルに入れる動きに加えて「**物をアナルに入れる**」動作を H3 に教える。トリガー `thum1n8utt`。学習文は「the man inserts his right thumb in her anus causing the woman to moan with pleasure」の形。I2V 学習。T2V / R2V は「一応動くが見た目は良くない」。**膣がアナルより上に映る構図だと親指は膣に入る。**

studio での使い方:

- **アナル指入れ**: 女1人・自分の右親指。学習文の構造を女体に書き換え（`(S1) uses her right thumb to rub around her anus in a circular motion then inserts her right thumb in her anus`）。竿 LoRA は積まない
- **アナルセックス（女体） / アナル挿入（画質）**: 入れる物を**ふたなりの竿**にする（`(S2) inserts her penis in (S1)'s anus causing (S1) to moan with pleasure`）。竿 0.7 + 穴 0.55、Turbo オフ。挿入側の**両手は腰**に置く（LoRA が竿を親指に置き換えるのを防ぐ）。ネガに `thumb in anus, fingers in anus, hand near anus, vaginal penetration`
- 共通: **四つん這い・後ろから・穴が膣より上**。写真からが本線で、写真は後ろから穴が見えるもの。空欄文は男を一切書かない（`the man` / `his` は使わない。feminine_lock が書き換えるが、最初から書かないのが確実）
- 積まない: 膣の指入れ、CoachBate、AIO、HMMasturbation。行為は 1 本

### 中出し / 口内射精

後射精（HMCumshot）は**外に出す**。顔射（cmst）は顔。中に出す動きは別 LoRA。

- **中出し（女体）**: [Final Thrust 2891879](https://civitai.com/models/2891879)。深い突きのまま膣の中に出す。学習文は男なので studio は `(S2) performs powerful, intense thrusts with her penis inside (S1) and cums inside of her` に置換。空欄に `male character` / `the man` / `his` は書かない。竿 + 穴、Turbo オフ・12step。写真からが本線。後射精・顔射・口内とは積まない
- **口内射精（女体）**: [CUMOUF 2846978](https://civitai.com/models/2846978)。口の中で痙攣しながら出す。トリガー `CUMOUF` を先頭。強さ **0.5**（0.7で精液が不自然）。I2V は口が付いた途中の写真。作者文の he/his は her に置換。顔にかける金玉ショットではない。フェラ本線・顔射・中出しとは積まない。精液はニクカベと同じ重油級の白いドロッドロ（色は白。黒・茶色のタールにしない）、肌と顔に残る、竿先から垂れてヌルヌル。口内のあとは尺を増やさず、ジュボ側が相手と同じ目線に立ち上がって、白い粘つく液体を舌で絡める濃厚キス口移し（中出し・机の下・歩行は足さない）

```bash
python h3-lora-studio/scripts/select_loras.py --list
python h3-lora-studio/scripts/select_loras.py --situation sfw_daily --mode t2v --prompt '（シーン）'
python colab/_write_lora_studio_nb.py
```

T2V は 9:16・first_frame なし。I2V は 8:9・Picture 1 必須。Colab の秒数は 1本 4〜10。15秒はメモリ不足で画面が小さくなるので使わない。つなぐ 20〜120秒は同じカットを最後のコマで I2V 繋ぎ（③の「つなぐ 20秒」〜「つなぐ 120秒」。1本目は長回しにリライト。1本で 11秒以上は作らない）。120秒は 10×12。任意の 16〜120 は「つなぐ（秒数欄・16〜120）」。2〜12本目は③のつなぎ欄。空なら前の続き。帰宅・洗い物・登校・授業・屋上〜下校・おかえり・風呂・食卓・布団・休日・縁側の専用ストーリーは ③ で5パターン（長さの作り方・つなぎ欄・秒数は無視）。全話 10秒・1本1場所1動作。

| ③のラベル | 再生 | last-frame | 文の修正 |
|---|---|---|---|
| `登校（専用）` など | カット。JSON のまま（`CHAIN=False`、`last_frame=None`） | なし | なし（③「最終シーン合わせ」オン＋写真からの静止画だけ `rewrite_dedicated_scene_i2v_prompt`） |
| `登校（つなぐ）` | 文を直さずつなぐ | 2本目以降 I2V | Picture 1 ロック（`continue_chain_prompt`）だけ。`rewrite_chain_opening_prompt` も最後の `rewrite_final_scene_i2v_prompt` もオフ |
| `登校（つなぐ修）` | 文を直してつなぐ | 2本目以降 I2V | 1本目に `rewrite_chain_opening_prompt`。③オンなら最後の本だけ `rewrite_final_scene_i2v_prompt` |
| `登校（参照つなぐ）` | つなぐ＋1本目は `input/cast/` を **R2V 参照** | 2本目以降 I2V | 文はそのまま。③テキストからは無視。FL2VA の竿は1本目に載せない。穴（synth-pussy）は載せる |
| `登校（参照つなぐ修）` | 参照つなぐ＋1本目を長回し | 2本目以降 I2V | 1本目 `rewrite_chain_opening_prompt`。③オンなら最後の本だけ |
| `短編集（参照）` | 10秒完結×複数。つなぎなし。メイン4人のうち竿＋ハメの2人。画面は本ごと | なし | 文は自動。各本が独立 **R2V**（フェラは blowjob＋Ref2VA turbo・9:16寄り、挿入は AfterMidnight・16:9または立ち9:16） |

旧名「登校120秒（専用）」は `SITUATION_JA` のエイリアス（dedicated）。初期値は **登校（専用）**。実装は `resolve_story_play()` / `apply_story_play()`。キャスト8枚: `sayaka-bust` `sayaka-full` `rei-bust` `rei-full` `aya-bust` `aya-full` `madoka-bust` `madoka-full`。

名前付きパック（`CHAIN_PACK_IDS`）は専用ではない（`is_story` False、`is_chain_pack` True）が、③では**同じ5パターン**で再生する。`訪問販売（専用）` / `訪問販売（つなぐ）` / `訪問販売（つなぐ修）` のように短名＋接尾辞。旧名「訪問販売60秒（つなぐ）」「定期検診100秒（つなぐ）」「終点40秒（つなぐ）」と裸の id は前と同じ動き（＝つなぐ修）。JSON は全部 9:16 576×1024・`kind:"chain"`・`seamless:true`・セリフは10秒（**物語の追加**も全部10秒。画面サイズは維持）・無言の行為も10秒・LoRA は JSON の本ごと。画像サイズは JSON の `canvas` で決まる（文に大きさは書かなくてよい）。物語の追加は JSON 10秒×2＝20秒、台詞は1本目だけ、行為は無言、hmmotion は挿入本だけ。終電は 9本＝90秒・全部10秒（15秒禁止）。

| パック | id | 本数 | 建前 / 型 | 台詞 |
|---|---|---|---|---|
| 訪問販売 | `sales-visit-60s` | 対面20秒。ジュボ10秒。8本＝80秒 | 玄関の対面。おミズ＝放尿を飲んでからジュボ→口内 | カナ、1本1行 |
| 定期検診 | `checkup-100s` | 対面30秒。キス10＋ジュボ10。9本＝90秒 | 家の玄関。キスと胸→カクニン→口内。「モンダイありますね」 | カナ、1本1行 |
| ケンシン | `clinic-75s` | 6本＝60秒。台詞10秒、キス10・ジュボ10・口内10無言 | 医院にアヤが来る。医師が20cm。1本目は左手シコシコ無表情、右入場、「おっきい」のあとお互い立って短いキス、右の椅子におすわり（女医は立つ）。ウンチ相談→立ちのおクチキス（身を胸につける。胸は揉まない）→ジュボ尻餅→口内口移し→ゲンキ | カナ、1本2行まで |
| 終点 | `last-stop-40s` | 10×4 | 終点の車内。起こして跪いて咥える（竿舐め禁止）。ジュボで起こす | カナ、1本1行 |
| 終電 | `last-train-120s` | 9本＝90秒（全部10秒。15秒禁止）。ジュボ20秒、騎乗10×2、抜き10 | 終点の延長。2人だけ。声かけはレイに向ける。向き合う座位で挿入を書く。中出しのあと抜くと隙間から白液、マンコからドロドロ | カナ、1本2行まで |
| ザーメン風呂 | `semen-bath-70s` | 5本＝50秒 | 家のおフロ。アヤが湯船、レイが20cmで白い粘液を溜める。口移しなし | カナ、1本2行まで |
| ニクカベ | `meat-wall-85s` | 7本＝70秒。歩行10、台詞10、ジュボ10・口内10無言 | 巨大生物の体内。コンクリートに肉を貼った部屋ではない。歩行の床は弾力（足は沈まない）。茶色い粘液は全身。白いおフロはベトベト。レイは1本目からフタナリ勃起。顔は液面より上。全部飲む。口移しなし。家のザーメン風呂とは別 | カナ、1本2行まで |
| カフェ | `cafe-100s` | 10×10 | おミズ＝放尿、ミルク＝ジュボと口内。コーヒーは本物 | カナ、1本2行まで |
| 車内販売 | `train-sales-80s` | 10×8 | おチャ＝放尿、ミルクコーヒー＝ジュボと口内。レイの竿は使わない | カナ、2行まで |
| 赤信号 | `red-light-50s` | 10×5 | 信号待ち。運転レイ両手ハンドル、口アヤ。ジュボ→口内 | カナ、2行まで |
| ヨガ | `yoga-50s` | 10×5 | コツバン。四つん這いでもう入っている（doggy） | カナ、2行まで |
| 背中流し | `back-wash-60s` | 10×6 | 洗う→マドカのマンコ舐め（cunnilingus_futa）→アガリユ＝放尿 | カナ、2行まで |
| カラオケ | `karaoke-50s` | 10×5 | 歌のあいだジュボ、最後の音で口内、点数 | カナ、2行まで |
| ランドリー | `laundromat-50s` | 10×5 | あと何分。洗濯機の上でもう入っている（futa_sex） | カナ、2行まで |
| 講義机 | `lecture-desk-50s` | 10×5 | 板書。教卓の下でジュボ→口内 | カナ、2行まで |
| キャンプ | `camp-50s` | 10×5 | 虫よけ。レイがアヤを舐めるだけ（cunnilingus_futa）。竿は使わない | カナ、2行まで |
| 花火 | `fireworks-50s` | 10×5 | 上を見る。立ったまま後ろから（futa_sex）。顔は花火 | カナ、2行まで |
| ハイスイコウ | `manhole-30s` | 10×2 | 物語の追加。フタの会話→口を開けて先端から手の幅→無言ジュボ口内。ジュボ側が同じ目線に立ち上がって濃厚キス口移し | カナ、1本目2行 |
| 屋上クーラー | `roof-ac-30s` | 10×2 | 物語の追加。会話→受け入れる立ち・挿入寸前→無言でもう入っている立ち（hmmotion） | カナ、1本目2行 |
| ハマのテトラ | `tetrapod-30s` | 10×2 | 物語の追加。風の会話→跪いて口を開けて先端から手の幅→無言ジュボ口内。ジュボ側が同じ目線に立ち上がって濃厚キス口移し | カナ、1本目2行 |
| 廃校ロッカー | `locker-30s` | 10×2 | 物語の追加。カギの会話＋キス→跪いて口を開けて先端から手の幅→無言ジュボ口内。ジュボ側が同じ目線に立ち上がって濃厚キス口移し | カナ、1本目2行 |
| ドウロのど真ん中 | `crossing-30s` | 10×2 | 物語の追加。信号の会話→跪いて口を開けて先端から手の幅→無言ジュボ口内。ジュボ側が同じ目線に立ち上がって濃厚キス口移し | カナ、1本目2行 |
| ガケの展望台 | `lookout-30s` | 10×2 | 物語の追加。霧の会話→仰向け・膝を開いて舐め寸前→無言クンニ（竿は使わない） | カナ、1本目2行 |
| コウジョウあと | `factory-30s` | 10×2 | 物語の追加。サビの会話→受け入れる立ち・挿入寸前→無言でもう入っている立ち（hmmotion） | カナ、1本目2行 |
| ガソリンスタンド跡 | `gas-station-30s` | 10×2 | 物語の追加。ミズ＝放尿を飲んで口を開けて先端から手の幅→無言ジュボ口内。ジュボ側が同じ目線に立ち上がって濃厚キス口移し | カナ、1本目2行 |
| トンネル非常電話 | `tunnel-phone-30s` | 10×2 | 物語の追加。電話の会話→受話器持ったまま跪いて口を開けて先端から手の幅→口だけ。ジュボ側が同じ目線に立ち上がって濃厚キス口移し | カナ、1本目2行 |
| 川原のゴミ | `riverbank-30s` | 10×2 | 物語の追加。フクロの会話→跪いて口を開けて先端から手の幅→無言ジュボ口内。ジュボ側が同じ目線に立ち上がって濃厚キス口移し | カナ、1本目2行 |

建前パック（カフェ〜花火）のユーザー原稿は 15秒×N。H3 追従（10秒・1本1動作・行為中は無言）に合わせて 10秒×N に割り直し、行為中の台詞は前後の口元の本へ移した。セックス／口／クンニの直前の本は挿入寸前・受け入れる姿勢（先端から手の幅、未挿入／口を開けて先端から手の幅／膝を開いて舐め寸前）で終わる。物語の追加は1本目の余り尺でその姿勢にする（3本目は足さない）。`spoken_max: 2` で口元の本に1往復（2行）まで（上限2。無いパックは1）。`hmmotion` は AIO の本だけ先頭（ランドリー・花火・屋上クーラー・コウジョウあと）。アナル舐め・アナル指入れの建前パックは作らない（アナル舐め LoRA が無い）。全シーンのふたなりは **玉なし＋マンコあり**（竿の付け根に無毛の女陰。`lock_futa_anatomy` / `Penis plus vagina, never balls`。ボッキ時は約20cm・太い人間の竿で形固定 `lock_futa_shaft`。アヤとサヤカは竿なしのまま）。口にする台詞は話し言葉（漢字禁止。おチンチン・おミズ・ムク等の符丁はカタカナ。`validate_story_follow` が「」内の漢字を落とす）。シーンごとに WHO で誰が出て何をするかを書く。余り役は NOT IN FRAME。常時2人以上ではない。訪問（献身・水販売）は最初一人（閉扉・チャイム）→ドアが開いてからメインが入る。カフェ1本目は店員なし。台詞は棒読み禁止（感情＋表情。あちぃーは真夏の暑そうな顔）。放尿は精液と同じく亀頭先の穴から黄色い水。ジュボ中は気持ちよさ、射精はイキ顔。セリフは口元が見える本だけ（リップシンク）。行為は LoRA のカメラ（口元／舌／接合点／膝元）。歩く本に行為部品を載せない。体位とカメラが合わない行為は捩じ込まない。登校・おかえり・風呂・食卓・布団・休日・縁側は 10秒×12本・16:9。授業と屋上は 10秒×10本・16:9。

### 専用ストーリーの追従最適化（速度と再現の両立）

専用の各本は独立生成（前の本も他の話もモデルは見ない）。③は JSON の文をそのまま送らず `compact_story_prompt()` で整えてから送る。

- **画面に居ない人の全身描写を消す**。`X = NOT IN FRAME` / `NOT IN THIS CLIP` の人は `subject_definitions` から外し、`Not in this clip: X.` の1行にする。居ない裸の女を細かく書くのが「勝手に出てくる」最大の原因
- **編集者向けのメタ行を消す**。`Do not copy the previous clip` / `Clip 7 of 12` / CAST LOCK の他話タイトル列挙はモデルに意味が無い。CAST LOCK は「同じ顔・髪・体」の1文に置き換える
- **H3 の正規順に並べ直す**。`subject_definitions → environment → integrated_multimodal_description → overall_soundscape → non_diegetic_music`。WHO の配置と HARD LOCK / CAMERA / LIP SYNC は description ブロックの中に畳む。feminine_lock も soundscape の前に入る
- **セリフの本だけフルステップ**。`「」` がある本は Larry とシネマを外して竿だけ・res_multistep 12step（口の動きと日本語の音。シネマ＋口パクで顎が溶ける）。歩く・キス・テレビの本は Larry 0.6 / 8step
- **音声チャンネルは効果音と「」だけ**。`lock_spoken_japanese` が `overall_soundscape` から `lip-synced` / `No other speech` / `No spoken words` / 台詞だけ を消す。同じ「」は絵（LIP SYNC）と音で各1つ。`[AUDIO-LOCK] other_text: not_spoken` と日本語の音声ルールは撤回（H3が音読した）。③の再生グラフも同じ。`validate_story_follow` は「」内のラテン文字も落とす
- **VRAM の /free は OOM と土台切替だけ**。②の全部入れはディスクへ保存するだけ。再生グラフは今の本の LoRA だけ繋ぐ。口パクでシネマを外しても H3 本体は載せたまま。FL2VA↔Ref2VA のときとメモリ不足の再試行だけ `/free`
- **②の2回目は設定だけ**（既定オン）。文章・JSON を GitHub tar で一括取得。土台・LoRA の再取得と Drive の全部一覧は飛ばす。土台が無いときだけ全部入れる。欠けた部品は③で足す
- **トリガーは単語一致**。`DY` が `body` の中に見つかって落ちていた。今は `PENISLORA, DY` が歩く本の先頭に付く
- **`negative` は文書用**。公式グラフは BasicGuider（CFG なし）で負の文を送る配線が無い。除外したいものは正の文に `No men. No feces.` のように書く（専用文はそうしている）。CFG を足すと NFE が倍になるので入れない
- `validate_story_follow()` は **全話10秒（15秒禁止）**／行為中は無言／口元の寄り／接合点（セックス本）に加えて **hmmotion は AIO セックス本だけ・先頭**、ユニーク「」は1本に `spoken_max`（既定1、上限2）まで、**「」内に漢字なし**、Clear futanari は玉なし＋マンコあり、物語の追加は行為の前の本が挿入寸前／口を開けて先端から手の幅／膝を開いて舐め寸前 を検査する。生成時のセックス本は `lock_penis_inside`（勃起20cmがマンコまたはアナルの中）。精液は全話 `lock_semen_look`（ニクカベと同じ重油級の白いドロッドロ。色は白）。ジュボと口内は `lock_oral_in_mouth`（奥まで根元。先端咥え禁止）

## 禁止語

設定は **1ファイルだけ**。`catalog/forbidden.json`。Colab では Drive の `minimax-h3-comfyui/forbidden.json`（②が無ければ作る。あれば上書きしない）。③に欄は無い。編集したら③を再実行。

- `extra` … 足す・消してよい（初期は schoolgirl / 稼げる / 月収 など）
- `minors` / `commercial` / `min_age` … 書いてあるのは一覧。消してもコード側のロックは残る（未成年・21歳未満の数字・`px.a8.net`）

```bash
python h3-lora-studio/scripts/select_loras.py --situation sfw_daily --mode t2v --prompt '（シーン）'
```

## 不変条件

1. 速さ用と画質用を分け、Larry と LightX2V を同時に積まない
2. アナル挿入・アナルセックス（ThumbInButt + 竿 + 穴）は Turbo オフ
3. FL2VA に ref2va を載せない
4. T2V に Picture 1 を書かない
5. 未成年・ロリ・ショタ禁止
6. キーは print しない。Git に入れない
7. ココナラ homage の turbo 既定を変えない
8. Fal に LoRA を載せない
9. 体位 LoRA は AIO の代わり。同時に積まない。訓練で体位を足さない
10. エロは女かふたなりのみ。男は出さない。空欄は全裸のごく普通の若い成人女性（21+）
