# 学習キット — 準備すること / やること

キットは **重みを作らない**。やることは素材の検品と fal 用 zip まで。
学習は fal。③への接続は `.safetensors` が Drive に入ってから **別セッション**。
今の③は竿＋穴＋文章で出す。このキットは効きを固める用。

## 担当

| 誰 | やること |
|---|---|
| ナオミチ | 権利のある素材、撮影／収集、フォルダ分け、fal の課金、できた重みを Drive に置く |
| キット（このフォルダ） | グリッド、キャプション、zip、構図の偏り検品 |
| fal | `debug_dataset` のあと本学習 |
| 別セッション | カタログ接続。重みが無いあいだは③に足さない |

## 作る3本（1フォルダ1本。混ぜない）

| id | トリガー | 覚えること | 体位 | グリッド |
|---|---|---|---|---|
| `anal-any-h3` | `AN4LIN` | アナル（どの構図でも） | standing / doggy / missionary / cowgirl / side / pov | 96セル |
| `urine-drink-h3` | `URNKISS` | 飲尿（どの構図でも） | standing / kneeling / sitting / cowgirl / side / pov | 96セル |
| `scat-act-h3` | `DFCTH3` | 脱糞（出す行為・どの構図でも） | standing / squat / doggy / missionary / sitting / side | 96セル |

1セル1本で埋めると **96本／概念**。これが本線（目標 80〜160）。fal の下限は 10本だが、それだと構図が固定される。
1体位は全体の **25%超禁止**（96本なら1体位24本まで。均等なら16本）。

## 作らない

- `sex-any-h3` … hmnsfw-aio-v25 がどの構図でも膣セックスを出す。4本目は作らない。
- 3行為を1 LoRA に混ぜる（立ってキスしただけで糞や尿が混ざる）
- ThumbInButt の四つん這い素材を流用する（また構図が死ぬ）

## 準備（撮る／集める前。これがないと始めない）

1. **ffmpeg / ffprobe**（24.000fps に打ち直す。無いとパックが落ちる）
2. **fal アカウント**。trainer は `minimax/h3/i2v/trainer`。Fal H3 Max には LoRA を差せない
3. **作業フォルダを3つ**。zip も素材も Git に入れない

```
h3-train/
  raw/anal-any-h3/
  raw/urine-drink-h3/
  raw/scat-act-h3/
  packed/
```

4. **権利のある素材だけ**（自分で撮る／買う／利用許諾がある）。無断転載は使わない
5. **出演は成人女性／ふたなり 22歳以上だけ**。男なし。未成年なし
6. グリッドを出す（印刷してチェックする）

```bash
python3 h3-lora-studio/train/pack_dataset.py --print-checklist
python3 h3-lora-studio/train/pack_dataset.py --concept anal-any-h3 --print-grid
python3 h3-lora-studio/train/pack_dataset.py --write-kit
```

印刷用は `h3-lora-studio/train/grids/<id>.txt`。

## 素材の仕様（1本ずつ）

- 長さ **5〜10秒**。3秒未満と 15秒超は落とす
- **ちょうど 24.000 fps**。23.976 / 25 / 30 は打ち直す。スローは等速に戻す
- 先頭と末尾は黒・フェードなし
- **音は残す**（H3 は映像と音を同時に覚える）
- 解像度は 32 の倍数。9:16 は 704×1280。16:9 は 1280×704
- ファイル名（キャプションは手で書かなくてよい）

```
{pose}_{camera}_{shot}_{aspect}_{番号}.mp4
standing_front_close_9x16_01.mp4
```

camera は `front` `behind` `side` `above`。shot は `close` `medium`。aspect は `9x16` `16x9`。

打ち直し（9:16の例。音を消さない）:

```bash
ffmpeg -y -i IN.mp4 \
  -filter:v "fps=24,scale=704:1280:force_original_aspect_ratio=decrease,pad=704:1280:(ow-iw)/2:(oh-ih)/2,setsar=1" \
  -t 10 -c:v libx264 -pix_fmt yuv420p -c:a aac -ar 44100 \
  standing_front_close_9x16_01.mp4
```

16:9 は `scale=1280:704` と `pad=1280:704`。

## 概念ごとの中身（撮るときこれだけ見る）

### `anal-any-h3`（`AN4LIN`）

今の ThumbInButt は四つん這い・後ろから・穴が膣より上、に固定される。どの体位でもアナルに入っている状態を出す。

画面に必須:
- fully erect 20cm human penis already fully inside the anus, not the vagina
- both hands of the penetrating partner stay on the hips, not near the anus as thumbs
- anus is the penetrated hole in every pose

画面に出したら捨てる:
- vaginal penetration
- thumb or fingers in the anus
- men or male bodies
- minors

この LoRA の仕事ではない: vaginal sex / thumb in anus / already-coated feces / urine drinking

### `urine-drink-h3`（`URNKISS`）

黄色い水の見た目ロックはある。飲む行為そのものをどの体位でも出す LoRA は無い。既存ストーリーの飲尿はジュボのまま。この LoRA は新規シーン用。

