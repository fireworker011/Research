---
name: h3-lora-studio
description: MiniMax H3 LoRA studio for Colab. SFW fast+quality is turbo plus one cinematic LoRA (Larry daily, LightX2V preview). Adult stacks stay act + helper-or-cinema + optional thin turbo. Futa blowjob may use two helpers plus thin Larry 6step. Anal sex is ThumbInButt + penis + synth, turbo off. Use when the user names h3-lora-studio, Colab LoRA, Larry, LightX2V, cinematic DY, or select_loras.py.
---

# h3-lora-studio

質問しない。Colab 実装なら `minimax_h3_lora_studio.ipynb`。設定だけなら `select_loras.py`。ノートは `python colab/_write_lora_studio_nb.py` で再生成。`colab/h3_lora_studio.py` と `minimaxh3/h3_lora_studio.py` は同期する。ココナラ homage ノートの Turbo 既定は変えない。③の初期値は **登校（専用）**＋テキストから（訪問販売/検診/終点を初期値にしない）。`prepare_story_clip(..., force_t2v=True)` は Drive の試験 jpg を無視する。普通のつなぐ 20〜120秒は 1シーン＋長さで last-frame I2V（`rewrite_chain_opening_prompt` / `continue_chain_prompt`）。

専用ストーリー（`STORY_IDS`、帰宅〜縁側の11話）は ③ で5パターン（`resolve_story_play` / `apply_story_play`）:
- `〜（専用）` = カット。JSON のまま。`CHAIN=False`・`last_frame=None`。旧名「登校120秒（専用）」は `SITUATION_JA` のエイリアスで dedicated
- `〜（つなぐ）` = 文を直さずつなぐ。last-frame I2V。`rewrite_chain_opening_prompt` も最後の `rewrite_final_scene_i2v_prompt` もオフ。Picture 1 ロック（`continue_chain_prompt`）だけ必須
- `〜（つなぐ修）` = 文を直してつなぐ。last-frame I2V ＋ 1本目に `rewrite_chain_opening_prompt`。③「最終シーン合わせ」オンなら最後の本だけ `rewrite_final_scene_i2v_prompt`
- `〜（参照つなぐ）` = つなぐと同じだが **1本目は R2V**（Drive `input/cast/` の bust+full を identity 参照。I2V の最初のコマではない。FL2VA の竿/穴は載せない。口は blowjob＋Ref2VA turbo、歩行は cinema＋Ref2VA turbo、行為は AfterMidnight）。2本目以降は last-frame I2V（FL2VA の竿+穴スタック）
- `〜（参照つなぐ修）` = 参照つなぐ ＋ 1本目を長回しに直す。③オンなら最後の本だけ合わせる
- `短編集（参照）` = 15秒完結の濃厚日常インモラル×複数。つなぎなし・連結なし。各本 **R2V**。文は `generate_immoral_shorts()`。部品は clip の situation の `stack_plan.r2v`

名前付きパック（`CHAIN_PACK_IDS` = sales-visit-60s / checkup-100s / last-stop-40s ＋ 建前パック cafe-100s / train-sales-80s / red-light-50s / yoga-50s / back-wash-60s / karaoke-50s / laundromat-50s / lecture-desk-50s / camp-50s / fireworks-50s）は専用ではない（`is_story` False、`is_chain_pack` True）が、③では**同じ5パターン**で再生する（`訪問販売（専用｜つなぐ｜つなぐ修｜参照つなぐ｜参照つなぐ修）` … `花火（…）`）。JSON は `kind:"chain"`・`seamless:true`・9:16 576×1024・セリフは10秒・無言の行為は15秒まで・LoRA は JSON の本ごと。旧名「訪問販売60秒（つなぐ）」と裸の id は **つなぐ修**。画像サイズは JSON の `canvas` だけ（`story_canvas_wh`）。全シーンのふたなりは **玉なし＋マンコあり**（`lock_futa_anatomy`）。口にする台詞はカタカナ。建前パックは `spoken_max: 2`。行為→LoRA: ジュボ=oral（フェラ+竿+穴）、口内=oral_creampie（CUMOUF+竿+穴）、放尿を飲む=oral、クンニ=cunnilingus_futa、もう入っている=futa_sex または doggy。

**積まない（正しい未使用）:** `futa-h3-v51`（変身）、`riding-pose-i2v`（I2V専用・未使用）、`anal-penetration-coachbate`（有料）、`photoreal-h3-still`（静止画）、Ref2VA を FL2VA に、Larry+LightX2V、AIO+体位、③上級 extras。歩行 `futa_visible` はシネマがあるので穴ヘルパーは載せない。

```bash
python h3-lora-studio/scripts/select_loras.py --list
python h3-lora-studio/scripts/select_loras.py --situation sfw_daily --mode t2v --prompt '（シーン）'
python colab/_write_lora_studio_nb.py
```

Fal に LoRA は差せない。成人 21+。

エロなし: Turbo1 + 画質1。日常は Larry v4 1.0 + シネマ DY 0.65 / 8step。最速は LightX2V 4step。音残しは LightX2V 8step。専用「普通」は LightX2V 4step のみ。Larry と LightX2V は同時に積まない。FL2VA と Ref2VA を混ぜない。Photoreal still は動画本体に載せない。DY と ASTROCINEMA は同時に積まない。

