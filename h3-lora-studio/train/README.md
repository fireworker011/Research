# どの構図でも出す行為 LoRA

膣セックスは今の `hmnsfw-aio-v25` で足りる。新しく作るのは **足りない3本だけ**。1ファイルに混ぜない。

| 作りたいもの | 今のスタジオ | このキット |
|---|---|---|
| セックス（膣） | AIO + 竿 + 穴。どの構図でも出る | **作らない** |
| アナル | ThumbInButt。四つん這い・後ろから・穴が膣より上、に固定 | `anal-any-h3`（`AN4LIN`） |
| 飲尿 | 黄色い水の見た目ロックだけ。飲む行為 LoRA は無い。既存話はジュボのまま | `urine-drink-h3`（`URNKISS`） |
| 脱糞 | ニクカベ肥溜めは **すでに塗れている** 見た目。出す行為ではない | `scat-act-h3`（`DFCTH3`） |

③は **今すぐ** 竿＋穴＋文章で出す（ThumbInButt は外した）。学習キットは効きを固める用。既存ストーリーの飲尿はジュボのまま。医院・終電の `No feces.` は外さない。

## なぜ3本か

アナルと飲尿と脱糞を同じ LoRA に入れると、立ってキスしただけで糞や尿が混ざる。概念は1行為1ファイル。

ThumbInButt が「どの構図でも出ない」理由は、学習素材がほぼ同じ体位だから。こっちは **行為を先に書き、カメラは最後**。1つの体位が全体の25%を超えたらパックが警告する。

## 素材

- クリップ **80〜160本** / 概念（fal の下限は10。それだと構図が固定される）
- **5〜10秒**。3秒未満と15秒超は落とす
- **ちょうど 24.000 fps**。23.976 / 25 / 30 は打ち直す。スローモーションは等速に戻す
- 先頭と末尾は黒・フェードなし
- 音は残す（H3 は映像と音を同時に覚える）
- 解像度は 32 の倍数。16:9 は 1280×704、9:16 は 704×1280
- 成人女性 / ふたなり **22歳以上** だけ。男なし。未成年なし
- 権利のある素材だけ

ファイル名で構図を書く（キャプションを手で書かなくてよい）:

```
{pose}_{camera}_{shot}_{aspect}_{番号}.mp4
standing_front_close_9x16_01.mp4
doggy_behind_medium_16x9_02.mp4
```

| 概念 | pose |
|---|---|
| アナル | standing / doggy / missionary / cowgirl / side / pov |
| 飲尿 | standing / kneeling / sitting / cowgirl / side / pov |
| 脱糞 | standing / squat / doggy / missionary / sitting / side |

camera は `front` `behind` `side` `above`。shot は `close` `medium`。aspect は `9x16` `16x9`。

グリッドの一覧:

```bash
python3 h3-lora-studio/train/pack_dataset.py --concept anal-any-h3 --print-grid
python3 h3-lora-studio/train/pack_dataset.py --concept urine-drink-h3 --write-shot-list /tmp/urine-grid.txt
```

アナルは **もう入っている**（未挿入から入れる練習はしない。手は腰。親指にしない。膣にしない）。
飲尿は **亀頭先の尿道口から黄色い水**（精液と同じ穴。根元のマンコから出さない。透明・白・画面外から、にしない）。相手の成人女性が飲む。
脱糞は **今出している動き**（最初から塗れている肥溜めとは別）。

## パック

```bash
python3 h3-lora-studio/train/pack_dataset.py --list
python3 h3-lora-studio/train/pack_dataset.py \
  --concept anal-any-h3 \
  --src /path/to/anal-clips \
  --out /path/to/out
```

zip は `01.mp4` + `01.txt` の連番（fal の形式）。隣に `{id}-pack-report.json` が出る。キャプション先頭にトリガーを焼く。既存の `.txt` にトリガーがあればそれを残す。`--rewrite-captions` でテンプレに戻す。

ffprobe が無いとき / ダミー確認は `--skip-probe`。10本未満の試しは `--allow-small`。

## fal

スタジオの行為クリップは last-frame I2V が本線なので、学習も **`minimax/h3/i2v/trainer`**。Fal H3 Max には LoRA を差せない。できた `.safetensors` は Colab Comfy（FL2VA）で使う。

1. 先に `debug_dataset: true`（課金の本学習の前に、クロップとキャプションを見る）
2. rank **16**
3. 80本前後は 3000 step / 2e-4。120本超は 5000 step / 1e-4
4. `trigger_phrase` は **空**。キャプションに焼いてある。両方に入れると従わなくなる
5. `auto_scale_input: true`、`strict_dataset: true`、`number_of_frames: 73`、24fps
6. 料金は fal の trainer ページをその場で見る（ここには書かない）
7. 終わったら CDN を当てにせず `.safetensors` をすぐ落とす

`Lora_Trainer_XL.ipynb` は SDXL。H3 には使わない。musubi-tuner の still / one-frame は顔 LoRA 向き。この3本は動画で覚える。

## 重みができたあと（別セッション）

Drive `minimax-h3-comfyui/models/loras/` に置く。カタログは `source: local`。アナルは ThumbInButt を外して `anal-any-h3` + 竿 + 穴。飲尿・脱糞は **新しい situation** だけ。既存話のジュボ置き換えは戻さない。医院・終電に糞は足さない。

## やらないこと

- 3行為を1 LoRA に混ぜる
- 1体位ばかり集める
- 重みが無い状態で③に足す
- 既存ストーリーへ飲尿を戻す
- 医院・終電の `No feces.` を外す
- 男・未成年を素材に入れる
- fal の trigger とキャプションの二重焼き
- 数字を発明して「学習できた」ことにする
