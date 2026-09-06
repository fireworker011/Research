# h3-lora-studio

MiniMax H3 の LoRA を **シチュエーション × モード** で積む。Fal H3 Max には LoRA を差せない。Colab Comfy（T2V / I2V）専用。

成人のみ（21+）。速さ用と画質用を分けて積む。エロ本体は 1 系統だけ。3 本以上の画質 LoRA は穴も竿も顔も崩れる。API キーは print しない。

## Colab（初心者はここだけ）

[minimax_h3_lora_studio.ipynb](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_lora_studio.ipynb)

1. Open in Colab → GPU を **A100**
2. [Civitai の API Keys](https://civitai.com/user/account) でキーを作り、**②の「CivitaiのAPIキー」欄に貼る**（シネマ質感とえっち用。専用ノートと同じ「普通」だけなら不要）
3. **①** Drive 許可 → **②** 部品ダウンロード（初回は待つ）→ **③** シーンを日本語で選んで実行。**プロンプトは任意**（空ならおすすめ文。写真からで Picture 1 が無いときは自動で足す）

Drive `minimax-h3-comfyui` は専用 I2V / T2V ノートと共用。同時に 2 ノートを動かさない。ココナラ homage ノートの Turbo 既定は変えない。

## エロなし（速い＋綺麗）

速さ LoRA と画質 LoRA を分ける。同時オンは **Turbo 1 + 画質 0〜1**。

| 速さ | LoRA | step | メモ |
|---|---|---|---|
| 常用・顔と質感 | larryvrh v4 step600 EMA（Comfy 変換） | 6–8 | 作者推奨。4step は動きが滲む。8超はシャープ過多。強さ 1.0 |
| 最速プレビュー | LightX2V FL2VA 4step 768p v1.0 | 4 | 768p 直出し。音は弱い |
| 音も残して速く | LightX2V FL2VA 8step v1.0 | 8 | 4step より音がマシ。歌・日本語は Larry の方が安定 |
| 顔固定 R2V | LightX2V Ref2VA 4step v0.1 | 4 | FL2VA 用と混ぜない。この Colab では選ばない |

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

同時オンは **行為 1 + ヘルパー 0〜2 + Turbo 0〜1**。**ふたなりフェラはヘルパー2（竿＋穴）+ Larry 6step。** セックス（女体）/ アナル / 騎乗 / 後背位はヘルパー2で Turbo オフ。体位 LoRA は総合えっちの代わり（同時に積まない）。シネマを足すならヘルパーを落とす。挿入 LoRA と SFW の速い＋綺麗は併用しない。アナルセックスは ThumbInButt + 竿 + 穴で Turbo オフ（専用のアナルセックス LoRA は無い。CoachBate は有料で未使用、AIO は微妙）。穴の見え方 LoRA は積むが、空欄文は全裸のごく普通の若い成人女性（21+）だけ。行為の細かい描写は③の文章欄。男は出さない（女かふたなりのみ）。

| ③の名前 | situation | 行為 | ヘルパー | Turbo | シネマ | sampler |
|---|---|---|---|---|---|---|
| アナル挿入（画質） | `anal_penetration` | ThumbInButt 0.85 | Penis 0.7 + Synth 0.55 | **切る** | **切る** | res_multistep / beta / 16。穴のアップ。遅いが綺麗 |
| アナル舐め・指 | `anal_closeup` | Synth 0.7 | なし | Larry 0.5 | 0.4 | euler / simple / 8。動きの本線はアナル指入れ |
| アナル指入れ | `anal_fingering` | ThumbInButt 0.85 | Synth 0.55 | Larry 0.5 | **切る** | 8step。自分の親指。膣の指入れ・アナルセックスとは別。I2V本線。T2Vは実験的 |
| フェラ（女体） | `oral` | Blowjob 0.75 | Penis 0.7 | Larry 0.7 | なし | 女がふたなりに。男なし |
| ふたなりフェラ | `futa_blowjob` | Blowjob 0.75 | Penis 0.7 + Synth 0.55 | Larry 0.5 | なし | ふたなりが受け。男なし。6step |
| セックス（女体） | `futa_sex` | AIO 0.8 | Penis 0.7 + Synth 0.55 | **切る** | **切る** | 男にしない。12step。横クローズ。穴の強調は文章欄 |
| アナルセックス（女体） | `futa_anal` | ThumbInButt 0.85 | Penis 0.7 + Synth 0.55 | **切る** | **切る** | euler / simple / 12。アナル本線。後ろから、穴が膣より上の構図。手は腰。I2V本線 |
| 騎乗位（女体） | `riding` | cowgirl 0.8 | Penis 0.7 + Synth 0.55 | **切る** | **切る** | 12step。AIO も riding-pose I2V も積まない |
| 後背位（女体） | `doggy` | doggy 0.8 | Penis 0.7 + Synth 0.55 | **切る** | **切る** | 12step。前後の突き。T2V は実験的 |
| 正常位POV（女体） | `missionary_pov` | POV 0.85 | Penis 0.7 | Larry 0.5 | **切る** | 8step。Synth オフ。横はセックス（女体） |
| 後射精（女体） | `after_ejaculation` | HMCumshot 0.9 | Penis 0.7 | Larry 0.5 | **切る** | 8step。外に出す射精。絶頂・顔射・中出しとは別 |
| 顔射（女体） | `facial` | cmst 0.8 | Penis 0.7 | Larry 0.5 | **切る** | 8step。顔にかける。後射精・口内とは別。I2V本線。T2Vは実験的 |
| 中出し（女体） | `creampie` | Final Thrust 0.85 | Penis 0.7 + Synth 0.55 | **切る** | **切る** | 12step。膣の中。男なし。I2V本線 |
| 口内射精（女体） | `oral_creampie` | CUMOUF 0.5 | Penis 0.7 | Larry 0.5 | **切る** | 8step。口の中。顔射ではない。I2V本線。強さ 0.5 |
| 指入れ | `fingering` | fingering 0.85 | Synth 0.55 | Larry 0.5 | **切る** | 8step。膣。オナニー LoRA は積まない。アナルはアナル指入れ |
| オナニー | `masturbation` | HMMasturbation 0.8 | Synth 0.55 | Larry 0.5 | **切る** | 12step。指入れ LoRA は積まない |
| 足コキ | `footjob` | Type D 0.85 | Penis 0.7 | Larry 0.5 | **切る** | 8step。Type A/B/C は積まない |
| 絶頂 | `remote_orgasm` | Remoteorgasm 0.8 | Synth 0.55 | Larry 0.5 | **切る** | 8step。射精ではない |
| 汎用エロ（女体） | `general_sex` | AIO 0.8 | なし | Larry 0.5 | なし | ふたなり＋女。男なし。12step |
| 試し打ち | `preview` | AIO 0.7 | なし | LightX2V 4step 1.0 | なし | euler / simple / 4 |
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
- **口内射精（女体）**: [CUMOUF 2846978](https://civitai.com/models/2846978)。口の中で痙攣しながら出す。トリガー `CUMOUF` を先頭。強さ **0.5**（0.7で精液が不自然）。I2V は口が付いた途中の写真。作者文の he/his は her に置換。顔にかける金玉ショットではない。フェラ本線・顔射・中出しとは積まない

```bash
python h3-lora-studio/scripts/select_loras.py --list
python h3-lora-studio/scripts/select_loras.py --situation sfw_daily --mode t2v --prompt '（シーン）'
python colab/_write_lora_studio_nb.py
```

T2V は 9:16・first_frame なし。I2V は 8:9・Picture 1 必須。Colab の秒数は 1本 4〜15。20〜120秒は③の「つなぐ 20秒」〜「つなぐ 120秒」（10秒クリップ。1本で 16秒以上は作らない）。120秒は 10×12。任意の 16〜120 は「つなぐ（秒数欄・16〜120）」。2〜12本目は③のつなぎ欄。空なら前の続き。帰宅90秒・洗い物90秒専用はカット編集。

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