エロ: 行為1 + ヘルパー0〜2 + Turbo0〜1。空欄は全裸のごく普通の若い成人女性（21+）。女かふたなりのみ。男厳禁。描写は③の文章欄。ふたなりフェラはヘルパー2（竿＋穴）+ Larry 0.5 / 6step。セックス（女体）/ アナル / 騎乗 / 後背位はヘルパー2で Turbo オフ。専用のアナルセックス LoRA は無い（CoachBate は有料・未使用、AIO は微妙）。アナルセックス（女体）は ThumbInButt 0.85 + 竿 0.7 + 穴 0.55 / Turbo オフ・12step。アナル挿入（画質）は同じ積みで res_multistep 16step。ThumbInButt は「物をアナルに入れる」LoRA なので入れる物をふたなりの竿にする。構図は四つん這い・後ろから・穴が膣より上（膣が上だと膣に入る）。挿入側の両手は腰（親指に置き換わるのを防ぐ）。ネガに thumb in anus / hand near anus / vaginal penetration。空欄文に the man / his は書かない。写真からが本線。体位 LoRA は AIO の代わり（同時に積まない）。騎乗は cowgirl + 竿 + 穴 / 12step。後背位は doggy + 竿 + 穴 / 12step。正常位POVは POV + 竿 + Larry 0.5 / 8step（横はセックス（女体））。後射精は HMCumshot + 竿 + Larry 0.5 / 8step（外出し。中出し・顔射とは別）。顔射は cmst + 竿 + Larry 0.5 / 8step（後射精・絶頂・口内とは別。I2V本線）。中出しは Final Thrust 0.85 + 竿 0.7 + 穴 0.55 / Turbo オフ・12step（膣の中。学習文の male character は書かない。I2V本線）。口内射精は CUMOUF 0.5 + 竿 0.7 + 穴 0.55 + Larry 0.5 / 8step（口の中。顔射ではない。I2Vは口が付いた途中の写真）。指入れは膣。アナル指入れは ThumbInButt + 穴 + Larry 0.5 / 8step（I2V本線。指入れ・CoachBate・AIO・竿とは積まない）。指入れとオナニーは別シーン（同時に積まない）。足コキは Type D + 竿 + Larry。絶頂は Remoteorgasm（射精ではない）。汎用エロ（女体）は AIO + Larry 0.5 / 12step。変身 LoRA は足さない。riding-pose-i2v は I2V専用で未使用。秒数は 1本 4〜15。つなぐ 20〜120秒は同じカットを最後のコマで I2V（③の「つなぐ 20秒」〜「つなぐ 120秒」。1本目は長回しにリライト。秒数欄は無視）。120秒は 10×12。任意の 16〜120 は「つなぐ（秒数欄・16〜120）」。2〜12本目は③のつなぎ欄（空なら前の続き）。帰宅・洗い物・登校・授業・屋上・おかえり・風呂・食卓・布団・休日・縁側の（専用）はカット編集（長さの作り方・つなぎ欄・秒数は無視）。（つなぐ）/（つなぐ修）は同じ JSON を last-frame I2V でつなぐ（長さの作り方・つなぎ欄・秒数は無視）。全話10秒・1本1場所1動作。セリフは口元が見える本だけ（リップシンク）。行為はLoRAのカメラ（口元／舌／接合点／膝元）。歩く本に行為部品を載せない。体位とカメラが合わない行為は捩じ込まない（仰向けの口にアナルやセックスを足さない）。登校・おかえり・風呂・食卓・布団・休日・縁側は10秒×12本・16:9。授業と屋上は10秒×10本・16:9。挿入 LoRA と SFW の速い＋綺麗は併用しない。訓練で体位を足さない。 専用の文は③で `compact_story_prompt()` を通す：画面に居ない人の全身描写を消して `Not in this clip: X.` にする、`Do not copy the previous clip`・`Clip N of M`・CAST LOCK の他話タイトルを消す、H3 正規順（subject_definitions → environment → integrated_multimodal_description → overall_soundscape → non_diegetic_music）に並べ直す。歩行（futa_visible）は竿 0.7 + シネマ 0.5 + Larry 0.6 / 8step。`「」` のある口パク本は Larry とシネマを外して竿だけ・res_multistep 12step（シネマ＋口パクで顎が溶ける。`drop_speech_face_killers`）。音声は `lock_spoken_japanese` が soundscape 先頭に [AUDIO-LOCK] spoken_transcript を足す（「」だけ。止めの日本語は書かない。H3がそれを台詞として読む）。③の再生グラフも同じロックを通す。フェラ（女体）は Blowjob 0.8 + 竿 0.7 + 穴 0.55 + Larry 0.5 / 8step。ふたなりフェラは同じヘルパー2 + Larry 6step。口内は CUMOUF + 竿 + 穴 + Larry 8step。②の全部入れはディスク保存。再生グラフはその本の LoRA だけ。部品の id+強さが変わったら `/free` で前の LoRA を VRAM から下ろす（毎本ではない。メモリ不足の再試行でも解放）。トリガーは単語一致（`DY` が `body` に埋もれない）。`negative` は文書用（BasicGuider、CFG なし。除外は正の文に書く）。hmmotion は AIO セックス本だけ・先頭（validate_story_follow が検査）。重みと pip/torch キャッシュは Drive。生成はローカル SSD に載せてから（`stage_models_to_local` + `warmup_h3_engine`）。Drive FUSE を mmap しない。