画面に必須:
- opaque yellow urine
- stream from the urethral opening at the glans tip of the erect 20cm, the same hole semen would pulse from, not from the pussy at the base
- the other adult woman drinks the yellow stream

画面に出したら捨てる:
- white liquid
- clear water
- urine from off-screen
- urine from the pussy
- men or male bodies
- minors

この LoRA の仕事ではない: semen / clear water / pee from the pussy at the base / off-screen stream / defecation

### `scat-act-h3`（`DFCTH3`）

ニクカベ肥溜めはすでに塗れている見た目。出す行為そのものでは無い。どの体位でも今出している動きを覚える。医院・終電には足さない。

画面に必須:
- the act of defecating now: brown feces coming out of the anus in this clip
- motion of passing, not a still already-coated body

画面に出したら捨てる:
- already-coated cesspit look with no act
- men or male bodies
- minors

この LoRA の仕事ではない: body already coated from before / urine drinking / anal sex / semen

アナルは **もう入っている**。未挿入から入れる練習はしない。手は腰。親指にしない。膣にしない。
飲尿は **亀頭先の尿道口から黄色い水**。根元のマンコから出さない。透明・白・画面外から、にしない。相手が飲む。
脱糞は **今出している動き**。最初から塗れている肥溜めとは別。

## やること（1概念ずつ。3本並行で混ぜない）

### A. 集める

1. `grids/<id>.txt` を開く
2. 1セル1本撮る／集める。ファイル名をグリッド通りにする
3. 上の ffmpeg で 24.000fps にする
4. 目視: 行為が見える。別行為が映っていない。男がいない

### B. パック（キット）

```bash
python3 h3-lora-studio/train/pack_dataset.py --list
python3 h3-lora-studio/train/pack_dataset.py \
  --concept anal-any-h3 \
  --src ~/h3-train/raw/anal-any-h3 \
  --out ~/h3-train/packed \
  --check-only --strict-coverage
```

警告が残るうちは zip を作らない。体位が偏っていたら撮り足す。
通ったら `--check-only` を外して zip を出す。

```bash
python3 h3-lora-studio/train/pack_dataset.py \
  --concept anal-any-h3 \
  --src ~/h3-train/raw/anal-any-h3 \
  --out ~/h3-train/packed \
  --rewrite-captions --strict-coverage
```

出来物:

- `packed/anal-any-h3.zip` … 中身は `01.mp4` + `01.txt` の連番（fal の形式）
- `packed/anal-any-h3-pack-report.json` … 本数・体位の割合・fal の推奨値
- 隣の `.txt` はキャプション。先頭にトリガーが焼いてある

ffprobe が無い試し打ちだけ `--skip-probe`。10本未満の配線確認だけ `--allow-small`。本学習には使わない。

### C. fal

1. trainer `minimax/h3/i2v/trainer` を開く
2. **先に** `debug_dataset: true`。クロップとキャプションを見る。おかしかったら本学習しない
3. rank **16**
4. 80本前後は 3000 step / 2e-4。120本超は 5000 step / 1e-4（report の `fal` に書いてある）
5. `trigger_phrase` は **空**。キャプションに焼いてある。両方に入れると従わなくなる
6. `auto_scale_input: true`、`strict_dataset: true`、`number_of_frames: 73`、24fps
7. 料金はその場で fal の trainer ページを見る（ここに数字を書かない）
8. 終わったら CDN を当てにせず `.safetensors` をすぐ落とす

`Lora_Trainer_XL.ipynb` は SDXL。H3 には使わない。musubi-tuner の still は顔向き。この3本は動画で覚える。

### D. 重みが手元に来てから（今はやらない）

1. Drive `minimax-h3-comfyui/models/loras/` に置く
   - `anal-any-h3.safetensors`
   - `urine-drink-h3.safetensors`
   - `scat-act-h3.safetensors`
2. 別セッションでカタログに行を足す（`source: local`。②は DL せず Drive の同名ファイルを使う）
3. アナルの act を `anal-any-h3` にする（竿＋穴は残す。ThumbInButt は戻さない）
4. 飲尿・脱糞は今の situation の act を差し替える。**新しい話だけ**
5. 既存話のジュボ置き換えは戻さない。医院・終電の `No feces.` は外さない

## この概念が終わったと言える条件

- その概念の zip がある。中は連番の mp4+txt。本数 80以上
- report の体位シェアがどれも 25%以下。欠け体位なし
- キャプション先頭がトリガー。fal の `trigger_phrase` は空
- debug_dataset でクロップが行為を映している
- `.safetensors` をローカル／Drive に保存した（CDN だけにしない）
- まだカタログに行が無い（無い重みを③に足していない）

## やらないこと

- 3行為を1 LoRA に混ぜる
- 1体位ばかり集める
- 重みが無い状態で③／カタログに足す
- 既存ストーリーへ飲尿を戻す
- 医院・終電の `No feces.` を外す
- 男・未成年を素材に入れる
- fal の trigger とキャプションの二重焼き
- 数字を発明して「学習できた」ことにする
- Threads の schedule を戻す
